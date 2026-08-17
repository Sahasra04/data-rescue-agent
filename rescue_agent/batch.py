"""
Batch processing for the Data Rescue Agent.
Lets the agent clean every supported file in a folder in one autonomous run,
rather than one file at a time.
"""

import os
from .tools import fix_csv_file
from .file_converters import supported_extensions


def fix_all_files_in_folder(folder_path: str) -> str:
    """Cleans every supported data file (.csv, .xlsx, .json) in a given folder.

    Use this tool when the user wants to clean multiple files at once, or
    says something like "clean all the files in this folder" or "process
    this whole batch". It processes each file independently and reports
    a combined summary at the end.

    Args:
        folder_path: The path to the folder containing files to clean.

    Returns:
        A summary of results for every file processed, including successes and failures.
    """
    if not os.path.isdir(folder_path):
        return f"ERROR: Folder not found at {folder_path}"

    exts = set(supported_extensions())
    candidate_files = [
        f for f in os.listdir(folder_path)
        if os.path.splitext(f)[1].lower() in exts
        and not f.startswith("cleaned_")
    ]

    if not candidate_files:
        return f"No supported files (.csv, .xlsx, .json) found in {folder_path}"

    results = []
    success_count = 0
    fail_count = 0

    for file_name in candidate_files:
        file_path = os.path.join(folder_path, file_name)
        try:
            result = fix_csv_file(file_path)
            if result.startswith("ERROR"):
                fail_count += 1
                results.append(f"❌ {file_name}: {result}")
            else:
                success_count += 1
                first_line = result.split("\n")[0]
                results.append(f"✅ {file_name}: {first_line}")
        except Exception as e:
            fail_count += 1
            results.append(f"❌ {file_name}: unexpected error - {e}")

    summary = [
        f"Batch complete: {success_count} succeeded, {fail_count} failed, "
        f"{len(candidate_files)} total files processed.",
        ""
    ]
    summary.extend(results)
    return "\n".join(summary)