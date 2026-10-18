"""Interactive dashboard.  Run: python -m streamlit run app.py
Adapts to the columns in your dataset (dates / customers are optional)."""
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import sales_analysis as sa

st.set_page_config(page_title="Sales Dashboard", page_icon="📊", layout="wide")
sns.set_theme(style="whitegrid")


@st.cache_data
def get_data(uploaded=None):
    raw = pd.read_csv(uploaded, encoding="latin-1") if uploaded else sa.load_data()
    return sa.clean_data(raw)


st.title("📊 Sales Data Analysis and Business Insights")

# ---------------- Sidebar ----------------
uploaded = st.sidebar.file_uploader("Upload your sales CSV (optional)", type="csv")
df_all, report = get_data(uploaded)
has_dates = report["has_dates"]
has_customers = report["has_customers"]

st.sidebar.header("Filters")
mask = pd.Series(True, index=df_all.index)
if has_dates:
    years = sorted(df_all["year"].unique())
    sel = st.sidebar.multiselect("Year", years, default=years)
    mask &= df_all["year"].isin(sel)
for col, label in [("region", "Region"), ("category", "Category"), ("segment", "Segment")]:
    if col in df_all:
        opts = sorted(df_all[col].unique())
        sel = st.sidebar.multiselect(label, opts, default=opts)
        mask &= df_all[col].isin(sel)
df = df_all[mask]
if df.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ---------------- KPI cards ----------------
k = sa.compute_kpis(df)
cards = [("Total Sales", f"${k['total_sales']:,.0f}")]
if "total_profit" in k:
    cards += [("Total Profit", f"${k['total_profit']:,.0f}"),
              ("Profit Margin", f"{k['profit_margin_pct']:.1f}%")]
cards += [("Orders", f"{k['total_orders']:,}"), ("Avg Order Value", f"${k['avg_order_value']:,.0f}")]
for col, (label, value) in zip(st.columns(len(cards)), cards):
    col.metric(label, value)
if "note" in report:
    st.caption(report["note"])

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["📈 Trends", "🛒 Products", "🌍 Regions", "👥 Customers", "💡 Insights & Data"])

# ---------------- Trends ----------------
with tab1:
    if has_dates:
        m = sa.monthly_sales(df)
        fig, ax = plt.subplots(figsize=(11, 4))
        ax.plot(m.index, m["sales"], marker="o", ms=3, label="Monthly")
        ax.plot(m.index, m["rolling_3m"], lw=2.5, label="3-month avg")
        ax.set_title("Monthly Sales"); ax.legend()
        st.pyplot(fig)
        col1, col2 = st.columns(2)
        with col1:
            pivot = df.pivot_table(index="year", columns="month", values="sales", aggfunc="sum")
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.heatmap(pivot, cmap="YlGnBu", ax=ax); ax.set_title("Seasonality heatmap")
            st.pyplot(fig)
        with col2:
            wd = df.groupby("weekday")["sales"].sum().reindex(
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
            fig, ax = plt.subplots(figsize=(6, 3))
            sns.barplot(x=wd.index, y=wd.values, ax=ax)
            ax.set_title("Sales by weekday"); plt.setp(ax.get_xticklabels(), rotation=45)
            st.pyplot(fig)
    else:
        st.info("This dataset has no order-date column, so time trends are not available. "
                "Showing distributions instead.")
        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.histplot(df["sales"].clip(upper=df["sales"].quantile(.99)), bins=50, ax=ax)
            ax.set_title("Sales per row (clipped at 99th pct)")
            st.pyplot(fig)
        with col2:
            if "discount" in df and "profit" in df:
                fig, ax = plt.subplots(figsize=(6, 4))
                sns.boxplot(data=df, x="discount", y="profit_margin", showfliers=False, ax=ax)
                ax.set_title("Profit margin by discount level")
                plt.setp(ax.get_xticklabels(), rotation=45)
                st.pyplot(fig)

# ---------------- Products ----------------
with tab2:
    item = sa.item_column(df)
    col1, col2 = st.columns(2)
    with col1:
        if item:
            top = sa.group_summary(df, item).head(10)
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(y=top.index, x=top["sales"], ax=ax, orient="h")
            ax.set_title(f"Top 10 {item.replace('_', ' ')} by sales")
            st.pyplot(fig)
    with col2:
        if "sub_category" in df and "profit" in df:
            sub = sa.group_summary(df, "sub_category").sort_values("margin_pct")
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(y=sub.index, x=sub["margin_pct"], ax=ax, orient="h")
            ax.axvline(0, color="k", lw=1); ax.set_title("Margin % by sub-category")
            st.pyplot(fig)
    if "category" in df and "sub_category" in df:
        st.dataframe(sa.group_summary(df, ["category", "sub_category"]).round(2))
    elif item:
        st.dataframe(sa.group_summary(df, item).round(2))

# ---------------- Regions ----------------
with tab3:
    col1, col2 = st.columns(2)
    with col1:
        if "region" in df:
            reg = sa.group_summary(df, "region")
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.pie(reg["sales"], labels=reg.index, autopct="%1.1f%%", startangle=90)
            ax.set_title("Share of sales by region")
            st.pyplot(fig)
            st.dataframe(reg.round(2))
    with col2:
        if "state" in df:
            top = sa.group_summary(df, "state").head(10)
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(y=top.index, x=top["sales"], ax=ax, orient="h")
            ax.set_title("Top 10 states by sales")
            st.pyplot(fig)
    if "state" in df and "profit" in df:
        st.subheader("State performance")
        st.dataframe(sa.group_summary(df, "state").round(2))

# ---------------- Customers ----------------
with tab4:
    if has_dates and has_customers:
        rfm = sa.rfm_segmentation(df)
        col1, col2 = st.columns(2)
        with col1:
            s = rfm["segment"].value_counts()
            fig, ax = plt.subplots(figsize=(6, 4))
            sns.barplot(x=s.index, y=s.values, ax=ax); ax.set_title("RFM customer segments")
            st.pyplot(fig)
        with col2:
            st.subheader("Top 10 customers")
            st.dataframe(rfm.sort_values("monetary", ascending=False).head(10)[
                ["recency", "frequency", "monetary", "segment"]].round(0))
    else:
        st.info("RFM customer analysis needs Customer ID and Order Date columns, which this dataset "
                "does not have. Showing segment and shipping analysis instead.")
        for col in ("segment", "ship_mode"):
            if col in df:
                st.subheader(f"By {col.replace('_', ' ')}")
                st.dataframe(sa.group_summary(df, col).round(2))

# ---------------- Insights ----------------
with tab5:
    st.subheader("Key business insights")
    for i in sa.generate_insights(df):
        st.markdown(f"- {i}")
    with st.expander("Data cleaning report"):
        st.json({k: v for k, v in report.items() if k != "columns_found"})
    st.download_button("Download filtered data (CSV)", df.to_csv(index=False), "filtered_sales.csv")
