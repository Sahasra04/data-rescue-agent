"""
Tools for the Data Rescue Agent.
Each function here becomes something the ADK agent can call on its own
to actually do work, not just talk. ADK reads the function name, its
type hints, and its docstring to understand what each tool does and
when to use it -- so keep docstrings clear, they matter.
"""

import os
import re
import json
import time
from history import log_run, get_run_history
from google import genai
from dotenv import load_dotenv
from quality_score import calculate_quality_score
from file_converters import convert_to_csv_text, supported_extensions

load_dotenv()

_client = None


def _get_client():
    global _client
    if _client is None:
        use_vertex = os.environ.get("GOOGLE_GENAI_USE_ENTERPRISE") == "1"
        if use_vertex:
            project = os.environ.get("GOOGLE_CLOUD_PROJECT")
            location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us")
            _client = genai.Client(vertexai=True, project=project, location=location)
        else:
            api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
            _client = genai.Client(api_key=api_key)
    return _client

def _extract_json(text):
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def _call_gemini_json(prompt, max_attempts=4):
    client = _get_client()
    for attempt in range(1, max_attempts + 1):
        try:
            response = client.models.generate_content(
                model="gemini-3.5-flash",
                contents=prompt
            )
            raw = _extract_json(response.text)
            return json.loads(raw)
        except Exception:
            if attempt < max_attempts:
                time.sleep(attempt * 2)
            else:
                raise


def detect_csv_issues(csv_file_path: str) -> str:
    """Analyzes a data file and identifies all data quality issues in it.

    Use this tool when the user wants to know what's wrong with a data file,
    before fixing it. Supports CSV, Excel (.xlsx), and JSON files. It reads
    the file from disk and returns a clear summary of every issue found:
    duplicates, inconsistent formatting, missing values, invalid data, etc.,
    plus an objective quality score.

    Args:
        csv_file_path: The path to the file to analyze (.csv, .xlsx, or .json).

    Returns:
        A summary string describing all data quality issues found, plus a quality score.
    """
    if not os.path.exists(csv_file_path):
        return f"ERROR: File not found at {csv_file_path}"

    try:
        csv_text = convert_to_csv_text(csv_file_path)
    except ValueError as e:
        return f"ERROR: {e}"

    score = calculate_quality_score(csv_text)

    prompt = f"""You are a data quality expert. Analyze this CSV and identify ALL data quality issues.
Look for: duplicate rows, inconsistent formatting (dates, casing, whitespace), missing values,
inconsistent categorical values, invalid data (e.g. malformed emails), and anything else that looks off.

CSV DATA:
{csv_text}

Respond with ONLY valid JSON in this structure, no other text:
{{
  "issues": [
    {{"location": "row/column", "problem": "what's wrong", "why_it_matters": "impact"}}
  ]
}}
"""
    result = _call_gemini_json(prompt)
    lines = [
        f"Quality Score: {score['total_score']}/100",
        f"  (duplicates: {score['breakdown']['no_duplicates']}/25, "
        f"missing values: {score['breakdown']['no_missing_values']}/25, "
        f"formatting: {score['breakdown']['formatting_consistency']}/25, "
        f"validity: {score['breakdown']['no_malformed_values']}/25)",
        "",
        f"Found {len(result['issues'])} issue(s):"
    ]
    for issue in result["issues"]:
        lines.append(f"- [{issue['location']}] {issue['problem']} ({issue['why_it_matters']})")
    return "\n".join(lines)


def fix_csv_file(csv_file_path: str) -> str:
    """Cleans a messy data file and saves a corrected version to disk.

    Use this tool when the user wants to actually fix/clean a data file,
    not just see what's wrong with it. Supports CSV, Excel (.xlsx), and
    JSON files -- the cleaned output is always saved as a .csv file
    regardless of the input format. This removes duplicates, standardizes
    dates/casing/whitespace, and never invents missing data. It writes the
    cleaned file to disk as 'cleaned_<original_filename>.csv' in the same
    folder, and reports a before/after quality score.

    Args:
        csv_file_path: The path to the messy file to clean (.csv, .xlsx, or .json).

    Returns:
        A summary of what was changed, the before/after quality score, and the path to the cleaned file.
    """
    if not os.path.exists(csv_file_path):
        return f"ERROR: File not found at {csv_file_path}"

    try:
        csv_text = convert_to_csv_text(csv_file_path)
    except ValueError as e:
        return f"ERROR: {e}"

    before_score = calculate_quality_score(csv_text)

    prompt = f"""You are a data cleaning expert. Clean this messy CSV data.

Rules:
- Remove exact duplicate rows (keep the first occurrence)
- Standardize all dates to YYYY-MM-DD format
- Standardize text casing: Names in Title Case, Emails lowercase, Status values lowercase
- Trim leading/trailing whitespace from all fields
- Standardize number formatting (e.g. "200" -> "200.00")
- For missing/blank values, leave them blank (do NOT guess) but flag them in your summary
- Do NOT invent or remove any real data beyond what these rules specify

MESSY CSV DATA:
{csv_text}

Respond with ONLY valid JSON in this structure, no other text:
{{
  "cleaned_csv": "the full cleaned CSV as a single string, including header row, with \\n between rows",
  "changes_summary": ["short description of change 1", "short description of change 2"]
}}
"""
    result = _call_gemini_json(prompt)
    after_score = calculate_quality_score(result["cleaned_csv"])

    original_name = os.path.splitext(os.path.basename(csv_file_path))[0]
    output_path = os.path.join(
        os.path.dirname(csv_file_path) or ".",
        f"cleaned_{original_name}.csv"
    )
    with open(output_path, "w") as f:
        f.write(result["cleaned_csv"])

    lines = [
        f"Quality Score: {before_score['total_score']}/100 -> {after_score['total_score']}/100",
        f"Cleaned file saved to: {output_path}",
        "",
        "Changes made:"
    ]
    for change in result["changes_summary"]:
        lines.append(f"- {change}")

    log_run(
        file_name=os.path.basename(csv_file_path),
        before_score=before_score['total_score'],
        after_score=after_score['total_score'],
        changes_summary=result['changes_summary'],
        issues_found=len(result['changes_summary'])
    )

    return "\n".join(lines)