# Project-Specific Pipeline Guide

Each project's workflow execution is **completely isolated** within its own folder.

---

## Structure (Isolated per Project)

```
projects/[project_name]/
│
├── README.md                    Project overview
├── metadata.json                Project configuration
│
├── input/                       📥 Input files
│   ├── transcript.txt
│   └── metadata.json
│
├── workflow_execution/          🔄 Pipeline Results (ISOLATED)
│   ├── 01_flattened/
│   │   ├── meeting_summary.md
│   │   ├── risks_issues.md
│   │   ├── deliverables.md
│   │   ├── timeline.md
│   │   ├── budget.md
│   │   └── metadata.yaml
│   │
│   ├── 02_intake_output.json
│   ├── 03_prioritized_output.json
│   ├── [project_name]_Status_Report.html
│   └── README.md
│
└── output/                      📤 Final outputs
    └── [project_name]_Status_Report.html
```

**Key Point**: Each project has its **own complete workflow_execution folder** with no cross-project mixing.

---

## How to Run (Project-Specific)

### Method 1: Easy (Recommended) ⭐

```bash
# This automatically finds input files and puts results in right place
python run_project_pipeline.py --project-name stephenson_rife
```

**This does automatically**:
- ✅ Finds transcript in `projects/stephenson_rife/input/transcript.txt`
- ✅ Finds metadata in `projects/stephenson_rife/input/metadata.json`
- ✅ Creates `projects/stephenson_rife/workflow_execution/`
- ✅ Puts all results in the right folder
- ✅ Copies final report to `projects/stephenson_rife/output/`

### Method 2: Custom Files

```bash
# Use custom transcript/metadata locations
python run_project_pipeline.py \
  --project-name stephenson_rife \
  --transcript projects/stephenson_rife/input/custom_transcript.txt \
  --metadata projects/stephenson_rife/input/custom_metadata.json
```

### Method 3: Advanced (Manual)

```bash
# Full control over the pipeline
python run_pipeline.py \
  --transcript projects/stephenson_rife/input/transcript.txt \
  --metadata projects/stephenson_rife/input/metadata.json \
  --project-name "Stephenson Rife" \
  --project-dir projects/stephenson_rife
```

---

## Results Location

All results go to **project's own workflow_execution folder**:

```bash
projects/stephenson_rife/workflow_execution/

# After running pipeline, you'll see:
├── 01_flattened/
│   ├── meeting_summary.md
│   ├── risks_issues.md
│   ├── deliverables.md
│   ├── timeline.md
│   ├── budget.md
│   └── metadata.yaml
├── 02_intake_output.json
├── 03_prioritized_output.json
├── stephenson_rife_Status_Report.html
└── README.md
```

---

## Complete Workflow (Step-by-Step)

### Step 1: Create Project
```bash
# Copy template
cp -r projects/_template_project projects/my_new_project

# Update project README
nano projects/my_new_project/README.md
```

### Step 2: Add Input Files
```bash
# Copy transcript
cp your_transcript.txt projects/my_new_project/input/transcript.txt

# Create metadata
nano projects/my_new_project/input/metadata.json
```

**metadata.json template**:
```json
{
  "project_name": "My New Project",
  "practice": "PMO",
  "client_name": "Client Name",
  "go_live_date": "2026-09-15",
  "timeline_status": "ON_TRACK",
  "budget_total": "$450,000",
  "budget_spent": "$187,000"
}
```

### Step 3: Run Pipeline
```bash
# Automatic (easiest)
python run_project_pipeline.py --project-name my_new_project
```

### Step 4: View Results
```bash
# Results are in:
projects/my_new_project/workflow_execution/

# Open the report:
open projects/my_new_project/workflow_execution/my_new_project_Status_Report.html
```

### Step 5: Archive When Done
```bash
# Move completed project to archive
mv projects/my_new_project archive/archived_2026_q3/my_new_project
```

---

## File Isolation (Complete Separation)

### ✅ Stephenson Rife Project
```
projects/stephenson_rife/
├── input/
│   ├── transcript.txt          (Stephenson Rife data only)
│   └── metadata.json
└── workflow_execution/         (Stephenson Rife results only)
    ├── 01_flattened/
    ├── 02_intake_output.json
    ├── 03_prioritized_output.json
    └── stephenson_rife_Status_Report.html
```

### ✅ Galfand Berger Project
```
projects/galfand_berger/
├── input/
│   ├── transcript.txt          (Galfand Berger data only)
│   └── metadata.json
└── workflow_execution/         (Galfand Berger results only)
    ├── 01_flattened/
    ├── 02_intake_output.json
    ├── 03_prioritized_output.json
    └── galfand_berger_Status_Report.html
```

