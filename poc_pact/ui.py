"""Reusable Streamlit presentation helpers."""

from collections.abc import Sequence
from typing import Any

import streamlit as st

CUSTOM_CSS = """
<style>
    :root {
        --ink: #f4fff9;
        --muted: #9db8ac;
        --line: rgba(167, 243, 208, 0.13);
        --panel: rgba(10, 30, 23, 0.78);
        --panel-strong: rgba(13, 39, 29, 0.94);
        --mint: #5ee9ad;
        --emerald: #14b87a;
        --lime: #c7f77f;
        --amber: #f8c56a;
    }

    html {scroll-behavior: smooth;}
    .stApp {
        background:
            radial-gradient(circle at 14% -8%, rgba(25, 195, 125, .17), transparent 30rem),
            radial-gradient(circle at 88% 15%, rgba(64, 145, 255, .09), transparent 26rem),
            linear-gradient(160deg, #06110d 0%, #071812 50%, #050d0a 100%);
    }
    .stApp::before {
        content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .22;
        background-image: linear-gradient(rgba(255,255,255,.022) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255,255,255,.022) 1px, transparent 1px);
        background-size: 44px 44px;
        mask-image: linear-gradient(to bottom, black, transparent 75%);
    }
    [data-testid="stHeader"] {background: transparent;}
    [data-testid="stAppViewBlockContainer"] {
        max-width: 1180px; padding-top: 2.4rem; padding-bottom: 5rem;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(8, 27, 20, .98), rgba(5, 17, 13, .98));
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebarContent"] {padding: 1.2rem .75rem;}
    [data-testid="stSidebar"] hr {border-color: var(--line); margin: 1.1rem 0;}

    .brand {display:flex; align-items:center; gap:.78rem; padding:.45rem .35rem .9rem;}
    .brand-mark {
        width:2.65rem; height:2.65rem; display:grid; place-items:center; border-radius:.9rem;
        background: linear-gradient(145deg, var(--mint), var(--emerald)); color:#042116;
        font-weight:950; font-size:1.15rem; box-shadow:0 10px 30px rgba(20,184,122,.25);
    }
    .brand-name {font-weight:850; font-size:1.16rem; letter-spacing:-.02em; color:var(--ink);}
    .brand-tagline {font-size:.72rem; color:var(--muted); margin-top:.08rem;}
    .sidebar-label {font-size:.68rem; letter-spacing:.13em; text-transform:uppercase; color:#719587; font-weight:800; margin:.25rem .42rem .5rem;}
    .privacy-note {font-size:.72rem; line-height:1.5; color:#78988b; padding:.4rem .45rem;}

    [data-testid="stSidebar"] [data-testid="stRadio"] > div {gap:.28rem;}
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        padding:.58rem .68rem; border-radius:.72rem; transition:all .18s ease;
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:rgba(94,233,173,.07);}

    h1, h2, h3 {letter-spacing:-.035em;}
    h1 {font-weight:820 !important;}
    p {line-height:1.62;}

    .hero {
        position:relative; overflow:hidden; min-height:310px; padding:2.7rem 3rem;
        border:1px solid rgba(94,233,173,.23); border-radius:28px;
        background:linear-gradient(135deg, rgba(15,58,42,.95), rgba(8,29,22,.88) 58%, rgba(8,42,31,.8));
        box-shadow:0 28px 80px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.04);
        margin-bottom:1.6rem;
    }
    .hero::after {
        content:""; position:absolute; width:380px; height:380px; border-radius:50%; right:-120px; top:-150px;
        background:radial-gradient(circle, rgba(94,233,173,.2), transparent 66%); filter:blur(2px);
    }
    .hero-inner {display:grid; grid-template-columns:minmax(0,1.45fr) minmax(250px,.75fr); align-items:center; gap:2rem; position:relative; z-index:1;}
    .eyebrow {display:flex; align-items:center; gap:.5rem; color:#89f5c4; font-size:.72rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase;}
    .eyebrow::before {content:""; width:1.6rem; height:1px; background:#89f5c4;}
    .hero h1 {font-size:clamp(2.5rem,5.2vw,4.35rem); line-height:.98; margin:.75rem 0 1rem; max-width:700px;}
    .hero h1 span {color:var(--mint);}
    .hero p {font-size:1.06rem; color:#bed8ce; max-width:650px; margin:0;}
    .hero-kicker {display:flex; gap:.55rem; flex-wrap:wrap; margin-top:1.45rem;}
    .micro-chip {padding:.38rem .64rem; border-radius:999px; border:1px solid rgba(167,243,208,.16); background:rgba(2,16,11,.28); color:#b9d5c9; font-size:.74rem;}
    .hero-visual {height:215px; position:relative; display:flex; align-items:center; justify-content:center;}
    .orbit {position:absolute; border:1px solid rgba(94,233,173,.16); border-radius:50%;}
    .orbit.one {width:190px;height:190px;animation:spin 18s linear infinite;}
    .orbit.two {width:132px;height:132px;animation:spin 12s linear infinite reverse;}
    .orbit-dot {position:absolute; width:11px;height:11px;border-radius:50%;background:var(--mint);box-shadow:0 0 18px var(--mint);top:-6px;left:50%;}
    .orbit.two .orbit-dot {background:#70a7ff;box-shadow:0 0 18px #70a7ff;}
    .hero-core {width:88px;height:88px;border-radius:25px;display:grid;place-items:center;background:linear-gradient(145deg,#6cf0b6,#16b77b);color:#052016;font-size:2rem;box-shadow:0 18px 45px rgba(21,184,123,.3);transform:rotate(-5deg);}
    @keyframes spin {to{transform:rotate(360deg)}}

    .page-heading {margin:.15rem 0 1.7rem;}
    .page-heading .eyebrow {margin-bottom:.6rem;}
    .page-heading h1 {font-size:clamp(2rem,4.5vw,3.35rem); margin:.15rem 0 .55rem;}
    .page-heading p {color:var(--muted); max-width:720px; margin:0; font-size:1.02rem;}

    div[data-testid="stMetric"] {
        min-height:126px; padding:1.12rem 1.2rem; border-radius:18px;
        background:linear-gradient(145deg, rgba(16,46,35,.9), rgba(8,26,19,.88));
        border:1px solid var(--line); box-shadow:0 14px 35px rgba(0,0,0,.13);
        transition:transform .18s ease, border-color .18s ease;
    }
    div[data-testid="stMetric"]:hover {transform:translateY(-2px);border-color:rgba(94,233,173,.32);}
    div[data-testid="stMetricLabel"] {color:#91b4a6;}
    div[data-testid="stMetricValue"] {color:var(--ink); font-weight:830; letter-spacing:-.04em;}

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color:var(--line) !important; border-radius:20px !important;
        background:linear-gradient(145deg,rgba(12,35,27,.78),rgba(6,21,16,.72));
        box-shadow:0 16px 45px rgba(0,0,0,.12);
    }
    [data-testid="stTextInputRootElement"], [data-testid="stTextAreaRootElement"], [data-baseweb="select"] > div {
        background:rgba(4,18,13,.72) !important; border-color:rgba(167,243,208,.15) !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        min-height:205px; border:1px dashed rgba(94,233,173,.35); border-radius:18px;
        background:linear-gradient(145deg,rgba(20,184,122,.055),rgba(8,25,19,.6));
    }
    [data-testid="stFileUploaderDropzone"]:hover {border-color:var(--mint);background:rgba(20,184,122,.09);}

    .stButton > button, .stDownloadButton > button {
        border-radius:11px; font-weight:760; min-height:2.75rem; transition:all .18s ease;
        border-color:rgba(167,243,208,.18);
    }
    .stButton > button[kind="primary"] {
        color:#032015; background:linear-gradient(135deg,#71f2bd,#21c98a); border:0;
        box-shadow:0 10px 28px rgba(20,184,122,.22);
    }
    .stButton > button:hover, .stDownloadButton > button:hover {transform:translateY(-1px);border-color:var(--mint);}
    .stButton > button[kind="primary"]:hover {box-shadow:0 14px 34px rgba(20,184,122,.32);color:#02160f;}

    [data-testid="stTabs"] [data-baseweb="tab-list"] {gap:.35rem; background:rgba(5,20,15,.55);padding:.32rem;border-radius:13px;}
    [data-testid="stTabs"] [data-baseweb="tab"] {border-radius:9px;padding:.48rem .9rem;}
    [data-testid="stTabs"] [aria-selected="true"] {background:rgba(94,233,173,.1);}

    .section-row {display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:2rem 0 .9rem;}
    .section-row h2 {font-size:1.42rem;margin:0;}
    .section-row p {font-size:.82rem;color:var(--muted);margin:0;}
    .soft-card {
        position:relative; overflow:hidden; display:grid; grid-template-columns:auto 1fr auto; gap:1rem; align-items:center;
        padding:1.15rem 1.25rem; border:1px solid var(--line); border-radius:18px;
        background:linear-gradient(135deg,rgba(15,45,34,.86),rgba(7,24,18,.78));
        box-shadow:0 12px 36px rgba(0,0,0,.1); transition:all .18s ease;
    }
    .soft-card::before {content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:linear-gradient(var(--mint),var(--emerald));}
    .soft-card:hover {transform:translateY(-2px);border-color:rgba(94,233,173,.28);}
    .contact-avatar {width:3rem;height:3rem;border-radius:14px;display:grid;place-items:center;background:rgba(94,233,173,.1);border:1px solid rgba(94,233,173,.18);color:var(--mint);font-weight:850;}
    .contact-name {font-size:1.02rem;font-weight:800;color:var(--ink);margin:0 0 .1rem;}
    .contact-meta {color:#8ead9f;font-size:.79rem;}
    .contact-idea {color:#c3d9d0;font-size:.86rem;margin:.5rem 0 0;line-height:1.45;}
    .country-route {color:#94b7a9;font-size:.76rem;white-space:nowrap;}
    .status-pill {display:inline-block;padding:.28rem .62rem;border-radius:999px;background:rgba(94,233,173,.1);border:1px solid rgba(94,233,173,.15);color:#9cf4cb;font-size:.68rem;font-weight:780;white-space:nowrap;}
    .status-pill.outcome-recorded {background:rgba(199,247,127,.1);color:var(--lime);border-color:rgba(199,247,127,.2);}
    .status-pill.poc-running,.status-pill.poc-agreed {background:rgba(112,167,255,.1);color:#9ac0ff;border-color:rgba(112,167,255,.2);}

    .empty-state {text-align:center;padding:3rem 1.5rem;border:1px dashed rgba(94,233,173,.22);border-radius:22px;background:rgba(10,31,23,.46);}
    .empty-icon {width:4.2rem;height:4.2rem;margin:0 auto 1rem;border-radius:20px;display:grid;place-items:center;background:rgba(94,233,173,.09);color:var(--mint);font-size:1.8rem;border:1px solid rgba(94,233,173,.16);}
    .empty-state h3 {margin:.2rem 0 .45rem;}
    .empty-state p {color:var(--muted);max-width:520px;margin:0 auto;}

    .workflow-strip {display:grid;grid-template-columns:repeat(4,1fr);gap:.75rem;margin:1rem 0 1.7rem;}
    .workflow-item {padding:.9rem;border-radius:15px;border:1px solid var(--line);background:rgba(8,28,20,.58);}
    .workflow-index {color:var(--mint);font-size:.68rem;font-weight:850;letter-spacing:.1em;}
    .workflow-name {font-weight:750;font-size:.86rem;margin-top:.2rem;}

    .status-rail {display:grid;grid-template-columns:repeat(8,1fr);gap:.25rem;margin:1.1rem 0 1.5rem;}
    .rail-step {position:relative;text-align:center;padding-top:1.9rem;color:#638477;font-size:.64rem;line-height:1.25;}
    .rail-step::before {content:"";position:absolute;top:.65rem;left:0;right:0;height:2px;background:#16342a;}
    .rail-step:first-child::before {left:50%;}.rail-step:last-child::before {right:50%;}
    .rail-dot {position:absolute;z-index:1;top:.33rem;left:calc(50% - .34rem);width:.68rem;height:.68rem;border-radius:50%;background:#24483b;border:2px solid #0b2119;}
    .rail-step.done {color:#83b7a2}.rail-step.done::before {background:#1a9d6a}.rail-step.done .rail-dot {background:var(--mint);box-shadow:0 0 12px rgba(94,233,173,.35);}
    .rail-step.current {color:var(--ink);font-weight:780}.rail-step.current .rail-dot {transform:scale(1.35);background:var(--lime);}

    .poc-hero {padding:1.35rem 1.5rem;border:1px solid rgba(94,233,173,.2);border-radius:20px;background:linear-gradient(135deg,rgba(19,64,46,.72),rgba(8,28,21,.66));margin:.7rem 0 1.2rem;}
    .poc-hero .poc-label {font-size:.68rem;color:var(--mint);font-weight:850;letter-spacing:.13em;text-transform:uppercase;}
    .poc-hero h2 {font-size:1.75rem;margin:.35rem 0 0;}
    .insight-card {height:100%;padding:1.05rem 1.1rem;border:1px solid var(--line);border-radius:16px;background:rgba(8,27,20,.6);}
    .insight-label {color:#7aa08f;font-size:.68rem;font-weight:820;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.45rem;}
    .insight-card p {color:#d0e2da;margin:0;font-size:.9rem;}
    .milestone {display:grid;grid-template-columns:95px 1fr;gap:.8rem;padding:.72rem 0;border-bottom:1px solid rgba(167,243,208,.08);}
    .milestone:last-child {border-bottom:0}.milestone-when {color:var(--mint);font-size:.78rem;font-weight:800}.milestone-text {color:#c5dacf;font-size:.86rem;}
    .next-action {padding:1rem 1.15rem;border-radius:15px;background:linear-gradient(135deg,rgba(94,233,173,.12),rgba(20,184,122,.05));border:1px solid rgba(94,233,173,.18);color:#dffff1;margin:1rem 0;}
    .next-action b {color:var(--mint);}
    .legal-note {color:#a8aa96;font-size:.78rem;padding:.8rem 1rem;border-left:3px solid var(--amber);background:rgba(248,197,106,.055);border-radius:0 10px 10px 0;}

    .how-grid {display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem;margin:1.2rem 0 2rem;}
    .how-card {padding:1.2rem;border:1px solid var(--line);border-radius:17px;background:rgba(9,29,22,.62);}
    .how-number {font-size:.7rem;font-weight:900;color:var(--mint);letter-spacing:.12em;}
    .how-card h3 {font-size:1rem;margin:.5rem 0 .35rem;}.how-card p {font-size:.8rem;color:var(--muted);margin:0;line-height:1.5;}

    @media (max-width: 800px) {
        [data-testid="stAppViewBlockContainer"] {padding-top:1.2rem;}
        .hero {padding:2rem 1.4rem;min-height:auto}.hero-inner {grid-template-columns:1fr}.hero-visual {display:none}
        .workflow-strip,.how-grid {grid-template-columns:1fr 1fr}.soft-card {grid-template-columns:auto 1fr}.soft-card > :last-child {grid-column:2}
        .status-rail {overflow-x:auto;grid-template-columns:repeat(8,85px);padding-bottom:.5rem}
    }
    @media (max-width: 480px) {.workflow-strip,.how-grid {grid-template-columns:1fr}.hero h1{font-size:2.35rem}}
</style>
"""


