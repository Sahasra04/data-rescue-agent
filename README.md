# 🧹 Data Rescue Agent

An autonomous AI agent that detects and fixes data quality issues in messy CSV, Excel, and JSON files — built for the **All Things Agentic Hackathon** using Gemini 3.5, Google's Agent Development Kit (ADK), and Cloud Run.

**Category:** Taskmaster — Bring Your Own Friction (BYOF)

## The Problem

Cleaning messy spreadsheets — duplicate rows, inconsistent date formats, mismatched casing, missing values — is tedious manual work most people put off. The Data Rescue Agent does this autonomously: give it a file (or a whole folder), and it detects every issue, fixes it, and reports exactly what changed and why.

## Live Demo

- **Agent (chat interface):** https://data-rescue-agent-249981837129.us-central1.run.app/dev-ui/?app=rescue_agent
- **Web App (polished UI):** https://data-rescue-web-249981837129.us-central1.run.app

## Features

- **Autonomous detection & cleaning** — the agent decides on its own which tool to call based on what you ask (detect vs. fix vs. batch vs. history)
- **Objective quality scoring** — a deterministic 0-100 score (not just an AI's opinion) based on duplicates, missing values, formatting consistency, and data validity, reported before and after every clean
- **Persistent memory (Firestore)** — the agent remembers every file it has ever cleaned, across sessions, and can answer questions about its own history
- **Multi-format support** — handles `.csv`, `.xlsx` (Excel), and `.json` files, always outputting a clean `.csv`
- **Batch processing** — clean an entire folder of files in a single autonomous run
- **Two interfaces** — a full ADK chat agent for judges/developers, and a polished standalone web app for end users
- **Never invents data** — missing values are always left blank rather than guessed, and this is explicitly enforced in the agent's instructions

## Tech Stack

| Component | Technology |
|---|---|
| LLM | Gemini 3.5 (via Vertex AI) |
| Agent Framework | Google ADK (Agent Development Kit) |
| Deployment | Google Cloud Run (2 services) |
| Persistent State | Google Cloud Firestore |
| Web Frontend | Flask |
| File Parsing | openpyxl (Excel), built-in csv/json (Python) |

## Architecture

```
                          ┌─────────────────────┐
                          │   Gemini 3.5         │
                          │   (via Vertex AI)     │
                          └──────────▲───────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
   ┌──────────▼──────────┐  ┌────────▼────────┐   ┌─────────▼─────────┐
   │  ADK Agent           │  │  Shared Logic    │   │  Firestore         │
   │  (Cloud Run)         │◄─┤  - tools.py      │──►│  (run history)     │
   │  Chat interface       │  │  - quality_score │   │                     │
   └──────────────────────┘  │  - file_converters│  └─────────────────────┘
                              │  - batch.py       │
   ┌──────────────────────┐  └────────▲──────────┘
   │  Web Frontend         │           │
   │  (Cloud Run / Flask)  │───────────┘
   │  Upload UI             │
   └──────────────────────┘
```

Both Cloud Run services share the same core detection/cleaning/scoring logic, so behavior is consistent whether you use the chat agent or the web app.

## Agent Tools

The agent has four tools it autonomously chooses between based on user intent:

1. **`detect_csv_issues`** — analyzes a file and reports quality issues + score, without changing anything
2. **`fix_csv_file`** — cleans a file and saves the corrected version, reporting before/after score
3. **`fix_all_files_in_folder`** — batch-processes every supported file in a directory
4. **`get_run_history`** — retrieves past cleaning runs from Firestore

## Setup Instructions

### Prerequisites
- Python 3.10+
- A Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated

### 1. Clone the repo
```bash
git clone https://github.com/Sahasra04/data-rescue-agent.git
cd data-rescue-agent
```

### 2. Set up the environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r rescue_agent/requirements.txt
pip install google-adk google-genai python-dotenv
```

### 3. Configure credentials
Create a `.env` file inside `rescue_agent/` with:
```
GOOGLE_API_KEY=your-gemini-api-key
```
Get a free key at https://aistudio.google.com/apikey

### 4. Enable required Google Cloud APIs
```bash
gcloud services enable aiplatform.googleapis.com firestore.googleapis.com run.googleapis.com
gcloud firestore databases create --location=us-central1
```

### 5. Run locally
```bash
adk run rescue_agent
```
Then try: `Can you fix the file at rescue_agent/messy_data.csv?`

### 6. Deploy to Cloud Run
```bash
chmod +x deploy.sh
./deploy.sh
```

## Project Structure

```
data-rescue-agent/
├── rescue_agent/          # ADK agent (deployed to Cloud Run)
│   ├── agent.py           # Agent definition & instructions
│   ├── tools.py           # Detect/fix tool implementations
│   ├── quality_score.py   # Deterministic scoring logic
│   ├── file_converters.py # CSV/Excel/JSON handling
│   ├── batch.py           # Multi-file batch processing
│   └── history.py         # Firestore run-history logging
├── web_frontend/          # Flask web app (deployed separately)
│   ├── app.py
│   └── templates/index.html
└── deploy.sh               # One-command deploy script
```

## What We Learned

Deploying Gemini 3.5 via Vertex AI on Cloud Run required discovering an undocumented-feeling requirement: newer Gemini models need `GOOGLE_CLOUD_LOCATION=us` (not a regional value like `us-central1`) for multi-region routing. We also learned that `adk deploy cloud_run` bakes the `--region` flag into both the Cloud Run region *and* the Vertex AI location environment variable, requiring a manual override via `gcloud run services update` to set them independently.