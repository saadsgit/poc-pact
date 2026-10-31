"""POC Pact Streamlit application."""

from __future__ import annotations

from collections import Counter, defaultdict

import streamlit as st

from poc_pact.ai import (
    AiServiceError,
    analyze_connection,
    generate_poc_pack,
    get_api_key,
)
from poc_pact.config import MAX_UPLOAD_BYTES, MODEL_ID, STATUSES
from poc_pact.database import (
    create_connection,
    get_connection,
    initialize_database,
    list_connections,
    save_outcome,
    save_poc_pack,
    update_status,
)
from poc_pact.demo import SAMPLE_NOTES, demo_connection, demo_poc_pack
from poc_pact.models import ConnectionDraft
from poc_pact.ui import (
    inject_styles,
    plan_as_markdown,
    render_brand,
    render_connection_summary,
    render_empty_state,
    render_how_cards,
    render_page_header,
    render_plan,
    render_section_header,
    render_status_rail,
    render_workflow_strip,
)

st.set_page_config(page_title="POC Pact", page_icon="🤝", layout="wide")
inject_styles()
initialize_database()

CONFIGURED_API_KEY = get_api_key()


def sidebar() -> tuple[str, str, str | None]:
    with st.sidebar:
        render_brand()
        st.markdown('<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True)
        nav_labels = {
            "Dashboard": "◫  Dashboard",
            "Capture connection": "＋  Capture connection",
            "Connection workspace": "◇  Connection workspace",
            "How it works": "◎  How it works",
        }
        page = st.radio(
            "Navigate",
            tuple(nav_labels),
            format_func=lambda value: nav_labels[value],
            label_visibility="collapsed",
        )
        st.divider()
        st.markdown('<div class="sidebar-label">AI connection</div>', unsafe_allow_html=True)
        active_api_key = CONFIGURED_API_KEY
        if not active_api_key:
            active_api_key = st.text_input(
                "Gemma API key",
                type="password",
                key="runtime_api_key",
                help="Kept only in this browser session; never saved by POC Pact.",
                placeholder="Paste a Google AI Studio key",
            ).strip() or None

        if active_api_key:
            mode = st.radio("Analysis mode", ("Gemma 4", "Demo simulation"), horizontal=True)
            if mode == "Gemma 4":
                source = "configured secret" if CONFIGURED_API_KEY else "session key"
                st.success(f"Connected · {MODEL_ID} · {source}")
            else:
                st.warning("Demo simulation is active")
        else:
            mode = "Demo simulation"
            st.warning("Demo mode · no API key found")
            st.caption("Paste a key above for this session, or configure Streamlit secrets.")
        st.divider()
        st.markdown(
            '<div class="privacy-note">🔒 Images are analyzed but not stored.<br>Only process material you have permission to use.</div>',
            unsafe_allow_html=True,
        )
    return page, mode, active_api_key


def dashboard_page() -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-inner">
            <div>
              <div class="eyebrow">ASEAN connection conversion</div>
              <h1>Turn warm intros into <span>real outcomes.</span></h1>
              <p>Capture the context while it is fresh. Shape a low-risk proof of concept. Track the connection all the way to measurable value.</p>
              <div class="hero-kicker"><span class="micro-chip">✦ Gemma 4 powered</span><span class="micro-chip">↗ Cross-border ready</span><span class="micro-chip">✓ Human reviewed</span></div>
            </div>
            <div class="hero-visual">
              <div class="orbit one"><span class="orbit-dot"></span></div>
              <div class="orbit two"><span class="orbit-dot"></span></div>
              <div class="hero-core">↗</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_workflow_strip()
    items = list_connections()
    total = len(items)
    active = sum(item["status"] in {"POC agreed", "POC running"} for item in items)
    proposed = sum(item["poc_plan"] is not None for item in items)
    outcomes = sum(bool(item["outcome_type"]) for item in items)

    cols = st.columns(4)
    cols[0].metric("Connections", total)
    cols[1].metric("POCs drafted", proposed)
    cols[2].metric("Active POCs", active)
    cols[3].metric("Outcomes", outcomes)

    if not items:
        render_empty_state()
        st.caption("Start from Capture connection in the left navigation. Demo mode works without an API key.")
        return

    left, right = st.columns([1.35, 1])
    with left:
        render_section_header("Connection pipeline", "Where every relationship stands")
        counts = Counter(item["status"] for item in items)
        chart_data = [
            {"Stage": status, "Connections": counts.get(status, 0)}
            for status in STATUSES
        ]
        st.bar_chart(
            chart_data,
            x="Stage",
            y="Connections",
            horizontal=True,
        )
    with right:
        render_section_header("Recorded value", "Grouped by currency")
        by_currency: dict[str, float] = defaultdict(float)
        for item in items:
            if item["estimated_value"]:
                by_currency[item["currency"]] += float(item["estimated_value"])
        if by_currency:
            for currency, value in sorted(by_currency.items()):
                st.metric(currency, f"{value:,.0f}")
        else:
            st.caption("No commercial value recorded yet. Value remains optional until a real outcome exists.")

    render_section_header("Recently updated", "Your latest connection activity")
    for item in items[:4]:
        render_connection_summary(item)
        st.write("")


def capture_page(mode: str, api_key: str | None) -> None:
    render_page_header(
        "Capture the spark",
        "What came out of the conversation?",
        "Add the scraps you left with. Gemma organizes the signal, and you approve every detail before it becomes a record.",
    )
    st.caption(f"Current analysis mode · {mode}")

    if st.button("Use the sample ASEAN meeting", type="secondary"):
        st.session_state["capture_notes"] = SAMPLE_NOTES
        st.session_state["capture_your_company"] = "ThermaTrack"
        st.session_state["capture_your_country"] = "Malaysia"
        st.session_state.pop("draft", None)

    left, right = st.columns([1.05, 1])
    with left:
        your_company = st.text_input("Your startup or organization", key="capture_your_company", placeholder="e.g. ThermaTrack")
        your_country = st.text_input("Your country", key="capture_your_country", placeholder="e.g. Malaysia")
        notes = st.text_area(
            "What happened in the conversation?",
            key="capture_notes",
            height=230,
            placeholder="Who did you meet? What problem did they mention? What did you agree to do next?",
            max_chars=5_000,
        )
    with right:
        uploaded = st.file_uploader(
            "Optional meeting evidence",
            type=("png", "jpg", "jpeg", "webp"),
            help="Business card, event badge, whiteboard, or conversation screenshot. Maximum 10 MB.",
        )
        if uploaded:
            st.image(uploaded, caption=uploaded.name, width=380)
        st.caption("Only upload information you are allowed to process. POC Pact does not save the image after analysis.")

    if st.button("Analyze connection", type="primary", use_container_width=True):
        if not notes.strip() and not uploaded:
            st.error("Add a note or an image first.")
        elif uploaded and uploaded.size > MAX_UPLOAD_BYTES:
            st.error("The image is larger than 10 MB.")
        else:
            with st.spinner("Turning the meeting into a structured opportunity…"):
                try:
                    if mode == "Gemma 4":
                        draft = analyze_connection(
                            notes=notes,
                            your_company=your_company,
                            your_country=your_country,
                            image_bytes=uploaded.getvalue() if uploaded else None,
                            mime_type=uploaded.type if uploaded else None,
                            api_key=api_key or "",
                        )
                        source_mode = MODEL_ID
                    else:
                        draft = demo_connection(your_company, your_country, notes)
                        source_mode = "Demo simulation"
                    st.session_state["draft"] = draft.to_dict()
                    st.session_state["draft_raw_notes"] = notes
                    st.session_state["draft_source_filename"] = uploaded.name if uploaded else ""
                    st.session_state["draft_source_mode"] = source_mode
                    for key, value in draft.to_dict().items():
                        if key != "confidence_notes":
                            st.session_state[f"review_{key}"] = value
                except AiServiceError as exc:
                    st.error(str(exc))
                    st.info("Your material was not saved. Check the key and try again, or switch to Demo simulation.")

    if "draft" in st.session_state:
        st.divider()
        render_section_header("Review the signal", "Nothing is saved until you approve it")
        st.caption("AI can misread names and companies. Correct every field that matters.")
        with st.form("review_connection"):
            a, b = st.columns(2)
            with a:
                contact_name = st.text_input("Contact name", key="review_contact_name")
                contact_role = st.text_input("Contact role", key="review_contact_role")
                contact_company = st.text_input("Contact company", key="review_contact_company")
                contact_country = st.text_input("Contact country", key="review_contact_country")
            with b:
                reviewed_your_company = st.text_input("Your company", key="review_your_company")
                reviewed_your_country = st.text_input("Your country", key="review_your_country")
                meeting_context = st.text_input("Where you connected", key="review_meeting_context")
                next_step = st.text_area("Recommended next step", key="review_next_step", height=95)
            collaboration_idea = st.text_area("Potential collaboration", key="review_collaboration_idea", height=110)
            save = st.form_submit_button("Save connection", type="primary", use_container_width=True)

        confidence_notes = st.session_state["draft"].get("confidence_notes", [])
        if confidence_notes:
            with st.expander("What needs confirmation"):
                for note in confidence_notes:
                    st.markdown(f"- {note}")

        if save:
            if not contact_company.strip() and not contact_name.strip():
                st.error("Add at least a contact name or company before saving.")
            else:
                reviewed = ConnectionDraft(
                    contact_name=contact_name.strip(),
                    contact_role=contact_role.strip(),
                    contact_company=contact_company.strip(),
                    contact_country=contact_country.strip(),
                    your_company=reviewed_your_company.strip(),
                    your_country=reviewed_your_country.strip(),
                    meeting_context=meeting_context.strip(),
                    collaboration_idea=collaboration_idea.strip(),
                    next_step=next_step.strip(),
                    confidence_notes=confidence_notes,
                )
                new_id = create_connection(
                    reviewed,
                    raw_notes=st.session_state.get("draft_raw_notes", ""),
                    source_filename=st.session_state.get("draft_source_filename", ""),
                    ai_mode=st.session_state.get("draft_source_mode", ""),
                )
                st.session_state.pop("draft", None)
                st.success(f"Connection #{new_id} saved. Open **Connection workspace** to create its POC pack.")


def workspace_page(mode: str, api_key: str | None) -> None:
    render_page_header(
        "Move it forward",
        "Connection workspace",
        "Turn context into a practical pilot, then keep the relationship moving toward an outcome.",
    )
    items = list_connections()
    if not items:
        st.info("Capture and save a connection first.")
        return

    labels = {
        item["id"]: f"#{item['id']} · {item['contact_company'] or item['contact_name'] or 'Unnamed'} · {item['status']}"
        for item in items
    }
    selected_id = st.selectbox("Choose a connection", list(labels), format_func=lambda value: labels[value])
    connection = get_connection(selected_id)
    if not connection:
        st.error("That connection could not be loaded.")
        return

    render_connection_summary(connection)
    render_status_rail(connection["status"], STATUSES)
    details, progress, outcome = st.tabs(("Context", "Move forward", "Record outcome"))
    with details:
        one, two = st.columns(2)
        with one:
            st.markdown("**Connection context**")
            st.write(connection["meeting_context"] or "Not recorded")
            st.markdown("**Initial next step**")
            st.write(connection["next_step"] or "Not recorded")
        with two:
            st.markdown("**Countries connected**")
            st.write(f"{connection['your_country'] or 'Unknown'} → {connection['contact_country'] or 'Unknown'}")
            st.markdown("**Processed with**")
            st.write(connection["ai_mode"] or "Not recorded")
        if connection["raw_notes"]:
            with st.expander("Original meeting note"):
                st.write(connection["raw_notes"])

    with progress:
        current_index = STATUSES.index(connection["status"]) if connection["status"] in STATUSES else 0
        new_status = st.selectbox("Current stage", STATUSES, index=current_index)
        if st.button("Update stage"):
            update_status(selected_id, new_status)
            st.success("Stage updated.")
            st.rerun()

    with outcome:
        outcome_options = ("", "POC launched", "Commercial partnership", "Investment", "Market expansion", "Cross-border sale", "Other")
        existing = connection["outcome_type"] if connection["outcome_type"] in outcome_options else ""
        selected_outcome = st.selectbox("Outcome", outcome_options, index=outcome_options.index(existing), format_func=lambda value: value or "No outcome yet")
        value_col, currency_col = st.columns([2, 1])
        with value_col:
            estimated_value = st.number_input("Estimated commercial value (optional)", min_value=0.0, value=float(connection["estimated_value"]), step=100.0)
        with currency_col:
            currency = st.selectbox("Currency", ("USD", "SGD", "MYR", "IDR", "THB", "VND", "PHP", "BND"), index=0 if connection["currency"] not in ("USD", "SGD", "MYR", "IDR", "THB", "VND", "PHP", "BND") else ("USD", "SGD", "MYR", "IDR", "THB", "VND", "PHP", "BND").index(connection["currency"]))
        if st.button("Save outcome"):
            save_outcome(selected_id, selected_outcome, estimated_value, currency)
            st.success("Outcome updated.")
            st.rerun()

    st.divider()
    render_section_header("POC pack", "A small test designed to earn the next yes")
    if not connection["poc_plan"]:
        st.write("Generate a narrow pilot plan and a message that makes the next step easy to accept.")
        if st.button("Generate POC pack", type="primary", use_container_width=True):
            with st.spinner("Scoping the smallest useful pilot…"):
                try:
                    if mode == "Gemma 4":
                        plan, message = generate_poc_pack(connection, api_key=api_key or "")
                        source_mode = MODEL_ID
                    else:
                        plan, message = demo_poc_pack(connection)
                        source_mode = "Demo simulation"
                    save_poc_pack(selected_id, plan, message, ai_mode=source_mode)
                    st.success("POC pack created.")
                    st.rerun()
                except AiServiceError as exc:
                    st.error(str(exc))
    else:
        render_plan(connection["poc_plan"])
        st.markdown("#### Draft follow-up message")
        st.text_area("Editable copy", connection["follow_up_message"], height=280, label_visibility="collapsed")
        st.download_button(
            "Download POC pack as Markdown",
            data=plan_as_markdown(connection),
            file_name=f"poc-pack-{selected_id}.md",
            mime="text/markdown",
            use_container_width=True,
        )


def how_it_works_page() -> None:
    render_page_header(
        "The conversion layer",
        "From handshake to outcome",
        "POC Pact closes the gap between meeting the right person and building something concrete together.",
    )
    render_how_cards()
    with st.container(border=True):
        st.markdown("#### Built for the challenge")
        st.write(
            "**Best Use of Gemma 4 · Problem statement 1**  \n"
            "Convert ASEAN ecosystem connections into measurable investments, partnerships, market expansion, and cross-border POCs."
        )

    render_section_header("Responsible by design", "Useful AI needs visible boundaries")
    responsibility_cols = st.columns(2)
    with responsibility_cols[0], st.container(border=True):
        st.markdown("**Human control**")
        st.markdown(
            "- Review extraction before saving\n"
            "- Edit every generated POC\n"
            "- Record outcomes manually"
        )
    with responsibility_cols[1], st.container(border=True):
        st.markdown("**Safe boundaries**")
        st.markdown(
            "- Get permission before uploading information\n"
            "- Treat plans as drafts, not legal advice\n"
            "- Verify all cross-border requirements"
        )

    render_section_header("Under the hood", "Small, understandable, and easy to extend")
    st.write(
        f"Streamlit for the experience · SQLite for local records · Google Gen AI SDK · `{MODEL_ID}` through the Gemini API"
    )


page, analysis_mode, active_api_key = sidebar()
if page == "Dashboard":
    dashboard_page()
elif page == "Capture connection":
    capture_page(analysis_mode, active_api_key)
elif page == "Connection workspace":
    workspace_page(analysis_mode, active_api_key)
else:
    how_it_works_page()
