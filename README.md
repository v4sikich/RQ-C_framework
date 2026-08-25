# PMO Status Report Automation - Production Ready

**Status**: Production Ready  
**Version**: 1.0.0  
**Last Updated**: August 2026

## Overview

This is an automated PMO status report generation system that transforms meeting transcripts and project metadata into beautiful, branded HTML reports using Claude AI agents.

**Key Features:**
- ✅ Automated extraction of KPIs from unstructured data
- ✅ Professional Sikich-branded HTML reports
- ✅ Three-agent pipeline (Intake → Prioritization → Status)
- ✅ Confidence scoring for quality assurance
- ✅ Mobile-responsive, print-friendly reports
- ✅ Ready for SharePoint/Power Automate integration

---

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="sk-ant-..."  # Linux/macOS
# or
$env:ANTHROPIC_API_KEY = "sk-ant-..."   # Windows PowerShell
```

### 2. Generate Your First Report

```bash
# Run with sample data (recommended)
python run_pipeline.py

# Run with your own data
python run_pipeline.py \
  --transcript path/to/transcript.txt \
  --metadata path/to/metadata.json \
  --project-name "Your Project" \
  --practice PMO
```

### 3. View the Report

Open the generated HTML file in any web browser. Reports are self-contained with no external dependencies.

---

## Project Structure

```
production/
├── README.md                           (this file)
├── GETTING_STARTED.md                  (detailed setup guide)
├── ARCHITECTURE.md                     (system design & scalability)
├── DIAGRAMS.md                         (visual architecture)
│
├── run_pipeline.py                     (main orchestration script)
├── requirements.txt                    (Python dependencies)
│
├── agents/                             (Claude agent modules)
│   ├── __init__.py
│   ├── intake_agent.py                 (Extract KPIs from markdown)
│   ├── prioritization_agent.py         (Rank & filter for slide)
│   └── status_agent.py                 (Generate HTML report)
│
├── scripts/                            (Data processing utilities)
│   └── flatten.py                      (Convert transcripts to markdown)
│
├── sample_data/                        (Test data)
│   ├── sample_1_transcript.txt
│   └── sample_1_metadata.json
│
└── output/                             (Generated reports - created at runtime)
    └── [project_name]_[timestamp]/
        ├── 01_flattened/               (markdown chunks)
        ├── 02_intake_output.json       (extracted KPIs)
        ├── 03_prioritized_output.json  (ranked KPIs)
        └── [project]_Status_Report.html (final report)
```

---

## Pipeline Overview

The system processes data through four steps:

```
Transcript + Metadata
    ↓ (Step 1: Flatten)
Organized Markdown
    ↓ (Step 2: Intake Agent - Claude Sonnet)
Structured JSON with KPIs
    ↓ (Step 3: Prioritization Agent - Claude Haiku)
Prioritized JSON (what fits on slide)
    ↓ (Step 4: Status Agent - Claude Sonnet)
Beautiful HTML Report
```

### Step-by-Step

**Step 1 - Flattening** (`scripts/flatten.py`)
- Reads: Meeting transcripts, metadata JSON, optional Excel files
- Extracts: Summary, risks, deliverables, timeline, budget
- Outputs: Markdown chunks with confidence scores
- Cost: Free (local processing)

**Step 2 - Intake Agent** (`agents/intake_agent.py`)
- Reads: Flattened markdown files
- Extracts: All KPIs in structured JSON format
- Includes: Health status, confidence scores, RAID log
- Model: Claude Sonnet 5 (high quality)
- Cost: ~$0.03 per report

**Step 3 - Prioritization Agent** (`agents/prioritization_agent.py`)
- Reads: Full KPIs JSON
- Filters: To what fits on a slide (3-5 risks max, etc.)
- Ranks: By importance for stakeholders
- Model: Claude Haiku (fast, cheap)
- Cost: ~$0.001 per report

**Step 4 - Status Agent** (`agents/status_agent.py`)
- Reads: Prioritized KPIs
- Generates: Professional HTML report
- Styling: Sikich branding, responsive design
- Model: Claude Sonnet 5
- Cost: ~$0.04 per report

**Total Cost**: ~$0.08 per report

---

## Usage Examples

### Basic Usage
```bash
python run_pipeline.py
```

### With Custom Project
```bash
python run_pipeline.py \
  --transcript meeting_notes.txt \
  --metadata project_info.json \
  --project-name "Acme Corp Implementation" \
  --practice PMO
```

### With Budget Data
```bash
python run_pipeline.py \
  --transcript transcript.txt \
  --metadata metadata.json \
  --excel smartsheet_export.xlsx \
  --project-name "Project Name"
```

### Individual Steps
```bash
# Step 1: Flatten only
python scripts/flatten.py \
  --transcript transcript.txt \
  --metadata metadata.json \
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

