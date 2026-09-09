#!/usr/bin/env python3
"""
Input Adapter: Normalizes an arbitrary folder of real-world project files into
the transcript/metadata/excel shape the rest of the pipeline expects.

Real client folders don't arrive as one transcript.txt + one metadata.json -
they show up as a pile of meeting notes, SOW exports, deck exports, and a
project workbook split into a dozen CSVs, all named however the client named
them. Rather than requiring the input to be reshaped to fit the pipeline, this
module adapts the pipeline's input handling to whatever it's handed:

  - every .txt/.md file gets concatenated into one transcript
  - every .csv file becomes a sheet in one merged .xlsx
  - if a SOW-like document is present, real project metadata (name, dates,
    budget, deliverables) is extracted from it via Claude instead of relying
    on a hand-authored metadata.json
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import anthropic

TEXT_EXTENSIONS = {".txt", ".md"}
DOC_EXTENSIONS = {".docx", ".pdf", ".pptx"}
DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS | DOC_EXTENSIONS
CSV_EXTENSION = ".csv"
WORKBOOK_EXTENSIONS = {".xlsx", ".xlsm"}
# Formats real client folders contain that this pipeline has no text/data
# extraction for (video/audio recordings, in-progress downloads). Rather than
# silently dropping them, they're called out in the combined transcript so the
# evidence gap they represent stays visible downstream.
UNPROCESSED_EXTENSIONS = {".mp4", ".mov", ".m4a", ".wav", ".crdownload"}
SOW_NAME_HINTS = ("sow", "statement of work")


def _is_office_temp_file(path: Path) -> bool:
    # Word/Excel/PowerPoint lock files (e.g. "~$Notes.docx") left behind by an
    # open editor - not real content, and often unreadable as a zip archive.
    return path.name.startswith("~$")


def _is_sow_file(path: Path) -> bool:
    name = path.stem.lower()
    return any(hint in name for hint in SOW_NAME_HINTS)


def discover_text_files(input_dir: Path) -> List[Path]:
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS)


def discover_document_files(input_dir: Path) -> List[Path]:
    """Every text-extractable document: plain text/markdown plus DOCX/PDF/PPTX,
    which is how real client folders actually hand over meeting notes, SOWs and
    kickoff decks."""
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in DOCUMENT_EXTENSIONS and not _is_office_temp_file(p)
    )


def discover_csv_files(input_dir: Path) -> List[Path]:
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() == CSV_EXTENSION)


def discover_workbook_files(input_dir: Path) -> List[Path]:
    return sorted(
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in WORKBOOK_EXTENSIONS and not _is_office_temp_file(p)
    )


def discover_unprocessed_files(input_dir: Path) -> List[Path]:
    return sorted(p for p in input_dir.iterdir() if p.is_file() and p.suffix.lower() in UNPROCESSED_EXTENSIONS)


def extract_docx_text(path: Path) -> str:
    import docx
    document = docx.Document(str(path))
    parts = [p.text for p in document.paragraphs if p.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            if any(cells):
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def extract_pdf_text(path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def extract_pptx_text(path: Path) -> str:
    from pptx import Presentation
    presentation = Presentation(str(path))
    parts = []
    for i, slide in enumerate(presentation.slides, start=1):
        slide_parts = []
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                slide_parts.append(shape.text_frame.text.strip())
            elif shape.has_table:
                for row in shape.table.rows:
                    cells = [c.text.strip() for c in row.cells]
                    if any(cells):
                        slide_parts.append(" | ".join(cells))
        if slide_parts:
            parts.append(f"[Slide {i}]\n" + "\n".join(slide_parts))
    return "\n\n".join(parts)


def extract_document_text(path: Path) -> str:
    """Dispatch to the right extractor for whatever document format this is."""
    suffix = path.suffix.lower()
    if suffix in TEXT_EXTENSIONS:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix == ".docx":
        return extract_docx_text(path)
    if suffix == ".pdf":
        return extract_pdf_text(path)
    if suffix == ".pptx":
        return extract_pptx_text(path)
    raise ValueError(f"No text extractor for {path.suffix} ({path.name})")


def find_sow_file(input_dir: Path) -> Optional[Path]:
    for path in discover_document_files(input_dir):
        if _is_sow_file(path):
            return path
    return None


def combine_text_sources(input_dir: Path) -> str:
    """Concatenate every text-extractable document (.txt/.md/.docx/.pdf/.pptx)
    into one transcript-like document, labeled by source filename so downstream
    keyword extraction can still tell sections apart regardless of how many
    separate notes/decks/exports the folder contains. Files this pipeline can't
    extract text from (meeting recordings, in-progress downloads) are listed
    by name instead of silently dropped, so the evidence gap stays visible."""
    document_files = discover_document_files(input_dir)
    if not document_files:
        raise ValueError(f"No text-extractable files (.txt/.md/.docx/.pdf/.pptx) found in {input_dir}")

    chunks = []
    for path in document_files:
        try:
            text = extract_document_text(path)
        except Exception as e:
            text = f"[Could not extract text from this file: {e}]"
        chunks.append(f"\n\n===== SOURCE: {path.name} =====\n\n{text}")

    unprocessed = discover_unprocessed_files(input_dir)
    if unprocessed:
        names = "\n".join(f"- {p.name}" for p in unprocessed)
        chunks.append(
            "\n\n===== UNPROCESSED SOURCES (no text extraction available - "
            f"treat as evidence gap) =====\n\n{names}\n"
        )

    return "".join(chunks).strip() + "\n"


def _strip_common_prefix(names: List[str]) -> List[str]:
    """Real project workbook exports are often split into many CSVs sharing one
    long filename prefix (e.g. "PROJECT WORKBOOK (2)_Timeline", "..._Scope").
    Naive 31-char sheet-name truncation would collapse them all to that shared
    prefix, discarding the one part that actually distinguishes each sheet."""
    if len(names) <= 1:
        return names
    prefix = os.path.commonprefix(names)
    cut = max(prefix.rfind('_'), prefix.rfind(' '))
    if cut > 0:
        prefix = prefix[:cut + 1]
    return [n[len(prefix):].strip() or n for n in names]


def _safe_sheet_name(name: str, used_names: set) -> str:
    # Excel sheet names: <=31 chars, and can't contain [ ] : * ? / \
    cleaned = re.sub(r'[\[\]:*?/\\]', '_', name).strip()[:31] or "Sheet"
    candidate = cleaned
    i = 2
    while candidate in used_names:
        suffix = f"_{i}"
        candidate = cleaned[:31 - len(suffix)] + suffix
        i += 1
    used_names.add(candidate)
    return candidate


def _read_csv_robust(path: Path) -> pd.DataFrame:
    """Windows/Excel-exported CSVs are frequently cp1252 (smart quotes, en/em
    dashes), not UTF-8. Try common encodings before giving up."""
    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except UnicodeDecodeError as e:
            last_error = e
    # latin-1 maps every byte to a character so it should never reach here, but
    # keep a final explicit fallback rather than raising last_error silently.
    return pd.read_csv(path, encoding="latin-1")


def _read_workbook_sheets(path: Path) -> List[tuple]:
    """Read every sheet of one workbook as (sheet_name, dataframe) pairs."""
    try:
        excel_file = pd.ExcelFile(path)
    except Exception as e:
        print(f"   [skipped] {path.name}: {e}")
        return []

    sheets = []
    for sheet_name in excel_file.sheet_names:
        try:
            df = pd.read_excel(path, sheet_name=sheet_name)
        except Exception as e:
            print(f"   [skipped] {path.name}::{sheet_name}: {e}")
            continue
        if df.empty:
            continue
        sheets.append((sheet_name, df))
    return sheets


def combine_tabular_sources_to_excel(input_dir: Path, output_path: Path) -> Optional[Path]:
    """Merge every CSV export and every Excel workbook found into one .xlsx (one
    sheet per CSV, every sheet of every workbook carried over) so a real project
    folder can hand over any number of spreadsheets/exports without the pipeline
    silently dropping all but one."""
    csv_files = discover_csv_files(input_dir)
    workbook_files = discover_workbook_files(input_dir)
    if not csv_files and not workbook_files:
        return None

    # Exactly one workbook and no CSVs to merge in: pass it through as-is
    # rather than round-tripping it through pandas.
    if not csv_files and len(workbook_files) == 1:
        return workbook_files[0]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    used_names: set = set()
    wrote_any = False
    csv_short_names = _strip_common_prefix([p.stem for p in csv_files])

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for path, short_name in zip(csv_files, csv_short_names):
            try:
                df = _read_csv_robust(path)
            except Exception as e:
                print(f"   [skipped] {path.name}: {e}")
                continue
            if df.empty:
                continue
            df.to_excel(writer, sheet_name=_safe_sheet_name(short_name, used_names), index=False)
            wrote_any = True

        multiple_workbooks = len(workbook_files) > 1
        for wb_path in workbook_files:
            for sheet_name, df in _read_workbook_sheets(wb_path):
                # Only prefix with the source workbook name when there's more
                # than one workbook, so a single workbook's sheets keep their
                # original names (matches the old passthrough behavior).
                label = f"{wb_path.stem}_{sheet_name}" if multiple_workbooks else sheet_name
                df.to_excel(writer, sheet_name=_safe_sheet_name(label, used_names), index=False)
                wrote_any = True

    return output_path if wrote_any else None


class MetadataExtractor:
    """Reads a SOW (or other contract-like document) and extracts real project
    metadata - name, dates, budget, deliverables - instead of relying on a
    hand-authored metadata.json."""

    def __init__(self, model: str = "claude-sonnet-5"):
        self.client = anthropic.Anthropic()
        self.model = model

    def extract(self, sow_text: str) -> Dict:
        # Keys are intentionally flat (not nested) to match what
        # scripts/flatten.py's FlatteningEngine actually reads off metadata
        # (metadata['go_live_date'], metadata['timeline_status'],
        # metadata['budget_total'], metadata['budget_spent'], metadata['deliverables']).
        prompt = f"""You are a PMO analyst extracting project metadata from a Statement of Work (SOW).

