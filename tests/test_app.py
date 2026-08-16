import pytest
from app import create_app
from app.models import db, User, Goal

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


def test_auth_workflow(client):
    # 1. Register
    reg_res = client.post("/api/v1/auth/register", json={
        "username": "tester",
        "email": "tester@test.com",
        "password": "password123"
    })
    assert reg_res.status_code == 201
    reg_data = reg_res.get_json()
    assert "access_token" in reg_data
    token = reg_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Login
    login_res = client.post("/api/v1/auth/login", json={
        "username": "tester",
        "password": "password123"
    })
    assert login_res.status_code == 200

    # 3. Log Steps
    step_res = client.post("/api/v1/logs/steps", headers=headers, json={"count": 8000})
    assert step_res.status_code == 201

    # 4. Log Heart Rate
    hr_res = client.post("/api/v1/logs/heart-rate", headers=headers, json={"bpm": 74})
    assert hr_res.status_code == 201

    # 5. Log Workout
    w_res = client.post("/api/v1/logs/workout", headers=headers, json={
        "type": "Running",
        "duration_min": 35,
        "intensity": "high"
    })
    assert w_res.status_code == 201

    # 6. Check Goals Progress
    progress_res = client.get("/api/v1/goals/progress", headers=headers)
    assert progress_res.status_code == 200
    prog_data = progress_res.get_json()
    assert prog_data["steps"]["current"] == 8000

    # 7. Check Matplotlib PNG Charts
    chart_res = client.get("/api/v1/charts/steps.png", headers=headers)
    assert chart_res.status_code == 200
    assert chart_res.content_type == "image/png"

    hr_chart_res = client.get("/api/v1/charts/heart_rate.png", headers=headers)
    assert hr_chart_res.status_code == 200
    assert hr_chart_res.content_type == "image/png"

    # 8. Check AI Insights (cached / generated fallback)
    ai_res = client.post("/api/v1/ai/insights", headers=headers)
    assert ai_res.status_code == 200
    ai_data = ai_res.get_json()
    assert "summary" in ai_data["insight"]
    assert "recommendation" in ai_data["insight"]
