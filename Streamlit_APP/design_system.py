"""
design_system.py  —  النسخة الاحترافية (Corporate / SNB-ready)
==================================================================
نفس أسماء الدوال بالظبط زي القديم، فمفيش أي تغيير مطلوب في app.py:

    inject_design_system, page_header, kpi_row, section_title, card,
    empty_state, info_box, style_fig, sidebar_brand, money_rain, PAGE_THEMES

الفلسفة: تصميم بنكي/مؤسسي هادئ — حدود رفيعة، ظلال ناعمة، ألوان مطفية،
خط Cairo نضيف، من غير أي رسوم كرتونية أو أنيميشن مبالغ فيه. الحركة
مقصورة على fade-in بسيط عند تحميل الصفحة بس.
"""

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import base64
import html as _html
import streamlit as st

_HERE = Path(__file__).resolve().parent
LOGO_CANDIDATES = ["logo.png", "logo.webp", "logo.jpg", "logo.jpeg", "logo.svg"]
BG_CANDIDATES = ["bg.jpg", "bg.jpeg", "bg.png", "bg.webp"]

INK = "#1E2A38"          # نص أساسي (كحلي غامق قريب من الأسود، مش أسود خالص)
MUTED = "#5B6B7C"        # نص ثانوي
BORDER = "#DDE3EA"       # حدود عامة
BG = "#F5F7FA"           # خلفية الصفحة
SURFACE = "#FFFFFF"      # خلفية الكروت

# باليتة مطفية احترافية لكل صفحة — accent فاتح للـ soft، لون غامق للنص فوقه
THEMES = {
    "promises":     dict(accent="#0F6B4F", soft="#E6F2ED"),   # أخضر داكن
    "neglect":      dict(accent="#9B2C2C", soft="#F6E8E8"),   # عنابي
    "distribution": dict(accent="#4C3A8A", soft="#ECE8F6"),   # كحلي بنفسجي
    "activity":     dict(accent="#0E6E80", soft="#E4F1F3"),   # تركواز غامق
    "payments":     dict(accent="#8A6210", soft="#F5EEDD"),   # ذهبي غامق
    "rotation":     dict(accent="#1E4C8A", soft="#E7EEF6"),   # أزرق كحلي
}

PAGE_THEMES = {
    "الوعود القائمة و المكسورة": "promises",
    "الاهمال": "neglect",
    "التوزيع": "distribution",
    "النشاط": "activity",
    "التقرير اليومي للسدادات": "payments",
    "التدوير": "rotation",
}

# ألوان الرسومات (Plotly) — مطفية ومتناسقة، مناسبة لتقرير رسمي
GREEN, GOLD, RED, BLUE, VIOLET, TEAL = (
    "#0F6B4F", "#8A6210", "#9B2C2C", "#1E4C8A", "#4C3A8A", "#0E6E80"
)
PALETTE = [BLUE, GREEN, GOLD, RED, TEAL, VIOLET, "#6B7280", "#9CA3AF"]

_TONES = {"ok": "#0F6B4F", "bad": "#9B2C2C", "warn": "#8A6210", "info": None}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');

:root{
  --ink:__INK__; --muted:__MUTED__; --border:__BORDER__; --bg:__BG__; --surface:__SURFACE__;
  --ds-accent:__ACCENT__; --ds-soft:__SOFT__;
  --radius:10px; --radius-lg:14px;
  --sh-sm:0 1px 2px rgba(20,30,45,.06);
  --sh:0 2px 8px rgba(20,30,45,.08);
  --sh-lg:0 6px 20px rgba(20,30,45,.10);
}

