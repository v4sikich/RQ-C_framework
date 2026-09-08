#!/usr/bin/env python3
"""
Review Gate: Generic human-in-the-loop approve/revise loop, shared by every
interactive checkpoint in the pipeline (Intake, Prioritization, Final Report).

The loop itself (show summary -> get decision -> revise -> show again) is
UI-agnostic: it's driven by small callables passed in by the caller, so the
exact same run_review_loop function works whether the "decision" comes from
a terminal input() prompt (cli_get_decision, used by run_pipeline.py
--interactive) or, later, from Streamlit button clicks. Only the decision
function needs to change per UI - the review/revise semantics stay identical.
"""

from typing import Any, Callable, Dict, List, Optional

# get_decision_fn(step_name, summary_lines, round_num) -> feedback string, or None if approved
DecisionFn = Callable[[str, List[str], int], Optional[str]]


def cli_get_decision(step_name: str, summary_lines: List[str], round_num: int) -> Optional[str]:
    """Plain terminal prompt: numbered summary, then Approve/Changes choice."""
    header = f"REVIEW: {step_name}" + (f" (revision {round_num})" if round_num else "")
    print(f"\n{'=' * 80}\n{header}\n{'=' * 80}")
    for i, line in enumerate(summary_lines, 1):
        print(f"{i}. {line}")

    while True:
        choice = input("\n[1] Approve   [2] Changes needed   > ").strip().lower()
        if choice in ("1", "a", "approve"):
            return None
        if choice in ("2", "c", "change", "changes"):
            feedback = input("What would you like changed? ").strip()
            if feedback:
                return feedback
            print("Feedback can't be empty - describe what should change, or choose Approve.")
        else:
            print("Please enter 1 to approve or 2 for changes.")


def run_review_loop(
    step_name: str,
    get_summary_fn: Callable[[], List[str]],
    revise_fn: Callable[[str], None],
    get_decision_fn: DecisionFn = cli_get_decision,
    max_rounds: int = 8,
) -> List[Dict[str, Any]]:
    """
    Show a step's output, let the reviewer approve or request changes, and
    keep revising until approved (or max_rounds is hit, to bound API cost if
    a reviewer and the model can't converge).

    Args:
        step_name: Human-readable label for this checkpoint (e.g. "Intake (KPI extraction)").
        get_summary_fn: Returns the current bullet-point summary of the step's output.
            Called fresh each round so it always reflects the latest revision.
        revise_fn: Given the reviewer's feedback text, mutates the underlying state
            (e.g. re-runs the agent's revise_* method and saves the new output) so the
            next get_summary_fn() call reflects the change.
        get_decision_fn: Returns reviewer feedback, or None to approve. Swappable per UI.
        max_rounds: Safety cap on revision rounds for one step.

    Returns:
        A list of {"round": n, "feedback": str} dicts - the revision history for this step.
    """
    history: List[Dict[str, Any]] = []
    round_num = 0

    while True:
        summary_lines = get_summary_fn()
        feedback = get_decision_fn(step_name, summary_lines, round_num)

        if feedback is None:
            print(f"✅ {step_name}: approved" + (f" after {round_num} revision(s)" if round_num else ""))
            return history

        history.append({"round": round_num + 1, "feedback": feedback})
        revise_fn(feedback)
        round_num += 1

        if round_num >= max_rounds:
            print(f"⚠️  Reached max revision rounds ({max_rounds}) for {step_name} - proceeding with latest version.")
            return history
