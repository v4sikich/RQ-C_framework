# PMO Status Report Automation - Architecture & Design

## System Architecture Overview

This document describes the technical architecture, design decisions, and scalability framework for the PMO Status Report Automation system.

---

## 1. Core Design Principles

### 1.1 Separation of Concerns
- **Data Layer**: Flattening script processes raw input
- **Logic Layer**: Three specialized agents (Intake, Prioritization, Status)
- **Presentation Layer**: HTML formatting with Sikich branding

### 1.2 Cost Optimization
- Flattening is local (free) - only 3-4 KB per section
- Intake Agent uses Sonnet (balanced cost/quality)
- Prioritization uses Haiku (lightweight, fast)
- Status Agent uses Sonnet (high-quality HTML)

### 1.3 Modularity
- Each agent is independently testable
- Agents can be swapped for alternative models
- Steps can be run individually without running full pipeline

### 1.4 Reliability
- Confidence scoring on all extractions
- Fallback to null values for uncertain data
- Error handling at each step
- Metadata tracking for auditing

---

## 2. Pipeline Architecture

### 2.1 Data Flow

```
INPUT
  ├── Meeting Transcript (VTT, TXT)
  └── Project Metadata (JSON)
  └── Optional: Excel data

PROCESSING
  ├─ Step 1: Flatten (Local Python)
  │   └── Output: Markdown chunks with confidence
  │
  ├─ Step 2: Intake Agent (Claude Sonnet)
  │   ├── Input: Markdown chunks
  │   └── Output: Structured KPIs (JSON)
  │
  ├─ Step 3: Prioritization Agent (Claude Haiku)
  │   ├── Input: Full KPIs
  │   └── Output: Filtered/ranked KPIs
  │
  └─ Step 4: Status Agent (Claude Sonnet)
      ├── Input: Prioritized KPIs
      └── Output: HTML report

OUTPUT
  └── Beautiful HTML Report (self-contained, no dependencies)
```

### 2.2 Agent Chain Architecture

```python
class PipelineOrchestrator:
    def run(transcript, metadata, project_name):
        # Step 1
        flattened = FlatteningEngine.flatten(transcript, metadata)
        
        # Step 2
        kpis = IntakeAgent.extract_kpis(flattened)
        
        # Step 3
        prioritized = PrioritizationAgent.prioritize(kpis)
        
        # Step 4
        html = StatusReportAgent.generate(prioritized)
        
        return html
```

---

## 3. Component Details

### 3.1 Flattening Engine (`scripts/flatten.py`)

**Purpose**: Convert messy input into structured markdown chunks

**Input Handling**:
- Reads meeting transcripts (VTT, TXT, plain text)
- Parses metadata JSON
- Extracts Excel data (Smartsheet, budget tracking, etc.)
- Uses regex for date detection
- Handles PDFs via OCR (future enhancement)

**Extraction Methods**:
```python
extract_meeting_summary()      # Find agenda/key topics
extract_risks_and_issues()     # Find risk keywords
extract_deliverables()         # Find completed/upcoming work
extract_timeline()             # Find dates and status keywords
extract_budget()               # Find spending information
extract_excel_data()           # Parse spreadsheets
```

**Confidence Scoring**:
- 95%+ : Explicit markers found (e.g., "Agenda:" label)
- 80-95%: Strong keyword matches with good context
- 50-80%: Weak signals, may need human review
- <50%: Uncertain, treated as "not found"

**Output**:
```
output/[project]/01_flattened/
├── meeting_summary.md       (extracted with confidence)
├── risks_issues.md
├── deliverables.md
├── timeline.md
├── budget.md
└── metadata.yaml           (tracking & confidence scores)
```

### 3.2 Intake Agent (`agents/intake_agent.py`)

**Purpose**: Extract structured KPIs from markdown

**Model**: Claude Sonnet 5 (high quality, ~$0.03 cost)

**Output Schema**:
```json
{
  "project_name": "string",
  "practice": "string",
  "status_date": "YYYY-MM-DD",
  "timeline": {
    "original_go_live": "date",
    "current_status": "on_track | at_risk | delayed | ahead",
    "days_variance": integer,
    "key_dates": [...]
  },
  "deliverables": {
    "completed": [...],
    "upcoming": [...],
    "value_delivered": "narrative"
  },
  "risks": [
    {
      "title": "string",
      "description": "string",
      "severity": "critical | high | medium | low",
      "mitigation": "string"
    }
  ],
  "budget": {
    "total": "string",
    "spent": "string",
    "percentage_used": float,
    "status": "on_budget | over_budget | under_budget"
  },
  "open_items": [...],
  "raid_log": {
    "risks": [...],
    "assumptions": [...],
    "issues": [...],
    "decisions": [...]
  },
  "health_status": "red | yellow | green",
  "key_takeaways": [...],
  "confidence_scores": {
    "timeline": float,
    "deliverables": float,
    "risks": float,
    "budget": float
  }
}
```

