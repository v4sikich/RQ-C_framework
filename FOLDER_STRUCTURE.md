# Production Folder Structure - Clean & Organized

This document explains the clean folder structure for easy navigation, file tracking, and project management.

---

## Directory Tree

```
production/
│
├── 📚 docs/                                 [DOCUMENTATION]
│   ├── README.md                            Main project overview
│   ├── GETTING_STARTED.md                   Setup & installation guide
│   ├── ARCHITECTURE.md                      Technical design & scalability
│   ├── DIAGRAMS.md                          Visual system architecture
│   ├── PRODUCTION_CHECKLIST.md              Deployment validation
│   ├── FOLDER_STRUCTURE.md                  This file
│   └── API.md                               API reference (optional)
│
├── 🔧 src/                                  [SOURCE CODE]
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── intake_agent.py                  Extract KPIs from markdown
│   │   ├── prioritization_agent.py          Rank & filter for slide
│   │   └── status_agent.py                  Generate HTML report
│   │
│   ├── scripts/
│   │   └── flatten.py                       Convert transcript to markdown
│   │
│   └── run_pipeline.py                      Main orchestration script
│
├── ⚙️ config/                               [CONFIGURATION]
│   ├── requirements.txt                     Python dependencies
│   ├── .env.example                         Environment variables template
│   ├── .gitignore                           Git configuration
│   └── settings.json                        Optional project settings
│
├── 📋 projects/                             [PROJECT-SPECIFIC DATA]
│   │
│   ├── stephenson_rife/                     ✅ EXAMPLE PROJECT
│   │   ├── README.md                        Project-specific notes
│   │   ├── metadata.json                    Project configuration
│   │   │
│   │   ├── input/                           📥 Input files
│   │   │   ├── transcript.txt
│   │   │   ├── transcript.vtt (optional)
│   │   │   └── metadata.json
│   │   │
│   │   ├── workflow_execution/              🔄 Pipeline execution results
│   │   │   ├── 01_flattened/                Flattened markdown chunks
│   │   │   │   ├── meeting_summary.md
│   │   │   │   ├── risks_issues.md
│   │   │   │   ├── deliverables.md
│   │   │   │   ├── timeline.md
│   │   │   │   ├── budget.md
│   │   │   │   └── metadata.yaml
│   │   │   │
│   │   │   ├── 02_intake_output.json        Extracted KPIs
│   │   │   ├── 03_prioritized_output.json   Ranked & filtered KPIs
│   │   │   ├── stephenson_rife_Status_Report.html
│   │   │   └── README.md                    Workflow execution notes
│   │   │
│   │   └── output/                          📤 Final outputs (if needed)
│   │       └── stephenson_rife_Status_Report.html
│   │
│   ├── galfand_berger/                      ✅ EXAMPLE PROJECT
│   │   ├── README.md
│   │   ├── metadata.json
│   │   ├── input/
│   │   ├── workflow_execution/
│   │   └── output/
│   │
│   ├── _template_project/                   📝 TEMPLATE FOR NEW PROJECTS
│   │   ├── README.md
│   │   ├── metadata.json.example
│   │   ├── input/
│   │   │   ├── README.md                    Instructions for input files
│   │   │   └── transcript.txt.example
│   │   ├── workflow_execution/
│   │   │   └── README.md
│   │   └── output/
│   │       └── README.md
│   │
│   └── README.md                            Guide for managing projects
│
├── 🎨 branding/                             [LOGOS & VISUAL ASSETS]
│   ├── sikich/
│   │   ├── logo.svg
│   │   ├── logo.png
│   │   ├── colors.json                      Color palette
│   │   └── README.md
│   │
│   └── custom/                              Custom branding per client
│       └── client_name/
│           └── logo.png
│
├── 📦 templates/                            [HTML & CSS TEMPLATES]
│   ├── base_template.html                   Base HTML structure
│   ├── styles.css                           Styling (if needed)
│   ├── sikich_theme.css                     Sikich branded theme
│   └── README.md                            Template guide
│
├── 🛠️ utils/                                [UTILITY SCRIPTS & HELPERS]
│   ├── backup.py                            Backup script
│   ├── validate_json.py                     JSON validator
│   ├── bulk_process.py                      Process multiple projects
│   └── README.md                            Utilities guide
│
├── 📖 examples/                             [EXAMPLE OUTPUTS & REFERENCES]
│   ├── sample_report_output.html            Example generated report
│   ├── sample_intake_output.json            Example KPIs
│   ├── sample_prioritized_output.json       Example prioritized data
│   └── README.md
│
└── 📊 archive/                              [OLD PROJECTS & BACKUPS]
    ├── archived_2026_q1/
    └── README.md

```

---

## Folder Purposes & Guidelines

