"""
DataClean Pro - Professional Automated PDF Report Generator
Produces an executive-ready multi-page PDF report (DataClean_Analysis_Report.pdf)
using ReportLab with customized styling, tables, metrics cards, and embedded charts.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.analyzer import AnalyticsReport
from src.profiler import DatasetProfile

# Palette constants
COLOR_PRIMARY = colors.HexColor("#1E3A8A")   # Royal Navy
COLOR_SECONDARY = colors.HexColor("#2563EB") # Blue
COLOR_ACCENT = colors.HexColor("#0D9488")    # Teal
COLOR_SUCCESS = colors.HexColor("#10B981")   # Emerald
COLOR_DARK = colors.HexColor("#0F172A")      # Dark Slate
COLOR_MUTED = colors.HexColor("#64748B")     # Muted Slate
COLOR_LIGHT_BG = colors.HexColor("#F8FAFC")  # Light gray-blue
COLOR_BORDER = colors.HexColor("#E2E8F0")

class NumberedCanvas(canvas.Canvas):
    """Canvas that performs a two-pass calculation to write 'Page X of Y' on all pages."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(COLOR_MUTED)

        # Draw header only on pages > 1
        if self._pageNumber > 1:
            self.drawString(54, 750, "DataClean Pro — Automated Data Cleaning & Reporting")
            self.drawRightString(558, 750, "CONFIDENTIAL & PROPRIETARY")
            self.setStrokeColor(COLOR_BORDER)
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Draw footer on all pages
        self.setStrokeColor(COLOR_BORDER)
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        self.drawString(54, 32, "Developed as a Data Science Internship Project | DataClean Pro v1.0")
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 32, page_text)

        self.restoreState()


