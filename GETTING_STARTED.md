# Getting Started - PMO Status Report Automation

Welcome! This guide will get you up and running in 5-10 minutes.

---

## Prerequisites

- Python 3.9 or higher
- Anthropic API key (get one at https://console.anthropic.com)
- ~5 minutes for your first run

---

## Step 1: Install Dependencies (2 minutes)

```bash
# Navigate to the project directory
cd production

# Install Python packages
pip install -r requirements.txt
```

**Windows users**: You may need to run this in PowerShell as Administrator.

---

## Step 2: Set Your API Key (1 minute)

### Option A: Set Temporarily (for this session only)

**macOS/Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

**Windows Command Prompt:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-...
```

### Option B: Set Permanently (recommended for regular use)

**macOS/Linux:** Add to `~/.bashrc` or `~/.zshrc`:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Windows:** Use Environment Variables GUI:
1. Right-click "This PC" → Properties
2. Advanced system settings → Environment Variables
3. New → ANTHROPIC_API_KEY = `sk-ant-...`
4. Restart PowerShell/Command Prompt

---

## Step 3: Verify Setup (1 minute)

```bash
# Check Python installation
python --version

# Check API key
echo $ANTHROPIC_API_KEY  # Linux/Mac
echo %ANTHROPIC_API_KEY%  # Windows Command Prompt
$env:ANTHROPIC_API_KEY   # Windows PowerShell

# Should output: sk-ant-...
```

If you see your API key, you're ready to go!

---

## Step 4: Generate Your First Report (5 minutes)

### Option A: Use Sample Data (Easiest)

Run the complete pipeline with built-in sample data:

```bash
python run_pipeline.py
```

**What this does:**
1. ✅ Reads sample meeting transcript
2. ✅ Reads sample project metadata  
3. ✅ Flattens data into markdown chunks
4. ✅ Extracts KPIs using Claude Sonnet
5. ✅ Prioritizes items using Claude Haiku
6. ✅ Generates beautiful HTML report
7. ✅ Saves everything to `output/` folder

**Result**: A professional HTML report ready to view in your browser

### Option B: Use Your Own Data

Create two files:

**File 1: Transcript** (`meeting_notes.txt`)
```
Agenda: Project Status Update

Project is on track for go-live on September 15th.
We completed requirements gathering 2 weeks early.
Key risk: main developer unavailable for 3 weeks in Sept.
Mitigation: contractor backup identified.

Next steps:
- UAT starts Sept 8
- Go-live Sept 15
```

**File 2: Metadata** (`metadata.json`)
```json
{
  "project_name": "My Project",
  "practice": "PMO",
  "go_live_date": "2026-09-15",
  "timeline_status": "ON_TRACK",
  "budget_total": "$500,000",
  "budget_spent": "$200,000"
}
```

Then run:
```bash
python run_pipeline.py \
  --transcript meeting_notes.txt \
  --metadata metadata.json \
  --project-name "My Project"
```

---

## Step 5: View Your Report

The HTML file is generated and ready to open immediately:

```bash
# macOS
open output/My_Project_20260805_120000/My_Project_Status_Report.html

# Windows (PowerShell)
start output/My_Project_20260805_120000/My_Project_Status_Report.html

# Linux
xdg-open output/My_Project_20260805_120000/My_Project_Status_Report.html
```

Or copy the path and paste into your browser address bar.

**The report includes:**
- ✅ Executive Summary
- ✅ Health Status (Red/Yellow/Green)
- ✅ Timeline Status
- ✅ Completed Deliverables
- ✅ Upcoming Focus Items
- ✅ Risks & Mitigations
- ✅ Budget Status
- ✅ Recommendations

---

## Understanding the Output Structure

```
output/
├── Stephenson_Rife_Implementation_20260805_120000/    (timestamp-based folder)
│   ├── 01_flattened/                                  (flattened markdown chunks)
│   │   ├── meeting_summary.md
│   │   ├── risks_issues.md
│   │   ├── deliverables.md
│   │   ├── timeline.md
│   │   ├── budget.md
│   │   └── metadata.yaml
│   │
│   ├── 02_intake_output.json                          (extracted KPIs)
│   ├── 03_prioritized_output.json                     (ranked/filtered KPIs)
│   └── Stephenson_Rife_Status_Report.html             (FINAL REPORT)
```

---

## Customization Quick Starts

### Change Report Colors/Branding

Edit `agents/status_agent.py` and update:
- `#003366` → Your primary color (navy)
- `#0099cc` → Your accent color (light blue)
- Logo reference in the HTML template section

### Change What Gets Extracted

Edit `agents/intake_agent.py` - modify `INTAKE_OUTPUT_SCHEMA` dict to capture different metrics

### Change What Gets Highlighted

Edit `agents/prioritization_agent.py` - modify `build_prioritization_prompt()` to emphasize different priorities

### Add Excel File Support

Uncomment pandas/openpyxl in `requirements.txt`:
```bash
pip install pandas openpyxl
```

Then use:
```bash
python run_pipeline.py \
  --transcript transcript.txt \
  --metadata metadata.json \
  --excel smartsheet_export.xlsx
```

---

## Running Individual Steps

You can run each step independently:

```bash
# Step 1: Flatten only
python scripts/flatten.py \
  --transcript sample_data/sample_1_transcript.txt \
  --metadata sample_data/sample_1_metadata.json \
  --output output/flattened/

# Step 2: Intake only
python agents/intake_agent.py \
  --flattened output/flattened/ \
  --output output/intake.json

# Step 3: Prioritization only
python agents/prioritization_agent.py \
  --input output/intake.json \
  --output output/prioritized.json

# Step 4: Status report only
python agents/status_agent.py \
  --input output/prioritized.json \
  --output output/report.html
```

---

## Troubleshooting

### "Command not found: python"
- Make sure Python is installed and added to PATH
- Try `python3` instead of `python`
- Or check: `which python` (Mac/Linux) or `where python` (Windows)

### "No module named 'anthropic'"
```bash
pip install -r requirements.txt
```

### "API Key Not Found"
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY

# If not set, run:
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "JSON Parse Error"
- Check that metadata JSON is valid (use jsonlint.com)
- Check that transcript file is readable and not empty
- Check that API key is correct

### "HTML Report is too large" (>1MB)
- Reduce verbosity in `agents/status_agent.py` prompt
- Reduce input data size

### "Connection timeout"
- Check internet connection
- Verify API key has remaining balance
- Try again (rate limiting may apply)

---

## Next Steps

1. **Run with sample data** → See what a report looks like
2. **Prepare your data** → Create transcript + metadata files
3. **Generate your first report** → See it in action
4. **Share with team** → Email the HTML file
5. **Customize as needed** → Adjust colors, prompts, fields
6. **Deploy** → Use with Power Automate, cron, or web service

---

## Cost Estimate

Each report typically costs:
- **Intake Agent** (Sonnet): $0.03
- **Prioritization Agent** (Haiku): $0.001
- **Status Agent** (Sonnet): $0.04
- **Total per report**: ~$0.08

(Prices current August 2026. Check Anthropic pricing page for latest rates)

---

## What's Happening Under the Hood?

1. **Flattening** (Python) - Converts messy input into organized chunks
2. **Intake Agent** (Claude Sonnet) - Extracts structured data from chunks
3. **Prioritization** (Claude Haiku) - Filters to what fits on a slide
4. **Status Report** (Claude Sonnet) - Formats into beautiful HTML
5. **Pipeline** (Python) - Orchestrates all steps, saves outputs

Total processing time: **20-30 seconds**

---

## Getting Help

- **Setup issues?** → See troubleshooting above
- **How to customize?** → See ARCHITECTURE.md
- **Want to understand the design?** → See ARCHITECTURE.md
- **Want to see diagrams?** → See DIAGRAMS.md
- **Need detailed setup?** → See README.md

---

## Quick Reference

```bash
# First time
pip install -r requirements.txt
export ANTHROPIC_API_KEY="sk-ant-..."

# Generate report
python run_pipeline.py

# Generate with your data
python run_pipeline.py --transcript YOUR_FILE.txt --metadata YOUR_META.json

# View report
open output/*/Your_Project_Status_Report.html
```

**You're ready! Run `python run_pipeline.py` and generate your first report.** 🚀
