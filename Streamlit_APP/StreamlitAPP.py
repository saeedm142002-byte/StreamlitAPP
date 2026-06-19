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

    st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        text-align: right;
        border-radius: 10px;
        height: 45px;
    }

    .active-btn {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    for page_name, icon in pages:

        is_active = st.session_state.page == page_name

        if is_active:
            st.markdown(
                f"""
                <style>
                div[data-testid="stButton"] button[kind="secondary"] {{
                    background-color:#ff4b4b;
                    color:white;
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

        if st.button(f"{icon} {page_name}", use_container_width=True):
            st.session_state.page = page_name
            st.rerun()


# ======================
# MAIN ROUTER
# ======================
page = st.session_state.page


# ======================
# PAGE 1 - الوعود القائمة
# ======================
if page == "الوعود القائمة":

    st.subheader("📊 الوعود القائمة")

    col1, col2 = st.columns(2)

    with col1:
        promises_file = st.file_uploader(
            "رفع الوعود القائمة",
            type=["xlsx", "xls"]
        )

    with col2:
        portfolio_file = st.file_uploader(
            "رفع المحفظة",
            type=["xlsx", "xls"]
        )

    if promises_file and portfolio_file:

        progress_bar = st.progress(0)
        status = st.empty()

        df = pd.read_excel(promises_file)
        portfolio = pd.read_excel(portfolio_file)

        df = df.drop_duplicates(subset=["رقم الهوية"])

        df["مبلغ المديونية"] = pd.to_numeric(df["مبلغ المديونية"], errors="coerce")
        df["السدادات الموثقة"] = pd.to_numeric(df["السدادات الموثقة"], errors="coerce")

        df["رقم الحساب"] = df["رقم الحساب"].astype(str).str.replace("^S", "", regex=True)
        df["رقم المديونية"] = df["رقم المديونية"].astype(str).str.replace("^S", "", regex=True)

        df = df[df["الحالة الرئيسية"] == "واعد بالسداد"]
        df = df[df["الفرع"] == "Madinah"]

        today = pd.Timestamp.today().normalize()

        df["تاريخ وعد السداد"] = pd.to_datetime(df["تاريخ وعد السداد"], errors="coerce")
        df = df[df["تاريخ وعد السداد"].dt.normalize() == today]

        df["آخر متابعة على العميل"] = pd.to_datetime(df["آخر متابعة على العميل"], errors="coerce")
        df = df[df["آخر متابعة على العميل"].dt.normalize() != today]

        portfolio["رقم الحساب"] = portfolio["رقم الحساب"].astype(str).str.replace("^S", "", regex=True)

        mapping = portfolio[["رقم الهوية", "رقم الحساب"]].drop_duplicates()

        df = df.merge(mapping, on="رقم الهوية", how="left", suffixes=("", "_portfolio"))
        df = df[df["رقم الحساب_portfolio"].notna()]
        df["رقم الحساب"] = df["رقم الحساب_portfolio"]
        df.drop(columns=["رقم الحساب_portfolio"], inplace=True)

        df = df[df["السدادات الموثقة"] == 0]

        progress_bar.progress(1.0)
        status.text("100%")

        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)

        output.seek(0)

        st.success("تم الانتهاء")
        st.download_button("تحميل الملف", output, file_name="output.xlsx")


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

        if "Feedback" not in df.columns:
            st.error("لا يوجد عمود Feedback")
        else:

            progress_bar = st.progress(0)
            status = st.empty()

            predictions = []
            total = len(df)

            for i, text in enumerate(df["Feedback"]):

                predictions.append(predict_text(text))

                progress = (i + 1) / total
                progress_bar.progress(progress)
                status.text(f"{int(progress*100)}% ({i+1}/{total})")

            df["Label"] = predictions

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
