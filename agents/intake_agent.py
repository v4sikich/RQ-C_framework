#!/usr/bin/env python3
"""
Intake Agent: Reads flattened markdown files and extracts structured KPIs.

Role: Information extraction specialist
Input: Flattened markdown files (meeting_summary.md, risks_issues.md, etc.)
Output: Structured JSON with all KPIs needed for status report

Uses Claude Sonnet (balanced cost/quality) to extract and normalize data.
Flags low-confidence items for human review.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import anthropic

# Schema for what the Intake Agent extracts
INTAKE_OUTPUT_SCHEMA = {
    "project_name": "string",
    "practice": "string",
    "status_date": "date",
    "project_closure_date": "date or null (only if a source explicitly states one)",
    "timeline": {
        "original_go_live": "date or string",
        "current_status": "on_track | at_risk | delayed | ahead",
        "days_variance": "integer (positive=ahead, negative=behind)",
        "key_dates": ["list of dates and milestones"],
    },
    "status_by_dimension": {
        "scope": "on_track | at_risk | delayed | ahead | null",
        "timeline": "on_track | at_risk | delayed | ahead | null",
        "resources": "on_track | at_risk | delayed | ahead | null",
        "budget": "on_track | at_risk | delayed | ahead | null",
    },
    "deliverables": {
        "completed": ["list of completed items"],
        "upcoming": ["list of upcoming milestones"],
        "value_delivered": "narrative summary of value",
    },
    "risks": [
        {
            "title": "string",
            "description": "string",
            "severity": "critical | high | medium | low",
            "mitigation": "string",
        }
    ],
    "budget": {
        "total": "string",
        "spent": "string",
        "percentage_used": "float (0-100)",
        "status": "on_budget | over_budget | under_budget",
        "contract_type": "fixed_fee | time_and_materials | null",
        "hours_estimated": "number or null",
        "hours_consumed": "number or null",
        "hours_remaining": "number or null",
    },
    "stakeholders": [
        {"name": "string", "role": "string or null", "organization": "client | sikich | vendor | null"}
    ],
    "open_items": ["list of action items with owners"],
    "raid_log": {
        "risks": ["list"],
        "assumptions": ["list"],
        "issues": ["list"],
        "decisions": ["list"],
    },
    "health_status": "red | yellow | green",
    "key_takeaways": ["top 3-5 insights"],
    "confidence_scores": {
        "timeline": "float (0-100)",
        "deliverables": "float (0-100)",
        "risks": "float (0-100)",
        "budget": "float (0-100)",
    },
}


class IntakeAgent:
    """Extracts structured data from flattened markdown files using Claude."""

    def __init__(self, model: str = "claude-sonnet-5"):
        self.client = anthropic.Anthropic()
        self.model = model

    def read_flattened_files(self, flattened_dir: str) -> Dict[str, str]:
        """Read all markdown files from flattened directory."""
        files = {}
        flattened_path = Path(flattened_dir)

        for md_file in flattened_path.glob("*.md"):
            section_name = md_file.stem
            with open(md_file, 'r', encoding='utf-8') as f:
                files[section_name] = f.read()

        return files

    def read_metadata(self, flattened_dir: str) -> Dict[str, Any]:
        """Read metadata.yaml for additional context."""
        metadata_path = Path(flattened_dir) / "metadata.yaml"
        metadata = {}

        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                # Simple YAML parsing (enough for our use case)
                content = f.read()
                metadata['raw'] = content

        return metadata

    def build_intake_prompt(self, flattened_files: Dict[str, str], project_metadata: Dict) -> str:
        """Build the prompt for Claude to extract KPIs."""
        prompt = """You are an expert project manager and data extraction specialist.

Your task: Extract all key project status information from the provided markdown files
and return it as structured JSON.

