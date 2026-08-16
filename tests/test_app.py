import pytest
from app import create_app
from app.models import db, User, Goal, FitnessTask, GeminiCoachPlan

@pytest.fixture
def client():
    app = create_app("development")
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()


def test_full_system_features(client):
    # 1. Unauthenticated root access redirects to /login
    unauth_res = client.get("/")
    assert unauth_res.status_code == 302
    assert "/login" in unauth_res.headers.get("Location", "")

    # 2. Registration
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "end_to_end_user",
        "email": "e2e@fitness.io",
        "password": "strongpassword123"
    })
    assert reg_res.status_code == 201
    token = reg_res.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Login
    login_res = client.post("/api/v1/auth/login", json={
        "username": "end_to_end_user",
        "password": "strongpassword123"
    })
    assert login_res.status_code == 200

    # 4. Profile / Me
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.get_json()["user"]["username"] == "end_to_end_user"

    # 5. Log Daily Activities
    step_res = client.post("/api/v1/logs/steps", headers=headers, json={"count": 10500})
    assert step_res.status_code == 201

    hr_res = client.post("/api/v1/logs/heart-rate", headers=headers, json={"bpm": 72})
    assert hr_res.status_code == 201

    cal_res = client.post("/api/v1/logs/calories", headers=headers, json={"burned": 520.5})
    assert cal_res.status_code == 201

    workout_res = client.post("/api/v1/logs/workout", headers=headers, json={
        "type": "Strength Hypertrophy",
        "duration_min": 50,
        "intensity": "high"
    })
    assert workout_res.status_code == 201

    # 6. Summary Aggregation
    summary_res = client.get("/api/v1/logs/summary?days=30", headers=headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.get_json()
    assert summary_data["total_steps"] == 10500

    # 7. Goals CRUD & Progress
    goal_update = client.post("/api/v1/goals", headers=headers, json={
        "step_goal": 12000,
        "calorie_goal": 600.0,
        "active_minutes_goal": 50.0
    })
    assert goal_update.status_code == 200

    progress_res = client.get("/api/v1/goals/progress", headers=headers)
    assert progress_res.status_code == 200
    prog = progress_res.get_json()
    assert prog["steps"]["target"] == 12000
    assert prog["steps"]["current"] == 10500

    # 8. All 4 Monochrome Matplotlib Streaming Charts
    for chart_type in ["steps", "heart_rate", "workout", "heatmap"]:
        chart_res = client.get(f"/api/v1/charts/{chart_type}.png", headers=headers)
        assert chart_res.status_code == 200
        assert chart_res.content_type == "image/png"

    # 9. Gemini Coach Plan Generation with Full Profile Questionnaire
    plan_res = client.post("/api/v1/gemini/coach", headers=headers, json={
        "age": 27,
        "gender": "Male",
        "weight_kg": 85,
        "height_cm": 178,
        "fitness_level": "Intermediate",
        "workout_days_per_week": 4,
        "goal_focus": "Build Lean Muscle & Six Pack Abs",
        "dietary_preference": "High Protein Non-Veg",
        "target_timeline_weeks": 4,
        "injuries_or_limitations": "None"
    })
    assert plan_res.status_code == 200
    plan_data = plan_res.get_json()["plan"]
    assert len(plan_data["exercise_suggestions"]) >= 2
    assert len(plan_data["diet_suggestions"]) >= 3
    assert len(plan_data["timeline"]) >= 4
    assert len(plan_data["tasks"]) >= 6

    # 10. Gemini Tasks Toggle Checkbox
    task_id = plan_data["tasks"][0]["id"]
    toggle_res = client.post(f"/api/v1/gemini/tasks/{task_id}/toggle", headers=headers)
    assert toggle_res.status_code == 200
    assert toggle_res.get_json()["task"]["is_completed"] is True
