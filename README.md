# ⚡ PulsePulse AI - Personal Fitness Tracker

A full-stack, production-ready Personal Fitness Tracker web application featuring JWT authentication, rich biometric logging, server-side rendered Matplotlib analytics charts, and 24h-cached AI insights powered by Anthropic's Claude 3.5 Sonnet.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask, Flask-JWT-Extended, Flask-SQLAlchemy, Flask-Bcrypt, Flask-Cors
- **Database**: SQLite (local development) & PostgreSQL (production on Render / Heroku / AWS)
- **Visualization**: Matplotlib (server-side streaming via in-memory `io.BytesIO` PNG endpoints)
- **AI Integration**: Anthropic Claude API (`claude-3-5-sonnet-20241022` / `claude-sonnet-4-6`) with smart 24h caching and resilient offline fallback
- **Frontend**: Responsive Dark Glassmorphism UI (Jinja2 templates, Vanilla CSS, Fetch API)
- **Deployment**: Render.com Blueprint (`render.yaml` & `Procfile` with Gunicorn)

---

## 🚀 Quick Start (Local Setup)

### 1. Clone & Set Up Environment

```bash
# Navigate to project directory
cd "Fitness tracker"

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the sample environment file:
```bash
cp .env.example .env
```

Edit `.env` (optional):
```ini
SECRET_KEY=dev-fitness-secret-key-9988776655
JWT_SECRET_KEY=dev-jwt-fitness-key-1122334455
DATABASE_URL=sqlite:///fitness.db
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

> **Note on Anthropic API Key:**
> If `ANTHROPIC_API_KEY` is not provided, the app automatically falls back to an intelligent, rule-based sports science engine, ensuring 100% functionality without crashes.

### 3. Seed Demo Data (30 Days of Activity)

Populate the database with 30 days of realistic steps, heart rates, workouts, and calories:
```bash
python seed.py
```
This generates a pre-configured demo account:
- **Email / Username**: `alex@fitnesstracker.io` or `alex_athlete`
- **Password**: `fitness123`

### 4. Run the Local Development Server

```bash
python run.py
```