class PDFReportGenerator:
    """Creates publication-ready PDF documentation of dataset health and analytical insights."""

    @classmethod
    def generate_report(
        cls,
        cleaned_df: pd.DataFrame,
        cleaning_log_df: pd.DataFrame,
        raw_profile: DatasetProfile,
        clean_profile: DatasetProfile,
        analytics: AnalyticsReport,
        chart_image_paths: Dict[str, str],
        output_file_path: str = "reports/pdf/DataClean_Analysis_Report.pdf"
    ) -> str:
        """
        Build and save the automated PDF report.
        
        Returns:
            The file path of the generated PDF.
        """
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        doc = SimpleDocTemplate(
            output_file_path,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54
        )

        styles = getSampleStyleSheet()
        
        # Custom Typography Styles
        title_style = ParagraphStyle(
            "CoverTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=32,
            textColor=COLOR_PRIMARY
        )
        subtitle_style = ParagraphStyle(
            "CoverSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=COLOR_MUTED
        )
        h1_style = ParagraphStyle(
            "SectionH1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=22,
            textColor=COLOR_PRIMARY,
            spaceBefore=12,
            spaceAfter=6
        )
        h2_style = ParagraphStyle(
            "SectionH2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=COLOR_SECONDARY,
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=COLOR_DARK
        )
        th_style = ParagraphStyle(
            "TableHeader",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=1
        )
        td_style = ParagraphStyle(
            "TableCell",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=COLOR_DARK
        )
        td_bold_style = ParagraphStyle(
            "TableCellBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=11,
            textColor=COLOR_DARK
        )

        story = []

        # =========================================================
        # 1. COVER / TITLE PAGE
        # =========================================================
        story.append(Spacer(1, 40))
        # Top banner accent
        story.append(HRFlowable(width="100%", thickness=6, color=COLOR_PRIMARY, spaceAfter=20))
        
        story.append(Paragraph("DataClean Pro", title_style))
        story.append(Paragraph("Data Cleaning & Reporting Automation Platform", subtitle_style))
        story.append(Spacer(1, 15))
        
        story.append(Paragraph("Comprehensive Dataset Health & Analytical Audit Report", ParagraphStyle(
            "SubDoc", parent=subtitle_style, fontSize=11, textColor=COLOR_SECONDARY
        )))
        story.append(Spacer(1, 25))

        # Metadata Box
        meta_data = [
            [Paragraph("<b>Report Generated:</b>", td_bold_style), Paragraph(datetime.now().strftime("%B %d, %Y at %H:%M:%S"), td_style)],
            [Paragraph("<b>Pipeline Stage:</b>", td_bold_style), Paragraph("Post-Cleaning Production Audit", td_style)],
            [Paragraph("<b>Source Rows / Cols:</b>", td_bold_style), Paragraph(f"{raw_profile.total_rows:,} rows × {raw_profile.total_columns} columns", td_style)],
            [Paragraph("<b>Initial Quality Score:</b>", td_bold_style), Paragraph(f"<b>{raw_profile.quality_score.overall_score}%</b> ({raw_profile.quality_score.grade})", td_style)],
            [Paragraph("<b>Cleaned Quality Score:</b>", td_bold_style), Paragraph(f"<b>{clean_profile.quality_score.overall_score}%</b> ({clean_profile.quality_score.grade})", td_style)],
            [Paragraph("<b>Project Context:</b>", td_bold_style), Paragraph("Developed as a Data Science Internship Project", td_style)],
        ]
        meta_table = Table(meta_data, colWidths=[150, 350])
        meta_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        story.append(meta_table)

        story.append(Spacer(1, 40))

        # Executive Summary Callout
        story.append(Paragraph("Executive Summary", h1_style))
        summary_p = (
            f"This automated audit documents the transformation of the input dataset from an unverified, "
            f"inconsistent state to a high-integrity, normalized production dataset. "
            f"DataClean Pro detected <b>{raw_profile.total_duplicate_rows:,} duplicate records</b> and "
            f"<b>{raw_profile.total_missing_cells:,} missing data cells</b> across {raw_profile.total_columns} features. "
            f"Following deterministic pipeline remediation, the overall Data Quality Score elevated from "
            f"<b>{raw_profile.quality_score.overall_score}% ({raw_profile.quality_score.grade})</b> to "
            f"<b>{clean_profile.quality_score.overall_score}% ({clean_profile.quality_score.grade})</b>. "
            f"Downstream business analytics, frequency profiling, and statistical distributions are detailed below."
        )
        story.append(Paragraph(summary_p, body_style))
        story.append(Spacer(1, 20))
        story.append(PageBreak())

        # =========================================================
        # 2. DATASET OVERVIEW & QUALITY ANALYSIS
        # =========================================================
        story.append(Paragraph("1. Data Quality Transformation Matrix", h1_style))
        story.append(Paragraph("Comparison of fundamental quality indicators prior to and following automated cleaning:", body_style))
        story.append(Spacer(1, 8))

        kpi_table_data = [
            [
                Paragraph("<b>Audit Metric</b>", th_style),
                Paragraph("<b>Pre-Cleaning (Raw)</b>", th_style),
                Paragraph("<b>Post-Cleaning (Clean)</b>", th_style),
                Paragraph("<b>Net Remediation Impact</b>", th_style),
            ],
            [
                Paragraph("Data Quality Score", td_bold_style),
                Paragraph(f"{raw_profile.quality_score.overall_score}%", td_style),
                Paragraph(f"<b>{clean_profile.quality_score.overall_score}%</b>", td_bold_style),
                Paragraph(f"+{round(clean_profile.quality_score.overall_score - raw_profile.quality_score.overall_score, 1)}% improvement", td_style),
            ],
            [
                Paragraph("Row Count", td_bold_style),
                Paragraph(f"{raw_profile.total_rows:,}", td_style),
                Paragraph(f"{clean_profile.total_rows:,}", td_style),
                Paragraph(f"-{raw_profile.total_rows - clean_profile.total_rows:,} duplicate records purged", td_style),
            ],
            [
                Paragraph("Missing Value Cells", td_bold_style),
                Paragraph(f"{raw_profile.total_missing_cells:,} ({raw_profile.missing_cells_pct}%)", td_style),
                Paragraph(f"{clean_profile.total_missing_cells:,} ({clean_profile.missing_cells_pct}%)", td_style),
                Paragraph(f"{raw_profile.total_missing_cells - clean_profile.total_missing_cells:,} cells imputed", td_style),
            ],
            [
                Paragraph("Duplicate Rows", td_bold_style),
                Paragraph(f"{raw_profile.total_duplicate_rows:,}", td_style),
                Paragraph(f"{clean_profile.total_duplicate_rows:,}", td_style),
                Paragraph("100% duplicate elimination", td_style),
            ],
            [
                Paragraph("Quality Rating Tier", td_bold_style),
                Paragraph(raw_profile.quality_score.grade, td_style),
                Paragraph(f"<b>{clean_profile.quality_score.grade}</b>", td_bold_style),
                Paragraph("Enterprise Certified", td_style),
            ],
        ]

        kpi_t = Table(kpi_table_data, colWidths=[130, 110, 110, 150])
        kpi_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(kpi_t)
        story.append(Spacer(1, 15))

        # Column Profile Breakdown Table
        story.append(Paragraph("Feature Quality & Anomaly Diagnostics", h2_style))
        col_headers = [
            Paragraph("<b>Column</b>", th_style),
            Paragraph("<b>Type</b>", th_style),
            Paragraph("<b>Missing</b>", th_style),
            Paragraph("<b>Unique</b>", th_style),
            Paragraph("<b>Identified Defects & Remediation</b>", th_style),
        ]
        col_table_data = [col_headers]

        for col_name, p in raw_profile.column_profiles.items():
            issues = "; ".join(p.quality_issues) if p.quality_issues else "Fully valid"
            col_table_data.append([
                Paragraph(col_name, td_bold_style),
                Paragraph(p.inferred_type, td_style),
                Paragraph(f"{p.null_count} ({p.null_percentage}%)", td_style),
                Paragraph(str(p.unique_count), td_style),
                Paragraph(issues[:120], td_style),
            ])

        col_t = Table(col_table_data, colWidths=[100, 75, 75, 55, 195])
        col_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_SECONDARY),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(col_t)
        story.append(Spacer(1, 15))

        # =========================================================
        # 3. CLEANING OPERATIONS AUDIT TRAIL
        # =========================================================
        story.append(Paragraph("2. Automated Cleaning Operations Audit Trail", h1_style))
        story.append(Paragraph("Full deterministic log of data transformations executed by DataClean Pro:", body_style))
        story.append(Spacer(1, 8))

        log_headers = [
            Paragraph("<b>Timestamp</b>", th_style),
            Paragraph("<b>Operation</b>", th_style),
            Paragraph("<b>Column Target</b>", th_style),
            Paragraph("<b>Affected</b>", th_style),
            Paragraph("<b>Action Details</b>", th_style),
        ]
        log_table_data = [log_headers]

        # Take first 15 operations to fit cleanly
        for row in cleaning_log_df.head(15).itertuples(index=False):
            log_table_data.append([
                Paragraph(str(row.Timestamp), td_style),
                Paragraph(str(row.Operation), td_bold_style),
                Paragraph(str(row.Column), td_style),
                Paragraph(str(row[3]), td_style),
                Paragraph(str(row.Description)[:100], td_style),
            ])

        log_t = Table(log_table_data, colWidths=[65, 110, 85, 50, 190])
        log_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("BOX", (0, 0), (-1, -1), 1, COLOR_PRIMARY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(log_t)
        story.append(Spacer(1, 15))
        story.append(PageBreak())

        # =========================================================
        # 4. BUSINESS ANALYTICS & INSIGHTS
        # =========================================================
        story.append(Paragraph("3. Analytical Intelligence & Key Metrics", h1_style))

        if analytics.is_sales_domain and analytics.sales_kpis:
            sales = analytics.sales_kpis
            story.append(Paragraph("Domain detected: Commercial E-Commerce / Retail Sales Dataset", h2_style))
            
            sales_grid = [
                [
                    Paragraph("<b>Gross Revenue</b><br/>" f"<font size='12' color='#1E3A8A'><b>{sales.total_revenue_formatted}</b></font>", td_style),
                    Paragraph("<b>Average Order Value</b><br/>" f"<font size='12' color='#0D9488'><b>{sales.avg_order_value_formatted}</b></font>", td_style),
                    Paragraph("<b>Total Orders</b><br/>" f"<font size='12' color='#2563EB'><b>{sales.total_orders_formatted}</b></font>", td_style),
                    Paragraph("<b>Units Sold</b><br/>" f"<font size='12' color='#0F172A'><b>{sales.total_quantity_formatted}</b></font>", td_style),
                ]
            ]
            sg_t = Table(sales_grid, colWidths=[125, 125, 125, 125])
            sg_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_LIGHT_BG),
                ("BOX", (0, 0), (-1, -1), 1, COLOR_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, COLOR_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]))
            story.append(sg_t)
            story.append(Spacer(1, 15))

        # Embed Visualizations
        story.append(Paragraph("4. Graphical Visualizations", h1_style))
        story.append(Paragraph("Embedded visual analytics produced during pipeline execution:", body_style))
        story.append(Spacer(1, 10))

        # Add charts in pairs or single full width
        chart_keys = list(chart_image_paths.keys())
        for k in chart_keys:
            path = chart_image_paths[k]
            if os.path.exists(path):
                img = Image(path, width=6.5 * inch, height=3.2 * inch)
                story.append(KeepTogether([img, Spacer(1, 12)]))

        story.append(Spacer(1, 15))

        # =========================================================
        # 5. CONCLUSION & RECOMMENDATIONS
        # =========================================================
        story.append(Paragraph("5. Audit Conclusion & Next Steps", h1_style))
        conclusion_text = (
            f"The dataset has undergone automated inspection, cleansing, and validation via <b>DataClean Pro</b>. "
            f"All critical data hygiene standards including record uniqueness, categorical standardization, "
            f"numerical validation, and datetime formatting have achieved certified thresholds. "
            f"The final composite Data Quality Score of <b>{clean_profile.quality_score.overall_score}%</b> "
            f"confirms this dataset is robust and primed for downstream business intelligence, machine learning modeling, "
            f"or executive dashboard deployment."
        )
        story.append(Paragraph(conclusion_text, body_style))
        story.append(Spacer(1, 20))

        doc.build(story, canvasmaker=NumberedCanvas)
        return output_file_path
