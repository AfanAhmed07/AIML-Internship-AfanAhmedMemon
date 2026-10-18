"""Build the project report PDF from YOUR dataset.

Usage (inside the project folder):
    python make_report.py --author "Your Name" --github "https://github.com/you/repo" --app "https://your-app.streamlit.app"

* Reads the CSV in data/ (same loader as the dashboard), re-runs the analysis and charts.
* Embeds every PNG/JPG found in screenshots/ in the "App UI Screenshots" section.
* Writes Sales_Analysis_Project_Report.pdf
"""
import argparse
import datetime
import glob
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

import run_eda
import sales_analysis as sa

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "outputs")
SHOTS = os.path.join(HERE, "screenshots")
PAGE_W, PAGE_H = A4
FRAME_W = PAGE_W - 4 * cm

CHARTS = [  # (file, caption)
    ("01_monthly_trend.png", "Monthly sales with a 3-month moving average."),
    ("06_seasonality_heatmap.png", "Seasonality: total sales by year and month."),
    ("02_sales_by_dimension.png", "Sales by category, region, segment and shipping mode."),
    ("03_top_items.png", "Top 10 products / sub-categories by sales."),
    ("03b_top_states.png", "Top 10 states by sales."),
    ("04_margin_subcategory.png", "Profit margin (%) by sub-category."),
    ("04b_profit_by_state.png", "Most and least profitable states."),
    ("05_discount_vs_margin.png", "Profit margin by discount level."),
    ("07_correlation.png", "Correlation between numeric variables."),
    ("08_rfm_segments.png", "Customer segments from RFM analysis."),
    ("09_distributions.png", "Distribution of sales and profit per record."),
]

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, spaceBefore=14, spaceAfter=8,
                    textColor=colors.HexColor("#1f3b5c"))
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1f3b5c"))
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontSize=10.5, leading=15, alignment=4)
CAP = ParagraphStyle("Cap", parent=styles["BodyText"], fontSize=9, leading=11, alignment=1,
                     textColor=colors.HexColor("#555555"), spaceAfter=10)
TITLE = ParagraphStyle("Title2", parent=styles["Title"], fontSize=26, leading=32,
                       textColor=colors.HexColor("#1f3b5c"))
SUB = ParagraphStyle("Sub", parent=styles["BodyText"], fontSize=13, alignment=1, leading=18)


def P(text, style=BODY):
    return Paragraph(text, style)


def bullets(items):
    return [Paragraph("&bull; " + t, ParagraphStyle("b", parent=BODY, leftIndent=14, firstLineIndent=-10,
                                                     spaceAfter=3, alignment=0)) for t in items]


def fit_image(path, max_w=FRAME_W, max_h=11 * cm):
    iw, ih = ImageReader(path).getSize()
    s = min(max_w / iw, max_h / ih, 1.0 if max_w / iw > 1 else 9e9)
    return Image(path, iw * s, ih * s)


