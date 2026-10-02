"""
DataClean Pro - Robust Data Loader Module
Handles importing CSV, Excel (.xlsx, .xls) files with multi-encoding fallback,
automatic separator sniffing, and comprehensive metadata extraction.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
import io
import os
import csv
import pandas as pd
import numpy as np

from src.utils import format_bytes

@dataclass
class DatasetMetadata:
    """Stores detailed metadata about loaded datasets."""
    file_name: str
    file_type: str
    file_size_bytes: int
    file_size_formatted: str
    row_count: int
    column_count: int
    memory_usage_bytes: int
    memory_usage_formatted: str
    columns: List[str]
    sheet_names: Optional[List[str]] = None
    selected_sheet: Optional[str] = None
    encoding_detected: Optional[str] = None
    delimiter_detected: Optional[str] = None
    has_empty_cells: bool = False
    missing_cells_total: int = 0
    duplicate_rows_total: int = 0
    load_warnings: List[str] = field(default_factory=list)

class DataLoader:
    """Production-grade data loader with format detection and fallback mechanisms."""

    COMMON_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "iso-8859-1"]

    @classmethod
    def load_dataset(
        cls,
        file_source: Union[str, io.BytesIO, Any],
        file_name: Optional[str] = None,
        sheet_name: Optional[Union[str, int]] = 0
    ) -> Tuple[Optional[pd.DataFrame], Optional[DatasetMetadata], Optional[str]]:
        """
        Load dataset from file path, UploadedFile, or BytesIO.
        
        Returns:
            Tuple of (DataFrame, DatasetMetadata, ErrorMessage)
            If loading succeeds, ErrorMessage is None.
            If loading fails, DataFrame is None and ErrorMessage contains friendly text.
        """
        try:
            # Determine file name and raw bytes
            if hasattr(file_source, "name") and file_name is None:
                file_name = file_source.name
            elif file_name is None and isinstance(file_source, str):
                file_name = os.path.basename(file_source)
            elif file_name is None:
                file_name = "dataset.csv"

            extension = os.path.splitext(file_name)[1].lower()

            # Read raw bytes to calculate exact size and allow multiple read passes
            if isinstance(file_source, (str, os.PathLike)):
                if not os.path.exists(file_source):
                    return None, None, f"⚠ File '{file_source}' does not exist."
                file_size_bytes = os.path.getsize(file_source)
                if file_size_bytes == 0:
                    return None, None, "⚠ The uploaded file is completely empty (0 bytes)."
                with open(file_source, "rb") as f:
                    raw_bytes = f.read()
            elif hasattr(file_source, "getvalue"):
                raw_bytes = file_source.getvalue()
                file_size_bytes = len(raw_bytes)
            elif hasattr(file_source, "read"):
                file_source.seek(0)
                raw_bytes = file_source.read()
                file_size_bytes = len(raw_bytes)
            else:
                return None, None, "⚠ Unsupported file input format."

            if file_size_bytes == 0:
                return None, None, "⚠ The uploaded file contains no data (0 bytes)."

            # Parse based on extension
            warnings: List[str] = []
            df: Optional[pd.DataFrame] = None
            encoding_used: Optional[str] = None
            delimiter_used: Optional[str] = None
            sheet_names_list: Optional[List[str]] = None
            active_sheet: Optional[str] = None

            if extension in [".xlsx", ".xls"]:
                # Excel file
                excel_io = io.BytesIO(raw_bytes)
                try:
                    excel_file = pd.ExcelFile(excel_io)
                    sheet_names_list = excel_file.sheet_names
                    if not sheet_names_list:
                        return None, None, "⚠ The Excel workbook contains no valid sheets."
                    
                    target_sheet = sheet_name if sheet_name in sheet_names_list else sheet_names_list[0]
                    active_sheet = str(target_sheet)
                    df = excel_file.parse(sheet_name=target_sheet)
                except Exception as excel_err:
                    return None, None, f"⚠ Unable to parse Excel file: {str(excel_err)}. Please verify the workbook is not password protected or corrupted."

            elif extension in [".csv", ".txt", ".tsv", ""]:
                # CSV or plain delimited file
                df, encoding_used, delimiter_used, csv_err = cls._read_csv_with_fallbacks(raw_bytes)
                if csv_err:
                    return None, None, csv_err
            else:
                return None, None, f"⚠ Unsupported file extension '{extension}'. Please upload a .csv, .xlsx, or .xls file."

            if df is None or df.empty:
                return None, None, "⚠ The dataset was loaded but contains 0 rows or is empty."

            # Clean whitespace from column names automatically (prevent hidden bugs with " Column ")
            df.columns = [str(c).strip() for c in df.columns]

            # Compute dataset metrics
            row_count, col_count = df.shape
            mem_bytes = int(df.memory_usage(deep=True).sum())
            missing_cells = int(df.isna().sum().sum())
            duplicate_rows = int(df.duplicated().sum())

            metadata = DatasetMetadata(
                file_name=file_name,
                file_type=extension.replace(".", "").upper() if extension else "CSV",
                file_size_bytes=file_size_bytes,
                file_size_formatted=format_bytes(file_size_bytes),
                row_count=row_count,
                column_count=col_count,
                memory_usage_bytes=mem_bytes,
                memory_usage_formatted=format_bytes(mem_bytes),
                columns=list(df.columns),
                sheet_names=sheet_names_list,
                selected_sheet=active_sheet,
                encoding_detected=encoding_used,
                delimiter_detected=delimiter_used,
                has_empty_cells=(missing_cells > 0),
                missing_cells_total=missing_cells,
                duplicate_rows_total=duplicate_rows,
                load_warnings=warnings
            )

            return df, metadata, None

        except Exception as e:
            return None, None, f"⚠ Unexpected error loading dataset: {str(e)}"

    @classmethod
    def _read_csv_with_fallbacks(
        cls, raw_bytes: bytes
    ) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str], Optional[str]]:
        """Attempt to read CSV data trying multiple encodings and separator sniffing."""
        # Try sniffing delimiter from text sample
        sample_size = min(len(raw_bytes), 32768)
        sample_bytes = raw_bytes[:sample_size]
        
        last_error = None
        for enc in cls.COMMON_ENCODINGS:
            try:
                sample_text = sample_bytes.decode(enc)
                # Sniff delimiter
                try:
                    dialect = csv.Sniffer().sniff(sample_text[:4096])
                    detected_delimiter = dialect.delimiter
                except Exception:
                    # Fallback common delimiters
                    if "\t" in sample_text and sample_text.count("\t") > sample_text.count(","):
                        detected_delimiter = "\t"
                    elif ";" in sample_text and sample_text.count(";") > sample_text.count(","):
                        detected_delimiter = ";"
                    elif "|" in sample_text and sample_text.count("|") > sample_text.count(","):
                        detected_delimiter = "|"
                    else:
                        detected_delimiter = ","

                # Parse full DataFrame
                csv_io = io.StringIO(raw_bytes.decode(enc))
                df = pd.read_csv(
                    csv_io,
                    sep=detected_delimiter,
                    engine="python",
                    on_bad_lines="skip"
                )
                return df, enc, detected_delimiter, None
            except UnicodeDecodeError:
                continue
            except Exception as e:
                last_error = str(e)
                continue

        return None, None, None, f"⚠ Unable to parse CSV with standard encodings: {last_error or 'Unknown encoding error'}"
