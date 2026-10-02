# DataClean Pro — Automated Data Cleaning & Reporting Platform

![DataClean Pro Logo](assets/logo.png)

> **Upload → Clean → Analyze → Report**  
> An enterprise-ready, automated data cleaning, profiling, business intelligence, and reporting platform built with Python and Streamlit.

---

## 🌟 Executive Overview

**DataClean Pro** is an end-to-end data automation platform engineered to bridge the gap between raw, messy datasets and publication-ready analytics. Developed as a high-impact internship project titled **"Data Cleaning & Reporting Automation"**, the platform eliminates repetitive data preparation tasks by:

1. **Ingesting Multi-Format Data**: Seamlessly loading CSV, TSV, XLSX, and XLS datasets with automatic encoding and delimiter detection.
2. **Automated Structural & Semantic Profiling**: Diagnosing missing values, duplicate records, mixed casing, whitespace defects, and anomalies.
3. **Objective Data Quality Scoring**: Computing a weighted, 4-dimensional Data Quality Score (0–100%) before and after remediation.
4. **Deterministic Cleaning Pipeline**: Imputing missing numerical/categorical values, stripping whitespace, fixing negative values, resolving categorical synonyms, standardizing dates (`YYYY-MM-DD`), and winsorizing statistical outliers.
5. **Audit Trail Logging**: Recording every transformation step with timestamps, target columns, records affected, and human-readable descriptions.
6. **Adaptive Business Intelligence**: Automatically detecting domain features (e.g. Sales, Revenue, Quantity, Region, Payment) to calculate commercial KPIs or general statistical summaries.
7. **Multi-Format Executive Reporting**: Exporting cleaned datasets (CSV/Excel), a multi-sheet formatted workbook (`.xlsx`) via openpyxl, and a publication-quality executive summary (`.pdf`) via ReportLab.

---

## 🏗 Architecture & System Design

```
                                  ┌────────────────────────┐
                                  │   Raw Dataset Ingestion│ (.csv, .xlsx, .xls)
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │ Safe In-Memory Loader  │ (Multi-encoding fallback)
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │ Data Profiling Engine  │ ──► Data Quality Score (0-100%)
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │  Data Cleaning Engine  │
                                  │  - Duplicate Purging   │
                                  │  - Missing Imputation  │
                                  │  - Text Normalization  │
                                  │  - Date Standardization│
                                  │  - Numerical Bounds    │
                                  └───────────┬────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
          ┌────────────────────────┐                      ┌────────────────────────┐
          │ Domain Analytics Engine│                      │   Audit Trail Logger   │
          │ (Sales & General KPIs) │                      │ (Timestamp & Operation)│
          └───────────┬────────────┘                      └───────────┬────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │ Visualization Studio   │ (Plotly & Matplotlib)
                                  └───────────┬────────────┘
                                              │
                                              ▼
                        ┌───────────────────────────────────────────┐
                        │              Reporting Suite              │
                        │ ├── Cleaned CSV / Cleaned Excel           │
                        │ ├── Multi-Tab Styled Workbook (.xlsx)     │
                        │ └── Executive Visual Audit Report (.pdf)  │
                        └───────────────────────────────────────────┘
```

---

## 🛠 Technology Stack

