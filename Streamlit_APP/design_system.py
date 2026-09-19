"""
design_system.py
================
نظام تصميم موحّد لكل صفحات التطبيق (نفس روح صفحتي الوعود والإهمال).

الاستخدام في app.py:

    from design_system import (
        inject_design_system, page_header, kpi_row, section_title,
        card, empty_state, info_box, style_fig, sidebar_brand, PAGE_THEMES,
    )

    st.set_page_config(...)
    ...
    inject_design_system(PAGE_THEMES.get(st.session_state.page, "promises"))

سطر inject_design_system لوحده بيلبّس كل الويدجتس (تابات، أزرار، رفع ملفات،
جداول، سلايدرز، إكسباندرز، رسائل) بنفس الستايل ولون الصفحة، حتى الصفحات
اللي لسه ما اتعدلتش.
"""

from contextlib import contextmanager
import html as _html
import streamlit as st

# ----------------------------------------------------------------------
# ألوان كل صفحة: (أساسي، غامق، فاتح للخلفيات، لمعة الهيدر)
# ----------------------------------------------------------------------
THEMES = {
    "promises":     dict(accent="#00693E", dark="#0a3d2c", soft="#e7f4ec", glow="#0f7a4a"),
    "neglect":      dict(accent="#A33A3A", dark="#5a1f1a", soft="#f8e8e7", glow="#b8493f"),
    "distribution": dict(accent="#5B3FA0", dark="#2a1a5c", soft="#eee9f8", glow="#7452c2"),
    "activity":     dict(accent="#0E7490", dark="#0a3a4a", soft="#e0f2f6", glow="#1490b0"),
    "payments":     dict(accent="#B7791F", dark="#5a3a0a", soft="#faf0dc", glow="#d09030"),
    "rotation":     dict(accent="#155A8A", dark="#0d2d4a", soft="#e5f0f8", glow="#1c76b3"),
}

# اسم الصفحة في السايد بار -> الثيم
PAGE_THEMES = {
    "الوعود القائمة و المكسورة": "promises",
    "الاهمال": "neglect",
    "التوزيع": "distribution",
    "النشاط": "activity",
    "التقرير اليومي للسدادات": "payments",
    "التدوير": "rotation",
}

# ألوان الرسوم البيانية (ثابتة عبر الصفحات)
GREEN, GOLD, RED, BLUE, VIOLET, TEAL = (
    "#00693E", "#C9A227", "#A33A3A", "#155A8A", "#5B3FA0", "#0E7490"
)
PALETTE = [GREEN, GOLD, RED, BLUE, VIOLET, TEAL, "#7A8B99", "#D97706"]

_TONES = {
    "ok": "#00693E",
    "bad": "#A33A3A",
    "warn": "#C9A227",
    "info": None,  # = لون الصفحة
}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap');

:root{
  --ds-accent:__ACCENT__;
  --ds-dark:__DARK__;
  --ds-soft:__SOFT__;
  --ds-glow:__GLOW__;
  --ds-ink:#0f172a;
  --ds-muted:#6b7280;
  --ds-line:#e6ebe8;
  --ds-radius:18px;
}

/* ===== الخط: نتجنب span عشان أيقونات Material متتكسرش ===== */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb], .stApp [data-testid="stMarkdownContainer"]{
  font-family:'Tajawal', sans-serif;
}
.main .block-container{ padding-top:1.2rem; padding-bottom:3.5rem; max-width:1280px; }
h2, h3, h4{ font-weight:800; letter-spacing:0; }

