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
    ("التوزيع", "📈"),
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
            base["حالة المعالجة - التمويل"] == "غير معالج"
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
        
        # حذف العمود لو موجود
        if "عدد ايام ترحيل الوعد" in broken.columns:
            broken.drop(columns=["عدد ايام ترحيل الوعد"], inplace=True)
        
        # مكان العمود بعد Follow up Last Date
        insert_position = broken.columns.get_loc("Follow up Last Date") + 1
        
        # إضافة العمود بعد Follow up Last Date مباشرة
        broken.insert(
            insert_position,
            "عدد ايام ترحيل الوعد",
            (today - broken["Follow up Due Date"]).dt.days
        )
        
        # الاحتفاظ فقط بالوعود المكسورة (المتأخرة)
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
elif page == "التوزيع":

    st.subheader("📦 توزيع المحافظ")
    uploaded_file = st.file_uploader(
        "ارفع ملف Excel",
        type=["xlsx"]
    )
    
    if uploaded_file is None:
        st.warning("برجاء رفع الملف أولاً.")
        st.stop()
    
    df = pd.read_excel(uploaded_file)
    
    base = df.copy()

    # حذف فريق Sara || Op
    base = base[
        base["Sales Team"] != "Sara || Op"
    ]

    # غير معالج فقط
    base = base[
        base["حالة المعالجة - التمويل"] == "غير معالج"
    ]

    if base.empty:
        st.warning("لا توجد بيانات بعد الفلترة.")
        st.stop()

    # =========================
    # أسماء المحصلين
    # =========================

    collectors = sorted(
        base["Collector"]
        .dropna()
        .unique()
        .tolist()
    )

    st.markdown("### المحصلين الحاليين")

    st.dataframe(
        pd.DataFrame(
            {
                "Collector": collectors
            }
        ),
        use_container_width=True
    )

    # =========================
    # إحصائيات كل محصل
    # =========================

    collector_stats = (
        base
        .groupby("Collector")
        .agg(
            Accounts=(
                "Account Number",
                "nunique"
            ),
            Customers=(
                "Debitor",
                "nunique"
            ),
            Debt=(
                "Net Amount",
                "sum"
            )
        )
        .reset_index()
    )

    collector_stats["Debt"] = (
        collector_stats["Debt"]
        .round(2)
    )

    st.markdown("## إحصائيات المحافظ الحالية")

    st.dataframe(
        collector_stats,
        use_container_width=True,
        hide_index=True
    )

    # =========================
    # الأزرار
    # =========================





# ==================================================
# توزيع محفظة محصل مستقيل
# ==================================================

st.markdown("## نوع العملية")

operation = st.radio(
    "اختر العملية",
    [
        "1️⃣ توزيع محفظة محصل مستقيل",
        "2️⃣ إسناد محفظة لموظف جديد",
        "3️⃣ إسناد محفظة من موظف مستقيل لموظف جديد"
    ],
    key="distribution_operation"
)

# ==================================================
# توزيع محفظة محصل مستقيل
# ==================================================