The JSON should follow this schema:
{
  "project_name": "string",
  "practice": "string",
  "status_date": "YYYY-MM-DD",
  "project_closure_date": "YYYY-MM-DD or null",
  "timeline": {
    "original_go_live": "date or description",
    "current_status": "on_track | at_risk | delayed | ahead",
    "days_variance": integer,
    "key_dates": ["milestone 1", "milestone 2"]
  },
  "status_by_dimension": {
    "scope": "on_track | at_risk | delayed | ahead | null",
    "timeline": "on_track | at_risk | delayed | ahead | null",
    "resources": "on_track | at_risk | delayed | ahead | null",
    "budget": "on_track | at_risk | delayed | ahead | null"
  },
  "deliverables": {
    "completed": ["item 1", "item 2"],
    "upcoming": ["item 1", "item 2"],
    "value_delivered": "summary of value delivered to date"
  },
  "risks": [
    {
      "title": "Risk Name",
      "description": "what could happen",
      "severity": "critical | high | medium | low",
      "mitigation": "what we're doing about it"
    }
  ],
  "budget": {
    "total": "$XXX,XXX",
    "spent": "$XXX,XXX",
    "percentage_used": 45.5,
    "status": "on_budget | over_budget | under_budget",
    "contract_type": "fixed_fee | time_and_materials | null",
    "hours_estimated": 400,
    "hours_consumed": null,
    "hours_remaining": null
  },
  "stakeholders": [
    {"name": "Full Name", "role": "title/role or null", "organization": "client | sikich | vendor | null"}
  ],
  "open_items": ["item with owner", "another item"],
  "raid_log": {
    "risks": [],
    "assumptions": [],
    "issues": [],
    "decisions": []
  },
  "health_status": "red | yellow | green",
  "key_takeaways": ["insight 1", "insight 2", "insight 3"],
  "confidence_scores": {
    "timeline": 85,
    "deliverables": 90,
    "risks": 75,
    "budget": 60
  }
}

CRITICAL RULES:
1. ONLY return valid JSON. No additional text before or after.
2. Be conservative with confidence scores. If info is unclear, mark <80%.
3. For missing data, use null instead of guessing. This applies especially to project_closure_date,
   status_by_dimension entries, contract_type, hours_estimated/consumed/remaining, and stakeholder
   roles/organizations - only fill these in when a source document states them explicitly.
4. Keep risk descriptions concise (1-2 sentences).
5. For health_status and status_by_dimension: if a source (especially a workbook/Excel table, e.g.
   an excel_data.md section) states an explicit status/RAG value for the project overall or for a
   specific dimension (scope/timeline/resources/budget), COPY THAT VALUE VERBATIM. Only infer a
   status from meeting-note sentiment when no explicit sourced status field exists for that
   dimension. Never let your own read of the narrative override an explicit sourced status field.
6. If timeline is "delayed", calculate days_variance as negative.
7. Extract budget percentages accurately: (spent / total) * 100.
8. For hours_estimated/hours_consumed/hours_remaining and contract_type: extract only if a source
   explicitly states the number/type (e.g. in the SOW or a workbook hours-tracking sheet). Do not
   calculate hours_remaining by subtracting unless both estimated and consumed are themselves
   explicitly sourced numbers - otherwise leave it null.
9. For stakeholders: list every named person you can find across all sources (meeting notes,
   decks, SOW signature blocks, workbook owner columns) with whatever role/organization is stated;
   use null for role/organization if not stated, but still include the name.

