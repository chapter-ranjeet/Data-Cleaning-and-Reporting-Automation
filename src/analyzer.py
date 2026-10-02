"""
DataClean Pro - Domain-Adaptive Data Analytics Engine
Performs general summary statistics, correlation computations, and
domain-specific business KPIs (e.g. Sales, E-Commerce, Retail).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.validator import DataValidator, SemanticMapping
from src.utils import format_currency, format_number, format_percent

@dataclass
class SalesAnalytics:
    total_revenue: float
    total_revenue_formatted: str
    avg_order_value: float
    avg_order_value_formatted: str
    total_quantity_sold: int
    total_quantity_formatted: str
    total_orders: int
    total_orders_formatted: str
    unique_customers: int
    revenue_by_category: Dict[str, float] = field(default_factory=dict)
    revenue_by_region: Dict[str, float] = field(default_factory=dict)
    top_products_by_revenue: List[Dict[str, Any]] = field(default_factory=list)
    payment_method_distribution: Dict[str, int] = field(default_factory=dict)
    monthly_revenue_trend: List[Dict[str, Any]] = field(default_factory=list)
    order_status_distribution: Dict[str, int] = field(default_factory=dict)

@dataclass
class GenericAnalytics:
    summary_statistics: pd.DataFrame
    categorical_distributions: Dict[str, pd.DataFrame]
    correlation_matrix: Optional[pd.DataFrame]
    top_grouped_insights: Optional[pd.DataFrame]

@dataclass
class AnalyticsReport:
    is_sales_domain: bool
    general_kpis: Dict[str, Any]
    sales_kpis: Optional[SalesAnalytics] = None
    generic_kpis: Optional[GenericAnalytics] = None
    semantics: SemanticMapping = field(default_factory=SemanticMapping)

class DataAnalyzer:
    """Computes multidimensional business and statistical analytics."""

    @classmethod
    def analyze_dataset(cls, df: pd.DataFrame) -> AnalyticsReport:
        """Run deep statistical analysis adapted to dataset domain."""
        semantics = DataValidator.detect_semantics(df)

        # General KPIs
        total_rows = len(df)
        total_cols = len(df.columns)
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c]) and df[c].dtype != "datetime64[ns]"]
        missing_count = int(df.isna().sum().sum())
        duplicate_count = int(df.duplicated().sum())

        general_kpis = {
            "total_records": total_rows,
            "total_columns": total_cols,
            "numeric_columns_count": len(num_cols),
            "categorical_columns_count": len(cat_cols),
            "missing_values": missing_count,
            "duplicate_records": duplicate_count,
            "data_density": round((1.0 - (missing_count / (total_rows * total_cols if total_rows * total_cols > 0 else 1))) * 100, 2)
        }

        # Check domain: Is it a sales dataset?
        is_sales = semantics.is_sales_dataset

        sales_kpis = None
        generic_kpis = None

        if is_sales:
            sales_kpis = cls._compute_sales_analytics(df, semantics)

        # Always compute generic analytics for statistical depth
        generic_kpis = cls._compute_generic_analytics(df, num_cols, cat_cols)

        return AnalyticsReport(
            is_sales_domain=is_sales,
            general_kpis=general_kpis,
            sales_kpis=sales_kpis,
            generic_kpis=generic_kpis,
            semantics=semantics
        )

    @classmethod
    def _compute_sales_analytics(cls, df: pd.DataFrame, semantics: SemanticMapping) -> SalesAnalytics:
        """Calculate high-impact e-commerce and retail metrics."""
        # Determine revenue column or compute from quantity * price
        sales_col = semantics.sales_col
        price_col = semantics.price_col
        qty_col = semantics.quantity_col

        sales_series = None
        if sales_col and sales_col in df.columns:
            sales_series = pd.to_numeric(df[sales_col], errors="coerce").fillna(0)
        elif price_col and qty_col and price_col in df.columns and qty_col in df.columns:
            p = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
            q = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
            sales_series = p * q
        else:
            # Fallback to any positive numeric column
            num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
            if num_cols:
                sales_series = pd.to_numeric(df[num_cols[0]], errors="coerce").fillna(0)
            else:
                sales_series = pd.Series([0] * len(df))

        total_rev = float(sales_series.sum())
        total_orders = len(df)
        avg_rev = float(sales_series.mean()) if total_orders > 0 else 0.0

        # Quantity
        total_qty = 0
        if qty_col and qty_col in df.columns:
            total_qty = int(pd.to_numeric(df[qty_col], errors="coerce").fillna(0).sum())
        else:
            total_qty = total_orders

        # Unique Customers
        cust_col = semantics.customer_col
        uniq_cust = int(df[cust_col].nunique()) if cust_col and cust_col in df.columns else total_orders

        # Revenue by Category
        rev_by_cat = {}
        if semantics.category_col and semantics.category_col in df.columns:
            cat_grouped = df.groupby(semantics.category_col)[sales_series.name or "Revenue"].sum() if sales_series.name in df.columns else pd.Series(sales_series.values, index=df[semantics.category_col]).groupby(level=0).sum()
            rev_by_cat = {str(k): round(float(v), 2) for k, v in cat_grouped.sort_values(ascending=False).items()}

        # Revenue by Region
        rev_by_reg = {}
        if semantics.region_col and semantics.region_col in df.columns:
            reg_grouped = pd.Series(sales_series.values, index=df[semantics.region_col]).groupby(level=0).sum()
            rev_by_reg = {str(k): round(float(v), 2) for k, v in reg_grouped.sort_values(ascending=False).items()}

        # Top 10 Products by Revenue
        top_prods = []
        if semantics.product_col and semantics.product_col in df.columns:
            prod_grouped = pd.Series(sales_series.values, index=df[semantics.product_col]).groupby(level=0).sum().sort_values(ascending=False).head(10)
            for prod_name, p_rev in prod_grouped.items():
                top_prods.append({
                    "Product": str(prod_name),
                    "Revenue": round(float(p_rev), 2),
                    "Revenue_Formatted": format_currency(p_rev)
                })

        # Payment Method Distribution
        pay_dist = {}
        if semantics.payment_col and semantics.payment_col in df.columns:
            pay_counts = df[semantics.payment_col].value_counts().head(10)
            pay_dist = {str(k): int(v) for k, v in pay_counts.items()}

        # Order Status Distribution
        stat_dist = {}
        if semantics.status_col and semantics.status_col in df.columns:
            stat_counts = df[semantics.status_col].value_counts().head(10)
            stat_dist = {str(k): int(v) for k, v in stat_counts.items()}

        # Monthly Revenue Trend
        monthly_trend = []
        if semantics.date_col and semantics.date_col in df.columns:
            date_series = pd.to_datetime(df[semantics.date_col], errors="coerce")
            valid_dates_df = pd.DataFrame({"Date": date_series, "Sales": sales_series}).dropna(subset=["Date"])
            if not valid_dates_df.empty:
                valid_dates_df["YearMonth"] = valid_dates_df["Date"].dt.to_period("M").astype(str)
                month_grouped = valid_dates_df.groupby("YearMonth")["Sales"].agg(["sum", "count"]).reset_index()
                month_grouped = month_grouped.sort_values("YearMonth")
                for _, row in month_grouped.iterrows():
                    monthly_trend.append({
                        "Month": str(row["YearMonth"]),
                        "Revenue": round(float(row["sum"]), 2),
                        "Orders": int(row["count"])
                    })

        return SalesAnalytics(
            total_revenue=round(total_rev, 2),
            total_revenue_formatted=format_currency(total_rev),
            avg_order_value=round(avg_rev, 2),
            avg_order_value_formatted=format_currency(avg_rev),
            total_quantity_sold=total_qty,
            total_quantity_formatted=format_number(total_qty),
            total_orders=total_orders,
            total_orders_formatted=format_number(total_orders),
            unique_customers=uniq_cust,
            revenue_by_category=rev_by_cat,
            revenue_by_region=rev_by_reg,
            top_products_by_revenue=top_prods,
            payment_method_distribution=pay_dist,
            monthly_revenue_trend=monthly_trend,
            order_status_distribution=stat_dist
        )

    @classmethod
    def _compute_generic_analytics(
        cls, df: pd.DataFrame, num_cols: List[str], cat_cols: List[str]
    ) -> GenericAnalytics:
        """Calculate general descriptive and correlation statistics."""
        # Summary statistics
        if num_cols:
            desc_df = df[num_cols].describe().T
            desc_df["skew"] = df[num_cols].skew()
            desc_df = desc_df.round(2)
        else:
            desc_df = pd.DataFrame()

        # Categorical distributions
        cat_dists = {}
        for c in cat_cols[:8]:
            counts = df[c].value_counts(dropna=False).head(10).reset_index()
            counts.columns = [c, "Count"]
            counts["Percentage"] = (counts["Count"] / len(df) * 100).round(1)
            cat_dists[c] = counts

        # Correlation matrix
        corr_matrix = None
        if len(num_cols) >= 2:
            corr_matrix = df[num_cols].corr().round(2)

        # Top Grouped Insights (Aggregate dominant numeric by dominant categorical)
        top_grouped = None
        if num_cols and cat_cols:
            primary_cat = cat_cols[0]
            primary_num = num_cols[0]
            # Group by top 10 categories
            top_grouped = df.groupby(primary_cat)[primary_num].agg(["count", "mean", "sum"]).round(2).reset_index()
            top_grouped = top_grouped.sort_values(by="sum", ascending=False).head(10)

        return GenericAnalytics(
            summary_statistics=desc_df,
            categorical_distributions=cat_dists,
            correlation_matrix=corr_matrix,
            top_grouped_insights=top_grouped
        )
