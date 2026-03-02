from __future__ import annotations

import streamlit as st


EDITORIAL_THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,600;9..144,700&family=IBM+Plex+Mono:wght@400;500;600&family=Manrope:wght@400;500;700;800&display=swap');

:root {
  --ink: #182433;
  --sand: #f4efe5;
  --card: rgba(255, 249, 240, 0.78);
  --line: rgba(24, 36, 51, 0.14);
  --accent: #c85c2c;
  --accent-soft: #f1be94;
  --accent-dark: #883b18;
  --forest: #476b5d;
}

.stApp {
  background:
    radial-gradient(circle at top left, rgba(200, 92, 44, 0.18), transparent 28%),
    radial-gradient(circle at top right, rgba(71, 107, 93, 0.16), transparent 25%),
    linear-gradient(180deg, #f6f0e7 0%, #f0e4d3 100%);
  color: var(--ink);
}

[data-testid="stHeader"] {
  background: transparent;
}

[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, rgba(24, 36, 51, 0.94), rgba(29, 53, 66, 0.98));
  border-right: 1px solid rgba(255,255,255,0.08);
}

[data-testid="stSidebar"] * {
  color: #f7f1e8;
  font-family: "Manrope", sans-serif;
}

.hero-shell {
  position: relative;
  padding: 1.5rem 1.5rem 1.8rem;
  border: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(255,255,255,0.66), rgba(250,244,236,0.88));
  box-shadow: 0 16px 40px rgba(24, 36, 51, 0.09);
  overflow: hidden;
}

.hero-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(24,36,51,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(24,36,51,0.03) 1px, transparent 1px);
  background-size: 24px 24px;
  pointer-events: none;
}

.eyebrow {
  font-family: "IBM Plex Mono", monospace;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--accent-dark);
  font-size: 0.78rem;
}

.hero-title {
  font-family: "Fraunces", serif;
  color: var(--ink);
  font-size: clamp(2.1rem, 4vw, 4rem);
  line-height: 0.95;
  margin: 0.25rem 0 0.75rem;
  max-width: 10ch;
}

.hero-copy {
  font-family: "Manrope", sans-serif;
  font-size: 1rem;
  line-height: 1.6;
  max-width: 70ch;
}

.signal-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.8rem;
  margin-top: 1rem;
}

.signal-card,
.metric-card {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 1rem;
  backdrop-filter: blur(10px);
}

.signal-label,
.metric-label {
  font-family: "IBM Plex Mono", monospace;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  font-size: 0.72rem;
  color: rgba(24, 36, 51, 0.76);
}

.signal-value,
.metric-value {
  font-family: "Fraunces", serif;
  font-size: 1.8rem;
  line-height: 1;
  color: var(--ink);
  margin-top: 0.35rem;
}

.metric-note {
  font-family: "Manrope", sans-serif;
  font-size: 0.92rem;
  color: rgba(24, 36, 51, 0.74);
  margin-top: 0.35rem;
}

.section-title {
  font-family: "Fraunces", serif;
  font-size: 1.55rem;
  margin: 0.25rem 0 0.4rem;
}

.section-copy {
  font-family: "Manrope", sans-serif;
  margin-bottom: 0.8rem;
  max-width: 74ch;
}

.callout {
  border-left: 6px solid var(--accent);
  padding: 1rem 1rem 1rem 1.25rem;
  background: rgba(255, 251, 245, 0.82);
  border-top: 1px solid var(--line);
  border-right: 1px solid var(--line);
  border-bottom: 1px solid var(--line);
  font-family: "Manrope", sans-serif;
}

.footer-note {
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.82rem;
  letter-spacing: 0.04em;
  color: rgba(24, 36, 51, 0.65);
}

div[data-testid="stMetric"] {
  background: var(--card);
  border: 1px solid var(--line);
  padding: 1rem;
}
</style>
"""


def apply_theme() -> None:
    st.markdown(EDITORIAL_THEME, unsafe_allow_html=True)