## Input Requirements

### Meeting Transcript
- Format: Plain text, VTT, or TXT
- Content: Meeting notes, discussion points, decisions
- Should mention: Timeline, deliverables, risks, budget status

Example snippet:
```
Agenda: Project status update
- Kickoff phase completed on time
- Risk: Developer unavailable next week
- Next: UAT scheduled for August 15
- Budget: 45% spent, on track
```

### Project Metadata (JSON)
```json
{
  "project_name": "Your Project",
  "practice": "PMO",
  "go_live_date": "2026-09-15",
  "budget_total": "$500,000",
  "budget_spent": "$200,000",
  "timeline_status": "ON_TRACK",
  "deliverables": ["item 1", "item 2"]
}
```

### Optional: Excel File
- Smartsheet exports
- Budget tracking spreadsheets
- Timeline/Gantt data
- Custom project tracking sheets

---

## Output

### HTML Report Features
- ✅ Professional Sikich branding
- ✅ Red/Yellow/Green status indicators
- ✅ Collapsible sections for detailed info
- ✅ Mobile responsive
- ✅ Print-friendly (PDF-ready)
- ✅ Self-contained (no external files)

### Report Sections
1. Executive Summary
2. Health Status
3. Timeline
4. Key Accomplishments
5. Upcoming Focus Items
6. Risks & Mitigations
7. Critical Blockers
8. Recommendations
9. Budget Status (if applicable)
10. RAID Log

---

## Customization

### Change Colors/Branding
Edit `agents/status_agent.py` - look for color hex codes:
- `#003366` → Navy (primary)
- `#0099cc` → Light Blue (accent)
- Update to match your brand

### Change KPI Extraction
Edit `agents/intake_agent.py` - modify `INTAKE_OUTPUT_SCHEMA` to capture different metrics

### Adjust Prioritization Rules
Edit `agents/prioritization_agent.py` - customize `build_prioritization_prompt()` to match your practice-specific priorities

### Add New Data Sources
Edit `scripts/flatten.py` - add new `extract_*` methods for additional data types

---

## Deployment Options

### Option 1: Local Command Line
Run `python run_pipeline.py` locally whenever you need a report.

### Option 2: Power Automate Integration
Set up Power Automate flow to trigger the pipeline when files are uploaded to SharePoint.

### Option 3: Scheduled Reports
Use cron (Linux/Mac) or Task Scheduler (Windows) to run reports on a schedule.

### Option 4: Web Service
Deploy as a Flask/FastAPI service with an API endpoint for report generation.

---

## Troubleshooting

### "API Key Not Found"
```bash
# Check if key is set
echo $ANTHROPIC_API_KEY  # Linux/Mac
echo $env:ANTHROPIC_API_KEY  # PowerShell

# Set it
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Module Not Found"
```bash
pip install -r requirements.txt
```

### "JSON Parse Error"
- Ensure metadata JSON is valid
- Check that transcript file is readable
- Verify API key is correct

### "Report Too Large"
Reduce verbosity in status_agent.py prompt or reduce input data size.

---

## Performance

| Metric | Value |
|--------|-------|
| Processing Time | 20-30 seconds |
| Total Tokens | 5,500-8,800 |
| Report Size | 50-100 KB |
| Cost per Report | ~$0.08 |
| Accuracy Target | 80-90% |

---

## Integration with Other Systems

### SharePoint
1. Create input folder: `/PMO Reports/Input`
2. Create output folder: `/PMO Reports/Output`
3. Save reports to output folder

### Power Automate
1. Trigger on file creation in input folder
2. Run Python script via Azure Container or local machine
3. Save HTML to output folder
4. Send Teams notification to PM

### Email
Copy HTML file and send as attachment. Report is self-contained and doesn't require external resources.

---

## Best Practices

1. **Verify Confidence Scores**: Items under 80% confidence should be reviewed by a human
2. **Review Sample Reports**: Before deploying, review sample HTML output
3. **Test with Real Data**: Run with actual project transcripts to validate accuracy
4. **Monitor Costs**: Track API usage via Anthropic dashboard
5. **Version Control**: Keep templates and customizations in git

---

## Support & Documentation

- **Setup Help**: See `GETTING_STARTED.md`
- **Architecture Details**: See `ARCHITECTURE.md`
- **Visual Diagrams**: See `DIAGRAMS.md`
- **API Issues**: Check `agents/*.py` docstrings
- **Data Processing**: Check `scripts/flatten.py` docstrings

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Aug 2026 | Initial production release |

---

## License & Credits

Built with Claude AI (Anthropic)  
Sikich Branding Applied  
Enterprise-Ready

---

**Ready to automate your PMO reports? Start with:**
```bash
python run_pipeline.py
```

For detailed setup instructions, see [GETTING_STARTED.md](GETTING_STARTED.md)
