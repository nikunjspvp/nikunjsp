"""
Advance Quiz Bot — Open Source Project
This project was originally developed by Gagan (github.com/devgaganin).
Reference: https://t.me/advance_quiz_bot
The codebase has been reviewed and verified with the assistance of Claude AI.
"""

from __future__ import annotations

import html
import json
import random
import re
import uuid
from typing import Any

# --------------------------------------------------------------------------
# Small local helpers (no external deps -- stdlib only)
# --------------------------------------------------------------------------


def _esc(value: Any) -> str:
    """Escape arbitrary input for safe interpolation into HTML text nodes."""
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _slug(text: str, fallback: str = "quiz") -> str:
    """Turn a quiz name into a filesystem-safe filename stem."""
    text = (text or "").strip().lower()
    cleaned = "".join(ch if ch.isalnum() else "-" for ch in text)
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:60] or fallback


def _js_literal(value: Any) -> str:
    """Serialize a Python value to a JSON literal safe for embedding in a
    <script> block (also neutralizes '</script>' breakout sequences)."""
    raw = json.dumps(value, ensure_ascii=False)
    return raw.replace("</", "<\\/")


# --------------------------------------------------------------------------
# Shared design system: CSS variables, base layout, dark-mode toggle.
# Both report types import this so the two documents look like one family.
# --------------------------------------------------------------------------

_GOOGLE_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;'
    '600;700;800&display=swap" rel="stylesheet">'
)

_FONT_AWESOME_LINK = (
    '<link rel="stylesheet" '
    'href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/'
    'all.min.css" '
    'integrity="sha512-DTOQO9RWCH3ppGqcWaEA1BIZOC6xxalwEsw9c2QQeAIftl+Vegovlnee1c9QX4TctnWMn13TZye+giMm8e2LwA==" '
    'crossorigin="anonymous" referrerpolicy="no-referrer">'
)

_CHARTJS_SCRIPT = (
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/'
    'chart.umd.min.js" '
    'integrity="sha512-CMF3tQtjOoOJoOKlsS7/2loJlkyctwzSoDK/S40iAB+MqRHFsfKl6dZWRSuwpVXcy77gjPFVmDzoTfjWLmOJvA==" '
    'crossorigin="anonymous" referrerpolicy="no-referrer"></script>'
)

# Core design tokens + resets shared by both page types.
_BASE_CSS = """
:root {
  --color-bg: #f4f6fb;
  --color-surface: #ffffff;
  --color-surface-alt: #eef1f8;
  --color-border: #dde2ee;
  --color-text: #1c2333;
  --color-text-muted: #5b6478;
  --color-primary: #4f46e5;
  --color-primary-dark: #4338ca;
  --color-primary-soft: #eef0fe;
  --color-success: #16a34a;
  --color-success-soft: #e8f8ee;
  --color-danger: #dc2626;
  --color-danger-soft: #fdecec;
  --color-warning: #d97706;
  --color-warning-soft: #fef3e2;
  --color-accent: #0ea5e9;
  --shadow-sm: 0 1px 2px rgba(15, 23, 42, 0.06);
  --shadow-md: 0 8px 24px rgba(15, 23, 42, 0.08);
  --shadow-lg: 0 20px 45px rgba(15, 23, 42, 0.14);
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --font-body: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
    Roboto, Helvetica, Arial, sans-serif;
}

html[data-theme="dark"] {
  --color-bg: #0f1320;
  --color-surface: #161b2c;
  --color-surface-alt: #1e2438;
  --color-border: #2a3149;
  --color-text: #e7e9f5;
  --color-text-muted: #9aa2bd;
  --color-primary: #818cf8;
  --color-primary-dark: #6366f1;
  --color-primary-soft: #232a49;
  --color-success: #34d399;
  --color-success-soft: #103524;
  --color-danger: #f87171;
  --color-danger-soft: #3a1620;
  --color-warning: #fbbf24;
  --color-warning-soft: #3a2b0c;
  --color-accent: #38bdf8;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.35);
  --shadow-md: 0 8px 24px rgba(0, 0, 0, 0.45);
  --shadow-lg: 0 20px 45px rgba(0, 0, 0, 0.55);
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--color-bg);
  color: var(--color-text);
  font-family: var(--font-body);
  -webkit-font-smoothing: antialiased;
  transition: background 0.25s ease, color 0.25s ease;
}

body { min-height: 100vh; }

a { color: inherit; }

.container {
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 clamp(12px, 3vw, 28px);
}

.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border: none;
  border-radius: var(--radius-sm);
  padding: 10px 18px;
  font-family: inherit;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease, opacity 0.12s ease;
  user-select: none;
}
.btn:active { transform: translateY(1px); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.btn-primary { background: var(--color-primary); color: #fff; }
.btn-primary:hover:not(:disabled) { background: var(--color-primary-dark); }

.btn-outline {
  background: transparent;
  color: var(--color-text);
  border: 1px solid var(--color-border);
}
.btn-outline:hover:not(:disabled) { background: var(--color-surface-alt); }

.btn-ghost {
  background: var(--color-surface-alt);
  color: var(--color-text);
}
.btn-ghost:hover:not(:disabled) { background: var(--color-border); }

.btn-danger { background: var(--color-danger); color: #fff; }
.btn-success { background: var(--color-success); color: #fff; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}
.topbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px clamp(12px, 3vw, 28px);
  max-width: 1180px;
  margin: 0 auto;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 1.05rem;
  letter-spacing: -0.01em;
}
.brand i { color: var(--color-primary); }

.theme-toggle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--color-border);
  background: var(--color-surface-alt);
  color: var(--color-text);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex: 0 0 auto;
}
.theme-toggle:hover { background: var(--color-border); }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: 10px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.badge-primary { background: var(--color-primary-soft); color: var(--color-primary); }
.badge-success { background: var(--color-success-soft); color: var(--color-success); }
.badge-danger  { background: var(--color-danger-soft);  color: var(--color-danger); }
.badge-warning { background: var(--color-warning-soft); color: var(--color-warning); }

.visually-hidden {
  position: absolute !important;
  width: 1px; height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

footer.site-footer {
  text-align: center;
  color: var(--color-text-muted);
  font-size: 0.82rem;
  padding: 28px 12px 40px;
}
"""

