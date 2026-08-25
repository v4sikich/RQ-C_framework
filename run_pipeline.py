#!/usr/bin/env python3
"""
Master Orchestration Script: Run the complete PMO status report pipeline.

Flow:
  1. Flatten: Transcript + Metadata → Markdown chunks
  2. Intake: Markdown chunks → Structured JSON (KPIs)
  3. Prioritization: Structured JSON → Prioritized JSON
  4. Status: Prioritized JSON → Beautiful HTML Report

Usage:
  python run_pipeline.py --transcript sample_data/sample_1_transcript.txt \
                          --metadata sample_data/sample_1_metadata.json \
                          --output output/Stephenson_Rife_Status_Aug5

Or with all defaults:
  python run_pipeline.py
"""

import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from flatten import FlatteningEngine
from intake_agent import IntakeAgent
from prioritization_agent import PrioritizationAgent
from status_agent import StatusReportAgent


class PipelineOrchestrator:
    """Runs the complete PMO status report generation pipeline."""

    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def run(self, transcript_path: str, metadata_path: str, project_name: str = "Project",
            practice: str = "PMO", output_name: str = None, excel_path: str = None,
            project_dir: str = None) -> dict:
        """
        Run complete pipeline: flatten → intake → prioritization → status report

        Args:
            transcript_path: Path to meeting transcript
            metadata_path: Path to metadata JSON
            project_name: Project name
            practice: Practice area (PMO, QMS, ITQC, etc)
            output_name: Custom output directory name
            excel_path: Optional path to Excel file (Smartsheet export, budget tracking, etc)
            project_dir: Optional path to projects/[project_name]/ folder for isolated workflow

        Returns:
            Dictionary with paths to all outputs
        """
        if project_dir:
            # Use project-specific workflow_execution folder
            output_dir = Path(project_dir) / "workflow_execution"
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fall back to root output folder
            if output_name is None:
                output_name = f"{project_name.replace(' ', '_')}_{self.timestamp}"
            output_dir = self.base_output_dir / output_name
            output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*80}")
        print(f"🚀 PMO Status Report Pipeline")
        print(f"{'='*80}")
        print(f"📌 Project: {project_name}")
        print(f"📌 Practice: {practice}")
        print(f"📌 Output: {output_dir}\n")

        results = {}

        try:
            # STEP 1: FLATTEN
            print(f"\n{'='*80}")
            print(f"STEP 1: Data Flattening")
            print(f"{'='*80}")
            flattened_dir = output_dir / "01_flattened"
            flattened_engine = FlatteningEngine(str(flattened_dir))
            flatten_result = flattened_engine.flatten(transcript_path, metadata_path, excel_path)
            results['flatten'] = flatten_result
            print(f"✅ Flattening complete: {len(flatten_result['files_created'])} files created")

            # STEP 2: INTAKE AGENT
            print(f"\n{'='*80}")
            print(f"STEP 2: Intake Agent (Extract KPIs)")
            print(f"{'='*80}")
            intake_output = output_dir / "02_intake_output.json"
            intake_agent = IntakeAgent()
            kpis = intake_agent.extract_kpis(
                str(flattened_dir),
                project_metadata={
                    "project_name": project_name,
                    "practice": practice,
                }
            )
            with open(intake_output, 'w') as f:
                json.dump(kpis, f, indent=2)
            results['intake'] = {
                'file': str(intake_output),
                'risks_found': len(kpis.get('risks', [])),
                'health_status': kpis.get('health_status'),
            }
            print(f"✅ Intake complete: saved to {intake_output.name}")

            # STEP 3: PRIORITIZATION AGENT
            print(f"\n{'='*80}")
            print(f"STEP 3: Prioritization Agent (Rank & Filter)")
            print(f"{'='*80}")
            prioritized_output = output_dir / "03_prioritized_output.json"
            prioritization_agent = PrioritizationAgent()
            prioritized = prioritization_agent.prioritize_kpis(
                str(intake_output),
                practice=practice,
                output_path=str(prioritized_output)
            )
            results['prioritization'] = {
                'file': str(prioritized_output),
                'risks_highlighted': len(prioritized.get('risks_to_highlight', [])),
                'health_status': prioritized.get('health_status_visual'),
            }
            print(f"✅ Prioritization complete: saved to {prioritized_output.name}")

            # STEP 4: STATUS REPORT AGENT
            print(f"\n{'='*80}")
            print(f"STEP 4: Status Report Agent (Generate HTML)")
            print(f"{'='*80}")
            html_output = output_dir / f"{project_name.replace(' ', '_')}_Status_Report.html"
            status_agent = StatusReportAgent()
            html_path = status_agent.generate_html_report(str(prioritized_output), str(html_output))
            results['status_report'] = {
                'file': html_path,
                'size_kb': len(open(html_path).read()) / 1024,
            }
            print(f"✅ HTML Report complete: saved to {Path(html_path).name}")

            # SUMMARY
            print(f"\n{'='*80}")
            print(f"✅ PIPELINE COMPLETE!")
            print(f"{'='*80}")
            print(f"\n📁 Output Directory: {output_dir}")
            print(f"\n📄 Generated Files:")
            print(f"   1️⃣  Flattened Data: {flattened_dir}/")
            print(f"   2️⃣  KPIs (JSON): {Path(results['intake']['file']).name}")
            print(f"   3️⃣  Prioritized (JSON): {Path(results['prioritization']['file']).name}")
            print(f"   4️⃣  HTML Report: {Path(results['status_report']['file']).name}")

            print(f"\n📊 Report Summary:")
            print(f"   • Health: {results['prioritization']['health_status']}")
            print(f"   • Risks Highlighted: {results['prioritization']['risks_highlighted']}")
            print(f"   • Report Size: {results['status_report']['size_kb']:.1f} KB")

            print(f"\n🌐 View Report:")
            print(f"   Open in browser: file://{Path(html_path).absolute()}")

            return results

        except Exception as e:
            print(f"\n❌ Pipeline failed at step!")
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Run complete PMO status report pipeline")
    parser.add_argument("--transcript", default="sample_data/sample_1_transcript.txt",
                        help="Meeting transcript file (TXT, VTT)")
    parser.add_argument("--metadata", default="sample_data/sample_1_metadata.json",
                        help="Project metadata JSON")
    parser.add_argument("--excel", help="Excel file (Smartsheet export, budget tracking, etc)")
    parser.add_argument("--project-name", default="Stephenson Rife Implementation",
                        help="Project name")
    parser.add_argument("--practice", default="PMO", help="Practice (PMO, QMS, ITQC, etc.)")
    parser.add_argument("--output-dir", default="output", help="Base output directory")
    parser.add_argument("--output-name", help="Specific output subdirectory name")
    parser.add_argument("--project-dir", help="Project folder (projects/[project_name]/) - results go to workflow_execution/")

    args = parser.parse_args()

    orchestrator = PipelineOrchestrator(args.output_dir)
    results = orchestrator.run(
        args.transcript,
        args.metadata,
        project_name=args.project_name,
        practice=args.practice,
        output_name=args.output_name,
        excel_path=args.excel,
        project_dir=args.project_dir,
    )

    if results:
        # Write pipeline summary
        summary = {
            "pipeline_run": datetime.now().isoformat(),
            "inputs": {
                "transcript": args.transcript,
                "metadata": args.metadata,
                "excel": args.excel,
            },
            "results": results,
        }
        summary_path = Path(args.output_dir) / "pipeline_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n✨ Pipeline Summary: {summary_path}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
