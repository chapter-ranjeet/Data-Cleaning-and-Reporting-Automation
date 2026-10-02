"""
End-to-End Pipeline Verification Script for DataClean Pro.
Validates loading, profiling, cleaning, analyzing, chart generation, Excel and PDF reports.
"""

import os
import sys

from src.data_loader import DataLoader
from src.profiler import DataProfiler
from src.data_cleaner import DataCleaner, CleaningConfig
from src.analyzer import DataAnalyzer
from src.visualizer import Visualizer
from src.excel_report import ExcelReportGenerator
from src.pdf_report import PDFReportGenerator

def test_pipeline():
    sample_csv = "data/raw/sample_sales_data.csv"
    print(f"1. Loading dataset: {sample_csv}")
    df_raw, metadata, err = DataLoader.load_dataset(sample_csv)
    if err:
        print(f"Error loading: {err}")
        return False
    print(f"   Loaded: {metadata.row_count} rows, {metadata.column_count} columns, size: {metadata.file_size_formatted}")

    print("2. Profiling raw dataset...")
    raw_profile = DataProfiler.profile_dataset(df_raw)
    print(f"   Raw Quality Score: {raw_profile.quality_score.overall_score}% ({raw_profile.quality_score.grade})")
    print(f"   Duplicates: {raw_profile.total_duplicate_rows}, Missing cells: {raw_profile.total_missing_cells}")

    print("3. Executing Cleaning Engine...")
    config = CleaningConfig(
        remove_duplicates=True,
        duplicate_keep_strategy="first",
        num_missing_strategy="median",
        cat_missing_strategy="unknown",
        strip_whitespace=True,
        normalize_internal_spaces=True,
        casing_strategy="title",
        standardize_known_categories=True,
        auto_convert_types=True,
        standardize_dates=True,
        fix_negative_values=True,
        outlier_strategy="flag_only"
    )
    cleaned_df, cleaning_log_df, summary_stats = DataCleaner.clean_dataset(df_raw, config)
    print(f"   Cleaned rows: {len(cleaned_df)}, Total operations logged: {len(cleaning_log_df)}")
    print(f"   Removed duplicates: {summary_stats['records_removed']}, Imputed missing: {summary_stats['missing_cells_imputed']}")

    print("4. Profiling cleaned dataset...")
    clean_profile = DataProfiler.profile_dataset(cleaned_df)
    print(f"   Clean Quality Score: {clean_profile.quality_score.overall_score}% ({clean_profile.quality_score.grade})")

    print("5. Running Analytics Engine...")
    analytics = DataAnalyzer.analyze_dataset(cleaned_df)
    print(f"   Is Sales Domain: {analytics.is_sales_domain}")
    if analytics.sales_kpis:
        print(f"   Total Revenue: {analytics.sales_kpis.total_revenue_formatted}")
        print(f"   AOV: {analytics.sales_kpis.avg_order_value_formatted}")
        print(f"   Total Quantity: {analytics.sales_kpis.total_quantity_formatted}")

    print("6. Generating High-Res Static Charts...")
    chart_dir = "reports/charts_temp"
    chart_paths = Visualizer.generate_static_charts(cleaned_df, analytics, chart_dir)
    print(f"   Generated {len(chart_paths)} charts: {list(chart_paths.keys())}")

    print("7. Generating Excel Report...")
    excel_path = ExcelReportGenerator.generate_report(
        cleaned_df=cleaned_df,
        cleaning_log_df=cleaning_log_df,
        raw_profile=raw_profile,
        clean_profile=clean_profile,
        analytics=analytics,
        chart_image_paths=chart_paths,
        output_file_path="reports/excel/DataClean_Analysis_Report.xlsx"
    )
    print(f"   Excel Report saved: {excel_path} ({os.path.getsize(excel_path):,} bytes)")

    print("8. Generating PDF Report...")
    pdf_path = PDFReportGenerator.generate_report(
        cleaned_df=cleaned_df,
        cleaning_log_df=cleaning_log_df,
        raw_profile=raw_profile,
        clean_profile=clean_profile,
        analytics=analytics,
        chart_image_paths=chart_paths,
        output_file_path="reports/pdf/DataClean_Analysis_Report.pdf"
    )
    print(f"   PDF Report saved: {pdf_path} ({os.path.getsize(pdf_path):,} bytes)")

    print("\n All pipeline tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_pipeline()
    if not success:
        sys.exit(1)