# JS shared by both page types: theme persistence + toggle wiring.
_THEME_JS = """
(function () {
  var root = document.documentElement;
  var stored = null;
  try { stored = localStorage.getItem('quiz-theme'); } catch (e) {}
  if (stored === 'dark') { root.setAttribute('data-theme', 'dark'); }

  function applyIcon() {
    var btn = document.getElementById('themeToggleBtn');
    if (!btn) return;
    var isDark = root.getAttribute('data-theme') === 'dark';
    btn.innerHTML = isDark
      ? '<i class="fa-solid fa-sun"></i>'
      : '<i class="fa-solid fa-moon"></i>';
    btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
  }

  window.addEventListener('DOMContentLoaded', function () {
    applyIcon();
    var btn = document.getElementById('themeToggleBtn');
    if (btn) {
      btn.addEventListener('click', function () {
        var isDark = root.getAttribute('data-theme') === 'dark';
        if (isDark) {
          root.removeAttribute('data-theme');
          try { localStorage.setItem('quiz-theme', 'light'); } catch (e) {}
        } else {
          root.setAttribute('data-theme', 'dark');
          try { localStorage.setItem('quiz-theme', 'dark'); } catch (e) {}
        }
        applyIcon();
      });
    }
  });
})();
"""


def _topbar_html(title: str, subtitle: str = "") -> str:
    """Sticky header shared by both report types."""
    sub = f'<div class="topbar-sub">{_esc(subtitle)}</div>' if subtitle else ""
    return f"""
<div class="topbar">
  <div class="topbar-inner">
    <div class="brand">
      <i class="fa-solid fa-layer-group"></i>
      <span>{_esc(title)}</span>
    </div>
    <button id="themeToggleBtn" class="theme-toggle" type="button"
      aria-label="Toggle dark mode">
      <i class="fa-solid fa-moon"></i>
    </button>
  </div>
  {sub}
</div>
"""


def _page_shell(*, title: str, extra_head: str, body: str, extra_scripts: str) -> str:
    """Wrap CSS/body/JS fragments into one complete HTML document."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1">
<title>{_esc(title)}</title>
{_GOOGLE_FONTS_LINK}
{_FONT_AWESOME_LINK}
<style>{_BASE_CSS}
{extra_head}
</style>
</head>
<body>
{body}
<script>{_THEME_JS}</script>
{extra_scripts}
</body>
</html>
"""


# --------------------------------------------------------------------------
# render_quiz_html: CBT-exam-style interactive quiz page
# --------------------------------------------------------------------------

