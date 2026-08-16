// Client-side interactions & API bindings for Black & White Fitness Tracker with Gemini AI Coach

document.addEventListener("DOMContentLoaded", () => {
  initDashboard();
  initForms();
  initAssessmentModal();
});

function initDashboard() {
  const refreshAiBtn = document.getElementById("btn-refresh-ai");
  if (refreshAiBtn) {
    refreshAiBtn.addEventListener("click", refreshAiInsights);
  }

  const refreshGeminiBtn = document.getElementById("btn-refresh-gemini");
  if (refreshGeminiBtn) {
    refreshGeminiBtn.addEventListener("click", openAssessmentModal);
  }

  const openAssessBtn = document.getElementById("btn-open-assessment");
  if (openAssessBtn) {
    openAssessBtn.addEventListener("click", openAssessmentModal);
  }

  if (document.getElementById("gemini-coach-section")) {
    loadGoalsProgress();
    loadAiInsights();
    loadGeminiCoachPlan();
  }
}

// -------------------------------------------------------------
// Assessment Modal Controls
// -------------------------------------------------------------
function openAssessmentModal() {
  const modal = document.getElementById("assessment-modal");
  if (modal) modal.classList.add("active");
}

function closeAssessmentModal() {
  const modal = document.getElementById("assessment-modal");
  if (modal) modal.classList.remove("active");
}

function initAssessmentModal() {
  const form = document.getElementById("gemini-assessment-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const submitBtn = document.getElementById("btn-submit-assessment");
    const originalText = submitBtn.innerHTML;
    submitBtn.disabled = true;
    submitBtn.innerHTML = `<span>⏳</span> Generating Plan with Gemini AI...`;

    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());

    try {
      const res = await fetch("/api/v1/gemini/coach", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok && data.plan) {
        renderGeminiCoachPlan(data.plan);
        closeAssessmentModal();
      } else {
        alert(data.error || "Failed to generate plan. Please try again.");
      }
    } catch (err) {
      console.error("Error generating assessment plan:", err);
      alert("Network error. Please try again.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalText;
    }
  });

  initQuickLogModal();
}

// -------------------------------------------------------------
// Quick Activity Log Controls
// -------------------------------------------------------------
function openQuickLogModal() {
  const modal = document.getElementById("quick-log-modal");
  if (modal) modal.classList.add("active");
}

function closeQuickLogModal() {
  const modal = document.getElementById("quick-log-modal");
  if (modal) modal.classList.remove("active");
}

function toggleQuickLogFields() {
  const type = document.getElementById("quick-log-type").value;
  document.getElementById("q-field-steps").style.display = type === "steps" ? "block" : "none";
  document.getElementById("q-field-workout").style.display = type === "workout" ? "block" : "none";
  document.getElementById("q-field-heart-rate").style.display = type === "heart_rate" ? "block" : "none";
  document.getElementById("q-field-calories").style.display = type === "calories" ? "block" : "none";
}

function initQuickLogModal() {
  const form = document.getElementById("quick-log-form");
  if (!form) return;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const alertEl = document.getElementById("quick-log-alert");
    const submitBtn = document.getElementById("btn-submit-quick-log");
    alertEl.style.display = "none";

    const type = document.getElementById("quick-log-type").value;
    let endpoint = "";
    let payload = {};

    if (type === "steps") {
      endpoint = "/api/v1/logs/steps";
      payload = { count: Number(document.getElementById("q-step-count").value) };
    } else if (type === "workout") {
      endpoint = "/api/v1/logs/workout";
      payload = {
        type: document.getElementById("q-workout-type").value || "Workout Session",
        duration_min: Number(document.getElementById("q-workout-duration").value || 30),
        intensity: document.getElementById("q-workout-intensity").value || "medium",
      };
    } else if (type === "heart_rate") {
      endpoint = "/api/v1/logs/heart-rate";
      payload = { bpm: Number(document.getElementById("q-hr-bpm").value) };
    } else if (type === "calories") {
      endpoint = "/api/v1/logs/calories";
      payload = { burned: Number(document.getElementById("q-cal-burned").value) };
    }

    submitBtn.disabled = true;
    submitBtn.innerText = "Saving...";

    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();

      if (res.ok) {
        form.reset();
        closeQuickLogModal();
        // Refresh goal metrics and charts
        loadGoalsProgress();
        // Reload chart images by busting cache
        document.querySelectorAll(".chart-container img").forEach((img) => {
          const baseSrc = img.src.split("?")[0];
          img.src = `${baseSrc}?t=${Date.now()}`;
        });
      } else {
        alertEl.innerText = data.error || "Failed to log activity.";
        alertEl.style.display = "block";
      }
    } catch (err) {
      alertEl.innerText = "Network error. Please try again.";
      alertEl.style.display = "block";
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = "Save Activity";
    }
  });
}

