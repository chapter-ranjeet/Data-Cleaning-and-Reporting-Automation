"""
DataClean Pro - Interactive & Static Visualization Engine
Generates modern Plotly interactive charts for the Streamlit UI,
and renders high-resolution Matplotlib figures for PDF and Excel reports.
"""

from typing import Any, Dict, List, Optional, Tuple
import os
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for thread-safe server rendering
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.analyzer import AnalyticsReport
from src.utils import CHART_PALETTE, THEME_COLORS

# Default layout styling for Plotly
PLOTLY_TEMPLATE = "plotly_white"
PLOTLY_FONT = dict(family="Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif", size=12)

class Visualizer:
    """Produces interactive Plotly figures and static Matplotlib figures."""

    # -------------------------------------------------------------
    # PLOTLY INTERACTIVE CHARTS (For Streamlit UI)
    # -------------------------------------------------------------

    @classmethod
    def plot_quality_gauge(cls, score: float) -> go.Figure:
        """Create an attractive circular gauge chart for the Data Quality Score."""
        color = "#10B981" if score >= 85 else ("#2563EB" if score >= 70 else ("#F59E0B" if score >= 50 else "#EF4444"))
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 42, "color": color, "family": "Inter, sans-serif"}},
            title={"text": "Data Quality Score", "font": {"size": 18, "color": "#1E293B"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#CBD5E1"},
                "bar": {"color": color, "thickness": 0.3},
                "bgcolor": "#F1F5F9",
                "borderwidth": 1,
                "bordercolor": "#E2E8F0",
                "steps": [
                    {"range": [0, 50], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [50, 75], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [75, 90], "color": "rgba(37, 99, 235, 0.15)"},
                    {"range": [90, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
            }
        ))
        fig.update_layout(
            height=260,
            margin=dict(l=25, r=25, t=40, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            font=PLOTLY_FONT
        )
        return fig

    @classmethod
    def plot_monthly_revenue_trend(cls, trend_data: List[Dict[str, Any]]) -> go.Figure:
        """Plot monthly revenue trend as an interactive area/line chart."""
        if not trend_data:
            return cls._empty_figure("No monthly date trend data available")

        months = [d["Month"] for d in trend_data]
        revenues = [d["Revenue"] for d in trend_data]
        orders = [d["Orders"] for d in trend_data]

        fig = go.Figure()
        # Area / Line for revenue
        fig.add_trace(go.Scatter(
            x=months,
            y=revenues,
            mode="lines+markers",
            name="Revenue ($)",
            line=dict(color="#2563EB", width=3, shape="spline"),
            marker=dict(size=7, color="#1E3A8A"),
            fill="tozeroy",
            fillcolor="rgba(37, 99, 235, 0.10)",
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            title="<b>Monthly Revenue Trend</b>",
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=380,
            margin=dict(l=30, r=20, t=50, b=40),
            xaxis=dict(title="Month", showgrid=False),
            yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
            hovermode="x unified"
        )
        return fig

    @classmethod
    def plot_category_performance(cls, category_dict: Dict[str, float]) -> go.Figure:
        """Bar chart for category performance."""
        if not category_dict:
            return cls._empty_figure("No category distribution available")

        cats = list(category_dict.keys())
        revs = list(category_dict.values())

        fig = go.Figure(go.Bar(
            x=cats,
            y=revs,
            marker=dict(
                color=revs,
                colorscale="Blues",
                line=dict(color="#1E3A8A", width=1)
            ),
            text=[f"${v:,.0f}" for v in revs],
            textposition="auto",
            hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            title="<b>Revenue by Category</b>",
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=360,
            margin=dict(l=30, r=20, t=50, b=40),
            xaxis=dict(title="Category", showgrid=False),
            yaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#F1F5F9", tickprefix="$")
        )
        return fig

    @classmethod
    def plot_regional_performance(cls, region_dict: Dict[str, float]) -> go.Figure:
        """Donut or Horizontal Bar chart for regional performance."""
        if not region_dict:
            return cls._empty_figure("No regional distribution available")

        regions = list(region_dict.keys())
        revs = list(region_dict.values())

        fig = go.Figure(go.Pie(
            labels=regions,
            values=revs,
            hole=0.45,
            marker=dict(colors=CHART_PALETTE[:len(regions)]),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Revenue: $%{value:,.2f} (%{percent})<extra></extra>"
        ))

        fig.update_layout(
            title="<b>Regional Revenue Share</b>",
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=360,
            margin=dict(l=20, r=20, t=50, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
        )
        return fig

    @classmethod
    def plot_top_products(cls, top_products: List[Dict[str, Any]]) -> go.Figure:
        """Horizontal bar chart for top selling products."""
        if not top_products:
            return cls._empty_figure("No product breakdown available")

        prods = [p["Product"] for p in reversed(top_products[:8])]
        revs = [p["Revenue"] for p in reversed(top_products[:8])]

        fig = go.Figure(go.Bar(
            y=prods,
            x=revs,
            orientation="h",
            marker=dict(
                color="#0D9488",  # Teal
                line=dict(color="#0F766E", width=1)
            ),
            text=[f"${v:,.0f}" for v in revs],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Revenue: $%{x:,.2f}<extra></extra>"
        ))

        fig.update_layout(
            title="<b>Top Products by Revenue</b>",
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=360,
            margin=dict(l=150, r=30, t=50, b=40),
            xaxis=dict(title="Revenue ($)", showgrid=True, gridcolor="#F1F5F9", tickprefix="$"),
            yaxis=dict(title="", showgrid=False)
        )
        return fig

    @classmethod
    def plot_payment_distribution(cls, pay_dist: Dict[str, int]) -> go.Figure:
        """Donut chart for payment method distribution."""
        if not pay_dist:
            return cls._empty_figure("No payment method data available")

        labels = list(pay_dist.keys())
        values = list(pay_dist.values())

        fig = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.45,
            marker=dict(colors=CHART_PALETTE[:len(labels)]),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>Orders: %{value} (%{percent})<extra></extra>"
        ))

        fig.update_layout(
            title="<b>Payment Method Distribution</b>",
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=340,
            margin=dict(l=20, r=20, t=50, b=30),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
        )
        return fig

    @classmethod
    def plot_histogram_distribution(cls, df: pd.DataFrame, column: str) -> go.Figure:
        """Interactive histogram with KDE curve and box margin."""
        if column not in df.columns:
            return cls._empty_figure(f"Column '{column}' not found")

        clean_series = pd.to_numeric(df[column], errors="coerce").dropna()
        if clean_series.empty:
            return cls._empty_figure(f"No numeric data in column '{column}'")

        fig = px.histogram(
            x=clean_series,
            marginal="box",
            nbins=35,
            title=f"<b>Distribution of {column}</b>",
            color_discrete_sequence=["#2563EB"]
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=360,
            margin=dict(l=30, r=20, t=50, b=40),
            xaxis=dict(title=column, showgrid=True, gridcolor="#F1F5F9"),
            yaxis=dict(title="Frequency", showgrid=True, gridcolor="#F1F5F9")
        )
        return fig

    @classmethod
    def plot_box_distribution(cls, df: pd.DataFrame, num_col: str, cat_col: Optional[str] = None) -> go.Figure:
        """Box plot for outlier detection and variance inspection."""
        if num_col not in df.columns:
            return cls._empty_figure("Column not found")

        fig = px.box(
            df,
            y=num_col,
            x=cat_col if (cat_col and cat_col in df.columns) else None,
            points="outliers",
            color=cat_col if (cat_col and cat_col in df.columns) else None,
            color_discrete_sequence=CHART_PALETTE,
            title=f"<b>Box Plot: {num_col} {'by ' + cat_col if cat_col else ''}</b>"
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=360,
            margin=dict(l=30, r=20, t=50, b=40),
            yaxis=dict(title=num_col, showgrid=True, gridcolor="#F1F5F9")
        )
        return fig

    @classmethod
    def plot_correlation_heatmap(cls, corr_df: Optional[pd.DataFrame]) -> go.Figure:
        """Interactive correlation heatmap for numerical attributes."""
        if corr_df is None or corr_df.empty:
            return cls._empty_figure("Insufficient numeric columns for correlation analysis")

        fig = px.imshow(
            corr_df,
            text_auto=True,
            aspect="auto",
            color_continuous_scale="Blues",
            title="<b>Correlation Heatmap (Numerical Columns)</b>"
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=380,
            margin=dict(l=40, r=40, t=50, b=40)
        )
        return fig

    @classmethod
    def plot_scatter_relationship(
        cls, df: pd.DataFrame, x_col: str, y_col: str, color_col: Optional[str] = None
    ) -> go.Figure:
        """Scatter plot with optional category coloring."""
        if x_col not in df.columns or y_col not in df.columns:
            return cls._empty_figure("Selected columns unavailable")

        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col if (color_col and color_col in df.columns) else None,
            trendline="ols" if len(df) > 5 else None,
            color_discrete_sequence=CHART_PALETTE,
            title=f"<b>Relationship: {x_col} vs {y_col}</b>",
            opacity=0.75
        )

        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            font=PLOTLY_FONT,
            height=380,
            margin=dict(l=40, r=30, t=50, b=40)
        )
        return fig

    @classmethod
    def _empty_figure(cls, message: str) -> go.Figure:
        """Create empty placeholder figure with informational message."""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="#94A3B8")
        )
        fig.update_layout(
            template=PLOTLY_TEMPLATE,
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            height=250
        )
        return fig

    # -------------------------------------------------------------
    # STATIC MATPLOTLIB RENDERING (For PDF & Excel Reports)
    # -------------------------------------------------------------

    @classmethod
    def generate_static_charts(
        cls, df: pd.DataFrame, analytics: AnalyticsReport, output_dir: str
    ) -> Dict[str, str]:
        """
        Render high-res PNG charts using Matplotlib for embedding into PDF and Excel reports.
        
        Returns:
            Dictionary mapping chart_name -> file_path
        """
        os.makedirs(output_dir, exist_ok=True)
        chart_paths = {}

        # Set consistent styling
        plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
        plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
        plt.rcParams["axes.edgecolor"] = "#E2E8F0"
        plt.rcParams["axes.linewidth"] = 0.8

        # 1. Sales Domain Charts (if applicable)
        if analytics.is_sales_domain and analytics.sales_kpis:
            sales = analytics.sales_kpis

            # A. Monthly Revenue Trend
            if sales.monthly_revenue_trend:
                fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
                months = [d["Month"] for d in sales.monthly_revenue_trend]
                revs = [d["Revenue"] for d in sales.monthly_revenue_trend]
                ax.plot(months, revs, marker="o", color="#2563EB", linewidth=2.5, markersize=6)
                ax.fill_between(months, revs, color="#2563EB", alpha=0.15)
                ax.set_title("Monthly Revenue Trend", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
                ax.set_ylabel("Revenue ($)", fontsize=10, color="#475569")
                ax.tick_params(axis="x", rotation=40, labelsize=8)
                ax.tick_params(axis="y", labelsize=8)
                ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
                fig.tight_layout()
                p = os.path.join(output_dir, "chart_revenue_trend.png")
                fig.savefig(p, bbox_inches="tight")
                plt.close(fig)
                chart_paths["revenue_trend"] = p

            # B. Revenue by Category
            if sales.revenue_by_category:
                fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
                cats = list(sales.revenue_by_category.keys())[:7]
                revs = [sales.revenue_by_category[c] for c in cats]
                colors = ["#2563EB", "#0D9488", "#F59E0B", "#8B5CF6", "#EC4899", "#10B981", "#3B82F6"][:len(cats)]
                bars = ax.bar(cats, revs, color=colors, width=0.55, edgecolor="#1E293B", linewidth=0.5)
                ax.set_title("Revenue by Product Category", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
                ax.set_ylabel("Revenue ($)", fontsize=10, color="#475569")
                ax.tick_params(axis="x", rotation=25, labelsize=8)
                ax.tick_params(axis="y", labelsize=8)
                ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
                fig.tight_layout()
                p = os.path.join(output_dir, "chart_category_revenue.png")
                fig.savefig(p, bbox_inches="tight")
                plt.close(fig)
                chart_paths["category_revenue"] = p

            # C. Regional Revenue Share (Donut)
            if sales.revenue_by_region:
                fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
                regions = list(sales.revenue_by_region.keys())
                revs = list(sales.revenue_by_region.values())
                colors = ["#2563EB", "#0D9488", "#F59E0B", "#10B981", "#8B5CF6"][:len(regions)]
                wedges, texts, autotexts = ax.pie(
                    revs, labels=regions, autopct="%1.1f%%", startangle=140,
                    colors=colors, pctdistance=0.75, textprops=dict(color="#0F172A", fontsize=8)
                )
                plt.setp(autotexts, size=8, weight="bold")
                centre_circle = plt.Circle((0, 0), 0.50, fc="white")
                fig.gca().add_artist(centre_circle)
                ax.set_title("Regional Revenue Distribution", fontsize=12, fontweight="bold", pad=12, color="#0F172A")
                fig.tight_layout()
                p = os.path.join(output_dir, "chart_region_distribution.png")
                fig.savefig(p, bbox_inches="tight")
                plt.close(fig)
                chart_paths["region_distribution"] = p

            # D. Top Products by Revenue
            if sales.top_products_by_revenue:
                fig, ax = plt.subplots(figsize=(8, 4), dpi=150)
                top_p = list(reversed(sales.top_products_by_revenue[:6]))
                p_names = [x["Product"] for x in top_p]
                p_revs = [x["Revenue"] for x in top_p]
                ax.barh(p_names, p_revs, color="#0D9488", height=0.55, edgecolor="#0F766E", linewidth=0.5)
                ax.set_title("Top Products by Sales Volume", fontsize=13, fontweight="bold", pad=12, color="#0F172A")
                ax.set_xlabel("Revenue ($)", fontsize=10, color="#475569")
                ax.tick_params(axis="y", labelsize=8)
                ax.tick_params(axis="x", labelsize=8)
                ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f"${x:,.0f}"))
                fig.tight_layout()
                p = os.path.join(output_dir, "chart_top_products.png")
                fig.savefig(p, bbox_inches="tight")
                plt.close(fig)
                chart_paths["top_products"] = p

        # 2. General Distribution Chart (First numeric column)
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            primary_num = num_cols[0]
            fig, ax = plt.subplots(figsize=(7, 4), dpi=150)
            data_series = pd.to_numeric(df[primary_num], errors="coerce").dropna()
            ax.hist(data_series, bins=30, color="#3B82F6", edgecolor="#1E3A8A", alpha=0.85)
            ax.set_title(f"Frequency Distribution: {primary_num}", fontsize=12, fontweight="bold", pad=12, color="#0F172A")
            ax.set_xlabel(primary_num, fontsize=9, color="#475569")
            ax.set_ylabel("Frequency", fontsize=9, color="#475569")
            ax.tick_params(labelsize=8)
            fig.tight_layout()
            p = os.path.join(output_dir, "chart_distribution.png")
            fig.savefig(p, bbox_inches="tight")
            plt.close(fig)
            chart_paths["distribution"] = p

        # 3. Correlation Heatmap (if >= 2 numeric columns)
        if len(num_cols) >= 2:
            fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
            corr = df[num_cols].corr()
            cax = ax.matshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
            fig.colorbar(cax)
            ax.set_xticks(range(len(num_cols)))
            ax.set_yticks(range(len(num_cols)))
            ax.set_xticklabels(num_cols, rotation=45, ha="left", fontsize=8)
            ax.set_yticklabels(num_cols, fontsize=8)
            for (i, j), z in np.ndenumerate(corr):
                ax.text(j, i, f"{z:.2f}", ha="center", va="center", color="black" if abs(z) < 0.6 else "white", fontsize=8)
            ax.set_title("Correlation Heatmap", fontsize=12, fontweight="bold", pad=20, color="#0F172A")
            fig.tight_layout()
            p = os.path.join(output_dir, "chart_correlation.png")
            fig.savefig(p, bbox_inches="tight")
            plt.close(fig)
            chart_paths["correlation"] = p

        return chart_paths
