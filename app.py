"""
DataClean Pro - Automated Data Cleaning & Reporting Platform
Main Streamlit Application.
"""

from datetime import datetime
import io
import os
import pandas as pd
import streamlit as st

# Configure Streamlit Page
st.set_page_config(
    page_title="DataClean Pro — Automated Data Cleaning & Reporting",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import internal modular components
from src.analyzer import DataAnalyzer
from src.data_cleaner import CleaningConfig, DataCleaner
from src.data_loader import DataLoader
from src.excel_report import ExcelReportGenerator
from src.pdf_report import PDFReportGenerator
from src.profiler import DataProfiler
from src.utils import THEME_COLORS, format_bytes, format_currency, format_number
from src.visualizer import Visualizer

# -----------------------------------------------------------------------------
# CUSTOM CSS STYLING FOR MODERN DASHBOARD AESTHETICS
# -----------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Top Brand Banner */
    .brand-container {
        padding: 18px 24px;
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #2563EB 100%);
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px -2px rgba(30, 58, 138, 0.25);
    }
    .brand-title {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .brand-badge {
        background-color: #38BDF8;
        color: #0F172A;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }
    .brand-subtitle {
        font-size: 13px;
        color: #CBD5E1;
        margin-top: 4px;
        margin-bottom: 8px;
    }
    .pipeline-pills {
        display: flex;
        gap: 10px;
        margin-top: 10px;
    }
    .pill {
        background: rgba(255, 255, 255, 0.12);
        backdrop-filter: blur(8px);
        padding: 4px 14px;
        border-radius: 20px;
        font-size: 11.5px;
        font-weight: 500;
        color: #F8FAFC;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .pill.active {
        background: #38BDF8;
        color: #0F172A;
        font-weight: 600;
        border-color: #38BDF8;
    }

    /* KPI Card Style */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px -2px rgba(0, 0, 0, 0.08);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
    }
    .kpi-delta {
        font-size: 12px;
        margin-top: 4px;
        font-weight: 500;
    }
    .delta-positive { color: #10B981; }
    .delta-negative { color: #EF4444; }
    .delta-neutral { color: #64748B; }

    /* Quality Score Banner */
    .quality-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .score-progress-bg {
        background: #E2E8F0;
        border-radius: 8px;
        height: 12px;
        width: 100%;
        overflow: hidden;
        margin: 10px 0;
    }
    .score-progress-bar {
        height: 100%;
        border-radius: 8px;
        transition: width 0.4s ease;
    }

    /* Section Cards */
    .content-box {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 24px;
    }

    /* Dataframe Table styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }

    /* Custom button enhancements */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "raw_df" not in st.session_state:
    st.session_state.raw_df = None
if "cleaned_df" not in st.session_state:
    st.session_state.cleaned_df = None
if "cleaning_log_df" not in st.session_state:
    st.session_state.cleaning_log_df = None
if "raw_profile" not in st.session_state:
    st.session_state.raw_profile = None
if "clean_profile" not in st.session_state:
    st.session_state.clean_profile = None
if "file_metadata" not in st.session_state:
    st.session_state.file_metadata = None
if "summary_stats" not in st.session_state:
    st.session_state.summary_stats = None
if "analytics_report" not in st.session_state:
    st.session_state.analytics_report = None
if "chart_paths" not in st.session_state:
    st.session_state.chart_paths = {}
if "excel_path" not in st.session_state:
    st.session_state.excel_path = None
if "pdf_path" not in st.session_state:
    st.session_state.pdf_path = None

# -----------------------------------------------------------------------------
# HELPER FUNCTIONS FOR APP STATE
# -----------------------------------------------------------------------------
def load_new_dataset(file_source, file_name=None):
    """Load, profile, and update session state safely."""
    with st.spinner("Analyzing and profiling dataset..."):
        df, meta, err = DataLoader.load_dataset(file_source, file_name=file_name)
        if err:
            st.error(err)
            return False

        st.session_state.raw_df = df
        st.session_state.cleaned_df = None
        st.session_state.cleaning_log_df = None
        st.session_state.clean_profile = None
        st.session_state.file_metadata = meta
        st.session_state.summary_stats = None
        st.session_state.analytics_report = None
        st.session_state.chart_paths = {}
        st.session_state.excel_path = None
        st.session_state.pdf_path = None

        # Profile raw data immediately
        st.session_state.raw_profile = DataProfiler.profile_dataset(df)
        return True

def trigger_clean_pipeline(config: CleaningConfig):
    """Execute cleaning, re-profile, compute analytics, and generate reports."""
    if st.session_state.raw_df is None:
        return

    with st.spinner("Executing automated cleaning pipeline and generating audit trail..."):
        cleaned, log_df, stats = DataCleaner.clean_dataset(st.session_state.raw_df, config)
        st.session_state.cleaned_df = cleaned
        st.session_state.cleaning_log_df = log_df
        st.session_state.summary_stats = stats

        # Profile cleaned data
        st.session_state.clean_profile = DataProfiler.profile_dataset(cleaned)

        # Run domain analytics
        analytics = DataAnalyzer.analyze_dataset(cleaned)
        st.session_state.analytics_report = analytics

        # Generate static charts for PDF and Excel
        chart_dir = "reports/charts_temp"
        chart_paths = Visualizer.generate_static_charts(cleaned, analytics, chart_dir)
        st.session_state.chart_paths = chart_paths

        # Generate reports in background
        excel_file = "reports/excel/DataClean_Analysis_Report.xlsx"
        ExcelReportGenerator.generate_report(
            cleaned_df=cleaned,
            cleaning_log_df=log_df,
            raw_profile=st.session_state.raw_profile,
            clean_profile=st.session_state.clean_profile,
            analytics=analytics,
            chart_image_paths=chart_paths,
            output_file_path=excel_file
        )
        st.session_state.excel_path = excel_file

        pdf_file = "reports/pdf/DataClean_Analysis_Report.pdf"
        PDFReportGenerator.generate_report(
            cleaned_df=cleaned,
            cleaning_log_df=log_df,
            raw_profile=st.session_state.raw_profile,
            clean_profile=st.session_state.clean_profile,
            analytics=analytics,
            chart_image_paths=chart_paths,
            output_file_path=pdf_file
        )
        st.session_state.pdf_path = pdf_file

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("assets/logo.png", use_container_width=True)
    st.markdown("---")

    selected_page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "📂 Upload Dataset",
            "🧹 Data Cleaning",
            "📊 Analytics",
            "📈 Visualizations",
            "📑 Reports",
            "⚙️ Settings"
        ],
        index=0
    )

    st.markdown("---")
    # Dataset Status Card in Sidebar
    if st.session_state.raw_df is not None:
        st.markdown("#### 📁 Active Dataset")
        meta = st.session_state.file_metadata
        st.markdown(f"**File:** `{meta.file_name}`")
        st.markdown(f"**Size:** {meta.file_size_formatted} ({meta.file_type})")
        st.markdown(f"**Raw Rows:** {meta.row_count:,}")
        st.markdown(f"**Columns:** {meta.column_count}")

        if st.session_state.cleaned_df is not None:
            st.success(f" Cleaned: {len(st.session_state.cleaned_df):,} rows")
            raw_score = st.session_state.raw_profile.quality_score.overall_score
            clean_score = st.session_state.clean_profile.quality_score.overall_score
            st.metric("Quality Score", f"{clean_score}%", delta=f"{round(clean_score - raw_score, 1)}%")
        else:
            raw_score = st.session_state.raw_profile.quality_score.overall_score
            st.info(f"⚡ Raw Score: {raw_score}%")
    else:
        st.info("ℹ No dataset loaded yet. Upload a file or launch the demo dataset to begin.")

    st.markdown("---")
    st.caption("DataClean Pro v1.0\n\nDeveloped as a Data Science Internship Project")

# -----------------------------------------------------------------------------
# MAIN HEADER BANNER
# -----------------------------------------------------------------------------
has_raw = st.session_state.raw_df is not None
has_clean = st.session_state.cleaned_df is not None
has_analytics = st.session_state.analytics_report is not None
has_reports = st.session_state.excel_path is not None

st.markdown(f"""
<div class="brand-container">
    <div class="brand-title">
        <span>DataClean Pro</span>
        <span class="brand-badge">Automated Engine</span>
    </div>
    <div class="brand-subtitle">Automated Data Cleaning, Profiling & Business Intelligence Reporting Platform</div>
    <div class="pipeline-pills">
        <span class="pill {'active' if has_raw else ''}">1. Upload {'✓' if has_raw else ''}</span>
        <span class="pill {'active' if has_clean else ''}">2. Clean {'✓' if has_clean else ''}</span>
        <span class="pill {'active' if has_analytics else ''}">3. Analyze {'✓' if has_analytics else ''}</span>
        <span class="pill {'active' if has_reports else ''}">4. Report {'✓' if has_reports else ''}</span>
    </div>
</div>
""", unsafe_allow_html=True)


# =============================================================================
# 1. PAGE: DASHBOARD
# =============================================================================
if selected_page == "🏠 Dashboard":
    st.subheader("System Overview & Quality Health")

    if st.session_state.raw_df is None:
        st.markdown("""
        <div class="content-box" style="text-align: center; padding: 40px 20px;">
            <h3 style="color: #1E3A8A; margin-bottom: 10px;">Welcome to DataClean Pro</h3>
            <p style="color: #64748B; max-width: 650px; margin: 0 auto 24px auto;">
                DataClean Pro automates the entire tabular data lifecycle: ingest messy CSV/Excel datasets,
                diagnose formatting defects, impute missing entries, remove duplicates, and generate publication-quality
                Excel and PDF reports with embedded charts.
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("#### Get Started Immediately")
            if st.button("🚀 Load Sample Sales Dataset (2,200 records)", use_container_width=True, type="primary"):
                demo_path = "data/raw/sample_sales_data.csv"
                if os.path.exists(demo_path):
                    success = load_new_dataset(demo_path, "sample_sales_data.csv")
                    if success:
                        st.success("Sample Sales Dataset loaded successfully! Redirecting...")
                        st.rerun()
                else:
                    st.error("Demo dataset file not found at data/raw/sample_sales_data.csv")
    else:
        # Display Dashboard Metrics
        raw_p = st.session_state.raw_profile
        clean_p = st.session_state.clean_profile

        # Metric Cards Row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            total_r = clean_p.total_rows if clean_p else raw_p.total_rows
            delta_r = f"-{raw_p.total_rows - clean_p.total_rows} dupes" if clean_p else "Input count"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Records</div>
                <div class="kpi-value">{total_r:,}</div>
                <div class="kpi-delta delta-neutral">{delta_r}</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            missing_c = clean_p.total_missing_cells if clean_p else raw_p.total_missing_cells
            delta_m = f"Imputed {raw_p.total_missing_cells - missing_c:,} cells" if clean_p else f"{raw_p.missing_cells_pct}% missing"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Missing Cells</div>
                <div class="kpi-value">{missing_c:,}</div>
                <div class="kpi-delta {'delta-positive' if missing_c == 0 else 'delta-negative'}">{delta_m}</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            dupes = clean_p.total_duplicate_rows if clean_p else raw_p.total_duplicate_rows
            delta_d = "100% purged" if clean_p and dupes == 0 else f"{raw_p.total_duplicate_rows} detected"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Duplicate Rows</div>
                <div class="kpi-value">{dupes:,}</div>
                <div class="kpi-delta {'delta-positive' if dupes == 0 else 'delta-negative'}">{delta_d}</div>
            </div>
            """, unsafe_allow_html=True)

        with c4:
            score = clean_p.quality_score.overall_score if clean_p else raw_p.quality_score.overall_score
            grade = clean_p.quality_score.grade if clean_p else raw_p.quality_score.grade
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Data Quality Score</div>
                <div class="kpi-value" style="color: {clean_p.quality_score.grade_color if clean_p else raw_p.quality_score.grade_color};">{score}%</div>
                <div class="kpi-delta delta-positive">{grade} Tier</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Quality Score Gauge & Breakdown
        col_gauge, col_breakdown = st.columns([1.2, 2])
        with col_gauge:
            current_score = clean_p.quality_score.overall_score if clean_p else raw_p.quality_score.overall_score
            fig_gauge = Visualizer.plot_quality_gauge(current_score)
            st.plotly_chart(fig_gauge, use_container_width=True)

        with col_breakdown:
            st.markdown("#### Quality Dimension Breakdown")
            q_info = clean_p.quality_score if clean_p else raw_p.quality_score
            
            # 4 Dimension Progress Bars
            st.write(f"**Completeness:** {q_info.completeness_score}%")
            st.progress(q_info.completeness_score / 100.0)

            st.write(f"**Uniqueness:** {q_info.uniqueness_score}%")
            st.progress(q_info.uniqueness_score / 100.0)

            st.write(f"**Consistency:** {q_info.consistency_score}%")
            st.progress(q_info.consistency_score / 100.0)

            st.write(f"**Validity:** {q_info.validity_score}%")
            st.progress(q_info.validity_score / 100.0)

            st.caption(f"Status: {q_info.summary_text}")

        # Quick Actions Callout
        st.markdown("---")
        if not clean_p:
            st.info("💡 Your dataset is profiled. Navigate to **🧹 Data Cleaning** to customize cleaning strategies or execute one-click automated cleaning.")
            if st.button("⚡ Run One-Click Automated Cleaning Now", type="primary"):
                trigger_clean_pipeline(CleaningConfig())
                st.success("Automated cleaning pipeline completed successfully!")
                st.rerun()
        else:
            st.success("🎉 Dataset has been cleaned and verified! Explore **📊 Analytics**, **📈 Visualizations**, or download your **📑 Reports**.")


# =============================================================================
# 2. PAGE: UPLOAD DATASET
# =============================================================================
elif selected_page == "📂 Upload Dataset":
    st.subheader("Dataset Ingestion & Inspection")

    col_up, col_demo = st.columns([2.5, 1])
    with col_up:
        uploaded_file = st.file_uploader(
            "Upload tabular data (.csv, .xlsx, .xls)",
            type=["csv", "xlsx", "xls"],
            help="Files are loaded safely into an isolated in-memory copy without altering original disk files."
        )
        if uploaded_file is not None:
            if st.session_state.file_metadata is None or st.session_state.file_metadata.file_name != uploaded_file.name:
                success = load_new_dataset(uploaded_file)
                if success:
                    st.success(f"Successfully loaded '{uploaded_file.name}'!")
                    st.rerun()

    with col_demo:
        st.markdown("#### Or Try Sample Dataset")
        st.caption("Load a 2,200-row realistic sales dataset containing deliberate real-world defects to test all features.")
        if st.button("🚀 Load Sample Sales Data", use_container_width=True):
            demo_path = "data/raw/sample_sales_data.csv"
            if os.path.exists(demo_path):
                success = load_new_dataset(demo_path, "sample_sales_data.csv")
                if success:
                    st.success("Loaded sample dataset!")
                    st.rerun()

    if st.session_state.raw_df is not None:
        st.markdown("---")
        meta = st.session_state.file_metadata
        st.markdown("### Dataset Overview & Metadata")

        # Metadata Row
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Rows", f"{meta.row_count:,}")
        m2.metric("Columns", meta.column_count)
        m3.metric("File Size", meta.file_size_formatted)
        m4.metric("Memory Usage", meta.memory_usage_formatted)
        m5.metric("File Type", meta.file_type)

        st.markdown("#### Dataset Preview (First 15 Rows)")
        st.dataframe(st.session_state.raw_df.head(15), use_container_width=True)

        st.markdown("#### Column Diagnostics & Profiling")
        # Build profile summary table
        col_rows = []
        for col_name, cp in st.session_state.raw_profile.column_profiles.items():
            issues_str = "; ".join(cp.quality_issues) if cp.quality_issues else "None (Clean)"
            col_rows.append({
                "Column Name": col_name,
                "Inferred Type": cp.inferred_type,
                "Data Type": cp.dtype,
                "Non-Null": cp.non_null_count,
                "Missing": cp.null_count,
                "Missing %": f"{cp.null_percentage}%",
                "Unique Values": cp.unique_count,
                "Issues Detected": issues_str
            })
        st.dataframe(pd.DataFrame(col_rows), use_container_width=True)


# =============================================================================
# 3. PAGE: DATA CLEANING
# =============================================================================
elif selected_page == "🧹 Data Cleaning":
    st.subheader("Data Cleaning Engine & Strategy Configuration")

    if st.session_state.raw_df is None:
        st.warning("⚠ Please upload a dataset or click 'Load Sample Sales Data' first.")
    else:
        raw_p = st.session_state.raw_profile
        st.markdown(f"Configuring cleaning parameters for **{st.session_state.file_metadata.file_name}** ({raw_p.total_rows:,} rows, {raw_p.total_columns} columns)")

        with st.form("cleaning_config_form"):
            c_left, c_right = st.columns(2)

            with c_left:
                st.markdown("#### 1. Missing Value Strategy")
                num_strategy = st.radio(
                    "Missing Numerical Values",
                    options=["median", "mean", "mode", "zero", "leave_unchanged"],
                    format_func=lambda x: {
                        "median": "● Median (Recommended for skewed data)",
                        "mean": "○ Mean (Average)",
                        "mode": "○ Mode (Most frequent)",
                        "zero": "○ Constant Zero (0)",
                        "leave_unchanged": "○ Leave unchanged"
                    }[x],
                    index=0
                )

                cat_strategy = st.radio(
                    "Missing Categorical Values",
                    options=["unknown", "mode", "leave_unchanged"],
                    format_func=lambda x: {
                        "unknown": "● Fill with 'Unknown'",
                        "mode": "○ Most frequent Category (Mode)",
                        "leave_unchanged": "○ Leave unchanged"
                    }[x],
                    index=0
                )

                st.markdown("#### 2. Duplicate Handling")
                st.info(f"Duplicate Records Found: **{raw_p.total_duplicate_rows}**")
                remove_dupes = st.checkbox("Remove Duplicate Rows", value=True)
                dupe_keep = st.selectbox("Duplicate Retention Rule", options=["first", "last"], index=0, format_func=lambda x: f"Keep {x} instance")

            with c_right:
                st.markdown("#### 3. Text Standardization")
                strip_spaces = st.checkbox("Strip leading & trailing whitespace", value=True)
                collapse_spaces = st.checkbox("Collapse multiple internal spaces", value=True)
                casing = st.selectbox(
                    "Text Casing Normalization",
                    options=["title", "lower", "upper", "preserve"],
                    index=0,
                    format_func=lambda x: {
                        "title": "Title Case (e.g. 'Kathmandu', 'Ergonomic Chair')",
                        "lower": "lowercase (e.g. 'kathmandu')",
                        "upper": "UPPERCASE (e.g. 'KATHMANDU')",
                        "preserve": "Preserve existing casing (Trim only)"
                    }[x]
                )
                standardize_synonyms = st.checkbox("Standardize categorical synonyms (e.g., COD/wire -> canonical)", value=True)

                st.markdown("#### 4. Numerical & Date Validation")
                std_dates = st.checkbox("Standardize dates to YYYY-MM-DD", value=True)
                fix_negatives = st.checkbox("Fix negative values in positive fields (Quantity, Price)", value=True)
                outlier_opt = st.selectbox(
                    "Outlier Handling (IQR Rule)",
                    options=["flag_only", "cap_iqr", "replace_median"],
                    index=0,
                    format_func=lambda x: {
                        "flag_only": "Flag potential outliers (Do not modify)",
                        "cap_iqr": "Winsorize (Cap at 1.5 * IQR bounds)",
                        "replace_median": "Replace outliers with column median"
                    }[x]
                )

            submit_clean = st.form_submit_button("🚀 Run Automated Cleaning Pipeline", type="primary", use_container_width=True)

        if submit_clean:
            cfg = CleaningConfig(
                remove_duplicates=remove_dupes,
                duplicate_keep_strategy=dupe_keep,
                num_missing_strategy=num_strategy,
                cat_missing_strategy=cat_strategy,
                strip_whitespace=strip_spaces,
                normalize_internal_spaces=collapse_spaces,
                casing_strategy=casing,
                standardize_known_categories=standardize_synonyms,
                standardize_dates=std_dates,
                fix_negative_values=fix_negatives,
                outlier_strategy=outlier_opt
            )
            trigger_clean_pipeline(cfg)
            st.success("Cleaning operations completed successfully! Audit log and reports generated.")
            st.rerun()

        # Display Cleaning Results & Summary if available
        if st.session_state.cleaned_df is not None:
            st.markdown("---")
            st.markdown("### 📊 Cleaning Summary: Before vs. After")

            clean_p = st.session_state.clean_profile
            sum_stats = st.session_state.summary_stats

            # Before / After Comparison Cards
            cmp1, cmp2, cmp3, cmp4 = st.columns(4)
            with cmp1:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Rows Before / After</div>
                    <div class="kpi-value">{raw_p.total_rows:,} → {clean_p.total_rows:,}</div>
                    <div class="kpi-delta delta-positive">-{sum_stats['records_removed']} duplicates removed</div>
                </div>
                """, unsafe_allow_html=True)
            with cmp2:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Missing Cells</div>
                    <div class="kpi-value">{raw_p.total_missing_cells:,} → {clean_p.total_missing_cells:,}</div>
                    <div class="kpi-delta delta-positive">{sum_stats['missing_cells_imputed']} cells imputed</div>
                </div>
                """, unsafe_allow_html=True)
            with cmp3:
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Duplicates Remaining</div>
                    <div class="kpi-value">{raw_p.total_duplicate_rows:,} → {clean_p.total_duplicate_rows:,}</div>
                    <div class="kpi-delta delta-positive">100% duplicate elimination</div>
                </div>
                """, unsafe_allow_html=True)
            with cmp4:
                raw_s = raw_p.quality_score.overall_score
                cln_s = clean_p.quality_score.overall_score
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-title">Quality Score</div>
                    <div class="kpi-value" style="color: {clean_p.quality_score.grade_color};">{raw_s}% → {cln_s}%</div>
                    <div class="kpi-delta delta-positive">+{round(cln_s - raw_s, 1)}% improvement</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br/>", unsafe_allow_html=True)
            st.markdown("#### 📋 Detailed Cleaning Operations Audit Log")
            st.dataframe(st.session_state.cleaning_log_df, use_container_width=True)

            # CSV Download for Cleaning Log
            log_csv = st.session_state.cleaning_log_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Download Cleaning Audit Log (CSV)",
                data=log_csv,
                file_name="cleaning_audit_log.csv",
                mime="text/csv"
            )


# =============================================================================
# 4. PAGE: ANALYTICS
# =============================================================================
elif selected_page == "📊 Analytics":
    st.subheader("Statistical & Domain Analytics Dashboard")

    target_df = st.session_state.cleaned_df if st.session_state.cleaned_df is not None else st.session_state.raw_df

    if target_df is None:
        st.warning("⚠ Please upload or load a dataset first.")
    else:
        # Run or fetch analytics
        if st.session_state.analytics_report is None:
            st.session_state.analytics_report = DataAnalyzer.analyze_dataset(target_df)
        
        rep = st.session_state.analytics_report

        if rep.is_sales_domain and rep.sales_kpis:
            sales = rep.sales_kpis
            st.markdown("#### 🛍 Commercial Sales Key Performance Indicators")
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Revenue", sales.total_revenue_formatted)
            s2.metric("Average Order Value (AOV)", sales.avg_order_value_formatted)
            s3.metric("Total Units Sold", sales.total_quantity_formatted)
            s4.metric("Verified Orders", sales.total_orders_formatted)

            st.markdown("---")
            # Revenue Trend Full Width
            st.markdown("#### 📈 Revenue Trend Over Time")
            fig_trend = Visualizer.plot_monthly_revenue_trend(sales.monthly_revenue_trend)
            st.plotly_chart(fig_trend, use_container_width=True)

            # Category and Region Rows
            col_cat, col_reg = st.columns(2)
            with col_cat:
                fig_cat = Visualizer.plot_category_performance(sales.revenue_by_category)
                st.plotly_chart(fig_cat, use_container_width=True)
            with col_reg:
                fig_reg = Visualizer.plot_regional_performance(sales.revenue_by_region)
                st.plotly_chart(fig_reg, use_container_width=True)

            # Products and Payment Rows
            col_prod, col_pay = st.columns(2)
            with col_prod:
                fig_prod = Visualizer.plot_top_products(sales.top_products_by_revenue)
                st.plotly_chart(fig_prod, use_container_width=True)
            with col_pay:
                fig_pay = Visualizer.plot_payment_distribution(sales.payment_method_distribution)
                st.plotly_chart(fig_pay, use_container_width=True)

        st.markdown("---")
        st.markdown("#### 🔢 Numerical Descriptive Statistics")
        if rep.generic_kpis and not rep.generic_kpis.summary_statistics.empty:
            st.dataframe(rep.generic_kpis.summary_statistics, use_container_width=True)

        # Correlation Heatmap
        if rep.generic_kpis and rep.generic_kpis.correlation_matrix is not None:
            st.markdown("#### 🔗 Feature Correlation Heatmap")
            fig_corr = Visualizer.plot_correlation_heatmap(rep.generic_kpis.correlation_matrix)
            st.plotly_chart(fig_corr, use_container_width=True)


# =============================================================================
# 5. PAGE: VISUALIZATIONS
# =============================================================================
elif selected_page == "📈 Visualizations":
    st.subheader("Interactive Visual Analytics Studio")

    target_df = st.session_state.cleaned_df if st.session_state.cleaned_df is not None else st.session_state.raw_df

    if target_df is None:
        st.warning("⚠ Please upload or load a dataset first.")
    else:
        num_cols = [c for c in target_df.columns if pd.api.types.is_numeric_dtype(target_df[c])]
        cat_cols = [c for c in target_df.columns if not pd.api.types.is_numeric_dtype(target_df[c])]

        tab_num, tab_cat, tab_rel = st.tabs(["📊 Numeric Distributions", "🍩 Categorical Breakdown", "🔍 Relationship & Scatter"])

        with tab_num:
            if num_cols:
                col_sel = st.selectbox("Select Numeric Column to Inspect", options=num_cols, index=0)
                v1, v2 = st.columns(2)
                with v1:
                    fig_hist = Visualizer.plot_histogram_distribution(target_df, col_sel)
                    st.plotly_chart(fig_hist, use_container_width=True)
                with v2:
                    cat_group = st.selectbox("Group by Category (Optional)", options=["None"] + cat_cols, index=0)
                    chosen_cat = cat_group if cat_group != "None" else None
                    fig_box = Visualizer.plot_box_distribution(target_df, col_sel, chosen_cat)
                    st.plotly_chart(fig_box, use_container_width=True)
            else:
                st.info("No numerical columns detected.")

        with tab_cat:
            if cat_cols:
                c_sel = st.selectbox("Select Categorical Column", options=cat_cols, index=0)
                counts = target_df[c_sel].value_counts().head(10).to_dict()
                v3, v4 = st.columns(2)
                with v3:
                    fig_bar = Visualizer.plot_category_performance(counts)
                    st.plotly_chart(fig_bar, use_container_width=True)
                with v4:
                    fig_donut = Visualizer.plot_regional_performance(counts)
                    st.plotly_chart(fig_donut, use_container_width=True)
            else:
                st.info("No categorical columns detected.")

        with tab_rel:
            if len(num_cols) >= 2:
                r1, r2, r3 = st.columns(3)
                with r1:
                    x_axis = st.selectbox("X-Axis", options=num_cols, index=0)
                with r2:
                    y_axis = st.selectbox("Y-Axis", options=num_cols, index=min(1, len(num_cols) - 1))
                with r3:
                    color_dim = st.selectbox("Color Dimension (Optional)", options=["None"] + cat_cols, index=0)
                    c_dim = color_dim if color_dim != "None" else None

                fig_scatter = Visualizer.plot_scatter_relationship(target_df, x_axis, y_axis, c_dim)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Need at least 2 numerical columns for scatter plot.")


# =============================================================================
# 6. PAGE: REPORTS
# =============================================================================
elif selected_page == "📑 Reports":
    st.subheader("Executive Download & Reports Center")

    if st.session_state.raw_df is None:
        st.warning("⚠ Please upload or load a dataset first.")
    else:
        if st.session_state.cleaned_df is None:
            st.info("💡 You can download the reports after running the cleaning pipeline. Click below to generate reports now:")
            if st.button("⚡ Clean & Generate All Reports", type="primary"):
                trigger_clean_pipeline(CleaningConfig())
                st.rerun()
        else:
            st.success("✅ Cleaned dataset, audit logs, and executive reports are ready for download!")

            r1, r2 = st.columns(2)

            with r1:
                st.markdown("""
                <div class="content-box">
                    <h4 style="color: #1E3A8A; margin-bottom: 8px;">📊 Automated Excel Report</h4>
                    <p style="color: #64748B; font-size: 13px; margin-bottom: 16px;">
                        Professional multi-tab workbook (.xlsx) including Executive Summary, Data Quality,
                        Cleaned Data, Audit Trail, Statistics, and Embedded Graphical Charts.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.session_state.excel_path and os.path.exists(st.session_state.excel_path):
                    with open(st.session_state.excel_path, "rb") as f:
                        excel_bytes = f.read()
                    st.download_button(
                        label="📥 Download Excel Report (.xlsx)",
                        data=excel_bytes,
                        file_name="DataClean_Analysis_Report.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="primary"
                    )

                st.markdown("<br/>", unsafe_allow_html=True)

                st.markdown("""
                <div class="content-box">
                    <h4 style="color: #0D9488; margin-bottom: 8px;">📁 Cleaned Dataset Exports</h4>
                    <p style="color: #64748B; font-size: 13px; margin-bottom: 16px;">
                        Export the sanitized, normalized, and validated dataset in standard CSV or Excel formats.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                c_csv = st.session_state.cleaned_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download Cleaned Dataset (CSV)",
                    data=c_csv,
                    file_name="cleaned_dataset.csv",
                    mime="text/csv",
                    use_container_width=True
                )

                # Cleaned Excel
                excel_buffer = io.BytesIO()
                st.session_state.cleaned_df.to_excel(excel_buffer, index=False, engine="openpyxl")
                st.download_button(
                    label="📥 Download Cleaned Dataset (Excel)",
                    data=excel_buffer.getvalue(),
                    file_name="cleaned_dataset.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

            with r2:
                st.markdown("""
                <div class="content-box">
                    <h4 style="color: #1E3A8A; margin-bottom: 8px;">📑 Automated PDF Report</h4>
                    <p style="color: #64748B; font-size: 13px; margin-bottom: 16px;">
                        Publication-quality multi-page PDF document generated with ReportLab. Contains executive cover,
                        before/after KPI matrices, audit trail, embedded charts, and quality certification.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                    with open(st.session_state.pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    st.download_button(
                        label="📥 Download PDF Audit Report (.pdf)",
                        data=pdf_bytes,
                        file_name="DataClean_Analysis_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )

                st.markdown("<br/>", unsafe_allow_html=True)

                st.markdown("""
                <div class="content-box">
                    <h4 style="color: #2563EB; margin-bottom: 8px;">📋 Audit Trail & Cleaning Log</h4>
                    <p style="color: #64748B; font-size: 13px; margin-bottom: 16px;">
                        Complete forensic record of all algorithmic modifications, affected records, and timestamps.
                    </p>
                </div>
                """, unsafe_allow_html=True)

                if st.session_state.cleaning_log_df is not None:
                    log_csv = st.session_state.cleaning_log_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Download Cleaning Audit Log (CSV)",
                        data=log_csv,
                        file_name="cleaning_log.csv",
                        mime="text/csv",
                        use_container_width=True
                    )


# =============================================================================
# 7. PAGE: SETTINGS
# =============================================================================
elif selected_page == "⚙️ Settings":
    st.subheader("Platform Settings & Engine Information")

    st.markdown("""
    <div class="content-box">
        <h4 style="color: #1E3A8A; margin-bottom: 10px;">DataClean Pro Engine Specifications</h4>
        <table style="width: 100%; border-collapse: collapse; font-size: 13.5px;">
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; width: 220px; color: #475569;">Application Version</td>
                <td style="color: #0F172A;">1.0.0 (Production Release)</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; color: #475569;">Core Framework</td>
                <td style="color: #0F172A;">Python 3.11+ / Streamlit 1.35+</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; color: #475569;">Data Processing</td>
                <td style="color: #0F172A;">Pandas, NumPy</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; color: #475569;">Visualizations</td>
                <td style="color: #0F172A;">Plotly Express, Matplotlib</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; color: #475569;">Report Engines</td>
                <td style="color: #0F172A;">openpyxl (Excel), ReportLab (PDF)</td>
            </tr>
            <tr style="border-bottom: 1px solid #E2E8F0; height: 36px;">
                <td style="font-weight: 600; color: #475569;">Execution Mode</td>
                <td style="color: #10B981; font-weight: 600;">Isolated In-Memory Non-Destructive Copy</td>
            </tr>
            <tr style="height: 36px;">
                <td style="font-weight: 600; color: #475569;">Project Scope</td>
                <td style="color: #0F172A;">Data Science Internship Project: "Data Cleaning & Reporting Automation"</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("#### Engine Diagnostics & Memory")
    if st.session_state.raw_df is not None:
        st.write(f"**Loaded Dataset:** `{st.session_state.file_metadata.file_name}`")
        st.write(f"**Raw Dimensions:** {st.session_state.raw_df.shape[0]:,} rows × {st.session_state.raw_df.shape[1]} columns")
        if st.session_state.cleaned_df is not None:
            st.write(f"**Cleaned Dimensions:** {st.session_state.cleaned_df.shape[0]:,} rows × {st.session_state.cleaned_df.shape[1]} columns")
        if st.button("🗑 Reset Session & Clear In-Memory Data"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session reset. Redirecting...")
            st.rerun()
    else:
        st.info("No active dataset in memory.")
