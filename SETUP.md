Status IQ Cloud — Setup & Run Instructions
============================================

## What you (the human) need to do

1. Save this file somewhere on your computer, open a terminal in that folder,
   and start Claude Code (type `claude`).
2. Say to it: **"Read SETUP.md and set this project up for me."**
3. That's it. Claude Code will do everything else itself, and will only stop
   to ask you for three things, when it gets there:
   - Your **Anthropic API key** (a string given to you separately, starting
     with `sk-ant-`).
   - Your **project/client name**, and for you to drop your files into a
     folder it creates — any mix of Word docs, PDFs, Excel workbooks,
     PowerPoint decks, meeting notes, whatever you have, exactly as they are.
     No cleanup or converting needed.
   - Whether the **report it generates looks right**, or what to change about
     it — just describe it in plain English (e.g. "the budget is wrong, it
     should be $500k" or "remove the risk about staffing, that's resolved").
     You can go back and forth on this as many times as you like.

Everything past this point is written for Claude Code to follow, not for you.
You don't need to read any further.

---

## Instructions for Claude Code

Work through the steps below **in order, automatically**, using your own
shell access — do not ask the user to type or run any command themselves.
Narrate briefly in plain, non-technical language as you go (the user has no
coding background) and confirm each step succeeded before moving to the next.

**Only stop and ask the user directly at the three points marked `⏸ PAUSE`.**
Everywhere else, make reasonable decisions yourself and keep going use professional formal language to ask anything to user.

### 1. Check for Python, install it if missing

Run `python --version`.
- If it prints something like `Python 3.12.4`, continue to step 2.
- If it says `'python' is not recognized...` or opens the Microsoft Store,
  install it:
  ```
  winget install Python.Python.3.12
  ```
  Answer `Y` if prompted to accept terms. Note that a fresh terminal process
  may be needed afterward for PATH to update — if `python --version` still
  fails right after install, tell the user you need to be restarted (closed
  and reopened) once, then re-verify.

### 2. Get the project code

Check whether you're already inside the `RQ-C_framework` repo (e.g. this
SETUP.md file lives inside a folder containing `run_pipeline.py`, `agents/`,
etc.). If so, skip cloning and just note that the code is already present.

Otherwise, clone it into a subfolder here and move into it:
```
git clone https://github.com/v4sikich/RQ-C_framework
cd RQ-C_framework
```

### 3. Create and activate a virtual environment

```
python -m venv venv
.\venv\Scripts\Activate.ps1
```
From here on, run all Python/pip commands using this venv (e.g.
`.\venv\Scripts\python.exe`, `.\venv\Scripts\pip.exe`, or with it activated in
the current shell).

### 4. Install required packages

```
pip install -r requirements.txt
```
Confirm it finishes without errors before continuing.

### 5. ⏸ PAUSE — Ask for the Anthropic API key

Ask the user to paste their Anthropic API key (looks like
`sk-ant-api03-...`). Wait for their reply, then save it:
```powershell
"ANTHROPIC_API_KEY=<the key they gave you>" | Out-File -Encoding utf8 .env
```
Confirm it saved by reading `.env` back and checking it starts with
`ANTHROPIC_API_KEY=sk-ant-`. Don't echo the full key back into the chat.
`.env` is already covered by `.gitignore` — never commit it.

### 6. ⏸ PAUSE — Ask for the project name and input files

Ask the user two things at once:
- What should this project/client be called?
- Please add their files for it now (Word docs, PDFs, Excel, PowerPoint,
  meeting notes — any mix, unedited add that currently audio and video files are not supported).

While waiting on their reply, prepare the folder so it's ready the moment
they say the files are in:
- Turn the name into a safe folder name (lowercase, spaces → underscores,
  e.g. "Acme Corp" → `acme_corp`).
- Create it from the template:
  ```
  Copy-Item -Recurse projects\_template_project projects\acme_corp
  ```
