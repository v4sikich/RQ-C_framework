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
    "timeline": {
        "original_go_live": "date or string",
        "current_status": "on_track | at_risk | delayed | ahead",
        "days_variance": "integer (positive=ahead, negative=behind)",
        "key_dates": ["list of dates and milestones"],
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
    },
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

    def __init__(self, model: str = "claude-sonnet-5-20250514"):
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
  "timeline": {
    "original_go_live": "date or description",
    "current_status": "on_track | at_risk | delayed | ahead",
    "days_variance": integer,
    "key_dates": ["milestone 1", "milestone 2"]
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
    "status": "on_budget | over_budget | under_budget"
  },
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
3. For missing data, use null instead of guessing.
4. Keep risk descriptions concise (1-2 sentences).
5. For health_status: GREEN = on track, YELLOW = minor risks, RED = critical risks.
6. If timeline is "delayed", calculate days_variance as negative.
7. Extract budget percentages accurately: (spent / total) * 100.

Here are the flattened markdown files:
"""
        for section, content in flattened_files.items():
            prompt += f"\n## {section}.md\n\n{content}\n"

        return prompt

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

        # Build prompt
        prompt = self.build_intake_prompt(flattened_files, project_metadata)

        # Call Claude
        print(f"🧠 Calling {self.model} for KPI extraction...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Extract JSON from response
        response_text = response.content[0].text

        # Parse JSON
        try:
            # Try to find JSON block if response has extra text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                kpis = json.loads(json_str)
            else:
                kpis = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from Claude response")
            print(f"Response:\n{response_text}")
            raise e

        # Add metadata
        if project_metadata:
            kpis['metadata'] = project_metadata

        print(f"✅ Extraction complete!")
        print(f"📊 Health Status: {kpis.get('health_status', 'unknown').upper()}")
        print(f"📋 Risks Found: {len(kpis.get('risks', []))}")
        print(f"✅ Deliverables: {len(kpis.get('deliverables', {}).get('completed', []))} completed, "
              f"{len(kpis.get('deliverables', {}).get('upcoming', []))} upcoming")

        return kpis


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