**Prompt Strategy**:
- Provides complete schema in prompt
- Conservative extraction (flags uncertainty)
- Uses null for missing/unclear data
- Calculates health status from risks and timeline

### 3.3 Prioritization Agent (`agents/prioritization_agent.py`)

**Purpose**: Filter and rank KPIs for slide presentation

**Model**: Claude Haiku (lightweight, ~$0.001 cost)

**Constraints**:
- Max 2-3 critical risks
- Max 3-5 upcoming milestones
- Max 2-3 completed items
- 1 executive summary
- 1 health status

**Ranking Rules** (configurable per practice):
```python
PMO Priority:
  Timeline > Risks > Budget > Accomplishments
  
QMS Priority:
  Quality Metrics > Process Compliance > Timeline > Risks
  
ITQC Priority:
  System Stability > Change Management > Timeline > Risks
```

**Output**:
```json
{
  "executive_summary": "string",
  "health_status_visual": "RED | YELLOW | GREEN",
  "risks_to_highlight": [...],
  "key_accomplishments": [...],
  "upcoming_focus": [...],
  "critical_blockers": [...],
  "flagged_items": [...],
  "recommendations": [...],
  "confidence_level": "high | medium | low"
}
```

### 3.4 Status Report Agent (`agents/status_agent.py`)

**Purpose**: Generate professional HTML report

**Model**: Claude Sonnet 5 (high quality, ~$0.04 cost)

**Design System** (Sikich Branding):
```css
Primary Colors:
  Navy: #003366
  Light Blue: #0099cc
  White: #ffffff
  Light Gray: #f5f5f5

Typography:
  Headings: sans-serif, bold
  Body: sans-serif, 14-16px
  
Spacing:
  Padding: 20px, 40px
  Margins: 10px, 20px
  Section gaps: 30px

Status Indicators:
  Red: #d32f2f (critical)
  Yellow: #fbc02d (warning)
  Green: #388e3c (healthy)
```

**HTML Features**:
- Self-contained (all CSS inline)
- Mobile responsive (viewport meta tag)
- Print-friendly (no external assets)
- Collapsible sections (CSS-only, no JavaScript)
- SVG status badges (no images)

**Report Structure**:
```html
<html>
<head>
  <meta viewport>
  <style>/* all CSS inline */</style>
</head>
<body>
  <header>Logo + Project Name + Date</header>
  <section>Executive Summary</section>
  <section>Health Status Badge</section>
  <section collapsible>Timeline</section>
  <section collapsible>Accomplishments</section>
  <section collapsible>Upcoming Focus</section>
  <section collapsible>Risks</section>
  <section collapsible>Blockers</section>
  <section>Recommendations</section>
  <footer>Sikich branding</footer>
</body>
</html>
```

---

## 4. Technology Stack

| Component | Technology | Why? |
|-----------|-----------|------|
| Data Processing | Python 3.9+ | Flexible, widely available |
| LLM Client | Anthropic Python SDK | Direct API integration |
| Model - Intake | Claude Sonnet 5 | Balanced cost/quality |
| Model - Prioritization | Claude Haiku | Fast, cheap ranking |
| Model - Status | Claude Sonnet 5 | High-quality HTML generation |
| Data Format | JSON | Widely supported, machine-readable |
| Report Format | HTML/CSS | Self-contained, no dependencies |
| Optional: Spreadsheets | Pandas | Read Smartsheet exports |
| Configuration | Environment variables | Secure API key handling |

---

## 5. Scalability Framework

### 5.1 Adapting to Other Practices

**Current**: PMO (Project Management Office)

**Can Adapt To**:
1. **QMS** (Quality Management Systems)
2. **ITQC** (IT Quality Control)
3. **InsurTech** (Insurance Tech Projects)
4. **Salesforce** (CRM Implementations)
5. **LegalTech** (Legal Services Implementations)

### 5.2 What Stays the Same (70-95% reuse)

- Flattening script structure
- Intake Agent schema (mostly)
- Prioritization logic (just different weights)
- HTML generation framework
- Error handling, logging, file I/O

### 5.3 What Changes Per Practice

| Aspect | Change | Example |
|--------|--------|---------|
| Data Extraction | Keywords, fields | QMS looks for "audit", "compliance" |
| Prioritization Rules | What matters | QMS: Quality > Timeline |
| Health Status Logic | Success criteria | QMS: "Red if audit issues found" |
| Report Sections | Content emphasis | QMS adds "Compliance Status" section |
| HTML Styling | Optional branding | Different logo, colors per practice |

### 5.4 Effort to Add New Practice

| Practice | Effort | Reason |
|----------|--------|--------|
| QMS | 1-2 days | High data similarity to PMO |
| ITQC | 2-3 days | Moderate divergence, custom metrics |
| InsurTech | 2-3 days | Similar to PMO + insurance vocab |
| Salesforce | 3-4 days | 7 different project types |
| LegalTech | 4-6 days | Highly specialized terminology |

