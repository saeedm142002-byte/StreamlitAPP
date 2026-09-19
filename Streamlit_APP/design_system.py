"""
design_system.py  —  النسخة الاحترافية / Corporate Edition 🖤💛
================================================================
نفس أسماء الدوال بالظبط، فمفيش أي تغيير مطلوب في app.py:

    inject_design_system, page_header, kpi_row, section_title, card,
    empty_state, info_box, style_fig, sidebar_brand, PAGE_THEMES

الستايل: هوية "إجادة" الفعلية (كحلي غامق + لمسة ذهبية)، خط Cairo
الاحترافي، ظلال ناعمة (soft shadow) بدل الظل الصلب، حواف مدورة
هادئة، سايدبار غامق راقي، وكروت بيضاء نضيفة بتوحي بالثقة والاحترافية
اللي تليق بشركة تحصيل ديون.

مهم: الستايل ده مبني على خلفية فاتحة. حط في .streamlit/config.toml:
    [theme]
    base = "light"

اللوجو: حط ملف logo.png (الشعار مفرّغ الخلفية) جنب الملف ده، وهيتظهر
أوتوماتيك في الهيدر والسايدبار. لو عندك نسخة الشعار من غير الاسم
(الأيقونة/الرمز لوحدها) سمّيها logo-mark.png وهي اللي هتتستخدم في
الدوائر الصغيرة (الهيدر والسايدبار) عشان تبان واضحة ومظبوطة.
"""

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import base64
import html as _html
import streamlit as st

_HERE = Path(__file__).resolve().parent
LOGO_MARK_CANDIDATES = ["logo-mark.png", "logo-mark.webp", "logo-mark.svg", "logo-icon.png"]
LOGO_CANDIDATES = ["logo.png", "logo.webp", "logo.jpg", "logo.jpeg", "logo.svg"]

# ===== هوية إجادة =====
INK        = "#16233D"   # كحلي غامق - النص الأساسي
NAVY       = "#16233D"
NAVY_DEEP  = "#0B1626"   # كحلي شبه أسود - السايدبار
NAVY_MID   = "#1E3A63"
NAVY_SOFT  = "#EEF2F8"
GOLD       = "#C9971F"   # ذهبي - لمسة تميّز
MUTED      = "#64748B"
BORDER     = "#E3E8F0"
BG         = "#F4F6FA"

# accent = لون التمييز الخاص بالصفحة | soft = خلفية فاتحة منه | on = لون الكتابة فوقه | glow = هالة الهيدر
THEMES = {
    "promises":     dict(accent="#0E9F6E", soft="#E5F6EF", on="#FFFFFF"),  # أخضر زمردي - وعود
    "neglect":      dict(accent="#D5484F", soft="#FBE9EA", on="#FFFFFF"),  # أحمر هادي - إهمال
    "distribution": dict(accent="#6C5DD3", soft="#EEEAFB", on="#FFFFFF"),  # بنفسجي - توزيع
    "activity":     dict(accent="#1596B7", soft="#E3F4F8", on="#FFFFFF"),  # تركواز - نشاط
    "payments":     dict(accent="#C9971F", soft="#FBF1DC", on="#FFFFFF"),  # ذهبي - سدادات
    "rotation":     dict(accent="#2F5FA8", soft="#E7EEF8", on="#FFFFFF"),  # أزرق - تدوير
}

PAGE_THEMES = {
    "الوعود القائمة و المكسورة": "promises",
    "الاهمال": "neglect",
    "التوزيع": "distribution",
    "النشاط": "activity",
    "التقرير اليومي للسدادات": "payments",
    "التدوير": "rotation",
}

# ألوان الرسومات - لوحة احترافية هادية مبنية على هوية إجادة
# (نفس الأسماء القديمة GREEN/GOLD/RED/BLUE/VIOLET/TEAL محتفظ بيها عشان أي
#  استيراد مباشر ليها في app.py يفضل شغال من غير أي تعديل هناك)
GREEN, RED, VIOLET, TEAL, BLUE, SLATE = (
    "#0E9F6E", "#D5484F", "#6C5DD3", "#1596B7", "#2F5FA8", "#7C8CA6"
)
PALETTE = [NAVY, GOLD, RED, GREEN, VIOLET, TEAL, BLUE, SLATE]

