"""
DataClean Pro - Comprehensive Data Profiling Engine
Performs deep structural and statistical profiling, column classification,
and calculates an objective, multi-factor Data Quality Score.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.validator import DataValidator, SemanticMapping
from src.utils import format_bytes, format_number, format_percent

@dataclass
class ColumnProfile:
    name: str
    inferred_type: str  # 'Numeric', 'Categorical', 'Datetime', 'Boolean', 'Text/ID'
    dtype: str
    total_count: int
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    unique_percentage: float
    memory_bytes: int
    memory_formatted: str
    top_values: List[Tuple[Any, int]]
    sample_values: List[Any]
    # Numerical specific metrics
    min_val: Optional[Any] = None
    max_val: Optional[Any] = None
    mean_val: Optional[float] = None
    median_val: Optional[float] = None
    std_val: Optional[float] = None
    q25_val: Optional[float] = None
    q75_val: Optional[float] = None
    outliers_count: int = 0
    negatives_count: int = 0
    # Text / Date specific
    has_leading_trailing_spaces: bool = False
    invalid_dates_count: int = 0
    invalid_emails_count: int = 0
    quality_issues: List[str] = field(default_factory=list)

@dataclass
class QualityScoreBreakdown:
    overall_score: float
    grade: str
    grade_color: str
    completeness_score: float
    uniqueness_score: float
    consistency_score: float
    validity_score: float
    summary_text: str
    recommendations: List[str] = field(default_factory=list)

@dataclass
class DatasetProfile:
    total_rows: int
    total_columns: int
    total_cells: int
    total_missing_cells: int
    missing_cells_pct: float
    total_duplicate_rows: int
    duplicate_rows_pct: float
    memory_usage_bytes: int
    memory_usage_formatted: str
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    boolean_columns: List[str]
    text_columns: List[str]
    column_profiles: Dict[str, ColumnProfile]
    quality_score: QualityScoreBreakdown
    semantics: SemanticMapping

class DataProfiler:
    """Profiles DataFrames and generates actionable metrics and quality scores."""

    @classmethod
    def profile_dataset(cls, df: pd.DataFrame) -> DatasetProfile:
        """Run complete profiling scan on the dataset."""
        total_rows, total_cols = df.shape
        total_cells = total_rows * total_cols
        total_missing = int(df.isna().sum().sum())
        missing_pct = (total_missing / total_cells * 100.0) if total_cells > 0 else 0.0

        total_duplicates = int(df.duplicated().sum())
        duplicate_pct = (total_duplicates / total_rows * 100.0) if total_rows > 0 else 0.0

        mem_bytes = int(df.memory_usage(deep=True).sum())
        mem_formatted = format_bytes(mem_bytes)

        # Detect semantic mappings
        semantics = DataValidator.detect_semantics(df)

        numeric_cols: List[str] = []
        categorical_cols: List[str] = []
        datetime_cols: List[str] = []
        boolean_cols: List[str] = []
        text_cols: List[str] = []

        col_profiles: Dict[str, ColumnProfile] = {}

        for col in df.columns:
            series = df[col]
            profile = cls._profile_column(series, col, semantics)
            col_profiles[col] = profile

            if profile.inferred_type == "Numeric":
                numeric_cols.append(col)
            elif profile.inferred_type == "Categorical":
                categorical_cols.append(col)
            elif profile.inferred_type == "Datetime":
                datetime_cols.append(col)
            elif profile.inferred_type == "Boolean":
                boolean_cols.append(col)
            else:
                text_cols.append(col)

        # Calculate Quality Score
        quality_score = cls._compute_quality_score(
            total_rows=total_rows,
            total_cols=total_cols,
            total_missing=total_missing,
            total_duplicates=total_duplicates,
            col_profiles=col_profiles
        )

        return DatasetProfile(
            total_rows=total_rows,
            total_columns=total_cols,
            total_cells=total_cells,
            total_missing_cells=total_missing,
            missing_cells_pct=round(missing_pct, 2),
            total_duplicate_rows=total_duplicates,
            duplicate_rows_pct=round(duplicate_pct, 2),
            memory_usage_bytes=mem_bytes,
            memory_usage_formatted=mem_formatted,
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            datetime_columns=datetime_cols,
            boolean_columns=boolean_cols,
            text_columns=text_cols,
            column_profiles=col_profiles,
            quality_score=quality_score,
            semantics=semantics
        )

    @classmethod
    def _profile_column(
        cls, series: pd.Series, col_name: str, semantics: SemanticMapping
    ) -> ColumnProfile:
        """Analyze a single column in detail."""
        total = len(series)
        null_count = int(series.isna().sum())
        non_null_count = total - null_count
        null_pct = (null_count / total * 100.0) if total > 0 else 0.0

        unique_count = int(series.nunique(dropna=True))
        unique_pct = (unique_count / non_null_count * 100.0) if non_null_count > 0 else 0.0

        mem_bytes = int(series.memory_usage(deep=True))
        mem_formatted = format_bytes(mem_bytes)

        # Value counts for top values
        val_counts = series.value_counts(dropna=True).head(5)
        top_values = [(k, int(v)) for k, v in val_counts.items()]
        sample_values = series.dropna().head(5).tolist()

        # Inferred type logic
        inferred_type = "Text/ID"
        issues: List[str] = []

        if null_count > 0:
            issues.append(f"{null_count} missing values ({null_pct:.1f}%)")

        # 1. Check if datetime
        is_date_col = (col_name == semantics.date_col) or ("date" in col_name.lower()) or ("time" in col_name.lower())
        invalid_dates_count = 0
        min_val = None
        max_val = None
        mean_val = None
        median_val = None
        std_val = None
        q25_val = None
        q75_val = None
        outliers_count = 0
        negatives_count = 0
        has_spaces = False
        invalid_emails_count = 0

        # Try date parsing if candidate
        if is_date_col or pd.api.types.is_datetime64_any_dtype(series):
            date_res = DataValidator.validate_dates(series)
            if date_res.valid_count > 0 or is_date_col:
                inferred_type = "Datetime"
                invalid_dates_count = date_res.invalid_count
                if invalid_dates_count > 0:
                    issues.append(f"{invalid_dates_count} invalid date formats")
                min_val = date_res.min_date
                max_val = date_res.max_date

        # 2. Check if numeric
        if inferred_type != "Datetime":
            if pd.api.types.is_numeric_dtype(series):
                inferred_type = "Numeric"
            else:
                # Check if string series can be converted to numeric (>80% convertible)
                if non_null_count > 0:
                    numeric_try = pd.to_numeric(series.dropna(), errors="coerce")
                    if (numeric_try.notna().sum() / non_null_count) > 0.85:
                        inferred_type = "Numeric"

        # Numerical calculations
        if inferred_type == "Numeric":
            num_series = pd.to_numeric(series, errors="coerce").dropna()
            if not num_series.empty:
                min_val = float(num_series.min())
                max_val = float(num_series.max())
                mean_val = float(num_series.mean())
                median_val = float(num_series.median())
                std_val = float(num_series.std()) if len(num_series) > 1 else 0.0
                q25_val = float(num_series.quantile(0.25))
                q75_val = float(num_series.quantile(0.75))

                # Check negatives on quantity or price
                is_pos_field = col_name in [semantics.quantity_col, semantics.price_col, semantics.sales_col]
                num_res = DataValidator.validate_numeric(series, check_negatives=is_pos_field)
                outliers_count = num_res.outliers_iqr_count
                negatives_count = num_res.negative_count

                if is_pos_field and negatives_count > 0:
                    issues.append(f"{negatives_count} negative values detected")
                if outliers_count > 0:
                    issues.append(f"{outliers_count} statistical outliers (IQR)")

        # 3. Check if Boolean
        if inferred_type not in ["Datetime", "Numeric"]:
            if pd.api.types.is_bool_dtype(series):
                inferred_type = "Boolean"
            elif unique_count <= 2 and set(series.dropna().astype(str).str.lower().unique()).issubset({"true", "false", "0", "1", "yes", "no"}):
                inferred_type = "Boolean"

        # 4. Check if Email
        if inferred_type not in ["Datetime", "Numeric", "Boolean"]:
            is_email_col = (col_name == semantics.email_col) or ("email" in col_name.lower())
            if is_email_col or (non_null_count > 0 and series.dropna().astype(str).str.contains("@").mean() > 0.5):
                email_res = DataValidator.validate_emails(series)
                invalid_emails_count = email_res.invalid_count
                if invalid_emails_count > 0:
                    issues.append(f"{invalid_emails_count} malformed email addresses")

        # 5. Check Categorical vs Text/ID
        if inferred_type not in ["Datetime", "Numeric", "Boolean"]:
            # Check for leading/trailing whitespaces in string data
            str_series = series.dropna().astype(str)
            spaces_mask = (str_series != str_series.str.strip()) | str_series.str.contains(r"\s{2,}", regex=True)
            has_spaces = bool(spaces_mask.any())
            if has_spaces:
                issues.append("Inconsistent whitespace / extra spaces")

            # Check casing inconsistency (e.g., lower, UPPER, Title mix)
            unique_lower = set(str_series.str.strip().str.lower().unique())
            if len(unique_lower) < unique_count:
                issues.append(f"Inconsistent capitalization ({unique_count} distinct cases vs {len(unique_lower)} semantic values)")

            # Low cardinality is Categorical
            if unique_count <= max(30, int(total * 0.05)):
                inferred_type = "Categorical"
            else:
                inferred_type = "Text/ID"

        return ColumnProfile(
            name=col_name,
            inferred_type=inferred_type,
            dtype=str(series.dtype),
            total_count=total,
            non_null_count=non_null_count,
            null_count=null_count,
            null_percentage=round(null_pct, 2),
            unique_count=unique_count,
            unique_percentage=round(unique_pct, 2),
            memory_bytes=mem_bytes,
            memory_formatted=mem_formatted,
            top_values=top_values,
            sample_values=sample_values,
            min_val=min_val,
            max_val=max_val,
            mean_val=mean_val,
            median_val=median_val,
            std_val=std_val,
            q25_val=q25_val,
            q75_val=q75_val,
            outliers_count=outliers_count,
            negatives_count=negatives_count,
            has_leading_trailing_spaces=has_spaces,
            invalid_dates_count=invalid_dates_count,
            invalid_emails_count=invalid_emails_count,
            quality_issues=issues
        )

    @classmethod
    def _compute_quality_score(
        cls,
        total_rows: int,
        total_cols: int,
        total_missing: int,
        total_duplicates: int,
        col_profiles: Dict[str, ColumnProfile]
    ) -> QualityScoreBreakdown:
        """Compute objective 0-100% Data Quality Score across 4 dimensions."""
        if total_rows == 0 or total_cols == 0:
            return QualityScoreBreakdown(
                overall_score=0.0,
                grade="Critical",
                grade_color="#EF4444",
                completeness_score=0.0,
                uniqueness_score=0.0,
                consistency_score=0.0,
                validity_score=0.0,
                summary_text="Empty dataset.",
                recommendations=["Upload a non-empty dataset."]
            )

        total_cells = total_rows * total_cols

        # 1. Completeness (Weight: 35%)
        completeness = max(0.0, min(100.0, (1.0 - (total_missing / total_cells)) * 100.0))

        # 2. Uniqueness (Weight: 25%)
        uniqueness = max(0.0, min(100.0, (1.0 - (total_duplicates / total_rows)) * 100.0))

        # 3. Consistency (Weight: 20%) - whitespace, mixed casing
        inconsistent_cols = 0
        for p in col_profiles.values():
            if p.has_leading_trailing_spaces or any("Inconsistent capitalization" in is_s for is_s in p.quality_issues):
                inconsistent_cols += 1
        consistency = max(0.0, min(100.0, (1.0 - (inconsistent_cols / total_cols)) * 100.0))

        # 4. Validity (Weight: 20%) - invalid dates, invalid emails, negative quantity/prices
        total_validation_checks = 0
        total_validation_failures = 0
        for p in col_profiles.values():
            if p.invalid_dates_count > 0:
                total_validation_checks += p.total_count
                total_validation_failures += p.invalid_dates_count
            if p.invalid_emails_count > 0:
                total_validation_checks += p.total_count
                total_validation_failures += p.invalid_emails_count
            if p.negatives_count > 0:
                total_validation_checks += p.total_count
                total_validation_failures += p.negatives_count

        if total_validation_checks > 0:
            validity = max(0.0, min(100.0, (1.0 - (total_validation_failures / total_validation_checks)) * 100.0))
        else:
            validity = 100.0

        # Weighted Composite Score
        overall = (completeness * 0.35) + (uniqueness * 0.25) + (consistency * 0.20) + (validity * 0.20)
        overall = round(overall, 1)

        recommendations: List[str] = []
        if total_duplicates > 0:
            recommendations.append(f"Remove {total_duplicates} duplicate records.")
        if total_missing > 0:
            recommendations.append(f"Impute or handle {total_missing} missing cells across columns.")
        if inconsistent_cols > 0:
            recommendations.append("Apply text standardization to fix whitespace and casing inconsistencies.")
        if total_validation_failures > 0:
            recommendations.append("Resolve format anomalies in date, email, or negative quantity fields.")

        if not recommendations:
            recommendations.append("Dataset meets professional quality benchmarks.")

        # Determine Grade
        if overall >= 90:
            grade = "Excellent"
            color = "#10B981"  # Emerald
            summary = "Dataset is in excellent condition with minimal defects."
        elif overall >= 75:
            grade = "Good"
            color = "#2563EB"  # Blue
            summary = "Dataset is in good shape with moderate cleaning recommended."
        elif overall >= 60:
            grade = "Fair"
            color = "#F59E0B"  # Amber
            summary = "Notable data hygiene issues detected. Data cleaning required."
        elif overall >= 40:
            grade = "Poor"
            color = "#F97316"  # Orange
            summary = "Substantial missingness, duplicates, or formatting errors require remediation."
        else:
            grade = "Critical"
            color = "#EF4444"  # Red
            summary = "Severe data-quality problems detected across multiple dimensions."

        return QualityScoreBreakdown(
            overall_score=overall,
            grade=grade,
            grade_color=color,
            completeness_score=round(completeness, 1),
            uniqueness_score=round(uniqueness, 1),
            consistency_score=round(consistency, 1),
            validity_score=round(validity, 1),
            summary_text=summary,
            recommendations=recommendations
        )
