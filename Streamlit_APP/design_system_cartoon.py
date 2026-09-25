"""
design_system.py  —  النسخة الكرتونية المتحركة 🎨🎬
====================================================
نفس أسماء الدوال بالظبط، فمفيش أي تغيير مطلوب في app.py غير استيراد money_rain:

    inject_design_system, page_header, kpi_row, section_title, card,
    empty_state, info_box, style_fig, sidebar_brand, money_rain, PAGE_THEMES

الستايل: حدود سودا تخينة + ظلال صلبة (من غير blur) + ألوان زاهية +
ستيكرز مايلة شوية + خط Baloo Bhaijaan 2 المدوّر + أنيميشن في كل حته.

جديد: money_rain("رسالة") — مطر فلوس + رسالة نجاح، نادِها بعد ما التقرير يتعمل.

مهم: الستايل ده مبني على خلفية فاتحة. حط في .streamlit/config.toml:
    [theme]
    base = "light"
"""

from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import base64
import html as _html
import random
import time
import streamlit as st

_HERE = Path(__file__).resolve().parent
LOGO_CANDIDATES = ["logo.png", "logo.webp", "logo.jpg", "logo.jpeg", "logo.svg"]

INK = "#1B1B2F"

# accent = لون الصفحة | soft = نسخة فاتحة | on = لون الكتابة فوق الـ accent | pop = ظل النص
THEMES = {
    "promises":     dict(accent="#2DC26B", soft="#D5F7E2", on="#FFFFFF", pop=INK,
                         sky1="#A8E9D0", sky2="#D3F5E6", sky3="#FFF4DA", city="#1F6B5A", sun="#FFF3B0"),
    "neglect":      dict(accent="#FF5A5F", soft="#FFE0E1", on="#FFFFFF", pop=INK,
                         sky1="#FFB7B0", sky2="#FFD9CC", sky3="#FFF0DE", city="#8E3B4F", sun="#FFF0B8"),
    "distribution": dict(accent="#8B5CF6", soft="#EADFFF", on="#FFFFFF", pop=INK,
                         sky1="#BFA9FF", sky2="#E6C6F7", sky3="#FFE4EE", city="#4B3A8F", sun="#FFE9F3"),
    "activity":     dict(accent="#14B8D4", soft="#D2F5FB", on="#FFFFFF", pop=INK,
                         sky1="#94DFF0", sky2="#C4F0F3", sky3="#FFF6E2", city="#1E6F8C", sun="#FFF6C4"),
    "payments":     dict(accent="#FFC93C", soft="#FFF1C4", on=INK,       pop="#FFFFFF",
                         sky1="#FFD976", sky2="#FFCFA6", sky3="#FFF0E0", city="#9A6A2A", sun="#FFFBE0"),
    "rotation":     dict(accent="#3B82F6", soft="#DCE9FF", on="#FFFFFF", pop=INK,
                         sky1="#9EC5FF", sky2="#CDE0FF", sky3="#F2F8FF", city="#2F4E9A", sun="#FFFBE6"),
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
  --sky1:__SKY1__; --sky2:__SKY2__; --sky3:__SKY3__;
  --ds-muted:#5b5b7a;
  --bw:3px;
  --sh:5px 5px 0 var(--ink);
  --sh-lg:8px 8px 0 var(--ink);
}

/* ===== الخلفية: ورقة كريمي منقطة ===== */
.stApp{
  color-scheme:light; color:var(--ink); background:transparent !important;
}
html, body{ background:var(--sky3) !important; }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stBottom"]{ background:transparent !important; }
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
.ds-header::after{
  content:"✦ ✧"; position:absolute; right:24px; top:8px; font-size:26px; letter-spacing:8px; color:#fff;
  text-shadow:2px 2px 0 var(--ink); transform:rotate(-6deg);
}
.ds-header-logo{
  position:absolute; z-index:1; left:26px; top:50%; margin-top:-46px; width:92px; height:92px; border-radius:50%;
  display:flex; align-items:center; justify-content:center; background:#fff; border:4px solid var(--ink);
  box-shadow:5px 5px 0 var(--ink); transform:rotate(8deg); overflow:hidden;
}
.ds-header-logo img, .ds-header-logo svg{ width:74%; height:74%; object-fit:contain; }
.ds-header{ padding-left:150px; }
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
.ds-empty .ds-empty-icon{ display:block; font-size:46px; margin-bottom:6px; }
@media (prefers-reduced-motion:reduce){ .ds-kpi,.ds-kpi:hover{ transition:none; } }

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
  border-left:4px solid var(--ink);
  background-color:var(--sky2);
  background-image:radial-gradient(rgba(255,255,255,.9) 1.6px, transparent 2.2px), linear-gradient(180deg, var(--sky1) 0%, var(--sky2) 60%, var(--sky3) 100%);
  background-size:44px 44px, auto;
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
  flex:0 0 auto; width:56px; height:56px; border-radius:50%; display:flex; align-items:center; justify-content:center;
  background:#fff; border:var(--bw) solid var(--ink); overflow:hidden;
}
.ds-brand-logo img, .ds-brand-logo svg{ width:82%; height:82%; object-fit:contain; }
.ds-brand-title{ font-weight:800; font-size:18px; line-height:1.2; color:var(--ink); }
.ds-brand-sub{ font-weight:600; font-size:12.5px; color:var(--ds-muted); }