def inject_styles() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def render_brand() -> None:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-mark">P</div>
          <div><div class="brand-name">POC Pact</div><div class="brand-tagline">Connections → outcomes</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_header(eyebrow: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="page-heading">
          <div class="eyebrow">{_escape(eyebrow)}</div>
          <h1>{_escape(title)}</h1>
          <p>{_escape(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, note: str = "") -> None:
    st.markdown(
        f'<div class="section-row"><h2>{_escape(title)}</h2><p>{_escape(note)}</p></div>',
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <div class="empty-state">
          <div class="empty-icon">↗</div>
          <h3>Your next outcome starts with one conversation</h3>
          <p>Capture a meeting note, business card, or chat screenshot. POC Pact turns it into a concrete next step.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_workflow_strip() -> None:
    steps = (("01", "Capture"), ("02", "Clarify"), ("03", "Scope a POC"), ("04", "Track outcome"))
    cards = "".join(
        f'<div class="workflow-item"><div class="workflow-index">{number}</div><div class="workflow-name">{name}</div></div>'
        for number, name in steps
    )
    st.markdown(f'<div class="workflow-strip">{cards}</div>', unsafe_allow_html=True)


def render_status_rail(current_status: str, statuses: Sequence[str]) -> None:
    current_index = statuses.index(current_status) if current_status in statuses else 0
    rendered = []
    for index, status in enumerate(statuses):
        classes = ["rail-step"]
        if index <= current_index:
            classes.append("done")
        if index == current_index:
            classes.append("current")
        rendered.append(
            f'<div class="{" ".join(classes)}"><span class="rail-dot"></span>{_escape(status)}</div>'
        )
    st.markdown(f'<div class="status-rail">{"".join(rendered)}</div>', unsafe_allow_html=True)


def render_connection_summary(connection: dict[str, Any]) -> None:
    name = connection.get("contact_name") or "Unnamed contact"
    initials = "".join(part[0] for part in str(name).split()[:2]).upper() or "?"
    status = str(connection.get("status", "Captured"))
    status_class = status.lower().replace(" ", "-")
    route = f"{connection.get('your_country') or 'Unknown'} → {connection.get('contact_country') or 'Unknown'}"
    st.markdown(
        f"""
        <div class="soft-card">
          <div class="contact-avatar">{_escape(initials)}</div>
          <div>
            <div class="contact-name">{_escape(name)}</div>
            <div class="contact-meta">{_escape(connection.get('contact_role') or 'Role unknown')} · {_escape(connection.get('contact_company') or 'Company unknown')}</div>
            <div class="contact-idea">{_escape(connection.get('collaboration_idea') or 'No collaboration idea recorded.')}</div>
          </div>
          <div style="text-align:right"><span class="status-pill {status_class}">{_escape(status)}</span><div class="country-route" style="margin-top:.55rem">{_escape(route)}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_plan(plan: dict[str, Any]) -> None:
    st.markdown(
        f"""
        <div class="poc-hero"><div class="poc-label">Generated POC blueprint</div>
        <h2>{_escape(plan.get('title') or 'POC proposal')}</h2></div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns(2)
    with left:
        _insight_card("Problem to solve", plan.get("problem") or "Not specified")
    with right:
        _insight_card("Testable hypothesis", plan.get("hypothesis") or "Not specified")

    render_section_header("Pilot boundaries", f"Suggested duration · {plan.get('duration') or 'To be agreed'}")
    scope_col, out_col = st.columns(2)
    with scope_col, st.container(border=True):
        st.markdown("**✓ In scope**")
        _bullet_list(plan.get("scope", []))
    with out_col, st.container(border=True):
        st.markdown("**– Out of scope**")
        _bullet_list(plan.get("out_of_scope", []))

    render_section_header("Measures of success", "Agree these before the pilot begins")
    with st.container(border=True):
        _bullet_list(plan.get("success_metrics", []))

    render_section_header("Who does what", "Clear ownership prevents stalled pilots")
    owner_col, partner_col = st.columns(2)
    with owner_col, st.container(border=True):
        st.markdown("**Your team**")
        _bullet_list(plan.get("your_responsibilities", []))
    with partner_col, st.container(border=True):
        st.markdown("**Partner team**")
        _bullet_list(plan.get("partner_responsibilities", []))

    if plan.get("milestones"):
        render_section_header("Milestones", "A lightweight path to a decision")
        milestones = "".join(
            f'<div class="milestone"><div class="milestone-when">{_escape(item.get("when", ""))}</div><div class="milestone-text">{_escape(item.get("deliverable", ""))}</div></div>'
            for item in plan["milestones"]
        )
        st.markdown(f'<div class="insight-card">{milestones}</div>', unsafe_allow_html=True)

    render_section_header("Check before launch", "Questions, not legal conclusions")
    with st.container(border=True):
        _bullet_list(plan.get("risks_to_verify", []))
    st.markdown(
        f'<div class="next-action"><b>Next action</b><br>{_escape(plan.get("immediate_next_step") or "Agree on the next action.")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="legal-note">AI-generated starting point. Both parties must verify legal, regulatory, financial, and technical details before agreeing to a pilot.</div>',
        unsafe_allow_html=True,
    )


def render_how_cards() -> None:
    steps = (
        ("01", "Capture", "Add a meeting note, card, or screenshot."),
        ("02", "Clarify", "Gemma finds the people, context, and opportunity."),
        ("03", "Scope", "Turn the idea into a small measurable pilot."),
        ("04", "Convert", "Track progress through to a real outcome."),
    )
    cards = "".join(
        f'<div class="how-card"><div class="how-number">{number}</div><h3>{title}</h3><p>{body}</p></div>'
        for number, title, body in steps
    )
    st.markdown(f'<div class="how-grid">{cards}</div>', unsafe_allow_html=True)


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


def _insight_card(label: str, content: Any) -> None:
    st.markdown(
        f'<div class="insight-card"><div class="insight-label">{_escape(label)}</div><p>{_escape(content)}</p></div>',
        unsafe_allow_html=True,
    )


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
