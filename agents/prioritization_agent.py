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
        # confidence_scores is internal pipeline data-quality metadata (how confident the
        # Intake Agent was about its own extraction), not a project fact. It has no
        # business being in a client-facing report, so it's dropped before the model
        # ever sees it rather than trusting a prompt instruction to filter it out later.
        kpis_for_prompt = {k: v for k, v in kpis.items() if k != "confidence_scores"}

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
{json.dumps(kpis_for_prompt, indent=2)}

Return this JSON structure:
{{
  "executive_summary": "1-sentence status, e.g., 'Project on track with one critical dependency'",
  "health_status_visual": "RED | YELLOW | GREEN",
  "status_indicators": {{
    "scope": "value copied from input status_by_dimension.scope, or null",
    "timeline": "value copied from input status_by_dimension.timeline, or null",
    "resources": "value copied from input status_by_dimension.resources, or null",
    "budget": "value copied from input status_by_dimension.budget, or null"
  }},
  "metrics": {{
    "contract_type": "copied from input budget.contract_type, or null",
    "hours_estimated": "copied from input budget.hours_estimated, or null",
    "hours_consumed": "copied from input budget.hours_consumed, or null",
    "hours_remaining": "copied from input budget.hours_remaining, or null",
    "budget_total": "copied from input budget.total, or null",
    "budget_spent": "copied from input budget.spent, or null"
  }},
  "key_stakeholders": [
    {{"name": "copied from input stakeholders[].name", "role": "copied from input stakeholders[].role, or null"}}
  ],
  "status_date": "copied from input status_date, or null",
  "go_live_date": "copied from input timeline.original_go_live, or null",
  "project_closure_date": "copied from input project_closure_date, or null",
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
4. For health_status: RED if critical risk, YELLOW if medium risk, GREEN otherwise - but if the
   input KPIs already contain an explicit sourced status (health_status or status_by_dimension),
   copy that value rather than recomputing your own from the risks list.
5. Upcoming items should be concrete, not vague.
6. Keep text concise (1 sentence max per item).
7. If multiple risks have same impact, pick the one closest to happening.
8. status_indicators, metrics, status_date, go_live_date, and project_closure_date must be copied
   directly from the matching input KPI fields - never compute, infer, or invent a value for
   these. If the input field is null, keep it null in your output; do not guess.
9. For key_stakeholders: the input's stakeholders list may contain every name mentioned anywhere
   in the source material. Narrow it to at most 7 genuinely key people for an executive report -
   prioritize named roles (project manager, technical/data lead, client-side decision makers,
   executive sponsors) over people who only appear once as an incidental task reference. Do not
   invent a stakeholder that isn't in the input list.
"""
        return prompt

    def _call_claude_for_json(self, prompt: str, max_tokens: int = 6144) -> Dict[str, Any]:
        """Send a prompt to Claude Haiku and parse a JSON object out of the
        response. Shared by prioritize_kpis and revise_prioritized so both go
        through identical response-handling rather than duplicating it."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

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
            print(f"❌ Failed to parse JSON from Haiku response")
            print(f"Response:\n{response_text}")
            raise e

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
        print(f"📖 Reading KPIs from {kpis_json_path}...")
        with open(kpis_json_path, 'r') as f:
            kpis = json.load(f)

        print(f"✅ Loaded KPIs for project: {kpis.get('project_name', 'Unknown')}")

        prompt = self.build_prioritization_prompt(kpis, practice)

        print(f"🎯 Calling {self.model} for prioritization...")
        prioritized = self._call_claude_for_json(prompt)

        prioritized['source_kpis'] = {
            'project_name': kpis.get('project_name'),
            'total_risks': len(kpis.get('risks', [])),
            'total_upcoming': len(kpis.get('deliverables', {}).get('upcoming', [])),
            'total_completed': len(kpis.get('deliverables', {}).get('completed', [])),
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(prioritized, f, indent=2)
            print(f"💾 Saved prioritized KPIs to {output_path}")

        print(f"✅ Prioritization complete!")
        print(f"📊 Health: {prioritized.get('health_status_visual')}")
        print(f"⚠️ Risks to highlight: {len(prioritized.get('risks_to_highlight', []))}")
        print(f"✅ Key accomplishments: {len(prioritized.get('key_accomplishments', []))}")
        print(f"📅 Upcoming focus items: {len(prioritized.get('upcoming_focus', []))}")
        print(f"🚨 Critical blockers: {len(prioritized.get('critical_blockers', []))}")

        return prioritized

    def revise_prioritized(self, current_prioritized: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """
        Apply a human reviewer's requested change to the already-prioritized
        slide content. Targeted patch, not a re-run: only the requested change
        is applied, everything else is carried through unchanged.
        """
        source_kpis = current_prioritized.get('source_kpis')
        current_for_prompt = {k: v for k, v in current_prioritized.items() if k != 'source_kpis'}

        prompt = f"""You are revising a prioritized project status report's content based on human
reviewer feedback.

Here is the CURRENT prioritized JSON:
{json.dumps(current_for_prompt, indent=2)}

The reviewer's requested change:
"{feedback}"

CRITICAL RULES:
1. Apply ONLY the requested change. Do not alter, rephrase, reorder, or "improve" any field the
   reviewer did not ask about - copy those fields through completely unchanged.
2. Keep the exact same JSON schema/keys as the current JSON (add/remove list items as needed to
   satisfy the request, but don't introduce new top-level keys).
3. If the feedback asks for information that isn't already present anywhere in this JSON, use
   null / an honest placeholder rather than inventing a plausible-sounding value.
4. ONLY return the complete revised JSON. No explanation before or after.
"""
        print(f"🎯 Calling {self.model} to apply reviewer feedback...")
        revised = self._call_claude_for_json(prompt)
        if source_kpis is not None:
            revised['source_kpis'] = source_kpis
        print("✅ Revision applied.")
        return revised


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