Read the SOW below and extract real values into this JSON schema. Use null for anything not
stated in the document - do not guess or invent values.

{{
  "project_name": "string",
  "practice": "string (e.g. PMO, QMS, ITQC)",
  "client_name": "string or null",
  "status_date": "YYYY-MM-DD or null",
  "go_live_date": "date or null",
  "project_closure_date": "date or null (rarely stated in a SOW - leave null unless explicit)",
  "timeline_status": "ON_TRACK | AT_RISK | DELAYED | null",
  "deliverables": ["list of deliverables/services in scope"],
  "budget_total": "$X or null",
  "budget_spent": "$X or null (a SOW rarely states this - leave null unless explicit)",
  "contract_type": "fixed_fee | time_and_materials | null (per the SOW's fee/payment terms)",
  "hours_estimated": "number or null (total estimated/contracted hours, if the SOW states one)",
  "notes": "any other relevant context, 1-2 sentences"
}}

CRITICAL RULES:
1. ONLY return valid JSON, no explanation before or after.
2. Use null for unknown fields rather than guessing.
3. project_name should be the actual project/engagement name from the document.

SOW content:
{sow_text[:15000]}
"""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = next((b.text for b in response.content if b.type == "text"), None)
        if response_text is None:
            raise ValueError("No text content found in Claude response")

        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        extracted = json.loads(response_text[json_start:json_end])

        # flatten.py checks presence with `"key" in metadata` rather than truthiness
        # (e.g. metadata["budget_spent"].replace(...) guarded only by an "in" check),
        # so a present-but-null key crashes it. Drop nulls rather than keep them.
        return {k: v for k, v in extracted.items() if v is not None}


def prepare_pipeline_inputs(input_dir: str, staging_dir: str) -> Dict[str, Optional[str]]:
    """
    Normalize an arbitrary project folder into pipeline-ready inputs.

    Returns dict with keys: transcript (always set), metadata, excel (either may be None).
    """
    input_path = Path(input_dir)
    staging_path = Path(staging_dir)

    if not input_path.is_dir():
        raise ValueError(f"Input directory not found: {input_dir}")

    staging_path.mkdir(parents=True, exist_ok=True)

    print(f"\U0001f4c2 Preparing pipeline inputs from {input_path}...")

    # 1. Transcript: combine every text/markdown source
    text_files = discover_text_files(input_path)
    transcript_path = staging_path / "combined_transcript.txt"
    transcript_path.write_text(combine_text_sources(input_path), encoding="utf-8")
    print(f"   ✅ Combined {len(text_files)} text/markdown file(s) -> {transcript_path.name}")

    # 2. Excel: merge every CSV export and every workbook found into one
    #    combined spreadsheet (or pass a lone workbook through as-is)
    csv_files = discover_csv_files(input_path)
    workbook_files = discover_workbook_files(input_path)
    excel_path = combine_tabular_sources_to_excel(input_path, staging_path / "combined_data.xlsx")
    if excel_path and excel_path.parent == staging_path:
        print(f"   ✅ Merged {len(csv_files)} CSV file(s) and {len(workbook_files)} workbook(s) -> {excel_path.name}")
    elif excel_path:
        print(f"   ✅ Using project workbook -> {excel_path.name}")
    else:
        print(f"   ℹ️  No CSV or workbook files found - skipping Excel input")

    # 3. Metadata: extract real values from a SOW, if present
    metadata_path = None
    sow_file = find_sow_file(input_path)
    if sow_file:
        print(f"   \U0001f9e0 Extracting metadata from SOW: {sow_file.name}")
        metadata = MetadataExtractor().extract(extract_document_text(sow_file))
        metadata_path = staging_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"   ✅ Metadata extracted -> {metadata_path.name} (project: {metadata.get('project_name')})")
    else:
        print(f"   ℹ️  No SOW file found - metadata will be auto-generated")

    return {
        "transcript": str(transcript_path),
        "metadata": str(metadata_path) if metadata_path else None,
        "excel": str(excel_path) if excel_path else None,
    }