### ✅ No Cross-Contamination
- Stephenson Rife's workflow_execution does NOT contain Galfand Berger data
- Galfand Berger's workflow_execution does NOT contain Stephenson Rife data
- Complete isolation per project
- Each project is self-contained

---

## Common Tasks

### View Project's Report
```bash
# Stephenson Rife
open projects/stephenson_rife/workflow_execution/stephenson_rife_Status_Report.html

# Galfand Berger
open projects/galfand_berger/workflow_execution/galfand_berger_Status_Report.html
```

### View Project's Extracted KPIs
```bash
# Pretty-print the JSON
cat projects/stephenson_rife/workflow_execution/02_intake_output.json | python -m json.tool

# Or in editor
nano projects/stephenson_rife/workflow_execution/02_intake_output.json
```

### View Flattened Data
```bash
# List flattened files
ls projects/stephenson_rife/workflow_execution/01_flattened/

# View specific file
cat projects/stephenson_rife/workflow_execution/01_flattened/meeting_summary.md
```

### Compare Two Projects
```bash
# View both reports side-by-side
open projects/stephenson_rife/workflow_execution/stephenson_rife_Status_Report.html
open projects/galfand_berger/workflow_execution/galfand_berger_Status_Report.html
```

### Delete Project Results (Keep Input)
```bash
# Remove workflow_execution (keep input/)
rm -rf projects/stephenson_rife/workflow_execution/*

# Then run pipeline again
python run_project_pipeline.py --project-name stephenson_rife
```

### Backup Project
```bash
# Tar the entire project
tar -czf stephenson_rife_backup.tar.gz projects/stephenson_rife/

# Or copy to external drive
cp -r projects/stephenson_rife /mnt/backup/
```

---

## Troubleshooting

### "Project folder not found"
```bash
# Create it from template
cp -r projects/_template_project projects/[project_name]
```

### "Transcript not found"
```bash
# Add it
cp your_transcript.txt projects/[project_name]/input/transcript.txt
```

### "Metadata not found"
```bash
# Create it
nano projects/[project_name]/input/metadata.json
```

### "Results not appearing"
```bash
# Check project folder structure
ls -la projects/[project_name]/

# Check for errors in console output above
```

### "Can't find the report"
```bash
# Look in workflow_execution
ls projects/[project_name]/workflow_execution/

# Should see: [project_name]_Status_Report.html
```

---

## Key Principles

✅ **Each Project Isolated**
- Own input folder
- Own workflow_execution folder
- Own output folder
- No cross-contamination

✅ **Organized Results**
- Stage 1: 01_flattened/
- Stage 2: 02_intake_output.json
- Stage 3: 03_prioritized_output.json
- Stage 4: [project]_Status_Report.html

✅ **Easy to Find**
- All project files in one place
- All pipeline results in one place
- Clear folder structure
- Easy to track sources

✅ **Scalable**
- Add unlimited projects
- Each is self-contained
- Archive completed ones
- No performance impact

---

## Example Scenarios

### Scenario 1: Run Pipeline for One Project
```bash
python run_project_pipeline.py --project-name stephenson_rife
# Results → projects/stephenson_rife/workflow_execution/
```

### Scenario 2: Run Multiple Projects in Sequence
```bash
python run_project_pipeline.py --project-name stephenson_rife
python run_project_pipeline.py --project-name galfand_berger
python run_project_pipeline.py --project-name new_client

# Each has results in its own workflow_execution/ folder
```

### Scenario 3: Rerun One Project (Overwrite Results)
```bash
# Update input files
nano projects/stephenson_rife/input/transcript.txt

# Run again
python run_project_pipeline.py --project-name stephenson_rife

# Results overwritten in workflow_execution/
```

### Scenario 4: Archive Project, Start Fresh
```bash
# Archive old project
mv projects/stephenson_rife archive/archived_2026_q3/stephenson_rife

# Create new one
cp -r projects/_template_project projects/stephenson_rife

# Fresh start with new input
```

---

## Summary

✅ **Yes, workflow execution IS completely isolated per project**
- Stephenson Rife: `projects/stephenson_rife/workflow_execution/`
- Galfand Berger: `projects/galfand_berger/workflow_execution/`
- Each project stores its own input → pipeline → output
- No mixing of data between projects
- Easy to find, track, and manage

**Run any project with**: 
```bash
python run_project_pipeline.py --project-name [project_name]
```

---

For questions, see:
- `docs/GETTING_STARTED.md` - General setup
- `projects/README.md` - Project management
- `FOLDER_STRUCTURE.md` - Overall organization