/* ===== الخلفية والخط ===== */
.stApp{ color-scheme:light; color:var(--ink); background:var(--bg) !important; }
html, body{ background:var(--bg) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"]{ background:transparent !important; }
header[data-testid="stHeader"]{ background:transparent; }
.main .block-container{ padding-top:1.6rem; padding-bottom:3rem; max-width:1280px; position:relative; z-index:1; }

/* ===== خلفية ثابتة: صورة حقيقية (bg.jpg) + طبقة تعتيم فاتحة تحافظ على وضوح القراءة ===== */
div[data-testid="stElementContainer"]:has(.ds-bg), .element-container:has(.ds-bg){ height:0 !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
.ds-bg{ position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; background:var(--bg); }
.ds-bg-photo{ position:absolute; inset:0; background-size:cover; background-position:center 30%; }
.ds-bg-overlay{ position:absolute; inset:0; background:linear-gradient(180deg, color-mix(in srgb, var(--bg) 45%, transparent) 0%, color-mix(in srgb, var(--bg) 62%, transparent) 100%); }
.ds-agent{ position:absolute; bottom:-30px; left:-30px; width:360px; opacity:.07; }
@media (max-width:900px){ .ds-agent{ display:none; } .ds-bg-photo{ background-position:center 20%; } }

html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb], .stApp [data-testid="stMarkdownContainer"]{
  font-family:'Cairo','Tajawal',sans-serif;
}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp label,.stApp p{ color:var(--ink); }
.stApp h2,.stApp h3,.stApp h4{ font-weight:700; }
.stApp hr{ border:0; border-top:1px solid var(--border); }

/* ===== الهيدر ===== */
.ds-header{
  display:flex; align-items:center; gap:20px; margin:2px 0 26px 0; padding:22px 26px;
  background:var(--surface); border:1px solid var(--border); border-radius:var(--radius-lg);
  box-shadow:var(--sh-sm); border-right:4px solid var(--ds-accent);
  animation:ds-fade .35s ease-out;
}
.ds-header-logo{
  flex:0 0 auto; width:56px; height:56px; border-radius:10px; overflow:hidden;
  display:flex; align-items:center; justify-content:center; background:var(--ds-soft);
  border:1px solid var(--border);
}
.ds-header-logo img, .ds-header-logo svg{ width:70%; height:70%; object-fit:contain; }
.ds-header-icon{
  flex:0 0 auto; width:52px; height:52px; border-radius:10px; display:flex; align-items:center;
  justify-content:center; font-size:26px; background:var(--ds-soft); color:var(--ds-accent);
  border:1px solid var(--border);
}
.ds-header-body{ min-width:0; }
.ds-header h1{ margin:0 !important; padding:0 !important; font-size:24px; font-weight:700; line-height:1.35; color:var(--ink) !important; }
.ds-header p{ margin:5px 0 0 0; max-width:820px; font-size:14px; font-weight:500; line-height:1.7; color:var(--muted) !important; }
.ds-chips{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }
.ds-chip{
  background:var(--ds-soft); color:var(--ds-accent); font-size:12.5px; font-weight:700; padding:3px 12px;
  border:1px solid var(--border); border-radius:999px;
}

/* ===== بطاقات KPI ===== */
.ds-kpis{ display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:16px; margin:4px 0 12px 0; }
.ds-kpi{
  position:relative; background:var(--surface); border:1px solid var(--border); border-radius:var(--radius);
  padding:16px 18px; box-shadow:var(--sh-sm); border-right:3px solid var(--tone, var(--ds-accent));
  animation:ds-fade .35s ease-out backwards;
}
.ds-kpi-icon{
  width:38px; height:38px; border-radius:8px; font-size:19px; display:flex; align-items:center; justify-content:center;
  background:color-mix(in srgb, var(--tone, var(--ds-accent)) 12%, white); color:var(--tone, var(--ds-accent));
}
.ds-kpi-label{ font-size:13.5px; font-weight:600; color:var(--muted); margin-top:10px; }
.ds-kpi-value{ font-size:28px; font-weight:800; line-height:1.2; color:var(--ink); overflow-wrap:anywhere; }
.ds-kpi-sub{
  display:inline-block; margin-top:8px; padding:1px 10px; font-size:12px; font-weight:600; color:var(--tone, var(--ds-accent));
  background:color-mix(in srgb, var(--tone, var(--ds-accent)) 10%, white); border-radius:999px;
}

/* ===== عناوين الأقسام ===== */
.ds-section{ display:flex; align-items:center; gap:12px; margin:32px 0 16px 0; font-weight:700; font-size:17px; color:var(--ink); }
.ds-section > .ds-sec-label{
  display:inline-block; color:var(--ink); border-right:3px solid var(--ds-accent); padding:2px 12px;
}
.ds-section::after{ content:""; flex:1; border-top:1px solid var(--border); }
.ds-section small{ order:3; font-weight:500; font-size:12.5px; color:var(--muted); }

/* ===== الكروت ===== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){
  background:var(--surface); border:1px solid var(--border) !important; border-radius:var(--radius) !important;
  box-shadow:var(--sh-sm); padding:10px 12px 6px 12px;
}
.ds-card-title{ display:flex; align-items:center; gap:8px; font-weight:700; font-size:15.5px; margin:2px 0 4px 0; color:var(--ink); }
.ds-card-title::before{ content:""; flex:0 0 auto; width:8px; height:8px; border-radius:2px; background:var(--ds-accent); }
.ds-card-sub{ font-size:12.5px; font-weight:500; color:var(--muted); margin:0 0 8px 0; }

/* ===== صناديق المعلومات ===== */
.ds-box{ border:1px solid var(--border); border-radius:var(--radius); padding:12px 18px; margin:0 0 14px 0; font-weight:600; line-height:1.8; color:var(--ink); }
.ds-box.info{ background:#FDF6E3; border-color:#EFE0A8; }
.ds-box.ok{ background:#E6F2ED; border-color:#BFE0D0; }
.ds-box.bad{ background:#F6E8E8; border-color:#E6BFBF; }

/* ===== الحالة الفارغة ===== */
.ds-empty{
  text-align:center; padding:30px 16px; margin:10px 0; border:1.5px dashed var(--border); border-radius:var(--radius-lg);
  background:var(--surface); color:var(--muted); font-weight:600; font-size:15px;
}
.ds-empty .ds-empty-icon{ display:block; font-size:32px; margin-bottom:8px; opacity:.7; }

/* ===== التابات — خط سفلي بدل الحبوب ===== */
div[data-baseweb="tab-list"]{ gap:22px; border-bottom:1px solid var(--border) !important; padding:0; }
div[data-baseweb="tab-border"], div[data-baseweb="tab-highlight"]{ display:none !important; }
button[data-baseweb="tab"]{
  background:transparent !important; color:var(--muted) !important; font-weight:600 !important; font-size:14.5px !important;
  border:0 !important; border-bottom:2px solid transparent !important; border-radius:0 !important;
  padding:8px 2px !important; height:auto !important;
}
button[data-baseweb="tab"][aria-selected="true"]{ color:var(--ds-accent) !important; border-bottom:2px solid var(--ds-accent) !important; }

/* ===== الأزرار ===== */
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button, div[data-testid="stFormSubmitButton"] button{
  background:var(--surface); color:var(--ink); font-weight:600 !important; font-size:14.5px;
  border:1px solid var(--border) !important; border-radius:8px !important; padding:.5rem 1.1rem;
  box-shadow:none; transition:background .12s ease, border-color .12s ease;
}
div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover{
  border-color:var(--ds-accent) !important; color:var(--ds-accent);
}
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
div[data-testid="stDownloadButton"] button[kind="primary"], div[data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"]{
  background:var(--ds-accent) !important; color:#fff !important; border-color:var(--ds-accent) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover{ filter:brightness(1.08); color:#fff !important; }
div[data-testid="stButton"] button:disabled{ opacity:.5; }

/* ===== رفع الملفات ===== */
div[data-testid="stFileUploader"]{ background:var(--surface); border:1.5px dashed var(--border); border-radius:var(--radius-lg); padding:8px; }
div[data-testid="stFileUploader"] section{ background:var(--bg); border:1px solid var(--border); border-radius:8px; }

/* ===== الحقول ===== */
.stApp input, .stApp textarea{ color:var(--ink) !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"], div[data-testid="stTimeInput"] div[data-baseweb="input"]{
  background:var(--surface) !important; border:1px solid var(--border) !important; border-radius:8px !important; box-shadow:none;
}
div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within{ border-color:var(--ds-accent) !important; }
div[data-baseweb="select"] *{ color:var(--ink); }
div[data-baseweb="popover"] ul{ border:1px solid var(--border); border-radius:8px; }
span[data-baseweb="tag"]{ background:var(--ds-soft) !important; color:var(--ds-accent) !important; border:1px solid var(--border); border-radius:6px !important; font-weight:600; }
span[data-baseweb="tag"] *{ color:var(--ds-accent) !important; }
div[data-testid="stSlider"] [role="slider"]{ background:var(--ds-accent) !important; border:2px solid #fff !important; box-shadow:0 0 0 1px var(--ds-accent); }
div[data-testid="stCheckbox"] label{ font-weight:500; }

div[data-testid="stRadio"] div[role="radiogroup"]{ gap:.5rem; }
div[data-testid="stRadio"] label[data-baseweb="radio"]{
  background:var(--surface); border:1px solid var(--border); border-radius:999px; padding:5px 16px; font-weight:600;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){ background:var(--ds-soft); border-color:var(--ds-accent); color:var(--ds-accent); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) *{ color:var(--ds-accent); }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child{ display:none; }

div[data-testid="stProgress"] > div > div{ border:1px solid var(--border); border-radius:999px; background:var(--surface); height:10px; }
div[data-testid="stProgress"] > div > div > div > div{ background:var(--ds-accent) !important; }

/* ===== الجداول ===== */
div[data-testid="stDataFrame"]{ border:1px solid var(--border); border-radius:var(--radius); overflow:hidden; box-shadow:none; background:var(--surface); }

/* ===== Metric ===== */
div[data-testid="stMetric"]{ background:var(--surface); border:1px solid var(--border); border-radius:var(--radius); padding:12px 16px; }
div[data-testid="stMetric"] *{ color:var(--ink) !important; }
div[data-testid="stMetricLabel"] p{ color:var(--muted) !important; font-weight:600; }
div[data-testid="stMetricValue"]{ font-weight:800; }

/* ===== الإكسبندر والتنبيهات ===== */
div[data-testid="stExpander"]{ background:var(--surface); border:1px solid var(--border) !important; border-radius:var(--radius) !important; box-shadow:none; overflow:hidden; }
div[data-testid="stExpander"] summary{ font-weight:600; }
div[data-testid="stAlert"]{ border:1px solid var(--border); border-radius:var(--radius); box-shadow:none; font-weight:500; }
div[data-testid="stAlert"] *{ color:var(--ink) !important; }

/* ===== السايد بار ===== */
section[data-testid="stSidebar"]{ border-left:1px solid var(--border); background:#101B2C; }
section[data-testid="stSidebar"] *{ color:#E7ECF3; }
section[data-testid="stSidebar"] hr{ border-top:1px solid rgba(255,255,255,.12); }
section[data-testid="stSidebar"] div[data-testid="stButton"] button{
  width:100%; justify-content:flex-start; text-align:right; background:transparent; color:#C7D2E0; border:1px solid transparent !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{ background:rgba(255,255,255,.06); color:#fff; border-color:transparent !important; }
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  background:rgba(255,255,255,.10) !important; color:#fff !important; border-right:3px solid var(--ds-accent) !important;
}
.ds-brand{
  display:flex; align-items:center; gap:12px; margin:2px 0 20px 0; padding:14px; background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.10); border-radius:var(--radius);
}
.ds-brand-logo{ flex:0 0 auto; width:44px; height:44px; border-radius:8px; display:flex; align-items:center; justify-content:center; background:#fff; overflow:hidden; }
.ds-brand-logo img, .ds-brand-logo svg{ width:78%; height:78%; object-fit:contain; }
.ds-brand-title{ font-weight:700; font-size:15.5px; line-height:1.25; color:#fff; }
.ds-brand-sub{ font-weight:500; font-size:12px; color:#9FB0C4; }

@media (max-width:760px){
  .ds-header{ flex-direction:column; align-items:flex-start; }
  .ds-header h1{ font-size:20px; }
}

/* ===== حركة دخول بسيطة جدًا ===== */
@keyframes ds-fade{ from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:none;} }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){ animation:ds-fade .3s ease-out backwards; }
.ds-box{ animation:ds-fade .3s ease-out backwards; }

/* ===== توست نجاح بسيط (بديل مطر الفلوس) ===== */
div[data-testid="stElementContainer"]:has(.ds-toast-wrap), .element-container:has(.ds-toast-wrap){ height:0 !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
.ds-toast-wrap{ position:fixed; inset:0; z-index:99999; pointer-events:none; }
.ds-toast{
  position:absolute; top:22px; left:50%; transform:translateX(-50%);
  background:var(--surface); color:var(--ink); font-weight:700; font-size:15px; padding:10px 22px;
  border:1px solid var(--border); border-right:3px solid #0F6B4F; border-radius:8px; box-shadow:var(--sh);
  animation:ds-toast 3s ease-out both;
}
@keyframes ds-toast{
  0%{opacity:0; transform:translate(-50%,-14px);}
  10%{opacity:1; transform:translate(-50%,0);}
  85%{opacity:1;}
  100%{opacity:0; transform:translate(-50%,-8px);}
}

@media (prefers-reduced-motion:reduce){ *, *::before, *::after{ animation:none !important; } }
</style>
"""

_MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}

_BUILTIN_LOGO = (
    '<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="إجادة">'
    '<rect x="6" y="6" width="52" height="52" rx="12" fill="#0F6B4F"/>'
    '<path d="M17 34 L28 45 L48 21" fill="none" stroke="#fff" stroke-width="6" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)


@lru_cache(maxsize=8)
def _data_uri(path_str: str) -> str:
    p = Path(path_str)
    mime = _MIME.get(p.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _find_logo():
    for name in LOGO_CANDIDATES:
        p = _HERE / name
        if p.exists():
            return p
    return None


def _find_bg():
    for name in BG_CANDIDATES:
        p = _HERE / name
        if p.exists():
            return p
    return None


def logo_html(logo=None) -> str:
    p = Path(logo) if logo else _find_logo()
    if p and p.exists():
        return f'<img src="{_data_uri(str(p))}" alt="logo">'
    return _BUILTIN_LOGO


@lru_cache(maxsize=8)
def _agent_svg(accent: str) -> str:
    """
    رسمة فلات مسطحة (illustration) لموظف تحصيل بيرد على مكالمة بابتسامة —
    مرسومة بالكود (مش صورة فوتوغرافية) عشان تفضل خفيفة الوزن ومن غير أي
    مشاكل حقوق ملكية، وتتلون تلقائيًا بلون الصفحة الحالية.
    """
    skin = "#D9A066"
    return f'''
    <svg viewBox="0 0 400 420" xmlns="http://www.w3.org/2000/svg">
      <circle cx="200" cy="220" r="190" fill="{accent}" opacity=".06"/>
      <path d="M110 420 C110 300 145 240 200 240 C255 240 290 300 290 420 Z" fill="#FFFFFF" stroke="{accent}" stroke-width="5"/>
      <rect x="182" y="150" width="36" height="36" rx="10" fill="{skin}"/>
      <circle cx="200" cy="115" r="58" fill="{skin}"/>
      <path d="M138 96 Q200 34 262 96 L272 158 Q200 190 128 158 Z" fill="#FFFFFF" stroke="#D9DEE6" stroke-width="2"/>
      <ellipse cx="200" cy="90" rx="68" ry="13" fill="none" stroke="{INK}" stroke-width="6"/>
      <circle cx="180" cy="116" r="4.5" fill="{INK}"/>
      <circle cx="220" cy="116" r="4.5" fill="{INK}"/>
      <path d="M174 134 Q200 154 226 134" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>
      <path d="M258 195 Q296 150 252 100" fill="none" stroke="#FFFFFF" stroke-width="30" stroke-linecap="round"/>
      <path d="M258 195 Q296 150 252 100" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round"/>
      <rect x="232" y="82" width="28" height="48" rx="9" fill="{accent}"/>
    </svg>
    '''


def inject_design_system(theme: str = "promises", background: str = "plain", bg_gif=None) -> None:
    """
    يتنادى مرة واحدة في كل rerun، بعد set_page_config.
    background و bg_gif اتسابوا في التوقيع بس مش بيتستخدموا هنا —
    التصميم الاحترافي بيستخدم خلفية solid ثابتة + رسمة موظف خفيفة في الركن.
    """
    t = THEMES.get(theme, THEMES["promises"])
    css = (
        _CSS.replace("__INK__", INK)
        .replace("__MUTED__", MUTED)
        .replace("__BORDER__", BORDER)
        .replace("__BG__", BG)
        .replace("__SURFACE__", SURFACE)
        .replace("__ACCENT__", t["accent"])
        .replace("__SOFT__", t["soft"])
    )
    st.markdown(css, unsafe_allow_html=True)

    bg_path = _find_bg()
    if bg_path:
        # صورة حقيقية توضع بجانب design_system.py باسم bg.jpg/bg.png/bg.webp —
        # بتتغطى بطبقة تعتيم فاتحة عشان تفضل خلفية بس ومتأثرش على وضوح المحتوى.
        photo_css = f'background-image:url({_data_uri(str(bg_path))})'
        st.markdown(
            f'<div class="ds-bg"><div class="ds-bg-photo" style="{photo_css}"></div>'
            f'<div class="ds-bg-overlay"></div></div>',
            unsafe_allow_html=True,
        )
    else:
        # مفيش صورة خلفية متاحة — رجوع تلقائي للرسمة المرسومة بالكود
        st.markdown(
            f'<div class="ds-bg"><div class="ds-agent">{_agent_svg(t["accent"])}</div></div>',
            unsafe_allow_html=True,
        )


def _e(x) -> str:
    return _html.escape(str(x))


def money_rain(message: str = "تم إنشاء التقرير", count: int = 0, emojis=None) -> None:
    """
    توست نجاح بسيط بدون أي احتفال بصري (بديل احترافي لمطر الفلوس).
    نفس الاسم والتوقيع القديم عشان app.py يفضل شغال من غير تعديل،
    لكن count/emojis اتجاهلوا عمدًا.
    """
    st.markdown(
        f'<div class="ds-toast-wrap"><div class="ds-toast">✓ {_e(message)}</div></div>',
        unsafe_allow_html=True,
    )


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
            <div class="ds-header-logo">{logo_html()}</div>
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
    with st.container(border=True):
        st.markdown(
            f'<div class="ds-card-title">{title or "&nbsp;"}</div>'
            + (f'<div class="ds-card-sub">{_e(subtitle)}</div>' if subtitle else ""),
            unsafe_allow_html=True,
        )
        yield


def info_box(text: str, kind: str = "info") -> None:
    st.markdown(f'<div class="ds-box {kind}">{text}</div>', unsafe_allow_html=True)


def empty_state(text: str, icon: str = "🎯") -> None:
    st.markdown(
        f'<div class="ds-empty"><span class="ds-empty-icon">{icon}</span>{text}</div>',
        unsafe_allow_html=True,
    )


def sidebar_brand(title: str = "إجادة", subtitle: str = "لتحصيل الديون", logo=None) -> None:
    st.markdown(
        f"""
        <div class="ds-brand">
            <div class="ds-brand-logo">{logo_html(logo)}</div>
            <div>
                <div class="ds-brand-title">{_e(title)}</div>
                <div class="ds-brand-sub">{_e(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 400, angle: int = -20, legend_top: bool = True):
    """رسومات plotly احترافية: ألوان مطفية، خطوط رفيعة، من غير حدود سودا تخينة."""
    fig.update_xaxes(tickfont=dict(size=13, family="Cairo, Tajawal", color=INK),
                     linecolor=BORDER, linewidth=1, showgrid=False)
    fig.update_yaxes(tickfont=dict(size=12, family="Cairo, Tajawal", color=MUTED),
                     gridcolor=BORDER, griddash="dot", zeroline=False)
    layout = dict(
        height=height, xaxis_tickangle=angle, margin=dict(t=20, b=10, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Cairo, Tajawal", color=INK), colorway=PALETTE,
        hoverlabel=dict(font_family="Cairo, Tajawal", bgcolor="#fff", bordercolor=BORDER),
    )
    if legend_top:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="",
                                bordercolor=BORDER, borderwidth=1, bgcolor="#fff")
    fig.update_layout(**layout)
    fig.update_traces(marker_line_color=BORDER, marker_line_width=1, selector=dict(type="bar"))
    fig.update_traces(textfont=dict(color=INK), selector=dict(type="bar"))
    return fig
