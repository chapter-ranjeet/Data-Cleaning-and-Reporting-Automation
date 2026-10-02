"""
DataClean Pro - Professional Automated Excel Report Generator
Produces a multi-sheet, beautifully formatted workbook (DataClean_Analysis_Report.xlsx)
using openpyxl with corporate styling, freeze panes, auto-fit columns, and embedded charts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import openpyxl
from openpyxl.drawing.image import Image as OpenPyxlImage
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from src.analyzer import AnalyticsReport
from src.profiler import DatasetProfile
from src.utils import THEME_COLORS

# Professional styling definitions
COLOR_PRIMARY_NAVY = "1E3A8A"
COLOR_SECONDARY_BLUE = "2563EB"
COLOR_ACCENT_TEAL = "0D9488"
COLOR_LIGHT_BG = "F8FAFC"
COLOR_ZEBRA = "F1F5F9"
COLOR_BORDER = "E2E8F0"
COLOR_WHITE = "FFFFFF"
COLOR_DARK_TEXT = "0F172A"

font_header = Font(name="Calibri", size=11, bold=True, color=COLOR_WHITE)
font_title = Font(name="Calibri", size=16, bold=True, color=COLOR_PRIMARY_NAVY)
font_subtitle = Font(name="Calibri", size=11, italic=True, color="64748B")
font_section = Font(name="Calibri", size=13, bold=True, color=COLOR_PRIMARY_NAVY)
font_bold = Font(name="Calibri", size=11, bold=True, color=COLOR_DARK_TEXT)
font_regular = Font(name="Calibri", size=11, color=COLOR_DARK_TEXT)

fill_primary = PatternFill(start_color=COLOR_PRIMARY_NAVY, end_color=COLOR_PRIMARY_NAVY, fill_type="solid")
fill_secondary = PatternFill(start_color=COLOR_SECONDARY_BLUE, end_color=COLOR_SECONDARY_BLUE, fill_type="solid")
fill_accent = PatternFill(start_color=COLOR_ACCENT_TEAL, end_color=COLOR_ACCENT_TEAL, fill_type="solid")
fill_light = PatternFill(start_color=COLOR_LIGHT_BG, end_color=COLOR_LIGHT_BG, fill_type="solid")
fill_zebra = PatternFill(start_color=COLOR_ZEBRA, end_color=COLOR_ZEBRA, fill_type="solid")

thin_border_side = Side(style="thin", color=COLOR_BORDER)
border_cell = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
border_header = Border(
    left=thin_border_side, right=thin_border_side,
    top=Side(style="medium", color=COLOR_PRIMARY_NAVY),
    bottom=Side(style="medium", color=COLOR_PRIMARY_NAVY)
)

class ExcelReportGenerator:
    """Creates executive-ready Excel reports containing analysis, data, and charts."""

    @classmethod
    def generate_report(
        cls,
        cleaned_df: pd.DataFrame,
        cleaning_log_df: pd.DataFrame,
        raw_profile: DatasetProfile,
        clean_profile: DatasetProfile,
        analytics: AnalyticsReport,
        chart_image_paths: Dict[str, str],
        output_file_path: str = "reports/excel/DataClean_Analysis_Report.xlsx"
    ) -> str:
        """
        Build full multi-tab automated Excel workbook.
        
        Returns:
            The absolute path of the generated Excel workbook.
        """
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        wb = openpyxl.Workbook()
        # Remove default sheet
        wb.remove(wb.active)

        # 1. Sheet 1: Executive Summary
        ws_exec = wb.create_sheet(title="Executive Summary")
        cls._build_executive_summary_sheet(ws_exec, raw_profile, clean_profile, analytics)

        # 2. Sheet 2: Data Quality
        ws_quality = wb.create_sheet(title="Data Quality")
        cls._build_data_quality_sheet(ws_quality, raw_profile, clean_profile)

        # 3. Sheet 3: Cleaned Data
        ws_data = wb.create_sheet(title="Cleaned Data")
        cls._build_cleaned_data_sheet(ws_data, cleaned_df)

        # 4. Sheet 4: Cleaning Log
        ws_log = wb.create_sheet(title="Cleaning Log")
        cls._build_cleaning_log_sheet(ws_log, cleaning_log_df)

        # 5. Sheet 5: Statistics
        ws_stats = wb.create_sheet(title="Statistics")
        cls._build_statistics_sheet(ws_stats, analytics, cleaned_df)

        # 6. Sheet 6: Charts
        ws_charts = wb.create_sheet(title="Charts")
        cls._build_charts_sheet(ws_charts, chart_image_paths)

        wb.save(output_file_path)
        return output_file_path

    @classmethod
    def _build_executive_summary_sheet(
        cls,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        raw_profile: DatasetProfile,
        clean_profile: DatasetProfile,
        analytics: AnalyticsReport
    ) -> None:
        """Build executive cover summary with KPI comparisons."""
        ws.views.sheetView[0].showGridLines = True
        
        # Header banner
        ws["B2"] = "DataClean Pro — Automated Data Cleaning & Reporting Platform"
        ws["B2"].font = font_title
        ws["B3"] = f"Executive Analysis Report | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ws["B3"].font = font_subtitle

        # Table: Before vs After Data Quality KPIs
        ws["B5"] = "DATASET QUALITY TRANSFORMATION"
        ws["B5"].font = font_section

        headers = ["Metric", "Raw Input", "Cleaned Output", "Improvement / Net Change"]
        for col_idx, h in enumerate(headers, start=2):
            cell = ws.cell(row=6, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_primary
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_header

        kpi_rows = [
            ("Data Quality Score", f"{raw_profile.quality_score.overall_score}%", f"{clean_profile.quality_score.overall_score}%", f"+{round(clean_profile.quality_score.overall_score - raw_profile.quality_score.overall_score, 1)}%"),
            ("Total Rows", f"{raw_profile.total_rows:,}", f"{clean_profile.total_rows:,}", f"-{raw_profile.total_rows - clean_profile.total_rows:,} duplicates removed"),
            ("Total Columns", f"{raw_profile.total_columns}", f"{clean_profile.total_columns}", "Maintained"),
            ("Missing Cells", f"{raw_profile.total_missing_cells:,} ({raw_profile.missing_cells_pct}%)", f"{clean_profile.total_missing_cells:,} ({clean_profile.missing_cells_pct}%)", f"{raw_profile.total_missing_cells - clean_profile.total_missing_cells:,} imputed"),
            ("Duplicate Records", f"{raw_profile.total_duplicate_rows:,}", f"{clean_profile.total_duplicate_rows:,}", f"{raw_profile.total_duplicate_rows:,} dropped"),
            ("Quality Assessment Grade", raw_profile.quality_score.grade, clean_profile.quality_score.grade, "Optimized")
        ]

        for r_idx, (m, b, a, c) in enumerate(kpi_rows, start=7):
            bg = fill_zebra if r_idx % 2 == 0 else fill_light
            for c_idx, val in enumerate([m, b, a, c], start=2):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = font_bold if c_idx == 2 else font_regular
                cell.fill = bg
                cell.border = border_cell
                cell.alignment = Alignment(horizontal="left" if c_idx == 2 else "center", vertical="center")

        # Business Insights / Domain KPIs
        start_r = 15
        if analytics.is_sales_domain and analytics.sales_kpis:
            sales = analytics.sales_kpis
            ws.cell(row=start_r, column=2, value="COMMERCIAL BUSINESS KPIS").font = font_section

            biz_headers = ["Key Metric", "Calculated Value", "Business Significance"]
            for col_idx, h in enumerate(biz_headers, start=2):
                cell = ws.cell(row=start_r + 1, column=col_idx, value=h)
                cell.font = font_header
                cell.fill = fill_accent
                cell.alignment = Alignment(horizontal="center")
                cell.border = border_header

            biz_metrics = [
                ("Total Gross Revenue", sales.total_revenue_formatted, "Total monetized throughput across valid orders"),
                ("Average Order Value (AOV)", sales.avg_order_value_formatted, "Mean commercial spend per customer order"),
                ("Total Quantity Sold", sales.total_quantity_formatted, "Aggregated units distributed across all transactions"),
                ("Total Orders Processed", sales.total_orders_formatted, "Net verified purchasing records post-cleaning"),
                ("Unique Customers", f"{sales.unique_customers:,}", "Distinct individual clients identified in pipeline")
            ]

            for r_idx, (m, v, s) in enumerate(biz_metrics, start=start_r + 2):
                bg = fill_zebra if r_idx % 2 == 0 else fill_light
                for c_idx, val in enumerate([m, v, s], start=2):
                    cell = ws.cell(row=r_idx, column=c_idx, value=val)
                    cell.font = font_bold if c_idx in [2, 3] else font_regular
                    cell.fill = bg
                    cell.border = border_cell
                    cell.alignment = Alignment(horizontal="left" if c_idx != 3 else "center")

        cls._autofit_columns(ws)

    @classmethod
    def _build_data_quality_sheet(
        cls, ws: openpyxl.worksheet.worksheet.Worksheet, raw_profile: DatasetProfile, clean_profile: DatasetProfile
    ) -> None:
        """Detailed column-by-column quality metrics."""
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        headers = [
            "Column Name", "Inferred Type", "Raw Missing", "Raw Missing %",
            "Cleaned Missing", "Unique Count", "Anomalies / Identified Issues"
        ]

        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_primary
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_header

        for r_idx, (col_name, raw_p) in enumerate(raw_profile.column_profiles.items(), start=2):
            clean_p = clean_profile.column_profiles.get(col_name)
            clean_null = clean_p.null_count if clean_p else 0
            issues = "; ".join(raw_p.quality_issues) if raw_p.quality_issues else "Clean"

            row_data = [
                col_name,
                raw_p.inferred_type,
                raw_p.null_count,
                f"{raw_p.null_percentage}%",
                clean_null,
                raw_p.unique_count,
                issues
            ]

            bg = fill_zebra if r_idx % 2 == 0 else fill_light
            for c_idx, val in enumerate(row_data, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = font_regular
                cell.fill = bg
                cell.border = border_cell
                cell.alignment = Alignment(horizontal="left" if c_idx in [1, 7] else "center")

        cls._autofit_columns(ws)

    @classmethod
    def _build_cleaned_data_sheet(
        cls, ws: openpyxl.worksheet.worksheet.Worksheet, cleaned_df: pd.DataFrame
    ) -> None:
        """Export the complete cleaned dataset with styled headers, freeze panes, and formatting."""
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        # Headers
        for col_idx, col_name in enumerate(cleaned_df.columns, start=1):
            cell = ws.cell(row=1, column=col_idx, value=str(col_name))
            cell.font = font_header
            cell.fill = fill_primary
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_header

        # Data rows (stream row by row)
        # For performance, take up to 10,000 rows
        display_df = cleaned_df.head(10000)
        for r_idx, row_values in enumerate(display_df.itertuples(index=False), start=2):
            bg = fill_zebra if r_idx % 2 == 0 else fill_light
            for c_idx, val in enumerate(row_values, start=1):
                cell = ws.cell(row=r_idx, column=c_idx)
                if pd.isna(val):
                    cell.value = ""
                elif isinstance(val, (int, float)) and not isinstance(val, bool):
                    cell.value = val
                    if isinstance(val, float):
                        cell.number_format = "#,##0.00"
                    else:
                        cell.number_format = "#,##0"
                else:
                    cell.value = str(val)

                cell.font = font_regular
                cell.fill = bg
                cell.border = border_cell

        cls._autofit_columns(ws, max_cols=25)

    @classmethod
    def _build_cleaning_log_sheet(
        cls, ws: openpyxl.worksheet.worksheet.Worksheet, cleaning_log_df: pd.DataFrame
    ) -> None:
        """Audit trail sheet of all transformations."""
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"

        headers = ["Timestamp", "Operation", "Column Target", "Records Affected", "Detailed Description"]
        for col_idx, h in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.font = font_header
            cell.fill = fill_secondary
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border_header

        for r_idx, row in enumerate(cleaning_log_df.itertuples(index=False), start=2):
            bg = fill_zebra if r_idx % 2 == 0 else fill_light
            values = [row.Timestamp, row.Operation, row.Column, row[3], row.Description]
            for c_idx, val in enumerate(values, start=1):
                cell = ws.cell(row=r_idx, column=c_idx, value=val)
                cell.font = font_regular
                cell.fill = bg
                cell.border = border_cell
                cell.alignment = Alignment(horizontal="left" if c_idx in [2, 3, 5] else "center")

        cls._autofit_columns(ws)

    @classmethod
    def _build_statistics_sheet(
        cls,
        ws: openpyxl.worksheet.worksheet.Worksheet,
        analytics: AnalyticsReport,
        cleaned_df: pd.DataFrame
    ) -> None:
        """Statistical descriptions for numerical and categorical fields."""
        ws.views.sheetView[0].showGridLines = True

        ws["A1"] = "NUMERICAL DESCRIPTIVE STATISTICS"
        ws["A1"].font = font_section

        if analytics.generic_kpis and not analytics.generic_kpis.summary_statistics.empty:
            stats_df = analytics.generic_kpis.summary_statistics.reset_index()
            stats_df.rename(columns={"index": "Attribute"}, inplace=True)

            for col_idx, col_name in enumerate(stats_df.columns, start=1):
                cell = ws.cell(row=3, column=col_idx, value=str(col_name).title())
                cell.font = font_header
                cell.fill = fill_primary
                cell.alignment = Alignment(horizontal="center")
                cell.border = border_header

            for r_idx, row_values in enumerate(stats_df.itertuples(index=False), start=4):
                bg = fill_zebra if r_idx % 2 == 0 else fill_light
                for c_idx, val in enumerate(row_values, start=1):
                    cell = ws.cell(row=r_idx, column=c_idx, value=val)
                    cell.font = font_regular
                    cell.fill = bg
                    cell.border = border_cell
                    cell.alignment = Alignment(horizontal="left" if c_idx == 1 else "center")
                    if isinstance(val, (float, int)):
                        cell.number_format = "#,##0.00"

        cls._autofit_columns(ws)

    @classmethod
    def _build_charts_sheet(
        cls, ws: openpyxl.worksheet.worksheet.Worksheet, chart_image_paths: Dict[str, str]
    ) -> None:
        """Insert rendered charts as images into the workbook."""
        ws.views.sheetView[0].showGridLines = False

        ws["B2"] = "AUTOMATED VISUAL ANALYTICS"
        ws["B2"].font = font_title
        ws["B3"] = "Embedded high-resolution graphical visualizations generated from dataset analysis."
        ws["B3"].font = font_subtitle

        current_row = 5
        for chart_name, path in chart_image_paths.items():
            if os.path.exists(path):
                img = OpenPyxlImage(path)
                # Scale image cleanly (width ~ 600px)
                img.width = 620
                img.height = 320
                cell_loc = f"B{current_row}"
                ws.add_image(img, cell_loc)
                current_row += 18  # Spacing between charts

    @classmethod
    def _autofit_columns(cls, ws: openpyxl.worksheet.worksheet.Worksheet, max_cols: int = 20) -> None:
        """Helper to dynamically adjust column widths to fit contents cleanly."""
        for col in ws.iter_cols(min_col=1, max_col=min(ws.max_column, max_cols)):
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col[:100]:  # sample top 100 cells
                if cell.value:
                    val_str = str(cell.value)
                    max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)