### 5.5 Customization Checklist

When adding a new practice:

```markdown
- [ ] Update `extract_*` methods in flatten.py with practice-specific keywords
- [ ] Adjust intake prompt to capture practice-specific KPIs
- [ ] Modify prioritization rules in agents/prioritization_agent.py
- [ ] Update health_status logic for practice criteria
- [ ] Customize HTML report sections in status_agent.py
- [ ] Test with 3-5 real projects
- [ ] Update documentation with practice-specific examples
- [ ] Adjust color scheme if using practice-specific branding
- [ ] Validate confidence scores with practice experts
```

---

## 6. Cost Analysis

### 6.1 Per-Report Cost

| Step | Model | Tokens | Cost |
|------|-------|--------|------|
| Flattening | Local | 0 | $0.00 |
| Intake | Sonnet | 2,000-3,000 | $0.03 |
| Prioritization | Haiku | 500-800 | $0.001 |
| Status | Sonnet | 3,000-5,000 | $0.04 |
| **Total** | - | 5,500-8,800 | **~$0.08** |

### 6.2 Monthly Cost Examples

```
10 reports/month   → $0.80
50 reports/month   → $4.00
100 reports/month  → $8.00
```

### 6.3 Cost Optimization Strategies

1. **Use Haiku for more steps**: Cheaper for simple tasks
2. **Reduce markdown size**: Fewer tokens to process
3. **Batch reports**: Process multiple in sequence
4. **Cache results**: Re-use extraction for similar reports

---

## 7. Error Handling & Resilience

### 7.1 Failure Points

| Step | Failure | Handling |
|------|---------|----------|
| File Read | Transcript missing | Raise ValueError with path |
| Metadata Parse | Invalid JSON | Fallback to empty dict |
| Flattening | No content found | Return empty string, low confidence |
| Intake API | Rate limit | Retry with exponential backoff |
| Intake JSON | Invalid response | Print response, raise error |
| Prioritization | Fewer items than expected | Continue with what exists |
| Status Generation | API failure | Fallback to template HTML |

### 7.2 Quality Assurance

- Confidence scores on all extractions
- Validation of JSON schemas
- Test with sample data before deployment
- Manual review of low-confidence items
- User feedback loop for improvements

---

## 8. Security Considerations

### 8.1 API Key Management
- Use environment variables, never hardcode
- Validate key exists before processing
- Consider using Azure Key Vault for enterprise

### 8.2 Data Handling
- All data processing is local (Python script)
- Only transcript text and KPIs sent to Claude API
- No PII storage between runs
- Reports can be sent via email (self-contained)

### 8.3 HTML Security
- No JavaScript in generated reports (prevents XSS)
- CSS-only interactions (collapsible sections)
- Content escaping in Claude prompts
- User-provided data sanitized before insertion

---

## 9. Integration Paths

### 9.1 Local Usage
```bash
python run_pipeline.py --transcript file.txt --metadata meta.json
```

### 9.2 Power Automate
```
Trigger: File created in SharePoint
→ Run Python script
→ Save HTML to output folder
→ Send Teams notification
```

### 9.3 Web Service
```
Flask app with endpoint:
POST /generate-report
  ├── Upload transcript
  ├── Upload metadata
  └── Return HTML or JSON
```

### 9.4 Scheduled Reports
```
Cron job (Linux/Mac):
0 9 * * MON python run_pipeline.py

Task Scheduler (Windows):
Daily at 9 AM: python run_pipeline.py
```

---

## 10. Future Enhancements

### Phase 2 (Next Quarter)
- [ ] Power Automate integration examples
- [ ] PDF snapshot archiving
- [ ] Multi-language support
- [ ] Custom color scheme per client

### Phase 3 (Next Half-Year)
- [ ] Dashboard for report history
- [ ] Trend analysis (project trajectory)
- [ ] Team-level roll-up reports
- [ ] Slack/Teams bot integration

### Phase 4 (Year+)
- [ ] Vision/image analysis for whiteboard photos
- [ ] Real-time transcription integration
- [ ] Predictive risk analysis
- [ ] Automated recommendation engine

---

## 11. Maintenance & Support

### 11.1 Monitoring
- Track API usage via Anthropic dashboard
- Monitor processing time trends
- Log all errors for debugging
- Archive reports for historical reference

### 11.2 Updates
- Monitor Claude model releases
- Test new models as they become available
- Update prompts if model behavior changes
- Maintain backward compatibility

### 11.3 Troubleshooting
- Check API key validity
- Validate input file formats
- Verify Python dependencies installed
- Review error messages in console output

---

## Conclusion

This architecture is designed for **production use**, **cost efficiency**, and **easy scalability** to other business practices. The modular design allows for customization without rewriting core components.

For questions about customization, see [Scalability Framework](#5-scalability-framework) section.