async function loadGoalsProgress() {
  try {
    const res = await fetch("/api/v1/goals/progress");
    if (res.ok) {
      const data = await res.json();
      updateGoalUI("steps", data.steps);
      updateGoalUI("calories", data.calories);
      updateGoalUI("active", data.active_minutes);
    }
  } catch (err) {
    console.error("Failed to load goal progress:", err);
  }
}

function updateGoalUI(type, metric) {
  const curEl = document.getElementById(`${type}-current`);
  const tgtEl = document.getElementById(`${type}-target`);
  const pctEl = document.getElementById(`${type}-pct`);
  const barEl = document.getElementById(`${type}-bar`);

  if (curEl) curEl.innerText = metric.current.toLocaleString();
  if (tgtEl) tgtEl.innerText = metric.target.toLocaleString();
  if (pctEl) pctEl.innerText = `${metric.percent}%`;
  if (barEl) barEl.style.width = `${Math.min(metric.percent, 100)}%`;
}

// -------------------------------------------------------------
// Gemini AI Coach (Diet, Exercise, Timeline & Tasks)
// -------------------------------------------------------------
async function loadGeminiCoachPlan() {
  const container = document.getElementById("gemini-coach-section");
  if (!container) return;

  try {
    const res = await fetch("/api/v1/gemini/coach");
    if (res.ok) {
      const data = await res.json();
      if (data.plan) {
        renderGeminiCoachPlan(data.plan);
      }
    }
  } catch (err) {
    console.error("Failed to load Gemini Coach plan:", err);
  }
}

async function refreshGeminiCoachPlan(goalText = "") {
  const btn = document.getElementById("btn-refresh-gemini");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳</span> Consulting Gemini AI...`;
  }

  try {
    const res = await fetch("/api/v1/gemini/coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goalText || "" }),
    });
    const data = await res.json();
    if (res.ok && data.plan) {
      renderGeminiCoachPlan(data.plan);
    }
  } catch (err) {
    console.error("Error refreshing Gemini coach plan:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>⚡</span> Update Gemini AI Plan`;
    }
  }
}

