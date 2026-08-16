import os
import json
import logging
from datetime import datetime, timezone, timedelta
from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError
from flask import current_app
from app.models import db, User, StepLog, HeartRateLog, CalorieLog, WorkoutLog, Goal, AIInsightCache

logger = logging.getLogger(__name__)

def generate_local_fallback_insight(summary_data: dict) -> dict:
    """Generate structured fallback insights when Anthropic API key is not configured or unavailable."""
    avg_steps = summary_data.get("avg_daily_steps", 0)
    step_goal = summary_data.get("step_goal", 10000)
    avg_hr = summary_data.get("avg_heart_rate", 72)
    total_workouts = summary_data.get("total_workouts", 0)
    total_cals = summary_data.get("total_calories_burned", 0)
    avg_active_mins = summary_data.get("avg_daily_active_mins", 0)

    step_ratio = (avg_steps / step_goal) if step_goal else 0.8
    risk_flags = []

    if avg_hr > 95:
        risk_flags.append("Elevated resting heart rate detected over recent sessions.")
    if avg_steps < 4000 and total_workouts < 3:
        risk_flags.append("Sedentary trend: daily activity is below recommended levels.")
    if total_workouts > 25 and avg_active_mins > 90:
        risk_flags.append("High volume alert: monitor recovery and ensure sufficient sleep.")

    if not risk_flags:
        risk_flags.append("No immediate health risks detected based on recent metrics.")

    trend = "Upward consistent momentum" if step_ratio >= 0.8 else "Needs consistency boost"
    summary = (
        f"Over the last 30 days, you logged {total_workouts} workouts burning approx {total_cals:,.0f} calories. "
        f"Your daily steps averaged {avg_steps:,.0f} (Goal: {step_goal:,.0f}), with an average heart rate of {avg_hr:.0f} BPM."
    )
    
    if step_ratio >= 1.0:
        rec = "You are crushing your daily step and workout goals! Maintain hydration and add dedicated stretching or mobility routines."
    elif step_ratio >= 0.7:
        rec = "Solid progress! Try scheduling an extra 15-minute brisk walk during lunch breaks to hit your full 100% daily step target."
    else:
        rec = "Focus on micro-habits: start with a 20-minute daily walk and 2 short strength sessions this week to build consistency."

    return {
        "summary": summary,
        "trend": trend,
        "recommendation": rec,
        "risk_flags": risk_flags,
    }


