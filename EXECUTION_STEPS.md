# Execution Steps - PMO Automation Application

Complete guide to execute and run the PMO Status Report Automation system.

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Prepare Project Data](#prepare-project-data)
4. [Run Pipeline](#run-pipeline)
5. [View Results](#view-results)
6. [Next Steps](#next-steps)

---

## Prerequisites

### Required
- Python 3.9 or higher
- Anthropic API key
- GitHub repository cloned locally
- Windows/Mac/Linux with PowerShell or Bash

### Optional
- Git configured
- Text editor (VS Code, Notepad++, etc.)
- Web browser for viewing reports

---

## Initial Setup

### Step 1: Verify Python Installation

```powershell
# Check Python version
python --version

# Should show: Python 3.9.x or higher
```

If Python is not installed, download from: https://www.python.org/downloads/

### Step 2: Clone Repository

```powershell
# Clone from GitHub
git clone https://github.com/v4sikich/RQ-C_framework.git

# Navigate to production folder
cd RQ-C_framework\production

# Or if already cloned
cd "c:\Users\vansh.samaiya\Music\Nick\production"
```

### Step 3: Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate

# On Mac/Linux
# source venv/bin/activate
```

### Step 4: Install Dependencies

```powershell
# Install required packages
pip install -r config\requirements.txt

# Verify installation
pip list
```

### Step 5: Set Anthropic API Key

```powershell
# Set environment variable
$env:ANTHROPIC_API_KEY = "sk-ant-YOUR_API_KEY_HERE"

# On Mac/Linux
# export ANTHROPIC_API_KEY="sk-ant-YOUR_API_KEY_HERE"

# Verify it's set
$env:ANTHROPIC_API_KEY
```

Get API key from: https://console.anthropic.com/account/keys

---

## Prepare Project Data

### Option A: Use Example/Template Data

```powershell
# Copy template project
Copy-Item "projects\_template_project" -Destination "projects\my_first_project" -Recurse

# Navigate to project
cd projects\my_first_project\input

# Add your data files:
# 1. Copy meeting transcript to: transcript.txt
# 2. Edit metadata.json with project details
```

### Option B: Create New Project

```powershell
# Create project structure
New-Item -Path "projects\client_name" -ItemType Directory
New-Item -Path "projects\client_name\input" -ItemType Directory
New-Item -Path "projects\client_name\workflow_execution" -ItemType Directory
New-Item -Path "projects\client_name\output" -ItemType Directory

# Create README
New-Item -Path "projects\client_name\README.md" -ItemType File

# Create metadata.json template
@{
    project_name = "Project Name"
    practice = "PMO"
    client_name = "Client Name"
    go_live_date = "2026-09-15"
    timeline_status = "ON_TRACK"
    budget_total = "$450,000"
    budget_spent = "$187,000"
} | ConvertTo-Json | Out-File "projects\client_name\metadata.json"

# Add transcript.txt
# Copy your meeting transcript here
```

### Create Metadata.json

```json
{
  "project_name": "Your Project Name",
  "practice": "PMO",
  "client_name": "Client Name",
  "project_manager": "PM Name",
  "status_date": "2026-08-25",
  "go_live_date": "2026-09-15",
  "timeline_status": "ON_TRACK",
  "budget_total": "$450,000",
  "budget_spent": "$187,000",
  "budget_status": "ON_BUDGET",
  "notes": "Project description and notes"
}
```

### Create Meeting Transcript

Create `transcript.txt` with content like:

```
# Project Status Meeting - August 25, 2026
Date: August 25, 2026
Attendees: PM, Dev Lead, QA Lead, Client Rep

## Timeline Status
Project is on track for September 15 go-live.
Phase 1 completed early.
Phase 2 is 40% complete.

## Completed Work
- Requirements document signed off
- API design completed
- Security review passed

## Upcoming Milestones
- Technical design due Aug 22
- Development starts Aug 25
- UAT starts Sept 8

## Risks
- Main developer 50% available Sept 1
- Integration complexity increased
- Data quality issues in 20% of records

## Budget
$187K spent of $450K total (41.6%), on budget.
```

---

## Run Pipeline

### Method 1: Easy (Recommended)

```powershell
# From production root directory
cd "c:\Users\vansh.samaiya\Music\Nick\production"

# Run for your project
python run_project_pipeline.py --project-name my_first_project

# Wait 20-30 seconds for completion
```

### Method 2: Full Control

```powershell
# From production root directory
cd "c:\Users\vansh.samaiya\Music\Nick\production"

# Run with all options
python run_pipeline.py `
  --transcript projects\my_first_project\input\transcript.txt `
  --metadata projects\my_first_project\input\metadata.json `
  --project-name "Your Project Name" `
  --practice PMO `
  --project-dir projects\my_first_project
```

### Method 3: Step by Step

```powershell
# Step 1: Flatten data
python scripts\flatten.py `
  --transcript projects\my_first_project\input\transcript.txt `
  --metadata projects\my_first_project\input\metadata.json `
  --output projects\my_first_project\workflow_execution\01_flattened

# Step 2: Extract KPIs
python agents\intake_agent.py `
  --flattened projects\my_first_project\workflow_execution\01_flattened `
  --output projects\my_first_project\workflow_execution\02_intake_output.json

# Step 3: Prioritize
python agents\prioritization_agent.py `
  --input projects\my_first_project\workflow_execution\02_intake_output.json `
  --output projects\my_first_project\workflow_execution\03_prioritized_output.json

# Step 4: Generate Report
python agents\status_agent.py `
  --input projects\my_first_project\workflow_execution\03_prioritized_output.json `
  --output projects\my_first_project\workflow_execution\my_first_project_Status_Report.html
```

---

## View Results

### Check Execution Status

```powershell
# Check if pipeline completed successfully
$reportPath = "projects\my_first_project\workflow_execution\my_first_project_Status_Report.html"

if (Test-Path $reportPath) {
    Write-Host "✅ Report generated successfully!"
    Get-Item $reportPath | Select-Object LastWriteTime, Length
} else {
    Write-Host "❌ Report not found. Check pipeline output above."
}
```

### View Generated Files

```powershell
# List all generated files
Get-ChildItem "projects\my_first_project\workflow_execution\" -Recurse

# Show flattened markdown files
Get-ChildItem "projects\my_first_project\workflow_execution\01_flattened\"

# View JSON outputs
cat "projects\my_first_project\workflow_execution\02_intake_output.json" | python -m json.tool
```

### Open Report in Browser

```powershell
# Open the HTML report
start "projects\my_first_project\workflow_execution\my_first_project_Status_Report.html"

# On Mac
# open projects/my_first_project/workflow_execution/my_first_project_Status_Report.html

# On Linux
# xdg-open projects/my_first_project/workflow_execution/my_first_project_Status_Report.html
```

### View Report Contents

The generated HTML report includes:
- ✅ Executive Summary
- ✅ Health Status (Red/Yellow/Green)
- ✅ Timeline Status
- ✅ Key Accomplishments
- ✅ Upcoming Focus Items
- ✅ Risks & Mitigations
- ✅ Budget Status
- ✅ Critical Blockers
- ✅ Recommendations
- ✅ RAID Log

---

## Process Flow Explanation

### What Happens at Each Step

**STEP 1: Flattening**
```
Input: 
  - transcript.txt (meeting notes)
  - metadata.json (project info)

Processing:
  - Extracts key sections (timeline, risks, deliverables, budget)
  - Creates confidence scores
  - Organizes into markdown files

Output:
  - 01_flattened/
    ├── meeting_summary.md
    ├── risks_issues.md
    ├── deliverables.md
    ├── timeline.md
    ├── budget.md
    └── metadata.yaml
```

**STEP 2: Intake Agent (Claude Sonnet)**
```
Input: Flattened markdown files

Processing:
  - Reads all sections
  - Extracts structured data
  - Calculates health status
  - Adds confidence scores
  - Uses Claude AI for understanding

Output:
  - 02_intake_output.json
    {
      "project_name": "...",
      "timeline": {...},
      "deliverables": {...},
      "risks": [...],
      "budget": {...},
      "health_status": "green",
      "confidence_scores": {...}
    }
```

**STEP 3: Prioritization Agent (Claude Haiku)**
```
Input: Full KPIs JSON

Processing:
  - Filters what fits on slide
  - Ranks by importance
  - Selects top risks (2-3)
  - Top accomplishments (3-5)
  - Key upcoming items

Output:
  - 03_prioritized_output.json
    {
      "executive_summary": "...",
      "health_status_visual": "GREEN",
      "risks_to_highlight": [...],
      "key_accomplishments": [...],
      "upcoming_focus": [...],
      "recommendations": [...]
    }
```

**STEP 4: Status Report Agent (Claude Sonnet)**
```
Input: Prioritized JSON

Processing:
  - Formats as beautiful HTML
  - Applies Sikich branding
  - Adds R/Y/G indicators
  - Creates collapsible sections
  - Responsive design

Output:
  - [project]_Status_Report.html
    (Professional, branded, beautiful report)
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'anthropic'"

```powershell
# Solution: Install dependencies
pip install -r config\requirements.txt
```

### Issue: "API Key Not Found"

```powershell
# Check if key is set
echo $env:ANTHROPIC_API_KEY

# If empty, set it
$env:ANTHROPIC_API_KEY = "sk-ant-YOUR_KEY"

# Verify
echo $env:ANTHROPIC_API_KEY
```

### Issue: "Transcript not found"

```powershell
# Check file exists
Test-Path "projects\my_first_project\input\transcript.txt"

# If not, create it
# Copy your meeting notes to that location
```

### Issue: "JSON Parse Error"

```powershell
# Validate JSON
$json = Get-Content "projects\my_first_project\input\metadata.json" -Raw
$json | ConvertFrom-Json

# If error, fix JSON syntax in the file
# Check for missing commas, quotes, brackets
```

### Issue: "Pipeline runs but produces no output"

```powershell
# Check for errors in console output above
# Verify API key is valid
# Check internet connection
# Try again - sometimes rate limiting applies
```

---

## Best Practices

### ✅ DO:
- Use descriptive project names
- Keep transcripts clean and organized
- Fill in all metadata fields
- Review generated report before sharing
- Archive completed projects
- Back up important data
- Update project README after each run

### ❌ DON'T:
- Use special characters in project names
- Leave metadata fields empty
- Run multiple pipelines simultaneously
- Delete workflow_execution folders manually
- Share API keys
- Commit projects_data to git

---

## Advanced Usage

### Run Multiple Projects in Batch

```powershell
# Create list of projects
$projects = @("stephenson_rife", "galfand_berger", "my_project")

# Run each project
foreach ($project in $projects) {
    Write-Host "Running: $project"
    python run_project_pipeline.py --project-name $project
    Write-Host "Completed: $project`n"
}
```

### With Custom Excel Data

```powershell
# Run with Excel/Smartsheet data
python run_pipeline.py `
  --transcript projects\my_project\input\transcript.txt `
  --metadata projects\my_project\input\metadata.json `
  --excel projects\my_project\input\smartsheet_export.xlsx `
  --project-name "My Project"
```

### Generate Reports for Multiple Projects

```powershell
# Run multiple reports
1..5 | ForEach-Object {
    $projectName = "project_$_"
    python run_project_pipeline.py --project-name $projectName
}
```

---

## Performance Metrics

Typical execution times:
- **Step 1 (Flatten)**: 2-3 seconds
- **Step 2 (Intake)**: 8-10 seconds
- **Step 3 (Prioritization)**: 3-5 seconds
- **Step 4 (Status Report)**: 6-8 seconds
- **Total**: 20-30 seconds per report

Cost per report: ~$0.08 USD

---

## Next Steps

After generating a report:

1. **Review the HTML report** in your browser
2. **Check confidence scores** in the JSON files
3. **Archive the project** when complete
4. **Update project README** with results
5. **Commit changes to git** (if needed)
6. **Share report** with stakeholders
7. **Collect feedback** for improvements

---

## Getting Help

- **Setup issues?** See `GETTING_STARTED.md`
- **Architecture questions?** See `ARCHITECTURE.md`
- **Folder structure?** See `FOLDER_STRUCTURE.md`
- **Git/GitHub?** See `GIT_SETUP.md`
- **Project management?** See `projects/README.md`

---

## Summary

**Execution flow**:
1. ✅ Set up environment (one time)
2. ✅ Prepare project data
3. ✅ Run pipeline
4. ✅ View results
5. ✅ Archive project

**Quick command**:
```powershell
python run_project_pipeline.py --project-name my_project
```

**That's it!** Your professional status report is ready. 🚀

---

**Version**: 1.0  
**Last Updated**: August 25, 2026  
**Status**: Production Ready
