import random
from datetime import datetime, timezone, timedelta
from app import create_app
from app.models import db, User, Goal, StepLog, HeartRateLog, CalorieLog, WorkoutLog, AIInsightCache

app = create_app("development")

def seed_database():
    with app.app_context():
        print("🌱 Seeding database with realistic 30-day fitness demo data...")
        db.create_all()

        # Check if demo user already exists
        demo_user = User.query.filter_by(email="alex@fitnesstracker.io").first()
        if not demo_user:
            demo_user = User(
                username="alex_athlete",
                email="alex@fitnesstracker.io",
            )
            demo_user.set_password("fitness123")
            db.session.add(demo_user)
            db.session.commit()
            print(f"✅ Created Demo User: alex_athlete (email: alex@fitnesstracker.io, password: fitness123)")

        # Clear existing logs for a clean realistic 30-day history
        StepLog.query.filter_by(user_id=demo_user.id).delete()
        HeartRateLog.query.filter_by(user_id=demo_user.id).delete()
        CalorieLog.query.filter_by(user_id=demo_user.id).delete()
        WorkoutLog.query.filter_by(user_id=demo_user.id).delete()
        AIInsightCache.query.filter_by(user_id=demo_user.id).delete()
        Goal.query.filter_by(user_id=demo_user.id).delete()

        # Add Goals
        goal = Goal(
            user_id=demo_user.id,
            step_goal=10000,
            calorie_goal=650.0,
            active_minutes_goal=50.0,
        )
        db.session.add(goal)

        now = datetime.now(timezone.utc)
        workout_types = [
            ("Running", 30, 45, "high"),
            ("Strength Training", 45, 60, "medium"),
            ("HIIT", 25, 40, "high"),
            ("Cycling", 40, 75, "medium"),
            ("Yoga & Mobility", 30, 45, "low"),
            ("Swimming", 35, 50, "high"),
            ("Brisk Walking", 30, 45, "low")
        ]

        # Generate 30 days of data
        for day_offset in range(29, -1, -1):
            day_date = now - timedelta(days=day_offset)

            # 1. Step logs: 2-3 batches per day (morning, afternoon, evening)
            daily_step_target = random.randint(7500, 14500)
            # Morning walk
            m_steps = int(daily_step_target * random.uniform(0.3, 0.45))
            db.session.add(StepLog(
                user_id=demo_user.id,
                count=m_steps,
                timestamp=day_date.replace(hour=8, minute=random.randint(10, 50))
            ))
            # Afternoon / Evening steps
            e_steps = daily_step_target - m_steps
            db.session.add(StepLog(
                user_id=demo_user.id,
                count=e_steps,
                timestamp=day_date.replace(hour=18, minute=random.randint(10, 50))
            ))

            # 2. Heart Rate logs: 4-6 checks per day (Resting 60-72, Active 115-165)
            # Resting HR (morning)
            db.session.add(HeartRateLog(
                user_id=demo_user.id,
                bpm=random.randint(58, 68),
                timestamp=day_date.replace(hour=7, minute=15)
            ))
            # Midday HR
            db.session.add(HeartRateLog(
                user_id=demo_user.id,
                bpm=random.randint(72, 85),
                timestamp=day_date.replace(hour=13, minute=30)
            ))

            # 3. Workouts (5-6 days per week)
            if random.random() > 0.18:
                w_choice = random.choice(workout_types)
                w_type = w_choice[0]
                duration = random.randint(w_choice[1], w_choice[2])
                intensity = w_choice[3]
                w_time = day_date.replace(hour=random.choice([7, 17, 19]), minute=random.randint(0, 45))

                w_log = WorkoutLog(
                    user_id=demo_user.id,
                    type=w_type,
                    duration_min=duration,
                    intensity=intensity,
                    timestamp=w_time
                )
                db.session.add(w_log)

                # Workout active HR
                active_bpm = random.randint(135, 170) if intensity == "high" else random.randint(110, 140)
                db.session.add(HeartRateLog(
                    user_id=demo_user.id,
                    bpm=active_bpm,
                    timestamp=w_time + timedelta(minutes=duration // 2)
                ))

                # Calorie burned for workout
                rate = 11.5 if intensity == "high" else (8.0 if intensity == "medium" else 5.5)
                w_cals = round(duration * rate * random.uniform(0.9, 1.1), 1)
                db.session.add(CalorieLog(
                    user_id=demo_user.id,
                    burned=w_cals,
                    timestamp=w_time
                ))

            # Basal & daily general calories
            general_cals = round(random.uniform(250, 450), 1)
            db.session.add(CalorieLog(
                user_id=demo_user.id,
                burned=general_cals,
                timestamp=day_date.replace(hour=21, minute=0)
            ))

        # Add initial sample AI insight cache
        sample_insight = AIInsightCache(
            user_id=demo_user.id,
            summary="Outstanding 30-day performance. You maintained consistent cardiovascular engagement with an average of 10,850 daily steps and regular strength & endurance sessions.",
            trend="Peak Cardiovascular Momentum & Progressive Overload",
            recommendation="Incorporate a dedicated active recovery day (zone 2 walk or mobility) on Wednesdays to prevent central nervous system fatigue.",
            risk_flags=["Slightly elevated peak heart rate during high-intensity HIIT intervals; ensure 2-3 minute hydration rest intervals."],
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(sample_insight)

        db.session.commit()
        print("🎉 Database seeded successfully!")
        print("👤 Demo User: alex@fitnesstracker.io / fitness123")


if __name__ == "__main__":
    seed_database()