_TONES = {"ok": "#0E9F6E", "bad": "#D5484F", "warn": "#C9971F", "info": None}

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap');

:root{
  --ink:__INK__;
  --navy-deep:__NAVY_DEEP__;
  --navy-mid:__NAVY_MID__;
  --gold:__GOLD__;
  --ds-accent:__ACCENT__;
  --ds-soft:__SOFT__;
  --ds-on:__ON__;
  --ds-muted:__MUTED__;
  --ds-border:__BORDER__;
  --ds-bg:__BG__;
  --radius-lg:20px;
  --radius-md:14px;
  --radius-sm:10px;
  --shadow-sm:0 2px 8px rgba(11,22,38,.06);
  --shadow-md:0 8px 24px rgba(11,22,38,.09);
  --shadow-lg:0 16px 40px rgba(11,22,38,.14);
}

/* ===== الخلفية ===== */
.stApp{ color-scheme:light; color:var(--ink); background:transparent !important; }
html, body{ background:var(--ds-bg) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"]{ background:transparent !important; }
header[data-testid="stHeader"]{ background:transparent; }
.main .block-container{ padding-top:1.6rem; padding-bottom:4rem; max-width:1280px; }

/* ===== الخط ===== */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2,
.stApp h3, .stApp h4, .stApp button, .stApp input, .stApp textarea,
.stApp [data-baseweb], .stApp [data-testid="stMarkdownContainer"]{
  font-family:'Cairo','Tajawal',sans-serif;
}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp label,.stApp p{ color:var(--ink); }
.stApp h2,.stApp h3,.stApp h4{ font-weight:800; }
.stApp hr{ border:0; border-top:1px solid var(--ds-border); }

/* ===== الهيدر ===== */
.ds-header{
  position:relative; overflow:hidden; display:flex; align-items:center; gap:24px;
  margin:4px 0 32px 0; padding:30px 36px;
  background:linear-gradient(120deg, var(--navy-deep) 0%, var(--navy-mid) 55%, __ACCENT__ 165%);
  border-radius:var(--radius-lg); box-shadow:var(--shadow-lg);
}
.ds-header::before{
  content:""; position:absolute; inset:0; pointer-events:none; opacity:.5;
  background-image:radial-gradient(circle at 88% -10%, rgba(201,151,31,.35), transparent 45%),
                    radial-gradient(circle at 100% 100%, rgba(255,255,255,.08), transparent 55%);
}
.ds-header::after{
  content:""; position:absolute; left:-40px; top:-60px; width:220px; height:220px; border-radius:50%;
  background:radial-gradient(circle, rgba(255,255,255,.06), transparent 70%); pointer-events:none;
}
.ds-header-logo{
  position:relative; z-index:1; flex:0 0 auto; width:82px; height:82px; border-radius:20px;
  display:flex; align-items:center; justify-content:center; background:#fff;
  box-shadow:var(--shadow-md); padding:10px;
}
.ds-header-logo img, .ds-header-logo svg{ width:100%; height:100%; object-fit:contain; }
.ds-header-icon{
  position:relative; z-index:1; flex:0 0 auto; width:60px; height:60px; border-radius:16px;
  display:flex; align-items:center; justify-content:center; font-size:30px;
  background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.18); backdrop-filter:blur(6px);
}
.ds-header-body{ position:relative; z-index:1; min-width:0; }
.ds-header h1{
  margin:0 !important; padding:0 !important; font-size:30px; font-weight:800; line-height:1.3;
  color:#fff !important; letter-spacing:.2px;
}
.ds-header p{ margin:8px 0 0 0; max-width:820px; font-size:15px; font-weight:500; line-height:1.85; color:rgba(255,255,255,.82) !important; }
.ds-chips{ display:flex; flex-wrap:wrap; gap:9px; margin-top:16px; }
.ds-chip{
  background:rgba(255,255,255,.12); color:#fff; font-size:12.5px; font-weight:700; padding:5px 15px;
  border:1px solid rgba(255,255,255,.22); border-radius:999px; backdrop-filter:blur(4px);
}

