"""
Sales Data Analysis and Business Insights
Core module: load -> clean -> feature engineering -> KPIs -> aggregations.

Works with the Kaggle "Sample Superstore" dataset (data/superstore.csv) or any CSV
with similar columns. If no file exists, a realistic synthetic dataset is generated
so the whole pipeline runs end to end.
"""
import os
import numpy as np
import pandas as pd

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "superstore.csv")

# Map common column-name variants to one standard schema
COLUMN_MAP = {
    "order id": "order_id", "order date": "order_date", "customer id": "customer_id",
    "customer name": "customer_name", "segment": "segment", "region": "region",
    "category": "category", "sub-category": "sub_category", "sub_category": "sub_category",
    "product name": "product", "product": "product", "sales": "sales",
    "quantity": "quantity", "discount": "discount", "profit": "profit",
    "ship mode": "ship_mode", "ship date": "ship_date", "country": "country",
    "city": "city", "state": "state", "postal code": "postal_code",
    "row id": "row_id", "product id": "product_id",
}


# ----------------------------------------------------------------------------
# 1. Data loading
# ----------------------------------------------------------------------------
def generate_sample_data(n=5000, seed=42) -> pd.DataFrame:
    """Synthetic data shaped like a retail/superstore dataset (with dirty rows)."""
    rng = np.random.default_rng(seed)
    catalog = {
        "Technology": {"Phones": 450, "Laptops": 900, "Accessories": 60},
        "Furniture": {"Chairs": 220, "Tables": 380, "Bookcases": 260},
        "Office Supplies": {"Paper": 25, "Binders": 30, "Storage": 90},
    }
    rows = []
    dates = pd.date_range("2022-01-01", "2025-12-31")
    customers = [f"C{1000 + i}" for i in range(600)]
    for i in range(n):
        cat = rng.choice(list(catalog))
        sub = rng.choice(list(catalog[cat]))
        price = catalog[cat][sub] * rng.uniform(0.8, 1.2)
        qty = int(rng.integers(1, 8))
        disc = float(rng.choice([0, 0, 0, 0.1, 0.2, 0.3, 0.5]))
        d = rng.choice(dates)
        # seasonality: boost Nov/Dec
        if pd.Timestamp(d).month in (11, 12) and rng.random() < 0.5:
            qty += 2
        sales = price * qty * (1 - disc)
        margin = {"Technology": 0.22, "Furniture": 0.08, "Office Supplies": 0.18}[cat]
        profit = sales * (margin - disc * 0.6) + rng.normal(0, 5)
        rows.append({
            "Order ID": f"O-{100000 + i}", "Order Date": d,
            "Customer ID": rng.choice(customers),
            "Segment": rng.choice(["Consumer", "Corporate", "Home Office"], p=[.52, .30, .18]),
            "Region": rng.choice(["West", "East", "Central", "South"], p=[.32, .29, .23, .16]),
            "Category": cat, "Sub-Category": sub, "Product Name": f"{sub} Model {rng.integers(1, 6)}",
            "Sales": round(sales, 2), "Quantity": qty, "Discount": disc, "Profit": round(profit, 2),
        })
    df = pd.DataFrame(rows)
    # inject dirt: missing values and duplicates
    df.loc[rng.choice(n, 60, replace=False), "Region"] = np.nan
    df.loc[rng.choice(n, 40, replace=False), "Sales"] = np.nan
    df = pd.concat([df, df.sample(50, random_state=1)], ignore_index=True)
    return df


def find_dataset():
    """Return the dataset path: data/superstore.csv, else the first CSV in data/."""
    if os.path.exists(DATA_PATH):
        return DATA_PATH
    data_dir = os.path.dirname(DATA_PATH)
    if os.path.isdir(data_dir):
        csvs = sorted(f for f in os.listdir(data_dir) if f.lower().endswith(".csv"))
        if csvs:
            return os.path.join(data_dir, csvs[0])
    return None


def load_data(path: str = None) -> pd.DataFrame:
    path = path or find_dataset()
    if path:
        print(f"Loading dataset: {path}")
        try:
            return pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="latin-1")
    print("No CSV found in data/ - using generated sample data.")
    return generate_sample_data()