Here are the flattened markdown files:
"""
        for section, content in flattened_files.items():
            prompt += f"\n## {section}.md\n\n{content}\n"

        return prompt

    def _call_claude_for_json(self, prompt: str, max_tokens: int = 16384) -> Dict[str, Any]:
        """Send a prompt to Claude and parse a JSON object out of the response.
        Shared by extract_kpis and revise_kpis so both go through identical
        response-handling (thinking-block skip, truncation warning, JSON
        extraction) rather than duplicating that logic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        # Some models return a ThinkingBlock before the TextBlock, so find the
        # actual text block rather than assuming index 0.
        response_text = next((block.text for block in response.content if block.type == "text"), None)
        if response_text is None:
            raise ValueError("No text content found in Claude response")

        if response.stop_reason == "max_tokens":
            print(f"⚠️  Response was truncated (hit max_tokens={max_tokens} limit) - JSON parsing will likely fail")

        try:
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(response_text[json_start:json_end])
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from Claude response")
            print(f"Response:\n{response_text}")
            raise e

    def extract_kpis(self, flattened_dir: str, project_metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main orchestration: read flattened files, call Claude, return structured JSON.

        Args:
            flattened_dir: Directory containing flattened markdown files
            project_metadata: Optional project context (name, practice, etc.)

        Returns:
            Structured JSON with extracted KPIs
        """
        if project_metadata is None:
            project_metadata = {}

        print(f"📖 Reading flattened files from {flattened_dir}...")
        flattened_files = self.read_flattened_files(flattened_dir)
        metadata = self.read_metadata(flattened_dir)

        if not flattened_files:
            raise ValueError(f"No markdown files found in {flattened_dir}")

        print(f"✅ Found {len(flattened_files)} sections")

        prompt = self.build_intake_prompt(flattened_files, project_metadata)

        print(f"🧠 Calling {self.model} for KPI extraction...")
        kpis = self._call_claude_for_json(prompt)

        # Add metadata. The caller-provided project_name/practice are authoritative -
        # the model sometimes leaves these null if the transcript doesn't state them
        # explicitly, so fill them in rather than letting "None" flow downstream.
        if project_metadata:
            if project_metadata.get('project_name'):
                kpis['project_name'] = project_metadata['project_name']
            if project_metadata.get('practice'):
                kpis['practice'] = project_metadata['practice']
            kpis['metadata'] = project_metadata

        print(f"✅ Extraction complete!")
        print(f"📊 Health Status: {kpis.get('health_status', 'unknown').upper()}")
        print(f"📋 Risks Found: {len(kpis.get('risks', []))}")
        print(f"✅ Deliverables: {len(kpis.get('deliverables', {}).get('completed', []))} completed, "
              f"{len(kpis.get('deliverables', {}).get('upcoming', []))} upcoming")

        return kpis

    def revise_kpis(self, current_kpis: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Apply a human reviewer's requested change to already-extracted KPIs.

        This is a targeted patch, not a re-extraction: the model is shown the
        current JSON and told to change only what the feedback asks for,
        leaving every other field byte-for-byte the same. That keeps a
        reviewer's unrelated approved facts from drifting on each revision
        round.
        """
        prompt = f"""You are revising a project status KPI extraction based on human reviewer feedback.

Here is the CURRENT extracted JSON:
{json.dumps(current_kpis, indent=2)}

The reviewer's requested change:
"{feedback}"

CRITICAL RULES:
1. Apply ONLY the requested change. Do not alter, rephrase, reorder, or "improve" any field the
   reviewer did not ask about - copy those fields through completely unchanged.
2. Keep the exact same JSON schema/keys as the current JSON (add/remove list items as needed to
   satisfy the request, but don't introduce new top-level keys).
3. If the feedback asks for information that isn't derivable from what's already in this JSON
   (e.g. a fact never extracted from any source), use null / an honest placeholder rather than
   inventing a plausible-sounding value.
4. ONLY return the complete revised JSON. No explanation before or after.
"""
        print(f"🧠 Calling {self.model} to apply reviewer feedback...")
        revised = self._call_claude_for_json(prompt)
        print("✅ Revision applied.")
        return revised


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Extract KPIs from flattened markdown files")
    parser.add_argument("--flattened", required=True, help="Directory with flattened markdown files")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--project-name", default="Unknown Project", help="Project name")
    parser.add_argument("--practice", default="PMO", help="Practice (PMO, QMS, ITQC, etc.)")

    args = parser.parse_args()

    agent = IntakeAgent()
    project_metadata = {
        "project_name": args.project_name,
        "practice": args.practice,
    }

    kpis = agent.extract_kpis(args.flattened, project_metadata)

    # Save to file
    with open(args.output, 'w') as f:
        json.dump(kpis, f, indent=2)

    print(f"💾 Saved to {args.output}")


if __name__ == "__main__":
    main()
