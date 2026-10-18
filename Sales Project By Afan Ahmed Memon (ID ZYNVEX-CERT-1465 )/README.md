# Sales Data Analysis and Business Insights

An end-to-end data science project that cleans a real-world retail sales dataset, analyses it, and presents the findings in an interactive Streamlit dashboard.

**Live app:** _add your Streamlit link here_  
**Demo video:** _add your Google Drive link here_

## What it does
- **Data cleaning** - standardises columns, removes duplicates, fixes types, handles missing values, flags outliers (IQR).
- **KPIs** - total sales, profit, profit margin, orders, average order value, year-over-year growth (when dates exist).
- **Analysis** - sales and profit by product, category, sub-category, region, state, segment and ship mode; discount impact on margin; correlations; distributions.
- **Time and customer analysis** (only when the dataset has Order Date / Customer ID) - monthly trend, seasonality heatmap, weekday pattern, RFM customer segmentation.
- **Auto-generated business insights** in plain English.
- **Dashboard** - sidebar filters, KPI cards, five tabs, CSV upload and download.

The code adapts to the columns it finds, so it works on both the short 13-column Superstore file and the full version with dates and customers.

## Tech stack
Python, Pandas, NumPy, Matplotlib, Seaborn, Streamlit, ReportLab (PDF report).

## Project structure
```
.
├── app.py                # Streamlit dashboard
├── sales_analysis.py     # loading, cleaning, KPIs, RFM, insights
├── run_eda.py            # full EDA: prints stats, saves charts to outputs/
├── make_report.py        # builds the PDF report from your data + screenshots
├── requirements.txt
├── data/                 # put your sales CSV here
└── screenshots/          # dashboard screenshots used by the report
```

## Dataset
Put your sales CSV (for example the Kaggle "Sample - Superstore" file) in the `data/` folder. Any `.csv` there is picked up automatically. If the folder has no CSV, the code generates sample data so it still runs.

Expected columns (names are matched case-insensitively): Sales is required; Order Date, Order ID, Customer ID, Segment, Region, State, Category, Sub-Category, Product Name, Quantity, Discount, Profit, Ship Mode are optional.

## Run locally
```bash
pip install -r requirements.txt
python run_eda.py                 # analysis + charts in outputs/
python -m streamlit run app.py    # dashboard at http://localhost:8501
```

## Build the PDF report
Save dashboard screenshots into `screenshots/`, then:
```bash
python make_report.py --author "Your Name" --github "<repo link>" --app "<live app link>"
```

## Deploy (Streamlit Community Cloud)
1. Push this repo to GitHub (include your CSV in `data/`).
2. Go to https://share.streamlit.io, sign in with GitHub, click **Create app**.
3. Choose the repo, branch `main`, main file `app.py`, then **Deploy**.

## Future work
Sales forecasting (ARIMA / Prophet), profit prediction and discount optimisation models, customer lifetime value and churn, Plotly interactivity, live database connection, automated tests and CI.
