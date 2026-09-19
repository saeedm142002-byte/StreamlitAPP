"""
design_system.py  —  النسخة الكرتونية 🎨
========================================
نفس أسماء الدوال بالظبط، فمفيش أي تغيير مطلوب في app.py:

    inject_design_system, page_header, kpi_row, section_title, card,
    empty_state, info_box, style_fig, sidebar_brand, PAGE_THEMES

الستايل: حدود سودا تخينة + ظلال صلبة (من غير blur) + ألوان زاهية +
ستيكرز مايلة شوية + خط Baloo Bhaijaan 2 المدوّر.
(النسخة الهادية القديمة محفوظة في design_system_classic.py)

مهم: الستايل ده مبني على خلفية فاتحة. حط في .streamlit/config.toml:
    [theme]
    base = "light"
"""

from contextlib import contextmanager
import html as _html
import streamlit as st

INK = "#1B1B2F"

# accent = لون الصفحة | soft = نسخة فاتحة | on = لون الكتابة فوق الـ accent | pop = ظل النص
THEMES = {
    "promises":     dict(accent="#2DC26B", soft="#D5F7E2", on="#FFFFFF", pop=INK),
    "neglect":      dict(accent="#FF5A5F", soft="#FFE0E1", on="#FFFFFF", pop=INK),
    "distribution": dict(accent="#8B5CF6", soft="#EADFFF", on="#FFFFFF", pop=INK),
    "activity":     dict(accent="#14B8D4", soft="#D2F5FB", on="#FFFFFF", pop=INK),
    "payments":     dict(accent="#FFC93C", soft="#FFF1C4", on=INK,       pop="#FFFFFF"),
    "rotation":     dict(accent="#3B82F6", soft="#DCE9FF", on="#FFFFFF", pop=INK),
}

PAGE_THEMES = {
    "الوعود القائمة و المكسورة": "promises",
    "الاهمال": "neglect",
    "التوزيع": "distribution",
    "النشاط": "activity",
    "التقرير اليومي للسدادات": "payments",
    "التدوير": "rotation",
}

# ألوان الرسومات
GREEN, GOLD, RED, BLUE, VIOLET, TEAL = (
    "#2DC26B", "#FFC93C", "#FF5A5F", "#3B82F6", "#8B5CF6", "#14B8A6"
)
PALETTE = [BLUE, GOLD, RED, GREEN, VIOLET, TEAL, "#FF8A3D", "#F472B6"]

_TONES = {"ok": "#2DC26B", "bad": "#FF5A5F", "warn": "#FFC93C", "info": None}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Baloo+Bhaijaan+2:wght@400;500;600;700;800&display=swap');

:root{
  --ink:__INK__;
  --ds-accent:__ACCENT__;
  --ds-soft:__SOFT__;
  --ds-on:__ON__;
  --ds-pop:__POP__;
  --ds-muted:#5b5b7a;
  --bw:3px;
  --sh:5px 5px 0 var(--ink);
  --sh-lg:8px 8px 0 var(--ink);
}

/* ===== الخلفية: ورقة كريمي منقطة ===== */
.stApp{
  color-scheme:light; color:var(--ink);
  background-color:#FFF6DC;
  background-image:radial-gradient(rgba(27,27,47,.13) 1.6px, transparent 1.6px);
  background-size:24px 24px;
}
header[data-testid="stHeader"]{ background:transparent; }
.main .block-container{ padding-top:1.4rem; padding-bottom:4rem; max-width:1280px; }

/* ===== الخط (من غير span عشان أيقونات Material) ===== */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb], .stApp [data-testid="stMarkdownContainer"]{
  font-family:'Baloo Bhaijaan 2','Tajawal',sans-serif;
}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp label,.stApp p{ color:var(--ink); }
.stApp h2,.stApp h3,.stApp h4{ font-weight:800; }
.stApp hr{ border:0; border-top:3px dashed var(--ink); opacity:.25; }

