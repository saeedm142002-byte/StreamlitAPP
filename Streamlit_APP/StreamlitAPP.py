import streamlit as st
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from io import BytesIO
import torch
import torch.nn.functional as F
from datetime import datetime, date, time, timedelta
from openpyxl.worksheet.table import Table, TableStyleInfo

import plotly.express as px
import plotly.express as px
import textwrap

from openpyxl.styles import Font, PatternFill, Border, Side, Alignment

# ======================
# MODEL
# ======================
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import streamlit as st

repo_id = "Saeed1233/AraBERTSNB"

@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    model = AutoModelForSequenceClassification.from_pretrained(repo_id)
    model.eval()
    return tokenizer, model

tokenizer, model = load_model()


import torch

def predict_text(text):
    inputs = tokenizer(
        str(text),
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    )

    with torch.no_grad():
        outputs = model(**inputs)

    probs = torch.softmax(outputs.logits, dim=1)

    pred = torch.argmax(probs, dim=1).item()   # 0 أو 1
    confidence = probs[0][pred].item() * 100

    return pred, round(confidence, 2)


# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Saeed Mohamed",
    page_icon="❤️🦅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ======================
# SESSION STATE
# ======================
if "page" not in st.session_state:
    st.session_state.page = "الوعود القائمة و المكسورة"

if "sub_page" not in st.session_state:
    st.session_state.sub_page = "اهمال"


# ======================
# SIDEBAR
# ======================
pages = [
    ("الوعود القائمة و المكسورة", "📊"),
    ("الاهمال", "⚠️"),
    ("التوزيع", "📈"),
    ("النشاط", "⚡"),
    ("اخطاء الحالات", "❌"),
    ("مطابقة السدادات", "💰")
    
]

with st.sidebar:
    st.markdown("### ❤️🦅 لوحة التحكم")

    for page_name, icon in pages:
        if st.button(f"{icon} {page_name}", use_container_width=True):
            st.session_state.page = page_name
            st.rerun()

    # sub menu فقط للاهمال
    if st.session_state.page == "الاهمال":
        st.markdown("---")
        st.markdown("### خيارات الإهمال")

        for sub in ["اهمال", "متابعة اهمال"]:
            if st.button(sub, use_container_width=True):
                st.session_state.sub_page = sub
                st.rerun()


# ======================
# MAIN ROUTER
# ======================
page = st.session_state.page