Open your browser at: **[http://localhost:5000](http://localhost:5000)**

---

## 🔑 Obtaining an Anthropic Claude API Key

1. Visit [https://console.anthropic.com/](https://console.anthropic.com/) and register or sign in.
2. Navigate to **API Keys** -> **Create Key**.
3. Copy the generated key (`sk-ant-api03-...`).
4. Paste it into your `.env` file:
   ```ini
   ANTHROPIC_API_KEY=sk-ant-api03-xxxx...
   ```

---

## 📡 API Endpoints Documentation (`/api/v1/`)

All protected endpoints accept either `Authorization: Bearer <access_token>` or the automatic secure HTTP cookie.

### Authentication
- `POST /api/v1/auth/register` — `{ username, email, password }`
- `POST /api/v1/auth/login` — `{ username, password }`
- `POST /api/v1/auth/refresh` — Refresh access token
- `GET  /api/v1/auth/me` — Get current user profile

### Data Logging
- `POST /api/v1/logs/heart-rate` — `{ bpm: 72, timestamp?: "ISO" }`
- `POST /api/v1/logs/steps` — `{ count: 8500, timestamp?: "ISO" }`
- `POST /api/v1/logs/calories` — `{ burned: 420.5, timestamp?: "ISO" }`
- `POST /api/v1/logs/workout` — `{ type: "Running", duration_min: 45, intensity: "high", timestamp?: "ISO" }`
- `GET  /api/v1/logs/summary?days=30` — Aggregated metrics & daily breakdown

### Goal Tracking
- `GET  /api/v1/goals` — Retrieve user daily goals
- `POST /api/v1/goals` — Update daily goals `{ step_goal, calorie_goal, active_minutes_goal }`
- `GET  /api/v1/goals/progress` — Daily % complete for today's targets

### Matplotlib Streaming Charts (In-Memory PNG)
- `GET /api/v1/charts/steps.png` — Bar chart: Daily step count vs target
- `GET /api/v1/charts/heart_rate.png` — Line chart: 30-day heart rate trend
- `GET /api/v1/charts/workout.png` — Scatter chart: Workout duration vs calories burned
- `GET /api/v1/charts/heatmap.png` — Intensity heatmap: 24h vs day-of-week

### AI Insights (Claude 3.5 Sonnet)
- `GET  /api/v1/ai/insights` — Returns cached 24h AI fitness analysis
- `POST /api/v1/ai/insights` — Forces a fresh AI analysis across 30-day logs

---

## 🚀 Hosting on Vercel (Step-by-Step)

This application is fully configured for **Vercel Serverless Functions** via [vercel.json](file:///Users/anuragkodge/Fitness%20tracker/vercel.json) and [api/index.py](file:///Users/anuragkodge/Fitness%20tracker/api/index.py).

### Option A: Deploy via GitHub & Vercel Dashboard (Recommended)

1. **Push your code to a GitHub repository**:
   ```bash
   cd "Fitness tracker"
   git init
   git add .
   git commit -m "Deploy Personal Fitness Tracker to Vercel"
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/fitness-tracker.git
   git push -u origin main
   ```

2. **Import into Vercel**:
   - Go to [vercel.com](https://vercel.com) and log in.
   - Click **"Add New..."** -> **"Project"**.
   - Select your `fitness-tracker` repository from GitHub.
   - Framework Preset: **Other** (Vercel automatically detects `vercel.json`).

3. **Configure Environment Variables in Vercel**:
   Under **Environment Variables**, add the following keys:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = `<any-long-random-string>`
   - `JWT_SECRET_KEY` = `<any-long-random-string>`
   - `GEMINI_API_KEY` = `<your-google-gemini-api-key>` *(from https://aistudio.google.com/)*
   - `ANTHROPIC_API_KEY` = `<your-anthropic-key-optional>`
   - `DATABASE_URL` = `<your-free-cloud-postgres-url>` *(e.g. from Neon.tech, Supabase, or Vercel Postgres)*

4. Click **"Deploy"**!
   Your web app will be live with an active HTTPS URL (e.g. `https://fitness-tracker-xyz.vercel.app`).

---

### Option B: Deploy via Vercel CLI

```bash
# 1. Install Vercel CLI globally (if you have npm/Node.js)
npm install -g vercel

# 2. Deploy
vercel

# 3. Deploy to production
vercel --prod
```

### Method 1: Infrastructure as Code (`render.yaml` Blueprint)

1. Push your repository to GitHub:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Personal Fitness Tracker"
   git remote add origin https://github.com/<your-user>/fitness-tracker.git
   git push -u origin main
   ```
2. Log in to [Render.com](https://render.com).
3. Click **Blueprints** -> **New Blueprint Instance**.
4. Select your GitHub repository.
5. Render will automatically detect `render.yaml` and provision:
   - A **Web Service** running `gunicorn run:app`
   - A **PostgreSQL Database** (`fitness_db`)
   - Automatic environment variables linking `DATABASE_URL`
6. Under **Environment Variables**, supply your `ANTHROPIC_API_KEY`.
7. Click **Apply**!

### Method 2: Manual Web Service Setup on Render

1. Create a free **PostgreSQL Database** on Render:
   - Name: `fitness-postgres-db`
   - Copy the **Internal Database URL**
2. Create a new **Web Service** on Render:
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn run:app --workers 3 --timeout 120`
3. Add Environment Variables in Render Web Service:
   - `FLASK_ENV` = `production`
   - `SECRET_KEY` = `<random-secret-key>`
   - `JWT_SECRET_KEY` = `<random-jwt-secret-key>`
   - `DATABASE_URL` = `<paste-postgres-database-url>`
   - `ANTHROPIC_API_KEY` = `<your-anthropic-key>`
4. Deploy! Run `python seed.py` via the Render SSH Shell if you wish to populate initial demo data on production.

---

## 🧪 Running Automated Tests

```bash
pytest tests/ -v
```
