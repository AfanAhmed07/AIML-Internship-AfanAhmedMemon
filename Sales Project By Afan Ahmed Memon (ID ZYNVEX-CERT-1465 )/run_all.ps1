# run_all.ps1 - Sales Data Analysis project: install, analyze, launch dashboard
# Usage (inside the sales_project folder):
#   powershell -ExecutionPolicy Bypass -File .\run_all.ps1

$ProjectDir = $PSScriptRoot
if (-not $ProjectDir) { $ProjectDir = (Get-Location).Path }
Set-Location $ProjectDir
Write-Host "Project folder: $ProjectDir" -ForegroundColor Cyan

# 1. Check required files
$required = @("app.py", "sales_analysis.py", "run_eda.py")
$missing = $required | Where-Object { -not (Test-Path $_) }
if ($missing) {
    Write-Host "Missing files: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Put them in $ProjectDir and run this script again."
    exit 1
}

# 2. Check Python
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python not found. Install it from python.org (tick 'Add python.exe to PATH')." -ForegroundColor Red
    exit 1
}

# 3. Install libraries
Write-Host "`nInstalling libraries..." -ForegroundColor Cyan
python -m pip install pandas numpy matplotlib seaborn streamlit
if ($LASTEXITCODE -ne 0) {
    Write-Host "Library install failed. Check the errors above." -ForegroundColor Red
    exit 1
}

# 4. Data folder (put any CSV inside data\; otherwise sample data is used)
if (-not (Test-Path "data")) { New-Item -ItemType Directory -Path "data" | Out-Null }
$csv = Get-ChildItem -Path "data" -Filter *.csv -ErrorAction SilentlyContinue | Select-Object -First 1
if ($csv) {
    Write-Host "`nUsing dataset: $($csv.FullName)" -ForegroundColor Green
} else {
    Write-Host "`nNo CSV found in data\ - using generated sample data." -ForegroundColor Yellow
}

# 5. Run the analysis (prints report, saves charts to outputs\)
Write-Host "`nRunning analysis..." -ForegroundColor Cyan
python run_eda.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "Analysis failed. Check the errors above." -ForegroundColor Red
    exit 1
}

# 6. Launch the dashboard (Ctrl+C to stop)
Write-Host "`nStarting dashboard at http://localhost:8501  (press Ctrl+C to stop)" -ForegroundColor Cyan
python -m streamlit run app.py
