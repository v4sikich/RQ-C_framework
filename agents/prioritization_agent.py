#!/usr/bin/env python3
"""
Prioritization Agent: Filters and ranks what goes on the status report slide.

Role: Content curator and decision-maker
Input: Structured JSON from Intake Agent (all KPIs)
Output: Prioritized JSON (only what fits on slide, ranked by importance)

Uses Claude Haiku (fast, lightweight) to make ranking decisions.
Removes low-confidence or redundant items.
Ensures top items are top priority.
"""

import json
from typing import Dict, List, Any, Optional
import anthropic


class PrioritizationAgent:
    """Filters and ranks KPIs for slide presentation using Claude Haiku."""

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        self.client = anthropic.Anthropic()
        self.model = model

    def build_prioritization_prompt(self, kpis: Dict[str, Any], practice: str = "PMO") -> str:
        """Build prompt for Claude Haiku to rank and filter KPIs."""
        prompt = f"""You are an expert PMO consultant who decides what matters most for a status report.

Current practice: {practice}
Your constraint: A status report slide can only fit:
- 1 executive summary (2-3 lines)
- 2-3 critical risks (if any)
- 3-5 upcoming milestones
- 2-3 completed deliverables
- 1 overall health status
- Recommendations

Given these KPIs from the project, filter and rank what goes on the slide.
Return ONLY valid JSON, no additional text.

Priority rules for {practice}:
- Timeline > Risks > Budget > Accomplishments
- Critical/High risks always included
- Only include risks if severity is high/critical OR impact is significant
- Only include upcoming items for next 30 days
- Use Red/Yellow/Green status to highlight health

Input KPIs:
{json.dumps(kpis, indent=2)}

Return this JSON structure:
{{
  "executive_summary": "1-sentence status, e.g., 'Project on track with one critical dependency'",
  "health_status_visual": "RED | YELLOW | GREEN",
  "risks_to_highlight": [
    {{
      "title": "risk title",
      "severity": "critical | high | medium",
      "why_it_matters": "why stakeholders care"
    }}
  ],
  "key_accomplishments": [
    "completed item 1",
    "completed item 2"
  ],
  "upcoming_focus": [
    {{
      "milestone": "what's happening",
      "due_date": "date if known",
      "owner": "who is responsible",
      "impact": "why it matters"
    }}
  ],
  "critical_blockers": ["blocker 1 if any"],
  "flagged_items": [
    {{
      "item": "something needing attention",
      "reason": "why flag it"
    }}
  ],
  "recommendations": ["what the project lead should do"],
  "confidence_level": "high | medium | low (overall data quality)"
}}

CRITICAL RULES:
1. ONLY return JSON. No explanation.
2. Be ruthless about filtering - only 3-5 risks max.
3. Only include blockers that are truly blocking progress.
4. For health_status: RED if critical risk, YELLOW if medium risk, GREEN otherwise.
5. Upcoming items should be concrete, not vague.
6. Keep text concise (1 sentence max per item).
7. If multiple risks have same impact, pick the one closest to happening.
"""
        return prompt

    def prioritize_kpis(self, kpis_json_path: str, practice: str = "PMO", output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Main orchestration: read KPIs, call Claude Haiku, return prioritized JSON.

        Args:
            kpis_json_path: Path to JSON output from Intake Agent
            practice: Practice name (PMO, QMS, ITQC, etc.) - affects priorities
            output_path: Optional path to save output

        Returns:
            Prioritized JSON with filtered KPIs
        """
        # Read input KPIs
        print(f"📖 Reading KPIs from {kpis_json_path}...")
        with open(kpis_json_path, 'r') as f:
            kpis = json.load(f)

        print(f"✅ Loaded KPIs for project: {kpis.get('project_name', 'Unknown')}")

        # Build prompt
        prompt = self.build_prioritization_prompt(kpis, practice)

        # Call Claude Haiku (lightweight ranking)
        print(f"🎯 Calling {self.model} for prioritization...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
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
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                prioritized = json.loads(json_str)
            else:
                prioritized = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON from Haiku response")
            print(f"Response:\n{response_text}")
            raise e

        # Add reference info
        prioritized['source_kpis'] = {
            'project_name': kpis.get('project_name'),
            'total_risks': len(kpis.get('risks', [])),
            'total_upcoming': len(kpis.get('deliverables', {}).get('upcoming', [])),
            'total_completed': len(kpis.get('deliverables', {}).get('completed', [])),
        }

        # Save if output path provided
        if output_path:
            with open(output_path, 'w') as f:
                json.dump(prioritized, f, indent=2)
            print(f"💾 Saved prioritized KPIs to {output_path}")

        # Print summary
        print(f"✅ Prioritization complete!")
        print(f"📊 Health: {prioritized.get('health_status_visual')}")
        print(f"⚠️ Risks to highlight: {len(prioritized.get('risks_to_highlight', []))}")
        print(f"✅ Key accomplishments: {len(prioritized.get('key_accomplishments', []))}")
        print(f"📅 Upcoming focus items: {len(prioritized.get('upcoming_focus', []))}")
        print(f"🚨 Critical blockers: {len(prioritized.get('critical_blockers', []))}")

        return prioritized


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prioritize KPIs for status report slide")
    parser.add_argument("--input", required=True, help="Path to intake_output.json from Intake Agent")
    parser.add_argument("--output", required=True, help="Output JSON file path")
    parser.add_argument("--practice", default="PMO", help="Practice (PMO, QMS, ITQC, etc.)")

    args = parser.parse_args()

    agent = PrioritizationAgent()
    prioritized = agent.prioritize_kpis(args.input, args.practice, args.output)

    print(f"\n✨ Prioritization ready for formatting agent")


if __name__ == "__main__":
    main()
