"""Run the full analysis and save charts to outputs/.  Usage: python run_eda.py
Adapts automatically to the columns in your dataset (dates/customers optional)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import sales_analysis as sa

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
os.makedirs(OUT, exist_ok=True)
sns.set_theme(style="whitegrid", palette="deep")


def save(name):
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, name), dpi=130)
    plt.close()
    print("  saved", name)


def main():
    raw = sa.load_data()
    print(f"Raw shape: {raw.shape}")
    df, report = sa.clean_data(raw)
    has = lambda *cols: all(c in df.columns for c in cols)

    print("\n--- Cleaning report ---")
    for k, v in report.items():
        print(f"{k}: {v}")
    if not report["has_dates"]:
        print("\nNOTE: no order-date column found -> time-trend charts are skipped.")
    if not report["has_customers"]:
        print("NOTE: no customer-id column found -> RFM customer segmentation is skipped.")

    print("\n--- Descriptive statistics ---")
    num = [c for c in ("sales", "quantity", "discount", "profit") if c in df]
    print(df[num].describe().round(2))

    print("\n--- KPIs ---")
    for k, v in sa.compute_kpis(df).items():
        print(f"{k}: {v:,.2f}")

    print("\n--- Saving charts ---")
    # 1. Monthly trend (needs dates)
    if has("year_month"):
        m = sa.monthly_sales(df)
        plt.figure(figsize=(11, 4.5))
        plt.plot(m.index, m["sales"], marker="o", ms=3, label="Monthly sales")
        plt.plot(m.index, m["rolling_3m"], lw=2.5, label="3-month average")
        plt.title("Monthly Sales Trend"); plt.ylabel("Sales ($)"); plt.legend()
        save("01_monthly_trend.png")

    # 2. Sales by each categorical dimension that exists
    dims = [c for c in ("category", "region", "segment", "ship_mode") if has(c)]
    if dims:
        ncols = min(2, len(dims)); nrows = (len(dims) + ncols - 1) // ncols
        fig, axes = plt.subplots(nrows, ncols, figsize=(6 * ncols, 4.3 * nrows), squeeze=False)
        for ax in axes.flat[len(dims):]:
            ax.axis("off")
        for ax, d in zip(axes.flat, dims):
            g = sa.group_summary(df, d)
            sns.barplot(x=g.index, y=g["sales"], ax=ax)
            ax.set_title(f"Sales by {d.replace('_', ' ').title()}")
            plt.setp(ax.get_xticklabels(), rotation=20)
        save("02_sales_by_dimension.png")

    # 3. Top 10 items and states
    item = sa.item_column(df)
    if item:
        top = sa.group_summary(df, item).head(10)
        plt.figure(figsize=(9, 5))
        sns.barplot(y=top.index, x=top["sales"], orient="h")
        plt.title(f"Top 10 {item.replace('_', ' ').title()} by Sales")
        save("03_top_items.png")
    if has("state"):
        top = sa.group_summary(df, "state").head(10)
        plt.figure(figsize=(9, 5))
        sns.barplot(y=top.index, x=top["sales"], orient="h")
        plt.title("Top 10 States by Sales")
        save("03b_top_states.png")

    # 4. Profit margin by sub-category / profit by state
    if has("sub_category", "profit"):
        sub = sa.group_summary(df, "sub_category").sort_values("margin_pct")
        plt.figure(figsize=(9, 5))
        sns.barplot(y=sub.index, x=sub["margin_pct"], orient="h")
        plt.axvline(0, color="k", lw=1); plt.title("Profit Margin % by Sub-Category")
        save("04_margin_subcategory.png")
    if has("state", "profit"):
        st_ = sa.group_summary(df, "state").sort_values("profit")
        pick = pd.concat([st_.head(8), st_.tail(8)])
        plt.figure(figsize=(9, 6))
        sns.barplot(y=pick.index, x=pick["profit"], orient="h")
        plt.axvline(0, color="k", lw=1); plt.title("Most and Least Profitable States")
        save("04b_profit_by_state.png")

    # 5. Discount vs profit margin
    if has("discount", "profit_margin"):
        plt.figure(figsize=(9, 5))
        sns.boxplot(data=df, x="discount", y="profit_margin", showfliers=False)
        plt.xticks(rotation=45); plt.title("Profit Margin by Discount Level")
        save("05_discount_vs_margin.png")

    # 6. Seasonality heatmap (needs dates)
    if has("year", "month"):
        pivot = df.pivot_table(index="year", columns="month", values="sales", aggfunc="sum")
        plt.figure(figsize=(10, 3.5))
        sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlGnBu")
        plt.title("Sales Heatmap (Year x Month)")
        save("06_seasonality_heatmap.png")

    # 7. Correlation
    if len(num) > 1:
        plt.figure(figsize=(5.5, 4.5))
        sns.heatmap(df[num].corr(), annot=True, cmap="coolwarm", center=0)
        plt.title("Correlation Matrix")
        save("07_correlation.png")

    # 8. RFM (needs customers + dates)
    if report["has_dates"] and report["has_customers"]:
        rfm = sa.rfm_segmentation(df)
        seg = rfm["segment"].value_counts()
        plt.figure(figsize=(7, 4))
        sns.barplot(x=seg.index, y=seg.values)
        plt.title("Customer Segments (RFM)"); plt.ylabel("Customers")
        save("08_rfm_segments.png")

    # 9. Distributions
    fig, ax = plt.subplots(1, 2 if has("profit") else 1, figsize=(11, 4), squeeze=False)
    sns.histplot(df["sales"].clip(upper=df["sales"].quantile(.99)), bins=50, ax=ax[0][0])
    ax[0][0].set_title("Sales per row (clipped at 99th pct)")
    if has("profit"):
        sns.histplot(df["profit"].clip(df["profit"].quantile(.01), df["profit"].quantile(.99)), bins=50, ax=ax[0][1])
        ax[0][1].set_title("Profit per row (1st-99th pct)")
    save("09_distributions.png")

    print("\n--- Business insights ---")
    for i in sa.generate_insights(df):
        print("*", i)

    df.to_csv(os.path.join(OUT, "cleaned_sales.csv"), index=False)
    print(f"\nCharts and cleaned data saved to {OUT}")


if __name__ == "__main__":
    main()
