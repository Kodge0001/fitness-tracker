from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # User Profile & Assessment Details for Gemini AI Customization
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    height_cm = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    fitness_level = db.Column(db.String(30), default="Intermediate")  # Beginner, Intermediate, Advanced, Athlete
    goal_focus = db.Column(db.String(100), default="Build Lean Muscle & Fat Loss")  # Muscle, Fat Loss, Endurance, Abs, General
    dietary_preference = db.Column(db.String(50), default="High Protein Non-Veg")  # Non-Veg, Vegetarian, Vegan, Keto, High Protein
    workout_days_per_week = db.Column(db.Integer, default=4)
    injuries_or_limitations = db.Column(db.String(255), default="None")
    target_timeline_weeks = db.Column(db.Integer, default=4)

    # Relationships
    heart_rates = db.relationship("HeartRateLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    steps = db.relationship("StepLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    calories = db.relationship("CalorieLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    workouts = db.relationship("WorkoutLog", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    goals = db.relationship("Goal", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    ai_insights = db.relationship("AIInsightCache", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str):
        self.password_hash = bcrypt.generate_password_hash(password.strip()).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password.strip())

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "age": self.age,
            "gender": self.gender,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "fitness_level": self.fitness_level,
            "goal_focus": self.goal_focus,
            "dietary_preference": self.dietary_preference,
            "workout_days_per_week": self.workout_days_per_week,
            "injuries_or_limitations": self.injuries_or_limitations,
            "target_timeline_weeks": self.target_timeline_weeks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class HeartRateLog(db.Model):
    __tablename__ = "heart_rate_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    bpm = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bpm": self.bpm,
            "timestamp": self.timestamp.isoformat(),
        }


class StepLog(db.Model):
    __tablename__ = "step_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    count = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "count": self.count,
            "timestamp": self.timestamp.isoformat(),
        }


class CalorieLog(db.Model):
    __tablename__ = "calorie_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    burned = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "burned": self.burned,
            "timestamp": self.timestamp.isoformat(),
        }


class WorkoutLog(db.Model):
    __tablename__ = "workout_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    type = db.Column(db.String(80), nullable=False)  # Running, Cycling, HIIT, Strength, Yoga, Swimming, etc.
    duration_min = db.Column(db.Float, nullable=False)
    intensity = db.Column(db.String(20), nullable=False, default="medium")  # low, medium, high
    timestamp = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "duration_min": self.duration_min,
            "intensity": self.intensity,
            "timestamp": self.timestamp.isoformat(),
        }


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    step_goal = db.Column(db.Integer, nullable=False, default=10000)
    calorie_goal = db.Column(db.Float, nullable=False, default=500.0)
    active_minutes_goal = db.Column(db.Float, nullable=False, default=45.0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "step_goal": self.step_goal,
            "calorie_goal": self.calorie_goal,
            "active_minutes_goal": self.active_minutes_goal,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AIInsightCache(db.Model):
    __tablename__ = "ai_insight_caches"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    summary = db.Column(db.Text, nullable=False)
    trend = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text, nullable=False)
    risk_flags = db.Column(db.JSON, nullable=False, default=list)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "summary": self.summary,
            "trend": self.trend,
            "recommendation": self.recommendation,
            "risk_flags": self.risk_flags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class GeminiCoachPlan(db.Model):
    __tablename__ = "gemini_coach_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False, default="Personalized Gemini Fitness & Nutrition Program")
    focus_goal = db.Column(db.String(100), nullable=False, default="Overall Fitness & Body Recomposition")
    exercise_suggestions = db.Column(db.JSON, nullable=False, default=list)
    diet_suggestions = db.Column(db.JSON, nullable=False, default=list)
    timeline = db.Column(db.JSON, nullable=False, default=list)  # 4-week structured milestones
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    # Relationships
    tasks = db.relationship("FitnessTask", backref="coach_plan", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "focus_goal": self.focus_goal,
            "exercise_suggestions": self.exercise_suggestions,
            "diet_suggestions": self.diet_suggestions,
            "timeline": self.timeline,
            "tasks": [t.to_dict() for t in self.tasks.order_by(FitnessTask.day_order.asc(), FitnessTask.id.asc()).all()],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FitnessTask(db.Model):
    __tablename__ = "fitness_tasks"

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("gemini_coach_plans.id"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False, default="exercise")  # exercise, diet, habit, recovery
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_metric = db.Column(db.String(100), nullable=True)
    day_order = db.Column(db.Integer, default=1)
    is_completed = db.Column(db.Boolean, default=False, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "user_id": self.user_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "target_metric": self.target_metric,
            "day_order": self.day_order,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
