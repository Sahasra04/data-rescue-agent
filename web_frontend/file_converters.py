"""
File format conversion for the Data Rescue Agent.

Converts Excel (.xlsx) and JSON files into CSV text internally, so the
existing detection/cleaning logic (built around CSV) can handle them too
without needing separate code paths for every format.
"""

import os
import csv
import io
import json
import openpyxl


def convert_to_csv_text(file_path: str) -> str:
    """Reads a file (CSV, XLSX, or JSON) and returns its content as CSV text.

    Raises a clear error for unsupported file types.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".csv":
        with open(file_path, "r") as f:
            return f.read()

    elif ext == ".xlsx":
        workbook = openpyxl.load_workbook(file_path, data_only=True)
        sheet = workbook.active
        output = io.StringIO()
        writer = csv.writer(output)
        for row in sheet.iter_rows(values_only=True):
            writer.writerow(["" if cell is None else cell for cell in row])
        return output.getvalue()

    elif ext == ".json":
        with open(file_path, "r") as f:
            data = json.load(f)
        if not isinstance(data, list) or not data:
            raise ValueError("JSON file must contain a non-empty array of objects (records).")
        fieldnames = list(data[0].keys())
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow(record)
        return output.getvalue()

    else:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: .csv, .xlsx, .json")


def supported_extensions() -> list:
    return [".csv", ".xlsx", ".json"]