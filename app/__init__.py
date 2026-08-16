import os
from flask import Flask, render_template, redirect, url_for, request
from flask_jwt_extended import JWTManager, get_jwt_identity, verify_jwt_in_request
from flask_cors import CORS
from app.models import db, bcrypt, User, Goal
from config import config_by_name

jwt = JWTManager()


def create_app(config_name=None):
    if not config_name:
        config_name = os.getenv("FLASK_ENV", "development")

    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_dir = os.path.join(base_dir, "templates")
    static_dir = os.path.join(base_dir, "static")

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Detect Vercel/Lambda serverless execution runtime
    is_serverless = bool(
        os.path.exists("/var/task")
        or "AWS_LAMBDA_FUNCTION_NAME" in os.environ
        or "VERCEL" in os.environ
        or "/var/task" in os.path.abspath(__file__)
    )

    db_url = os.getenv("DATABASE_URL")
    if db_url and db_url.strip():
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    elif is_serverless:
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/fitness.db"

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)

    # Register API blueprints under /api/v1/
    from app.auth import auth_bp
    from app.logs import logs_bp

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(logs_bp, url_prefix="/api/v1")

    # JWT Error handlers
    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        # If API request return JSON, if browser web page redirect to login
        if request.path.startswith("/api/"):
            return {"error": "Authorization token missing or invalid"}, 401
        return redirect(url_for("login_page"))

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        if request.path.startswith("/api/"):
            return {"error": "Token has expired"}, 401
        return redirect(url_for("login_page"))

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        if request.path.startswith("/api/"):
            return {"error": "Invalid token provided"}, 401
        return redirect(url_for("login_page"))

    # Frontend Page Routes (Jinja2)
    @app.route("/")
    def dashboard_page():
        user = None
        try:
            verify_jwt_in_request(optional=False, locations=["cookies", "headers"])
            user_id = get_jwt_identity()
            if user_id:
                user = db.session.get(User, int(user_id))
        except Exception:
            user = None

        if not user:
            return redirect(url_for("login_page"))

        # Fetch goals & user metrics
        goals = Goal.query.filter_by(user_id=user.id).first()
        return render_template("dashboard.html", user=user, goals=goals)

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/register")
    def register_page():
        return render_template("register.html")

    @app.route("/log")
    def log_page():
        user = None
        try:
            verify_jwt_in_request(optional=False, locations=["cookies", "headers"])
            user_id = get_jwt_identity()
            if user_id:
                user = db.session.get(User, int(user_id))
        except Exception:
            user = None

        if not user:
            return redirect(url_for("login_page"))
        return render_template("log_data.html", user=user)

    @app.route("/goals")
    def goals_page():
        user = None
        try:
            verify_jwt_in_request(optional=False, locations=["cookies", "headers"])
            user_id = get_jwt_identity()
            if user_id:
                user = db.session.get(User, int(user_id))
        except Exception:
            user = None

        if not user:
            return redirect(url_for("login_page"))
        goals = Goal.query.filter_by(user_id=user.id).first()
        return render_template("goals.html", user=user, goals=goals)

    # Create tables automatically on startup
    with app.app_context():
        db.create_all()

    return app
