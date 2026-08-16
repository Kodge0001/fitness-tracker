import os
import json
import logging
from datetime import datetime, timezone
from flask import current_app
from app.models import db, User, GeminiCoachPlan, FitnessTask
from app.ai_insights import get_user_compact_summary

logger = logging.getLogger(__name__)


def generate_fallback_gemini_plan(user: User, user_details: dict = None) -> dict:
    """Intelligent rule-based fallback generator customized to user's exact age, weight, diet, and goal."""
    details = user_details or {}
    try:
        age = int(details.get("age") or user.age or 26)
    except (ValueError, TypeError):
        age = 26

    gender = str(details.get("gender") or user.gender or "Male")

    try:
        weight = float(details.get("weight_kg") or user.weight_kg or 72.0)
    except (ValueError, TypeError):
        weight = 72.0

    try:
        height = float(details.get("height_cm") or user.height_cm or 175.0)
    except (ValueError, TypeError):
        height = 175.0

    level = str(details.get("fitness_level") or user.fitness_level or "Intermediate")
    goal = str(details.get("goal_focus") or user.goal_focus or "Build Lean Muscle & Fat Loss")
    diet_pref = str(details.get("dietary_preference") or user.dietary_preference or "High Protein Non-Veg")

    try:
        days_pw = int(details.get("workout_days_per_week") or user.workout_days_per_week or 4)
    except (ValueError, TypeError):
        days_pw = 4

    injuries = str(details.get("injuries_or_limitations") or user.injuries_or_limitations or "None")

    try:
        weeks = int(details.get("target_timeline_weeks") or user.target_timeline_weeks or 4)
    except (ValueError, TypeError):
        weeks = 4

    # Calculate optimal target protein (approx 2.0g per kg for muscle, 1.8g for fat loss)
    target_protein = round(float(weight) * 2.0)
    target_water = round(float(weight) * 0.045, 1)

    exercise_suggestions = [
        {
            "phase": f"{goal} - Phase 1 Routine",
            "focus": f"{level} Level Split ({days_pw} Days/Week)",
            "details": f"Tailored for {age}yo {gender} ({weight}kg). Exercises focused on progressive overload: Squats, Incline Press, Lat Pulls, Romanian Deadlifts with 3 sets of 8-12 reps.",
            "cardio": "Zone-2 Cardio: 25 mins brisk incline walking (heart rate 125-145 BPM) post-workout.",
            "recovery": f"Dedicated warm-up focusing on {injuries if injuries.lower() != 'none' else 'hips, core & rotator cuff'}."
        },
        {
            "phase": "Metabolic Conditioning & Core Definition",
            "focus": f"High-Efficiency Circuit ({days_pw - 2 if days_pw > 3 else 2} Sessions/Week)",
            "details": "Hanging knee raises, Cable woodchoppers, Planks with weight, and Dumbbell farmer walks to sculpt core.",
            "cardio": "15-minute HIIT intervals on stationary bike or rower.",
            "recovery": "Foam roll hamstrings, lats, and glutes for 10 mins post-session."
        }
    ]

    diet_suggestions = [
        {
            "title": f"Customized {diet_pref} Nutrition Blueprint",
            "guideline": f"Target: ~{target_protein}g Daily Protein ({target_protein // 4}g across 4 meals). Emphasize eggs, chicken/fish/tofu, Greek yogurt, lentils, quinoa.",
            "timing": "Breakfast: 35g protein + complex carbs; Post-workout: 35g protein shake within 45 mins; Dinner: Lean protein + green cruciferous vegetables."
        },
        {
            "title": f"Hydration & Micronutrient Target ({target_water}L / Day)",
            "guideline": f"Drink minimum {target_water} Liters of water daily. Add electrolyte salts during training days.",
            "timing": "500ml upon waking, 1L during workout session, 500ml with each major meal."
        },
        {
            "title": "Calorie Partitioning & Recovery Fuel",
            "guideline": f"Maintain a calibrated 250 kcal {'deficit for fat loss' if 'loss' in goal.lower() or 'abs' in goal.lower() else 'surplus for lean muscle gain'}.",
            "timing": "Taper carbohydrates after 8:00 PM; consume casein or cottage cheese before sleep for overnight recovery."
        }
    ]

    timeline = [
        {
            "week": "Week 1: Metabolic Baseline & Form Calibration",
            "milestone": f"Establish daily food log, calibrate {target_protein}g protein target, and execute all {days_pw} scheduled workouts.",
            "target": f"100% adherence to {days_pw} training days & hydration goal."
        },
        {
            "week": "Week 2: Progressive Overload & Weight Progression",
            "milestone": "Increase working weights by 2.5-5% on primary compound movements.",
            "target": "Log +2 reps on bench/squat and maintain zero missed protein targets."
        },
        {
            "week": "Week 3: Peak Conditioning & Metabolic Intensity",
            "milestone": "Shorten rest intervals to 60 seconds; add 10 mins extra Zone-2 cardio.",
            "target": "Visible reduction in waist circumference & increased endurance."
        },
        {
            "week": f"Week {weeks}: Transformation Assessment & Strategy Refinement",
            "milestone": "Assess overall strength increase, body measurements, and calibrate Phase 2.",
            "target": f"Complete {weeks}-week {goal} milestone review."
        }
    ]

    tasks = [
        {
            "category": "exercise",
            "title": f"Complete {level} {days_pw}-Day Split Workout Session",
            "description": f"Focus on compound lifts and strict form. Warm up thoroughly for {injuries if injuries.lower() != 'none' else 'shoulders and lower back'}.",
            "target_metric": f"{days_pw} Days / 45-60 mins",
            "day_order": 1
        },
        {
            "category": "diet",
            "title": f"Hit Exact {target_protein}g Daily Protein Target ({diet_pref})",
            "description": f"Eat 4 distinct meals with {target_protein // 4}g protein per meal.",
            "target_metric": f"{target_protein}g Protein",
            "day_order": 1
        },
        {
            "category": "diet",
            "title": f"Drink {target_water} Liters of Water Throughout Today",
            "description": "Keep hydration steady; drink 500ml before midday meal.",
            "target_metric": f"{target_water}L Water",
            "day_order": 1
        },
        {
            "category": "habit",
            "title": "Reach 10,000 Step Daily Baseline",
            "description": "Take brisk walks after lunch and dinner to promote metabolic rate and glucose clearance.",
            "target_metric": "10,000 Steps",
            "day_order": 2
        },
        {
            "category": "exercise",
            "title": "25-min Zone-2 Incline Cardio Session",
            "description": "Keep heart rate steady between 125-145 BPM to optimize fat oxidation and VO2 max.",
            "target_metric": "25 mins Cardio",
            "day_order": 2
        },
        {
            "category": "recovery",
            "title": "7.5 - 8.0 Hours Quality Sleep & Foam Rolling",
            "description": "10-min foam roll session, limit blue light 45 mins before bedtime for maximum muscle repair.",
            "target_metric": "8 hrs Sleep",
            "day_order": 3
        }
    ]

    return {
        "title": f"Customized {goal} Program for {user.username}",
        "focus_goal": f"{goal} ({level} • {diet_pref} • {weight}kg)",
        "exercise_suggestions": exercise_suggestions,
        "diet_suggestions": diet_suggestions,
        "timeline": timeline,
        "tasks": tasks
    }


