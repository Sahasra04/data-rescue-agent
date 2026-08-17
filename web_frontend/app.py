"""
Web frontend for the Data Rescue Agent.
A simple upload-and-clean interface, reusing the same core logic
(tools.py, quality_score.py, file_converters.py) as the ADK agent.
"""

import os
import tempfile
from flask import Flask, request, render_template, send_file
from tools import fix_csv_file, detect_csv_issues

app = Flask(__name__)
UPLOAD_FOLDER = tempfile.gettempdir()


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("data_file")
    if not file or file.filename == "":
        return render_template("index.html", error="Please choose a file first.")

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        action = request.form.get("action")
        if action == "detect":
            result = detect_csv_issues(filepath)
            return render_template("index.html", result=result, action="Analysis")
        else:
            result = fix_csv_file(filepath)
            cleaned_path = None
            for line in result.split("\n"):
                if line.startswith("Cleaned file saved to:"):
                    cleaned_path = line.split(":", 1)[1].strip()
            return render_template(
                "index.html", result=result, action="Cleaning",
                download_ready=bool(cleaned_path), download_name=os.path.basename(cleaned_path) if cleaned_path else None
            )
    except Exception as e:
        return render_template("index.html", error=f"Something went wrong: {e}")


@app.route("/download/<filename>")
def download(filename):
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return "File not found", 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)