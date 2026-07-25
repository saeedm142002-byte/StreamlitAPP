import streamlit as st
import pandas as pd
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from io import BytesIO

# ======================
# MODEL
# ======================
repo_id = "Saeed1233/saeedmohamed_AraBERT"

@st.cache_resource
def load_model():
    tokenizer = AutoTokenizer.from_pretrained(repo_id)
    model = AutoModelForSequenceClassification.from_pretrained(repo_id)
    model.eval()
    return tokenizer, model

tokenizer, model = load_model()


def predict_text(text):
    inputs = tokenizer(
        str(text),
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=256
    )

    with torch.no_grad():
        outputs = model(**inputs)

    pred = torch.argmax(outputs.logits, dim=1).item()
    return pred


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
            base["حالة المعالجة - التمويل"] == "لم يتم المعالجة"
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
                df["حالة المعالجة - التمويل"] == "لم يتم المعالجة"
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

        df = pd.read_excel(uploaded_file)

        if "الملاحظات" not in df.columns:
            st.error("لا يوجد عمود الملاحظات")
        else:

            progress_bar = st.progress(0)
            status = st.empty()

            predictions = []
            total = len(df)

            for i, text in enumerate(df["الملاحظات"]):

                predictions.append(predict_text(text))

                progress = (i + 1) / total
                progress_bar.progress(progress)
                status.text(f"{int(progress*100)}% ({i+1}/{total})")

            df["المكالمات الناجحة"] = predictions

            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False)

            output.seek(0)

            st.success("تم الانتهاء")
            st.download_button("تحميل الملف", output, file_name="activity.xlsx")


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
