# Final submission kit

Mandatory items: **GitHub link, PDF report, demo video (Drive), live app link (or local-run video), LinkedIn post.**
Links that are not accessible are rejected, so test each one in an incognito/private window.

---
## 0. Put the project in one folder
Folder (example): `C:\Users\Afan Ahmed Memon\Downloads\Internship\Zynvex\sales_project`
Contents: `app.py, sales_analysis.py, run_eda.py, make_report.py, requirements.txt, README.md, .gitignore`, `data\<your csv>`, `screenshots\`.
Replace your old `.py` files with the new ones from this kit (`run_eda.py` has a better chart layout).

## 1. Run it once and take screenshots
```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```
In the browser, press **Win + Shift + S**, capture each view, and save as PNG in `screenshots\`. Suggested names (they become the captions, and files are sorted by name):
- `1 Dashboard overview - KPI cards and filters.png`
- `2 Trends tab.png`
- `3 Products tab.png`
- `4 Regions tab.png`
- `5 Customers tab.png`
- `6 Insights and data tab.png`

## 2. GitHub (code)
1. Create an account/repo at github.com (New repository, public, name e.g. `sales-data-analysis`, no README).
2. Easiest way - web upload: open the empty repo, click **uploading an existing file**, drag in all project files **including** the `data` and `screenshots` folders, click **Commit changes**.
3. Or with Git installed, in PowerShell inside the project folder:
```powershell
git init
git add .
git commit -m "Sales data analysis project"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```
4. Copy the repo link, e.g. `https://github.com/<your-username>/sales-data-analysis`.

## 3. Live app (Streamlit Community Cloud, free)
1. Go to https://share.streamlit.io and sign in with GitHub.
2. **Create app** -> choose your repo, branch `main`, main file path `app.py`.
3. Click **Deploy** and wait a few minutes. Copy the `https://....streamlit.app` link.
4. Open the link in a private window to confirm it loads without login.
If deployment fails, open **Manage app -> logs**. Common causes: CSV not in `data/`, or file names differ in capitals. If you cannot deploy, the instructions allow a Drive video of the app running locally instead.

## 4. PDF report
After the screenshots are saved:
```powershell
python make_report.py --author "Your Name" --github "<repo link>" --app "<live app link>"
```
It writes `Sales_Analysis_Project_Report.pdf` with: problem statement, introduction, dataset and method, **app UI screenshots**, results (KPIs, insights, charts), conclusion, future approach, links. Open it and check the screenshots appear and your name is on the cover.

## 5. Demo video (2-3 minutes)
Record with **Win + G** (Xbox Game Bar -> Capture -> record) or OBS Studio. Suggested script:
1. (0:00) "Hi, I'm <name>. This is my Sales Data Analysis and Business Insights project." State the problem: businesses need to know which products, regions and discounts drive profit.
2. (0:20) Show the code folder and dataset; mention cleaning: duplicates, missing values, outliers.
3. (0:45) Run `python run_eda.py` briefly and show the printed KPIs and insights.
4. (1:05) Open the dashboard: KPI cards, change the sidebar filters, walk through each tab.
5. (2:10) Read out 2-3 real insights (top category, loss-making sub-category, discount effect).
6. (2:40) Close: tools used, GitHub and live link, future work (forecasting, ML models).
Upload to Google Drive -> **Share -> General access -> Anyone with the link -> Viewer** -> copy link. Test it in a private window.

## 6. LinkedIn post
Post the same screen recording as a native video, add the links, then copy the post URL.

> Excited to share my final Data Science internship project: **Sales Data Analysis and Business Insights**.
>
> I cleaned a real-world retail sales dataset with Python (duplicates, missing values, outliers), analysed sales and profit by product, category, region and discount, and built an interactive Streamlit dashboard with KPIs and filters.
>
> Key findings:
> - [your top finding, e.g. which category leads sales]
> - [your second finding, e.g. which sub-category loses money]
> - [your third finding, e.g. what heavy discounts do to margin]
>
> Tools: Python, Pandas, NumPy, Matplotlib, Seaborn, Streamlit
> Live app: <your streamlit link>
> Code: <your github link>
>
> Thank you @Zynvex for the opportunity and guidance. Next up: sales forecasting and profit prediction models.
>
> #DataScience #Python #Streamlit #DataAnalytics #Internship

## 7. Final checklist
- [ ] GitHub repo is **public**; link opens in a private window
- [ ] README shows live app link; `data/` contains your CSV
- [ ] PDF has screenshots, your name, results and future approach
- [ ] Demo video on Drive set to **Anyone with the link**
- [ ] Live app link opens without login (or local-run video provided)
- [ ] LinkedIn post is public and includes the video
- [ ] All five links copied into the submission form
