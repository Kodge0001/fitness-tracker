from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, User, HeartRateLog, StepLog, CalorieLog, WorkoutLog, Goal, GeminiCoachPlan, FitnessTask
from app.charts import render_chart_by_type
from app.ai_insights import fetch_or_generate_ai_insight
from app.gemini_coach import generate_gemini_coach_plan

logs_bp = Blueprint("logs", __name__)


def parse_timestamp(ts_str):
    if not ts_str:
        return datetime.now(timezone.utc)
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)


def get_current_user_obj(user_id):
    user = db.session.get(User, user_id)
    if not user:
        user = User.query.filter_by(id=user_id).first()
    if not user:
        user = User.query.first()
    if not user:
        user = User(username="Athlete", email=f"user_{user_id}@fitness.io")
        user.set_password("fitness123")
        db.session.add(user)
        db.session.commit()
    return user


# ==========================================
# 1. LOGGING ENDPOINTS
# ==========================================

@logs_bp.route("/logs/heart-rate", methods=["POST"])
@jwt_required()
def log_heart_rate():
    user = get_current_user_obj(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    bpm = data.get("bpm")

    if bpm is None or not isinstance(bpm, (int, float)) or bpm <= 0:
        return jsonify({"error": "Valid 'bpm' (positive number) is required"}), 400

    timestamp = parse_timestamp(data.get("timestamp"))
    hr_log = HeartRateLog(user_id=user.id, bpm=int(bpm), timestamp=timestamp)
    db.session.add(hr_log)
    db.session.commit()

    return jsonify({"message": "Heart rate logged", "log": hr_log.to_dict()}), 201


@logs_bp.route("/logs/steps", methods=["POST"])
@jwt_required()
def log_steps():
    user = get_current_user_obj(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    count = data.get("count")

    if count is None or not isinstance(count, (int, float)) or count < 0:
        return jsonify({"error": "Valid 'count' (non-negative number) is required"}), 400

    timestamp = parse_timestamp(data.get("timestamp"))
    step_log = StepLog(user_id=user.id, count=int(count), timestamp=timestamp)
    db.session.add(step_log)
    db.session.commit()

    return jsonify({"message": "Steps logged", "log": step_log.to_dict()}), 201


@logs_bp.route("/logs/calories", methods=["POST"])
@jwt_required()
def log_calories():
    user = get_current_user_obj(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    burned = data.get("burned")

    if burned is None or not isinstance(burned, (int, float)) or burned < 0:
        return jsonify({"error": "Valid 'burned' (non-negative number) is required"}), 400

    timestamp = parse_timestamp(data.get("timestamp"))
    cal_log = CalorieLog(user_id=user.id, burned=float(burned), timestamp=timestamp)
    db.session.add(cal_log)
    db.session.commit()

    return jsonify({"message": "Calories logged", "log": cal_log.to_dict()}), 201


@logs_bp.route("/logs/workout", methods=["POST"])
@jwt_required()
def log_workout():
    user = get_current_user_obj(int(get_jwt_identity()))
    data = request.get_json(silent=True) or {}
    workout_type = data.get("type", "").strip()
    duration_min = data.get("duration_min")
    intensity = data.get("intensity", "medium").lower()

    if not workout_type:
        return jsonify({"error": "Workout 'type' is required"}), 400

    if duration_min is None or not isinstance(duration_min, (int, float)) or duration_min <= 0:
        return jsonify({"error": "Valid positive 'duration_min' is required"}), 400

    if intensity not in ["low", "medium", "high"]:
        intensity = "medium"

    timestamp = parse_timestamp(data.get("timestamp"))
    w_log = WorkoutLog(
        user_id=user.id,
        type=workout_type,
        duration_min=float(duration_min),
        intensity=intensity,
        timestamp=timestamp,
    )
    db.session.add(w_log)

    rate = 11.5 if intensity == "high" else (8.0 if intensity == "medium" else 5.5)
    cal_log = CalorieLog(user_id=user.id, burned=round(float(duration_min) * rate, 1), timestamp=timestamp)
    db.session.add(cal_log)

    db.session.commit()

    return jsonify({"message": "Workout logged", "log": w_log.to_dict()}), 201


@logs_bp.route("/logs/summary", methods=["GET"])
@jwt_required()
def get_logs_summary():
    user_id = int(get_jwt_identity())
    days = request.args.get("days", default=30, type=int)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    steps = StepLog.query.filter(StepLog.user_id == user_id, StepLog.timestamp >= cutoff).all()
    hrs = HeartRateLog.query.filter(HeartRateLog.user_id == user_id, HeartRateLog.timestamp >= cutoff).all()
    cals = CalorieLog.query.filter(CalorieLog.user_id == user_id, CalorieLog.timestamp >= cutoff).all()
    workouts = WorkoutLog.query.filter(WorkoutLog.user_id == user_id, WorkoutLog.timestamp >= cutoff).all()
    goal = Goal.query.filter_by(user_id=user_id).first()

    total_steps = sum(s.count for s in steps)
    total_cals = sum(c.burned for c in cals)
    total_workout_mins = sum(w.duration_min for w in workouts)
    avg_hr = round(sum(h.bpm for h in hrs) / len(hrs), 1) if hrs else None

    daily_data = {}
    for i in range(days):
        d = (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_data[d] = {"steps": 0, "calories": 0.0, "active_mins": 0.0, "hr_readings": []}

    for s in steps:
        d = s.timestamp.strftime("%Y-%m-%d")
        if d in daily_data:
            daily_data[d]["steps"] += s.count

    for c in cals:
        d = c.timestamp.strftime("%Y-%m-%d")
        if d in daily_data:
            daily_data[d]["calories"] += c.burned

    for w in workouts:
        d = w.timestamp.strftime("%Y-%m-%d")
        if d in daily_data:
            daily_data[d]["active_mins"] += w.duration_min

    for h in hrs:
        d = h.timestamp.strftime("%Y-%m-%d")
        if d in daily_data:
            daily_data[d]["hr_readings"].append(h.bpm)

    summary_result = {
        "period_days": days,
        "total_steps": total_steps,
        "total_calories": round(total_cals, 1),
        "total_workout_minutes": round(total_workout_mins, 1),
        "average_heart_rate": avg_hr,
        "workout_count": len(workouts),
        "goals": goal.to_dict() if goal else None,
        "daily_breakdown": daily_data,
    }
    return jsonify(summary_result), 200


# ==========================================
# 2. GOALS ENDPOINTS (CRUD & Progress)
# ==========================================

@logs_bp.route("/goals", methods=["GET"])
@jwt_required()
def get_goals():
    user_id = int(get_jwt_identity())
    goal = Goal.query.filter_by(user_id=user_id).first()
    if not goal:
        goal = Goal(user_id=user_id, step_goal=10000, calorie_goal=500.0, active_minutes_goal=45.0)
        db.session.add(goal)
        db.session.commit()
    return jsonify({"goal": goal.to_dict()}), 200


@logs_bp.route("/goals", methods=["POST", "PUT"])
@jwt_required()
def update_goals():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}

    goal = Goal.query.filter_by(user_id=user_id).first()
    if not goal:
        goal = Goal(user_id=user_id)
        db.session.add(goal)

    if "step_goal" in data and isinstance(data["step_goal"], (int, float)):
        goal.step_goal = int(data["step_goal"])
    if "calorie_goal" in data and isinstance(data["calorie_goal"], (int, float)):
        goal.calorie_goal = float(data["calorie_goal"])
    if "active_minutes_goal" in data and isinstance(data["active_minutes_goal"], (int, float)):
        goal.active_minutes_goal = float(data["active_minutes_goal"])

    goal.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({"message": "Goals updated successfully", "goal": goal.to_dict()}), 200


@logs_bp.route("/goals/progress", methods=["GET"])
@jwt_required()
def get_goals_progress():
    user_id = int(get_jwt_identity())
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)

    goal = Goal.query.filter_by(user_id=user_id).first()
    if not goal:
        goal = Goal(user_id=user_id, step_goal=10000, calorie_goal=500.0, active_minutes_goal=45.0)
        db.session.add(goal)
        db.session.commit()

    steps_today = db.session.query(db.func.sum(StepLog.count)).filter(
        StepLog.user_id == user_id, StepLog.timestamp >= today_start
    ).scalar() or 0

    cals_today = db.session.query(db.func.sum(CalorieLog.burned)).filter(
        CalorieLog.user_id == user_id, CalorieLog.timestamp >= today_start
    ).scalar() or 0.0

    active_mins_today = db.session.query(db.func.sum(WorkoutLog.duration_min)).filter(
        WorkoutLog.user_id == user_id, WorkoutLog.timestamp >= today_start
    ).scalar() or 0.0

    step_pct = min(100.0, round((steps_today / goal.step_goal * 100) if goal.step_goal else 0.0, 1))
    cal_pct = min(100.0, round((cals_today / goal.calorie_goal * 100) if goal.calorie_goal else 0.0, 1))
    act_pct = min(100.0, round((active_mins_today / goal.active_minutes_goal * 100) if goal.active_minutes_goal else 0.0, 1))

    return jsonify({
        "today": today_start.strftime("%Y-%m-%d"),
        "steps": {"current": steps_today, "target": goal.step_goal, "percent": step_pct},
        "calories": {"current": round(cals_today, 1), "target": goal.calorie_goal, "percent": cal_pct},
        "active_minutes": {"current": round(active_mins_today, 1), "target": goal.active_minutes_goal, "percent": act_pct},
    }), 200


# ==========================================
# 3. MATPLOTLIB CHARTS STREAMING
# ==========================================

@logs_bp.route("/charts/<chart_type>.png", methods=["GET"])
@jwt_required()
def get_chart_image(chart_type):
    user_id = int(get_jwt_identity())
    img_io = render_chart_by_type(chart_type, user_id)
    return send_file(img_io, mimetype="image/png", as_attachment=False)


# ==========================================
# 4. GEMINI AI COACH (Diet, Exercise, Timeline, Tasks)
# ==========================================

@logs_bp.route("/gemini/coach", methods=["GET"])
@jwt_required()
def get_gemini_coach_plan():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        # If running in a fresh serverless instance without this user ID, auto-create/recover user
        user = User.query.first()
        if not user:
            user = User(username="Athlete", email=f"user_{user_id}@fitness.io")
            user.set_password("fitness123")
            db.session.add(user)
            db.session.commit()

    # Fetch latest plan or generate if absent
    plan = GeminiCoachPlan.query.filter_by(user_id=user.id).order_by(GeminiCoachPlan.created_at.desc()).first()
    if not plan:
        plan = generate_gemini_coach_plan(user)

    return jsonify({"plan": plan.to_dict() if plan else None}), 200


@logs_bp.route("/gemini/coach", methods=["POST"])
@jwt_required()
def refresh_gemini_coach_plan():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        user = User.query.first()
        if not user:
            user = User(username="Athlete", email=f"user_{user_id}@fitness.io")
            user.set_password("fitness123")
            db.session.add(user)
            db.session.commit()

    data = request.get_json(silent=True) or {}
    plan = generate_gemini_coach_plan(user, user_details=data)
    return jsonify({
        "message": "Gemini AI plan generated successfully",
        "user": user.to_dict(),
        "plan": plan.to_dict() if plan else None
    }), 200


@logs_bp.route("/gemini/tasks/<int:task_id>/toggle", methods=["POST", "PATCH"])
@jwt_required()
def toggle_gemini_task(task_id):
    user_id = int(get_jwt_identity())
    task = db.session.get(FitnessTask, task_id)
    if not task or task.user_id != user_id:
        return jsonify({"error": "Task not found"}), 404

    task.is_completed = not task.is_completed
    task.completed_at = datetime.now(timezone.utc) if task.is_completed else None
    db.session.commit()

    return jsonify({"message": "Task updated", "task": task.to_dict()}), 200


# ==========================================
# 5. AI INSIGHTS
# ==========================================

@logs_bp.route("/ai/insights", methods=["GET"])
@jwt_required()
def get_cached_ai_insight():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    insight, is_cached = fetch_or_generate_ai_insight(user, force_refresh=False)
    if not insight:
        return jsonify({"error": "No AI insights generated yet."}), 404

    return jsonify({"cached": is_cached, "insight": insight}), 200


@logs_bp.route("/ai/insights", methods=["POST"])
@jwt_required()
def refresh_ai_insight():
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    insight, _ = fetch_or_generate_ai_insight(user, force_refresh=True)
    return jsonify({"message": "AI insights refreshed", "insight": insight}), 200