_QUIZ_CSS = """
.exam-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
  padding: 20px 0 60px;
}
@media (min-width: 900px) {
  .exam-layout { grid-template-columns: minmax(0, 1fr) 300px; align-items: start; }
}

.exam-header {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 20px;
  margin-bottom: 4px;
}
.exam-title { font-size: 1.15rem; font-weight: 800; }
.exam-meta { color: var(--color-text-muted); font-size: 0.85rem; margin-top: 2px; }

.timer-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: 800;
  font-variant-numeric: tabular-nums;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 1.05rem;
}
.timer-pill.low { background: var(--color-danger-soft); color: var(--color-danger); }

.question-card { padding: 24px clamp(16px, 4vw, 32px); margin-bottom: 16px; }
.question-index {
  color: var(--color-text-muted);
  font-weight: 700;
  font-size: 0.85rem;
  letter-spacing: 0.03em;
  text-transform: uppercase;
  margin-bottom: 10px;
}
.question-text {
  font-size: 1.15rem;
  font-weight: 600;
  line-height: 1.55;
  margin-bottom: 22px;
  white-space: pre-wrap;
}

.option-list { display: flex; flex-direction: column; gap: 12px; }
.option {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 14px 16px;
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  background: var(--color-surface);
  transition: border-color 0.12s ease, background 0.12s ease;
}
.option:hover { border-color: var(--color-primary); background: var(--color-primary-soft); }
.option.selected { border-color: var(--color-primary); background: var(--color-primary-soft); }
.option.correct { border-color: var(--color-success); background: var(--color-success-soft); }
.option.incorrect { border-color: var(--color-danger); background: var(--color-danger-soft); }
.option-key {
  flex: 0 0 auto;
  width: 30px; height: 30px;
  border-radius: 50%;
  border: 1.5px solid var(--color-border);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.85rem;
  background: var(--color-surface-alt);
}
.option.selected .option-key { background: var(--color-primary); color: #fff; border-color: var(--color-primary); }
.option.correct .option-key { background: var(--color-success); color: #fff; border-color: var(--color-success); }
.option.incorrect .option-key { background: var(--color-danger); color: #fff; border-color: var(--color-danger); }
.option-text { padding-top: 3px; line-height: 1.5; }
.option-icon { margin-left: auto; padding-top: 4px; font-size: 1rem; }

.explanation-box {
  margin-top: 18px;
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-surface-alt);
  border-left: 4px solid var(--color-accent);
  font-size: 0.92rem;
  line-height: 1.55;
  display: none;
}
.explanation-box.show { display: block; }
.explanation-box strong { color: var(--color-accent); }

.exam-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: space-between;
  padding: 4px 2px;
}
.exam-actions .group { display: flex; gap: 10px; flex-wrap: wrap; }

.sidebar { display: flex; flex-direction: column; gap: 16px; }
.sidebar-card { padding: 18px; }
.sidebar-title {
  font-weight: 800;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-text-muted);
  margin-bottom: 12px;
}
.qgrid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(38px, 1fr));
  gap: 8px;
}
.qgrid button {
  aspect-ratio: 1 / 1;
  border-radius: 8px;
  border: 1.5px solid var(--color-border);
  background: var(--color-surface-alt);
  color: var(--color-text);
  font-weight: 700;
  font-size: 0.82rem;
  cursor: pointer;
}
.qgrid button.current { outline: 2px solid var(--color-primary); outline-offset: 1px; }
.qgrid button.answered { background: var(--color-success); color: #fff; border-color: var(--color-success); }
.qgrid button.review { background: var(--color-warning); color: #fff; border-color: var(--color-warning); }
.qgrid button.answered-review { background: var(--color-accent); color: #fff; border-color: var(--color-accent); }
.qgrid button.unanswered { background: var(--color-surface-alt); }

.legend { display: flex; flex-direction: column; gap: 8px; font-size: 0.82rem; margin-top: 14px; }
.legend-item { display: flex; align-items: center; gap: 8px; }
.legend-dot { width: 12px; height: 12px; border-radius: 4px; flex: 0 0 auto; }

.progress-track {
  height: 8px;
  border-radius: 999px;
  background: var(--color-surface-alt);
  overflow: hidden;
  margin-top: 10px;
}
.progress-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 999px;
  transition: width 0.25s ease;
}

/* Results screen */
.results-hero {
  text-align: center;
  padding: 40px clamp(16px, 5vw, 48px);
  margin-bottom: 20px;
}
.results-score {
  font-size: clamp(2.4rem, 8vw, 3.2rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  margin: 6px 0;
}
.results-verdict {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 18px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.95rem;
  margin-top: 8px;
}
.results-verdict.pass { background: var(--color-success-soft); color: var(--color-success); }
.results-verdict.fail { background: var(--color-danger-soft); color: var(--color-danger); }

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 26px;
}
@media (min-width: 640px) { .stat-grid { grid-template-columns: repeat(4, 1fr); } }
.stat-tile {
  background: var(--color-surface-alt);
  border-radius: var(--radius-md);
  padding: 16px 12px;
  text-align: center;
}
.stat-tile .value { font-size: 1.5rem; font-weight: 800; }
.stat-tile .label { font-size: 0.78rem; color: var(--color-text-muted); margin-top: 2px; }

.review-toggle-wrap { text-align: center; margin: 24px 0; }

#reviewSection { display: none; }
#reviewSection.show { display: block; }

.hidden { display: none !important; }

@media (max-width: 899px) {
  .sidebar { order: -1; }
  .qgrid { grid-template-columns: repeat(auto-fill, minmax(34px, 1fr)); }
}
"""