/* ===== الهيدر ===== */
.ds-header{
  position:relative; overflow:hidden; border-radius:22px; padding:30px 34px; margin-bottom:26px;
  background:linear-gradient(120deg, var(--ds-dark) 0%, var(--ds-accent) 58%, var(--ds-glow) 100%);
  box-shadow:0 14px 34px color-mix(in srgb, var(--ds-accent) 32%, transparent);
  display:flex; align-items:center; gap:22px;
}
.ds-header::before{
  content:""; position:absolute; inset:0; opacity:.55; pointer-events:none;
  background:
    radial-gradient(circle at 12% -20%, rgba(255,255,255,.22) 0, rgba(255,255,255,0) 42%),
    repeating-linear-gradient(135deg, rgba(255,255,255,.045) 0 2px, transparent 2px 22px);
}
.ds-header::after{
  content:""; position:absolute; left:-70px; bottom:-90px; width:260px; height:260px; border-radius:50%;
  background:radial-gradient(circle, rgba(255,255,255,.14) 0%, rgba(255,255,255,0) 70%);
}
.ds-header-icon{
  position:relative; z-index:1; flex:0 0 auto; width:64px; height:64px; border-radius:18px;
  display:flex; align-items:center; justify-content:center; font-size:30px;
  background:rgba(255,255,255,.16); border:1px solid rgba(255,255,255,.28);
  backdrop-filter:blur(6px);
}
.ds-header-body{ position:relative; z-index:1; min-width:0; }
.ds-header h1{ color:#fff !important; margin:0 !important; padding:0 !important; font-size:28px; font-weight:800; line-height:1.3; }
.ds-header p{ color:rgba(255,255,255,.82); margin:7px 0 0 0; font-size:14.5px; font-weight:500; max-width:820px; line-height:1.8; }
.ds-chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:13px; }
.ds-chip{
  background:rgba(255,255,255,.14); color:#fff; font-size:12px; font-weight:700;
  padding:4px 13px; border-radius:999px; border:1px solid rgba(255,255,255,.26);
}