/* ===== الهيدر ===== */
.ds-header{
  position:relative; overflow:hidden; display:flex; align-items:center; gap:22px;
  margin:4px 0 30px 0; padding:28px 32px;
  background:var(--ds-accent); border:4px solid var(--ink); border-radius:30px; box-shadow:var(--sh-lg);
}
.ds-header::before{ /* بقع وفقاقيع */
  content:""; position:absolute; inset:0; pointer-events:none;
  background:
    radial-gradient(circle at 92% 18%, rgba(255,255,255,.55) 0 26px, transparent 27px),
    radial-gradient(circle at 84% 78%, rgba(255,255,255,.35) 0 44px, transparent 45px),
    radial-gradient(circle at 6% 88%, rgba(255,255,255,.30) 0 34px, transparent 35px),
    radial-gradient(rgba(27,27,47,.10) 2px, transparent 2px);
  background-size:auto,auto,auto,20px 20px;
}
.ds-header::after{ /* نجمة كرتونية */
  content:"✦"; position:absolute; left:26px; top:8px; font-size:34px; color:#fff;
  text-shadow:2px 2px 0 var(--ink); transform:rotate(12deg); opacity:.95;
}
.ds-header-icon{
  position:relative; z-index:1; flex:0 0 auto; width:76px; height:76px; border-radius:50%;
  display:flex; align-items:center; justify-content:center; font-size:38px;
  background:#fff; border:4px solid var(--ink); box-shadow:4px 4px 0 var(--ink); transform:rotate(-8deg);
}
.ds-header-body{ position:relative; z-index:1; min-width:0; }
.ds-header h1{
  margin:0 !important; padding:0 !important; font-size:34px; font-weight:800; line-height:1.25;
  color:var(--ds-on) !important; text-shadow:3px 3px 0 var(--ds-pop); letter-spacing:.2px;
}
.ds-header p{ margin:6px 0 0 0; max-width:820px; font-size:15.5px; font-weight:600; line-height:1.8; color:var(--ds-on) !important; opacity:.95; }
.ds-chips{ display:flex; flex-wrap:wrap; gap:10px; margin-top:14px; }
.ds-chip{
  background:#fff; color:var(--ink); font-size:13px; font-weight:800; padding:3px 14px;
  border:3px solid var(--ink); border-radius:999px; box-shadow:3px 3px 0 var(--ink);
}
.ds-chip:nth-child(odd){ transform:rotate(-2deg); }
.ds-chip:nth-child(even){ transform:rotate(1.6deg); }

/* ===== بطاقات KPI (ستيكرز) ===== */
.ds-kpis{ display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:22px; margin:6px 0 14px 0; }
.ds-kpi{
  position:relative; background:#fff; border:var(--bw) solid var(--ink); border-radius:24px;
  padding:16px 20px 15px 20px; box-shadow:var(--sh); transition:transform .15s ease, box-shadow .15s ease;
}
.ds-kpi:nth-child(odd){ transform:rotate(-.9deg); }
.ds-kpi:nth-child(even){ transform:rotate(.9deg); }
.ds-kpi:hover{ transform:rotate(0) translate(-3px,-3px); box-shadow:8px 8px 0 var(--ink); }
.ds-kpi-icon{
  width:50px; height:50px; border-radius:50%; font-size:24px; display:flex; align-items:center; justify-content:center;
  background:var(--tone, var(--ds-accent)); border:var(--bw) solid var(--ink); box-shadow:2px 2px 0 var(--ink);
}
.ds-kpi-label{ font-size:14.5px; font-weight:700; color:var(--ds-muted); margin-top:10px; }
.ds-kpi-value{ font-size:34px; font-weight:800; line-height:1.15; color:var(--ink); overflow-wrap:anywhere; }
.ds-kpi-sub{
  display:inline-block; margin-top:8px; padding:0 10px; font-size:12.5px; font-weight:700; color:var(--ink);
  background:color-mix(in srgb, var(--tone, var(--ds-accent)) 35%, white); border:2px solid var(--ink); border-radius:999px;
}