if operation == "1️⃣ توزيع محفظة محصل مستقيل":

    departed_collectors = st.multiselect(
        "اختر المحصلين المستقيلين",
        collectors
    )

    run_distribution = st.button(
        "🚀 تنفيذ التوزيع",
        type="primary"
    )

    if run_distribution:

        if len(departed_collectors) == 0:
            st.warning("اختر محصل واحد على الأقل.")
            st.stop()

        departed_df = base[
            base["Collector"].isin(departed_collectors)
        ].copy()

        remaining_df = base[
            ~base["Collector"].isin(departed_collectors)
        ].copy()

        # من هنا يبدأ باقي كود التوزيع
        # من هنا يبدأ باقي كود التوزيعمن هنا يبدأ باقي كود التوزيع

    # =========================
    # اختيار المستقيلين
    # =========================

    if operation:

        departed_collectors = st.multiselect(
            "اختر المحصلين المستقيلين",
            collectors
        )
        
        run_distribution = st.button(
            "🚀 تنفيذ التوزيع",
            use_container_width=True,
            type="primary"
        )
        
        if run_distribution:
        
            if len(departed_collectors) == 0:
        
                st.warning("برجاء اختيار محصل واحد على الأقل.")
                st.stop()
        
            st.success(
                f"عدد المحصلين المختارين: {len(departed_collectors)}"
            )
        
            st.write(departed_collectors)
    
        # ============================================
        # من هنا يبدأ كود التوزيع
        # ============================================
    
        departed_df = base[
            base["Collector"].isin(departed_collectors)
        ].copy()
    
        remaining_df = base[
            ~base["Collector"].isin(departed_collectors)
        ].copy()

    # باقي الكود...

        # =========================
        # المحافظ
        # =========================

        departed_df = base[
            base["Collector"]
            .isin(departed_collectors)
        ].copy()
        st.write("عدد صفوف departed_df:", len(departed_df))
        st.write("المحصلين المختارين:", departed_collectors)
        st.write("أول 5 صفوف:")
        st.dataframe(departed_df.head())

        remaining_df = base[
            ~base["Collector"]
            .isin(departed_collectors)
        ].copy()

        st.markdown("## بيانات المحفظة")

        c1, c2 = st.columns(2)

        with c1:

            st.metric(
                "عدد صفوف المستقيلين",
                len(departed_df)
            )

        with c2:

            st.metric(
                "عدد صفوف المحصلين الباقيين",
                len(remaining_df)
            )

                # ============================================
        # تجميع العملاء المراد توزيعهم
        # ============================================
        customers = []

       

        for debitor, grp in departed_df.groupby("Debitor"):

            customers.append(
                {
                    "Debitor": debitor,

                    "Debt": grp["Net Amount"].sum(),

                    "Accounts": grp["Account Number"].nunique(),

                    "Rows": grp.index.tolist()
                }
            )


        customers_df = pd.DataFrame(customers)
    
        st.write("عدد العملاء:", len(customers_df))
        st.write(customers_df.columns.tolist())
        st.dataframe(customers_df.head())

        # ترتيب من أكبر مديونية لأصغر
        customers_df = customers_df.sort_values(
            by="Debt",
            ascending=False
        ).reset_index(drop=True)

        st.markdown("### العملاء المطلوب توزيعهم")

        st.dataframe(
            customers_df[
                [
                    "Debitor",
                    "Accounts",
                    "Debt"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        # ============================================
        # إحصائيات المحصلين المتبقين
        # ============================================

        remaining_stats = (
            remaining_df
            .groupby("Collector")
            .agg(
                Accounts=(
                    "Account Number",
                    "nunique"
                ),
                Customers=(
                    "Debitor",
                    "nunique"
                ),
                Debt=(
                    "Net Amount",
                    "sum"
                )
            )
            .reset_index()
        )

        remaining_stats["Debt"] = (
            remaining_stats["Debt"]
            .round(2)
        )

        st.markdown("### المحافظ قبل التوزيع")

        st.dataframe(
            remaining_stats,
            use_container_width=True,
            hide_index=True
        )

        # ============================================
        # إنشاء قاموس الإحصائيات
        # ============================================

        stats = {}

        for _, row in remaining_stats.iterrows():

            stats[row["Collector"]] = {

                "Debt": float(row["Debt"]),

                "Customers": int(row["Customers"]),

                "Accounts": int(row["Accounts"])

            }

        # ============================================
        # إجماليات بعد التوزيع
        # ============================================

        total_debt = (
            remaining_df["Net Amount"].sum()
            +
            departed_df["Net Amount"].sum()
        )

        total_customers = (
            remaining_df["Debitor"].nunique()
            +
            departed_df["Debitor"].nunique()
        )

        total_accounts = (
            remaining_df["Account Number"].nunique()
            +
            departed_df["Account Number"].nunique()
        )

        collectors_count = len(stats)

        target_debt = total_debt / collectors_count

        target_customers = (
            total_customers / collectors_count
        )

        target_accounts = (
            total_accounts / collectors_count
        )

        st.markdown("### الهدف لكل محصل")

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Target Debt",
                f"{target_debt:,.0f}"
            )

        with c2:

            st.metric(
                "Target Customers",
                round(target_customers, 1)
            )

        with c3:

            st.metric(
                "Target Accounts",
                round(target_accounts, 1)
            )

                # ============================================
        # توزيع العملاء
        # ============================================

        assignments = {}

        progress = st.progress(0)

        total_customers_to_assign = len(customers_df)

        for i, customer in customers_df.iterrows():

            customer_name = customer["Debitor"]

            customer_debt = float(customer["Debt"])

            customer_accounts = int(customer["Accounts"])

            best_collector = None

            best_score = None

            # ============================================
            # اختيار أفضل محصل
            # ============================================

            for collector in stats.keys():

                current = stats[collector]

                new_debt = current["Debt"] + customer_debt

                new_customers = current["Customers"] + 1

                new_accounts = current["Accounts"] + customer_accounts

                debt_diff = abs(
                    new_debt - target_debt
                )

                customer_diff = abs(
                    new_customers - target_customers
                )

                account_diff = abs(
                    new_accounts - target_accounts
                )

                score = (

                    debt_diff

                    +

                    (customer_diff * 5000)

                    +

                    (account_diff * 3000)

                )

                if (

                    best_score is None

                    or

                    score < best_score

                ):

                    best_score = score

                    best_collector = collector

            # ============================================
            # حفظ التوزيع
            # ============================================

            assignments[
                customer_name
            ] = best_collector

                        # ============================================
            # تحديث إحصائيات المحصل المختار
            # ============================================

            stats[best_collector]["Debt"] += customer_debt

            stats[best_collector]["Customers"] += 1

            stats[best_collector]["Accounts"] += customer_accounts

            # تحديث شريط التقدم
            progress.progress(
                int(
                    ((i + 1) / total_customers_to_assign) * 100
                )
            )

        # ============================================
        # انتهى التوزيع
        # ============================================

        st.success("تم الانتهاء من توزيع العملاء.")

        # ============================================
        # إنشاء عمود New Collector
        # ============================================

        result = base.copy()

        result["New Collector"] = result["Collector"]

        mask = result["Collector"].isin(
            departed_collectors
        )

        result.loc[
            mask,
            "New Collector"
        ] = result.loc[
            mask,
            "Debitor"
        ].map(assignments)

        # ============================================
        # عرض أول النتائج
        # ============================================

        st.markdown("### أول 20 صف بعد التوزيع")

        st.dataframe(
            result[
                [
                    "Collector",
                    "New Collector",
                    "Debitor",
                    "Account Number",
                    "Net Amount"
                ]
            ].head(20),
            use_container_width=True,
            hide_index=True
        )
                # ============================================
        # إحصائيات بعد التوزيع
        # ============================================

        after_stats = (
            result
            .groupby("New Collector")
            .agg(
                Accounts=(
                    "Account Number",
                    "nunique"
                ),
                Customers=(
                    "Debitor",
                    "nunique"
                ),
                Debt=(
                    "Net Amount",
                    "sum"
                )
            )
            .reset_index()
        )

        after_stats["Debt"] = (
            after_stats["Debt"]
            .round(2)
        )

        st.markdown("## المحافظ بعد التوزيع")

        st.dataframe(
            after_stats,
            use_container_width=True,
            hide_index=True
        )

        # ============================================
        # التحقق من عدم تقسيم العميل
        # ============================================

        validation = (
            result
            .groupby("Debitor")["New Collector"]
            .nunique()
            .reset_index(name="Collectors")
        )

        split_customers = validation[
            validation["Collectors"] > 1
        ]

        if len(split_customers) == 0:

            st.success(
                "✅ لم يتم تقسيم أي عميل بين أكثر من محصل."
            )

        else:

            st.error(
                f"❌ يوجد {len(split_customers)} عميل تم تقسيمهم."
            )

            st.dataframe(split_customers)

        # ============================================
        # مقارنة قبل وبعد
        # ============================================

        before_compare = remaining_stats.copy()

        before_compare = before_compare.rename(
            columns={
                "Collector": "New Collector",
                "Debt": "Debt Before",
                "Customers": "Customers Before",
                "Accounts": "Accounts Before"
            }
        )

        compare = before_compare.merge(
            after_stats.rename(
                columns={
                    "Debt": "Debt After",
                    "Customers": "Customers After",
                    "Accounts": "Accounts After"
                }
            ),
            on="New Collector",
            how="outer"
        ).fillna(0)

        st.markdown("## مقارنة قبل / بعد")

        st.dataframe(
            compare,
            use_container_width=True,
            hide_index=True
        )

        # ============================================
        # تنزيل الملف
        # ============================================

        output = io.BytesIO()

        with pd.ExcelWriter(
            output,
            engine="openpyxl"
        ) as writer:

            result.to_excel(
                writer,
                index=False,
                sheet_name="Distribution"
            )

            after_stats.to_excel(
                writer,
                index=False,
                sheet_name="Summary"
            )

            compare.to_excel(
                writer,
                index=False,
                sheet_name="Comparison"
            )

        output.seek(0)

        st.download_button(
            label="📥 تحميل ملف التوزيع",
            data=output,
            file_name="Collector_Distribution.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        





elif page == "اخطاء الحالات":
    st.subheader("❌ اخطاء الحالات")

elif page == "الاوتودايلر":
    st.subheader("📞 الاوتودايلر")

elif page == "مطابقة السدادات":
    st.subheader("💰 مطابقة السدادات")

elif page == "وعود لا يوجد لها تاريخ الوعد":
    st.subheader("📅 وعود بدون تاريخ")
