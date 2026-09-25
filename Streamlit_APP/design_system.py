"""
design_system.py  —  ملف وسيط (Dispatcher) بين ثيمين
========================================================
مش فيه أي CSS أو تصميم بنفسه — بس بينقل الاستدعاءات لواحد من الملفين:

    design_system_cartoon.py   ← الثيم الكرتوني المتحرك (الأصلي)
    design_system_pro.py       ← الثيم الاحترافي (البنكي/المؤسسي)

الاختيار محفوظ في st.session_state["ds_theme"] ("cartoon" أو "pro")،
وأي دالة بتتنادى (page_header, kpi_row, ...) بتتحول تلقائيًا للثيم
المختار حاليًا — من غير ما app.py يحتاج يعرف الفرق.

استخدام في app.py:
    from design_system import (
        inject_design_system, page_header, kpi_row, section_title, card,
        empty_state, info_box, style_fig, sidebar_brand, money_rain,
        PAGE_THEMES, theme_switcher,
        GREEN, GOLD, RED, BLUE, VIOLET, TEAL,
    )

    with st.sidebar:
        theme_switcher()          # <-- زرار اختيار الثيم (سطر واحد بس جديد)
        sidebar_brand(...)
        ...
"""

from contextlib import contextmanager
import streamlit as st

import design_system_cartoon as _cartoon
import design_system_pro as _pro

DEFAULT_THEME = "pro"   # القيمة الافتراضية أول ما حد يفتح التطبيق
_THEMES = {"cartoon": _cartoon, "pro": _pro}


def _current():
    """المودول المسؤول عن الثيم الحالي، حسب اختيار المستخدم."""
    key = st.session_state.get("ds_theme", DEFAULT_THEME)
    return _THEMES.get(key, _pro)


# ======================================================================
# 🎛️ زرار/سلايدر اختيار الثيم — يتنادى مرة في أعلى الـ sidebar
# ======================================================================
def theme_switcher(show_label: bool = True) -> None:
    """
    بيرسم اختيار بسيط (كرتوني / بروفيشنال) وبيحفظ الاختيار في session_state.
    أي تغيير بيعمل rerun فورًا عشان كل حاجة (الألوان، الخطوط، الخلفية) تتبدل.
    """
    st.session_state.setdefault("ds_theme", DEFAULT_THEME)

    labels = {"pro": "💼 بروفيشنال", "cartoon": "🎨 كرتوني"}
    keys = list(labels.keys())
    current_key = st.session_state["ds_theme"]

    if show_label:
        st.markdown(
            "<div style='font-size:12.5px;font-weight:700;opacity:.7;margin-bottom:4px;'>الثيم</div>",
            unsafe_allow_html=True,
        )

    choice = st.radio(
        "الثيم",
        keys,
        index=keys.index(current_key) if current_key in keys else 0,
        format_func=lambda k: labels[k],
        horizontal=True,
        label_visibility="collapsed",
        key="ds_theme_radio",
    )

    if choice != current_key:
        st.session_state["ds_theme"] = choice
        st.rerun()


# ======================================================================
# تمرير الدوال — كل دالة بتاخد الاستدعاء وتحوّله لمودول الثيم الحالي
# ======================================================================
def inject_design_system(*args, **kwargs):
    return _current().inject_design_system(*args, **kwargs)


def page_header(*args, **kwargs):
    return _current().page_header(*args, **kwargs)


def kpi_row(*args, **kwargs):
    return _current().kpi_row(*args, **kwargs)


def section_title(*args, **kwargs):
    return _current().section_title(*args, **kwargs)


@contextmanager
def card(*args, **kwargs):
    with _current().card(*args, **kwargs) as c:
        yield c


def empty_state(*args, **kwargs):
    return _current().empty_state(*args, **kwargs)


def info_box(*args, **kwargs):
    return _current().info_box(*args, **kwargs)


def style_fig(*args, **kwargs):
    return _current().style_fig(*args, **kwargs)


def sidebar_brand(*args, **kwargs):
    return _current().sidebar_brand(*args, **kwargs)


def money_rain(*args, **kwargs):
    return _current().money_rain(*args, **kwargs)


def logo_html(*args, **kwargs):
    return _current().logo_html(*args, **kwargs)


# ======================================================================
# ثوابت — نفس المفاتيح موجودة في الملفين بنفس القيم (أسماء الصفحات)،
# فمفيش داعي نختار حسب الثيم. الألوان بناخدها من الثيم البروفيشنال
# كقيمة افتراضية ثابتة (مش بتتغيّر مع تبديل الثيم لأنها constants
# بتتقرأ وقت الـ import مش وقت التشغيل).
# ======================================================================
PAGE_THEMES = _pro.PAGE_THEMES
GREEN, GOLD, RED, BLUE, VIOLET, TEAL = (
    _pro.GREEN, _pro.GOLD, _pro.RED, _pro.BLUE, _pro.VIOLET, _pro.TEAL
)