/* ===== بطاقات KPI ===== */
.ds-kpis{ display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:18px; margin:6px 0 16px 0; }
.ds-kpi{
  position:relative; background:#fff; border:1px solid var(--ds-border); border-radius:var(--radius-md);
  padding:18px 20px 17px 20px; box-shadow:var(--shadow-sm); transition:transform .18s ease, box-shadow .18s ease;
  overflow:hidden;
}
.ds-kpi::before{
  content:""; position:absolute; inset-inline-start:0; top:0; bottom:0; width:4px; background:var(--tone, var(--ds-accent));
}
.ds-kpi:hover{ transform:translateY(-3px); box-shadow:var(--shadow-md); }
.ds-kpi-icon{
  width:46px; height:46px; border-radius:13px; font-size:22px; display:flex; align-items:center; justify-content:center;
  background:color-mix(in srgb, var(--tone, var(--ds-accent)) 14%, white);
}
.ds-kpi-label{ font-size:14px; font-weight:600; color:var(--ds-muted); margin-top:12px; }
.ds-kpi-value{ font-size:30px; font-weight:800; line-height:1.2; color:var(--ink); overflow-wrap:anywhere; margin-top:2px; }
.ds-kpi-sub{
  display:inline-block; margin-top:9px; padding:0 10px; height:22px; line-height:22px; font-size:12px; font-weight:700;
  color:var(--tone, var(--ds-accent)); background:color-mix(in srgb, var(--tone, var(--ds-accent)) 12%, white); border-radius:999px;
}

/* ===== عناوين الأقسام ===== */
.ds-section{ display:flex; align-items:center; gap:12px; margin:40px 0 18px 0; font-weight:800; font-size:18px; color:var(--ink); }
.ds-section > .ds-sec-label{ display:flex; align-items:center; gap:10px; }
.ds-section > .ds-sec-label::before{
  content:""; width:8px; height:22px; border-radius:4px; background:var(--ds-accent); display:inline-block;
}
.ds-section::after{ content:""; flex:1; border-top:1px solid var(--ds-border); }
.ds-section small{ order:3; font-weight:600; font-size:12.5px; color:var(--ds-muted); }

/* ===== الكروت ===== */
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){
  background:#fff; border:1px solid var(--ds-border) !important; border-radius:var(--radius-md) !important;
  box-shadow:var(--shadow-sm); padding:10px 14px 6px 14px; transition:box-shadow .18s ease;
}
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title):hover{ box-shadow:var(--shadow-md); }
.ds-card-title{ display:flex; align-items:center; gap:9px; font-weight:800; font-size:16.5px; margin:3px 0 4px 0; color:var(--ink); }
.ds-card-title::before{
  content:""; flex:0 0 auto; width:9px; height:9px; border-radius:3px; background:var(--ds-accent);
}
.ds-card-sub{ font-size:13px; font-weight:500; color:var(--ds-muted); margin:0 0 10px 0; }

