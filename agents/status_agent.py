#!/usr/bin/env python3
"""
Status Report Agent: Formats prioritized KPIs into beautiful branded HTML report.

Role: Designer and presenter
Input: Prioritized JSON from Prioritization Agent
Output: Branded HTML report (Sikich colors, responsive, professional)

Uses Claude Sonnet to write compelling narrative + HTML structure.
Includes SVG visuals, collapsible sections, R/Y/G status indicators.
"""

import json
import re
from typing import Dict, Any, Optional
from pathlib import Path
import anthropic


class StatusReportAgent:
    """Generates beautiful HTML status reports using Claude Sonnet."""

    def __init__(self, model: str = "claude-sonnet-5"):
        self.client = anthropic.Anthropic()
        self.model = model

    def build_formatting_prompt(self, prioritized_kpis: Dict[str, Any]) -> str:
        """Build prompt for Claude Sonnet to generate HTML."""
        prompt = f"""You are an expert report designer and storyteller. Your task is to transform project data
into a beautiful, professional HTML status report that stakeholders love reading.

The report must:
1. Look professional (Sikich brand: navy, light blue, white)
2. Be mobile-responsive
3. Have collapsible sections
4. Use red/yellow/green status indicators
5. Tell the project story clearly
6. Be printable to PDF

Here's the project data to format:

{json.dumps(prioritized_kpis, indent=2)}

Return a complete, self-contained HTML page (no external CSS/JS).

Key sections to include:
1. Header: Project name + date + health status badge (+ project_closure_date if it is non-null;
   omit that line entirely if it's null - do not invent a closure date)
2. Executive Summary: 2-3 sentence overview
3. Status Indicators: four separate badges for Scope / Timeline / Resources / Budget, using the
   data.status_indicators object. For any dimension that is null, show a neutral "Not assessed"
   label instead of a color - do not guess a color for it.
4. Metrics: contract type (Fixed Fee / Time & Materials, from data.metrics.contract_type) and
   estimated/consumed/remaining hours or budget (from data.metrics). Show "TBD" for any null
   field in data.metrics - never calculate or guess a number that isn't explicitly provided.
5. Timeline: Current status vs. plan
6. Key Accomplishments: What shipped
7. Upcoming Focus: Next 30 days
8. Risks & Mitigations: What matters
9. Critical Blockers: What needs attention (if any)
10. Key Stakeholders: name + role for each entry in data.key_stakeholders. If that list is empty,
    omit this section entirely rather than inventing names or roles.
11. Next Steps/Recommendations: What to do

Style requirements:
- Sikich brand colors: #003366 (navy), #0099cc (light blue), #ffffff (white), #f5f5f5 (light gray)
- Use semantic HTML (no divitis)
- Include inline SVG for status badges (not fancy, simple colored circles)
- Collapsible sections use CSS only (no JavaScript required)
- Print-friendly (black text on white)
- Mobile: stack vertically, readable on phone
- Font: sans-serif, readable at small sizes

HTML Structure recommendations:
```html
<!DOCTYPE html>
<html>
<head>
  <meta name="viewport" content="width=device-width">
  <title>Project Status Report</title>
  <style>
    /* Include all CSS here - self-contained */
  </style>
</head>
<body>
  <!-- Header -->
  <!-- Executive Summary -->
  <!-- Status Indicators -->
  <!-- Timeline Section -->
  <!-- Accomplishments Section (collapsible) -->
  <!-- Upcoming Focus (collapsible) -->
  <!-- Risks (collapsible) -->
  <!-- Blockers (if any) -->
  <!-- Recommendations -->
  <!-- Footer -->
</body>
</html>
```

CRITICAL RULES:
1. Return ONLY the HTML. No explanation text before or after.
2. Make it beautiful - use whitespace, typography, colors effectively
3. Red = critical (health), Yellow = warning, Green = healthy
4. Say "Sikich" (no legal suffix like "LLC" or "LLP") in header/footer - the entity's exact legal
   form isn't part of the project data, so don't guess it.
5. Collapsible sections should start CLOSED to keep report scannable
6. Include "Generated on [date]" in footer, using data.status_date (or another explicit date
   field in the data) - do not invent a date that isn't in the provided data.
7. All CSS must be inline in <style> tag (no external files)
8. Make sure text has good contrast (dark text for readability)
9. Include subtle borders/dividers between sections
10. For R/Y/G indicator: use actual colors (red=#d32f2f, yellow=#fbc02d, green=#388e3c)
11. Use ONLY the data provided below. Do not invent dates, percentages, names, hours, or other
    figures that aren't present in the JSON. If a value is null or a list is empty, either show
    "TBD" or omit that line/section - never fabricate a plausible-sounding value to fill a gap.

Remember: This report will be sent to executives and clients. Make it look like Sikich knows what it's doing.
"""
        return prompt

    def generate_html_report(self, prioritized_json_path: str, output_html_path: str) -> str:
        """
        Main orchestration: read prioritized KPIs, call Claude, generate HTML.

        Args:
            prioritized_json_path: Path to prioritized_output.json
            output_html_path: Path to save generated HTML report

        Returns:
            Path to generated HTML file
        """
        # Read prioritized KPIs
        print(f"📖 Reading prioritized KPIs from {prioritized_json_path}...")
        with open(prioritized_json_path, 'r') as f:
            prioritized = json.load(f)

        project_name = prioritized.get('source_kpis', {}).get('project_name', 'Project Status Report')
        print(f"✅ Loaded: {project_name}")

        # Build formatting prompt
        prompt = self.build_formatting_prompt(prioritized)

        # Call Claude Sonnet
        print(f"🎨 Calling {self.model} for HTML generation...")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=20000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        # Extract HTML from response. Some models return a ThinkingBlock before
        # the TextBlock, so find the actual text block rather than assuming index 0.
        response_text = next((block.text for block in response.content if block.type == "text"), None)
        if response_text is None:
            raise ValueError("No text content found in Claude response")

        if response.stop_reason == "max_tokens":
            print(f"⚠️  Response was truncated (hit max_tokens=20000 limit) - HTML will likely be incomplete")

        # Find HTML content (it should start with <!DOCTYPE or <html)
        html_start = response_text.find('<!DOCTYPE')
        if html_start == -1:
            html_start = response_text.find('<html')
        if html_start == -1:
            html_start = response_text.find('<HTML')

        if html_start != -1:
            html_content = response_text[html_start:]
        else:
            # Fallback: assume entire response is HTML
            html_content = response_text

        # Basic validation
        if not html_content.strip().startswith('<'):
            print(f"❌ Response doesn't look like HTML")
            print(f"First 500 chars: {response_text[:500]}")
            raise ValueError("Claude didn't return valid HTML")

        # Save HTML
        output_path = Path(output_html_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"✅ HTML Report generated!")
        print(f"💾 Saved to {output_path}")

        # Print some stats
        line_count = len(html_content.split('\n'))
        size_kb = len(html_content.encode('utf-8')) / 1024

        print(f"📊 Report stats:")
        print(f"   - {line_count} lines of HTML")
        print(f"   - {size_kb:.1f} KB")
        print(f"   - Ready to view in browser")

        return str(output_path)

    def enhance_with_metadata(self, html_path: str, prioritized_json_path: str) -> None:
        """
        Optional: Enhance HTML with metadata comments.
        Adds JSON data as hidden comments for traceability.
        """
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            html = f.read()

        # Read JSON
        with open(prioritized_json_path, 'r') as f:
            json_data = json.load(f)

        # Create metadata comment
        metadata_comment = f"""<!--
Data Source Information:
Project: {json_data.get('source_kpis', {}).get('project_name', 'Unknown')}
Generated: {json_data.get('generated_date', 'Unknown')}
Data Quality: {json_data.get('confidence_level', 'Unknown')}

Original Metrics:
- Total Risks Found: {json_data.get('source_kpis', {}).get('total_risks', 0)}
- Total Completed Items: {json_data.get('source_kpis', {}).get('total_completed', 0)}
- Total Upcoming Items: {json_data.get('source_kpis', {}).get('total_upcoming', 0)}

Highlighted Items:
- Risks to Address: {len(json_data.get('risks_to_highlight', []))}
- Critical Blockers: {len(json_data.get('critical_blockers', []))}
- Recommendations: {len(json_data.get('recommendations', []))}
-->
"""

        # Insert after <body> tag
        html_with_metadata = html.replace('<body', f'<body{metadata_comment}', 1)

        # Save
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_with_metadata)

        print(f"✅ Enhanced HTML with metadata comments")


def main():
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description="Generate HTML status report from prioritized KPIs")
    parser.add_argument("--input", required=True, help="Path to prioritized_output.json")
    parser.add_argument("--output", required=True, help="Output HTML file path")
    parser.add_argument("--no-metadata", action="store_true", help="Skip metadata enhancement")

    args = parser.parse_args()

    agent = StatusReportAgent()
    html_path = agent.generate_html_report(args.input, args.output)

    if not args.no_metadata:
        agent.enhance_with_metadata(html_path, args.input)

    print(f"\n🌐 Report ready for viewing!")
    print(f"📄 Open in browser: file://{Path(html_path).absolute()}")


if __name__ == "__main__":
    main()
