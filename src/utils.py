"""
DataClean Pro - Utility Functions & Constants
Provides helper functions for formatting, string manipulation, color palettes, and audit logging.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import re
import datetime
import numpy as np
import pandas as pd

# Professional corporate theme color palette
THEME_COLORS = {
    "primary": "#1E3A8A",      # Deep Royal Navy
    "secondary": "#2563EB",    # Electric Blue
    "accent": "#0D9488",       # Vibrant Teal
    "success": "#10B981",      # Emerald Green
    "warning": "#F59E0B",      # Warm Amber
    "danger": "#EF4444",       # Coral Red
    "info": "#06B6D4",          # Cyan
    "bg_light": "#F8FAFC",      # Off-white Slate
    "card_bg": "#FFFFFF",       # Pure White
    "border": "#E2E8F0",       # Slate Border
    "text_dark": "#0F172A",    # Dark Slate
    "text_muted": "#64748B",   # Medium Slate
}

CHART_PALETTE = [
    "#2563EB", "#0D9488", "#F59E0B", "#8B5CF6", "#EC4899",
    "#10B981", "#3B82F6", "#6366F1", "#14B8A6", "#F97316"
]

def format_bytes(size_bytes: Union[int, float]) -> str:
    """Format byte count into human-readable size string."""
    if size_bytes is None or np.isnan(size_bytes):
        return "0 B"
    size_bytes = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:3.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_number(val: Union[int, float, None]) -> str:
    """Format large numbers with thousands commas or compact notation."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
        if abs(val) >= 1_000_000:
            return f"{val / 1_000_000:.2f}M"
        elif abs(val) >= 1_000:
            return f"{val:,.0f}" if val.is_integer() else f"{val:,.2f}"
        else:
            return f"{val:.0f}" if val.is_integer() else f"{val:.2f}"
    except (ValueError, TypeError):
        return str(val)

def format_currency(val: Union[int, float, None], symbol: str = "$") -> str:
    """Format number as currency."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
        if abs(val) >= 1_000_000:
            return f"{symbol}{val / 1_000_000:.2f}M"
        return f"{symbol}{val:,.2f}"
    except (ValueError, TypeError):
        return str(val)

def format_percent(val: Union[int, float, None]) -> str:
    """Format ratio or fraction as percentage string."""
    if val is None or pd.isna(val):
        return "0.0%"
    try:
        return f"{float(val):.1f}%"
    except (ValueError, TypeError):
        return "0.0%"

def normalize_column_name(col: Any) -> str:
    """Standardize column names to lower case with underscores."""
    s = str(col).strip().lower()
    s = re.sub(r"[^\w\s]", "", s)
    s = re.sub(r"\s+", "_", s)
    return s

def normalize_text_spacing(val: Any) -> Any:
    """Trim leading/trailing whitespaces and collapse multiple internal whitespaces."""
    if pd.isna(val):
        return val
    if isinstance(val, str):
        cleaned = re.sub(r"\s+", " ", val).strip()
        return cleaned
    return val

def create_cleaning_log_entry(
    operation: str,
    column: str,
    records_affected: int,
    description: str,
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """Helper to structure an audit log entry for the data cleaning log."""
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    return {
        "Timestamp": timestamp,
        "Operation": operation,
        "Column": column,
        "Records Affected": int(records_affected),
        "Description": description
    }