# JS template for the exam runner. `%%DATA%%` is replaced with a JSON blob
# describing the quiz; everything else is static behaviour.
_QUIZ_JS_TEMPLATE = """
(function () {
  var QUIZ = %%DATA%%;
  var questions = QUIZ.questions;
  var totalTime = QUIZ.timerPerQuestion; // seconds, per question
  var correctMarks = QUIZ.correctMarks;
  var negativeMarks = QUIZ.negativeMarks;

  var state = {
    current: 0,
    answers: new Array(questions.length).fill(null),
    marked: new Array(questions.length).fill(false),
    visited: new Array(questions.length).fill(false),
    submitted: false,
    secondsLeft: totalTime,
    timerId: null
  };

  var els = {};
  function q(id) { return document.getElementById(id); }

  function fmtTime(s) {
    s = Math.max(0, s | 0);
    var m = Math.floor(s / 60);
    var r = s % 60;
    return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
  }

  function renderGrid() {
    var grid = els.qgrid;
    grid.innerHTML = '';
    questions.forEach(function (_, i) {
      var btn = document.createElement('button');
      btn.type = 'button';
      btn.textContent = (i + 1);
      var cls = 'unanswered';
      var answered = state.answers[i] !== null;
      var marked = state.marked[i];
      if (answered && marked) cls = 'answered-review';
      else if (marked) cls = 'review';
      else if (answered) cls = 'answered';
      else if (state.visited[i]) cls = 'unanswered';
      btn.className = cls + (i === state.current ? ' current' : '');
      btn.addEventListener('click', function () { goTo(i); });
      grid.appendChild(btn);
    });
  }

  function renderProgress() {
    var answeredCount = state.answers.filter(function (a) { return a !== null; }).length;
    var pct = Math.round((answeredCount / questions.length) * 100);
    els.progressFill.style.width = pct + '%';
    els.progressLabel.textContent = answeredCount + ' / ' + questions.length + ' answered';
  }

  function renderQuestion() {
    var idx = state.current;
    var qd = questions[idx];
    state.visited[idx] = true;

    els.qIndex.textContent = 'Question ' + (idx + 1) + ' of ' + questions.length;
    els.qText.textContent = qd.question;

    els.optionList.innerHTML = '';
    qd.options.forEach(function (opt, i) {
      var row = document.createElement('div');
      row.className = 'option' + (state.answers[idx] === i ? ' selected' : '');
      row.setAttribute('role', 'button');
      row.setAttribute('tabindex', '0');
      var key = document.createElement('div');
      key.className = 'option-key';
      key.textContent = String.fromCharCode(65 + i);
      var text = document.createElement('div');
      text.className = 'option-text';
      text.textContent = opt;
      row.appendChild(key);
      row.appendChild(text);
      row.addEventListener('click', function () { selectOption(i); });
      els.optionList.appendChild(row);
    });

    els.markBtn.classList.toggle('btn-primary', state.marked[idx]);
    els.markBtn.classList.toggle('btn-outline', !state.marked[idx]);
    els.markBtn.innerHTML = state.marked[idx]
      ? '<i class="fa-solid fa-bookmark"></i> Marked for review'
      : '<i class="fa-regular fa-bookmark"></i> Mark for review';

    els.prevBtn.disabled = idx === 0;
    els.nextBtn.textContent = idx === questions.length - 1 ? 'Finish' : 'Next';
    els.nextBtn.innerHTML = idx === questions.length - 1
      ? 'Review & Submit <i class="fa-solid fa-flag-checkered"></i>'
      : 'Next
