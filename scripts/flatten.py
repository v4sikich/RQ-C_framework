#!/usr/bin/env python3
"""
Flattening Script: Turns messy meeting transcripts + metadata into organized markdown chunks.

Input: Meeting transcript (VTT, TXT), SOW, Smartsheet snapshot, prior status slide
Output: Organized markdown files (~3-4 KB each) with confidence metadata

Each output file is a "knowledge chunk" that Claude agents can read independently.
Confidence scores flag low-confidence extracts for human review.
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


class FlatteningEngine:
    """Converts messy project data into structured markdown chunks."""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata = {
            "generated_at": datetime.now().isoformat(),
            "sources": [],
            "confidence_scores": {},
        }

    def extract_meeting_summary(self, transcript: str) -> Tuple[str, float]:
        """
        Extract high-level meeting summary from transcript.

        Returns: (markdown_content, confidence_score)
        Confidence: HIGH (>90%) if transcript has intro/agenda; MEDIUM otherwise
        """
        lines = transcript.split("\n")

        # Try to find intro section (usually first few lines or marked with "agenda")
        intro_section = []
        found_intro = False

        for i, line in enumerate(lines):
            if any(kw in line.lower() for kw in ["agenda", "topics", "meeting agenda", "discuss"]):
                found_intro = True
                # Grab next 10-15 lines as intro
                intro_section = lines[i:min(i+15, len(lines))]
                break

        if not found_intro:
            # Fallback: first 5 meaningful lines
            intro_section = [l for l in lines[:20] if l.strip() and len(l.strip()) > 10][:5]

        # Create markdown
        content = "# Meeting Summary\n\n"
        content += "## Key Topics Discussed\n\n"
        for line in intro_section:
            clean = line.strip()
            if clean:
                content += f"- {clean}\n"

        content += f"\n**Date**: {datetime.now().strftime('%Y-%m-%d')}\n"

        # Confidence: HIGH if we found explicit agenda markers
        confidence = 95.0 if found_intro else 70.0

        return content, confidence

    def extract_risks_and_issues(self, transcript: str) -> Tuple[str, float]:
        """
        Extract risks, blockers, and issues from transcript.

        Looks for keywords: "risk", "issue", "blocker", "problem", "risk is", "concern"
        """
        lines = transcript.split("\n")
        risks = []

        risk_keywords = ["risk", "blocker", "issue", "problem", "concern", "challenge", "blocked"]

        for line in lines:
            line_lower = line.lower()
            # Look for sentences containing risk keywords
            if any(kw in line_lower for kw in risk_keywords):
                # Skip if it's a label/header without context
                if len(line.strip()) > 15:
                    risks.append(line.strip())

        # Remove duplicates
        risks = list(set(risks))

        content = "# Risks & Issues\n\n"
        if risks:
            for risk in risks[:15]:  # Limit to top 15
                content += f"- {risk}\n"
            content += f"\n**Extracted {len(risks)} risks/issues from transcript**\n"
        else:
            content += "No explicit risks/issues mentioned.\n"

        # Confidence: MEDIUM if we found risk keywords; LOW otherwise
        confidence = 75.0 if risks else 45.0

        return content, confidence

    def extract_deliverables(self, transcript: str, metadata: Dict) -> Tuple[str, float]:
        """
        Extract completed work and upcoming deliverables.

        Looks for: "completed", "done", "finished", "upcoming", "next", "milestone"
        Also checks metadata for SOW deliverables.
        """
        lines = transcript.split("\n")
        completed = []
        upcoming = []

        completed_kw = ["completed", "done", "finished", "shipped", "approved", "signed off"]
        upcoming_kw = ["upcoming", "next", "coming", "scheduled", "planned", "will be"]

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in completed_kw):
                if len(line.strip()) > 10:
                    completed.append(line.strip())
            elif any(kw in line_lower for kw in upcoming_kw):
                if len(line.strip()) > 10:
                    upcoming.append(line.strip())

        # Remove duplicates
        completed = list(set(completed))
        upcoming = list(set(upcoming))

        content = "# Deliverables & Milestones\n\n"

        if completed:
            content += "## Completed/Delivered\n\n"
            for item in completed[:10]:
                content += f"- {item}\n"

        if upcoming:
            content += "\n## Upcoming Milestones\n\n"
            for item in upcoming[:10]:
                content += f"- {item}\n"

        # Check metadata for SOW deliverables
        if "deliverables" in metadata:
            content += "\n## From SOW\n\n"
            for d in metadata.get("deliverables", [])[:5]:
                content += f"- {d}\n"

        # Confidence: MEDIUM-HIGH if we found items in transcript; else LOW
        confidence = 80.0 if (completed or upcoming) else 50.0
        if "deliverables" in metadata:
            confidence = min(95.0, confidence + 10)

        return content, confidence

    def extract_timeline(self, transcript: str, metadata: Dict) -> Tuple[str, float]:
        """
        Extract timeline information: current status, blockers, go-live dates.
        """
        content = "# Timeline & Schedule\n\n"
        confidence = 50.0  # Timeline is often implicit

        # Try to find date references
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        dates = re.findall(date_pattern, transcript)

        if dates:
            content += "## Key Dates Mentioned\n\n"
            unique_dates = list(set(dates))
            for date in unique_dates[:5]:
                content += f"- {date}\n"
            confidence = 85.0

        # Timeline keywords
        timeline_kw = ["on schedule", "on track", "delayed", "behind", "ahead", "at risk"]
        for kw in timeline_kw:
            if kw.lower() in transcript.lower():
                content += f"\n**Status**: {kw.capitalize()}\n"
                confidence = max(confidence, 80.0)

        # From metadata
        if "go_live_date" in metadata:
            content += f"\n**Original Go-Live**: {metadata['go_live_date']}\n"
            confidence = min(99.0, confidence + 15)

        if "timeline_status" in metadata:
            content += f"**Current Status**: {metadata['timeline_status']}\n"
            confidence = min(99.0, confidence + 15)

        if "project_closure_date" in metadata:
            content += f"**Project Closure Date**: {metadata['project_closure_date']}\n"
            confidence = min(99.0, confidence + 15)

        return content, confidence

    def extract_excel_data(self, excel_path: str) -> Tuple[str, float]:
        """
        Extract data from Excel files (Smartsheet exports, budget tracking, timelines, etc).

        Supports multiple sheets and converts them to organized markdown.
        """
        if not PANDAS_AVAILABLE:
            return "# Excel Data\n\nPandas not installed. Run: pip install pandas openpyxl\n", 0.0

        try:
            excel_file = pd.ExcelFile(excel_path)
            content = "# Excel / Smartsheet Data\n\n"
            confidence_base = 85.0

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)

                if df.empty:
                    continue

                content += f"## {sheet_name}\n\n"

                # Convert dataframe to markdown table
                content += df.to_markdown(index=False)
                content += "\n\n"

                # Extract key metrics from common columns
                key_columns = ["Status", "Timeline", "Risk", "Budget", "Owner", "Priority"]
                found_columns = [col for col in key_columns if col in df.columns]

                if found_columns:
                    content += f"**Key Fields**: {', '.join(found_columns)}\n"
                    content += f"**Rows**: {len(df)}\n\n"

            return content, confidence_base

        except Exception as e:
            error_msg = f"# Excel Data\n\nError reading Excel file: {str(e)}\n"
            return error_msg, 30.0

    def extract_budget(self, transcript: str, metadata: Dict) -> Tuple[str, float]:
        """
        Extract budget info (only for T&M projects).
        """
        content = "# Budget & Spending\n\n"
        confidence = 40.0  # Budget is rarely discussed in transcripts

        # Look for numbers that might be budget-related
        num_pattern = r"\$?\d+(?:,\d{3})*(?:\.\d{2})?"
        numbers = re.findall(num_pattern, transcript)

        if numbers:
            content += "## Numbers Mentioned\n\n"
            unique_nums = list(set(numbers))[:5]
            for num in unique_nums:
                content += f"- {num}\n"

        # From metadata (more reliable source)
        if "budget_total" in metadata:
            content += f"\n**Total Budget**: {metadata['budget_total']}\n"
            confidence = 95.0

        if "budget_spent" in metadata:
            pct = (float(metadata["budget_spent"].replace("$", "").replace(",", "")) /
                   float(metadata.get("budget_total", "$1").replace("$", "").replace(",", ""))) * 100
            content += f"**Spent**: {metadata['budget_spent']} ({pct:.1f}%)\n"
            confidence = 95.0

        if "contract_type" in metadata:
            content += f"**Contract Type**: {metadata['contract_type']}\n"
            confidence = max(confidence, 90.0)

        if "hours_estimated" in metadata:
            content += f"**Estimated Hours**: {metadata['hours_estimated']}\n"
            confidence = max(confidence, 90.0)

        if confidence == 40.0:
            content += "\n*No budget information found. Add to metadata if available.*\n"

        return content, confidence

    def extract_metadata(self, metadata: Dict) -> str:
        """
        Create metadata file (YAML) with sources and confidence scores.
        """
        yaml_content = f"""# Data Sources & Confidence Metadata

