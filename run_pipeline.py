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
from dotenv import load_dotenv

load_dotenv()

# Windows console defaults to cp1252, and a minimal Linux container can default
# to a non-UTF-8 (or even POSIX/C) locale - either way the emoji used in
# progress output below would crash the print. Force UTF-8 everywhere so this
# behaves the same on a dev machine, in Docker, or anywhere else.
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

# Add agents directory to path
sys.path.insert(0, str(Path(__file__).parent / "agents"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from flatten import FlatteningEngine
from intake_agent import IntakeAgent
from prioritization_agent import PrioritizationAgent
from status_agent import StatusReportAgent
from ppt_agent import PptxReportAgent
from input_adapter import prepare_pipeline_inputs
from review_gate import run_review_loop, cli_get_decision
from review_summaries import summarize_intake_kpis, summarize_prioritized_kpis


def _autodetect_input_dir(sample_data_dir: Path = Path("sample_data")) -> "str | None":
    """Fall back to the single project folder under sample_data/, if there is
    exactly one, so `python run_pipeline.py` works with no arguments no matter
    what real client folder has been dropped in there."""
    if not sample_data_dir.is_dir():
        return None
    subdirs = [p for p in sample_data_dir.iterdir() if p.is_dir()]
    return str(subdirs[0]) if len(subdirs) == 1 else None


class PipelineOrchestrator:
    """Runs the complete PMO status report generation pipeline."""

    def __init__(self, base_output_dir: str = "output"):
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def _create_default_metadata(self, output_dir: Path, project_name: str, practice: str) -> str:
        """Create minimal default metadata.json for pipeline to use."""
        metadata = {
            "project_name": project_name,
            "practice": practice,
            "status_date": datetime.now().strftime("%Y-%m-%d"),
            "note": "Auto-generated metadata - all KPIs extracted from transcript"
        }
        metadata_path = output_dir / "generated_metadata.json"
        metadata_path.parent.mkdir(parents=True, exist_ok=True)
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"ℹ️  No metadata provided - created auto-generated minimal metadata")
        return str(metadata_path)

    def run(self, transcript_path: str = None, metadata_path: str = None, project_name: str = None,
            practice: str = "PMO", output_name: str = None, excel_path: str = None,
            project_dir: str = None, input_dir: str = None, interactive: bool = False) -> dict:
        """
        Run complete pipeline: flatten → intake → prioritization → status report

        Args:
            transcript_path: Path to meeting transcript (required unless input_dir is given)
            metadata_path: Path to metadata JSON (optional - will be auto-generated if not provided)
            project_name: Project name (optional - inferred from a SOW via input_dir, or defaults to "Project")
            practice: Practice area (PMO, QMS, ITQC, etc)
            output_name: Custom output directory name
            excel_path: Optional path to Excel file (Smartsheet export, budget tracking, etc)
            project_dir: Optional path to projects/[project_name]/ folder for isolated workflow
            input_dir: Optional folder of arbitrary project files (meeting notes, SOW, CSV
                exports, in whatever naming/mix a real client hands over) - auto-adapted into
                transcript/metadata/excel inputs instead of requiring transcript_path directly
            interactive: If True, pause after Intake, Prioritization, and the Final Report for a
                human approve/request-changes checkpoint (via terminal prompts) before continuing.

        Returns:
            Dictionary with paths to all outputs
        """
        review_log: dict = {}
        if not transcript_path and not input_dir:
            raise ValueError("Must provide either transcript_path or input_dir")

        if project_dir:
            # Use project-specific workflow_execution folder
            output_dir = Path(project_dir) / "workflow_execution"
            output_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fall back to root output folder. Without an explicit project name yet
            # (it may still come from a SOW below), name the folder after the input
            # folder so it stays identifiable rather than the input's real name being
            # only apparent well after the fact.
            provisional_name = project_name or (Path(input_dir).name if input_dir else "Project")
            if output_name is None:
                output_name = f"{provisional_name.replace(' ', '_')}_{self.timestamp}"
            output_dir = self.base_output_dir / output_name
            output_dir.mkdir(parents=True, exist_ok=True)

        # If a folder of raw project files was given, adapt it into a single
        # transcript/metadata/excel triple before running the normal pipeline steps.
        if input_dir:
            prepared = prepare_pipeline_inputs(input_dir, str(output_dir / "00_prepared_input"))
            transcript_path = prepared["transcript"]
            excel_path = excel_path or prepared["excel"]
            if prepared["metadata"] and metadata_path is None:
                metadata_path = prepared["metadata"]
                if project_name is None:
                    with open(metadata_path) as f:
                        extracted_project_name = json.load(f).get("project_name")
                    if extracted_project_name:
                        project_name = extracted_project_name

        if project_name is None:
            project_name = "Project"

        # If still no metadata provided, create minimal default metadata
        if metadata_path is None:
            metadata_path = self._create_default_metadata(output_dir, project_name, practice)

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
            print(f"✅ Intake complete: saved to {intake_output.name}")

            if interactive:
                def _revise_intake(feedback: str) -> None:
                    nonlocal kpis
                    kpis = intake_agent.revise_kpis(kpis, feedback)
                    with open(intake_output, 'w') as f:
                        json.dump(kpis, f, indent=2)

                review_log['intake'] = run_review_loop(
                    "Intake (KPI extraction)",
                    get_summary_fn=lambda: summarize_intake_kpis(kpis),
                    revise_fn=_revise_intake,
                    get_decision_fn=cli_get_decision,
                )

            results['intake'] = {
                'file': str(intake_output),
                'risks_found': len(kpis.get('risks', [])),
                'health_status': kpis.get('health_status'),
            }

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
            print(f"✅ Prioritization complete: saved to {prioritized_output.name}")

            if interactive:
                def _revise_prioritized(feedback: str) -> None:
                    nonlocal prioritized
                    prioritized = prioritization_agent.revise_prioritized(prioritized, feedback)
                    with open(prioritized_output, 'w') as f:
                        json.dump(prioritized, f, indent=2)

                review_log['prioritization'] = run_review_loop(
                    "Prioritization (what goes on the report)",
                    get_summary_fn=lambda: summarize_prioritized_kpis(prioritized),
                    revise_fn=_revise_prioritized,
                    get_decision_fn=cli_get_decision,
                )

            results['prioritization'] = {
                'file': str(prioritized_output),
                'risks_highlighted': len(prioritized.get('risks_to_highlight', [])),
                'health_status': prioritized.get('health_status_visual'),
            }

            # STEP 4: STATUS REPORT AGENT
            print(f"\n{'='*80}")
            print(f"STEP 4: Status Report Agent (Generate HTML)")
            print(f"{'='*80}")
            html_output = output_dir / f"{project_name.replace(' ', '_')}_Status_Report.html"
            status_agent = StatusReportAgent()
            html_path = status_agent.generate_html_report(str(prioritized_output), str(html_output))
            print(f"✅ HTML Report complete: saved to {Path(html_path).name}")

            # STEP 5: PPTX REPORT AGENT
            print(f"\n{'='*80}")
            print(f"STEP 5: PPTX Report Agent (Generate PowerPoint slide)")
            print(f"{'='*80}")
            pptx_output = output_dir / f"{project_name.replace(' ', '_')}_Status_Report.pptx"
            ppt_agent = PptxReportAgent()
            pptx_path = ppt_agent.generate_pptx_report(str(prioritized_output), str(pptx_output))
            print(f"✅ PPTX Report complete: saved to {Path(pptx_path).name}")

            if interactive:
                def _revise_final_report(feedback: str) -> None:
                    nonlocal prioritized, html_path, pptx_path
                    # Feedback is applied to the underlying prioritized JSON (the single
                    # source of truth both artifacts render from), then both the HTML and
                    # PPTX are regenerated fresh from the patched JSON - simpler and more
                    # reliable than trying to patch already-rendered HTML/PPTX in place.
                    prioritized = prioritization_agent.revise_prioritized(prioritized, feedback)
                    with open(prioritized_output, 'w') as f:
                        json.dump(prioritized, f, indent=2)
                    html_path = status_agent.generate_html_report(str(prioritized_output), str(html_output))
                    pptx_path = ppt_agent.generate_pptx_report(str(prioritized_output), str(pptx_output))

                def _final_report_summary() -> list:
                    lines = [f"HTML report: {html_path}", f"PPTX report: {pptx_path}", ""]
                    lines += summarize_prioritized_kpis(prioritized)
                    return lines

                review_log['final_report'] = run_review_loop(
                    "Final Report (HTML + PPTX)",
                    get_summary_fn=_final_report_summary,
                    revise_fn=_revise_final_report,
                    get_decision_fn=cli_get_decision,
                )

            results['status_report'] = {
                'file': html_path,
                'size_kb': len(open(html_path, encoding='utf-8').read()) / 1024,
            }
            results['pptx_report'] = {
                'file': pptx_path,
                'size_kb': Path(pptx_path).stat().st_size / 1024,
            }

            if review_log:
                review_log_path = output_dir / "review_log.json"
                with open(review_log_path, 'w') as f:
                    json.dump(review_log, f, indent=2)
                print(f"\n📝 Review log saved to {review_log_path.name}")

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
            print(f"   5️⃣  PPTX Report: {Path(results['pptx_report']['file']).name}")

            print(f"\n📊 Report Summary:")
            print(f"   • Health: {results['prioritization']['health_status']}")
            print(f"   • Risks Highlighted: {results['prioritization']['risks_highlighted']}")
            print(f"   • Report Size: {results['status_report']['size_kb']:.1f} KB (HTML), {results['pptx_report']['size_kb']:.1f} KB (PPTX)")

            print(f"\n🌐 View Report:")
            print(f"   Open in browser: file://{Path(html_path).absolute()}")
            print(f"   Open PPTX: {Path(pptx_path).absolute()}")

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
    parser.add_argument("--transcript", default=None,
                        help="Meeting transcript file (TXT, VTT)")
    parser.add_argument("--input-dir", default=None,
                        help="Folder of arbitrary project files (meeting notes, SOW, CSV exports, "
                             "in whatever naming/mix a real client hands over) - auto-adapted into "
                             "transcript/metadata/excel inputs. Alternative to --transcript.")
    parser.add_argument("--metadata", default=None,
                        help="Project metadata JSON (optional - will be auto-generated, or extracted "
                             "from a SOW when using --input-dir, if not provided)")
    parser.add_argument("--excel", help="Excel file (Smartsheet export, budget tracking, etc)")
    parser.add_argument("--project-name", default=None,
                        help="Project name (optional - inferred from a SOW via --input-dir, else 'Project')")
    parser.add_argument("--practice", default="PMO", help="Practice (PMO, QMS, ITQC, etc.)")
    parser.add_argument("--output-dir", default="output", help="Base output directory")
    parser.add_argument("--output-name", help="Specific output subdirectory name")
    parser.add_argument("--project-dir", help="Project folder (projects/[project_name]/) - results go to workflow_execution/")
    parser.add_argument("--interactive", action="store_true",
                        help="Pause after Intake, Prioritization, and the Final Report for a human "
                             "approve/request-changes checkpoint (terminal prompts) before continuing.")

    args = parser.parse_args()

    input_dir = args.input_dir
    transcript = args.transcript
    if not input_dir and not transcript:
        input_dir = _autodetect_input_dir()
        if input_dir:
            print(f"ℹ️  No --transcript or --input-dir given - auto-detected input folder: {input_dir}")
        else:
            parser.error("No --transcript or --input-dir given, and no single folder could be "
                          "auto-detected under sample_data/. Specify one explicitly.")

    orchestrator = PipelineOrchestrator(args.output_dir)
    results = orchestrator.run(
        transcript,
        args.metadata,
        project_name=args.project_name,
        practice=args.practice,
        output_name=args.output_name,
        excel_path=args.excel,
        project_dir=args.project_dir,
        input_dir=input_dir,
        interactive=args.interactive,
    )

    if results:
        # Write pipeline summary
        summary = {
            "pipeline_run": datetime.now().isoformat(),
            "inputs": {
                "transcript": transcript,
                "input_dir": input_dir,
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
