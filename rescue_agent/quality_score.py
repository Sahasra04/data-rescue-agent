"""
Data Quality Scoring for the Data Rescue Agent.

Calculates a 0-100 quality score for a CSV based on measurable, deterministic
issues -- NOT an AI judgment call. This keeps the score objective and
reproducible, and lets us show a concrete before/after number.
"""

import csv
import io
import re


def _read_rows(csv_text):
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _score_duplicates(data_rows):
    if not data_rows:
        return 25.0
    unique_rows = set(tuple(row) for row in data_rows)
    duplicate_count = len(data_rows) - len(unique_rows)
    ratio = duplicate_count / len(data_rows)
    return max(0.0, 25.0 * (1 - ratio))


def _score_missing_values(data_rows):
    if not data_rows:
        return 25.0
    total_cells = sum(len(row) for row in data_rows)
    if total_cells == 0:
        return 25.0
    missing_cells = sum(1 for row in data_rows for cell in row if not cell.strip())
    ratio = missing_cells / total_cells
    return max(0.0, 25.0 * (1 - ratio))


def _score_formatting_consistency(header, data_rows):
    if not data_rows or not header:
        return 25.0

    col_count = len(header)
    inconsistent_cols = 0

    for col_idx in range(col_count):
        values = [row[col_idx] for row in data_rows if col_idx < len(row) and row[col_idx].strip()]
        if len(values) < 2:
            continue

        has_leading_trailing_space = any(v != v.strip() for v in values)

        non_numeric = [v for v in values if not re.match(r'^-?\d+\.?\d*$', v.strip())]
        casing_inconsistent = False
        if len(non_numeric) >= 2:
            patterns = set()
            for v in non_numeric:
                if v.isupper():
                    patterns.add('upper')
                elif v.islower():
                    patterns.add('lower')
                elif v.istitle():
                    patterns.add('title')
                else:
                    patterns.add('mixed')
            casing_inconsistent = len(patterns) > 1

        if has_leading_trailing_space or casing_inconsistent:
            inconsistent_cols += 1

    ratio = inconsistent_cols / col_count if col_count else 0
    return max(0.0, 25.0 * (1 - ratio))


def _score_malformed_values(header, data_rows):
    if not data_rows or not header:
        return 25.0

    email_col_idx = None
    for i, col_name in enumerate(header):
        if 'email' in col_name.lower():
            email_col_idx = i
            break

    if email_col_idx is None:
        return 25.0

    email_values = [row[email_col_idx] for row in data_rows if email_col_idx < len(row) and row[email_col_idx].strip()]
    if not email_values:
        return 25.0

    email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    malformed = sum(1 for v in email_values if not email_pattern.match(v.strip()))
    ratio = malformed / len(email_values)
    return max(0.0, 25.0 * (1 - ratio))


def calculate_quality_score(csv_text):
    header, data_rows = _read_rows(csv_text)

    duplicates_score = _score_duplicates(data_rows)
    missing_score = _score_missing_values(data_rows)
    formatting_score = _score_formatting_consistency(header, data_rows)
    malformed_score = _score_malformed_values(header, data_rows)

    total = round(duplicates_score + missing_score + formatting_score + malformed_score)

    return {
        "total_score": total,
        "breakdown": {
            "no_duplicates": round(duplicates_score, 1),
            "no_missing_values": round(missing_score, 1),
            "formatting_consistency": round(formatting_score, 1),
            "no_malformed_values": round(malformed_score, 1),
        }
    }