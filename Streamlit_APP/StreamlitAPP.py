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
    st.session_state.page = "الوعود القائمة"

if "sub_page" not in st.session_state:
    st.session_state.sub_page = "اهمال"


# ======================
# SIDEBAR
# ======================
pages = [
    ("الوعود القائمة", "📊"),
    ("الوعود المكسورة", "🚨"),
    ("الاهمال", "⚠️"),
    ("التغطية", "🌐"),
    ("الانتاجية", "📈"),
    ("النشاط", "⚡"),
    ("اخطاء الحالات", "❌"),
    ("الاوتودايلر", "📞"),
    ("مطابقة السدادات", "💰"),
    ("وعود لا يوجد لها تاريخ الوعد", "📅"),
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
if page == "الوعود القائمة":

    import pandas as pd
    from io import BytesIO

    st.subheader("📊 الوعود القائمة")

    portfolio_file = st.file_uploader(
        "رفع ملف المحفظة",
        type=["xlsx", "xls"]
    )

    if portfolio_file:

        progress_bar = st.progress(0)
        status = st.empty()

        # =========================
        # قراءة الملف
        # =========================
        df = pd.read_excel(portfolio_file)

        st.write("عدد الصفوف بعد القراءة:", len(df))
        st.write("أسماء الأعمدة:")
        st.write(df.columns.tolist())

        progress_bar.progress(10)

        # =========================
        # حذف أول صف
        # =========================
        df = df.iloc[1:].reset_index(drop=True)

        st.write("بعد حذف أول صف:", len(df))

        progress_bar.progress(20)

        # =========================
        # حذف Sara || Op
        # =========================
        df["Sales Team"] = df["Sales Team"].astype(str).str.strip()

        df = df[df["Sales Team"] != "Sara || Op"]

        st.write("بعد Sales Team:", len(df))

        progress_bar.progress(35)

        # =========================
        # تاريخ اليوم
        # =========================
        today = pd.Timestamp.today().normalize()

        # =========================
        # Follow up Due Date
        # =========================
        df["Follow up Due Date"] = pd.to_datetime(
            df["Follow up Due Date"],
            errors="coerce"
        ).dt.normalize()

        st.write("قيم Follow up Due Date:")
        st.write(df["Follow up Due Date"].head(10))

        df = df[df["Follow up Due Date"] == today]

        st.write("بعد Follow up Due Date:", len(df))

        progress_bar.progress(55)

        # =========================
        # Follow up Last Date
        # =========================
        df["Follow up Last Date"] = pd.to_datetime(
            df["Follow up Last Date"],
            errors="coerce"
        ).dt.normalize()

        df = df[df["Follow up Last Date"].notna()]
        df = df[df["Follow up Last Date"] != today]

        st.write("بعد Follow up Last Date:", len(df))

        progress_bar.progress(75)

        # =========================
        # Final State
        # =========================
        df["Final State"] = df["Final State"].astype(str).str.strip()

        st.write("القيم الموجودة في Final State:")
        st.write(df["Final State"].unique())

        df = df[
            df["Final State"] == "واعد بالسداد  II تم التواصل مع العميل"
        ]

        st.write("بعد Final State:", len(df))

        progress_bar.progress(90)

        # =========================
        # حالة المعالجة
        # =========================
        df["حالة المعالجة - التمويل"] = (
            df["حالة المعالجة - التمويل"]
            .astype(str)
            .str.strip()
        )

        st.write("القيم الموجودة في حالة المعالجة:")
        st.write(df["حالة المعالجة - التمويل"].unique())

        df = df[
            df["حالة المعالجة - التمويل"] == "غير معالج"
        ]

        st.write("بعد حالة المعالجة:", len(df))

        progress_bar.progress(100)
        status.text("100%")

        # =========================
        # تصدير الملف
        # =========================
        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        output.seek(0)

        st.success("تم تجهيز الملف")

        st.download_button(
            "📥 تحميل الملف",
            output,
            file_name="Portfolio_Filtered.xlsx",
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
        st.write("تقارير الإهمال")

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
elif page == "اخطاء الحالات":
    st.subheader("❌ اخطاء الحالات")

elif page == "الاوتودايلر":
    st.subheader("📞 الاوتودايلر")

elif page == "مطابقة السدادات":
    st.subheader("💰 مطابقة السدادات")

elif page == "وعود لا يوجد لها تاريخ الوعد":
    st.subheader("📅 وعود بدون تاريخ")
