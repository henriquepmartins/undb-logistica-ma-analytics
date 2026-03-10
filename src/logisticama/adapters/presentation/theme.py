from __future__ import annotations

import streamlit as st


MINIMAL_THEME = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');

:root {
  --bg: #F7F8F5;
  --panel: #FFFFFF;
  --text: #1B242C;
  --muted: #66727E;
  --line: #D7DFE5;
  --blue: #264653;
  --blue-soft: #9FB5C3;
  --alert: #C96A4A;
}

html, body, [class*="css"] {
  font-family: "IBM Plex Sans", sans-serif;
}

.stApp {
  background: var(--bg);
  color: var(--text);
}

[data-testid="stHeader"] {
  background: rgba(247, 248, 245, 0.92);
  border-bottom: 1px solid rgba(215, 223, 229, 0.8);
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"],
button[kind="header"][aria-label*="sidebar"],
button[kind="header"][aria-label*="Sidebar"] {
  display: none !important;
}

.app-shell {
  max-width: 1440px;
  margin: 0 auto;
}

.tab-shell {
  max-width: 1440px;
  margin: 0 auto;
  padding-bottom: 1rem;
}

.top-note,
.eyebrow,
.metric-label,
.section-note,
.small-note {
  font-family: "IBM Plex Mono", monospace;
}

.top-note {
  color: var(--blue);
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 0.35rem;
}

.page-title {
  font-size: clamp(1.45rem, 2.1vw, 1.85rem);
  line-height: 1.1;
  font-weight: 700;
  margin: 0;
  color: var(--text);
}

.page-copy {
  color: var(--muted);
  font-size: 0.92rem;
  line-height: 1.4;
  max-width: 62rem;
  margin: 0.35rem 0 0.55rem;
}

.page-meta {
  color: var(--muted);
  font-size: 0.82rem;
  margin-bottom: 0.95rem;
}

.metric-card,
.section-card {
  background: transparent;
  border: 0;
  border-radius: 0;
}

.metric-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.9rem 1rem;
  min-height: 136px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
}

.narrative-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.95rem 1.05rem;
  min-height: 176px;
}

.narrative-card .page-copy {
  margin-bottom: 0;
}

.method-card,
.filter-card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.95rem 1rem;
}

.method-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
  margin-top: 0.65rem;
}

.method-step {
  border: 1px solid rgba(215, 223, 229, 0.85);
  border-radius: 10px;
  padding: 0.8rem 0.85rem;
  background: rgba(159, 181, 195, 0.08);
}

.method-step strong {
  display: block;
  color: var(--text);
  font-size: 0.84rem;
  margin-bottom: 0.22rem;
}

.metric-label {
  color: var(--muted);
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.metric-value {
  color: var(--text);
  font-size: 1.55rem;
  line-height: 1.05;
  font-weight: 700;
  margin-top: 0.5rem;
  max-width: 100%;
  overflow-wrap: anywhere;
}

.metric-subtitle {
  color: var(--muted);
  font-size: 0.84rem;
  line-height: 1.35;
  margin-top: 0.45rem;
  max-width: 18rem;
}

.section-card {
  padding: 0.1rem 0 0.3rem;
  height: auto;
}

.section-title {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

.section-note {
  color: var(--muted);
  font-size: 0.72rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin: 0.02rem 0 0.45rem;
}

.small-note {
  color: var(--muted);
  font-size: 0.72rem;
  letter-spacing: 0.04em;
  margin-top: 0.3rem;
}

.benchmark-context {
  background: linear-gradient(135deg, rgba(38, 70, 83, 0.98) 0%, rgba(38, 70, 83, 0.9) 100%);
  border: 1px solid rgba(38, 70, 83, 0.14);
  border-radius: 16px;
  padding: 1rem 1.1rem 1.05rem;
  margin: 0.8rem 0 1rem;
  box-shadow: 0 18px 34px rgba(38, 70, 83, 0.1);
}

.benchmark-context .top-note {
  color: rgba(247, 248, 245, 0.72);
}

.benchmark-context-title {
  color: #F7F8F5;
  font-size: clamp(1.08rem, 2vw, 1.32rem);
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.benchmark-context-copy {
  color: rgba(247, 248, 245, 0.82);
  font-size: 0.9rem;
  line-height: 1.45;
  max-width: 60rem;
  margin: 0.35rem 0 0;
}

.benchmark-panel {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 1) 100%);
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 0.95rem 1rem 0.55rem;
  margin-top: 0.95rem;
  box-shadow: 0 12px 26px rgba(38, 70, 83, 0.06);
}

.benchmark-panel--secondary {
  margin-top: 1.1rem;
}

.benchmark-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.58rem;
  margin-bottom: 0.55rem;
  border-radius: 999px;
  background: rgba(159, 181, 195, 0.18);
  color: var(--blue);
  font-family: "IBM Plex Mono", monospace;
  font-size: 0.68rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.stPlotlyChart {
  border-top: 1px solid rgba(215, 223, 229, 0.85);
  padding-top: 0.45rem;
}

[data-baseweb="tab-list"] {
  gap: 0.6rem;
  margin: 0.8rem auto 1rem;
}

[data-baseweb="tab"] {
  height: 42px;
  border-radius: 999px;
  padding: 0 1rem;
  background: rgba(159, 181, 195, 0.12);
  border: 1px solid transparent;
}

[aria-selected="true"][data-baseweb="tab"] {
  background: var(--panel);
  border-color: var(--line);
}

.stSlider, .stSelectbox {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 0.25rem 0.7rem 0.55rem;
}

.stSlider label, .stSelectbox label {
  font-size: 0.82rem;
  font-weight: 600;
}

button[kind="primary"],
.stDownloadButton button,
.stButton button {
  background: var(--blue);
  color: #FFFFFF;
  border: 1px solid var(--blue);
  border-radius: 8px;
  font-weight: 600;
}

div[data-testid="stAlert"] {
  border-radius: 10px;
  border: 1px solid var(--line);
}

@media (max-width: 900px) {
  .metric-card {
    min-height: auto;
  }

  .method-grid {
    grid-template-columns: 1fr;
  }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(MINIMAL_THEME, unsafe_allow_html=True)
