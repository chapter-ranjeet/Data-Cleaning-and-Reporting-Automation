"""
DataClean Pro - Data Validation & Semantic Inference Module
Provides validations for emails, dates, numerical bounds, outlier detection,
and intelligent domain column detection.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set
import re
import numpy as np
import pandas as pd
from src.utils import normalize_column_name

# Standard RFC-compliant email regex
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

@dataclass
class EmailValidationResult:
    column: str
    total_records: int
    valid_count: int
    invalid_count: int
    missing_count: int
    valid_rate: float
    sample_invalids: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DateValidationResult:
    column: str
    total_records: int
    valid_count: int
    invalid_count: int
    missing_count: int
    valid_rate: float
    sample_invalids: List[Dict[str, Any]] = field(default_factory=list)
    min_date: Optional[str] = None
    max_date: Optional[str] = None

@dataclass
class NumericalValidationResult:
    column: str
    total_records: int
    negative_count: int
    zero_count: int
    positive_count: int
    missing_count: int
    outliers_iqr_count: int
    lower_bound_iqr: float
    upper_bound_iqr: float
    sample_outliers: List[Dict[str, Any]] = field(default_factory=list)
    has_negative_issues: bool = False

@dataclass
class SemanticMapping:
    sales_col: Optional[str] = None
    price_col: Optional[str] = None
    quantity_col: Optional[str] = None
    date_col: Optional[str] = None
    category_col: Optional[str] = None
    product_col: Optional[str] = None
    region_col: Optional[str] = None
    customer_col: Optional[str] = None
    email_col: Optional[str] = None
    payment_col: Optional[str] = None
    status_col: Optional[str] = None

    @property
    def is_sales_dataset(self) -> bool:
        """Determines if the dataset has sufficient sales/commerce attributes."""
        sales_indicators = [self.sales_col, self.price_col, self.quantity_col]
        has_monetary = any(x is not None for x in sales_indicators)
        has_dimension = any(x is not None for x in [self.category_col, self.product_col, self.date_col])
        return has_monetary and has_dimension

class DataValidator:
    """Performs deep validation scans and semantic analysis on tabular data."""

    # Keywords for semantic column matching
    SEMANTIC_KEYWORDS = {
        "sales_col": ["sales", "revenue", "order_total", "total_sales", "total_amount", "grand_total", "turnover"],
        "price_col": ["unit_price", "price", "unitprice", "rate", "cost_per_unit", "item_price"],
        "quantity_col": ["quantity", "qty", "units_sold", "units", "item_count", "pieces", "count"],
        "date_col": ["order_date", "transaction_date", "invoice_date", "sale_date", "date", "created_at", "timestamp"],
        "category_col": ["category", "product_category", "dept", "department", "genre", "item_group", "type"],
        "product_col": ["product", "product_name", "item", "item_name", "sku", "product_title", "description"],
        "region_col": ["region", "territory", "zone", "area", "market", "country", "state", "city", "location"],
        "customer_col": ["customer_name", "customer", "client_name", "client", "buyer", "user_name"],
        "email_col": ["customer_email", "email", "contact_email", "user_email", "e_mail"],
        "payment_col": ["payment_method", "payment_type", "payment", "mode_of_payment", "pay_method"],
        "status_col": ["order_status", "status", "delivery_status", "fulfillment_status", "state"]
    }

    @classmethod
    def detect_semantics(cls, df: pd.DataFrame) -> SemanticMapping:
        """Intelligently map DataFrame columns to standard business semantics."""
        mapping_dict = {}
        assigned_cols: Set[str] = set()

        # Build normalized lookups
        norm_to_orig = {normalize_column_name(col): col for col in df.columns}
        
        for semantic_key, keywords in cls.SEMANTIC_KEYWORDS.items():
            best_match = None
            
            # Exact match first
            for kw in keywords:
                if kw in norm_to_orig and norm_to_orig[kw] not in assigned_cols:
                    best_match = norm_to_orig[kw]
                    break
            
            # Substring / partial match second
            if best_match is None:
                for kw in keywords:
                    for norm_name, orig_name in norm_to_orig.items():
                        if orig_name in assigned_cols:
                            continue
                        if kw in norm_name or norm_name in kw:
                            best_match = orig_name
                            break
                    if best_match is not None:
                        break
            
            if best_match is not None:
                assigned_cols.add(best_match)
                mapping_dict[semantic_key] = best_match
            else:
                mapping_dict[semantic_key] = None

        return SemanticMapping(**mapping_dict)

    @classmethod
    def validate_emails(cls, series: pd.Series) -> EmailValidationResult:
        """Validate email formatting in a series."""
        total = len(series)
        missing = int(series.isna().sum())
        non_null_series = series.dropna().astype(str).str.strip()
        
        valid_count = 0
        invalid_count = 0
        sample_invalids = []

        for idx, val in non_null_series.items():
            if EMAIL_REGEX.match(val):
                valid_count += 1
            else:
                invalid_count += 1
                if len(sample_invalids) < 10:
                    sample_invalids.append({"Row": idx, "Value": val, "Reason": "Malformed email format"})

        valid_rate = (valid_count / (total - missing)) if (total - missing) > 0 else 0.0

        return EmailValidationResult(
            column=series.name,
            total_records=total,
            valid_count=valid_count,
            invalid_count=invalid_count,
            missing_count=missing,
            valid_rate=round(valid_rate * 100, 2),
            sample_invalids=sample_invalids
        )

    @classmethod
    def validate_dates(cls, series: pd.Series) -> DateValidationResult:
        """Validate date strings in a series."""
        total = len(series)
        missing = int(series.isna().sum())
        non_null_series = series.dropna()

        # Attempt pd.to_datetime with coerce
        parsed = pd.to_datetime(non_null_series, errors="coerce", dayfirst=True)
        valid_mask = parsed.notna()
        valid_count = int(valid_mask.sum())
        invalid_count = int((~valid_mask).sum())

        sample_invalids = []
        if invalid_count > 0:
            invalid_series = non_null_series[~valid_mask]
            for idx, val in invalid_series.head(10).items():
                sample_invalids.append({"Row": idx, "Value": str(val), "Reason": "Unparseable date expression"})

        valid_rate = (valid_count / (total - missing)) if (total - missing) > 0 else 0.0

        min_d = parsed.min().strftime("%Y-%m-%d") if valid_count > 0 else None
        max_d = parsed.max().strftime("%Y-%m-%d") if valid_count > 0 else None

        return DateValidationResult(
            column=series.name,
            total_records=total,
            valid_count=valid_count,
            invalid_count=invalid_count,
            missing_count=missing,
            valid_rate=round(valid_rate * 100, 2),
            sample_invalids=sample_invalids,
            min_date=min_d,
            max_date=max_d
        )

    @classmethod
    def validate_numeric(
        cls, series: pd.Series, check_negatives: bool = True
    ) -> NumericalValidationResult:
        """Validate numerical column for negative anomalies and IQR outliers."""
        total = len(series)
        missing = int(series.isna().sum())
        
        # Convert to numeric safely
        num_series = pd.to_numeric(series, errors="coerce").dropna()
        if num_series.empty:
            return NumericalValidationResult(
                column=series.name,
                total_records=total,
                negative_count=0,
                zero_count=0,
                positive_count=0,
                missing_count=missing,
                outliers_iqr_count=0,
                lower_bound_iqr=0.0,
                upper_bound_iqr=0.0
            )

        negative_count = int((num_series < 0).sum())
        zero_count = int((num_series == 0).sum())
        positive_count = int((num_series > 0).sum())

        # IQR Outliers
        q25 = float(num_series.quantile(0.25))
        q75 = float(num_series.quantile(0.75))
        iqr = q75 - q25
        lower_bound = q25 - (1.5 * iqr)
        upper_bound = q75 + (1.5 * iqr)

        outlier_mask = (num_series < lower_bound) | (num_series > upper_bound)
        outlier_count = int(outlier_mask.sum())

        sample_outliers = []
        if outlier_count > 0:
            outlier_series = num_series[outlier_mask]
            for idx, val in outlier_series.head(10).items():
                reason = "Below Q1 - 1.5*IQR" if val < lower_bound else "Above Q3 + 1.5*IQR"
                sample_outliers.append({"Row": idx, "Value": float(val), "Reason": reason})

        has_neg_issue = check_negatives and (negative_count > 0)

        return NumericalValidationResult(
            column=series.name,
            total_records=total,
            negative_count=negative_count,
            zero_count=zero_count,
            positive_count=positive_count,
            missing_count=missing,
            outliers_iqr_count=outlier_count,
            lower_bound_iqr=round(lower_bound, 2),
            upper_bound_iqr=round(upper_bound, 2),
            sample_outliers=sample_outliers,
            has_negative_issues=has_neg_issue
        )