### 📚 `docs/` - Documentation
**Purpose**: All project documentation, guides, and references

**Files**:
- `README.md` - Start here
- `GETTING_STARTED.md` - Setup instructions
- `ARCHITECTURE.md` - Technical details
- `DIAGRAMS.md` - System architecture
- `PRODUCTION_CHECKLIST.md` - Deployment checklist
- `FOLDER_STRUCTURE.md` - This file
- `API.md` - API reference (optional)

**Guidelines**:
- Keep docs current with code changes
- Use markdown format
- Include examples where helpful
- Version control all docs

---

### 🔧 `src/` - Source Code
**Purpose**: All production Python code

**Structure**:
```
src/
├── agents/              (Claude agent implementations)
├── scripts/             (Data processing utilities)
└── run_pipeline.py      (Main entry point)
```

**Guidelines**:
- Keep code production-ready
- Follow PEP 8 style guide
- Include docstrings
- Version control carefully
- Don't modify for individual projects

---

### ⚙️ `config/` - Configuration Files
**Purpose**: Settings, dependencies, environment config

**Files**:
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variable template
- `.gitignore` - Git configuration
- `settings.json` - Optional project settings

**Guidelines**:
- Never commit actual `.env` with secrets
- Keep `requirements.txt` minimal
- Document all config options
- Use `.env.example` for reference

---

### 📋 `projects/` - Project-Specific Data
**Purpose**: Organize each project separately

**Structure per project**:
```
projects/[project_name]/
├── README.md                    Project notes & metadata
├── metadata.json                Project configuration
├── input/                       Input files (transcripts, metadata)
├── workflow_execution/          Pipeline execution results
└── output/                      Final output files (if needed)
```

**Example Projects**:
- `stephenson_rife/` - Filevine implementation
- `galfand_berger/` - Law firm implementation
- `_template_project/` - Template for new projects

**Guidelines**:
- One folder per project
- Keep organized by phase
- Track inputs and outputs separately
- Include project-specific README
- Archive old projects to `archive/`

---

### 🎨 `branding/` - Visual Assets
**Purpose**: Logos, colors, and branding elements

**Structure**:
```
branding/
├── sikich/              (Sikich brand assets)
│   ├── logo.svg
│   ├── logo.png
│   ├── colors.json      (Color palette)
│   └── README.md
└── custom/              (Client-specific branding)
    └── [client_name]/
```

**Guidelines**:
- Keep logos in both SVG and PNG
- Document color hex codes
- Organize by brand/client
- SVG preferred for web

---

### 📦 `templates/` - HTML & CSS Templates
**Purpose**: Reusable HTML and CSS templates

**Files**:
- `base_template.html` - Base HTML structure
- `sikich_theme.css` - Sikich branded styling
- `custom_theme.css` - Optional custom themes

**Guidelines**:
- Maintain HTML structure
- Keep CSS modular
- Document template variables
- Test responsive design

---

### 🛠️ `utils/` - Utility Scripts
**Purpose**: Helper scripts for common tasks

**Examples**:
- `backup.py` - Backup projects
- `validate_json.py` - Validate JSON files
- `bulk_process.py` - Process multiple projects
- `cleanup.py` - Clean old files

**Guidelines**:
- Keep utilities independent
- Include usage documentation
- Test thoroughly before use
- Don't modify core agents

---

### 📖 `examples/` - Example Files
**Purpose**: Sample outputs and references

**Files**:
- `sample_report_output.html` - Example generated report
- `sample_intake_output.json` - Example KPIs
- `sample_prioritized_output.json` - Example prioritized data
- `sample_transcript.txt` - Example transcript

**Guidelines**:
- Keep examples fresh
- Update when output format changes
- Use for testing and reference
- Document example project details

---

### 📊 `archive/` - Old Projects
**Purpose**: Store completed/archived projects

**Structure**:
```
archive/
├── archived_2026_q1/   (Quarterly archives)
│   ├── project_1/
│   ├── project_2/
│   └── README.md
└── completed_projects/
    ├── old_project_1/
    └── old_project_2/
```

**Guidelines**:
- Archive by date or category
- Include archive README
- Maintain for historical reference
- Don't delete, only archive

---

## Project Directory Template

When creating a new project, use this structure:

```
projects/[project_name]/
│
├── README.md
│   # Project overview, dates, team, notes
│
├── metadata.json
│   # Project configuration
│   {
│     "project_name": "...",
│     "practice": "PMO",
│     "go_live_date": "...",
│     "status_date": "...",
│     "budget_total": "...",
│     "budget_spent": "..."
│   }
│
├── input/
│   ├── README.md              # Instructions for input files
│   ├── transcript.txt         # Meeting transcript
│   └── transcript.vtt         # Optional VTT format
│
├── workflow_execution/
│   ├── 01_flattened/          # Flattened markdown (auto-generated)
│   ├── 02_intake_output.json  # Extracted KPIs (auto-generated)
│   ├── 03_prioritized_output.json  # Ranked data (auto-generated)
│   ├── [project]_Status_Report.html # Final report (auto-generated)
│   └── README.md              # Execution notes
│
└── output/
    ├── README.md              # Output notes
    └── [project]_Status_Report.html # Copy of final report
```

