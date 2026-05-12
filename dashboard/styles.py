"""Global CSS styles matching the wireframe exactly."""

GLOBAL_CSS = """
<style>
/* ── Base overrides ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

.stApp {
    background: #f5f5f5 !important;
}
.stApp, .stApp * {
    font-family: -apple-system, system-ui, 'Inter', sans-serif !important;
}

/* ── Sidebar ────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    width: 340px !important;
    min-width: 340px !important;
    max-width: 340px !important;
    background: #fff !important;
    border-right: 1px solid #ddd !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding: 24px !important;
    padding-top: 24px !important;
    padding-bottom: 24px !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
    display: none !important;
}
/* Remove Streamlit sidebar header branding */
section[data-testid="stSidebar"] header {
    display: none !important;
}

/* ── Sidebar title ──────────────────────────────────────────────────── */
.sidebar-title {
    font-size: 18px !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
    color: #333 !important;
}
.sidebar-subtitle {
    font-size: 12px !important;
    color: #888 !important;
    margin-bottom: 24px !important;
}
.sidebar-section-title {
    font-size: 13px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    color: #666 !important;
    margin-bottom: 12px !important;
}

/* ── Form inputs inside sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] .stTextInput input,
section[data-testid="stSidebar"] .stNumberInput input,
section[data-testid="stSidebar"] .stSelectbox select {
    padding: 8px 10px !important;
    border: 1px solid #ccc !important;
    border-radius: 4px !important;
    font-size: 13px !important;
    background: #fff !important;
}
section[data-testid="stSidebar"] .stTextInput label,
section[data-testid="stSidebar"] .stNumberInput label,
section[data-testid="stSidebar"] .stSelectbox label {
    font-size: 12px !important;
    color: #555 !important;
    margin-bottom: 4px !important;
}

/* ── Ingredient rows ────────────────────────────────────────────────── */
.ingredient-row {
    display: flex !important;
    gap: 6px !important;
    margin-bottom: 8px !important;
    align-items: center !important;
}
.ingredient-row input {
    flex: 1 !important;
    padding: 7px 8px !important;
    border: 1px solid #ddd !important;
    border-radius: 3px !important;
    font-size: 12px !important;
    outline: none !important;
    background: #fff !important;
}
.ingredient-row input:focus {
    border-color: #0d7377 !important;
}
.ingredient-row select {
    width: 65px !important;
    flex: none !important;
    padding: 7px 4px !important;
    border: 1px solid #ddd !important;
    border-radius: 3px !important;
    font-size: 12px !important;
    background: #fff !important;
}

/* ── Buttons ────────────────────────────────────────────────────────── */
/* Add ingredient button */
.btn-add-ingredient {
    width: 100% !important;
    padding: 10px 16px !important;
    border: 1px dashed #ccc !important;
    border-radius: 4px !important;
    background: #f0f0f0 !important;
    color: #555 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    margin-bottom: 16px !important;
    text-align: center !important;
}
.btn-add-ingredient:hover {
    background: #e8e8e8 !important;
}

/* Analyze button (Streamlit override) */
section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"] {
    background: #0d7377 !important;
    color: white !important;
    border: none !important;
    border-radius: 4px !important;
    font-size: 14px !important;
    padding: 12px !important;
    font-weight: 500 !important;
    width: 100% !important;
}
section[data-testid="stSidebar"] .stButton button[data-testid="baseButton-primary"]:hover {
    background: #0a5c5f !important;
    border-color: transparent !important;
}

/* ── Main content padding ───────────────────────────────────────────── */
.main-content {
    padding: 24px 32px !important;
}

/* ── Pipeline strip ─────────────────────────────────────────────────── */
.pipeline-strip {
    display: flex !important;
    gap: 4px !important;
    margin-bottom: 32px !important;
    overflow-x: auto !important;
    padding-bottom: 8px !important;
}
.agent-card {
    flex: 1 !important;
    min-width: 110px !important;
    padding: 12px 8px !important;
    border-radius: 6px !important;
    text-align: center !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    position: relative !important;
    border: 2px solid transparent !important;
    background: #fff !important;
}
.agent-card .agent-name {
    margin-bottom: 4px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #333 !important;
}
.agent-card .agent-status {
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}

/* Status colors */
.agent-card.status-done {
    border-color: #2a9d8f !important;
    background: #e6f5f3 !important;
}
.agent-card.status-done .agent-status {
    color: #2a9d8f !important;
}
.agent-card.status-running {
    border-color: #457b9d !important;
    background: #e8f0f5 !important;
    animation: pulse 1.5s infinite !important;
}
.agent-card.status-running .agent-status {
    color: #457b9d !important;
}
.agent-card.status-waiting {
    border-color: #ddd !important;
    background: #fafafa !important;
}
.agent-card.status-waiting .agent-status {
    color: #aaa !important;
}
.agent-card.status-error {
    border-color: #d32f2f !important;
    background: #fce4e4 !important;
}
.agent-card.status-error .agent-status {
    color: #d32f2f !important;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

/* ── Result cards ───────────────────────────────────────────────────── */
.results-container {
    display: flex !important;
    flex-direction: column !important;
    gap: 16px !important;
}
.result-card {
    background: #fff !important;
    border: 1px solid #e0e0e0 !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}
.result-header {
    padding: 12px 16px !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    border-bottom: 1px solid #f0f0f0 !important;
    cursor: pointer !important;
}
.result-header h3 {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #333 !important;
    margin: 0 !important;
}
.badge {
    font-size: 11px !important;
    padding: 2px 8px !important;
    border-radius: 10px !important;
}
.badge-ok {
    background: #e6f5f3 !important;
    color: #2a9d8f !important;
}
.badge-warn {
    background: #fff3e0 !important;
    color: #e76f51 !important;
}
.badge-error {
    background: #fce4e4 !important;
    color: #d32f2f !important;
}
.result-body {
    padding: 16px !important;
    font-size: 13px !important;
    line-height: 1.6 !important;
    color: #555 !important;
}
.result-body.collapsed {
    display: none !important;
}
.placeholder-text {
    color: #bbb !important;
    font-style: italic !important;
    font-size: 13px !important;
}

/* ── Download bar ───────────────────────────────────────────────────── */
.download-bar {
    margin-top: 24px !important;
    padding: 16px 20px !important;
    background: #fff !important;
    border: 1px solid #d0d0d0 !important;
    border-radius: 6px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;
}
.download-bar .label {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #333 !important;
}
.download-bar .check {
    color: #2a9d8f !important;
    font-size: 16px !important;
}

/* ── History items ──────────────────────────────────────────────────── */
.history-section {
    margin-top: auto !important;
    border-top: 1px solid #eee !important;
    padding-top: 16px !important;
}
.history-item {
    padding: 8px 0 !important;
    border-bottom: 1px solid #f0f0f0 !important;
    font-size: 12px !important;
    cursor: pointer !important;
}
.history-item:hover {
    background: #f8f8f8 !important;
}
.history-item .name {
    font-weight: 500 !important;
    color: #333 !important;
}
.history-item .meta {
    color: #999 !important;
    font-size: 11px !important;
}

/* ── Remove Streamlit chrome ────────────────────────────────────────── */
#MainMenu { visibility: hidden !important; }
footer { visibility: hidden !important; }
header { visibility: hidden !important; }

/* Remove default Streamlit padding on main block */
.block-container {
    padding-top: 24px !important;
    padding-left: 32px !important;
    padding-right: 32px !important;
    max-width: none !important;
}

/* Hide horizontal rule used as separator */
hr {
    border: none !important;
    border-top: 1px solid #e0e0e0 !important;
    margin: 16px 0 !important;
}

/* Remove expander default styling */
.streamlit-expanderHeader {
    font-size: 14px !important;
    font-weight: 500 !important;
}
</style>
"""


def get_global_css() -> str:
    return GLOBAL_CSS