@media (max-width:760px){
  .ds-header-logo{ display:none; }
  .ds-header{ flex-direction:column; align-items:flex-start; padding:22px; }
  .ds-header h1{ font-size:26px; }
}
/* ===== الخلفية (ثابتة — مشهد أنمي) ===== */
div[data-testid="stElementContainer"]:has(.ds-bg), .element-container:has(.ds-bg){ height:0 !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
.ds-bg{
  position:fixed; inset:0; z-index:-1; pointer-events:none; overflow:hidden;
  background:linear-gradient(180deg, var(--sky1) 0%, var(--sky2) 58%, var(--sky3) 100%);
}
.ds-sky{ position:absolute; inset:0; width:100%; height:100%; }
.ds-city{ position:absolute; left:0; right:0; bottom:0; width:100%; height:34vh; min-height:200px; }
.ds-tone{ /* شبكة نقط مانجا بتتلاشى من الركن */
  position:absolute; inset:0; opacity:.55;
  background-image:radial-gradient(rgba(27,27,47,.28) 1.7px, transparent 2.2px); background-size:16px 16px;
  -webkit-mask-image:radial-gradient(circle at 100% 0, #000 0, transparent 40%);
          mask-image:radial-gradient(circle at 100% 0, #000 0, transparent 40%);
}
.ds-bg.custom{ background-size:cover; background-position:center; }
.ds-bg.custom > *{ display:none; }

/* =====================================================================
   🎬 ANIMATIONS
   ===================================================================== */
:root{ --ease-pop:cubic-bezier(.34,1.56,.64,1); }

@keyframes ds-drop-in{ from{opacity:0; transform:translateY(-40px) scale(.92);} 60%{transform:translateY(6px) scale(1.02);} to{opacity:1; transform:none;} }
@keyframes ds-pop-in{
  0%{opacity:0; transform:translateY(34px) scale(.55) rotate(var(--rot,0deg));}
  60%{opacity:1; transform:translateY(-6px) scale(1.06) rotate(var(--rot,0deg));}
  100%{opacity:1; transform:translateY(0) scale(1) rotate(var(--rot,0deg));}
}
@keyframes ds-slide-in{ from{opacity:0; transform:translateX(60px) rotate(var(--rot,0deg));} to{opacity:1; transform:translateX(0) rotate(var(--rot,0deg));} }
@keyframes ds-fade-up{ from{opacity:0; transform:translateY(24px);} to{opacity:1; transform:none;} }
@keyframes ds-line{ from{opacity:0;} to{opacity:.35;} }
@keyframes ds-bob{ 0%,100%{transform:translateY(0);} 50%{transform:translateY(-6px);} }
@keyframes ds-float{ 0%,100%{transform:translateY(0);} 50%{transform:translateY(-18px);} }
@keyframes ds-spin{ to{transform:rotate(360deg) scale(1.12);} }
@keyframes ds-wiggle-l{ 0%,100%{transform:rotate(-8deg);} 50%{transform:rotate(-1deg) scale(1.06);} }
@keyframes ds-wiggle-r{ 0%,100%{transform:rotate(8deg);} 50%{transform:rotate(15deg) scale(1.05);} }
@keyframes ds-spark{ 0%,100%{opacity:.55; transform:rotate(-6deg) scale(.9);} 50%{opacity:1; transform:rotate(6deg) scale(1.15);} }
@keyframes ds-twinkle{ 0%,100%{opacity:.25; transform:scale(.6);} 50%{opacity:1; transform:scale(1.15);} }
@keyframes ds-drift{ from{transform:translateX(-60px);} to{transform:translateX(100px);} }
@keyframes ds-pulse{ 0%,100%{transform:scale(1);} 50%{transform:scale(1.08);} }
@keyframes ds-blink{ 0%,100%{opacity:.9;} 50%{opacity:.2;} }
@keyframes ds-dots{ to{background-position:16px 16px;} }
@keyframes ds-shine{ 0%,60%{left:-90px;} 100%{left:130%;} }
@keyframes ds-stripes{ to{background-position:28px 0;} }
@keyframes ds-tab-pop{ 0%{transform:scale(.85);} 100%{transform:scale(1);} }
@keyframes ds-grow-y{ from{transform:scaleY(0);} to{transform:scaleY(1);} }
@keyframes ds-glow{
  0%,100%{box-shadow:4px 4px 0 var(--ink), 0 0 0 0 transparent;}
  50%{box-shadow:4px 4px 0 var(--ink), 0 0 0 8px color-mix(in srgb, var(--ds-accent) 35%, transparent);}
}
@keyframes ds-coinflip{ to{transform:rotateY(360deg);} }

/* --- الهيدر --- */
.ds-header{ animation:ds-drop-in .7s var(--ease-pop) backwards; }
.ds-header::after{ animation:ds-spark 2.4s ease-in-out infinite; }
.ds-header-icon{ animation:ds-wiggle-l 3.2s ease-in-out infinite; }
.ds-header-logo{ animation:ds-wiggle-r 4s ease-in-out infinite; }
.ds-chip:nth-child(odd){ --rot:-2deg; }
.ds-chip:nth-child(even){ --rot:1.6deg; }
.ds-chip{ animation:ds-pop-in .5s var(--ease-pop) backwards; }
.ds-chip:nth-child(1){animation-delay:.30s} .ds-chip:nth-child(2){animation-delay:.40s}
.ds-chip:nth-child(3){animation-delay:.50s} .ds-chip:nth-child(4){animation-delay:.60s}
.ds-chip:nth-child(5){animation-delay:.70s} .ds-chip:nth-child(6){animation-delay:.80s}

/* --- KPI --- */
.ds-kpi:nth-child(odd){ --rot:-.9deg; }
.ds-kpi:nth-child(even){ --rot:.9deg; }
.ds-kpi{ overflow:hidden; animation:ds-pop-in .6s var(--ease-pop) backwards; }
.ds-kpi:nth-child(1){animation-delay:.05s} .ds-kpi:nth-child(2){animation-delay:.15s}
.ds-kpi:nth-child(3){animation-delay:.25s} .ds-kpi:nth-child(4){animation-delay:.35s}
.ds-kpi:nth-child(5){animation-delay:.45s} .ds-kpi:nth-child(6){animation-delay:.55s}
.ds-kpi-icon{ animation:ds-bob 2.6s ease-in-out infinite; }
.ds-kpi:hover .ds-kpi-icon{ animation:ds-spin .6s ease; }
.ds-kpi::after{
  content:""; position:absolute; top:0; bottom:0; width:60px; left:-90px; pointer-events:none;
  background:linear-gradient(100deg, transparent, rgba(255,255,255,.75), transparent);
  transform:skewX(-20deg); animation:ds-shine 4.5s ease-in-out infinite;
}

/* --- العناوين والكروت والصناديق --- */
.ds-section > .ds-sec-label{ --rot:-1.2deg; animation:ds-slide-in .55s var(--ease-pop) backwards; }
.ds-section::after{ animation:ds-line .9s ease-out .2s backwards; }
div[data-testid="stVerticalBlockBorderWrapper"]:has(.ds-card-title){ animation:ds-fade-up .6s ease-out backwards; }
.ds-card-title::before{ animation:ds-pulse 2.4s ease-in-out infinite; }
.ds-box{ animation:ds-slide-in .5s var(--ease-pop) backwards; }
.ds-empty .ds-empty-icon{ display:inline-block; animation:ds-bob 1.8s ease-in-out infinite; }
div[data-testid="stMetric"], div[data-testid="stExpander"]{ animation:ds-fade-up .6s ease-out backwards; }

/* --- الرسومات: الأعمدة بتطلع من تحت --- */
.js-plotly-plot .bars .point path{ transform-box:fill-box; transform-origin:bottom; animation:ds-grow-y .8s var(--ease-pop) backwards; }

/* --- تابات وأزرار وسايد بار --- */
button[data-baseweb="tab"][aria-selected="true"]{ animation:ds-tab-pop .35s var(--ease-pop); }
div[data-testid="stButton"] button[kind="primary"], div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]{
  animation:ds-glow 2.2s ease-in-out infinite;
}
div[data-testid="stButton"] button[kind="primary"]:hover, div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:hover,
div[data-testid="stButton"] button[kind="primary"]:active, div[data-testid="stButton"] button[data-testid="stBaseButton-primary"]:active{ animation:none; }
section[data-testid="stSidebar"] div[data-testid="stButton"]{ animation:ds-slide-in .5s var(--ease-pop) backwards; }
.ds-brand:hover .ds-brand-logo{ animation:ds-spin .8s ease; }
div[data-testid="stProgress"] > div > div > div > div{
  background-image:repeating-linear-gradient(45deg, rgba(255,255,255,.4) 0 10px, transparent 10px 20px) !important;
  background-size:28px 28px; animation:ds-stripes .8s linear infinite;
}
div[data-testid="stSpinner"]{ display:flex; align-items:center; gap:10px; }
div[data-testid="stSpinner"]::before{ content:"🪙"; font-size:28px; animation:ds-coinflip 1s linear infinite; }

/* --- الخلفية --- */
.ds-tone{ animation:ds-dots 6s linear infinite; }
.ds-tw{ transform-box:fill-box; transform-origin:center; animation:ds-twinkle 2.6s ease-in-out infinite; }
.ds-cloud{ animation:ds-drift 50s ease-in-out infinite alternate; }
.ds-float{ animation:ds-float 4.5s ease-in-out infinite; }
.ds-sun{ transform-box:fill-box; transform-origin:center; animation:ds-pulse 6s ease-in-out infinite; }
.ds-win{ animation:ds-blink 5s ease-in-out infinite; }

/* --- 💰 مطر الفلوس + رسالة النجاح --- */
div[data-testid="stElementContainer"]:has(.ds-rain), .element-container:has(.ds-rain){ height:0 !important; min-height:0 !important; margin:0 !important; padding:0 !important; }
.ds-rain{ position:fixed; inset:0; z-index:99999; pointer-events:none; overflow:hidden; }
.ds-drop{
  position:absolute; top:-70px; left:var(--x); font-size:var(--s);
  filter:drop-shadow(2px 2px 0 var(--ink)); animation:ds-fall var(--d) linear var(--dl) both;
}
@keyframes ds-fall{
  0%{transform:translate(0,0) rotate(0deg); opacity:1;}
  50%{transform:translate(var(--sw),55vh) rotate(calc(var(--r) / 2));}
  85%{opacity:1;}
  100%{transform:translate(0,115vh) rotate(var(--r)); opacity:0;}
}
.ds-toast{
  position:fixed; top:22px; left:50%; z-index:100000; pointer-events:none; white-space:nowrap;
  background:#FFC93C; color:var(--ink); font-weight:800; font-size:20px; padding:10px 28px;
  border:4px solid var(--ink); border-radius:999px; box-shadow:6px 6px 0 var(--ink);
  animation:ds-toast 3.8s ease-out both;
}
.ds-toast-ico{ display:inline-block; animation:ds-bob .8s ease-in-out infinite; }
@keyframes ds-toast{
  0%{opacity:0; transform:translate(-50%,-90px) scale(.6);}
  12%{opacity:1; transform:translate(-50%,0) scale(1.08);}
  18%{transform:translate(-50%,0) scale(1);}
  85%{opacity:1; transform:translate(-50%,0) scale(1);}
  100%{opacity:0; transform:translate(-50%,-30px) scale(.9);}
}

@media (prefers-reduced-motion:reduce){
  *, *::before, *::after{ animation:none !important; }
  .ds-rain, .ds-toast{ display:none; }
}
</style>

"""


# ----------------------------------------------------------------------
# اللوجو: لو فيه ملف logo.png (أو svg/jpg/webp) جنب design_system.py هيتستخدم،
# غير كده بيتستخدم لوجو إجادة المرسوم بالكود.
# ----------------------------------------------------------------------
_MIME = {".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg",
         ".jpeg": "image/jpeg", ".svg": "image/svg+xml", ".gif": "image/gif"}

_BUILTIN_LOGO = (
    '<svg viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="إجادة">'
    '<circle cx="32" cy="32" r="28" fill="#FFC93C" stroke="#1B1B2F" stroke-width="4"/>'
    '<path d="M17 34 L28 45 L48 21" fill="none" stroke="#1B1B2F" stroke-width="7" '
    'stroke-linecap="round" stroke-linejoin="round"/>'
    '<circle cx="48" cy="15" r="6" fill="#2DC26B" stroke="#1B1B2F" stroke-width="3"/>'
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


def logo_html(logo=None) -> str:
    """logo: مسار صورة اختياري. لو None بندور على logo.* جنب الملف، وإلا اللوجو المدمج."""
    p = Path(logo) if logo else _find_logo()
    if p and p.exists():
        return f'<img src="{_data_uri(str(p))}" alt="logo">'
    return _BUILTIN_LOGO


def _sparkle(x, y, r, fill="#fff", op=0.95, rot=0):
    return (f'<g class="ds-tw" style="animation-delay:-{(x * 7 + y * 3) % 30 / 10:.1f}s">'
            f'<path d="M0 -1Q0 0 1 0Q0 0 0 1Q0 0 -1 0Q0 0 0 -1Z" fill="{fill}" opacity="{op}" '
            f'transform="translate({x} {y}) rotate({rot}) scale({r})"/></g>')


def _cloud(x, y, k, op=0.92):
    return (f'<g class="ds-cloud" style="animation-duration:{40 + (x % 5) * 8}s;animation-delay:-{x % 13}s">'
            f'<g transform="translate({x} {y}) scale({k})" opacity="{op}">'
            '<rect x="0" y="44" width="230" height="52" rx="26" fill="#fff"/>'
            '<circle cx="62" cy="44" r="40" fill="#fff"/><circle cx="118" cy="30" r="50" fill="#fff"/>'
            '<circle cx="176" cy="48" r="34" fill="#fff"/>'
            '<rect x="14" y="76" width="202" height="20" rx="10" fill="#B9C7F0" opacity=".28"/></g></g>')


def _coin(x, y, r, rot):
    return (f'<g class="ds-float" style="animation-delay:-{(x % 40) / 10:.1f}s">'
            f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<circle r="{r}" fill="#FFC93C" stroke="{INK}" stroke-width="3.5"/>'
            f'<circle r="{r*0.68:.1f}" fill="none" stroke="#E0A400" stroke-width="2.5"/>'
            f'<text y="{r*0.36:.1f}" text-anchor="middle" font-size="{r*1.05:.1f}" font-weight="800" fill="{INK}">$</text></g></g>')


def _city_svg(color: str) -> str:
    import random as _random
    rnd = _random.Random(11)
    layers = [  # (opacity, min_h, max_h, min_w, max_w, windows)
        (0.28, 110, 220, 40, 90, False),
        (0.48, 70, 170, 46, 100, False),
        (0.82, 34, 120, 52, 118, True),
    ]
    out = []
    for op, h0, h1, w0, w1, wins in layers:
        g = [f'<g fill="{color}" opacity="{op}">']
        x = -30
        while x < 1640:
            w, h = rnd.randint(w0, w1), rnd.randint(h0, h1)
            y = 300 - h
            g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h+4}" rx="4"/>')
            kind = rnd.randint(0, 3)
            if kind == 1:
                g.append(f'<rect x="{x + w//2 - 2}" y="{y-26}" width="4" height="27"/>')
            elif kind == 2:
                g.append(f'<rect x="{x + w//4}" y="{y-14}" width="{w//2}" height="15" rx="3"/>')
            elif kind == 3:
                g.append(f'<path d="M{x} {y} Q{x + w/2} {y-30} {x + w} {y}Z"/>')
            if wins:
                g.append("</g>")
                g.append(f'<g class="ds-win" fill="#FFE9A0" opacity="0.9" '
                         f'style="animation-delay:-{(x % 9) * 0.6:.1f}s">')
                for cx in range(x + 9, x + w - 10, 15):
                    for cy in range(y + 12, 292, 20):
                        if rnd.random() < 0.26:
                            g.append(f'<rect x="{cx}" y="{cy}" width="7" height="10" rx="1.5"/>')
                g.append("</g>")
                g.append(f'<g fill="{color}" opacity="{op}">')
            x += w + rnd.randint(-8, 10)
        g.append("</g>")
        out.append("".join(g))
    out.append(f'<rect x="0" y="288" width="1600" height="14" fill="{color}"/>')
    return ('<svg class="ds-city" viewBox="0 0 1600 300" preserveAspectRatio="xMidYMax slice" '
            'xmlns="http://www.w3.org/2000/svg">' + "".join(out) + "</svg>")


@lru_cache(maxsize=8)
def _scene_html(theme: str) -> str:
    t = THEMES.get(theme, THEMES["promises"])
    sky = [
        f'<g class="ds-sun"><circle cx="1240" cy="210" r="200" fill="{t["sun"]}" opacity=".20"/>'
        f'<circle cx="1240" cy="210" r="140" fill="{t["sun"]}" opacity=".38"/>'
        f'<circle cx="1240" cy="210" r="88" fill="{t["sun"]}"/></g>',
        _cloud(90, 110, 1.0), _cloud(520, 50, 0.7, .85), _cloud(880, 230, 0.9), _cloud(1330, 70, 1.1),
        _cloud(260, 360, 0.65, .8), _cloud(1120, 430, 0.6, .75),
    ]
    for x, y, r, rot in [(150, 250, 20, 0), (470, 190, 12, 15), (700, 90, 26, 0), (980, 330, 14, 0),
                          (1450, 250, 22, 0), (1540, 520, 12, 20), (60, 500, 16, 0), (820, 470, 10, 0),
                          (380, 470, 9, 0), (1010, 120, 9, 0), (1300, 470, 13, 0), (600, 300, 8, 0)]:
        sky.append(_sparkle(x, y, r, rot=rot))
    for x, y, r, rot in [(245, 300, 27, -14), (770, 150, 21, 10), (1450, 380, 30, 16), (70, 610, 24, -8)]:
        sky.append(_coin(x, y, r, rot))
    return (
        '<div class="ds-bg"><div class="ds-tone"></div>'
        '<svg class="ds-sky" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" '
        'xmlns="http://www.w3.org/2000/svg">' + "".join(sky) + "</svg>"
        + _city_svg(t["city"]) + "</div>"
    )


def _background_html(theme="promises", bg_gif=None) -> str:
    if bg_gif and Path(bg_gif).exists():
        return f'<div class="ds-bg custom" style="background-image:url({_data_uri(str(Path(bg_gif)))})"></div>'
    return _scene_html(theme)


def inject_design_system(theme: str = "promises", background: str = "scene", bg_gif=None) -> None:
    """
    يتنادى مرة واحدة في كل rerun، بعد set_page_config.
    background: "scene" (مشهد أنمي متحرك، الافتراضي) | "plain" (سماء متدرجة بس)
    bg_gif: مسار صورة اختيارية تستخدمها كخلفية بدل المشهد.
    """
    t = THEMES.get(theme, THEMES["promises"])
    css = (
        _CSS.replace("__INK__", INK)
        .replace("__ACCENT__", t["accent"])
        .replace("__SOFT__", t["soft"])
        .replace("__ON__", t["on"])
        .replace("__POP__", t["pop"])
        .replace("__SKY1__", t["sky1"])
        .replace("__SKY2__", t["sky2"])
        .replace("__SKY3__", t["sky3"])
    )
    st.markdown(css, unsafe_allow_html=True)
    if background == "plain" and not bg_gif:
        st.markdown('<div class="ds-bg"></div>', unsafe_allow_html=True)
    else:
        st.markdown(_background_html(theme, bg_gif), unsafe_allow_html=True)


def _e(x) -> str:
    return _html.escape(str(x))


def money_rain(message: str = "تم إنشاء التقرير", count: int = 32,
               emojis=("💰", "🪙", "💵", "💸", "💎")) -> None:
    """مطر فلوس + رسالة نجاح. نادِها بعد ما التقرير يتعمل (مرة واحدة لكل rerun)."""
    rnd = random.Random(time.time_ns())
    drops = "".join(
        f'<span class="ds-drop" style="--x:{rnd.randint(2, 96)}%;--s:{rnd.randint(26, 50)}px;'
        f'--d:{rnd.uniform(2.2, 4.2):.2f}s;--dl:{rnd.uniform(0, 1.6):.2f}s;'
        f'--sw:{rnd.randint(-60, 60)}px;--r:{rnd.randint(-360, 360)}deg">{rnd.choice(emojis)}</span>'
        for _ in range(count)
    )
    toast = (f'<div class="ds-toast"><span class="ds-toast-ico">💰</span> {_e(message)} '
             f'<span class="ds-toast-ico">✅</span></div>') if message else ""
    st.markdown(f'<div class="ds-rain">{drops}</div>{toast}', unsafe_allow_html=True)


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