generated_at: {datetime.now().isoformat()}
project_name: {metadata.get('project_name', 'Unknown')}
practice: {metadata.get('practice', 'PMO')}

sources:
  transcript: {metadata.get('transcript_source', 'meeting_transcript.vtt')}
  sow: {metadata.get('sow_source', 'SOW_document.pdf')}
  smartsheet: {metadata.get('smartsheet_source', 'Project tracking')}
  prior_status: {metadata.get('prior_status_source', 'previous_report.html')}

confidence_scores:
  meeting_summary: {self.metadata['confidence_scores'].get('meeting_summary', 0):.0f}%
  risks_issues: {self.metadata['confidence_scores'].get('risks_issues', 0):.0f}%
  deliverables: {self.metadata['confidence_scores'].get('deliverables', 0):.0f}%
  timeline: {self.metadata['confidence_scores'].get('timeline', 0):.0f}%
  budget: {self.metadata['confidence_scores'].get('budget', 0):.0f}%

notes:
  - Items with confidence <80% should be reviewed by human
  - Dates extracted via regex may need verification
  - Budget info from metadata is more reliable than transcript extraction
"""
        return yaml_content

    def flatten(self, transcript_path: str, metadata_path: Optional[str] = None, excel_path: Optional[str] = None) -> Dict:
        """
        Main flattening orchestration.

        Args:
            transcript_path: Path to meeting transcript (VTT, TXT)
            metadata_path: Path to metadata JSON
            excel_path: Path to Excel file (Smartsheet export, budget tracking, etc)

        Returns:
            Dictionary with file paths and confidence scores
        """
        # Read inputs
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript = f.read()

        metadata = {}
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

        # Extract all sections
        sections = {
            "meeting_summary": self.extract_meeting_summary(transcript),
            "risks_issues": self.extract_risks_and_issues(transcript),
            "deliverables": self.extract_deliverables(transcript, metadata),
            "timeline": self.extract_timeline(transcript, metadata),
            "budget": self.extract_budget(transcript, metadata),
        }

        # Add Excel data if provided
        if excel_path and os.path.exists(excel_path):
            sections["excel_data"] = self.extract_excel_data(excel_path)

        # Write markdown files
        output_files = {}
        for section_name, (content, confidence) in sections.items():
            filename = f"{section_name}.md"
            filepath = self.output_dir / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            output_files[section_name] = str(filepath)
            self.metadata['confidence_scores'][section_name] = confidence

        # Write metadata file
        metadata_content = self.extract_metadata(metadata)
        metadata_path = self.output_dir / "metadata.yaml"
        with open(metadata_path, 'w') as f:
            f.write(metadata_content)
        output_files['metadata'] = str(metadata_path)

        # Write summary
        summary = {
            "status": "success",
            "output_dir": str(self.output_dir),
            "files_created": output_files,
            "confidence_scores": self.metadata['confidence_scores'],
            "avg_confidence": sum(self.metadata['confidence_scores'].values()) / len(self.metadata['confidence_scores']),
        }

        print(f"\n✅ Flattening complete!")
        print(f"📁 Output: {self.output_dir}")
        print(f"📊 Average Confidence: {summary['avg_confidence']:.1f}%")
        print(f"📝 Files created:")
        for name, path in output_files.items():
            confidence = self.metadata['confidence_scores'].get(name, 0)
            print(f"   - {name}.md ({confidence:.0f}% confidence)")

        return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Flatten meeting data into markdown chunks")
    parser.add_argument("--transcript", required=True, help="Path to meeting transcript (VTT, TXT)")
    parser.add_argument("--metadata", help="Path to metadata JSON")
    parser.add_argument("--excel", help="Path to Excel file (Smartsheet export, budget tracking, etc)")
    parser.add_argument("--output", required=True, help="Output directory for flattened files")

    args = parser.parse_args()

    engine = FlatteningEngine(args.output)
    result = engine.flatten(args.transcript, args.metadata, args.excel)

    # Print summary
    print(f"\n📦 Summary:")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