def generate_gemini_coach_plan(user: User, user_details: dict = None) -> GeminiCoachPlan:
    """
    Calls Google Gemini API (gemini-2.5-flash) with comprehensive user questionnaire details:
    Age, Gender, Height, Weight, Fitness Level, Goal, Diet Preference, Workout Days, Injuries.
    """
    details = user_details or {}
    
    # Save user details to profile
    if details:
        if "age" in details and details["age"]: user.age = int(details["age"])
        if "gender" in details and details["gender"]: user.gender = str(details["gender"])
        if "height_cm" in details and details["height_cm"]: user.height_cm = float(details["height_cm"])
        if "weight_kg" in details and details["weight_kg"]: user.weight_kg = float(details["weight_kg"])
        if "fitness_level" in details and details["fitness_level"]: user.fitness_level = str(details["fitness_level"])
        if "goal_focus" in details and details["goal_focus"]: user.goal_focus = str(details["goal_focus"])
        if "dietary_preference" in details and details["dietary_preference"]: user.dietary_preference = str(details["dietary_preference"])
        if "workout_days_per_week" in details and details["workout_days_per_week"]: user.workout_days_per_week = int(details["workout_days_per_week"])
        if "injuries_or_limitations" in details and details["injuries_or_limitations"]: user.injuries_or_limitations = str(details["injuries_or_limitations"])
        if "target_timeline_weeks" in details and details["target_timeline_weeks"]: user.target_timeline_weeks = int(details["target_timeline_weeks"])
        db.session.commit()

    summary_data = get_user_compact_summary(user.id, days=30)
    api_key = current_app.config.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY", "")

    user_profile_prompt = {
        "user_name": user.username,
        "age": user.age or 26,
        "gender": user.gender or "Male",
        "height_cm": user.height_cm or 175.0,
        "weight_kg": user.weight_kg or 72.0,
        "fitness_level": user.fitness_level or "Intermediate",
        "primary_goal": user.goal_focus or "Build Lean Muscle & Fat Loss",
        "dietary_preference": user.dietary_preference or "High Protein Non-Veg",
        "workout_days_per_week": user.workout_days_per_week or 4,
        "injuries_or_limitations": user.injuries_or_limitations or "None",
        "target_timeline_weeks": user.target_timeline_weeks or 4,
        "recent_30_day_activity": summary_data,
    }

    plan_dict = None

    if api_key and api_key.strip():
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            prompt = (
                f"You are Gemini Fitness & Nutrition Master Coach. Analyze the user's detailed health profile, body metrics, and goals:\n\n"
                f"{json.dumps(user_profile_prompt, indent=2)}\n\n"
                f"Generate a customized, professional fitness & nutrition transformation plan tailored EXACTLY to their "
                f"age ({user.age or 26}), weight ({user.weight_kg or 72}kg), height ({user.height_cm or 175}cm), "
                f"diet preference ({user.dietary_preference}), fitness level ({user.fitness_level}), and goal ({user.goal_focus}).\n\n"
                f"You MUST return ONLY valid JSON matching this exact structure:\n"
                f"{{\n"
                f'  "title": "String (e.g. 4-Week Custom Muscle & Fat Loss Blueprint for Alex)",\n'
                f'  "focus_goal": "String (e.g. Build Lean Muscle & Abs • Intermediate • High Protein Non-Veg)",\n'
                f'  "exercise_suggestions": [\n'
                f'    {{\n'
                f'      "phase": "String (e.g. Hypertrophy & Progressive Overload)",\n'
                f'      "focus": "String (e.g. 4-Day Upper/Lower Split)",\n'
                f'      "details": "String (specific exercises, sets, reps, RPE tailored to their level)",\n'
                f'      "cardio": "String (specific cardio recommendations and heart rate zone)",\n'
                f'      "recovery": "String (mobility and recovery protocol avoiding any mentioned injuries)"\n'
                f'    }}\n'
                f'  ],\n'
                f'  "diet_suggestions": [\n'
                f'    {{\n'
                f'      "title": "String (e.g. Targeted High Protein Macro Plan)",\n'
                f'      "guideline": "String (exact daily protein in grams based on bodyweight, calories, food items tailored to their dietary preference)",\n'
                f'      "timing": "String (exact meal schedule, pre/post workout nutrition, daily hydration target in Liters)"\n'
                f'    }}\n'
                f'  ],\n'
                f'  "timeline": [\n'
                f'    {{\n'
                f'      "week": "String (e.g. Week 1: Phase Name)",\n'
                f'      "milestone": "String (measurable milestone to achieve this week)",\n'
                f'      "target": "String (exact target metric e.g. 100% workout completion, +5% lift)"\n'
                f'    }}\n'
                f'  ],\n'
                f'  "tasks": [\n'
                f'    {{\n'
                f'      "category": "String (exercise | diet | habit | recovery)",\n'
                f'      "title": "String (actionable daily task title)",\n'
                f'      "description": "String (clear instruction)",\n'
                f'      "target_metric": "String (e.g. 45 mins, 145g protein, 3.5L water)",\n'
                f'      "day_order": 1\n'
                f'    }}\n'
                f'  ]\n'
                f"}}\n"
                f"Provide 2 detailed exercise phase cards, 3 diet/hydration cards, 4 weekly timeline milestones, and 6-8 daily interactive checklist tasks.\n"
                f"Do not include markdown fences (```json). Output pure JSON only."
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.3,
                ),
            )

            text_resp = response.text.strip()
            if text_resp.startswith("```json"):
                text_resp = text_resp[7:]
            if text_resp.startswith("```"):
                text_resp = text_resp[3:]
            if text_resp.endswith("```"):
                text_resp = text_resp[:-3]

            parsed = json.loads(text_resp.strip())
            if isinstance(parsed, dict) and "exercise_suggestions" in parsed and "timeline" in parsed:
                plan_dict = parsed
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}. Falling back to rule-based engine.")
            plan_dict = generate_fallback_gemini_plan(user, details)
    else:
        logger.info("No GEMINI_API_KEY found. Generating precision rule-based custom plan.")
        plan_dict = generate_fallback_gemini_plan(user, details)

    if not plan_dict:
        plan_dict = generate_fallback_gemini_plan(user, details)

    # Save to database
    try:
        new_plan = GeminiCoachPlan(
            user_id=user.id,
            title=plan_dict.get("title", f"Customized Fitness Plan for {user.username}"),
            focus_goal=plan_dict.get("focus_goal", f"{user.goal_focus or 'Health Transformation'}"),
            exercise_suggestions=plan_dict.get("exercise_suggestions", []),
            diet_suggestions=plan_dict.get("diet_suggestions", []),
            timeline=plan_dict.get("timeline", []),
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(new_plan)
        db.session.flush()

        raw_tasks = plan_dict.get("tasks", [])
        for t in raw_tasks:
            task = FitnessTask(
                plan_id=new_plan.id,
                user_id=user.id,
                category=t.get("category", "exercise"),
                title=t.get("title", "Daily Fitness Habit"),
                description=t.get("description", ""),
                target_metric=t.get("target_metric", ""),
                day_order=int(t.get("day_order", 1)),
                is_completed=False
            )
            db.session.add(task)

        db.session.commit()
        return new_plan
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error persisting Gemini Coach Plan: {e}")
        return None
