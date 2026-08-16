import io
from datetime import datetime, timezone, timedelta
import matplotlib
# Headless rendering backend
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from app.models import StepLog, HeartRateLog, CalorieLog, WorkoutLog, Goal

# Monochromatic Black and White Theme Palette
BG_COLOR = "#000000"         # Pure Pitch Black
CARD_BG = "#0D0D0D"          # Deep Charcoal Black
SURFACE_BG = "#1A1A1A"       # Dark Gray Accent
TEXT_MAIN = "#FFFFFF"        # Pure White
TEXT_MUTED = "#A0A0A0"       # Neutral Silver Gray
BORDER_COLOR = "#333333"     # Medium Charcoal Border
LINE_WHITE = "#FAFAFA"       # Sharp Crisp White
ACCENT_GRAY = "#888888"      # Mid Gray


def set_monochrome_styling(fig, ax):
    """Apply high-contrast black & white minimalist styling to Matplotlib figures."""
    fig.patch.set_facecolor(CARD_BG)
    ax.set_facecolor(BG_COLOR)
    ax.tick_params(colors=TEXT_MAIN, labelsize=9)
    ax.xaxis.label.set_color(TEXT_MAIN)
    ax.yaxis.label.set_color(TEXT_MAIN)
    ax.title.set_color(TEXT_MAIN)
    for spine in ax.spines.values():
        spine.set_color(BORDER_COLOR)
        spine.set_linewidth(1.2)
    ax.grid(True, linestyle=":", alpha=0.35, color=BORDER_COLOR)