# ======================
# PAGE 1 - الوعود القائمة
# ======================
if page == "الوعود القائمة و المكسورة":
    import pandas as pd
    import plotly.express as px
    from io import BytesIO
    st.subheader("📊 الوعود القائمة / الوعود المكسورة")
    
    # ==========================================
    # اختيار المسار: NPL&Dpd60 أو SNB
    # ==========================================
    portfolio_type = st.radio(
        "اختار نوع المحفظة",
        options=["NPL&Dpd60", "SNB"],
        horizontal=True
    )
    
    portfolio_file = st.file_uploader(
        "رفع ملف المحفظة",
        type=["xlsx", "xls"]
    )
    
    # ============================================================
    # الدالة المعالجة الأساسية - Cached
    # ============================================================
    @st.cache_data(show_spinner="جاري معالجة الملف...")
    def process_portfolio(file_bytes, portfolio_type_):
        df = pd.read_excel(BytesIO(file_bytes))
        
        # حذف أول صف بعد الـ Header
        df = df.iloc[1:].reset_index(drop=True)
        
        # تنظيف النصوص
        text_cols = [
            "Sales Team",
            "Salesperson",
            "Final State",
            "Sub State",
            "حالة المعالجة - التمويل",
            "ملاحظات-التمويل"
        ]
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # تحويل "nan" النصي إلى NaN حقيقي عشان الفلترة تشتغل صح
                df[col] = df[col].replace(["nan", "None", ""], pd.NA)
        
        # تحويل التواريخ
        df["Follow up Due Date"] = pd.to_datetime(
            df["Follow up Due Date"],
            errors="coerce"
        ).dt.normalize()
        
        df["Follow up Last Date"] = pd.to_datetime(
            df["Follow up Last Date"],
            errors="coerce"
        ).dt.normalize()
        
        today = pd.Timestamp.today().normalize()
        
        # ==========================================
        # بناء الـ base حسب المسار المختار
        # ==========================================
        if portfolio_type_ == "NPL&Dpd60":
            base = df.copy()
            base = base[
                base["Sales Team"] != "Sara || Op"
            ]
            base = base[
                base["Final State"].str.contains(
                    "واعد بالسداد",
                    na=False
                )
            ]
            # ← شيلنا فلتر "حالة المعالجة - التمويل" من هنا عشان يبقى آخر خطوة
            
        else:  # SNB
            base = df.copy()
            allowed_sales_teams = [
                "SNB II Alsarhan II Naser",
                "SNB II Alsarhan II Tariq"
            ]
            base = base[
                base["Sales Team"].isin(allowed_sales_teams)
            ]
            excluded_salespersons = [
                "Closed payments II Alaa SNB",
                "Hold Companies II SNB2",
                "Abdullah Alsarhan",
                "Archive Companies II Alaa SNB"
            ]
            base = base[
                (~base["Salesperson"].isin(excluded_salespersons))
                & (base["Salesperson"].notna())
                & (base["Salesperson"].str.strip() != "")
                & (base["Salesperson"].str.lower() != "nan")
            ]
            base = base[
                base["Sub State"].str.contains(
                    "واعد بالسداد",
                    na=False
                )
            ]
        
        # ==========================================
        # الوعود القائمة
        # ==========================================
        current = base.copy()
        current = current[
            current["Follow up Due Date"] == today
        ]
        current = current[
            current["Follow up Last Date"].notna()
        ]
        current = current[
            current["Follow up Last Date"] != today
        ]
        
        # ==========================================
        # الوعود المكسورة
        # ==========================================
        broken = base.copy()
        broken = broken[
            broken["Follow up Due Date"] < today
        ]
        broken = broken[
            broken["Follow up Last Date"].notna()
        ]
        broken["فرق الايام"] = (
            broken["Follow up Last Date"] - broken["Follow up Due Date"]
        ).dt.days
        broken = broken[
            broken["فرق الايام"] < 0
        ]
        broken = broken.drop(columns=["فرق الايام"])
        
        insert_position = broken.columns.get_loc("Follow up Last Date") + 1
        broken.insert(
            insert_position,
            "عدد ايام ترحيل الوعد",
            (today - broken["Follow up Due Date"]).dt.days
        )
        broken = broken[
            broken["عدد ايام ترحيل الوعد"] > 0
        ]
        
        return current.reset_index(drop=True), broken.reset_index(drop=True)
    
    if portfolio_file:
        file_bytes = portfolio_file.getvalue()
        current, broken = process_portfolio(file_bytes, portfolio_type)
        
        # ==========================================
        # فلترة "حالة المعالجة - التمويل" (آخر خطوة) - فقط في NPL&Dpd60
        # ==========================================
        if portfolio_type == "NPL&Dpd60":
            # نجيب القيم الفريدة من العمودين مع بعض عشان الفلتر يبقى شامل
            all_status = pd.concat([
                current["حالة المعالجة - التمويل"],
                broken["حالة المعالجة - التمويل"]
            ]).dropna().unique().tolist()
            
            # نضيف خيار "فارغ / NaN" لو فيه قيم فاضية
            has_empty = (
                current["حالة المعالجة - التمويل"].isna().any() or 
                broken["حالة المعالجة - التمويل"].isna().any()
            )
            
            options = sorted([str(x) for x in all_status if str(x).strip() != ""])
            if has_empty:
                options = ["(فارغ / غير محدد)"] + options
            
            selected_status = st.multiselect(
                "فلتر حسب حالة المعالجة - التمويل (اختياري)",
                options=options,
                default=[],  # فاضي = يعرض الكل
                help="اختار الحالة اللي عايزها. لو سبتها فاضية هيعرض كل الحالات."
            )
            
            if selected_status:
                def apply_status_filter(df):
                    if "(فارغ / غير محدد)" in selected_status:
                        mask = df["حالة المعالجة - التمويل"].isna()
                        other_selected = [s for s in selected_status if s != "(فارغ / غير محدد)"]
                        if other_selected:
                            mask = mask | df["حالة المعالجة - التمويل"].isin(other_selected)
                        return df[mask]
                    else:
                        return df[df["حالة المعالجة - التمويل"].isin(selected_status)]
                
                current = apply_status_filter(current)
                broken = apply_status_filter(broken)
        
        st.success(f"تم استخراج وعود قائمة {len(current)} حساب")
        st.success(f"تم استخراج وعود مكسورة {len(broken)} حساب")
        
        # ==========================================
        # ملفات التحميل (Excel)
        # ==========================================
        output_current = BytesIO()
        with pd.ExcelWriter(output_current, engine="openpyxl") as writer:
            current.to_excel(writer, index=False)
        output_current.seek(0)
        
        output_broken = BytesIO()
        with pd.ExcelWriter(output_broken, engine="openpyxl") as writer:
            broken.to_excel(writer, index=False)
        output_broken.seek(0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 تحميل الوعود القائمة",
                data=output_current,
                file_name="الوعود_القائمة.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            st.download_button(
                "📥 تحميل الوعود المكسورة",
                data=output_broken,
                file_name="الوعود_المكسورة.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        # ============================================================
        # داشبورد الوعود
        # ============================================================

        st.markdown("---")
        st.markdown("## 📊 داشبورد الوعود")

        # عمود "المشرف" في الداشبورد يختلف حسب نوع المحفظة:
        # NPL&Dpd60 -> يقرأ من عمود "ملاحظات-التمويل"
        # SNB       -> يقرأ من عمود "Sales Team" زي ما هو
        supervisor_col = "ملاحظات-التمويل" if portfolio_type == "NPL&Dpd60" else "Sales Team"

        required_report_cols = [supervisor_col, "Salesperson", "Net Amount", "Account Number"]
        missing_report_cols = [c for c in required_report_cols if c not in current.columns]

        if missing_report_cols:
            st.warning(
                f"الأعمدة دي مش موجودة في الملف المرفوع: {', '.join(missing_report_cols)} — "
                "قسم الداشبورد مش هيظهر."
            )
        else:

            # ---------------------------
            # سلايسرات (المشرف / الموظف)
            # ---------------------------

            all_supervisors = sorted(
                pd.concat([current[supervisor_col], broken[supervisor_col]]).dropna().unique().tolist()
            )
            all_salespersons = sorted(
                pd.concat([current["Salesperson"], broken["Salesperson"]]).dropna().unique().tolist()
            )

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_supervisors = st.multiselect(
                    "فلترة حسب المشرف",
                    options=all_supervisors,
                    default=[],
                    key="promises_supervisor_filter"
                )

            with filter_col2:
                selected_salespersons = st.multiselect(
                    "فلترة حسب الموظف (Salesperson)",
                    options=all_salespersons,
                    default=[],
                    key="promises_salesperson_filter"
                )

            def apply_dashboard_filters(d):
                out = d
                if selected_supervisors:
                    out = out[out[supervisor_col].isin(selected_supervisors)]
                if selected_salespersons:
                    out = out[out["Salesperson"].isin(selected_salespersons)]
                return out

            current_f = apply_dashboard_filters(current)
            broken_f = apply_dashboard_filters(broken)

            # ---------------------------
            # دالة بناء تقرير Pivot-style
            # ---------------------------

            def build_pivot_style(d, extra_col=None, extra_label=None, extra_agg="sum"):
                base_cols = ["مبلغ المديونية", "عدد الحسابات"]
                if extra_col:
                    base_cols.append(extra_label)
                out_cols = base_cols + ["الموظف", "المشرف"]

                if d.empty:
                    return pd.DataFrame(columns=out_cols)

                rows = []
                grand_amount = 0.0
                grand_count = 0
                grand_extra = 0.0

                for supervisor, sup_group in d.groupby(supervisor_col, dropna=False):
                    sup_amount = 0.0
                    sup_count = 0
                    sup_extra = 0.0

                    emp_amount = sup_group.groupby("Salesperson", dropna=False)["Net Amount"].sum()
                    emp_count = sup_group.groupby("Salesperson", dropna=False)["Account Number"].nunique()
                    if extra_col:
                        if extra_agg == "sum":
                            emp_extra = sup_group.groupby("Salesperson", dropna=False)[extra_col].sum()
                        else:
                            emp_extra = sup_group.groupby("Salesperson", dropna=False)[extra_col].mean()

                    for salesperson in emp_amount.sort_values(ascending=False).index:
                        amount_val = float(emp_amount.get(salesperson, 0))
                        count_val = int(emp_count.get(salesperson, 0))
                        row = {
                            "مبلغ المديونية": amount_val,
                            "عدد الحسابات": count_val,
                            "الموظف": salesperson,
                            "المشرف": supervisor,
                        }
                        if extra_col:
                            extra_val = float(emp_extra.get(salesperson, 0))
                            row[extra_label] = extra_val
                            sup_extra += extra_val
                        rows.append(row)
                        sup_amount += amount_val
                        sup_count += count_val

                    total_row = {
                        "مبلغ المديونية": sup_amount,
                        "عدد الحسابات": sup_count,
                        "الموظف": f"{supervisor} إجمالي",
                        "المشرف": supervisor,
                    }
                    if extra_col:
                        total_row[extra_label] = (
                            sup_extra if extra_agg == "sum" else (sup_extra / max(sup_count, 1))
                        )
                    rows.append(total_row)

                    grand_amount += sup_amount
                    grand_count += sup_count
                    grand_extra += sup_extra

                grand_row = {
                    "مبلغ المديونية": grand_amount,
                    "عدد الحسابات": grand_count,
                    "الموظف": "الاجمالي",
                    "المشرف": "",
                }
                if extra_col:
                    grand_row[extra_label] = (
                        grand_extra if extra_agg == "sum" else (grand_extra / max(grand_count, 1))
                    )
                rows.append(grand_row)

                return pd.DataFrame(rows)[out_cols]

            def style_summary(d, extra_label=None):
                fmt = {"مبلغ المديونية": "{:,.0f}", "عدد الحسابات": "{:,.0f}"}
                if extra_label:
                    fmt[extra_label] = "{:,.0f}"

                def highlight_rows(row):
                    is_total = (row["الموظف"] == "الاجمالي") or ("إجمالي" in str(row["الموظف"]))
                    if is_total:
                        # صفوف إجمالي المشرف / الإجمالي الكلي: نص أسود Bold
                        return ["font-weight: bold; color: #000000; background-color: #eef2f7"] * len(row)
                    return [""] * len(row)

                return d.style.apply(highlight_rows, axis=1).format(fmt)

            # ---------------------------
            # 1) تقرير الوعود القائمة
            # ---------------------------
            st.markdown("### 📄 تقرير الوعود القائمة")
            current_summary = build_pivot_style(current_f)
            if current_summary.empty:
                st.info("لا توجد بيانات مطابقة.")
            else:
                st.dataframe(style_summary(current_summary), use_container_width=True, hide_index=True)

            # ---------------------------
            # 2) تقرير الوعود المكسورة
            # ---------------------------
            st.markdown("### 📄 تقرير الوعود المكسورة")
            broken_summary = build_pivot_style(broken_f)
            if broken_summary.empty:
                st.info("لا توجد بيانات مطابقة.")
            else:
                st.dataframe(style_summary(broken_summary), use_container_width=True, hide_index=True)

            # ---------------------------
            # 3) تقرير عدد ايام ترحيل الوعد
            # ---------------------------
            st.markdown("### 📄 تقرير عدد ايام ترحيل الوعد")
            days_summary = build_pivot_style(
                broken_f,
                extra_col="عدد ايام ترحيل الوعد",
                extra_label="عدد ايام ترحيل الوعد",
                extra_agg="sum"
            )
            if days_summary.empty:
                st.info("لا توجد بيانات مطابقة.")
            else:
                st.dataframe(
                    style_summary(days_summary, extra_label="عدد ايام ترحيل الوعد"),
                    use_container_width=True, hide_index=True
                )

            # ---------------------------
            # أصل البيانات
            # ---------------------------
            st.markdown("### 🗂️ أصل البيانات - الوعود القائمة")
            st.dataframe(current_f, use_container_width=True, hide_index=True)

            st.markdown("### 🗂️ أصل البيانات - الوعود المكسورة")
            st.dataframe(broken_f, use_container_width=True, hide_index=True)

            # ---------------------------
            # الشارتات
            # ---------------------------
            st.markdown("### 📈 الرسوم البيانية")

            SNB_GREEN = "#00693E"
            SNB_GOLD = "#C9A227"
            SNB_RED = "#A33A3A"

            # إعدادات موحدة لتكبير وتغميق الـ Data Labels وأسماء المحور السيني
            DATA_LABEL_FONT = dict(size=16, family="Arial Black", color="white")
            XAXIS_TICK_FONT = dict(size=14, family="Arial Black", color="white")

            sup_amount_current = (
                current_f.groupby(supervisor_col, dropna=False)["Net Amount"].sum()
                .reset_index().rename(columns={supervisor_col: "المشرف", "Net Amount": "مبلغ المديونية"})
            )
            sup_amount_current["النوع"] = "قائمة"

            sup_amount_broken = (
                broken_f.groupby(supervisor_col, dropna=False)["Net Amount"].sum()
                .reset_index().rename(columns={supervisor_col: "المشرف", "Net Amount": "مبلغ المديونية"})
            )
            sup_amount_broken["النوع"] = "مكسورة"

            sup_amount_combined = pd.concat([sup_amount_current, sup_amount_broken], ignore_index=True)

            if not sup_amount_combined.empty:
                fig1 = px.bar(
                    sup_amount_combined, x="المشرف", y="مبلغ المديونية", color="النوع",
                    barmode="group", text="مبلغ المديونية",
                    color_discrete_map={"قائمة": SNB_GREEN, "مكسورة": SNB_RED}
                )
                fig1.update_traces(
                    texttemplate="<b>%{text:,.0f}</b>",
                    textposition="outside",
                    textfont=DATA_LABEL_FONT
                )
                fig1.update_xaxes(tickfont=XAXIS_TICK_FONT)
                fig1.update_layout(height=420, xaxis_tickangle=-20, margin=dict(t=20, b=10))
                st.plotly_chart(fig1, use_container_width=True)

            emp_count_broken = (
                broken_f.groupby("Salesperson", dropna=False)["Account Number"].nunique()
                .reset_index(name="عدد الحسابات")
                .sort_values("عدد الحسابات", ascending=False).head(15)
            )
            if not emp_count_broken.empty:
                st.markdown("#### أعلى 15 موظف بعدد الحسابات (الوعود المكسورة)")
                fig2 = px.bar(
                    emp_count_broken, x="Salesperson", y="عدد الحسابات", text="عدد الحسابات",
                    color_discrete_sequence=[SNB_RED]
                )
                fig2.update_traces(
                    texttemplate="<b>%{text}</b>",
                    textposition="outside",
                    textfont=DATA_LABEL_FONT
                )
                fig2.update_xaxes(tickfont=XAXIS_TICK_FONT)
                fig2.update_layout(height=420, xaxis_tickangle=-30, margin=dict(t=20, b=10))
                st.plotly_chart(fig2, use_container_width=True)

            days_by_sup = (
                broken_f.groupby(supervisor_col, dropna=False)["عدد ايام ترحيل الوعد"].mean()
                .reset_index().rename(columns={supervisor_col: "المشرف", "عدد ايام ترحيل الوعد": "متوسط ايام الترحيل"})
            )
            if not days_by_sup.empty:
                st.markdown("#### متوسط عدد أيام ترحيل الوعد لكل مشرف")
                fig3 = px.bar(
                    days_by_sup, x="المشرف", y="متوسط ايام الترحيل", text="متوسط ايام الترحيل",
                    color_discrete_sequence=[SNB_GOLD]
                )
                fig3.update_traces(
                    texttemplate="<b>%{text:.1f}</b>",
                    textposition="outside",
                    textfont=DATA_LABEL_FONT
                )
                fig3.update_xaxes(tickfont=XAXIS_TICK_FONT)
                fig3.update_layout(height=420, xaxis_tickangle=-20, margin=dict(t=20, b=10))
                st.plotly_chart(fig3, use_container_width=True)
# ======================
# PAGE 2 - الوعود المكسورة
# ======================
elif page == "الوعود المكسورة":
    st.subheader("🚨 الوعود المكسورة")
    st.write("متابعة الوعود المكسورة")


# ======================
# PAGE 3 - الاهمال
# ======================
elif page == "الاهمال":

    sub = st.session_state.sub_page

    st.subheader("⚠️ الاهمال")
    if sub == "اهمال":
    
            # ==========================================
            # اختيار المسار: NPL&Dpd60 أو SNB
            # ==========================================
            neglect_portfolio_type = st.radio(
                "اختار نوع المحفظة",
                options=["NPL&Dpd60", "SNB"],
                horizontal=True,
                key="neglect_portfolio_type"
            )
    
            # ==========================================
            # سؤال عن عدد الأيام حسب المسار
            # ==========================================
            if neglect_portfolio_type == "NPL&Dpd60":
                neglect_days_threshold = st.number_input(
                    "عدد أيام الإهمال (الحد الأدنى)",
                    min_value=1,
                    value=3,
                    step=1,
                    key="neglect_npl_days"
                )
            else:
                neglect_days_threshold = st.number_input(
                    "فرق عدد ايام من اخر متابعة (الحد الأدنى)",
                    min_value=1,
                    value=7,
                    step=1,
                    key="neglect_snb_days"
                )
    
            uploaded_file = st.file_uploader(
                "رفع ملف المحفظة",
                type=["xlsx", "xls"],
                key="neglect_file_uploader"
            )
    
            # ============================================================
            # الدالة المعالجة الأساسية - Cached
            # (بتشتغل تاني بس لو الملف أو نوع المحفظة أو عدد الأيام اتغيروا،
            #  مش لما تغيّر السلايسر)
            # ============================================================
            @st.cache_data(show_spinner="جاري معالجة الملف...")
            def process_neglect(file_bytes, portfolio_type_, days_threshold_):
    
                import pandas as pd
                import re
                from io import BytesIO
    
                df = pd.read_excel(BytesIO(file_bytes))
    
                # حذف أول صف إذا كان التقرير يحتوي على صف إضافي
                df = df.iloc[1:].reset_index(drop=True)
    
                today = pd.Timestamp.today().normalize()
    
                # ============================================================
                # مسار NPL&Dpd60 - زي الكود الأصلي بالظبط + threshold قابل للتغيير
                # ============================================================
                if portfolio_type_ == "NPL&Dpd60":
    
                    text_cols = [
                        "Sales Team",
                        "Sub State",
                        "حالة المعالجة - التمويل"
                    ]
                    for col in text_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(str).str.strip()
    
                    df["Follow up Last Date"] = pd.to_datetime(
                        df["Follow up Last Date"],
                        errors="coerce"
                    ).dt.normalize()
    
                    # Sales Team
                    df = df[df["Sales Team"] != "Sara || Op"]
    
                    # Payment: سيب السالب والصفر فقط
                    df["Payment"] = (
                        df["Payment"]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.strip()
                    )
                    df["Payment"] = pd.to_numeric(df["Payment"], errors="coerce")
                    df = df[df["Payment"] <= 0]
    
                    # عدد أيام الإهمال
                    df["عدد أيام الإهمال"] = (today - df["Follow up Last Date"]).dt.days
    
                    if "فرق عدد ايام من اخر متابعة" in df.columns:
                        df.drop(columns=["فرق عدد ايام من اخر متابعة"], inplace=True)
    
                    insert_position = df.columns.get_loc("Follow up Last Date") + 1
                    df.insert(
                        insert_position,
                        "فرق عدد ايام من اخر متابعة",
                        (today - df["Follow up Last Date"]).dt.days
                    )
    
                    df = df[df["عدد أيام الإهمال"] >= days_threshold_]
    
                    # Sub State
                    allowed_states = [
                        "⁠وعد بسداد مبلغ المعالجة",
                        "*رافض السداد",
                        "*مسجون",
                        "*مماطل",
                        "تم سداد جزء وليس مبلغ المعالجة",
                        "لا يجيب",
                        "وعد بسداد تسوية",
                        "وعد بسداد جزء من المتأخرات",
                        "وعد بسداد قسط",
                        "وعد بسداد كامل المتأخرات",
                        "وعد بسداد كامل المديونية",
                        "يرغب بجدولة المديونية"
                    ]
                    df = df[df["Sub State"].isin(allowed_states)]
    
                    # حالة المعالجة
                    df = df[
                        (df["حالة المعالجة - التمويل"] == "لم يتم المعالجة")
                        | (df["حالة المعالجة - التمويل"].isna())
                    ]
    
                    supervisor_col_ = "ملاحظات-التمويل"
    
                # ============================================================
                # مسار SNB - إجراءات مختلفة
                # ============================================================
                else:
    
                    text_cols = ["Sales Team", "Salesperson", "Sub State"]
                    for col in text_cols:
                        if col in df.columns:
                            df[col] = df[col].astype(str).str.strip()
    
                    df["Follow up Last Date"] = pd.to_datetime(
                        df["Follow up Last Date"],
                        errors="coerce"
                    ).dt.normalize()
    
                    # 1) Sales Team - زي صفحة الوعود
                    allowed_sales_teams = [
                        "SNB II Alsarhan II Naser",
                        "SNB II Alsarhan II Tariq"
                    ]
                    df = df[df["Sales Team"].isin(allowed_sales_teams)]
    
                    # 2) Salesperson - زي صفحة الوعود
                    excluded_salespersons = [
                        "Closed payments II Alaa SNB",
                        "Hold Companies II SNB2",
                        "Abdullah Alsarhan",
                        "Archive Companies II Alaa SNB"
                    ]
                    df = df[
                        (~df["Salesperson"].isin(excluded_salespersons))
                        & (df["Salesperson"].notna())
                        & (df["Salesperson"].str.strip() != "")
                        & (df["Salesperson"].str.lower() != "nan")
                    ]
    
                    # 3) Payment - سيب الصفر بس
                    df["Payment"] = (
                        df["Payment"]
                        .astype(str)
                        .str.replace(",", "", regex=False)
                        .str.strip()
                    )
                    df["Payment"] = pd.to_numeric(df["Payment"], errors="coerce")
                    df = df[df["Payment"] == 0]
    
                    # 4) Sub State - مطابقة "contains" لكن متسامحة مع المسافات
                    # والرموز الزيادة (زي مسافات إضافية أو رموز غير مرئية)
                    def normalize_text(x):
                        if pd.isna(x):
                            return ""
                        x = str(x)
                        x = re.sub(r"[\u200b\u200c\u200d\u200e\u200f\ufeff]", "", x)
                        x = re.sub(r"\s+", "", x)
                        return x.strip()
    
                    target_states = [
                        "تم ابلاغ العميل - اتصال",
                        "جدولة",
                        "سداد جزئي",
                        "قيد التفاوض مع الورثة",
                        "مماطل",
                        "واعد بالسداد"
                    ]
                    normalized_targets = [normalize_text(t) for t in target_states]
    
                    df["_sub_state_norm"] = df["Sub State"].apply(normalize_text)
                    df = df[
                        df["_sub_state_norm"].apply(
                            lambda v: any(t in v for t in normalized_targets)
                        )
                    ]
                    df = df.drop(columns=["_sub_state_norm"])
    
                    # 5) Follow up Last Date - عمود الفرق + الفلترة بالـ threshold
                    if "فرق عدد ايام من اخر متابعة" in df.columns:
                        df.drop(columns=["فرق عدد ايام من اخر متابعة"], inplace=True)
    
                    insert_position = df.columns.get_loc("Follow up Last Date") + 1
                    df.insert(
                        insert_position,
                        "فرق عدد ايام من اخر متابعة",
                        (today - df["Follow up Last Date"]).dt.days
                    )
    
                    df = df[df["فرق عدد ايام من اخر متابعة"] >= days_threshold_]
    
                    supervisor_col_ = "Sales Team"
    
                return df.reset_index(drop=True), supervisor_col_
    
            if uploaded_file:
    
                import pandas as pd
                import plotly.express as px
                from io import BytesIO
    
                file_bytes = uploaded_file.getvalue()
                df, supervisor_col = process_neglect(
                    file_bytes, neglect_portfolio_type, neglect_days_threshold
                )
    
                # ============================
                # تحميل الملف
                # ============================
                output = BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    df.to_excel(writer, index=False)
                output.seek(0)
    
                st.success(f"تم استخراج {len(df)} حساب")
    
                st.download_button(
                    "📥 تحميل تقرير الإهمال",
                    data=output,
                    file_name="الاهمال.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
                # ============================================================
                # داشبورد الإهمال
                # ============================================================
    
                st.markdown("---")
                st.markdown("## 📊 داشبورد الإهمال")
    
                required_report_cols = [supervisor_col, "Salesperson", "Net Amount", "Account Number"]
                missing_report_cols = [c for c in required_report_cols if c not in df.columns]
    
                if missing_report_cols:
                    st.warning(
                        f"الأعمدة دي مش موجودة في الملف المرفوع: {', '.join(missing_report_cols)} — "
                        "قسم الداشبورد مش هيظهر."
                    )
                else:
    
                    # ---------------------------
                    # سلايسرات (المشرف / الموظف)
                    # مش بيعملوا Re-process — بس فلترة على الداتا المحفوظة (df) اللي اتعملها كاش
                    # ---------------------------
    
                    all_supervisors = sorted(df[supervisor_col].dropna().unique().tolist())
                    all_salespersons = sorted(df["Salesperson"].dropna().unique().tolist())
    
                    filter_col1, filter_col2 = st.columns(2)
    
                    with filter_col1:
                        selected_supervisors = st.multiselect(
                            "فلترة حسب المشرف",
                            options=all_supervisors,
                            default=[],
                            key="neglect_supervisor_filter"
                        )
    
                    with filter_col2:
                        selected_salespersons = st.multiselect(
                            "فلترة حسب الموظف (Salesperson)",
                            options=all_salespersons,
                            default=[],
                            key="neglect_salesperson_filter"
                        )
    
                    def apply_dashboard_filters(d):
                        out = d
                        if selected_supervisors:
                            out = out[out[supervisor_col].isin(selected_supervisors)]
                        if selected_salespersons:
                            out = out[out["Salesperson"].isin(selected_salespersons)]
                        return out
    
                    df_f = apply_dashboard_filters(df)
    
                    # ---------------------------
                    # دالة بناء تقرير Pivot-style
                    # ---------------------------
    
                    def build_pivot_style(d, extra_col=None, extra_label=None, extra_agg="sum"):
                        base_cols = ["مبلغ المديونية", "عدد الحسابات"]
                        if extra_col:
                            base_cols.append(extra_label)
                        out_cols = base_cols + ["الموظف", "المشرف"]
    
                        if d.empty:
                            return pd.DataFrame(columns=out_cols)
    
                        rows = []
                        grand_amount = 0.0
                        grand_count = 0
                        grand_extra = 0.0
    
                        for supervisor, sup_group in d.groupby(supervisor_col, dropna=False):
                            sup_amount = 0.0
                            sup_count = 0
                            sup_extra = 0.0
    
                            emp_amount = sup_group.groupby("Salesperson", dropna=False)["Net Amount"].sum()
                            emp_count = sup_group.groupby("Salesperson", dropna=False)["Account Number"].nunique()
                            if extra_col:
                                if extra_agg == "sum":
                                    emp_extra = sup_group.groupby("Salesperson", dropna=False)[extra_col].sum()
                                else:
                                    emp_extra = sup_group.groupby("Salesperson", dropna=False)[extra_col].mean()
    
                            for salesperson in emp_amount.sort_values(ascending=False).index:
                                amount_val = float(emp_amount.get(salesperson, 0))
                                count_val = int(emp_count.get(salesperson, 0))
                                row = {
                                    "مبلغ المديونية": amount_val,
                                    "عدد الحسابات": count_val,
                                    "الموظف": salesperson,
                                    "المشرف": supervisor,
                                }
                                if extra_col:
                                    extra_val = float(emp_extra.get(salesperson, 0))
                                    row[extra_label] = extra_val
                                    sup_extra += extra_val
                                rows.append(row)
                                sup_amount += amount_val
                                sup_count += count_val
    
                            total_row = {
                                "مبلغ المديونية": sup_amount,
                                "عدد الحسابات": sup_count,
                                "الموظف": f"{supervisor} إجمالي",
                                "المشرف": supervisor,
                            }
                            if extra_col:
                                total_row[extra_label] = (
                                    sup_extra if extra_agg == "sum" else (sup_extra / max(sup_count, 1))
                                )
                            rows.append(total_row)
    
                            grand_amount += sup_amount
                            grand_count += sup_count
                            grand_extra += sup_extra
    
                        grand_row = {
                            "مبلغ المديونية": grand_amount,
                            "عدد الحسابات": grand_count,
                            "الموظف": "الاجمالي",
                            "المشرف": "",
                        }
                        if extra_col:
                            grand_row[extra_label] = (
                                grand_extra if extra_agg == "sum" else (grand_extra / max(grand_count, 1))
                            )
                        rows.append(grand_row)
    
                        return pd.DataFrame(rows)[out_cols]
    
                    def style_summary(d, extra_label=None):
                        fmt = {"مبلغ المديونية": "{:,.0f}", "عدد الحسابات": "{:,.0f}"}
                        if extra_label:
                            fmt[extra_label] = "{:,.0f}"
    
                        def highlight_rows(row):
                            is_total = (row["الموظف"] == "الاجمالي") or ("إجمالي" in str(row["الموظف"]))
                            if is_total:
                                return ["font-weight: bold; color: #000000; background-color: #eef2f7"] * len(row)
                            return [""] * len(row)
    
                        return d.style.apply(highlight_rows, axis=1).format(fmt)
    
                    day_col_label = (
                        "عدد أيام الإهمال" if neglect_portfolio_type == "NPL&Dpd60"
                        else "فرق عدد ايام من اخر متابعة"
                    )
    
                    # ---------------------------
                    # 1) تقرير الإهمال
                    # ---------------------------
                    st.markdown("### 📄 تقرير الإهمال")
                    neglect_summary = build_pivot_style(df_f)
                    if neglect_summary.empty:
                        st.info("لا توجد بيانات مطابقة.")
                    else:
                        st.dataframe(style_summary(neglect_summary), use_container_width=True, hide_index=True)
    
                    # ---------------------------
                    # 2) تقرير متوسط عدد الأيام
                    # ---------------------------
                    st.markdown(f"### 📄 تقرير {day_col_label}")
                    days_summary = build_pivot_style(
                        df_f,
                        extra_col="فرق عدد ايام من اخر متابعة",
                        extra_label=day_col_label,
                        extra_agg="sum"
                    )
                    if days_summary.empty:
                        st.info("لا توجد بيانات مطابقة.")
                    else:
                        st.dataframe(
                            style_summary(days_summary, extra_label=day_col_label),
                            use_container_width=True, hide_index=True
                        )
    
                    # ---------------------------
                    # أصل البيانات
                    # ---------------------------
                    st.markdown("### 🗂️ أصل البيانات - الإهمال")
                    st.dataframe(df_f, use_container_width=True, hide_index=True)
    
                    # ---------------------------
                    # الشارتات
                    # ---------------------------
                    st.markdown("### 📈 الرسوم البيانية")
    
                    SNB_GREEN = "#00693E"
                    SNB_GOLD = "#C9A227"
                    SNB_RED = "#A33A3A"
    
                    DATA_LABEL_FONT = dict(size=16, family="Arial Black", color="white")
                    XAXIS_TICK_FONT = dict(size=14, family="Arial Black", color="white")
    
                    sup_amount = (
                        df_f.groupby(supervisor_col, dropna=False)["Net Amount"].sum()
                        .reset_index().rename(columns={supervisor_col: "المشرف", "Net Amount": "مبلغ المديونية"})
                    )
    
                    if not sup_amount.empty:
                        fig1 = px.bar(
                            sup_amount, x="المشرف", y="مبلغ المديونية", text="مبلغ المديونية",
                            color_discrete_sequence=[SNB_RED]
                        )
                        fig1.update_traces(
                            texttemplate="<b>%{text:,.0f}</b>",
                            textposition="outside",
                            textfont=DATA_LABEL_FONT
                        )
                        fig1.update_xaxes(tickfont=XAXIS_TICK_FONT)
                        fig1.update_layout(height=420, xaxis_tickangle=-20, margin=dict(t=20, b=10))
                        st.plotly_chart(fig1, use_container_width=True)
    
                    emp_count = (
                        df_f.groupby("Salesperson", dropna=False)["Account Number"].nunique()
                        .reset_index(name="عدد الحسابات")
                        .sort_values("عدد الحسابات", ascending=False).head(15)
                    )
                    if not emp_count.empty:
                        st.markdown("#### أعلى 15 موظف بعدد الحسابات (الإهمال)")
                        fig2 = px.bar(
                            emp_count, x="Salesperson", y="عدد الحسابات", text="عدد الحسابات",
                            color_discrete_sequence=[SNB_GOLD]
                        )
                        fig2.update_traces(
                            texttemplate="<b>%{text}</b>",
                            textposition="outside",
                            textfont=DATA_LABEL_FONT
                        )
                        fig2.update_xaxes(tickfont=XAXIS_TICK_FONT)
                        fig2.update_layout(height=420, xaxis_tickangle=-30, margin=dict(t=20, b=10))
                        st.plotly_chart(fig2, use_container_width=True)
    
                    days_by_sup = (
                        df_f.groupby(supervisor_col, dropna=False)["فرق عدد ايام من اخر متابعة"].mean()
                        .reset_index().rename(columns={
                            supervisor_col: "المشرف",
                            "فرق عدد ايام من اخر متابعة": "متوسط عدد الأيام"
                        })
                    )
                    if not days_by_sup.empty:
                        st.markdown(f"#### متوسط {day_col_label} لكل مشرف")
                        fig3 = px.bar(
                            days_by_sup, x="المشرف", y="متوسط عدد الأيام", text="متوسط عدد الأيام",
                            color_discrete_sequence=[SNB_GREEN]
                        )
                        fig3.update_traces(
                            texttemplate="<b>%{text:.1f}</b>",
                            textposition="outside",
                            textfont=DATA_LABEL_FONT
                        )
                        fig3.update_xaxes(tickfont=XAXIS_TICK_FONT)
                        fig3.update_layout(height=420, xaxis_tickangle=-20, margin=dict(t=20, b=10))
                        st.plotly_chart(fig3, use_container_width=True)


   
    
         

# ======================
# PAGE 4 - التغطية
# ======================
elif page == "التغطية":
    st.subheader("🌐 التغطية")
    st.write("نسب التغطية")


# ======================
# PAGE 5 - النشاط
# ======================
# ============================================================
# ملاحظة مهمة قبل الكود:
# مفيش مكتبة بايثون (openpyxl / xlsxwriter) بتقدر تعمل
# PivotTable حقيقي (اللي بتسحب فيه الحقول بنفسك جوه إكسيل)
# من غير إكسيل نفسه شغال (COM) — ودة مش متاح على Streamlit Cloud
# لأنه Linux وملوش Excel.
# البديل العملي اللي هعمله: شيت "Pivot" منسق كـ Excel Table
# حقيقي (فيه Filter + Sort جاهزين) وبيدي بالظبط الأرقام اللي
# طلبتها (ناجحة / مغطاة لكل محصل). لو عايز Pivot تفاعلي 100%
# تقدر تعمل Insert > PivotTable على الشيت دة من جوه إكسيل نفسه
# في ثانية لأن الداتا هتبقى جاهزة كـ Table.
# ============================================================

# ============================================================
# محتاج تضيف الاستيراد ده فوق مع باقي الـ imports (لو مش موجود):
#   import plotly.express as px
# ومحتاج تضيف plotly في requirements.txt
# ============================================================
# ملاحظة عن الألوان: مفيش ملف ألوان رسمي متاح للعامة من البنك
# الأهلي السعودي (SNB)، فاستخدمت باليتة أخضر غامق/ذهبي قريبة
# من هوية البنوك السعودية بشكل عام (مش شعار أو أصول مسجلة
# ملكية للبنك) — لو عندك الـ Brand Guidelines بتاعتهم ابعتلي
# الأكواد بالظبط وأظبطها.
# ============================================================

elif page == "النشاط":

    st.subheader("⚡ النشاط")

    uploaded_file = st.file_uploader(
        "رفع ملف واحد فقط",
        type=["xlsx", "xls"],
        accept_multiple_files=False
    )

    if uploaded_file:

        # =========================
        # الخطوة 1: هل فيه بريك؟
        # =========================

        if "break_choice" not in st.session_state:
            st.session_state.break_choice = None

        if st.session_state.break_choice is None:

            st.markdown("### هل يوجد بريك؟")
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Yes", use_container_width=True):
                    st.session_state.break_choice = "yes"
                    st.rerun()

            with col2:
                if st.button("No", use_container_width=True):
                    st.session_state.break_choice = "no"
                    st.rerun()

            st.stop()

        if st.button("🔄 تغيير الاختيار (فيه بريك / مفيش)"):
            st.session_state.break_choice = None
            st.session_state.pop("processed_output", None)
            st.session_state.pop("processed_df", None)
            st.rerun()

        has_break = st.session_state.break_choice == "yes"
        break_start_minutes = None
        break_end_minutes = None

        if has_break:
            st.markdown("### 🕐 إعدادات البريك")
            col1, col2 = st.columns(2)

            with col1:
                break_start = st.time_input("البريك يبدأ الساعة", value=time(12, 0))
            with col2:
                break_duration = st.number_input("مدة البريك بالدقائق", min_value=1, value=30, step=5)

            break_start_minutes = break_start.hour * 60 + break_start.minute
            break_end_minutes = break_start_minutes + int(break_duration)

            st.info(
                f"البريك من {break_start.strftime('%H:%M')} إلى "
                f"{(datetime.combine(date.today(), break_start) + timedelta(minutes=break_duration)).strftime('%H:%M')}"
            )
        else:
            st.info("تم اختيار: لا يوجد بريك.")

        start_button = st.button("🚀 ابدأ التصنيف", type="primary")

        # =========================
        # المعالجة (مرة واحدة فقط) + تخزين النتيجة في session_state
        # =========================

        if start_button:

            df = pd.read_excel(uploaded_file)
            df = df.iloc[1:].reset_index(drop=True)

            required_columns = ["Notes", "Created on", "Collector"]
            missing_columns = [c for c in required_columns if c not in df.columns]
            if missing_columns:
                st.error(f"الأعمدة التالية غير موجودة في الملف: {', '.join(missing_columns)}")
                st.stop()

            duplicate_columns = ["Collector", "ID Number", "Notes"]
            missing_duplicate_columns = [c for c in duplicate_columns if c not in df.columns]
            if missing_duplicate_columns:
                st.error(f"الأعمدة التالية غير موجودة: {', '.join(missing_duplicate_columns)}")
                st.stop()

            if "Final State" not in df.columns:
                st.error("لا يوجد عمود Final State في الملف")
                st.stop()

            progress_bar = st.progress(0)
            status = st.empty()

            predictions = []
            probabilities = []
            total = len(df)

            for i, text in enumerate(df["Notes"]):
                label, prob = predict_text(text)
                predictions.append(label)
                probabilities.append(prob)
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status.text(f"{int(progress * 100)}% ({i + 1}/{total})")

            notes_index = df.columns.get_loc("Notes")
            df.insert(notes_index + 1, "التصنيف", predictions)
            df.insert(notes_index + 2, "Probability (%)", probabilities)
            df["التصنيف"] = df["التصنيف"].astype(str)

            df["Created on"] = pd.to_datetime(df["Created on"], errors="coerce")
            df = df.drop_duplicates(subset=duplicate_columns, keep="first").reset_index(drop=True)
            df = df.sort_values(["Collector", "Created on"]).reset_index(drop=True)

            df["فرق التوقيت"] = (
                df.groupby("Collector")["Created on"].diff().dt.total_seconds().div(60)
            )

            def calculate_wasted(row):
                call_time = row["Created on"]
                classification = row["التصنيف"]
                time_diff = row["فرق التوقيت"]

                if pd.isna(time_diff) or pd.isna(call_time):
                    return 0
                if time_diff < 0:
                    return 0

                if has_break:
                    call_minutes = call_time.hour * 60 + call_time.minute
                    if break_start_minutes <= call_minutes < break_end_minutes:
                        return 0

                if classification == "1":
                    wasted = time_diff - 20
                elif classification == "0":
                    wasted = time_diff - 5
                else:
                    wasted = 0

                return max(wasted, 0)

            df["وقت مهدر"] = df.apply(calculate_wasted, axis=1)

            cols = list(df.columns)
            prob_index = cols.index("Probability (%)")
            for col in ["فرق التوقيت", "وقت مهدر"]:
                cols.remove(col)
            prob_index = cols.index("Probability (%)")
            cols.insert(prob_index + 1, "فرق التوقيت")
            cols.insert(prob_index + 2, "وقت مهدر")
            df = df[cols]

            collector_summary = (
                df.groupby("Collector", as_index=False)["وقت مهدر"]
                .sum().sort_values("وقت مهدر", ascending=False).reset_index(drop=True)
            )
            calls_over_30 = df[df["فرق التوقيت"] > 30].sort_values("فرق التوقيت", ascending=False)
            calls_under_1 = df[df["فرق التوقيت"] < 1].sort_values("فرق التوقيت", ascending=True)

            first_activity = (
                df.dropna(subset=["Created on"]).sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False).first()[["Collector", "Created on", "التصنيف", "Probability (%)"]]
                .rename(columns={"Created on": "وقت أول إفادة"})
            )
            last_activity = (
                df.dropna(subset=["Created on"]).sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False).last()[["Collector", "Created on", "التصنيف", "Probability (%)", "Final State", "Notes"]]
                .rename(columns={"Created on": "وقت آخر إفادة"})
            )

            final_state_summary = df["Final State"].fillna("Blank").value_counts().reset_index()
            final_state_summary.columns = ["Final State", "عدد الحالات"]

            pivot_summary = (
                df.groupby(["Collector", "التصنيف"]).size().unstack(fill_value=0)
                .rename(columns={"1": "مكالمات ناجحة", "0": "مكالمات غير ناجحة"})
            )
            for needed_col in ["مكالمات ناجحة", "مكالمات غير ناجحة"]:
                if needed_col not in pivot_summary.columns:
                    pivot_summary[needed_col] = 0
            pivot_summary = pivot_summary[["مكالمات ناجحة", "مكالمات غير ناجحة"]]
            pivot_summary["إجمالي المكالمات المغطاة"] = pivot_summary.sum(axis=1)
            pivot_summary["نسبة النجاح %"] = (
                (pivot_summary["مكالمات ناجحة"] / pivot_summary["إجمالي المكالمات المغطاة"] * 100).round(1)
            )
            pivot_summary = pivot_summary.reset_index().sort_values("إجمالي المكالمات المغطاة", ascending=False).reset_index(drop=True)

            first_after_break = None
            if has_break:
                after_break = df[df["Created on"].notna()].copy()
                after_break["وقت بالدقائق"] = after_break["Created on"].dt.hour * 60 + after_break["Created on"].dt.minute
                after_break = after_break[after_break["وقت بالدقائق"] >= break_end_minutes]
                first_after_break = (
                    after_break.sort_values(["Collector", "Created on"]).groupby("Collector", as_index=False).first()
                    [["Collector", "Created on", "التصنيف", "Probability (%)"]].rename(columns={"Created on": "وقت أول إفادة بعد البريك"})
                )
                first_after_break["حالة النجاح"] = first_after_break["التصنيف"].apply(
                    lambda v: "ناجحة" if v == "1" else ("غير ناجحة" if v == "0" else v)
                )

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="النشاط")
                pivot_summary.to_excel(writer, index=False, sheet_name="Pivot - أداء المحصلين")
                collector_summary.to_excel(writer, index=False, sheet_name="إجمالي الوقت المهدر")
                calls_over_30.to_excel(writer, index=False, sheet_name="مكالمات +30 دقيقة")
                calls_under_1.to_excel(writer, index=False, sheet_name="مكالمات أقل من دقيقة")
                first_activity.to_excel(writer, index=False, sheet_name="أول إفادة")
                last_activity.to_excel(writer, index=False, sheet_name="آخر إفادة")
                if first_after_break is not None:
                    first_after_break.to_excel(writer, index=False, sheet_name="أول إفادة بعد البريك")
                final_state_summary.to_excel(writer, index=False, sheet_name="Final State")

                workbook = writer.book
                header_fill = PatternFill(fill_type="solid", fgColor="073259")
                header_font = Font(color="FFFFFF", bold=True)
                thin_side = Side(style="thin", color="000000")
                thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

                for ws in workbook.worksheets:
                    for row in ws.iter_rows():
                        for cell in row:
                            cell.border = thin_border
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                    for cell in ws[1]:
                        cell.fill = header_fill
                        cell.font = header_font
                        cell.border = thin_border
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                    for column_cells in ws.columns:
                        max_length = 0
                        column_letter = column_cells[0].column_letter
                        for cell in column_cells:
                            if cell.value is not None:
                                max_length = max(max_length, len(str(cell.value)))
                        ws.column_dimensions[column_letter].width = min(max_length + 3, 50)
                    ws.row_dimensions[1].height = 25

                pivot_ws = workbook["Pivot - أداء المحصلين"]
                last_col_letter = pivot_ws.cell(row=1, column=pivot_ws.max_column).column_letter
                table_range = f"A1:{last_col_letter}{pivot_ws.max_row}"
                excel_table = Table(displayName="PivotAdaaAlMohaseleen", ref=table_range)
                excel_table.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
                pivot_ws.add_table(excel_table)

            output.seek(0)

            st.session_state.processed_output = output.getvalue()
            st.session_state.processed_df = df.copy()

            status.empty()
            progress_bar.empty()
            st.success("تم الانتهاء")

        if "processed_output" in st.session_state:
            st.download_button(
                "تحميل الملف",
                st.session_state.processed_output,
                file_name="activity.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        # ============================================================
        # الداشبورد (4 Cards + 4 Charts) — بيظهر بعد التصنيف مباشرة
        # ============================================================

# ============================================================
# ده بديل قسم "الداشبورد" بالكامل (من سطر SNB_GREEN = ...
# لحد آخر سطر في الملف اللي فاتت). امسح القسم القديم وحط
# ده مكانه، والباقي (البريك + التصنيف + تحميل الإكسيل) زي ما هو.
# ============================================================

        if "processed_df" in st.session_state:

            data = st.session_state.processed_df

            SNB_GREEN = "#00693E"
            SNB_GREEN_DARK = "#024930"
            SNB_GOLD = "#C9A227"
            SNB_RED = "#A33A3A"

            st.markdown("---")
            st.markdown("## 📊 داشبورد النشاط")

            # ---------------------------
            # السلايسرات (محصل / مشرف)
            # ---------------------------

            possible_supervisor_cols = ["Sales Team", "Supervisor", "المشرف", "Team Leader", "TL", "Manager", "Supervisor Name"]
            supervisor_col = next((c for c in possible_supervisor_cols if c in data.columns), None)

            filter_col1, filter_col2 = st.columns(2)

            with filter_col1:
                selected_collectors = st.multiselect(
                    "فلترة حسب المحصل",
                    options=sorted(data["Collector"].dropna().unique().tolist()),
                    default=[]
                )

            with filter_col2:
                if supervisor_col:
                    selected_supervisors = st.multiselect(
                        "فلترة حسب المشرف",
                        options=sorted(data[supervisor_col].dropna().unique().tolist()),
                        default=[]
                    )
                else:
                    selected_supervisors = []
                    st.caption(
                        "⚠️ مفيش عمود واضح للمشرف في الملف المرفوع "
                        "(بحثت عن: Supervisor / المشرف / Team Leader). "
                        "لو الملف فيه عمود بالاسم دة، ابعتلي اسمه بالظبط عشان أظبط الفلتر."
                    )

            filtered = data.copy()
            if selected_collectors:
                filtered = filtered[filtered["Collector"].isin(selected_collectors)]
            if supervisor_col and selected_supervisors:
                filtered = filtered[filtered[supervisor_col].isin(selected_supervisors)]

            if filtered.empty:
                st.warning("مفيش بيانات مطابقة للفلتر المختار.")
                st.stop()

            # ---------------------------
            # حساب مقاييس كل محصل (مستخدمة في الـ Cards والـ Charts)
            # ---------------------------

            collector_agg = filtered.groupby("Collector").agg(
                المكالمات_المغطاة=("Collector", "size"),
                المكالمات_الناجحة=("التصنيف", lambda s: (s == "1").sum()),
                الوقت_المهدر=("وقت مهدر", "sum"),
            ).reset_index()

            def normalize_0_100(s):
                if s.max() == s.min():
                    return pd.Series([100.0] * len(s), index=s.index)
                return (s - s.min()) / (s.max() - s.min()) * 100

            collector_agg["_covered_norm"] = normalize_0_100(collector_agg["المكالمات_المغطاة"])
            collector_agg["_success_norm"] = normalize_0_100(collector_agg["المكالمات_الناجحة"])
            collector_agg["_wasted_norm"] = normalize_0_100(collector_agg["الوقت_المهدر"])

            # سكور الفاعلية: 35% تغطية + 35% نجاح + 30% (100 - وقت مهدر)
            # يعني اللي بيغطي مكالمات كتير وناجح فيها وبيضيع وقت أقل بيطلع فوق
            collector_agg["سكور الفاعلية"] = (
                collector_agg["_covered_norm"] * 0.35
                + collector_agg["_success_norm"] * 0.35
                + (100 - collector_agg["_wasted_norm"]) * 0.30
            ).round(1)

            collector_agg = collector_agg.sort_values("سكور الفاعلية", ascending=False).reset_index(drop=True)
            top_performer = collector_agg.iloc[0]

            # ---------------------------
            # الـ 4 Cards
            # ---------------------------

            total_covered = len(filtered)
            total_successful = int((filtered["التصنيف"] == "1").sum())
            
            # Average وقت مهدر
            avg_wasted = filtered["وقت مهدر"].mean()
            avg_wasted = 0 if pd.isna(avg_wasted) else avg_wasted
            
            
            def render_card(col, title, value, subtitle=""):
                with col:
                    st.markdown(
                        f'<div style="background: linear-gradient(135deg, {SNB_GREEN} 0%, {SNB_GREEN_DARK} 100%); '
                        f'border-right: 5px solid {SNB_GOLD}; border-radius: 14px; padding: 18px; color: white; '
                        f'text-align: center; box-shadow: 0 4px 14px rgba(0,0,0,0.15); min-height: 130px;">'
                        f'<div style="font-size:13px; opacity:0.85; margin-bottom:8px;">{title}</div>'
                        f'<div style="font-size:24px; font-weight:800; overflow-wrap:anywhere;">{value}</div>'
                        f'<div style="font-size:11px; opacity:0.75; margin-top:6px;">{subtitle}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
            
            
            c1, c2, c3, c4 = st.columns(4)
            
            render_card(
                c1,
                "عدد المكالمات المغطاة",
                f"{total_covered:,}"
            )
            
            render_card(
                c2,
                "عدد المكالمات الناجحة",
                f"{total_successful:,}",
                f"{(total_successful / total_covered * 100 if total_covered else 0):.1f}% من المغطاة"
            )
            
            render_card(
                c3,
                "متوسط الوقت المهدر (AVG)",
                f"{avg_wasted:.1f} د"
            )
            
            render_card(
                c4,
                "أكتر محصل فاعلية",
                f"{top_performer['Collector']}",
                f"سكور {top_performer['سكور الفاعلية']:.0f}/100"
            )
            
            st.caption(
                "سكور الفاعلية بيوازن بين: عدد المكالمات المغطاة، عدد المكالمات الناجحة، "
                "ووقت الهدر (كل ما الوقت المهدر أقل كل ما السكور أعلى) — كل عامل بوزن نسبي "
                "مقارنة بباقي المحصلين في نفس الفلتر الحالي."
            )

            st.markdown("")

            with st.expander("📋 آخر نشاط لكل محصل"):
                last_per_collector = (
                    filtered.dropna(subset=["Created on"])
                    .sort_values(["Collector", "Created on"])
                    .groupby("Collector", as_index=False)
                    .last()
                )
                show_cols = [c for c in ["Collector", "Created on", "التصنيف", "Probability (%)", "Final State", "Notes"] if c in last_per_collector.columns]
                st.dataframe(last_per_collector[show_cols], use_container_width=True, hide_index=True)

            with st.expander("🏆 ترتيب المحصلين حسب سكور الفاعلية"):
                st.dataframe(
                    collector_agg[["Collector", "المكالمات_المغطاة", "المكالمات_الناجحة", "الوقت_المهدر", "سكور الفاعلية"]],
                    use_container_width=True, hide_index=True
                )

            st.markdown("")

            # ---------------------------
            # الـ 4 Charts — كل شارت ياخد مساحته كاملة (مش نص الشاشة)
            # ---------------------------

            base_font = dict(size=14)

            # 1) مكالمات ناجحة/غير ناجحة لكل محصل — Bar أفقي عشان الأسماء تبقى واضحة
            st.markdown("#### مكالمات ناجحة مقابل غير ناجحة لكل محصل")

            chart1_data = filtered.groupby(["Collector", "التصنيف"]).size().reset_index(name="عدد المكالمات")
            chart1_data["الحالة"] = chart1_data["التصنيف"].map({"1": "ناجحة", "0": "غير ناجحة"}).fillna(chart1_data["التصنيف"])

            n_collectors = filtered["Collector"].nunique()
            fig1_height = max(400, 55 * n_collectors)

            fig1 = px.bar(
                chart1_data, y="Collector", x="عدد المكالمات", color="الحالة",
                orientation="h", barmode="stack", text="عدد المكالمات",
                color_discrete_map={"ناجحة": SNB_GREEN, "غير ناجحة": SNB_GOLD}
            )
            fig1.update_traces(textposition="inside", textfont=dict(color="white", size=13))
            fig1.update_layout(
                height=fig1_height, font=base_font, legend_title_text="",
                margin=dict(t=10, b=10),
                yaxis={"categoryorder": "total ascending"}
            )
            st.plotly_chart(fig1, use_container_width=True)

            # 2) توزيع Final State — Column chart بدل الـ Pie
            st.markdown("#### توزيع Final State")

            fs_data = filtered["Final State"].fillna("Blank").value_counts().reset_index()
            fs_data.columns = ["Final State", "عدد"]
            fs_data = fs_data.sort_values("عدد", ascending=False)

            if len(fs_data) > 12:
                top_fs = fs_data.iloc[:11]
                other_sum = fs_data.iloc[11:]["عدد"].sum()
                fs_data = pd.concat([top_fs, pd.DataFrame({"Final State": ["أخرى"], "عدد": [other_sum]})], ignore_index=True)

            fig2 = px.bar(
                fs_data, x="Final State", y="عدد", text="عدد",
                color_discrete_sequence=[SNB_GREEN]
            )
            fig2.update_traces(textposition="outside", textfont=dict(size=13))
            fig2.update_layout(
                height=450, font=base_font, margin=dict(t=20, b=10),
                xaxis_tickangle=-30
            )
            st.plotly_chart(fig2, use_container_width=True)

            # 3) الوقت المهدر لكل محصل — Bar
            st.markdown("#### الوقت المهدر لكل محصل")

            wasted_data = (
                filtered.groupby("Collector", as_index=False)["وقت مهدر"]
                .sum().sort_values("وقت مهدر", ascending=False)
            )
            fig3_height = max(400, 45 * len(wasted_data))

            fig3 = px.bar(
                wasted_data, x="وقت مهدر", y="Collector", orientation="h",
                text="وقت مهدر", color_discrete_sequence=[SNB_RED]
            )
            fig3.update_traces(texttemplate="%{text:.0f}", textposition="outside", textfont=dict(size=13))
            fig3.update_layout(
                height=fig3_height, font=base_font, margin=dict(t=10, b=10),
                yaxis={"categoryorder": "total ascending"}
            )
            st.plotly_chart(fig3, use_container_width=True)

            # 4) توزيع المكالمات عبر ساعات اليوم
            st.markdown("#### توزيع المكالمات عبر ساعات اليوم")

            hour_data = filtered.dropna(subset=["Created on"]).copy()
            hour_data["الساعة"] = hour_data["Created on"].dt.hour
            hour_counts = hour_data.groupby("الساعة").size().reset_index(name="عدد المكالمات")

            fig4 = px.bar(
                hour_counts, x="الساعة", y="عدد المكالمات", text="عدد المكالمات",
                color_discrete_sequence=[SNB_GREEN_DARK]
            )
            fig4.update_traces(textposition="outside", textfont=dict(size=13))
            fig4.update_layout(
                height=420, font=base_font, margin=dict(t=20, b=10),
                xaxis=dict(dtick=1)
            )
            st.plotly_chart(fig4, use_container_width=True)


            # ============================================================
# 1) تعديل بسيط في تعريف عمود المشرف — ضيف "Sales Team" أول
#    القايمة عشان يتكشف هو الأول قبل أي اسم تاني:
#
#    possible_supervisor_cols = ["Sales Team", "Supervisor", "المشرف",
#                                 "Team Leader", "TL", "Manager", "Supervisor Name"]
#
#    (بدّل السطر القديم بده في نفس مكانه جوه قسم الداشبورد)
# ============================================================
# 2) القسم ده يتحط في الآخر، بعد آخر chart (توزيع المكالمات عبر
#    ساعات اليوم) وقبل ما يخلص الـ if "processed_df" in st.session_state:
# ============================================================

            # ---------------------------
            # تحليل العملاء (Debtor / Customer Account Number)
            # ---------------------------

# ============================================================
# 1) تعديل بسيط في تعريف عمود المشرف — ضيف "Sales Team" أول
#    القايمة عشان يتكشف هو الأول قبل أي اسم تاني:
#
#    possible_supervisor_cols = ["Sales Team", "Supervisor", "المشرف",
#                                 "Team Leader", "TL", "Manager", "Supervisor Name"]
#
#    (بدّل السطر القديم بده في نفس مكانه جوه قسم الداشبورد)
# ============================================================
# 2) القسم ده يتحط في الآخر، بعد آخر chart (توزيع المكالمات عبر
#    ساعات اليوم) وقبل ما يخلص الـ if "processed_df" in st.session_state:
# ============================================================

            # ---------------------------
            # تحليل العملاء (Debtor / Customer Account Number)
            # ---------------------------

            st.markdown("---")
            st.markdown("## 👥 تحليل العملاء")

            debtor_col = "Debtor"
            account_col = "Customer Account Number"
            missing_client_cols = [c for c in [debtor_col, account_col] if c not in filtered.columns]

            if missing_client_cols:
                st.warning(
                    f"الأعمدة دي مش موجودة في الملف المرفوع: {', '.join(missing_client_cols)} — "
                    "قسم تحليل العملاء مش هيظهر. تأكد من اسم العمود بالظبط في الشيت لو الاسم مختلف."
                )
            else:

                # كل موظف تابع كام عميل (Debtor) وكام رقم حساب (Customer Account Number)
                client_coverage = (
                    filtered.groupby("Collector")
                    .agg(
                        عدد_العملاء=(debtor_col, "nunique"),
                        عدد_أرقام_الحسابات=(account_col, "nunique"),
                        عدد_الإفادات=(debtor_col, "count"),
                    )
                    .reset_index()
                    .sort_values("عدد_العملاء", ascending=False)
                )

                st.markdown("#### كل موظف تابع كام عميل وكام رقم حساب")
                st.dataframe(client_coverage, use_container_width=True, hide_index=True)

                # الموظف اللي كرر نفس العميل أكتر من 5 مرات (أكتر من 5 إفادات على نفس الـ Debtor)
                repeat_contacts = (
                    filtered.groupby(["Collector", debtor_col])
                    .size()
                    .reset_index(name="عدد الإفادات على نفس العميل")
                )
                repeat_contacts = repeat_contacts[repeat_contacts["عدد الإفادات على نفس العميل"] >= 2]
                repeat_contacts = repeat_contacts.sort_values(
                    "عدد الإفادات على نفس العميل", ascending=False
                ).reset_index(drop=True)

                st.markdown("#### موظفين كلموا نفس العميل أكتر من مرة")

                if repeat_contacts.empty:
                    st.info("مفيش أي موظف كلم نفس العميل أكتر من مرة في البيانات الحالية.")
                else:
                    st.dataframe(repeat_contacts, use_container_width=True, hide_index=True)

                # =========================
                # زرار تحميل منفصل لتحليل العملاء
                # =========================

                client_output = BytesIO()
                with pd.ExcelWriter(client_output, engine="openpyxl") as writer:
                    client_coverage.to_excel(writer, index=False, sheet_name="تغطية العملاء لكل موظف")
                    repeat_contacts.to_excel(writer, index=False, sheet_name="تكرار نفس العميل")

                    workbook = writer.book
                    header_fill = PatternFill(fill_type="solid", fgColor="073259")
                    header_font = Font(color="FFFFFF", bold=True)
                    thin_side = Side(style="thin", color="000000")
                    thin_border = Border(left=thin_side, right=thin_side, top=thin_side, bottom=thin_side)

                    for ws in workbook.worksheets:
                        for row in ws.iter_rows():
                            for cell in row:
                                cell.border = thin_border
                                cell.alignment = Alignment(horizontal="center", vertical="center")
                        for cell in ws[1]:
                            cell.fill = header_fill
                            cell.font = header_font
                            cell.border = thin_border
                            cell.alignment = Alignment(horizontal="center", vertical="center")
                        for column_cells in ws.columns:
                            max_length = 0
                            column_letter = column_cells[0].column_letter
                            for cell in column_cells:
                                if cell.value is not None:
                                    max_length = max(max_length, len(str(cell.value)))
                            ws.column_dimensions[column_letter].width = min(max_length + 3, 50)
                        ws.row_dimensions[1].height = 25

                client_output.seek(0)

                st.download_button(
                    "⬇️ تحميل تحليل العملاء",
                    client_output.getvalue(),
                    file_name="client_analysis.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# ======================
# PAGE 6 - باقي الصفحات (مختصر)
# ======================
elif page == "التوزيع":

    st.subheader("📦 توزيع المحافظ")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel",
        type=["xlsx"]
    )
    
   
        





elif page == "اخطاء الحالات":
    st.subheader("❌ اخطاء الحالات")

elif page == "الاوتودايلر":
    st.subheader("📞 الاوتودايلر")

elif page == "مطابقة السدادات":
    st.subheader("💰 مطابقة السدادات")

elif page == "وعود لا يوجد لها تاريخ الوعد":
    st.subheader("📅 وعود بدون تاريخ")