/* ===== بطاقات KPI ===== */
.ds-kpis{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:16px; margin:4px 0 8px 0; }
.ds-kpi{
  position:relative; overflow:hidden; background:#fff; border-radius:var(--ds-radius);
  padding:18px 20px 16px 20px; border:1px solid #eef1ef; border-right:6px solid var(--tone, var(--ds-accent));
  box-shadow:0 6px 20px rgba(17,24,39,.07);
}
.ds-kpi::before{
  content:""; position:absolute; top:-30px; left:-30px; width:120px; height:120px; border-radius:50%;
  background:radial-gradient(circle, color-mix(in srgb, var(--tone, var(--ds-accent)) 14%, transparent) 0%, transparent 70%);
}
.ds-kpi-icon{
  position:relative; width:42px; height:42px; border-radius:12px; font-size:20px;
  display:flex; align-items:center; justify-content:center;
  background:color-mix(in srgb, var(--tone, var(--ds-accent)) 13%, white);
}
.ds-kpi-label{ position:relative; font-size:13px; color:var(--ds-muted); font-weight:700; margin-top:12px; }
.ds-kpi-value{ position:relative; font-size:30px; font-weight:800; color:var(--ds-ink); margin-top:2px; line-height:1.25; overflow-wrap:anywhere; }
.ds-kpi-sub{ position:relative; font-size:12px; color:#8a95a5; font-weight:600; margin-top:4px; }

/* ===== عناوين الأقسام ===== */
.ds-section{
  display:flex; align-items:center; gap:10px; margin:30px 0 14px 0; padding:12px 18px; border-radius:12px;
  background:linear-gradient(90deg, var(--ds-soft) 0%, rgba(255,255,255,0) 100%);
  border-right:5px solid var(--ds-accent); font-weight:800; font-size:16.5px; color:var(--ds-dark);
}
.ds-section small{ font-weight:600; font-size:12.5px; color:var(--ds-muted); margin-right:auto; }

/* ===== كروت الحاويات (تلف الويدجتس فعليًا) ===== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] .ds-card-title),
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){
  border-radius:var(--ds-radius) !important; border:1px solid #e9eeea !important;
  box-shadow:0 4px 16px rgba(17,24,39,.05); padding:6px 8px 2px 8px;
}
.ds-card-title{ font-weight:800; font-size:15px; margin:2px 0 2px 0; display:flex; align-items:center; gap:8px; }
.ds-card-title::before{ content:""; width:8px; height:8px; border-radius:50%; background:var(--ds-accent); flex:0 0 auto; }
.ds-card-sub{ font-size:12.5px; color:var(--ds-muted); font-weight:600; margin:0 0 6px 0; }

/* ===== صناديق معلومات ===== */
.ds-box{ border-radius:14px; padding:14px 18px; margin:0 0 14px 0; font-weight:700; line-height:1.9; border:1px solid; }
.ds-box.info{ background:#fbf6e9; border-color:#efe0ad; color:#6b5410; }
.ds-box.ok{ background:#eaf6ef; border-color:#c9e9d5; color:#0f3d2e; }
.ds-box.bad{ background:#fdecea; border-color:#f5c2c0; color:#7a1f1a; }

/* ===== حالة فارغة ===== */
.ds-empty{
  text-align:center; padding:34px 16px; margin:8px 0; border-radius:var(--ds-radius);
  border:2px dashed color-mix(in srgb, var(--ds-accent) 32%, transparent);
  background:color-mix(in srgb, var(--ds-soft) 55%, white); color:#5f6b7a; font-weight:700; font-size:14.5px;
}
.ds-empty .ds-empty-icon{ font-size:34px; display:block; margin-bottom:8px; }

/* ===== التابات (شكل حبوب) ===== */
div[data-baseweb="tab-list"]{ gap:6px; border-bottom:1px solid var(--ds-line); }
button[data-baseweb="tab"]{ font-weight:700 !important; font-size:14.5px !important; border-radius:10px 10px 0 0 !important; padding:8px 16px !important; }
button[data-baseweb="tab"][aria-selected="true"]{ background:var(--ds-soft) !important; color:var(--ds-accent) !important; }
div[data-baseweb="tab-highlight"]{ background-color:var(--ds-accent) !important; height:3px !important; }

/* ===== الأزرار ===== */
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button{
  border-radius:12px !important; font-weight:800 !important; transition:all .15s ease-in-out; padding:.5rem 1rem;
}
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stDownloadButton"] button[kind="primary"],
div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(120deg, var(--ds-accent), var(--ds-dark)) !important; border:none !important; color:#fff !important;
  box-shadow:0 6px 16px color-mix(in srgb, var(--ds-accent) 28%, transparent);
}
div[data-testid="stButton"] button[kind="primary"]:hover{ transform:translateY(-1px); filter:brightness(1.08); }
div[data-testid="stButton"] button[kind="secondary"]:hover,
div[data-testid="stDownloadButton"] button:hover{ border-color:var(--ds-accent) !important; color:var(--ds-accent) !important; transform:translateY(-1px); }
div[data-testid="stDownloadButton"] button{ border:1px solid #d8e2dc !important; }

/* ===== رفع الملفات ===== */
div[data-testid="stFileUploader"]{
  border:2px dashed color-mix(in srgb, var(--ds-accent) 32%, transparent); border-radius:16px; padding:8px;
  background:color-mix(in srgb, var(--ds-soft) 40%, white);
}
div[data-testid="stFileUploader"] section{ border-radius:12px; }

/* ===== الحقول والاختيارات ===== */
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"]{ border-radius:12px !important; }
div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within{ border-color:var(--ds-accent) !important; }
span[data-baseweb="tag"]{ background:var(--ds-soft) !important; color:var(--ds-dark) !important; border-radius:8px !important; font-weight:700; }
div[data-testid="stSlider"] [role="slider"]{ background:var(--ds-accent) !important; }
div[data-testid="stCheckbox"] label{ font-weight:600; }
div[role="radiogroup"][aria-orientation="horizontal"], div[data-testid="stRadio"] div[role="radiogroup"]{ gap:.5rem; }
div[data-testid="stRadio"] label[data-baseweb="radio"]{
  background:#fff; border:1px solid var(--ds-line); border-radius:12px; padding:8px 16px; font-weight:700;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){
  background:var(--ds-soft); border-color:var(--ds-accent); color:var(--ds-dark);
}
div[data-testid="stProgress"] > div > div > div > div{ background:var(--ds-accent) !important; }

/* ===== الجداول ===== */
div[data-testid="stDataFrame"]{ border:1px solid var(--ds-line); border-radius:14px; overflow:hidden; box-shadow:0 3px 12px rgba(17,24,39,.04); }

/* ===== Metric الأصلي بيبقى كارت ===== */
div[data-testid="stMetric"]{
  background:#fff; border:1px solid #eef1ef; border-right:5px solid var(--ds-accent); border-radius:16px;
  padding:14px 18px; box-shadow:0 5px 16px rgba(17,24,39,.06);
}
div[data-testid="stMetric"] *{ color:var(--ds-ink) !important; }
div[data-testid="stMetricLabel"] p{ color:var(--ds-muted) !important; font-weight:700; }
div[data-testid="stMetricValue"]{ font-weight:800; }

/* ===== الإكسبندر والتنبيهات ===== */
div[data-testid="stExpander"]{ border:1px solid var(--ds-line) !important; border-radius:14px !important; overflow:hidden; }
div[data-testid="stExpander"] summary{ font-weight:700; }
div[data-testid="stAlert"]{ border-radius:14px; font-weight:600; }

/* ===== السايد بار ===== */
section[data-testid="stSidebar"]{ background:linear-gradient(185deg, #0b1f2e 0%, #10293d 55%, #0d2233 100%); border-left:1px solid rgba(255,255,255,.06); }
section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h3, section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span{ color:#e4edf4; }
section[data-testid="stSidebar"] hr{ border-color:rgba(255,255,255,.10); }
section[data-testid="stSidebar"] div[data-testid="stButton"] button{
  justify-content:flex-start; text-align:right; border-radius:12px !important; font-weight:700 !important;
  background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.09); color:#d6e3ec !important; box-shadow:none;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{
  background:rgba(255,255,255,.11); border-color:rgba(255,255,255,.25) !important; color:#fff !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(120deg, var(--ds-accent), var(--ds-glow)) !important; border:none !important; color:#fff !important;
  box-shadow:0 8px 18px rgba(0,0,0,.30);
}
.ds-brand{
  display:flex; align-items:center; gap:12px; padding:14px 14px; margin:2px 0 14px 0; border-radius:16px;
  background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.12);
}
.ds-brand-logo{
  width:44px; height:44px; border-radius:13px; display:flex; align-items:center; justify-content:center; font-size:22px;
  background:linear-gradient(135deg, var(--ds-accent), var(--ds-glow));
}
.ds-brand-title{ color:#fff; font-weight:800; font-size:16px; line-height:1.3; }
.ds-brand-sub{ color:#9fb4c4; font-size:12px; font-weight:600; }

@media (max-width:760px){
  .ds-header{ flex-direction:column; align-items:flex-start; padding:22px; }
  .ds-header h1{ font-size:23px; }
}
</style>
"""


def inject_design_system(theme: str = "promises") -> None:
    """يتنادى مرة واحدة في كل rerun، بعد set_page_config."""
    t = THEMES.get(theme, THEMES["promises"])
    css = (
        _CSS.replace("__ACCENT__", t["accent"])
        .replace("__DARK__", t["dark"])
        .replace("__SOFT__", t["soft"])
        .replace("__GLOW__", t["glow"])
    )
    st.markdown(css, unsafe_allow_html=True)


def _e(x) -> str:
    return _html.escape(str(x))


def page_header(icon: str, title: str, subtitle: str = "", chips=None) -> None:
    chips_html = ""
    if chips:
        chips_html = '<div class="ds-chips">' + "".join(
            f'<span class="ds-chip">{_e(c)}</span>' for c in chips
        ) + "</div>"
    sub_html = f"<p>{_e(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="ds-header">
            <div class="ds-header-icon">{icon}</div>
            <div class="ds-header-body">
                <h1>{_e(title)}</h1>
                {sub_html}
                {chips_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_row(items) -> None:
    """
    items: قايمة dicts: icon, label, value, sub (اختياري), tone: ok|bad|warn|info
    الصف بيتظبط لوحده على عرض الشاشة (2-4 كروت أحسن حاجة).
    """
    cards = []
    for it in items:
        tone = _TONES.get(it.get("tone", "info"))
        style = f' style="--tone:{tone}"' if tone else ""
        sub = f'<div class="ds-kpi-sub">{_e(it["sub"])}</div>' if it.get("sub") else ""
        cards.append(
            f'<div class="ds-kpi"{style}>'
            f'<div class="ds-kpi-icon">{it.get("icon", "📊")}</div>'
            f'<div class="ds-kpi-label">{_e(it["label"])}</div>'
            f'<div class="ds-kpi-value">{_e(it["value"])}</div>{sub}</div>'
        )
    st.markdown(f'<div class="ds-kpis">{"".join(cards)}</div>', unsafe_allow_html=True)


def section_title(text: str, hint: str = "") -> None:
    hint_html = f"<small>{_e(hint)}</small>" if hint else ""
    st.markdown(f'<div class="ds-section">{text}{hint_html}</div>', unsafe_allow_html=True)


@contextmanager
def card(title: str = "", subtitle: str = ""):
    """
    كارت حقيقي بيلف الويدجتس اللي جواه (شارت، جدول، فلاتر...):
        with card("مبلغ المديونية لكل مشرف"):
            st.plotly_chart(fig, use_container_width=True)
    """
    with st.container(border=True):
        st.markdown(
            f'<div class="ds-card-title">{title or "&nbsp;"}</div>'
            + (f'<div class="ds-card-sub">{_e(subtitle)}</div>' if subtitle else ""),
            unsafe_allow_html=True,
        )
        yield


def info_box(text: str, kind: str = "info") -> None:
    """kind: info | ok | bad — text يقبل HTML بسيط (<b>)."""
    st.markdown(f'<div class="ds-box {kind}">{text}</div>', unsafe_allow_html=True)


def empty_state(text: str, icon: str = "🎯") -> None:
    st.markdown(
        f'<div class="ds-empty"><span class="ds-empty-icon">{icon}</span>{text}</div>',
        unsafe_allow_html=True,
    )


def sidebar_brand(title: str = "لوحة التحكم", subtitle: str = "إدارة المحافظ والتحصيل", logo: str = "❤️🦅") -> None:
    st.markdown(
        f"""
        <div class="ds-brand">
            <div class="ds-brand-logo">{logo}</div>
            <div>
                <div class="ds-brand-title">{_e(title)}</div>
                <div class="ds-brand-sub">{_e(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 400, angle: int = -20, legend_top: bool = True):
    """ستايل موحّد لكل رسومات plotly (بيشتغل في الوضعين الفاتح والداكن)."""
    tick = "#8390a2"
    fig.update_xaxes(tickfont=dict(size=13, family="Tajawal", color=tick), showline=False)
    fig.update_yaxes(
        tickfont=dict(size=12, family="Tajawal", color=tick),
        gridcolor="rgba(128,140,155,.18)", zeroline=False,
    )
    layout = dict(
        height=height, xaxis_tickangle=angle, margin=dict(t=24, b=10, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Tajawal", color=tick), colorway=PALETTE,
        hoverlabel=dict(font_family="Tajawal"),
    )
    if legend_top:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="")
    fig.update_layout(**layout)
    return fig