- **Application & Dashboard UI**: Python 3.11+, [Streamlit](https://streamlit.io/)
- **Data Manipulation & Analysis**: [Pandas](https://pandas.pydata.org/), [NumPy](https://numpy.org/)
- **Interactive Visualizations**: [Plotly Express & Graph Objects](https://plotly.com/python/)
- **Static Publication Graphics**: [Matplotlib](https://matplotlib.org/) (Agg non-interactive backend)
- **Excel Report Automation**: [openpyxl](https://openpyxl.readthedocs.io/) (Zebra striping, freeze panes, number formats, embedded charts)
- **PDF Report Automation**: [ReportLab](https://www.reportlab.com/) (Flowables, numbered two-pass canvas, custom tables, embedded images)
- **Image Processing**: [Pillow (PIL)](https://pillow.readthedocs.io/)

---

## 🚀 Installation & Local Setup

### 1. Clone the Repository
```bash
git clone https://github.com/chapter-ranjeet/Data-Cleaning-and-Reporting-Automation.git
cd Data-Cleaning-and-Reporting-Automation
```

### 2. Set Up a Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
streamlit run app.py
```

The application will launch automatically in your browser at `http://localhost:8501`.

---

## 📁 Project Directory Structure

```text
DataClean-Pro/
│
├── app.py                     # Main Streamlit web application & UI navigation
├── requirements.txt           # Project dependencies
├── README.md                  # Comprehensive technical documentation
├── .gitignore                 # Standard Python & Streamlit ignore rules
├── test_pipeline.py           # End-to-end backend verification script
│
├── data/
│   ├── raw/
│   │   ├── sample_sales_data.csv    # 2,200 records with realistic data defects
│   │   └── generate_sample_data.py  # Synthetic realistic dataset generator
│   └── cleaned/                     # Destination for exported clean datasets
│
├── reports/
│   ├── excel/                 # Generated automated Excel reports (.xlsx)
│   ├── pdf/                   # Generated automated PDF reports (.pdf)
│   └── charts_temp/           # Rendered high-res PNG charts for report embedding
│
├── src/
│   ├── __init__.py            # Package initializer
│   ├── data_loader.py         # Multi-format CSV/Excel loader with encoding sniffing
│   ├── profiler.py            # Deep profiling engine & objective Quality Score
│   ├── data_cleaner.py        # Core modular data cleaning engine & audit logger
│   ├── validator.py           # Email, date, numerical anomaly, and semantic detection
│   ├── analyzer.py            # Domain-adaptive business KPIs and summary stats
│   ├── visualizer.py          # Interactive Plotly and static Matplotlib renderers
│   ├── excel_report.py        # 6-sheet corporate Excel generator (openpyxl)
│   ├── pdf_report.py          # Multi-page executive PDF generator (ReportLab)
│   └── utils.py               # Formatting, constants, and color palette tokens
│
└── assets/
    ├── logo.png               # High-resolution application brand logo
    └── generate_logo.py       # Programmatic PIL brand logo generator
```

---

## 🧹 Data Cleaning Techniques & Capabilities

| Module | Issue Detected | Automated Remediation Strategy |
| :--- | :--- | :--- |
| **Duplicates** | Exact duplicate records | Purges duplicate rows while preserving the first or last instance; tracks record counts. |
| **Missing Values (Numeric)** | Empty / NaN numeric entries | User-selectable: Median (skew-resistant), Mean, Mode, Zero, or Leave Unchanged. |
| **Missing Values (Categoric)** | Empty / NaN text entries | User-selectable: Canonical `"Unknown"`, Mode, or Leave Unchanged. |
| **Whitespace Normalization** | Leading/trailing spaces, double spaces | Trims whitespace and collapses multiple internal spaces without modifying IDs/emails. |
| **Casing Standardization** | Inconsistent capitalization (e.g. `KATHMANDU`, `kathmandu`) | Standardizes to Title Case, Lowercase, or Uppercase on categorical columns. |
| **Categorical Synonyms** | Variant values (e.g. `COD`, `wire`, `credit_card`) | Maps synonyms to canonical business values (`Cash on Delivery`, `Bank Transfer`, etc.). |
| **Numerical Validation** | Negative values in positive fields (Quantity, Price) | Automatically applies absolute value conversion; logs affected records. |
| **Outlier Treatment** | Extreme anomalies | Evaluates using IQR bounds ($Q_1 - 1.5 \times IQR$ to $Q_3 + 1.5 \times IQR$); option to winsorize or replace with median. |
| **Date Normalization** | Mixed date formats (`DD/MM/YYYY`, `YYYY.MM.DD`, `Mon DD, YYYY`) | Parses dates flexibly and standardizes to canonical `YYYY-MM-DD` ISO format. |
| **Email Validation** | Broken or malformed emails | Performs RFC-regex validation; separates valid, invalid, and missing counts. |
| **Data Safety** | Overwriting original files | Maintains `Raw Data` → `In-Memory Deep Copy` → `Cleaned Output`; original files are never altered. |

---

## 📊 Comprehensive Data Quality Score Formula

DataClean Pro computes an objective, multi-factor Data Quality Score ($0 - 100\%$):

$$\text{Data Quality Score} = (0.35 \times \text{Completeness}) + (0.25 \times \text{Uniqueness}) + (0.20 \times \text{Consistency}) + (0.20 \times \text{Validity})$$

- **Completeness ($35\%$)**: $100 \times \left(1 - \frac{\text{Missing Cells}}{\text{Total Cells}}\right)$
- **Uniqueness ($25\%$)**: $100 \times \left(1 - \frac{\text{Duplicate Rows}}{\text{Total Rows}}\right)$
- **Consistency ($20\%$)**: Percentage of columns free from trailing whitespaces or mixed casing.
- **Validity ($20\%$)**: Ratio of valid format checks across dates, emails, and non-negative bounds.

### Quality Tiers:
- **90% – 100%**: 🟢 *Excellent* (Enterprise certified)
- **75% – 89%**: 🔵 *Good* (Minor cleaning recommended)
- **60% – 74%**: 🟡 *Fair* (Notable hygiene issues detected)
- **40% – 59%**: 🟠 *Poor* (Substantial remediation required)
- **< 40%**: 🔴 *Critical* (Severe data integrity defects)

---

## 📑 Automated Reports

### 1. Automated Excel Report (`DataClean_Analysis_Report.xlsx`)
Generated using `openpyxl` with corporate styling:
- **Sheet 1: Executive Summary** — High-level KPI cards, before/after metrics, business significance.
- **Sheet 2: Data Quality** — Column-level profile, missing percentage, unique counts, identified defects.
- **Sheet 3: Cleaned Data** — Complete sanitized dataset with navy headers, zebra striping, freeze panes, and auto-adjusted column widths.
- **Sheet 4: Cleaning Log** — Comprehensive forensic audit trail of all transformations.
- **Sheet 5: Statistics** — Descriptive statistics for numerical and categorical features.
- **Sheet 6: Charts** — High-resolution graphical charts embedded directly into the worksheet.

### 2. Automated PDF Report (`DataClean_Analysis_Report.pdf`)
Generated using `ReportLab`:
- Executive cover with document metadata and timestamps.
- Before/After quality transformation matrix.
- Feature quality & anomaly diagnostics table.
- Automated cleaning operations audit trail.
- Commercial sales KPIs (Total Revenue, AOV, Orders, Quantity) or generic statistical summaries.
- Embedded high-resolution graphics (Revenue trends, Category performance, Regional breakdown, Top products).
- Executive audit conclusion and two-pass `"Page X of Y"` numbered canvas.

---

## 🧪 Realistic Sample Dataset

The included demo dataset (`data/raw/sample_sales_data.csv`) contains **2,200 records** and **12 columns** with realistic real-world data flaws:
- **Duplicate rows**: 50 duplicate transactions.
- **Missing values**: 796 empty cells across multiple columns.
- **Inconsistent casing & whitespace**: Leading spaces, all-caps, and mixed casing.
- **Invalid dates & mixed formats**: Unparseable dates (`2024-02-31`, `invalid_date`), mixed formats (`DD/MM/YYYY`, `YYYY.MM.DD`).
- **Invalid emails**: Malformed addresses (`name@com`, `missing_domain@`).
- **Negative values**: Negative quantities and unit prices.
- **Categorical variants**: Non-standard payment methods (`cc`, `wire`, `COD`).

You can load this sample dataset with a single click in the UI via the **"Try Demo Dataset"** button.

---

## 🔮 Future Improvements

- [ ] Direct database connectors (PostgreSQL, MySQL, Snowflake, BigQuery).
- [ ] Automated regex rule builder for custom domain-specific column patterns.
- [ ] Machine learning-based anomaly detection (Isolation Forests, One-Class SVM).
- [ ] Scheduled background automation via cron/watchdog folder monitoring.
- [ ] Export directly to cloud storage (AWS S3, Google Cloud Storage, Azure Blob).

---

## 👤 Author & Project Attribution

**Developed as a Data Science Internship Project**  
*Project Title: Data Cleaning & Reporting Automation*  
*Application: DataClean Pro*  
*License: MIT*
