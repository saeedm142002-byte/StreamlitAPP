import streamlit as st
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from io import BytesIO
import torch
import torch.nn.functional as F
from datetime import datetime, date, time, timedelta
from openpyxl.worksheet.table import Table, TableStyleInfo


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
    from io import BytesIO

    st.subheader("📊 الوعود القائمة / الوعود المكسورة")

    portfolio_file = st.file_uploader(
        "رفع ملف المحفظة",
        type=["xlsx", "xls"]
    )

    if portfolio_file:

        progress_bar = st.progress(0)
        status = st.empty()

        # ==========================================
        # قراءة الملف
        # ==========================================
        df = pd.read_excel(portfolio_file)

        # حذف أول صف بعد الـ Header
        df = df.iloc[1:].reset_index(drop=True)

        # تنظيف النصوص
        text_cols = [
            "Sales Team",
            "Final State",
            "حالة المعالجة - التمويل"
        ]

        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
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

        progress_bar.progress(20)

        # ==========================================
        # فلتر مشترك
        # ==========================================
        base = df.copy()

        # حذف Sara || Op
        base = base[
            base["Sales Team"] != "Sara || Op"   
                                           
        ]

        # Final State
        base = base[
            base["Final State"].str.contains(
                "واعد بالسداد",
                na=False
            )
        ]

        # حالة المعالجة
        base = base[
            (base["حالة المعالجة - التمويل"] == "لم يتم المعالجة") |
            (base["حالة المعالجة - التمويل"].isna())
        ]

        progress_bar.progress(40)

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

        progress_bar.progress(70)

        # ==========================================
        # الوعود المكسورة
        # ==========================================
        broken = base.copy()
        
        # حذف مواعيد النهاردة والمستقبل
        broken = broken[
            broken["Follow up Due Date"] < today
        ]
        
        # الاحتفاظ فقط بالصفوف التي بها Follow up Last Date
        broken = broken[
            broken["Follow up Last Date"].notna()
        ]
        
        # حساب الفرق بين آخر متابعة وموعد الوعد
        broken["فرق الايام"] = (
            broken["Follow up Last Date"] - broken["Follow up Due Date"]
        ).dt.days
        
        # الاحتفاظ فقط بالقيم السالبة
        broken = broken[
            broken["فرق الايام"] < 0
        ]
        
        # حذف الأعمدة لو موجودة
        for col in ["عدد ايام ترحيل الوعد", "فرق الايام"]:
            if col in broken.columns:
                broken.drop(columns=[col], inplace=True)
        
        # مكان العمود بعد Follow up Last Date
        insert_position = broken.columns.get_loc("Follow up Last Date") + 1
        
        # إضافة عدد أيام ترحيل الوعد
        broken.insert(
            insert_position,
            "عدد ايام ترحيل الوعد",
            (today - broken["Follow up Due Date"]).dt.days
        )
        
        # الاحتفاظ فقط بالوعود المكسورة
        broken = broken[
            broken["عدد ايام ترحيل الوعد"] > 0
        ]
        
        progress_bar.progress(100)
        status.text("100%")

        # ==========================================
        # ملف الوعود القائمة
        # ==========================================
        output_current = BytesIO()

        with pd.ExcelWriter(
            output_current,
            engine="openpyxl"
        ) as writer:
            current.to_excel(
                writer,
                index=False
            )
        st.success(f"تم استخراج وعود قائمة {len(current)} حساب")

        
        output_current.seek(0)

         

        # ==========================================
        # ملف الوعود المكسورة
        # ==========================================
        output_broken = BytesIO()

        with pd.ExcelWriter(
            output_broken,
            engine="openpyxl"
        ) as writer:
            broken.to_excel(
                writer,
                index=False
            )

        st.success(f"تم استخراج وعود مكسورة {len(broken)} حساب")

        output_broken.seek(0)

        st.success("تم تجهيز الملفات بنجاح")

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

        uploaded_file = st.file_uploader(
            "رفع ملف المحفظة",
            type=["xlsx", "xls"]
        )

        if uploaded_file:

            import pandas as pd
            from io import BytesIO

            df = pd.read_excel(uploaded_file)

            # حذف أول صف إذا كان التقرير يحتوي على صف إضافي
            df = df.iloc[1:].reset_index(drop=True)

            # تنظيف النصوص
            text_cols = [
                "Sales Team",
                "Sub State",
                "حالة المعالجة - التمويل"
            ]

            for col in text_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()

            # تحويل التواريخ
            df["Follow up Last Date"] = pd.to_datetime(
                df["Follow up Last Date"],
                errors="coerce"
            ).dt.normalize()

            today = pd.Timestamp.today().normalize()

            # ============================
            # Sales Team
            # ============================
            df = df[
                df["Sales Team"] != "Sara || Op"
            ]

            # ============================
            # Payment
            # سيب السالب والصفر فقط
            # ============================
            df["Payment"] = (
                df["Payment"]
                .astype(str)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            
            df["Payment"] = pd.to_numeric(
                df["Payment"],
                errors="coerce"
            )

            df = df[
                df["Payment"] <= 0
            ]

            # ============================
            # Follow up Last Date
            # عدد الأيام من آخر متابعة
            # ============================
            df["عدد أيام الإهمال"] = (
                today - df["Follow up Last Date"]
            ).dt.days

            # حذف العمود لو موجود
            if "فرق عدد ايام من اخر متابعة" in df.columns:
                df.drop(columns=["فرق عدد ايام من اخر متابعة"], inplace=True)
            
            # مكان العمود بعد Follow up Last Date
            insert_position = df.columns.get_loc("Follow up Last Date") + 1
            
            # إضافة العمود
            df.insert(
                insert_position,
                "فرق عدد ايام من اخر متابعة",
                (today - df["Follow up Last Date"]).dt.days
            )

            df = df[
                df["عدد أيام الإهمال"] >= 3
            ]

            # ============================
            # Sub State
            # ============================
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

            df = df[
                df["Sub State"].isin(allowed_states)
            ]

            # ============================
            # حالة المعالجة
            # ============================
            df = df[
                (df["حالة المعالجة - التمويل"] == "لم يتم المعالجة") |
                (df["حالة المعالجة - التمويل"].isna())
            ]
 

            # ============================
            # تحميل الملف
            # ============================
            output = BytesIO()

            with pd.ExcelWriter(
                output,
                engine="openpyxl"
            ) as writer:
                df.to_excel(
                    writer,
                    index=False
                )

            output.seek(0)

            st.success(f"تم استخراج {len(df)} حساب")

            st.download_button(
                "📥 تحميل تقرير الإهمال",
                data=output,
                file_name="الاهمال.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    else:
        st.write("متابعة الإهمال")


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
            st.rerun()

        has_break = st.session_state.break_choice == "yes"

        break_start_minutes = None
        break_end_minutes = None

        if has_break:

            st.markdown("### 🕐 إعدادات البريك")

            col1, col2 = st.columns(2)

            with col1:
                break_start = st.time_input(
                    "البريك يبدأ الساعة",
                    value=time(12, 0)
                )

            with col2:
                break_duration = st.number_input(
                    "مدة البريك بالدقائق",
                    min_value=1,
                    value=30,
                    step=5
                )

            break_start_minutes = break_start.hour * 60 + break_start.minute
            break_end_minutes = break_start_minutes + int(break_duration)

            st.info(
                f"البريك من {break_start.strftime('%H:%M')} إلى "
                f"{(datetime.combine(date.today(), break_start) + timedelta(minutes=break_duration)).strftime('%H:%M')}"
            )

        else:
            st.info("تم اختيار: لا يوجد بريك — هيتحسب الوقت المهدر على طول اليوم من غير استثناء.")

        start_button = st.button("🚀 ابدأ التصنيف", type="primary")

        # =========================
        # المعالجة تحصل مرة واحدة وتتخزن في session_state
        # عشان زرار التحميل بعد كدة ميعملش re-run للتصنيف تاني
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

            # =========================
            # Prediction
            # =========================

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

            # =========================
            # تنظيف + ترتيب
            # =========================

            df["Created on"] = pd.to_datetime(df["Created on"], errors="coerce")

            df = df.drop_duplicates(subset=duplicate_columns, keep="first").reset_index(drop=True)

            df = df.sort_values(["Collector", "Created on"]).reset_index(drop=True)

            df["فرق التوقيت"] = (
                df.groupby("Collector")["Created on"]
                .diff()
                .dt.total_seconds()
                .div(60)
            )

            # =========================
            # الوقت المهدر (نسخة واحدة نظيفة)
            # =========================

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

            # ترتيب الأعمدة
            cols = list(df.columns)
            prob_index = cols.index("Probability (%)")
            for col in ["فرق التوقيت", "وقت مهدر"]:
                cols.remove(col)
            prob_index = cols.index("Probability (%)")
            cols.insert(prob_index + 1, "فرق التوقيت")
            cols.insert(prob_index + 2, "وقت مهدر")
            df = df[cols]

            # =========================
            # الملخصات
            # =========================

            collector_summary = (
                df.groupby("Collector", as_index=False)["وقت مهدر"]
                .sum()
                .sort_values("وقت مهدر", ascending=False)
                .reset_index(drop=True)
            )

            calls_over_30 = df[df["فرق التوقيت"] > 30].sort_values("فرق التوقيت", ascending=False)
            calls_under_1 = df[df["فرق التوقيت"] < 1].sort_values("فرق التوقيت", ascending=True)

            first_activity = (
                df.dropna(subset=["Created on"])
                .sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False)
                .first()[["Collector", "Created on", "التصنيف", "Probability (%)"]]
                .rename(columns={"Created on": "وقت أول إفادة"})
            )

            last_activity = (
                df.dropna(subset=["Created on"])
                .sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False)
                .last()[["Collector", "Created on", "التصنيف", "Probability (%)"]]
                .rename(columns={"Created on": "وقت آخر إفادة"})
            )

            final_state_summary = (
                df["Final State"].fillna("Blank").value_counts().reset_index()
            )
            final_state_summary.columns = ["Final State", "عدد الحالات"]

            # =========================
            # Pivot: أداء كل محصل (ناجحة / غير ناجحة / إجمالي المغطاة)
            # =========================

            pivot_summary = (
                df.groupby(["Collector", "التصنيف"])
                .size()
                .unstack(fill_value=0)
            )

            pivot_summary = pivot_summary.rename(
                columns={"1": "مكالمات ناجحة", "0": "مكالمات غير ناجحة"}
            )

            for needed_col in ["مكالمات ناجحة", "مكالمات غير ناجحة"]:
                if needed_col not in pivot_summary.columns:
                    pivot_summary[needed_col] = 0

            pivot_summary = pivot_summary[["مكالمات ناجحة", "مكالمات غير ناجحة"]]
            pivot_summary["إجمالي المكالمات المغطاة"] = pivot_summary.sum(axis=1)
            pivot_summary["نسبة النجاح %"] = (
                (pivot_summary["مكالمات ناجحة"] / pivot_summary["إجمالي المكالمات المغطاة"] * 100)
                .round(1)
            )
            pivot_summary = pivot_summary.reset_index().sort_values(
                "إجمالي المكالمات المغطاة", ascending=False
            ).reset_index(drop=True)

            # =========================
            # فقط لو فيه بريك: أول إفادة بعد البريك
            # =========================

            first_after_break = None

            if has_break:
                after_break = df[df["Created on"].notna()].copy()
                after_break["وقت بالدقائق"] = (
                    after_break["Created on"].dt.hour * 60 + after_break["Created on"].dt.minute
                )
                after_break = after_break[after_break["وقت بالدقائق"] >= break_end_minutes]

                first_after_break = (
                    after_break
                    .sort_values(["Collector", "Created on"])
                    .groupby("Collector", as_index=False)
                    .first()[["Collector", "Created on", "التصنيف", "Probability (%)"]]
                    .rename(columns={"Created on": "وقت أول إفادة بعد البريك"})
                )

                first_after_break["حالة النجاح"] = first_after_break["التصنيف"].apply(
                    lambda v: "ناجحة" if v == "1" else ("غير ناجحة" if v == "0" else v)
                )

            # =========================
            # كتابة ملف الإكسيل
            # =========================

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

                # =========================
                # تحويل شيت الـ Pivot لـ Excel Table حقيقي
                # (فيه Filter + Sort جاهزين على كل عمود)
                # =========================

                pivot_ws = workbook["Pivot - أداء المحصلين"]
                last_col_letter = pivot_ws.cell(row=1, column=pivot_ws.max_column).column_letter
                table_range = f"A1:{last_col_letter}{pivot_ws.max_row}"

                excel_table = Table(displayName="PivotAdaaAlMohaseleen", ref=table_range)
                excel_table.tableStyleInfo = TableStyleInfo(
                    name="TableStyleMedium2",
                    showRowStripes=True
                )
                pivot_ws.add_table(excel_table)

            output.seek(0)

            st.session_state.processed_output = output.getvalue()

            status.empty()
            progress_bar.empty()
            st.success("تم الانتهاء")

        # =========================
        # زرار التحميل — بيتحمل من الذاكرة من غير إعادة تصنيف
        # =========================

        if "processed_output" in st.session_state:
            st.download_button(
                "تحميل الملف",
                st.session_state.processed_output,
                file_name="activity.xlsx",
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