function renderGeminiCoachPlan(plan) {
  const titleEl = document.getElementById("gemini-plan-title");
  const goalEl = document.getElementById("gemini-plan-goal");
  const exerciseContainer = document.getElementById("gemini-exercise-list");
  const dietContainer = document.getElementById("gemini-diet-list");
  const timelineContainer = document.getElementById("gemini-timeline-list");
  const tasksContainer = document.getElementById("gemini-tasks-list");

  if (titleEl) titleEl.innerText = plan.title || "Gemini Personalized Fitness Blueprint";
  if (goalEl) goalEl.innerText = `Focus: ${plan.focus_goal || "General Health & Body Recomposition"}`;

  // 1. Exercise Suggestions
  if (exerciseContainer) {
    exerciseContainer.innerHTML = "";
    (plan.exercise_suggestions || []).forEach((ex) => {
      exerciseContainer.innerHTML += `
        <div class="suggestion-box">
          <h3>🏋️ ${ex.phase || "Exercise Phase"} • <span style="font-weight: 400; color: var(--text-muted);">${ex.focus || ""}</span></h3>
          <p>${ex.details || ""}</p>
          <div class="suggestion-sub">
            <strong>Cardio:</strong> ${ex.cardio || "Zone 2 aerobic base"}<br>
            <strong>Recovery:</strong> ${ex.recovery || "Mobility & stretching"}
          </div>
        </div>
      `;
    });
  }

  // 2. Diet & Nutrition Suggestions
  if (dietContainer) {
    dietContainer.innerHTML = "";
    (plan.diet_suggestions || []).forEach((d) => {
      dietContainer.innerHTML += `
        <div class="suggestion-box">
          <h3>🥗 ${d.title || "Nutrition Strategy"}</h3>
          <p>${d.guideline || ""}</p>
          <div class="suggestion-sub">
            <strong>Timing & Hydration:</strong> ${d.timing || "Consistent daily distribution"}
          </div>
        </div>
      `;
    });
  }

  // 3. 4-Week Timeline
  if (timelineContainer) {
    timelineContainer.innerHTML = "";
    (plan.timeline || []).forEach((t, idx) => {
      timelineContainer.innerHTML += `
        <div class="timeline-item">
          <div class="timeline-indicator">${idx + 1}</div>
          <div class="timeline-content">
            <h4>${t.week || `Phase ${idx + 1}`}</h4>
            <p>${t.milestone || ""}</p>
            <span class="timeline-target">🎯 Milestone Target: ${t.target || "Completed"}</span>
          </div>
        </div>
      `;
    });
  }

  // 4. Actionable Tasks Checklist
  if (tasksContainer) {
    tasksContainer.innerHTML = "";
    (plan.tasks || []).forEach((task) => {
      tasksContainer.innerHTML += `
        <div class="task-item ${task.is_completed ? "completed" : ""}" id="task-row-${task.id}">
          <input type="checkbox" class="task-checkbox" id="task-cb-${task.id}" ${task.is_completed ? "checked" : ""} onchange="toggleTaskStatus(${task.id})">
          <div class="task-text">
            <h5>${task.title}</h5>
            <p>${task.description || ""}</p>
          </div>
          <span class="task-badge">${task.category} ${task.target_metric ? `• ${task.target_metric}` : ""}</span>
        </div>
      `;
    });
  }
}

async function toggleTaskStatus(taskId) {
  const row = document.getElementById(`task-row-${taskId}`);
  const cb = document.getElementById(`task-cb-${taskId}`);
  try {
    const res = await fetch(`/api/v1/gemini/tasks/${taskId}/toggle`, { method: "POST" });
    const data = await res.json();
    if (res.ok && data.task) {
      if (data.task.is_completed) {
        row.classList.add("completed");
        cb.checked = true;
      } else {
        row.classList.remove("completed");
        cb.checked = false;
      }
    }
  } catch (err) {
    console.error("Failed to toggle task:", err);
  }
}

// -------------------------------------------------------------
// Biometrics AI Insights
// -------------------------------------------------------------
async function loadAiInsights() {
  try {
    const res = await fetch("/api/v1/ai/insights");
    if (res.ok) {
      const data = await res.json();
      renderAiInsightData(data.insight, data.cached);
    }
  } catch (err) {
    console.error("AI Insight fetch error:", err);
  }
}

async function refreshAiInsights() {
  const btn = document.getElementById("btn-refresh-ai");
  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<span>⏳</span> Analyzing logs...`;
  }

  try {
    const res = await fetch("/api/v1/ai/insights", { method: "POST" });
    const data = await res.json();
    if (res.ok && data.insight) {
      renderAiInsightData(data.insight, false);
    }
  } catch (err) {
    console.error("Error generating AI insight:", err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<span>✨</span> Refresh Biometrics AI`;
    }
  }
}

function renderAiInsightData(insight, isCached) {
  const summaryEl = document.getElementById("ai-summary-text");
  const recEl = document.getElementById("ai-recommendation-text");
  const trendEl = document.getElementById("ai-trend-val");
  const flagsEl = document.getElementById("ai-flags-list");

  if (summaryEl) summaryEl.innerText = insight.summary || "No summary available.";
  if (recEl) recEl.innerText = insight.recommendation || "Maintain your workout routine and stay hydrated.";
  if (trendEl) trendEl.innerText = insight.trend || "Consistent";
  
  if (flagsEl) {
    flagsEl.innerHTML = "";
    const flags = insight.risk_flags || [];
    if (flags.length === 0) {
      flagsEl.innerHTML = `<li>✓ All biometric readings in optimal ranges</li>`;
    } else {
      flags.forEach((f) => {
        flagsEl.innerHTML += `<li>• ${f}</li>`;
      });
    }
  }
}

