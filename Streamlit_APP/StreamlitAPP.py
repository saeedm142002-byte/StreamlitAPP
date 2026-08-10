import streamlit as st
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from io import BytesIO
import torch
import torch.nn.functional as F
from datetime import datetime, date, time, timedelta
import win32com.client as win32
import tempfile
import os
import shutil


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
elif page == "النشاط":

    st.subheader("⚡ النشاط")

    uploaded_file = st.file_uploader(
        "رفع ملف واحد فقط",
        type=["xlsx", "xls"],
        accept_multiple_files=False
    )

    if uploaded_file:

        # =========================
        # إعدادات البريك
        # =========================

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

        # حساب نهاية البريك
        break_start_minutes = (
            break_start.hour * 60 +
            break_start.minute
        )

        break_end_minutes = (
            break_start_minutes +
            int(break_duration)
        )

        st.info(
            f"البريك من {break_start.strftime('%H:%M')} "
            f"إلى "
            f"{(datetime.combine(date.today(), break_start) + timedelta(minutes=break_duration)).strftime('%H:%M')}"
        )

        # =========================
        # قراءة الملف
        # =========================

        df = pd.read_excel(uploaded_file)
        # حذف أول صف من الملف
        df = df.iloc[1:].reset_index(drop=True)

        # الأعمدة المطلوبة
        required_columns = [
            "Notes",
            "Created on",
            "Collector"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:

            st.error(
                f"الأعمدة التالية غير موجودة في الملف: "
                f"{', '.join(missing_columns)}"
            )

        else:

            progress_bar = st.progress(0)
            status = st.empty()

            predictions = []
            probabilities = []

            total = len(df)

            # =========================
            # Prediction
            # =========================

            for i, text in enumerate(df["Notes"]):

                label, prob = predict_text(text)

                predictions.append(label)
                probabilities.append(prob)

                progress = (i + 1) / total

                progress_bar.progress(progress)

                status.text(
                    f"{int(progress * 100)}% "
                    f"({i + 1}/{total})"
                )

            # =========================
            # إضافة التصنيف والاحتمالية
            # =========================

            notes_index = df.columns.get_loc("Notes")

            df.insert(
                notes_index + 1,
                "التصنيف",
                predictions
            )

            df.insert(
                notes_index + 2,
                "Probability (%)",
                probabilities
            )

            # =========================
            # حساب الوقت المهدر
            # =========================

            df["Created on"] = pd.to_datetime(
                df["Created on"],
                errors="coerce"
            )

            def calculate_wasted_time(row):

                call_time = row["Created on"]
                classification = row["التصنيف"]

                # لو الوقت غير موجود
                if pd.isna(call_time):
                    return 0

                # تحويل وقت المكالمة إلى دقائق من بداية اليوم
                call_minutes = (
                    call_time.hour * 60 +
                    call_time.minute
                )

                # =========================
                # داخل البريك
                # =========================

                if (
                    break_start_minutes
                    <= call_minutes
                    < break_end_minutes
                ):
                    return 0

                # =========================
                # خارج البريك
                # =========================

                # فرق الوقت بين المكالمات
                # سيتم حسابه لاحقاً
                return 0

            # =========================
            # فرق الوقت بين المكالمات
            # لكل محصل
            # =========================

            df = df.sort_values(
                ["Collector", "Created on"]
            ).reset_index(drop=True)

            df["فرق التوقيت"] = (
                df.groupby("Collector")["Created on"]
                .diff()
                .dt.total_seconds()
                .div(60)
            )

            # =========================
            # حساب الوقت المهدر
            # =========================

            def calculate_wasted(row):

                call_time = row["Created on"]
                classification = row["التصنيف"]
                time_diff = row["فرق التوقيت"]

                # أول مكالمة للمحصل
                if pd.isna(time_diff):
                    return 0

                # لو فرق الوقت بالسالب لأي سبب
                if time_diff < 0:
                    return 0

                # وقت المكالمة بالدقائق
                call_minutes = (
                    call_time.hour * 60 +
                    call_time.minute
                )

                # =========================
                # داخل البريك
                # =========================

                if (
                    break_start_minutes
                    <= call_minutes
                    < break_end_minutes
                ):
                    return 0

                # =========================
                # خارج البريك
                # =========================

                if str(classification) == "1":
                    wasted = time_diff - 20

                elif str(classification) == "0":
                    wasted = time_diff - 5

                else:
                    wasted = 0

                # لا نسمح بقيمة سالبة
                return max(wasted, 0)

            df["وقت مهدر"] = df.apply(
                calculate_wasted,
                axis=1
            )

            # =========================
            # إزالة الـ Duplicates
            # =========================
            
            duplicate_columns = [
                "Collector",
                "ID Number",
                "Notes"
            ]
            
            missing_duplicate_columns = [
                col for col in duplicate_columns
                if col not in df.columns
            ]
            
            if missing_duplicate_columns:
                st.error(
                    f"الأعمدة التالية غير موجودة: "
                    f"{', '.join(missing_duplicate_columns)}"
                )
                st.stop()
            
            df = df.drop_duplicates(
                subset=duplicate_columns,
                keep="first"
            ).reset_index(drop=True)
            
            
            # =========================
            # تحويل Created on إلى datetime
            # =========================
            
            df["Created on"] = pd.to_datetime(
                df["Created on"],
                errors="coerce"
            )
            
            
            # =========================
            # ترتيب حسب المحصل والوقت
            # =========================
            
            df = df.sort_values(
                ["Collector", "Created on"]
            ).reset_index(drop=True)
            
            
            # =========================
            # فرق التوقيت
            # =========================
            
            df["فرق التوقيت"] = (
                df.groupby("Collector")["Created on"]
                .diff()
                .dt.total_seconds()
                .div(60)
            )
            
            
            # =========================
            # حساب الوقت المهدر
            # =========================
            
            def calculate_wasted(row):
            
                call_time = row["Created on"]
                classification = row["التصنيف"]
                time_diff = row["فرق التوقيت"]
            
                if pd.isna(time_diff) or pd.isna(call_time):
                    return 0
            
                if time_diff < 0:
                    return 0
            
                call_minutes = (
                    call_time.hour * 60 +
                    call_time.minute
                )
            
                # داخل البريك
                if (
                    break_start_minutes
                    <= call_minutes
                    < break_end_minutes
                ):
                    return 0
            
                # خارج البريك
                if str(classification) == "1":
                    wasted = time_diff - 20
            
                elif str(classification) == "0":
                    wasted = time_diff - 5
            
                else:
                    wasted = 0
            
                return max(wasted, 0)
            
            
            df["وقت مهدر"] = df.apply(
                calculate_wasted,
                axis=1
            )
            
            
            # =====================================================
            # ترتيب الأعمدة
            # Probability -> فرق التوقيت -> وقت مهدر
            # =====================================================
            
            cols = list(df.columns)
            
            prob_index = cols.index("Probability (%)")
            
            for col in ["فرق التوقيت", "وقت مهدر"]:
                cols.remove(col)
            
            prob_index = cols.index("Probability (%)")
            
            cols.insert(prob_index + 1, "فرق التوقيت")
            cols.insert(prob_index + 2, "وقت مهدر")
            
            df = df[cols]
            
            
            # =====================================================
            # 1 - إجمالي الوقت المهدر لكل محصل
            # =====================================================
            
            collector_summary = (
                df.groupby("Collector", as_index=False)["وقت مهدر"]
                .sum()
                .sort_values(
                    "وقت مهدر",
                    ascending=False
                )
                .reset_index(drop=True)
            )
            
            
            # =====================================================
            # 2 - المكالمات أعلى من 30 دقيقة
            # =====================================================
            
            calls_over_30 = df[
                df["فرق التوقيت"] > 30
            ].copy()
            
            calls_over_30 = calls_over_30.sort_values(
                "فرق التوقيت",
                ascending=False
            )
            
            
            # =====================================================
            # 3 - المكالمات أقل من دقيقة
            # =====================================================
            
            calls_under_1 = df[
                df["فرق التوقيت"] < 1
            ].copy()
            
            calls_under_1 = calls_under_1.sort_values(
                "فرق التوقيت",
                ascending=True
            )
            
            
            # =====================================================
            # 4 - أول إفادة لكل محصل
            # =====================================================
            
            first_activity = (
                df.dropna(subset=["Created on"])
                .sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False)
                .first()
            )
            
            first_activity = first_activity[
                [
                    "Collector",
                    "Created on",
                    "التصنيف",
                    "Probability (%)"
                ]
            ].rename(
                columns={
                    "Created on": "وقت أول إفادة"
                }
            )
            
            
            # =====================================================
            # 5 - آخر إفادة لكل محصل
            # =====================================================
            
            last_activity = (
                df.dropna(subset=["Created on"])
                .sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False)
                .last()
            )
            
            last_activity = last_activity[
                [
                    "Collector",
                    "Created on",
                    "التصنيف",
                    "Probability (%)"
                ]
            ].rename(
                columns={
                    "Created on": "وقت آخر إفادة"
                }
            )
            
            
            # =====================================================
            # 6 - أول إفادة بعد البريك
            # =====================================================
            
            after_break = df[
                df["Created on"].notna()
            ].copy()
            
            after_break["وقت بالدقائق"] = (
                after_break["Created on"].dt.hour * 60
                + after_break["Created on"].dt.minute
            )
            
            after_break = after_break[
                after_break["وقت بالدقائق"] >= break_end_minutes
            ]
            
            first_after_break = (
                after_break
                .sort_values(["Collector", "Created on"])
                .groupby("Collector", as_index=False)
                .first()
            )
            
            first_after_break = first_after_break[
                [
                    "Collector",
                    "Created on",
                    "التصنيف",
                    "Probability (%)"
                ]
            ].rename(
                columns={
                    "Created on": "وقت أول إفادة بعد البريك"
                }
            )
            
            
            # =====================================================
            # تحويل التصنيف إلى حالة نجاح
            # =====================================================
            
            def success_status(value):
            
                if str(value) == "1":
                    return "ناجحة"
            
                elif str(value) == "0":
                    return "غير ناجحة"
            
                return value
            
            
            first_after_break["حالة النجاح"] = (
                first_after_break["التصنيف"]
                .apply(success_status)
            )
            
            
            # =====================================================
            # 7 - Final State
            # =====================================================
            
            if "Final State" not in df.columns:
            
                st.error("لا يوجد عمود Final State في الملف")
                st.stop()
            
            final_state_summary = (
                df["Final State"]
                .fillna("Blank")
                .value_counts()
                .reset_index()
            )
            
            final_state_summary.columns = [
                "Final State",
                "عدد الحالات"
            ]
            
            
                      # =====================================================
            # Excel - إنشاء Pivot Tables حقيقية
            # =====================================================
            
            # حفظ ملف النشاط أولاً في ملف مؤقت
            temp_input = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".xlsx"
            )
            
            temp_input.close()
            
            input_path = temp_input.name
            
            
            # =====================================================
            # إنشاء ملف Excel الأساسي
            # =====================================================
            
            with pd.ExcelWriter(
                input_path,
                engine="openpyxl"
            ) as writer:
            
                # البيانات الأصلية
                df.to_excel(
                    writer,
                    index=False,
                    sheet_name="النشاط"
                )
            
            
            # =====================================================
            # فتح Excel عن طريق Windows
            # =====================================================
            
            excel = win32.DispatchEx("Excel.Application")
            
            excel.Visible = False
            excel.DisplayAlerts = False
            
            wb = None
            
            try:
            
                wb = excel.Workbooks.Open(
                    os.path.abspath(input_path)
                )
            
                # =================================================
                # Source Sheet
                # =================================================
            
                ws_source = wb.Worksheets("النشاط")
            
                last_row = ws_source.Cells(
                    ws_source.Rows.Count,
                    1
                ).End(-4162).Row       # xlUp
            
                last_col = ws_source.Cells(
                    1,
                    ws_source.Columns.Count
                ).End(-4159).Column    # xlToLeft
            
                source_range = ws_source.Range(
                    ws_source.Cells(1, 1),
                    ws_source.Cells(last_row, last_col)
                )
            
            
                # =================================================
                # Helper لإنشاء Pivot Sheet
                # =================================================
            
                def create_pivot_sheet(
                    sheet_name,
                    pivot_name,
                    row_fields=None,
                    column_fields=None,
                    data_fields=None,
                    filters=None
                ):
            
                    row_fields = row_fields or []
                    column_fields = column_fields or []
                    data_fields = data_fields or []
                    filters = filters or []
            
            
                    # ---------------------------------------------
                    # حذف الشيت لو موجود
                    # ---------------------------------------------
            
                    try:
                        old_sheet = wb.Worksheets(sheet_name)
                        old_sheet.Delete()
                    except:
                        pass
            
            
                    # ---------------------------------------------
                    # إنشاء Sheet
                    # ---------------------------------------------
            
                    ws = wb.Worksheets.Add(
                        After=wb.Worksheets(
                            wb.Worksheets.Count
                        )
                    )
            
                    ws.Name = sheet_name
            
            
                    # ---------------------------------------------
                    # عنوان
                    # ---------------------------------------------
            
                    ws.Range("A1").Value = sheet_name
                    ws.Range("A1").Font.Bold = True
                    ws.Range("A1").Font.Size = 16
            
            
                    # ---------------------------------------------
                    # Pivot Cache
                    # ---------------------------------------------
            
                    cache = wb.PivotCaches().Create(
                        SourceType=1,
                        SourceData=source_range
                    )
            
            
                    # ---------------------------------------------
                    # Pivot Table
                    # ---------------------------------------------
            
                    pivot = cache.CreatePivotTable(
                        TableDestination=ws.Range("A3"),
                        TableName=pivot_name
                    )
            
            
                    # ---------------------------------------------
                    # Rows
                    # ---------------------------------------------
            
                    position = 1
            
                    for field_name in row_fields:
            
                        field = pivot.PivotFields(
                            field_name
                        )
            
                        field.Orientation = 1   # xlRowField
                        field.Position = position
            
                        position += 1
            
            
                    # ---------------------------------------------
                    # Columns
                    # ---------------------------------------------
            
                    position = 1
            
                    for field_name in column_fields:
            
                        field = pivot.PivotFields(
                            field_name
                        )
            
                        field.Orientation = 2   # xlColumnField
                        field.Position = position
            
                        position += 1
            
            
                    # ---------------------------------------------
                    # Filters
                    # ---------------------------------------------
            
                    position = 1
            
                    for field_name in filters:
            
                        field = pivot.PivotFields(
                            field_name
                        )
            
                        field.Orientation = 3   # xlPageField
                        field.Position = position
            
                        position += 1
            
            
                    # ---------------------------------------------
                    # Values
                    # ---------------------------------------------
            
                    for field_name, function, caption in data_fields:
            
                        field = pivot.PivotFields(
                            field_name
                        )
            
                        pivot.AddDataField(
                            field,
                            caption,
                            function
                        )
            
            
                    # ---------------------------------------------
                    # تنسيق
                    # ---------------------------------------------
            
                    ws.Columns.AutoFit()
            
                    ws.Range("A1").Font.Bold = True
            
                    return pivot
            
            
                # =================================================
                # 1 - إجمالي الوقت المهدر لكل محصل
                # =================================================
            
                pivot1 = create_pivot_sheet(
                    sheet_name="إجمالي الوقت المهدر",
                    pivot_name="Pivot_Total_Wasted_Time",
            
                    row_fields=[
                        "Collector"
                    ],
            
                    data_fields=[
                        (
                            "وقت مهدر",
                            -4157,  # xlSum
                            "إجمالي الوقت المهدر"
                        )
                    ]
                )
            
            
                # =================================================
                # ترتيب Pivot 1 تنازلياً
                # =================================================
            
                try:
            
                    pivot1.PivotFields(
                        "Collector"
                    ).AutoSort(
                        2,  # xlDescending
                        "إجمالي الوقت المهدر"
                    )
            
                except:
                    pass
            
            
                # =================================================
                # 2 - المكالمات أعلى من 30 دقيقة
                # =================================================
            
                pivot2 = create_pivot_sheet(
            
                    sheet_name="مكالمات +30 دقيقة",
                    pivot_name="Pivot_Calls_Over_30",
            
                    row_fields=[
                        "Collector",
                        "Created on",
                        "ID Number",
                        "Notes"
                    ],
            
                    data_fields=[
                        (
                            "فرق التوقيت",
                            -4106,  # xlMax
                            "فرق التوقيت"
                        )
                    ]
                )
            
            
                # =================================================
                # 3 - المكالمات أقل من دقيقة
                # =================================================
            
                pivot3 = create_pivot_sheet(
            
                    sheet_name="مكالمات أقل من دقيقة",
                    pivot_name="Pivot_Calls_Under_1",
            
                    row_fields=[
                        "Collector",
                        "Created on",
                        "ID Number",
                        "Notes"
                    ],
            
                    data_fields=[
                        (
                            "فرق التوقيت",
                            -4106,  # xlMax
                            "فرق التوقيت"
                        )
                    ]
                )
            
            
                # =================================================
                # 4 - أول إفادة لكل محصل
                # =================================================
            
                pivot4 = create_pivot_sheet(
            
                    sheet_name="أول إفادة",
                    pivot_name="Pivot_First_Activity",
            
                    row_fields=[
                        "Collector"
                    ],
            
                    data_fields=[
                        (
                            "Created on",
                            -4139,  # xlMin
                            "وقت أول إفادة"
                        )
                    ]
                )
            
            
                # =================================================
                # 5 - آخر إفادة لكل محصل
                # =================================================
            
                pivot5 = create_pivot_sheet(
            
                    sheet_name="آخر إفادة",
                    pivot_name="Pivot_Last_Activity",
            
                    row_fields=[
                        "Collector"
                    ],
            
                    data_fields=[
                        (
                            "Created on",
                            -4106,  # xlMax
                            "وقت آخر إفادة"
                        )
                    ]
                )
            
            
                # =================================================
                # 6 - أول إفادة بعد البريك
                # =================================================
            
                # هننشئ Sheet مساعد للبيانات بعد البريك
                try:
            
                    ws_after_break = wb.Worksheets(
                        "Data After Break"
                    )
            
                    ws_after_break.Delete()
            
                except:
                    pass
            
            
                ws_after_break = wb.Worksheets.Add(
                    After=wb.Worksheets(
                        wb.Worksheets.Count
                    )
                )
            
                ws_after_break.Name = "Data After Break"
            
            
                # نكتب بيانات أول إفادة بعد البريك
                first_after_break.to_excel(
                    excel_writer := pd.ExcelWriter(
                        input_path,
                        engine="openpyxl"
                    ),
                    index=False,
                    sheet_name="Data After Break"
                )
            
                excel_writer.close()
            
            
                # ================================================
                # إعادة فتح الملف بعد إضافة البيانات
                # ================================================
            
                wb.Close(
                    SaveChanges=True
                )
            
                excel.Quit()
            
            
                # فتحه مرة ثانية
                excel = win32.DispatchEx(
                    "Excel.Application"
                )
            
                excel.Visible = False
                excel.DisplayAlerts = False
            
                wb = excel.Workbooks.Open(
                    os.path.abspath(input_path)
                )
            
            
                # =================================================
                # مصدر أول إفادة بعد البريك
                # =================================================
            
                ws_break = wb.Worksheets(
                    "Data After Break"
                )
            
                last_row_break = ws_break.Cells(
                    ws_break.Rows.Count,
                    1
                ).End(-4162).Row
            
                last_col_break = ws_break.Cells(
                    1,
                    ws_break.Columns.Count
                ).End(-4159).Column
            
                source_break = ws_break.Range(
                    ws_break.Cells(1, 1),
                    ws_break.Cells(
                        last_row_break,
                        last_col_break
                    )
                )
            
            
                # =================================================
                # Pivot أول إفادة بعد البريك
                # =================================================
            
                try:
                    wb.Worksheets(
                        "أول إفادة بعد البريك"
                    ).Delete()
                except:
                    pass
            
            
                ws6 = wb.Worksheets.Add(
                    After=wb.Worksheets(
                        wb.Worksheets.Count
                    )
                )
            
                ws6.Name = "أول إفادة بعد البريك"
            
                cache6 = wb.PivotCaches().Create(
                    SourceType=1,
                    SourceData=source_break
                )
            
                pivot6 = cache6.CreatePivotTable(
                    TableDestination=ws6.Range("A3"),
                    TableName="Pivot_First_After_Break"
                )
            
            
                # Collector
                collector_field = pivot6.PivotFields(
                    "Collector"
                )
            
                collector_field.Orientation = 1
                collector_field.Position = 1
            
            
                # أول Created on
                created_field = pivot6.PivotFields(
                    "Created on"
                )
            
                pivot6.AddDataField(
                    created_field,
                    "وقت أول إفادة بعد البريك",
                    -4139   # xlMin
                )
            
            
                ws6.Range("A1").Value = (
                    "أول إفادة بعد البريك لكل محصل"
                )
            
                ws6.Range("A1").Font.Bold = True
                ws6.Range("A1").Font.Size = 16
            
                ws6.Columns.AutoFit()
            
            
                # =================================================
                # 7 - Final State
                # =================================================
            
                pivot7 = create_pivot_sheet(
            
                    sheet_name="Final State",
                    pivot_name="Pivot_Final_State",
            
                    row_fields=[
                        "Final State"
                    ],
            
                    data_fields=[
                        (
                            "Final State",
                            -4112,  # xlCount
                            "عدد الحالات"
                        )
                    ]
                )
            
            
                # =================================================
                # حذف الـ Sheet المساعد
                # =================================================
            
                try:
                    wb.Worksheets(
                        "Data After Break"
                    ).Delete()
                except:
                    pass
            
            
                # =================================================
                # حفظ
                # =================================================
            
                wb.Save()
            
            finally:
            
                if wb is not None:
            
                    try:
                        wb.Close(
                            SaveChanges=True
                        )
                    except:
                        pass
            
                try:
                    excel.Quit()
                except:
                    pass
            
            
            # =====================================================
            # قراءة الملف النهائي
            # =====================================================
            
            with open(
                input_path,
                "rb"
            ) as f:
            
                output = f.read()
            
            
            # =====================================================
            # حذف الملف المؤقت
            # =====================================================
            
            try:
                os.unlink(input_path)
            except:
                pass
            
            
            # =====================================================
            # Download
            # =====================================================
            
            st.success(
                "تم إنشاء ملف Excel بكل الـ Pivot Tables بنجاح ✅"
            )
            
            st.download_button(
                "تحميل الملف",
                output,
                file_name="activity.xlsx",
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "spreadsheetml.sheet"
                )
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