/* ===== عناوين الأقسام (ليبل ستيكر + خط منقط) ===== */
.ds-section{ display:flex; align-items:center; gap:14px; margin:38px 0 18px 0; font-weight:800; font-size:19px; color:var(--ink); }
.ds-section > .ds-sec-label{
  display:inline-block; background:var(--ds-accent); color:var(--ds-on); text-shadow:2px 2px 0 var(--ds-pop);
  padding:5px 20px; border:var(--bw) solid var(--ink); border-radius:16px; box-shadow:4px 4px 0 var(--ink); transform:rotate(-1.2deg);
}
.ds-section::after{ content:""; flex:1; border-top:4px dotted var(--ink); opacity:.35; }
.ds-section small{ order:3; font-weight:700; font-size:13px; color:var(--ds-muted); }

/* ===== الكروت (الحاويات) ===== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){
  background:#fff; border:var(--bw) solid var(--ink) !important; border-radius:24px !important;
  box-shadow:var(--sh); padding:8px 10px 4px 10px;
}
.ds-card-title{ display:flex; align-items:center; gap:10px; font-weight:800; font-size:17px; margin:2px 0 4px 0; color:var(--ink); }
.ds-card-title::before{
  content:""; flex:0 0 auto; width:16px; height:16px; border-radius:50%;
  background:var(--ds-accent); border:3px solid var(--ink);
}
.ds-card-sub{ font-size:13px; font-weight:600; color:var(--ds-muted); margin:0 0 8px 0; }

/* ===== صناديق المعلومات ===== */
.ds-box{
  border:var(--bw) solid var(--ink); border-radius:20px; padding:14px 20px; margin:0 0 16px 0;
  font-weight:700; line-height:1.9; color:var(--ink); box-shadow:4px 4px 0 var(--ink);
}
.ds-box.info{ background:#FFE9A8; }
.ds-box.ok{ background:#BFF1D2; }
.ds-box.bad{ background:#FFC9CB; }

/* ===== الحالة الفارغة ===== */
.ds-empty{
  text-align:center; padding:34px 16px; margin:10px 0; border:4px dashed var(--ink); border-radius:28px;
  background:var(--ds-soft); color:var(--ink); font-weight:800; font-size:16px;
}
.ds-empty .ds-empty-icon{ display:block; font-size:46px; margin-bottom:6px; animation:ds-bob 2.2s ease-in-out infinite; }
@keyframes ds-bob{ 0%,100%{ transform:translateY(0) rotate(-4deg);} 50%{ transform:translateY(-8px) rotate(4deg);} }
@media (prefers-reduced-motion:reduce){ .ds-empty .ds-empty-icon{ animation:none; } .ds-kpi,.ds-kpi:hover{ transition:none; } }

/* ===== التابات (أزرار حبوب) ===== */
div[data-baseweb="tab-list"]{ gap:10px; border:0 !important; padding:6px 2px 10px 2px; flex-wrap:wrap; }
div[data-baseweb="tab-border"], div[data-baseweb="tab-highlight"]{ display:none !important; }
button[data-baseweb="tab"]{
  background:#fff !important; color:var(--ink) !important; font-weight:800 !important; font-size:15px !important;
  border:var(--bw) solid var(--ink) !important; border-radius:999px !important; padding:5px 20px !important; height:auto !important;
  box-shadow:3px 3px 0 var(--ink); transition:transform .12s ease, box-shadow .12s ease;
}
button[data-baseweb="tab"]:hover{ transform:translate(-1px,-1px); box-shadow:4px 4px 0 var(--ink); }
button[data-baseweb="tab"][aria-selected="true"]{
  background:var(--ds-accent) !important; color:var(--ds-on) !important; text-shadow:1.5px 1.5px 0 var(--ds-pop);
}

/* ===== الأزرار (كبس حقيقي) ===== */
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button, div[data-testid="stFormSubmitButton"] button{
  background:#fff; color:var(--ink); font-weight:800 !important; font-size:16px;
  border:var(--bw) solid var(--ink) !important; border-radius:16px !important; padding:.45rem 1.1rem;
  box-shadow:4px 4px 0 var(--ink); transition:transform .1s ease, box-shadow .1s ease;
}
div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover{
  transform:translate(-2px,-2px); box-shadow:6px 6px 0 var(--ink); color:var(--ink);
}
div[data-testid="stButton"] button:active, div[data-testid="stDownloadButton"] button:active{
  transform:translate(4px,4px); box-shadow:0 0 0 var(--ink);
}
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
div[data-testid="stDownloadButton"] button[kind="primary"], div[data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"]{
  background:var(--ds-accent) !important; color:var(--ds-on) !important; text-shadow:2px 2px 0 var(--ds-pop);
}
div[data-testid="stButton"] button[kind="primary"]:hover{ color:var(--ds-on) !important; filter:brightness(1.04); }
div[data-testid="stButton"] button:disabled{ opacity:.5; box-shadow:2px 2px 0 var(--ink); }

/* ===== رفع الملفات ===== */
div[data-testid="stFileUploader"]{
  background:var(--ds-soft); border:4px dashed var(--ink); border-radius:26px; padding:10px;
}
div[data-testid="stFileUploader"] section{ background:#fff; border:var(--bw) solid var(--ink); border-radius:18px; }
div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] span{ color:var(--ink); }

/* ===== الحقول ===== */
.stApp input, .stApp textarea{ color:var(--ink) !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"], div[data-testid="stTimeInput"] div[data-baseweb="input"]{
  background:#fff !important; border:var(--bw) solid var(--ink) !important; border-radius:14px !important; box-shadow:3px 3px 0 var(--ink);
}
div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within{ box-shadow:5px 5px 0 var(--ds-accent); }
div[data-baseweb="select"] *{ color:var(--ink); }
div[data-baseweb="popover"] ul{ border:var(--bw) solid var(--ink); border-radius:14px; }
span[data-baseweb="tag"]{
  background:var(--ds-accent) !important; color:var(--ds-on) !important; border:2px solid var(--ink); border-radius:999px !important; font-weight:800;
}
span[data-baseweb="tag"] *{ color:var(--ds-on) !important; }
div[data-testid="stSlider"] [role="slider"]{ background:var(--ds-accent) !important; border:3px solid var(--ink) !important; box-shadow:2px 2px 0 var(--ink); }
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div{ height:8px; border-radius:99px; }
div[data-testid="stCheckbox"] label{ font-weight:700; }
div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] > span{ border:3px solid var(--ink) !important; border-radius:8px !important; }
div[data-testid="stCheckbox"] input:checked + div{ background:var(--ds-accent) !important; }

div[data-testid="stRadio"] div[role="radiogroup"]{ gap:.6rem; }
div[data-testid="stRadio"] label[data-baseweb="radio"]{
  background:#fff; border:var(--bw) solid var(--ink); border-radius:999px; padding:5px 18px; font-weight:800;
  box-shadow:3px 3px 0 var(--ink); transition:transform .1s ease;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover{ transform:translate(-1px,-1px); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){ background:var(--ds-accent); color:var(--ds-on); text-shadow:1.5px 1.5px 0 var(--ds-pop); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) *{ color:var(--ds-on); }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child{ display:none; }

div[data-testid="stProgress"] > div > div{ border:var(--bw) solid var(--ink); border-radius:999px; background:#fff; height:16px; }
div[data-testid="stProgress"] > div > div > div > div{ background:var(--ds-accent) !important; }

/* ===== الجداول ===== */
div[data-testid="stDataFrame"]{ border:var(--bw) solid var(--ink); border-radius:20px; overflow:hidden; box-shadow:var(--sh); background:#fff; }

/* ===== Metric الأصلي ===== */
div[data-testid="stMetric"]{ background:#fff; border:var(--bw) solid var(--ink); border-radius:22px; padding:12px 18px; box-shadow:var(--sh); }
div[data-testid="stMetric"] *{ color:var(--ink) !important; }
div[data-testid="stMetricLabel"] p{ color:var(--ds-muted) !important; font-weight:700; }
div[data-testid="stMetricValue"]{ font-weight:800; }

/* ===== الإكسبندر والتنبيهات ===== */
div[data-testid="stExpander"]{ background:#fff; border:var(--bw) solid var(--ink) !important; border-radius:20px !important; box-shadow:4px 4px 0 var(--ink); overflow:hidden; }
div[data-testid="stExpander"] summary{ font-weight:800; }
div[data-testid="stExpander"] summary:hover{ background:var(--ds-soft); }
div[data-testid="stAlert"]{ border:var(--bw) solid var(--ink); border-radius:20px; box-shadow:4px 4px 0 var(--ink); font-weight:700; }
div[data-testid="stAlert"] *{ color:var(--ink) !important; }
div[data-testid="stSpinner"] *{ color:var(--ink); font-weight:700; }

/* ===== السايد بار (أصفر) ===== */
section[data-testid="stSidebar"]{
  background-color:#FFD23F; border-left:4px solid var(--ink);
  background-image:radial-gradient(rgba(27,27,47,.16) 1.6px, transparent 1.6px); background-size:20px 20px;
}
section[data-testid="stSidebar"] *{ color:var(--ink); }
section[data-testid="stSidebar"] hr{ border-top:3px dashed var(--ink); opacity:.35; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button{
  width:100%; justify-content:flex-start; text-align:right; background:#fff; color:var(--ink);
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  background:var(--ds-accent) !important; color:var(--ds-on) !important; transform:translate(-2px,-2px); box-shadow:6px 6px 0 var(--ink);
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] *{ color:var(--ds-on) !important; }
.ds-brand{
  display:flex; align-items:center; gap:12px; margin:4px 0 18px 0; padding:12px 14px; background:#fff;
  border:var(--bw) solid var(--ink); border-radius:22px; box-shadow:5px 5px 0 var(--ink); transform:rotate(-1.4deg);
}
.ds-brand-logo{
  flex:0 0 auto; width:50px; height:50px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  font-size:22px; background:var(--ds-accent); border:var(--bw) solid var(--ink);
}
.ds-brand-title{ font-weight:800; font-size:18px; line-height:1.2; color:var(--ink); }
.ds-brand-sub{ font-weight:600; font-size:12.5px; color:var(--ds-muted); }

@media (max-width:760px){
  .ds-header{ flex-direction:column; align-items:flex-start; padding:22px; }
  .ds-header h1{ font-size:26px; }
}
</style>
"""


def inject_design_system(theme: str = "promises") -> None:
    """يتنادى مرة واحدة في كل rerun، بعد set_page_config."""
    t = THEMES.get(theme, THEMES["promises"])
    css = (
        _CSS.replace("__INK__", INK)
        .replace("__ACCENT__", t["accent"])
        .replace("__SOFT__", t["soft"])
        .replace("__ON__", t["on"])
        .replace("__POP__", t["pop"])
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
    """items: dicts فيها icon, label, value, sub (اختياري), tone: ok|bad|warn|info"""
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
    st.markdown(
        f'<div class="ds-section"><span class="ds-sec-label">{text}</span>{hint_html}</div>',
        unsafe_allow_html=True,
    )


@contextmanager
def card(title: str = "", subtitle: str = ""):
    """
    كارت حقيقي بيلف الويدجتس اللي جواه:
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
    """رسومات plotly كرتونية: أعمدة بحدود سودا وألوان زاهية."""
    fig.update_xaxes(tickfont=dict(size=14, family="Baloo Bhaijaan 2, Tajawal", color=INK),
                     linecolor=INK, linewidth=3, showgrid=False)
    fig.update_yaxes(tickfont=dict(size=13, family="Baloo Bhaijaan 2, Tajawal", color=INK),
                     gridcolor="rgba(27,27,47,.14)", griddash="dot", zeroline=False)
    layout = dict(
        height=height, xaxis_tickangle=angle, margin=dict(t=24, b=10, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Baloo Bhaijaan 2, Tajawal", color=INK), colorway=PALETTE,
        hoverlabel=dict(font_family="Baloo Bhaijaan 2, Tajawal", bgcolor="#fff", bordercolor=INK),
    )
    if legend_top:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="",
                                bordercolor=INK, borderwidth=2, bgcolor="#fff")
    fig.update_layout(**layout)
    fig.update_traces(marker_line_color=INK, marker_line_width=2.5, selector=dict(type="bar"))
    fig.update_traces(textfont=dict(color=INK), selector=dict(type="bar"))
    return fig