// Form Handlers
function initForms() {
  const loginForm = document.getElementById("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertEl = document.getElementById("form-alert");
      alertEl.style.display = "none";

      const formData = new FormData(loginForm);
      const jsonBody = Object.fromEntries(formData.entries());

      try {
        const res = await fetch("/api/v1/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(jsonBody),
        });
        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("access_token", data.access_token);
          window.location.href = "/";
        } else {
          alertEl.innerText = data.error || "Login failed.";
          alertEl.style.display = "block";
        }
      } catch (err) {
        alertEl.innerText = "Network error. Please try again.";
        alertEl.style.display = "block";
      }
    });
  }

  const registerForm = document.getElementById("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertEl = document.getElementById("form-alert");
      alertEl.style.display = "none";

      const formData = new FormData(registerForm);
      const jsonBody = Object.fromEntries(formData.entries());

      try {
        const res = await fetch("/api/v1/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(jsonBody),
        });
        const data = await res.json();

        if (res.ok) {
          localStorage.setItem("access_token", data.access_token);
          window.location.href = "/";
        } else {
          alertEl.innerText = data.error || "Registration failed.";
          alertEl.style.display = "block";
        }
      } catch (err) {
        alertEl.innerText = "Network error. Please try again.";
        alertEl.style.display = "block";
      }
    });
  }

  const logForm = document.getElementById("generic-log-form");
  if (logForm) {
    logForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertEl = document.getElementById("form-alert");
      const logType = document.getElementById("log-type").value;
      alertEl.style.display = "none";

      let endpoint = "";
      let payload = {};

      if (logType === "steps") {
        endpoint = "/api/v1/logs/steps";
        payload = { count: Number(document.getElementById("step-count").value) };
      } else if (logType === "heart_rate") {
        endpoint = "/api/v1/logs/heart-rate";
        payload = { bpm: Number(document.getElementById("hr-bpm").value) };
      } else if (logType === "calories") {
        endpoint = "/api/v1/logs/calories";
        payload = { burned: Number(document.getElementById("cal-burned").value) };
      } else if (logType === "workout") {
        endpoint = "/api/v1/logs/workout";
        payload = {
          type: document.getElementById("workout-type").value,
          duration_min: Number(document.getElementById("workout-duration").value),
          intensity: document.getElementById("workout-intensity").value,
        };
      }

      const customTs = document.getElementById("log-timestamp").value;
      if (customTs) {
        payload.timestamp = new Date(customTs).toISOString();
      }

      try {
        const res = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (res.ok) {
          alertEl.innerText = `Success! ${data.message || "Entry logged"}`;
          alertEl.style.display = "block";
          logForm.reset();
        } else {
          alertEl.innerText = data.error || "Failed to log entry.";
          alertEl.style.display = "block";
        }
      } catch (err) {
        alertEl.innerText = "Network error while saving log.";
        alertEl.style.display = "block";
      }
    });
  }

  const goalsForm = document.getElementById("goals-form");
  if (goalsForm) {
    goalsForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const alertEl = document.getElementById("form-alert");
      alertEl.style.display = "none";

      const payload = {
        step_goal: Number(document.getElementById("input-step-goal").value),
        calorie_goal: Number(document.getElementById("input-cal-goal").value),
        active_minutes_goal: Number(document.getElementById("input-act-goal").value),
      };

      try {
        const res = await fetch("/api/v1/goals", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await res.json();

        if (res.ok) {
          alertEl.innerText = "Daily goals updated successfully!";
          alertEl.style.display = "block";
        } else {
          alertEl.innerText = data.error || "Failed to update goals.";
          alertEl.style.display = "block";
        }
      } catch (err) {
        alertEl.innerText = "Network error while updating goals.";
        alertEl.style.display = "block";
      }
    });
  }
}

async function logoutUser() {
  await fetch("/api/v1/auth/logout", { method: "POST" });
  localStorage.removeItem("access_token");
  window.location.href = "/login";
}