- Tell the user the exact path to drop files into this is mandatory:
  `projects\acme_corp\input\`

Once they confirm files are in place, list `projects\acme_corp\input\` and
briefly confirm what you found (e.g. "found a SOW PDF, a Word doc, and an
Excel workbook") before moving on. If the folder is empty, say so and wait.

### 7. Run the pipeline

```
python run_pipeline.py --input-dir "projects\acme_corp\input" --project-dir "projects\acme_corp" --project-name "Acme Corp"
```
Do **not** add `--interactive` — that flag pauses for input in a live
terminal, which doesn't work over tool calls. The review/feedback loop below
happens in chat instead.

This produces, inside `projects\acme_corp\workflow_execution\`:
- `01_flattened/` — the raw files broken into organized sections
- `02_intake_output.json` — extracted facts (timeline, budget, risks, etc.)
- `03_prioritized_output.json` — the same facts, ranked/filtered for the report
- `<Client>_Status_Report.html` — the final report
- `<Client>_Status_Report.pptx` — the same report as a PowerPoint slide

If the run fails, diagnose the actual cause (e.g. bad API key, empty input
folder) and explain it to the user in plain language rather than showing a
raw traceback — fix what you can (e.g. re-run step 5 or 6) and retry.

### 8. ⏸ PAUSE (repeatable) — Review and get feedback

Read `02_intake_output.json` from the
client's `workflow_execution/` folder and give the user a simple-English
recap of what got extracted and what made it into the report: overall health
status, key risks, budget numbers, upcoming milestones, etc. (You can build
this from `agents/review_summaries.py`'s `summarize_intake_kpis()`  as a structured starting point, then show into plain language — don't show the user raw JSON but the exact content without rephrasing and state facts no guesses no recommendations nothing else)

Ask the user whether it looks right or what should change. Wait for their
reply. explicitely ask in bold : 'Do you approve or Do you need changes at this step'

- If they approve ("looks good", "approved", etc.), continue to step 9.
- If they give feedback, apply it using the same revise methods the built-in
  `--interactive` mode uses (don't hand-edit the JSON yourself):
  - `agents.intake_agent.IntakeAgent().revise_kpis(current_kpis, feedback)`
    for feedback about extracted facts.
  
  Save the revised JSON back to the same files, then regenerate the output
  file from the updated `02_intake_output.json`:

  Show the updated summary and ask again. Repeat as many rounds as the user
  wants — there's no limit. Try to include all important things in the report

### 9. ⏸ PAUSE (repeatable) — Review and get feedback

Read  `03_prioritized_output.json` from the
client's `workflow_execution/` folder and give the user a simple-English
recap of what got prioritised order them and what made it into the report and what was not included that might be important: overall health
status, key risks, budget numbers, upcoming milestones, etc. (You can build
this from `agents/review_summaries.py`'s `summarize_prioritized_kpis()`  as a structured starting point, then show into plain language — don't show the user raw JSON but the exact content without rephrasing and state facts no guesses no recommendations nothing else)

Ask the user whether it looks right or what should change. Wait for their
reply. explicitely ask in bold : 'Do you approve or Do you need changes at this step'

- If they approve ("looks good", "approved", etc.), continue to step 9.
- If they give feedback, apply it using the same revise methods the built-in
  `--interactive` mode uses (don't hand-edit the JSON yourself):

  - `agents.prioritization_agent.PrioritizationAgent().revise_prioritized(current_prioritized, feedback)`
    for feedback about what's highlighted or how it's framed.
  Save the revised JSON back to the same files, then regenerate the output
  file from the updated `03_prioritized_output.json`:
  - `agents.status_agent.StatusReportAgent().generate_html_report(...)`
  - `agents.ppt_agent.PptxReportAgent().generate_pptx_report(...)`
  Show the updated summary and ask again. Repeat as many rounds as the user
  wants — there's no limit. Try to include all important things in the report
  Use no emojis, no health-bar, keep it professional

### 10. Show the final report

Open the HTML report in the default browser (`start <path>`) and tell the
user where the PPTX file is too:
```
projects\acme_corp\workflow_execution\Acme_Corp_Status_Report.html
projects\acme_corp\workflow_execution\Acme_Corp_Status_Report.pptx
```
A copy of the final HTML also gets placed in `projects\acme_corp\output\`, show this path and keep the path of workflow execution hidden
Dont give any summary or insight at end just open the html and the path to pptx file

### 11. Later re-runs

If the user later says they have a **new client**, repeat from step 6 with a
new project name (a fresh folder, input files, run, review).

If they say they have **updated files for the same client** (e.g. this
month's status meeting), have them add/replace files in that client's
existing `input\` folder, then re-run from step 7 — new results overwrite the
previous ones in that client's `workflow_execution\` folder.

If they want to start over for a client, delete that client's
`workflow_execution\` folder (leaving `input\` untouched) and re-run step 7.

---

## Troubleshooting (for Claude Code's own diagnosis)

- **API key errors during step 7/8**: re-check `.env`; if wrong or missing,
  re-run step 5.
- **`python` not recognized after install**: PATH not refreshed yet — ask the
  user to restart the Claude Code session once, then re-verify.
- **A file the user added didn't seem to get used**: check its extension
  against what `scripts/input_adapter.py` supports; video/audio files (mp4,
  mov, wav, etc.) are intentionally called out as unprocessed evidence rather
  than silently dropped, not a bug.
- **Pipeline fails partway through**: read the actual error rather than
  guessing; most failures are a missing/invalid API key or an empty input
  folder.