---

## File Tracking & Source Management

### How to Find Files

**By Type**:
- Documentation → `docs/`
- Source Code → `src/`
- Project Data → `projects/[name]/`
- Configuration → `config/`
- Visual Assets → `branding/`

**By Project**:
- All project files → `projects/[project_name]/`
- Input files → `projects/[project_name]/input/`
- Execution results → `projects/[project_name]/workflow_execution/`
- Outputs → `projects/[project_name]/output/`

**By Stage**:
- Flattened data → `workflow_execution/01_flattened/`
- Extracted KPIs → `workflow_execution/02_intake_output.json`
- Prioritized → `workflow_execution/03_prioritized_output.json`
- Final report → `workflow_execution/[name]_Status_Report.html`

### Source Tracking

Each project folder includes metadata for tracking:

1. **metadata.json** - Project configuration and details
2. **input/README.md** - Input file descriptions
3. **workflow_execution/README.md** - Execution notes
4. **projects/README.md** - Project index

---

## Common Tasks & File Locations

| Task | Location |
|------|----------|
| Add new project | `projects/[new_project_name]/` |
| Review documentation | `docs/` |
| Find project transcript | `projects/[name]/input/` |
| Find project report | `projects/[name]/workflow_execution/` |
| Customize branding | `branding/sikich/` |
| View example output | `examples/` |
| Update dependencies | `config/requirements.txt` |
| Archive old project | `archive/` |

---

## Workflow Execution in Detail

For each project, the workflow_execution folder tracks the complete pipeline:

```
projects/[project]/workflow_execution/
│
├── 01_flattened/
│   ├── meeting_summary.md      (95% confidence)
│   ├── risks_issues.md         (75% confidence)
│   ├── deliverables.md         (80% confidence)
│   ├── timeline.md             (85% confidence)
│   ├── budget.md               (70% confidence)
│   └── metadata.yaml           (source tracking)
│
├── 02_intake_output.json
│   {
│     "project_name": "...",
│     "timeline": {...},
│     "deliverables": {...},
│     "risks": [{...}],
│     "budget": {...},
│     "health_status": "...",
│     "confidence_scores": {...}
│   }
│
├── 03_prioritized_output.json
│   {
│     "executive_summary": "...",
│     "health_status_visual": "RED|YELLOW|GREEN",
│     "risks_to_highlight": [...],
│     "key_accomplishments": [...],
│     "upcoming_focus": [...],
│     "recommendations": [...]
│   }
│
├── [project]_Status_Report.html
│   (Self-contained HTML report)
│
└── README.md
    # Notes about this execution
    # Date executed, version, any issues
```

---

## Version Control & Git

### Files to Track
- ✅ All files in `src/`
- ✅ All files in `docs/`
- ✅ All files in `config/` (except .env)
- ✅ `branding/` (except custom logos)
- ✅ `templates/`
- ✅ `utils/`

### Files to Ignore (.gitignore)
- ❌ `.env` (use `.env.example`)
- ❌ `projects/*/input/` (local data)
- ❌ `projects/*/workflow_execution/` (generated)
- ❌ `projects/*/output/` (generated)
- ❌ `__pycache__/`
- ❌ `*.pyc`

---

## Best Practices

### Organization
1. ✅ Keep projects separate in `projects/[name]/`
2. ✅ One workflow_execution per project
3. ✅ Archive old projects instead of deleting
4. ✅ Use consistent naming conventions
5. ✅ Document project metadata

### File Management
1. ✅ Keep input files organized by type
2. ✅ Don't modify workflow_execution files manually
3. ✅ Use README files to document
4. ✅ Track source of inputs
5. ✅ Archive outputs periodically

### Documentation
1. ✅ Keep README files current
2. ✅ Document project-specific notes
3. ✅ Include execution timestamps
4. ✅ Track version of code used
5. ✅ Note any customizations

---

## Summary

This folder structure ensures:
- 🎯 **Easy Navigation** - Find files quickly
- 📊 **Clear Organization** - By project and type
- 📈 **Scalability** - Grow to many projects
- 🔍 **Traceability** - Track sources and results
- 🔐 **Security** - Sensitive data separated
- 📝 **Documentation** - Everything explained
- 🗂️ **Maintainability** - Easy to manage

**Next Step**: Review `GETTING_STARTED.md` to begin using this structure!
