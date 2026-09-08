#!/usr/bin/env python3
"""
Review Summaries: Deterministic, no-LLM-call bullet summaries of what each
pipeline step produced, for the human-in-the-loop review gates.

Kept deterministic (plain Python over the JSON, not another Claude call) so
what a reviewer sees always literally matches the underlying data - no risk
of a summary paraphrasing or subtly misrepresenting what was actually
extracted, and no extra API cost/latency per review round.

Shared by the CLI review loop (run_pipeline.py --interactive) and any future
UI (e.g. Streamlit) built on the same pipeline, so both present identical
information for the same decision.
"""

from typing import Any, Dict, List


def _fmt(value: Any, default: str = "Not specified") -> str:
    if value in (None, "", [], {}):
        return default
    return str(value)


def summarize_intake_kpis(kpis: Dict[str, Any]) -> List[str]:
    """One line per fact extracted by the Intake Agent."""
    lines: List[str] = []

    lines.append(f"Project: {_fmt(kpis.get('project_name'))} ({_fmt(kpis.get('practice'))})")
    lines.append(
        f"Status date: {_fmt(kpis.get('status_date'))} | "
        f"Closure: {_fmt(kpis.get('project_closure_date'), 'TBD')}"
    )
    lines.append(f"Overall health: {_fmt(kpis.get('health_status'), 'unknown').upper()}")

    timeline = kpis.get('timeline') or {}
    lines.append(
        f"Timeline: {_fmt(timeline.get('current_status'))} "
        f"(go-live: {_fmt(timeline.get('original_go_live'))}, "
        f"variance: {_fmt(timeline.get('days_variance'), '0')} days)"
    )

    status_by_dim = kpis.get('status_by_dimension') or {}
    dims = ", ".join(
        f"{dim.capitalize()}={_fmt(status_by_dim.get(dim), 'n/a')}"
        for dim in ("scope", "timeline", "resources", "budget")
    )
    lines.append(f"Status by dimension: {dims}")

    budget = kpis.get('budget') or {}
    lines.append(
        f"Budget: {_fmt(budget.get('total'))} total "
        f"({_fmt(budget.get('contract_type'), 'contract type unknown')}), "
        f"{_fmt(budget.get('hours_estimated'), 'hours n/a')} est hours"
    )

    risks = kpis.get('risks') or []
    lines.append(f"Risks found: {len(risks)}")
    for r in risks:
        lines.append(f"  - {r.get('title', 'Untitled risk')} ({_fmt(r.get('severity'), 'n/a')})")

    deliverables = kpis.get('deliverables') or {}
    completed = deliverables.get('completed') or []
    upcoming = deliverables.get('upcoming') or []
    lines.append(f"Deliverables: {len(completed)} completed, {len(upcoming)} upcoming")

    stakeholders = kpis.get('stakeholders') or []
    lines.append(f"Stakeholders identified: {len(stakeholders)}")
    for s in stakeholders:
        role = f" - {s['role']}" if s.get('role') else ""
        lines.append(f"  - {s.get('name', 'Unknown')}{role}")

    open_items = kpis.get('open_items') or []
    lines.append(f"Open action items: {len(open_items)}")

    takeaways = kpis.get('key_takeaways') or []
    if takeaways:
        lines.append("Key takeaways:")
        for t in takeaways:
            lines.append(f"  - {t}")

    return lines


def summarize_prioritized_kpis(prioritized: Dict[str, Any]) -> List[str]:
    """One line per decision made by the Prioritization Agent - what actually
    made the cut for the report, and how it's being framed."""
    lines: List[str] = []

    lines.append(f"Executive summary: {_fmt(prioritized.get('executive_summary'))}")
    lines.append(f"Health badge: {_fmt(prioritized.get('health_status_visual'))}")

    status_indicators = prioritized.get('status_indicators') or {}
    dims = ", ".join(
        f"{dim.capitalize()}={_fmt(status_indicators.get(dim), 'n/a')}"
        for dim in ("scope", "timeline", "resources", "budget")
    )
    lines.append(f"Status indicators: {dims}")

    metrics = prioritized.get('metrics') or {}
    lines.append(
        f"Metrics: {_fmt(metrics.get('contract_type'))}, "
        f"{_fmt(metrics.get('hours_estimated'), 'TBD')} est / "
        f"{_fmt(metrics.get('hours_consumed'), 'TBD')} consumed / "
        f"{_fmt(metrics.get('hours_remaining'), 'TBD')} remaining"
    )

    lines.append(
        f"Header dates: Updated {_fmt(prioritized.get('status_date'))} | "
        f"Go-Live {_fmt(prioritized.get('go_live_date'))} | "
        f"Closure {_fmt(prioritized.get('project_closure_date'), 'TBD')}"
    )

    risks = prioritized.get('risks_to_highlight') or []
    lines.append(f"Risks highlighted ({len(risks)}):")
    for r in risks:
        lines.append(f"  - {r.get('title', 'Untitled')} ({_fmt(r.get('severity'), 'n/a')}): {_fmt(r.get('why_it_matters'), '')}")

    blockers = prioritized.get('critical_blockers') or []
    if blockers:
        lines.append(f"Critical blockers ({len(blockers)}):")
        for b in blockers:
            lines.append(f"  - {b}")

    accomplishments = prioritized.get('key_accomplishments') or []
    lines.append(f"Key accomplishments ({len(accomplishments)}):")
    for a in accomplishments:
        lines.append(f"  - {a}")

    upcoming = prioritized.get('upcoming_focus') or []
    lines.append(f"Upcoming focus ({len(upcoming)}):")
    for u in upcoming:
        lines.append(
            f"  - {u.get('milestone', 'TBD')} "
            f"(due {_fmt(u.get('due_date'), 'TBD')}, owner {_fmt(u.get('owner'), 'unassigned')})"
        )

    stakeholders = prioritized.get('key_stakeholders') or []
    lines.append(f"Key stakeholders ({len(stakeholders)}):")
    for s in stakeholders:
        role = f" - {s['role']}" if s.get('role') else ""
        lines.append(f"  - {s.get('name', 'Unknown')}{role}")

    recommendations = prioritized.get('recommendations') or []
    if recommendations:
        lines.append(f"Recommendations ({len(recommendations)}):")
        for r in recommendations:
            lines.append(f"  - {r}")

    return lines
