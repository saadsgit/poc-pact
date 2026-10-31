"""Reusable Streamlit presentation helpers."""

from typing import Any

import streamlit as st

CUSTOM_CSS = """
<style>
    .block-container {max-width: 1120px; padding-top: 2.2rem; padding-bottom: 4rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(120,255,192,.12);}
    .hero {
        padding: 2rem 2.2rem; border: 1px solid rgba(52,211,153,.28);
        border-radius: 24px; background: linear-gradient(135deg, rgba(16,185,129,.16), rgba(6,78,59,.05));
        margin-bottom: 1.5rem;
    }
    .eyebrow {color: #6ee7b7; font-size: .78rem; font-weight: 800; letter-spacing: .12em; text-transform: uppercase;}
    .hero h1 {font-size: 3rem; line-height: 1.03; margin: .45rem 0 .8rem;}
    .hero p {font-size: 1.08rem; color: #cce7dc; max-width: 750px; margin: 0;}
    .soft-card {padding: 1rem 1.15rem; border: 1px solid rgba(148,163,184,.16); border-radius: 16px; background: rgba(15,39,30,.62);}
    .status-pill {display:inline-block; padding:.25rem .65rem; border-radius:999px; background:#164e3b; color:#a7f3d0; font-size:.78rem; font-weight:700;}
    .small-label {color:#8fb9a8; font-size:.76rem; text-transform:uppercase; letter-spacing:.08em; font-weight:700;}
    div[data-testid="stMetric"] {background: rgba(15,39,30,.72); border: 1px solid rgba(148,163,184,.15); padding: 1rem; border-radius: 16px;}
    .step-number {display:inline-flex; width:2rem; height:2rem; align-items:center; justify-content:center; border-radius:50%; background:#10b981; color:#03110b; font-weight:900; margin-right:.5rem;}
    .legal-note {color:#91aa9f; font-size:.82rem; padding:.8rem 1rem; border-left:3px solid #f59e0b; background:rgba(245,158,11,.07);}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_connection_summary(connection: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="soft-card">
          <span class="status-pill">{_escape(connection.get('status', 'Captured'))}</span>
          <h3 style="margin:.65rem 0 .2rem">{_escape(connection.get('contact_name') or 'Unnamed contact')}</h3>
          <div>{_escape(connection.get('contact_role') or 'Role unknown')} · {_escape(connection.get('contact_company') or 'Company unknown')}</div>
          <p style="color:#a9c7bb;margin:.7rem 0 0">{_escape(connection.get('collaboration_idea') or 'No collaboration idea recorded.')}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plan(plan: dict[str, Any]) -> None:
    st.subheader(plan.get("title") or "POC proposal")
    left, right = st.columns(2)
    with left:
        st.markdown("**Problem**")
        st.write(plan.get("problem") or "Not specified")
    with right:
        st.markdown("**Hypothesis**")
        st.write(plan.get("hypothesis") or "Not specified")

    st.markdown("#### Pilot boundaries")
    scope_col, out_col = st.columns(2)
    with scope_col:
        st.markdown("**In scope**")
        _bullet_list(plan.get("scope", []))
    with out_col:
        st.markdown("**Out of scope**")
        _bullet_list(plan.get("out_of_scope", []))

    st.markdown("#### How success will be measured")
    _bullet_list(plan.get("success_metrics", []))
    st.caption(f"Suggested duration: {plan.get('duration') or 'To be agreed'}")

    owner_col, partner_col = st.columns(2)
    with owner_col:
        st.markdown("**Your responsibilities**")
        _bullet_list(plan.get("your_responsibilities", []))
    with partner_col:
        st.markdown("**Partner responsibilities**")
        _bullet_list(plan.get("partner_responsibilities", []))

    if plan.get("milestones"):
        st.markdown("#### Milestones")
        for item in plan["milestones"]:
            st.markdown(f"**{item.get('when', '')}** — {item.get('deliverable', '')}")

    st.markdown("#### Risks and details to verify")
    _bullet_list(plan.get("risks_to_verify", []))
    st.info(f"Next action: {plan.get('immediate_next_step') or 'Agree on the next action.'}")
    st.markdown(
        '<div class="legal-note">AI-generated starting point. Both parties must verify legal, regulatory, financial, and technical details before agreeing to a pilot.</div>',
        unsafe_allow_html=True,
    )


def plan_as_markdown(connection: dict[str, Any]) -> str:
    plan = connection.get("poc_plan") or {}
    sections = [
        f"# {plan.get('title', 'POC proposal')}",
        f"**Parties:** {connection.get('your_company', '')} and {connection.get('contact_company', '')}",
        f"**Suggested duration:** {plan.get('duration', '')}",
        "## Problem",
        plan.get("problem", ""),
        "## Hypothesis",
        plan.get("hypothesis", ""),
        "## In scope",
        _markdown_list(plan.get("scope", [])),
        "## Out of scope",
        _markdown_list(plan.get("out_of_scope", [])),
        "## Success metrics",
        _markdown_list(plan.get("success_metrics", [])),
        "## Your responsibilities",
        _markdown_list(plan.get("your_responsibilities", [])),
        "## Partner responsibilities",
        _markdown_list(plan.get("partner_responsibilities", [])),
        "## Risks and details to verify",
        _markdown_list(plan.get("risks_to_verify", [])),
        "## Immediate next step",
        plan.get("immediate_next_step", ""),
        "## Draft follow-up",
        connection.get("follow_up_message", ""),
        "---\nAI-generated starting point. Verify all details before agreement.",
    ]
    return "\n\n".join(sections)


def _bullet_list(items: list[Any]) -> None:
    if not items:
        st.caption("Not specified")
        return
    for item in items:
        st.markdown(f"- {item}")


def _markdown_list(items: list[Any]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Not specified"


def _escape(value: Any) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
