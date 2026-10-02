"""
DataClean Pro - Core Data Cleaning Engine
Implements safe, modular, and configurable data transformations:
- Missing value imputation (Mean, Median, Mode, "Unknown", Constant)
- Duplicate row elimination (First, Last, All)
- Text whitespace & casing normalization (with ID/Email exclusion)
- Safe data type inference and conversion
- Date format standardization (YYYY-MM-DD)
- Numerical validation (Negative value fixing, IQR winsorization)
- Comprehensive audit trail / cleaning log generation
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import re
import numpy as np
import pandas as pd

from src.profiler import DataProfiler, DatasetProfile
from src.validator import DataValidator, SemanticMapping
from src.utils import create_cleaning_log_entry, normalize_text_spacing

@dataclass
class CleaningConfig:
    """Configuration options for data cleaning pipeline."""
    # Duplicates
    remove_duplicates: bool = True
    duplicate_keep_strategy: str = "first"  # 'first', 'last'
    
    # Missing Values
    num_missing_strategy: str = "median"  # 'median', 'mean', 'mode', 'zero', 'leave_unchanged'
    cat_missing_strategy: str = "unknown"  # 'unknown', 'mode', 'leave_unchanged'
    custom_missing_rules: Dict[str, str] = field(default_factory=dict)
    
    # Text Standardization
    strip_whitespace: bool = True
    normalize_internal_spaces: bool = True
    casing_strategy: str = "title"  # 'title', 'lower', 'upper', 'preserve'
    standardize_known_categories: bool = True
    
    # Data Types & Dates
    auto_convert_types: bool = True
    standardize_dates: bool = True
    target_date_format: str = "%Y-%m-%d"
    
    # Numerical validation & Outliers
    fix_negative_values: bool = True  # Converts negative quantity/price to positive via abs()
    outlier_strategy: str = "flag_only"  # 'flag_only', 'cap_iqr', 'replace_median'

class DataCleaner:
    """Executes deterministic, non-destructive data cleaning pipelines."""

    KNOWN_SYNONYMS = {
        "payment": {
            "credit card": "Credit Card",
            "credit_card": "Credit Card",
            "cc": "Credit Card",
            "paypal": "PayPal",
            "pay-pal": "PayPal",
            "bank transfer": "Bank Transfer",
            "bank_transfer": "Bank Transfer",
            "wire": "Bank Transfer",
            "wire transfer": "Bank Transfer",
            "cash on delivery": "Cash on Delivery",
            "cod": "Cash on Delivery",
            "debit card": "Debit Card",
            "debit_card": "Debit Card",
            "debit": "Debit Card"
        },
        "status": {
            "completed": "Completed",
            "complete": "Completed",
            "shipped": "Shipped",
            "pending": "Pending",
            "cancelled": "Cancelled",
            "canceled": "Cancelled",
            "refunded": "Refunded"
        }
    }

    @classmethod
    def clean_dataset(
        cls,
        raw_df: pd.DataFrame,
        config: Optional[CleaningConfig] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """
        Execute full cleaning pipeline on a deep copy of raw_df.
        
        Returns:
            Tuple of:
            - cleaned_df (pd.DataFrame)
            - cleaning_log_df (pd.DataFrame)
            - summary_stats (Dict[str, Any])
        """
        if config is None:
            config = CleaningConfig()

        # Step 0: Ensure total data safety with deep copy
        df = raw_df.copy(deep=True)
        raw_stats = {
            "rows": len(raw_df),
            "columns": len(raw_df.columns),
            "missing_cells": int(raw_df.isna().sum().sum()),
            "duplicates": int(raw_df.duplicated().sum())
        }

        cleaning_log: List[Dict[str, Any]] = []
        semantics = DataValidator.detect_semantics(df)

        # 1. Clean Column Names (Strip whitespace)
        orig_cols = list(df.columns)
        clean_cols = [str(c).strip() for c in orig_cols]
        if clean_cols != orig_cols:
            df.columns = clean_cols
            cleaning_log.append(create_cleaning_log_entry(
                operation="Column Header Standardization",
                column="All Headers",
                records_affected=len(clean_cols),
                description="Trimmed leading/trailing whitespaces from column names"
            ))

        # 2. Duplicate Row Removal
        if config.remove_duplicates and raw_stats["duplicates"] > 0:
            dup_count = int(df.duplicated().sum())
            keep_val = "first" if config.duplicate_keep_strategy == "first" else "last"
            df = df.drop_duplicates(keep=keep_val).reset_index(drop=True)
            cleaning_log.append(create_cleaning_log_entry(
                operation="Duplicate Removal",
                column="All Columns",
                records_affected=dup_count,
                description=f"Removed {dup_count} duplicate rows (retained {keep_val} instance)"
            ))

        # 3. Text Standardization (Whitespace, Casing, Category Synonyms)
        df, text_logs = cls._clean_text_fields(df, config, semantics)
        cleaning_log.extend(text_logs)

        # 4. Numerical Validation & Anomaly Correction
        df, num_logs = cls._clean_numerical_fields(df, config, semantics)
        cleaning_log.extend(num_logs)

        # 5. Date Detection & Standardization
        if config.standardize_dates:
            df, date_logs = cls._standardize_date_fields(df, config, semantics)
            cleaning_log.extend(date_logs)

        # 6. Missing Value Imputation
        df, missing_logs = cls._impute_missing_values(df, config)
        cleaning_log.extend(missing_logs)

        # 7. Safe Data Type Standardization
        if config.auto_convert_types:
            df, type_logs = cls._standardize_data_types(df, semantics)
            cleaning_log.extend(type_logs)

        # Recalculate recalculation metrics
        cleaned_missing = int(df.isna().sum().sum())
        cleaned_duplicates = int(df.duplicated().sum())

        summary_stats = {
            "before": {
                "rows": raw_stats["rows"],
                "columns": raw_stats["columns"],
                "missing_cells": raw_stats["missing_cells"],
                "duplicates": raw_stats["duplicates"]
            },
            "after": {
                "rows": len(df),
                "columns": len(df.columns),
                "missing_cells": cleaned_missing,
                "duplicates": cleaned_duplicates
            },
            "records_removed": raw_stats["rows"] - len(df),
            "missing_cells_imputed": raw_stats["missing_cells"] - cleaned_missing,
            "total_operations": len(cleaning_log)
        }

        # Convert cleaning log to DataFrame
        if not cleaning_log:
            cleaning_log.append(create_cleaning_log_entry(
                operation="Quality Inspection",
                column="All",
                records_affected=0,
                description="Dataset inspected. No automated modifications were required."
            ))

        log_df = pd.DataFrame(cleaning_log)

        return df, log_df, summary_stats

    @classmethod
    def _clean_text_fields(
        cls, df: pd.DataFrame, config: CleaningConfig, semantics: SemanticMapping
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Normalize whitespaces and casing on string columns while protecting IDs/Emails."""
        logs: List[Dict[str, Any]] = []

        # Identify columns that should NOT be title-cased
        protected_cols = {
            semantics.email_col,
            "Order_ID", "ID", "id", "UUID", "guid", "URL", "url", "sku", "SKU"
        }

        for col in df.columns:
            if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
                # Skip if column is likely a date (handled in date section)
                if col == semantics.date_col or "date" in col.lower():
                    continue

                non_null_mask = df[col].notna()
                if not non_null_mask.any():
                    continue

                original_series = df[col].copy()
                series = df[col].astype(str)

                # Trim and collapse multiple spaces
                if config.strip_whitespace or config.normalize_internal_spaces:
                    cleaned_str = series.apply(lambda x: normalize_text_spacing(x) if pd.notna(x) else x)
                    changed_mask = non_null_mask & (original_series != cleaned_str)
                    changed_count = int(changed_mask.sum())
                    if changed_count > 0:
                        df.loc[non_null_mask, col] = cleaned_str[non_null_mask]
                        logs.append(create_cleaning_log_entry(
                            operation="Whitespace Normalization",
                            column=col,
                            records_affected=changed_count,
                            description=f"Trimmed leading/trailing whitespaces and collapsed double spaces in {changed_count} rows"
                        ))

                # Special cleaning for Email columns
                if col == semantics.email_col or "email" in col.lower():
                    # Strip and lowercase emails
                    email_cleaned = df.loc[non_null_mask, col].astype(str).str.strip().str.lower()
                    email_changes = int((df.loc[non_null_mask, col] != email_cleaned).sum())
                    if email_changes > 0:
                        df.loc[non_null_mask, col] = email_cleaned
                        logs.append(create_cleaning_log_entry(
                            operation="Email Standardization",
                            column=col,
                            records_affected=email_changes,
                            description=f"Normalized email casing to lowercase for {email_changes} records"
                        ))
                    continue

                # Standardize known categorical synonyms (payment method, status)
                if config.standardize_known_categories:
                    col_lower = col.lower()
                    target_dict = None
                    if "payment" in col_lower:
                        target_dict = cls.KNOWN_SYNONYMS["payment"]
                    elif "status" in col_lower:
                        target_dict = cls.KNOWN_SYNONYMS["status"]

                    if target_dict:
                        synonym_cleaned = df[col].apply(
                            lambda val: target_dict.get(str(val).strip().lower(), val) if pd.notna(val) else val
                        )
                        syn_changed = int((non_null_mask & (df[col] != synonym_cleaned)).sum())
                        if syn_changed > 0:
                            df[col] = synonym_cleaned
                            logs.append(create_cleaning_log_entry(
                                operation="Categorical Synonym Standardization",
                                column=col,
                                records_affected=syn_changed,
                                description=f"Mapped inconsistent representations (e.g. COD/wire/credit_card) to canonical terms ({syn_changed} rows)"
                            ))

                # Casing standardization for general text (excluding protected columns)
                if col not in protected_cols and not any(prot and prot.lower() in col.lower() for prot in ["id", "uuid", "sku", "url", "email"]):
                    # Check unique cardinality
                    uniq_cnt = df[col].nunique(dropna=True)
                    if uniq_cnt < max(50, int(len(df) * 0.1)):
                        if config.casing_strategy == "title":
                            cased_series = df.loc[non_null_mask, col].astype(str).apply(lambda s: s.title())
                        elif config.casing_strategy == "lower":
                            cased_series = df.loc[non_null_mask, col].astype(str).apply(lambda s: s.lower())
                        elif config.casing_strategy == "upper":
                            cased_series = df.loc[non_null_mask, col].astype(str).apply(lambda s: s.upper())
                        else:
                            cased_series = df.loc[non_null_mask, col]

                        cased_changes = int((df.loc[non_null_mask, col] != cased_series).sum())
                        if cased_changes > 0:
                            df.loc[non_null_mask, col] = cased_series
                            logs.append(create_cleaning_log_entry(
                                operation="Text Casing Normalization",
                                column=col,
                                records_affected=cased_changes,
                                description=f"Standardized text casing to {config.casing_strategy.capitalize()} for {cased_changes} records"
                            ))

        return df, logs

    @classmethod
    def _clean_numerical_fields(
        cls, df: pd.DataFrame, config: CleaningConfig, semantics: SemanticMapping
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Validate and adjust numerical columns (negatives in quantities/prices, IQR bounds)."""
        logs: List[Dict[str, Any]] = []
        positive_only_cols = {
            semantics.quantity_col,
            semantics.price_col,
            semantics.sales_col
        }

        for col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                continue

            # 1. Fix Negative Values in strictly positive fields
            if config.fix_negative_values and (col in positive_only_cols or any(k in col.lower() for k in ["quantity", "price", "sales", "revenue"])):
                neg_mask = df[col] < 0
                neg_count = int(neg_mask.sum())
                if neg_count > 0:
                    df.loc[neg_mask, col] = df.loc[neg_mask, col].abs()
                    logs.append(create_cleaning_log_entry(
                        operation="Negative Value Correction",
                        column=col,
                        records_affected=neg_count,
                        description=f"Converted {neg_count} negative entries into valid positive magnitudes using absolute value"
                    ))

            # 2. Outlier treatment
            if config.outlier_strategy in ["cap_iqr", "replace_median"]:
                valid_num = df[col].dropna()
                if len(valid_num) > 10:
                    q25 = float(valid_num.quantile(0.25))
                    q75 = float(valid_num.quantile(0.75))
                    iqr = q75 - q25
                    lower_bound = q25 - (1.5 * iqr)
                    upper_bound = q75 + (1.5 * iqr)

                    outliers_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
                    outliers_count = int(outliers_mask.sum())

                    if outliers_count > 0:
                        if config.outlier_strategy == "cap_iqr":
                            df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
                            logs.append(create_cleaning_log_entry(
                                operation="Outlier Winsorization",
                                column=col,
                                records_affected=outliers_count,
                                description=f"Capped {outliers_count} extreme statistical outliers to IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
                            ))
                        elif config.outlier_strategy == "replace_median":
                            med = float(valid_num.median())
                            df.loc[outliers_mask, col] = med
                            logs.append(create_cleaning_log_entry(
                                operation="Outlier Median Imputation",
                                column=col,
                                records_affected=outliers_count,
                                description=f"Replaced {outliers_count} extreme outliers with column median ({med:.2f})"
                            ))

        return df, logs

    @classmethod
    def _standardize_date_fields(
        cls, df: pd.DataFrame, config: CleaningConfig, semantics: SemanticMapping
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Detect date fields and standardize valid dates to YYYY-MM-DD format."""
        logs: List[Dict[str, Any]] = []

        date_candidates = []
        if semantics.date_col and semantics.date_col in df.columns:
            date_candidates.append(semantics.date_col)
        for col in df.columns:
            if col not in date_candidates and ("date" in col.lower() or "time" in col.lower()):
                date_candidates.append(col)

        for col in date_candidates:
            total_non_null = int(df[col].notna().sum())
            if total_non_null == 0:
                continue

            # Parse with dateutil / pandas flexible parser
            parsed = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
            valid_count = int(parsed.notna().sum())
            invalid_count = total_non_null - valid_count

            # If more than 50% are valid dates, standardize this column
            if valid_count > 0 and (valid_count / total_non_null) >= 0.50:
                # Format valid dates as YYYY-MM-DD string or datetime64[ns]
                formatted_dates = parsed.dt.strftime(config.target_date_format)
                # Keep original value for unparseable entries if desired or set to NaT
                df[col] = formatted_dates
                
                desc = f"Standardized {valid_count} dates to format '{config.target_date_format}'"
                if invalid_count > 0:
                    desc += f"; {invalid_count} unparseable entries coerced to null"

                logs.append(create_cleaning_log_entry(
                    operation="Date Standardization",
                    column=col,
                    records_affected=valid_count,
                    description=desc
                ))

        return df, logs

    @classmethod
    def _impute_missing_values(
        cls, df: pd.DataFrame, config: CleaningConfig
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Apply missing value imputation based on configured strategies."""
        logs: List[Dict[str, Any]] = []

        for col in df.columns:
            null_count = int(df[col].isna().sum())
            if null_count == 0:
                continue

            # Check for column-specific override
            strategy = config.custom_missing_rules.get(col)

            # Numerical columns
            if pd.api.types.is_numeric_dtype(df[col]):
                strat = strategy if strategy else config.num_missing_strategy
                if strat == "leave_unchanged":
                    continue
                elif strat == "median":
                    med_val = df[col].median()
                    df[col] = df[col].fillna(med_val)
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Imputed {null_count} missing entries using column Median ({med_val:.2f})"
                    ))
                elif strat == "mean":
                    mean_val = df[col].mean()
                    df[col] = df[col].fillna(mean_val)
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Imputed {null_count} missing entries using column Mean ({mean_val:.2f})"
                    ))
                elif strat == "mode":
                    mode_val = df[col].mode()
                    val = mode_val.iloc[0] if not mode_val.empty else 0
                    df[col] = df[col].fillna(val)
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Imputed {null_count} missing entries using column Mode ({val})"
                    ))
                elif strat == "zero":
                    df[col] = df[col].fillna(0)
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Filled {null_count} missing entries with constant 0"
                    ))

            # Categorical / String columns
            else:
                strat = strategy if strategy else config.cat_missing_strategy
                if strat == "leave_unchanged":
                    continue
                elif strat == "unknown":
                    df[col] = df[col].fillna("Unknown")
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Imputed {null_count} missing entries with category 'Unknown'"
                    ))
                elif strat == "mode":
                    mode_val = df[col].mode()
                    val = str(mode_val.iloc[0]) if not mode_val.empty else "Unknown"
                    df[col] = df[col].fillna(val)
                    logs.append(create_cleaning_log_entry(
                        operation="Missing Value Imputation",
                        column=col,
                        records_affected=null_count,
                        description=f"Imputed {null_count} missing entries using most frequent category Mode ('{val}')"
                    ))

        return df, logs

    @classmethod
    def _standardize_data_types(
        cls, df: pd.DataFrame, semantics: SemanticMapping
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """Safely cast columns to appropriate types without destructive loss."""
        logs: List[Dict[str, Any]] = []

        for col in df.columns:
            orig_dtype = str(df[col].dtype)

            # Check if integer candidate (e.g. quantity or whole numbers)
            if pd.api.types.is_float_dtype(df[col]):
                # If no fractional values exist and no nulls, convert to int
                non_null = df[col].dropna()
                if not non_null.empty and (non_null % 1 == 0).all():
                    try:
                        df[col] = df[col].astype("Int64")  # Nullable integer
                        logs.append(create_cleaning_log_entry(
                            operation="Data Type Conversion",
                            column=col,
                            records_affected=len(df),
                            description=f"Converted from {orig_dtype} to Integer (Int64)"
                        ))
                    except Exception:
                        pass

            # Check if string numeric should be float
            elif df[col].dtype == object:
                # If it's pure numbers stored as string
                non_null = df[col].dropna()
                if not non_null.empty and col != semantics.email_col and not ("id" in col.lower() or "date" in col.lower()):
                    try:
                        converted = pd.to_numeric(non_null, errors="raise")
                        if (converted % 1 == 0).all():
                            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                            new_t = "Int64"
                        else:
                            df[col] = pd.to_numeric(df[col], errors="coerce").astype("float64")
                            new_t = "float64"

                        logs.append(create_cleaning_log_entry(
                            operation="Data Type Conversion",
                            column=col,
                            records_affected=len(df),
                            description=f"Cast text-formatted numbers to {new_t}"
                        ))
                    except (ValueError, TypeError):
                        pass

        return df, logs