def table(rows, col_widths=None, header=True):
    t = Table(rows, colWidths=col_widths, hAlign="LEFT")
    st = [("FONTSIZE", (0, 0), (-1, -1), 9), ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#bbbbbb")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                                                    [colors.white, colors.HexColor("#f3f6fa")])]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3b5c")),
               ("TEXTCOLOR", (0, 0), (-1, 0), colors.white), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold")]
    t.setStyle(TableStyle(st))
    return t


def summary_table(df, by, n=10):
    g = sa.group_summary(df, by).head(n)
    cols = ["sales"] + (["profit", "margin_pct"] if "profit" in g else []) + ["orders"]
    rows = [[by.replace("_", " ").title(), "Sales ($)"] + (["Profit ($)", "Margin (%)"] if "profit" in g else [])
            + ["Records"]]
    for idx, r in g.iterrows():
        row = [str(idx), f"{r['sales']:,.0f}"]
        if "profit" in g:
            row += [f"{r['profit']:,.0f}", f"{r['margin_pct']:.1f}"]
        row.append(f"{int(r['orders']):,}")
        rows.append(row)
    return table(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--author", default="")
    ap.add_argument("--github", default="")
    ap.add_argument("--app", default="")
    ap.add_argument("--draft", action="store_true", help="stamp the report as a draft")
    ap.add_argument("--out", default=os.path.join(HERE, "Sales_Analysis_Project_Report.pdf"))
    a = ap.parse_args()

    # 1. run analysis (also saves charts to outputs/)
    for f in glob.glob(os.path.join(OUT, "*.png")):
        os.remove(f)
    run_eda.main()
    path = sa.find_dataset()
    raw = sa.load_data()
    df, rep = sa.clean_data(raw)
    k = sa.compute_kpis(df)
    insights = sa.generate_insights(df)
    ds_name = os.path.basename(path) if path else "generated sample data"
    shots = sorted(glob.glob(os.path.join(SHOTS, "*.png")) + glob.glob(os.path.join(SHOTS, "*.jpg"))
                   + glob.glob(os.path.join(SHOTS, "*.jpeg")))
    if not a.author:
        print("WARNING: pass --author \"Your Name\" so the cover page has your name.")
    if not shots:
        print("WARNING: no screenshots found in screenshots/ - add dashboard PNGs and re-run.")

    story = []
    # ---------- cover ----------
    story += [Spacer(1, 5 * cm), P("Sales Data Analysis<br/>and Business Insights", TITLE), Spacer(1, 0.6 * cm),
              P("Data Science Final Project Report", SUB), Spacer(1, 1.2 * cm)]
    if a.author:
        story.append(P(f"<b>Prepared by:</b> {a.author}", SUB))
    story.append(P(f"<b>Date:</b> {datetime.date.today():%d %B %Y}", SUB))
    story.append(P("<b>Tools:</b> Python, Pandas, NumPy, Matplotlib, Seaborn, Streamlit", SUB))
    if a.github:
        story.append(P(f"<b>Code:</b> {a.github}", SUB))
    if a.app:
        story.append(P(f"<b>Live app:</b> {a.app}", SUB))
    if a.draft:
        story += [Spacer(1, 1 * cm), P("<font color='red'><b>DRAFT - generated from stand-in sample data, "
                                       "not the final dataset.</b></font>", SUB)]
    story.append(PageBreak())

    # ---------- 1 problem ----------
    story += [P("1. Problem Statement", H1),
              P("Businesses record thousands of sales transactions, but raw records alone do not show which "
                "products, categories and regions drive revenue and profit, where discounting erodes margin, "
                "or how demand changes over time. Without a structured analysis, decisions on pricing, "
                "inventory and marketing rely on intuition. This project turns raw sales data into clean, "
                "reliable KPIs, visual analysis and an interactive dashboard so that decision-makers can "
                "find trends, top performers and problem areas quickly."),
              P("2. Introduction", H1),
              P("The project is an end-to-end data science workflow: loading a real-world retail sales "
                "dataset, cleaning it, exploring it statistically and visually, calculating business KPIs, "
                "and presenting the findings in a Streamlit dashboard. The pipeline adapts to the columns "
                "available in the dataset, so optional analyses (time trends, customer segmentation) run "
                "only when the required fields exist."),
              P("<b>Objectives</b>", H2)]
    story += bullets([
        "Load and clean the sales dataset, handling missing values, duplicates and invalid records.",
        "Perform exploratory data analysis and compute summary statistics and KPIs.",
        "Analyse sales and profit by product, category, region and (where available) time period.",
        "Identify top-performing products and loss-making areas, and the effect of discounts.",
        "Present results through charts and an interactive, filterable dashboard."])

    # ---------- 3 data & method ----------
    story += [P("3. Dataset and Methodology", H1),
              P(f"<b>Dataset:</b> {ds_name} - {rep['rows_raw']:,} raw records, "
                f"{len(rep['columns_found'])} columns "
                f"({', '.join(rep['columns_found'])}).")]
    story += [Spacer(1, 4), P("<b>Data cleaning summary</b>", H2)]
    story.append(table([["Step", "Result"],
                        ["Raw records", f"{rep['rows_raw']:,}"],
                        ["Duplicate rows removed", f"{rep['duplicates_removed']:,}"],
                        ["Rows dropped (missing date/sales)", f"{rep['rows_dropped_critical_na']:,}"],
                        ["Outlier records flagged (IQR, kept)", f"{rep['outliers_flagged']:,}"],
                        ["Clean records used for analysis", f"{rep['rows_clean']:,}"]],
                       col_widths=[9 * cm, 5 * cm]))
    if rep["missing_before"]:
        story.append(P("Missing values before cleaning: " +
                       ", ".join(f"{c} ({n})" for c, n in rep["missing_before"].items()) + ".", CAP))
    story.append(P("<b>Method</b>", H2))
    story += bullets([
        "<b>Cleaning:</b> standardised column names, removed duplicates, converted data types, dropped rows "
        "missing critical fields, filled other gaps (median for numbers, 'Unknown' for text), removed "
        "invalid values, flagged outliers with the IQR rule.",
        "<b>Feature engineering:</b> year, month, quarter, weekday and profit margin where the data allows.",
        "<b>KPIs:</b> total sales, profit, profit margin, orders, average order value, growth.",
        "<b>Analysis:</b> group summaries, discount impact, correlation, distributions, and RFM customer "
        "segmentation when customer IDs and dates exist.",
        "<b>Dashboard:</b> Streamlit app with filters, KPI cards, tabbed charts and CSV download."])
    if not rep["has_dates"]:
        story.append(P("<i>Note: this dataset has no order-date column, so time-trend analysis is not "
                       "included.</i>", CAP))
    story.append(CondPageBreak(10 * cm))

    # ---------- 4 screenshots ----------
    story.append(P("4. App UI Screenshots", H1))
    if shots:
        for s in shots:
            cap = os.path.splitext(os.path.basename(s))[0].replace("_", " ").replace("-", " ").strip()
            story.append(KeepTogether([fit_image(s, FRAME_W, 12 * cm), P(f"Figure: {cap}", CAP)]))
    else:
        story.append(P("(No screenshots found in the screenshots/ folder.)"))
    story.append(PageBreak())

    # ---------- 5 results ----------
    story.append(P("5. Results", H1))
    story.append(P("<b>Key performance indicators</b>", H2))
    names = {"total_sales": ("Total sales", "${:,.0f}"), "total_profit": ("Total profit", "${:,.0f}"),
             "profit_margin_pct": ("Profit margin", "{:.1f}%"), "total_orders": ("Orders / records", "{:,.0f}"),
             "avg_order_value": ("Average order value", "${:,.2f}"), "total_customers": ("Customers", "{:,.0f}"),
             "total_quantity": ("Units sold", "{:,.0f}"), "yoy_growth_pct": ("Latest year-over-year growth", "{:.1f}%")}
    story.append(table([["KPI", "Value"]] + [[names[x][0], names[x][1].format(v)] for x, v in k.items() if x in names],
                       col_widths=[9 * cm, 5 * cm]))
    story += [Spacer(1, 6), P("<b>Key business insights</b>", H2)] + bullets(insights)

    for by in ("category", "region", "sub_category"):
        if by in df:
            story.append(KeepTogether([Spacer(1, 6), P(f"<b>Performance by {by.replace('_', ' ')}</b>", H2),
                                       summary_table(df, by)]))
    story.append(CondPageBreak(10 * cm))
    story.append(P("Visual analysis", H2))
    for fname, cap in CHARTS:
        p = os.path.join(OUT, fname)
        if os.path.exists(p):
            story.append(KeepTogether([fit_image(p, FRAME_W, 9.5 * cm), P(cap, CAP)]))

    # ---------- 6 conclusion & future ----------
    story += [PageBreak(), P("6. Conclusion", H1),
              P("The project shows how a systematic cleaning and analysis pipeline converts raw sales "
                "records into decisions: it highlights the strongest categories and regions, exposes "
                "loss-making segments, and quantifies how heavy discounting affects profit margin. The "
                "dashboard lets non-technical users filter and explore these results on their own."),
              P("7. Future Approach", H1)]
    story += bullets([
        "<b>Sales forecasting:</b> add time-series models (ARIMA / Prophet) to predict future demand when "
        "date data is available.",
        "<b>Profit prediction and discount optimisation:</b> train regression or gradient-boosting models "
        "to find discount levels that protect margin.",
        "<b>Customer analytics:</b> extend RFM into customer lifetime value, churn prediction and "
        "product recommendations using customer-level data.",
        "<b>Richer interactivity:</b> move charts to Plotly for hover, zoom and drill-down.",
        "<b>Live data pipeline:</b> connect the dashboard to a database or API instead of a static CSV, "
        "with scheduled refresh.",
        "<b>Quality and operations:</b> add automated tests, CI checks, authentication and automated "
        "report emails."])
    if a.github or a.app:
        story.append(P("8. Links", H1))
        if a.github:
            story.append(P(f"GitHub repository: {a.github}"))
        if a.app:
            story.append(P(f"Live application: {a.app}"))

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, "Sales Data Analysis and Business Insights"
                          + ("  |  DRAFT - sample data" if a.draft else ""))
        canvas.drawRightString(PAGE_W - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(a.out, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm,
                            bottomMargin=2 * cm, title="Sales Data Analysis and Business Insights",
                            author=a.author or "")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"\nReport written to {a.out}")


if __name__ == "__main__":
    main()