# ----------------------------------------------------------------------------
# 2. Cleaning (adapts to whichever columns the dataset has)
# ----------------------------------------------------------------------------
def clean_data(df: pd.DataFrame):
    """Returns (clean_df, report_dict). Only 'sales' is mandatory."""
    report = {"rows_raw": len(df)}
    df = df.copy()
    df.columns = [COLUMN_MAP.get(c.strip().lower(), c.strip().lower().replace(" ", "_").replace("-", "_"))
                  for c in df.columns]
    if "sales" not in df.columns:
        raise ValueError(f"No 'Sales' column found. Your columns are: {list(df.columns)}")

    report["columns_found"] = list(df.columns)
    report["missing_before"] = df.isna().sum()[lambda s: s > 0].to_dict()

    # duplicates
    report["duplicates_removed"] = int(df.duplicated().sum())
    df = df.drop_duplicates()

    # types
    if "order_date" in df:
        df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
    for col in ("sales", "quantity", "discount", "profit"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # missing values: drop rows missing critical fields, impute the rest
    critical = [c for c in ("order_date", "sales") if c in df]
    report["rows_dropped_critical_na"] = int(df[critical].isna().any(axis=1).sum())
    df = df.dropna(subset=critical)
    for col in df.select_dtypes(include="object"):
        df[col] = df[col].fillna("Unknown").str.strip()
    for col in ("quantity", "discount", "profit"):
        if col in df:
            df[col] = df[col].fillna(df[col].median())

    # remove invalid rows
    df = df[df["sales"] > 0]
    if "quantity" in df:
        df = df[df["quantity"] > 0]
    df = df.reset_index(drop=True)

    # outliers flagged (IQR) but kept - they are often genuine big orders
    q1, q3 = df["sales"].quantile([.25, .75])
    iqr = q3 - q1
    df["is_outlier"] = (df["sales"] > q3 + 1.5 * iqr) | (df["sales"] < q1 - 1.5 * iqr)
    report["outliers_flagged"] = int(df["is_outlier"].sum())

    # no order id -> treat every row as one order line
    if "order_id" not in df:
        df["order_id"] = np.arange(1, len(df) + 1)
        report["note"] = "No Order ID column: each row is counted as one order."

    # feature engineering
    if "order_date" in df:
        df["year"] = df["order_date"].dt.year
        df["month"] = df["order_date"].dt.month
        df["month_name"] = df["order_date"].dt.strftime("%b")
        df["quarter"] = df["order_date"].dt.quarter
        df["weekday"] = df["order_date"].dt.day_name()
        df["year_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    if "profit" in df:
        df["profit_margin"] = df["profit"] / df["sales"]

    report["has_dates"] = "order_date" in df
    report["has_customers"] = "customer_id" in df
    report["rows_clean"] = len(df)
    return df, report


# ----------------------------------------------------------------------------
# 3. KPIs and aggregations
# ----------------------------------------------------------------------------
def compute_kpis(df: pd.DataFrame) -> dict:
    kpis = {
        "total_sales": df["sales"].sum(),
        "total_orders": df["order_id"].nunique(),
        "avg_order_value": df.groupby("order_id")["sales"].sum().mean(),
    }
    if "customer_id" in df:
        kpis["total_customers"] = df["customer_id"].nunique()
    if "quantity" in df:
        kpis["total_quantity"] = int(df["quantity"].sum())
    if "profit" in df:
        kpis["total_profit"] = df["profit"].sum()
        kpis["profit_margin_pct"] = 100 * df["profit"].sum() / df["sales"].sum()
    if "year" in df and df["year"].nunique() > 1:
        yearly = df.groupby("year")["sales"].sum().sort_index()
        kpis["yoy_growth_pct"] = float(yearly.pct_change().iloc[-1] * 100)
    return kpis


def group_summary(df: pd.DataFrame, by) -> pd.DataFrame:
    agg = {"sales": "sum", "order_id": "nunique"}
    if "quantity" in df:
        agg["quantity"] = "sum"
    if "profit" in df:
        agg["profit"] = "sum"
    out = df.groupby(by).agg(agg).rename(columns={"order_id": "orders"})
    if "profit" in out:
        out["margin_pct"] = 100 * out["profit"] / out["sales"]
    return out.sort_values("sales", ascending=False)


def monthly_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Requires an order date column."""
    m = df.groupby("year_month")["sales"].sum().to_frame()
    m["rolling_3m"] = m["sales"].rolling(3).mean()
    m["mom_growth_pct"] = m["sales"].pct_change() * 100
    return m


def rfm_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    """Recency / Frequency / Monetary segmentation. Requires customer_id and order_date."""
    snapshot = df["order_date"].max() + pd.Timedelta(days=1)
    rfm = df.groupby("customer_id").agg(
        recency=("order_date", lambda s: (snapshot - s.max()).days),
        frequency=("order_id", "nunique"),
        monetary=("sales", "sum"),
    )
    rfm["r"] = pd.qcut(rfm["recency"].rank(method="first"), 4, labels=[4, 3, 2, 1]).astype(int)
    rfm["f"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["m"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1, 2, 3, 4]).astype(int)
    rfm["score"] = rfm["r"] + rfm["f"] + rfm["m"]

    def label(s):
        if s >= 10: return "Champions"
        if s >= 8: return "Loyal"
        if s >= 6: return "Potential"
        if s >= 4: return "At Risk"
        return "Lost"
    rfm["segment"] = rfm["score"].apply(label)
    return rfm


def item_column(df: pd.DataFrame):
    """Best available 'product-like' column."""
    for c in ("product", "sub_category", "category"):
        if c in df:
            return c
    return None


def generate_insights(df: pd.DataFrame) -> list:
    """Plain-English business insights computed from whatever columns exist."""
    ins = []
    if "category" in df:
        cat = group_summary(df, "category")
        ins.append(f"Top category by sales: {cat.index[0]} (${cat['sales'].iloc[0]:,.0f}, "
                   f"{100 * cat['sales'].iloc[0] / cat['sales'].sum():.1f}% of revenue).")
    if "profit" in df and "sub_category" in df:
        sub = group_summary(df, "sub_category")
        worst, best = sub["margin_pct"].idxmin(), sub["margin_pct"].idxmax()
        ins.append(f"Lowest-margin sub-category: {worst} ({sub.loc[worst, 'margin_pct']:.1f}% margin); "
                   f"highest: {best} ({sub.loc[best, 'margin_pct']:.1f}%).")
        loss = sub[sub["profit"] < 0]
        if len(loss):
            ins.append(f"Loss-making sub-categories: {', '.join(loss.index)} - review pricing and discounts.")
    if "profit" in df and "discount" in df:
        hi, lo = df[df["discount"] >= 0.3], df[df["discount"] < 0.3]
        if len(hi) and len(lo):
            ins.append(f"Orders with >=30% discount earn {100 * hi['profit'].sum() / hi['sales'].sum():.1f}% "
                       f"margin vs {100 * lo['profit'].sum() / lo['sales'].sum():.1f}% otherwise.")
    if "region" in df:
        reg = group_summary(df[df["region"] != "Unknown"], "region")
        ins.append(f"Best region: {reg.index[0]}; weakest: {reg.index[-1]}.")
    if "state" in df:
        st_ = group_summary(df, "state")
        ins.append(f"Top state by sales: {st_.index[0]}; top 5 states make up "
                   f"{100 * st_['sales'].head(5).sum() / st_['sales'].sum():.1f}% of revenue.")
        if "profit" in st_:
            neg = st_[st_["profit"] < 0]
            if len(neg):
                ins.append(f"{len(neg)} states are loss-making, the worst being {neg['profit'].idxmin()}.")
    if "segment" in df:
        sg = group_summary(df, "segment")
        ins.append(f"Largest customer segment by sales: {sg.index[0]} "
                   f"({100 * sg['sales'].iloc[0] / sg['sales'].sum():.1f}%).")
    if "month_name" in df:
        m = df.groupby("month_name")["sales"].sum()
        ins.append(f"Peak month overall: {m.idxmax()}; slowest: {m.idxmin()} - plan inventory and promotions accordingly.")
    if "customer_id" in df:
        n = max(1, int(df["customer_id"].nunique() * .1))
        top = df.groupby("customer_id")["sales"].sum().nlargest(n).sum()
        ins.append(f"Top 10% of customers generate {100 * top / df['sales'].sum():.1f}% of sales.")
    return ins