/* ===== صناديق المعلومات ===== */
.ds-box{
  position:relative; border:1px solid var(--ds-border); border-inline-start:4px solid var(--edge, var(--ds-accent));
  border-radius:var(--radius-sm); padding:14px 20px; margin:0 0 16px 0;
  font-weight:600; line-height:1.9; color:var(--ink); background:#fff; box-shadow:var(--shadow-sm);
}
.ds-box.info{ --edge:#2F5FA8; background:#F3F7FC; }
.ds-box.ok{ --edge:#0E9F6E; background:#EEFBF5; }
.ds-box.bad{ --edge:#D5484F; background:#FDF0F1; }

/* ===== الحالة الفارغة ===== */
.ds-empty{
  text-align:center; padding:40px 16px; margin:10px 0; border:1.5px dashed var(--ds-border); border-radius:var(--radius-lg);
  background:#fff; color:var(--ds-muted); font-weight:700; font-size:15.5px;
}
.ds-empty .ds-empty-icon{ display:block; font-size:42px; margin-bottom:8px; opacity:.85; }
@media (prefers-reduced-motion:reduce){ .ds-kpi,.ds-kpi:hover{ transition:none; } }

/* ===== التابات ===== */
div[data-baseweb="tab-list"]{
  gap:4px; border:0 !important; padding:5px; flex-wrap:wrap; background:#fff; border-radius:999px;
  border:1px solid var(--ds-border); width:fit-content; box-shadow:var(--shadow-sm);
}
div[data-baseweb="tab-border"], div[data-baseweb="tab-highlight"]{ display:none !important; }
button[data-baseweb="tab"]{
  background:transparent !important; color:var(--ds-muted) !important; font-weight:700 !important; font-size:14.5px !important;
  border:0 !important; border-radius:999px !important; padding:7px 20px !important; height:auto !important;
  transition:background .15s ease, color .15s ease;
}
button[data-baseweb="tab"]:hover{ color:var(--ink) !important; }
button[data-baseweb="tab"][aria-selected="true"]{
  background:var(--navy-deep) !important; color:#fff !important; box-shadow:var(--shadow-sm);
}

/* ===== الأزرار ===== */
div[data-testid="stButton"] button, div[data-testid="stDownloadButton"] button, div[data-testid="stFormSubmitButton"] button{
  background:#fff; color:var(--ink); font-weight:700 !important; font-size:15px;
  border:1px solid var(--ds-border) !important; border-radius:var(--radius-sm) !important; padding:.5rem 1.2rem;
  box-shadow:var(--shadow-sm); transition:transform .12s ease, box-shadow .12s ease, filter .12s ease;
}
div[data-testid="stButton"] button:hover, div[data-testid="stDownloadButton"] button:hover{
  transform:translateY(-1px); box-shadow:var(--shadow-md); color:var(--ink);
}
div[data-testid="stButton"] button:active, div[data-testid="stDownloadButton"] button:active{ transform:translateY(0); filter:brightness(.97); }
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stButton"] button[data-testid="stBaseButton-primary"],
div[data-testid="stDownloadButton"] button[kind="primary"], div[data-testid="stDownloadButton"] button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(120deg, var(--navy-deep), var(--navy-mid)) !important; color:#fff !important; border:1px solid var(--navy-deep) !important;
}
div[data-testid="stButton"] button[kind="primary"]:hover{ color:#fff !important; filter:brightness(1.08); }
div[data-testid="stButton"] button:disabled{ opacity:.5; box-shadow:none; }

/* ===== رفع الملفات ===== */
div[data-testid="stFileUploader"]{ background:#fff; border:1.5px dashed var(--ds-border); border-radius:var(--radius-md); padding:10px; }
div[data-testid="stFileUploader"] section{ background:var(--ds-bg); border:1px solid var(--ds-border); border-radius:var(--radius-sm); }
div[data-testid="stFileUploader"] small, div[data-testid="stFileUploader"] span{ color:var(--ink); }

/* ===== الحقول ===== */
.stApp input, .stApp textarea{ color:var(--ink) !important; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, div[data-baseweb="textarea"], div[data-testid="stTimeInput"] div[data-baseweb="input"]{
  background:#fff !important; border:1px solid var(--ds-border) !important; border-radius:var(--radius-sm) !important; box-shadow:none !important;
  transition:border-color .15s ease, box-shadow .15s ease;
}
div[data-baseweb="select"] > div:focus-within, div[data-baseweb="input"] > div:focus-within{
  border-color:var(--ds-accent) !important; box-shadow:0 0 0 3px color-mix(in srgb, var(--ds-accent) 18%, transparent) !important;
}
div[data-baseweb="select"] *{ color:var(--ink); }
div[data-baseweb="popover"] ul{ border:1px solid var(--ds-border); border-radius:var(--radius-sm); box-shadow:var(--shadow-md); }
span[data-baseweb="tag"]{
  background:var(--navy-deep) !important; color:#fff !important; border:0; border-radius:8px !important; font-weight:700;
}
span[data-baseweb="tag"] *{ color:#fff !important; }
div[data-testid="stSlider"] [role="slider"]{ background:var(--ds-accent) !important; border:3px solid #fff !important; box-shadow:0 0 0 1px var(--ds-accent); }
div[data-testid="stSlider"] div[data-baseweb="slider"] > div > div{ height:6px; border-radius:99px; }
div[data-testid="stCheckbox"] label{ font-weight:600; }
div[data-testid="stCheckbox"] span[data-baseweb="checkbox"] > span{ border:1.5px solid var(--ds-border) !important; border-radius:6px !important; }
div[data-testid="stCheckbox"] input:checked + div{ background:var(--navy-deep) !important; }

div[data-testid="stRadio"] div[role="radiogroup"]{ gap:.5rem; }
div[data-testid="stRadio"] label[data-baseweb="radio"]{
  background:#fff; border:1px solid var(--ds-border); border-radius:999px; padding:6px 18px; font-weight:700;
  transition:border-color .12s ease, background .12s ease;
}
div[data-testid="stRadio"] label[data-baseweb="radio"]:hover{ border-color:var(--ds-accent); }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked){ background:var(--navy-deep); border-color:var(--navy-deep); color:#fff; }
div[data-testid="stRadio"] label[data-baseweb="radio"]:has(input:checked) *{ color:#fff; }
div[data-testid="stRadio"] label[data-baseweb="radio"] > div:first-child{ display:none; }

div[data-testid="stProgress"] > div > div{ border-radius:999px; background:var(--ds-border); height:10px; }
div[data-testid="stProgress"] > div > div > div > div{ background:linear-gradient(90deg, var(--navy-mid), var(--ds-accent)) !important; }

/* ===== الجداول ===== */
div[data-testid="stDataFrame"]{ border:1px solid var(--ds-border); border-radius:var(--radius-md); overflow:hidden; box-shadow:var(--shadow-sm); background:#fff; }

/* ===== Metric الأصلي ===== */
div[data-testid="stMetric"]{ background:#fff; border:1px solid var(--ds-border); border-radius:var(--radius-md); padding:14px 18px; box-shadow:var(--shadow-sm); }
div[data-testid="stMetric"] *{ color:var(--ink) !important; }
div[data-testid="stMetricLabel"] p{ color:var(--ds-muted) !important; font-weight:600; }
div[data-testid="stMetricValue"]{ font-weight:800; }

/* ===== الإكسبندر والتنبيهات ===== */
div[data-testid="stExpander"]{ background:#fff; border:1px solid var(--ds-border) !important; border-radius:var(--radius-md) !important; box-shadow:var(--shadow-sm); overflow:hidden; }
div[data-testid="stExpander"] summary{ font-weight:700; }
div[data-testid="stExpander"] summary:hover{ background:var(--ds-bg); }
div[data-testid="stAlert"]{ border:1px solid var(--ds-border); border-inline-start:4px solid var(--ds-accent); border-radius:var(--radius-sm); box-shadow:var(--shadow-sm); font-weight:600; }
div[data-testid="stAlert"] *{ color:var(--ink) !important; }
div[data-testid="stSpinner"] *{ color:var(--ink); font-weight:600; }

/* ===== السايد بار ===== */
section[data-testid="stSidebar"]{
  border-inline-start:1px solid rgba(255,255,255,.06);
  background:linear-gradient(180deg, var(--navy-deep) 0%, #0E1B30 100%);
}
section[data-testid="stSidebar"] *{ color:rgba(255,255,255,.88); }
section[data-testid="stSidebar"] hr{ border-top:1px solid rgba(255,255,255,.10); }
section[data-testid="stSidebar"] div[data-testid="stButton"] button{
  width:100%; justify-content:flex-start; text-align:right; background:transparent; color:rgba(255,255,255,.82);
  border:1px solid transparent !important; box-shadow:none;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button:hover{
  background:rgba(255,255,255,.06); border-color:rgba(255,255,255,.10) !important; color:#fff;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"],
section[data-testid="stSidebar"] div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  background:linear-gradient(120deg, var(--gold), #E0B54A) !important; color:var(--navy-deep) !important; font-weight:800 !important;
  border:0 !important; box-shadow:0 4px 14px rgba(201,151,31,.35);
}
section[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="primary"] *{ color:var(--navy-deep) !important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] > div, section[data-testid="stSidebar"] div[data-baseweb="input"] > div{
  background:rgba(255,255,255,.06) !important; border:1px solid rgba(255,255,255,.12) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] *{ color:#fff; }

.ds-brand{
  display:flex; align-items:center; gap:13px; margin:4px 0 22px 0; padding:14px 16px;
  background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.10); border-radius:var(--radius-md);
}
.ds-brand-logo{
  flex:0 0 auto; width:50px; height:50px; border-radius:13px; display:flex; align-items:center; justify-content:center;
  background:#fff; padding:7px; box-shadow:var(--shadow-sm);
}
.ds-brand-logo img, .ds-brand-logo svg{ width:100%; height:100%; object-fit:contain; }
.ds-brand-title{ font-weight:800; font-size:17px; line-height:1.25; color:#fff; }
.ds-brand-sub{ font-weight:500; font-size:12px; color:rgba(255,255,255,.55); }

/* ===== سكرول بار أنيق ===== */
::-webkit-scrollbar{ width:9px; height:9px; }
::-webkit-scrollbar-track{ background:transparent; }
::-webkit-scrollbar-thumb{ background:#C7D0DE; border-radius:99px; }
::-webkit-scrollbar-thumb:hover{ background:#AEB9CC; }
section[data-testid="stSidebar"] ::-webkit-scrollbar-thumb{ background:rgba(255,255,255,.18); }

@media (max-width:760px){
  .ds-header{ flex-direction:column; align-items:flex-start; padding:24px; }
  .ds-header h1{ font-size:24px; }
}

/* ===== خلفية الصفحة (هادية واحترافية) ===== */
div[data-testid="stElementContainer"]:has(.ds-bg), .element-container:has(.ds-bg){ height:0 !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
.ds-bg{ position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden; background:var(--ds-bg); }
.ds-bg::before{
  content:""; position:absolute; top:-220px; right:-160px; width:620px; height:620px; border-radius:50%;
  background:radial-gradient(circle, color-mix(in srgb, var(--ds-accent) 14%, transparent), transparent 70%);
}
.ds-bg::after{
  content:""; position:absolute; bottom:-260px; left:-200px; width:640px; height:640px; border-radius:50%;
  background:radial-gradient(circle, rgba(22,35,61,.06), transparent 70%);
}
.ds-bg.custom{ background-size:cover; background-position:center; }
.ds-bg.custom::before, .ds-bg.custom::after{ display:none; }
</style>
"""


# ----------------------------------------------------------------------
# اللوجو: بيدوّر على logo-mark.* (للدوائر الصغيرة زي الهيدر والسايدبار)،
# وإلا logo.* (الشعار الكامل)، وإلا الأيقونة المدمجة كحل احتياطي.
# ----------------------------------------------------------------------
_MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}

_BUILTIN_MARK = (
    '<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="إجادة">'
    '<circle cx="32" cy="32" r="30" fill="#16233D"/>'
    '<path d="M18 33 L28 43 L46 21" fill="none" stroke="#C9971F" stroke-width="6" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)


@lru_cache(maxsize=8)
def _data_uri(path_str: str) -> str:
    p = Path(path_str)
    mime = _MIME.get(p.suffix.lower(), "application/octet-stream")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def _find(names):
    for name in names:
        p = _HERE / name
        if p.exists():
            return p
    return None


def logo_html(logo=None, mark: bool = True) -> str:
    """
    logo: مسار صورة اختياري (بيتجاهل البحث التلقائي لو اتحدد).
    mark: True (افتراضي) => يفضّل الشعار المفرّغ بدون الاسم (للدوائر الصغيرة).
          False => يفضّل الشعار الكامل (بالاسم).
    """
    if logo:
        p = Path(logo)
        if p.exists():
            return f'<img src="{_data_uri(str(p))}" alt="logo">'
    order = [LOGO_MARK_CANDIDATES, LOGO_CANDIDATES] if mark else [LOGO_CANDIDATES, LOGO_MARK_CANDIDATES]
    for candidates in order:
        p = _find(candidates)
        if p:
            return f'<img src="{_data_uri(str(p))}" alt="logo">'
    return _BUILTIN_MARK


def _background_html(theme="promises", bg_gif=None) -> str:
    if bg_gif and Path(bg_gif).exists():
        return f'<div class="ds-bg custom" style="background-image:url({_data_uri(str(Path(bg_gif)))})"></div>'
    return '<div class="ds-bg"></div>'


def inject_design_system(theme: str = "promises", background: str = "scene", bg_gif=None) -> None:
    """
    يتنادى مرة واحدة في كل rerun، بعد set_page_config.
    background: "scene" (هالة لونية هادية خلف المحتوى، الافتراضي) | "plain" (خلفية مصمتة بس)
    bg_gif: مسار صورة اختيارية تستخدمها كخلفية بدل الهالة.
    """
    t = THEMES.get(theme, THEMES["promises"])
    css = (
        _CSS.replace("__INK__", INK)
        .replace("__NAVY_DEEP__", NAVY_DEEP)
        .replace("__NAVY_MID__", NAVY_MID)
        .replace("__GOLD__", GOLD)
        .replace("__ACCENT__", t["accent"])
        .replace("__SOFT__", t["soft"])
        .replace("__ON__", t["on"])
        .replace("__MUTED__", MUTED)
        .replace("__BORDER__", BORDER)
        .replace("__BG__", BG)
    )
    st.markdown(css, unsafe_allow_html=True)
    if background == "plain" and not bg_gif:
        st.markdown('<div class="ds-bg"></div>', unsafe_allow_html=True)
    else:
        st.markdown(_background_html(theme, bg_gif), unsafe_allow_html=True)


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
            <div class="ds-header-logo">{logo_html(mark=True)}</div>
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


def sidebar_brand(title: str = "إجادة", subtitle: str = "لتحصيل الديون", logo=None) -> None:
    st.markdown(
        f"""
        <div class="ds-brand">
            <div class="ds-brand-logo">{logo_html(logo, mark=True)}</div>
            <div>
                <div class="ds-brand-title">{_e(title)}</div>
                <div class="ds-brand-sub">{_e(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_fig(fig, height: int = 400, angle: int = -20, legend_top: bool = True):
    """رسومات plotly احترافية: خطوط نضيفة وألوان هادية من هوية إجادة."""
    fig.update_xaxes(tickfont=dict(size=13, family="Cairo, Tajawal", color=MUTED),
                     linecolor=BORDER, linewidth=1, showgrid=False)
    fig.update_yaxes(tickfont=dict(size=12.5, family="Cairo, Tajawal", color=MUTED),
                     gridcolor=BORDER, griddash="dot", zeroline=False)
    layout = dict(
        height=height, xaxis_tickangle=angle, margin=dict(t=24, b=10, l=10, r=10),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Cairo, Tajawal", color=INK), colorway=PALETTE,
        hoverlabel=dict(font_family="Cairo, Tajawal", bgcolor="#fff", bordercolor=BORDER),
    )
    if legend_top:
        layout["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text="",
                                bordercolor=BORDER, borderwidth=1, bgcolor="#fff")
    fig.update_layout(**layout)
    fig.update_traces(marker_line_width=0, selector=dict(type="bar"))
    fig.update_traces(textfont=dict(color=INK), selector=dict(type="bar"))
    return fig