def get_user_compact_summary(user_id: int, days: int = 30) -> dict:
    """Build a compact aggregated summary of user logs over the past N days for LLM prompt."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    steps = StepLog.query.filter(StepLog.user_id == user_id, StepLog.timestamp >= cutoff).all()
    hrs = HeartRateLog.query.filter(HeartRateLog.user_id == user_id, HeartRateLog.timestamp >= cutoff).all()
    cals = CalorieLog.query.filter(CalorieLog.user_id == user_id, CalorieLog.timestamp >= cutoff).all()
    workouts = WorkoutLog.query.filter(WorkoutLog.user_id == user_id, WorkoutLog.timestamp >= cutoff).all()
    goal = Goal.query.filter_by(user_id=user_id).first()

    total_steps = sum(s.count for s in steps)
    unique_step_days = len(set(s.timestamp.strftime("%Y-%m-%d") for s in steps)) or 1
    avg_daily_steps = round(total_steps / max(unique_step_days, 1))

    avg_hr = round(sum(h.bpm for h in hrs) / len(hrs), 1) if hrs else 72.0
    min_hr = min((h.bpm for h in hrs), default=60)
    max_hr = max((h.bpm for h in hrs), default=140)

    total_calories = round(sum(c.burned for c in cals), 1)
    total_workouts = len(workouts)
    total_workout_mins = sum(w.duration_min for w in workouts)
    avg_active_mins = round(total_workout_mins / max(unique_step_days, 1), 1)

    workout_types = {}
    for w in workouts:
        workout_types[w.type] = workout_types.get(w.type, 0) + 1

    return {
        "period_days": days,
        "step_goal": goal.step_goal if goal else 10000,
        "calorie_goal": goal.calorie_goal if goal else 500.0,
        "active_minutes_goal": goal.active_minutes_goal if goal else 45.0,
        "total_steps": total_steps,
        "avg_daily_steps": avg_daily_steps,
        "total_calories_burned": total_calories,
        "avg_heart_rate": avg_hr,
        "min_heart_rate": min_hr,
        "max_heart_rate": max_hr,
        "total_workouts": total_workouts,
        "total_workout_minutes": total_workout_mins,
        "avg_daily_active_mins": avg_active_mins,
        "workout_breakdown": workout_types,
    }


def fetch_or_generate_ai_insight(user: User, force_refresh: bool = False) -> tuple[dict, bool]:
    """
    Returns (insight_dict, is_cached).
    Checks cache first (valid for 24 hours). If force_refresh or stale, calls Claude API or fallback.
    Guarantees thread safety and never crashes the request.
    """
    now = datetime.now(timezone.utc)

    # Check 24-hour cache
    if not force_refresh:
        latest_cache = (
            AIInsightCache.query.filter_by(user_id=user.id)
            .order_by(AIInsightCache.created_at.desc())
            .first()
        )
        if latest_cache:
            created_at = latest_cache.created_at
            # Make sure timezone aware
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if now - created_at < timedelta(hours=24):
                return latest_cache.to_dict(), True

    compact_summary = get_user_compact_summary(user.id, days=30)
    api_key = current_app.config.get("ANTHROPIC_API_KEY")

    insight_data = None

    if api_key and api_key.strip():
        try:
            client = Anthropic(api_key=api_key)
            prompt = (
                "You are an expert sports scientist and personalized health coach. "
                "Analyze the user's last 30 days fitness and biometric activity data provided below:\n\n"
                f"{json.dumps(compact_summary, indent=2)}\n\n"
                "Return ONLY a valid JSON object with the exact keys: 'summary', 'trend', 'recommendation', 'risk_flags'.\n"
                "Constraints:\n"
                "- 'summary': (str) High-level assessment of their progress and activity.\n"
                "- 'trend': (str) Key trend trajectory (e.g. Improving, Plateauing, Highly Active, Recovering).\n"
                "- 'recommendation': (str) Actionable, motivating fitness/nutrition advice for next week.\n"
                "- 'risk_flags': (list of strings) Potential risks (e.g., overtraining, low step volume, erratic HR) or 'None' if optimal.\n"
                "Do not include markdown fences (```json), commentary, or extra text."
            )

            response = client.messages.create(
                model=current_app.config.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
                max_tokens=800,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                timeout=12.0
            )

            text_response = response.content[0].text.strip()
            # Clean possible markdown wrap
            if text_response.startswith("```json"):
                text_response = text_response[7:]
            if text_response.startswith("```"):
                text_response = text_response[3:]
            if text_response.endswith("```"):
                text_response = text_response[:-3]

            parsed = json.loads(text_response.strip())
            if isinstance(parsed, dict) and "summary" in parsed and "recommendation" in parsed:
                insight_data = {
                    "summary": str(parsed.get("summary", "")),
                    "trend": str(parsed.get("trend", "Consistent")),
                    "recommendation": str(parsed.get("recommendation", "")),
                    "risk_flags": list(parsed.get("risk_flags", [])),
                }
        except (APIError, APITimeoutError, RateLimitError) as e:
            logger.warning(f"Anthropic API call failed: {e}. Falling back to rule-based insight engine.")
            insight_data = generate_local_fallback_insight(compact_summary)
        except Exception as e:
            logger.error(f"Unexpected error in AI insight generation: {e}")
            insight_data = generate_local_fallback_insight(compact_summary)
    else:
        logger.info("No ANTHROPIC_API_KEY supplied. Using deterministic rule-based insight engine.")
        insight_data = generate_local_fallback_insight(compact_summary)

    if not insight_data:
        insight_data = generate_local_fallback_insight(compact_summary)

    # Save to database cache
    try:
        new_cache = AIInsightCache(
            user_id=user.id,
            summary=insight_data["summary"],
            trend=insight_data["trend"],
            recommendation=insight_data["recommendation"],
            risk_flags=insight_data["risk_flags"],
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(new_cache)
        db.session.commit()
        return new_cache.to_dict(), False
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error caching AI insight to database: {e}")
        return insight_data, False