def render_empty_chart(title: str, message: str = "No data recorded in last 30 days") -> io.BytesIO:
    """Render a clean monochrome placeholder chart."""
    fig, ax = plt.subplots(figsize=(7, 3.8), dpi=140)
    set_monochrome_styling(fig, ax)
    ax.text(0.5, 0.5, message, color=TEXT_MUTED, fontsize=11, ha="center", va="center", transform=ax.transAxes)
    ax.set_title(title, fontsize=12, pad=12, fontweight="bold", color=TEXT_MAIN)
    ax.set_xticks([])
    ax.set_yticks([])
    
    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format="png", facecolor=CARD_BG, edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_steps_bar_chart(user_id: int) -> io.BytesIO:
    """1. Bar chart: Daily step count vs step goal in Black & White."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    step_logs = (
        StepLog.query.filter(StepLog.user_id == user_id, StepLog.timestamp >= cutoff)
        .order_by(StepLog.timestamp.asc())
        .all()
    )
    goal = Goal.query.filter_by(user_id=user_id).first()
    step_goal = goal.step_goal if goal else 10000

    if not step_logs:
        return render_empty_chart("Daily Steps vs Goal", "No step logs recorded for the last 30 days")

    daily_steps = {}
    for s in step_logs:
        d = s.timestamp.strftime("%b %d")
        daily_steps[d] = daily_steps.get(d, 0) + s.count

    dates = list(daily_steps.keys())
    counts = list(daily_steps.values())

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=140)
    set_monochrome_styling(fig, ax)

    # Black and white contrast: Pure White for goal reached, Silver Gray for pending
    bar_colors = [LINE_WHITE if c >= step_goal else "#71717A" for c in counts]
    bars = ax.bar(dates, counts, color=bar_colors, width=0.6, alpha=0.95, edgecolor="none")

    # Dotted white goal line
    ax.axhline(step_goal, color="#E4E4E7", linestyle="--", linewidth=1.5, label=f"Target Goal ({step_goal:,} steps)")

    ax.set_title("Daily Step Count vs Target (30 Days)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Step Count", fontsize=9.5)
    ax.legend(facecolor=CARD_BG, edgecolor=BORDER_COLOR, labelcolor=TEXT_MAIN, loc="upper left", fontsize=8.5)

    ax.set_xticks(range(len(dates)))
    step_jump = max(1, len(dates) // 10)
    ax.set_xticks(range(0, len(dates), step_jump))
    ax.set_xticklabels([dates[i] for i in range(0, len(dates), step_jump)], rotation=30, ha="right")

    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format="png", facecolor=CARD_BG, edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_heart_rate_line_chart(user_id: int) -> io.BytesIO:
    """2. Line chart: Heart rate trend in monochrome high-contrast."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    hr_logs = (
        HeartRateLog.query.filter(HeartRateLog.user_id == user_id, HeartRateLog.timestamp >= cutoff)
        .order_by(HeartRateLog.timestamp.asc())
        .all()
    )

    if not hr_logs:
        return render_empty_chart("Heart Rate Trend (BPM)", "No heart rate logs found")

    timestamps = [h.timestamp for h in hr_logs]
    bpms = [h.bpm for h in hr_logs]

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=140)
    set_monochrome_styling(fig, ax)

    ax.plot(timestamps, bpms, color=LINE_WHITE, linewidth=2.0, marker="o", markersize=4, markerfacecolor="#FFFFFF", markeredgecolor=BG_COLOR, label="BPM Readout")
    ax.fill_between(timestamps, bpms, min(bpms) - 5, color="#FFFFFF", alpha=0.10)

    avg_bpm = sum(bpms) / len(bpms)
    ax.axhline(avg_bpm, color=ACCENT_GRAY, linestyle=":", linewidth=1.5, label=f"Average ({avg_bpm:.1f} BPM)")

    ax.set_title("Heart Rate Trend Over Time (30 Days)", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Heart Rate (BPM)", fontsize=9.5)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    fig.autofmt_xdate(rotation=30)
    ax.legend(facecolor=CARD_BG, edgecolor=BORDER_COLOR, labelcolor=TEXT_MAIN, loc="upper right", fontsize=8.5)

    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format="png", facecolor=CARD_BG, edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_workout_scatter_chart(user_id: int) -> io.BytesIO:
    """3. Scatter chart: Workout duration vs calories burned."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    workouts = (
        WorkoutLog.query.filter(WorkoutLog.user_id == user_id, WorkoutLog.timestamp >= cutoff)
        .order_by(WorkoutLog.timestamp.asc())
        .all()
    )

    if not workouts:
        return render_empty_chart("Workout Duration vs Calories Burned", "No workout logs found")

    durations = [w.duration_min for w in workouts]
    calories = []
    for w in workouts:
        rate = 11.5 if w.intensity == "high" else (8.0 if w.intensity == "medium" else 5.5)
        calories.append(round(w.duration_min * rate))

    types = [w.type for w in workouts]
    unique_types = list(set(types))
    shades = ["#FFFFFF", "#D4D4D8", "#A1A1AA", "#71717A", "#52525B", "#E4E4E7"]
    color_map = {t: shades[i % len(shades)] for i, t in enumerate(unique_types)}

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=140)
    set_monochrome_styling(fig, ax)

    for t in unique_types:
        x = [durations[i] for i in range(len(workouts)) if types[i] == t]
        y = [calories[i] for i in range(len(workouts)) if types[i] == t]
        ax.scatter(x, y, label=t, color=color_map[t], s=75, alpha=0.9, edgecolors="#000000", linewidths=0.8)

    if len(durations) > 1:
        z = np.polyfit(durations, calories, 1)
        p = np.poly1d(z)
        x_line = np.linspace(min(durations), max(durations), 100)
        ax.plot(x_line, p(x_line), color="#71717A", linestyle="--", linewidth=1.2, label="Trendline")

    ax.set_title("Workout Duration vs Calories Burned", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Duration (Minutes)", fontsize=9.5)
    ax.set_ylabel("Calories Burned (kcal)", fontsize=9.5)
    ax.legend(facecolor=CARD_BG, edgecolor=BORDER_COLOR, labelcolor=TEXT_MAIN, loc="upper left", fontsize=8.5)

    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format="png", facecolor=CARD_BG, edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def generate_heatmap_chart(user_id: int) -> io.BytesIO:
    """4. Heatmap: Activity intensity by hour vs day-of-week in monochrome grayscale."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    workouts = WorkoutLog.query.filter(WorkoutLog.user_id == user_id, WorkoutLog.timestamp >= cutoff).all()
    steps = StepLog.query.filter(StepLog.user_id == user_id, StepLog.timestamp >= cutoff).all()

    matrix = np.zeros((7, 24))

    for w in workouts:
        day_idx = w.timestamp.weekday()
        hour_idx = w.timestamp.hour
        weight = 3 if w.intensity == "high" else (2 if w.intensity == "medium" else 1)
        matrix[day_idx][hour_idx] += weight * (w.duration_min / 15.0)

    for s in steps:
        day_idx = s.timestamp.weekday()
        hour_idx = s.timestamp.hour
        matrix[day_idx][hour_idx] += (s.count / 1000.0)

    fig, ax = plt.subplots(figsize=(7.5, 4.0), dpi=140)
    set_monochrome_styling(fig, ax)

    # Monochromatic colormap: Black -> Dark Gray -> Light Gray -> Pure White
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "mono_fitness", ["#0D0D0D", "#27272A", "#52525B", "#A1A1AA", "#FFFFFF"]
    )

    im = ax.imshow(matrix, cmap=cmap, aspect="auto", interpolation="nearest")

    days_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    ax.set_yticks(range(7))
    ax.set_yticklabels(days_labels)

    ax.set_xticks(range(0, 24, 3))
    ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 3)], rotation=0)

    ax.set_title("Activity Intensity Heatmap (Hour vs Day)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Hour of Day", fontsize=9.5)
    ax.set_ylabel("Day of Week", fontsize=9.5)

    cbar = fig.colorbar(im, ax=ax, orientation="vertical", pad=0.03, shrink=0.85)
    cbar.ax.tick_params(colors=TEXT_MAIN, labelsize=8)
    cbar.outline.set_edgecolor(BORDER_COLOR)
    cbar.set_label("Intensity Level", color=TEXT_MAIN, fontsize=8.5)

    img_buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(img_buf, format="png", facecolor=CARD_BG, edgecolor="none", bbox_inches="tight")
    plt.close(fig)
    img_buf.seek(0)
    return img_buf


def render_chart_by_type(chart_type: str, user_id: int) -> io.BytesIO:
    """Route chart type to appropriate monochrome matplotlib renderer."""
    chart_type = chart_type.lower()
    if chart_type in ["steps", "step", "steps_vs_goal", "bar"]:
        return generate_steps_bar_chart(user_id)
    elif chart_type in ["heart_rate", "heart-rate", "hr", "line"]:
        return generate_heart_rate_line_chart(user_id)
    elif chart_type in ["workout", "workouts", "scatter", "calories_vs_duration"]:
        return generate_workout_scatter_chart(user_id)
    elif chart_type in ["heatmap", "activity_heatmap", "intensity"]:
        return generate_heatmap_chart(user_id)
    else:
        return render_empty_chart("Chart Not Found", f"Unknown chart type: {chart_type}")
