# Input Files - README

This folder contains the input files needed to run the pipeline.

---

## Required Files

### 1. transcript.txt
**Description**: Meeting transcript or project notes  
**Format**: Plain text file  
**Required Fields**:
- Meeting agenda/topics
- Timeline status
- Completed work
- Upcoming deliverables
- Known risks
- Budget status (if applicable)

**Example**:
```
# Project Status Meeting - [Date]

Attendees: [Names]

## Timeline Status
Project is on track for Sept 15 go-live.
Phase 1 completed early.
Phase 2 is 40% complete.

## Completed Work
- Requirements document approved
- API design completed
- Security review passed

## Upcoming
- Technical design due Aug 22
- Development starts Aug 25
- UAT starts Sept 8

## Risks
- Main developer 50% available Sept 1-3 weeks
- Integration complexity increased from 8 to 12 points
- Data quality issues in 20% of records

## Budget
$187K spent of $450K total (41.6%), on budget.
```

### 2. metadata.json
**Description**: Structured project configuration  
**Format**: JSON file

**Required Fields**:
```json
{
  "project_name": "Your Project Name",
  "practice": "PMO",
  "client_name": "Client Name",
  "go_live_date": "2026-09-15",
  "status_date": "2026-08-05",
  "timeline_status": "ON_TRACK",
  "budget_total": "$450,000",
  "budget_spent": "$187,000"
}
```

---

## Optional Files

- **transcript.vtt** - VTT (WebVTT) format transcript
- **Additional documents** - Supporting materials

---

## File Naming Conventions

Use consistent naming:
- **Transcripts**: `transcript.txt` or `[project]_transcript.vtt`
- **Metadata**: `metadata.json`
- **Date Format**: YYYY-MM-DD

---

## Preparing Your Files

### For Transcript.txt

1. **Gather Information**:
   - Meeting notes
   - Email updates
   - Status reports
   - Project documents

2. **Organize by Section**:
   - Timeline status
   - Completed deliverables
   - Upcoming milestones
   - Risks and issues
   - Budget status

3. **Clean Up**:
   - Remove sensitive data
   - Fix typos
   - Ensure dates are clear
   - Remove unnecessary details

4. **Save as Plain Text**:
   - File → Save As
   - Choose "Plain Text" format
   - Name it `transcript.txt`

### For metadata.json

1. **Gather Information**:
   - Project name
   - Client name
   - Go-live date
   - Current spending
   - Timeline status

2. **Format Properly**:
   - Valid JSON syntax
   - Date format: YYYY-MM-DD
   - Budget format: "$XXX,XXX"
   - Status: ON_TRACK, AT_RISK, DELAYED

3. **Validate**:
   - Use online JSON validator
   - Check all required fields
   - Verify date formats

4. **Save as JSON**:
   - Use .json extension
   - Name it `metadata.json`

---

## Validation

Before running pipeline, verify:

✅ `transcript.txt` exists and has content  
✅ `metadata.json` exists and is valid JSON  
✅ All required fields in metadata  
✅ Dates are in YYYY-MM-DD format  
✅ Budget values are formatted correctly  

---

## Troubleshooting

### File Not Found
- ✅ Check file is in this folder
- ✅ Check filename spelling
- ✅ Verify file extension

### Invalid JSON
- ✅ Use online JSON validator
- ✅ Check for missing commas
- ✅ Verify quotes are correct

### Missing Data
- ✅ Add missing sections to transcript
- ✅ Fill in all metadata fields
- ✅ Include timeline and risk info

---

**Next**: Once files are ready, run the pipeline from the production root:

```bash
python run_pipeline.py \
  --transcript projects/[project]/input/transcript.txt \
  --metadata projects/[project]/input/metadata.json \
  --project-name "[Project Name]"
```
