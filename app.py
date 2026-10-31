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
from poc_pact.config import (
    CURRENCIES,
    MAX_UPLOAD_BYTES,
    MODEL_ID,
    OUTCOME_TYPES,
    STATUSES,
)
from poc_pact.database import (
    add_contact_from_draft,
    capture_connection,
    create_company,
    delete_company,
    delete_contact,
    find_company_by_name,
    get_company,
    get_contact,
    get_profile,
    initialize_database,
    list_companies,
    list_completed,
    save_contact_poc,
    save_outcome,
    save_profile,
    update_company_fields,
    update_contact_fields,
    update_stage,
)
from poc_pact.demo import SAMPLE_NOTES, demo_connection, demo_poc_pack
from poc_pact.models import ConnectionDraft
from poc_pact.ui import (
    inject_styles,
    plan_as_markdown,
    render_brand,
    render_email_actions,
    render_empty_state,
    render_how_cards,
    render_page_header,
    render_plan,
    render_section_header,
    render_stage_history,
    render_status_rail,
    render_workflow_strip,
    split_subject_body,
)

st.set_page_config(page_title="POC Pact", page_icon="🤝", layout="wide")
inject_styles()
initialize_database()

CONFIGURED_API_KEY = get_api_key()


def sidebar() -> tuple[str, str, str | None]:
    profile = get_profile()
    with st.sidebar:
        render_brand()
        st.markdown(
            '<div class="sidebar-label">Workspace</div>', unsafe_allow_html=True
        )
        nav_labels = {
            "Dashboard": "◫  Dashboard",
            "Capture connection": "＋  Capture connection",
            "Connections": "☰  Connections",
            "Connection workspace": "◇  Connection workspace",
            "Completed": "✓  Completed",
            "How it works": "◎  How it works",
        }
        page = st.radio(
            "Navigate",
            tuple(nav_labels),
            format_func=lambda value: nav_labels[value],
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown(
            '<div class="sidebar-label">Your organization</div>', unsafe_allow_html=True
        )
        with (
            st.expander("Profile", expanded=not profile["your_company"]),
            st.form("profile_form"),
        ):
            company = st.text_input(
                "Company / startup",
                value=profile["your_company"],
                placeholder="e.g. ThermaTrack",
            )
            country = st.text_input(
                "Country", value=profile["your_country"], placeholder="e.g. Malaysia"
            )
            if st.form_submit_button("Save profile", use_container_width=True):
                save_profile(company.strip(), country.strip())
                st.success("Saved. Used automatically on every new connection.")
                st.rerun()
        if profile["your_company"] or profile["your_country"]:
            st.caption(
                f"Acting as {profile['your_company'] or 'your company'}"
                f" · {profile['your_country'] or 'location not set'}"
            )

        st.divider()
        st.markdown(
            '<div class="sidebar-label">AI connection</div>', unsafe_allow_html=True
        )
        active_api_key = CONFIGURED_API_KEY
        if not active_api_key:
            active_api_key = (
                st.text_input(
                    "Gemma API key",
                    type="password",
                    key="runtime_api_key",
                    help="Kept only in this browser session; never saved by POC Pact.",
                    placeholder="Paste a Google AI Studio key",
                ).strip()
                or None
            )

        if active_api_key:
            mode = st.radio(
                "Analysis mode", ("Gemma 4", "Demo simulation"), horizontal=True
            )
            if mode == "Gemma 4":
                source = "configured secret" if CONFIGURED_API_KEY else "session key"
                st.success(f"Connected · {MODEL_ID} · {source}")
            else:
                st.warning("Demo simulation is active")
        else:
            mode = "Demo simulation"
            st.warning("Demo mode · no API key found")
            st.caption(
                "Paste a key above for this session, or configure Streamlit secrets."
            )
        st.divider()
        st.markdown(
            '<div class="privacy-note">🔒 Images are analyzed but not stored.<br>Only process material you have permission to use.</div>',
            unsafe_allow_html=True,
        )
    return page, mode, active_api_key


def _run_analysis(
    mode: str, api_key: str | None, notes: str, uploaded, profile: dict
) -> ConnectionDraft:
    if mode == "Gemma 4":
        draft = analyze_connection(
            notes=notes,
            your_company=profile["your_company"],
            your_country=profile["your_country"],
            image_bytes=uploaded.getvalue() if uploaded else None,
            mime_type=uploaded.type if uploaded else None,
            api_key=api_key or "",
        )
    else:
        draft = demo_connection(profile["your_company"], profile["your_country"], notes)
    draft.your_company = draft.your_company or profile["your_company"]
    draft.your_country = draft.your_country or profile["your_country"]
    return draft


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
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
    active = list_companies(include_closed=False)
    completed = list_completed()
    all_companies = active + completed
    contacts = sum(len(c["contacts"]) for c in all_companies)
    running = sum(c["status"] in {"POC agreed", "POC running"} for c in all_companies)

    cols = st.columns(4)
    cols[0].metric("Companies", len(all_companies))
    cols[1].metric("Contacts", contacts)
    cols[2].metric("Active POCs", running)
    cols[3].metric("Completed", len(completed))

    if not all_companies:
        render_empty_state()
        st.caption(
            "Start from Capture connection in the left navigation. Demo mode works without an API key."
        )
        return

    left, right = st.columns([1.35, 1])
    with left:
        render_section_header("Connection pipeline", "Where every relationship stands")
        counts = Counter(c["status"] for c in all_companies)
        chart_data = [{"Stage": s, "Companies": counts.get(s, 0)} for s in STATUSES]
        st.bar_chart(chart_data, x="Stage", y="Companies", horizontal=True)
    with right:
        render_section_header("Recorded value", "Grouped by currency")
        by_currency: dict[str, float] = defaultdict(float)
        for c in all_companies:
            if c["estimated_value"]:
                by_currency[c["currency"]] += float(c["estimated_value"])
        if by_currency:
            for currency, value in sorted(by_currency.items()):
                st.metric(currency, f"{value:,.0f}")
        else:
            st.caption(
                "No commercial value recorded yet. Value remains optional until a real outcome exists."
            )


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------
def capture_page(mode: str, api_key: str | None) -> None:
    render_page_header(
        "Capture connection",
        "Capture connection",
        "Add a meeting note or an image. Gemma structures the details, and you confirm them before anything is saved.",
    )
    profile = get_profile()
    st.caption(f"Current analysis mode · {mode}")

    if st.button("Use the sample ASEAN meeting", type="secondary"):
        st.session_state["capture_notes"] = SAMPLE_NOTES
        st.session_state.pop("draft", None)

    left, right = st.columns([1.05, 1])
    with left:
        if not profile["your_company"]:
            st.info(
                "Tip: set your company and country once in the sidebar profile so you never retype them."
            )
        notes = st.text_area(
            "Meeting notes",
            key="capture_notes",
            height=260,
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
        st.caption(
            "Only upload information you are allowed to process. POC Pact does not save the image after analysis."
        )

    if st.button("Analyze connection", type="primary", use_container_width=True):
        if not notes.strip() and not uploaded:
            st.error("Add a note or an image first.")
        elif uploaded and uploaded.size > MAX_UPLOAD_BYTES:
            st.error("The image is larger than 10 MB.")
        else:
            with st.spinner("Turning the meeting into a structured opportunity…"):
                try:
                    draft = _run_analysis(mode, api_key, notes, uploaded, profile)
                    source_mode = MODEL_ID if mode == "Gemma 4" else "Demo simulation"
                    st.session_state["draft"] = draft.to_dict()
                    st.session_state["draft_raw_notes"] = notes
                    st.session_state["draft_source_filename"] = (
                        uploaded.name if uploaded else ""
                    )
                    st.session_state["draft_source_mode"] = source_mode
                    for key, value in draft.to_dict().items():
                        if key != "confidence_notes":
                            st.session_state[f"review_{key}"] = value
                except AiServiceError as exc:
                    st.error(str(exc))
                    st.info(
                        "Your material was not saved. Check the key and try again, or switch to Demo simulation."
                    )

    if "draft" in st.session_state:
        st.divider()
        render_section_header(
            "Review the details", "Nothing is saved until you approve it"
        )
        st.caption(
            "AI can misread names and companies. Correct every field that matters; leave unknowns blank."
        )
        with st.form("review_connection"):
            a, b = st.columns(2)
            with a:
                contact_name = st.text_input("Contact name", key="review_contact_name")
                contact_role = st.text_input("Job position", key="review_contact_role")
                contact_company = st.text_input(
                    "Company name", key="review_contact_company"
                )
                contact_country = st.text_input(
                    "Company country", key="review_contact_country"
                )
                contact_email = st.text_input(
                    "Email address",
                    key="review_contact_email",
                    placeholder="Leave blank if unknown",
                )
            with b:
                meeting_context = st.text_input(
                    "Where you connected", key="review_meeting_context"
                )
                next_step = st.text_area(
                    "Recommended next step", key="review_next_step", height=95
                )
                collaboration_idea = st.text_area(
                    "Potential collaboration",
                    key="review_collaboration_idea",
                    height=120,
                )
            save = st.form_submit_button(
                "Save connection", type="primary", use_container_width=True
            )

        existing = find_company_by_name(
            st.session_state.get("review_contact_company", "")
        )
        if existing:
            st.info(
                f"'{existing['company_name']}' already exists — this contact will be added to it."
            )

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
                    contact_email=contact_email.strip(),
                    your_company=profile["your_company"],
                    your_country=profile["your_country"],
                    meeting_context=meeting_context.strip(),
                    collaboration_idea=collaboration_idea.strip(),
                    next_step=next_step.strip(),
                    confidence_notes=confidence_notes,
                )
                company_id, _ = capture_connection(
                    reviewed,
                    discussion=st.session_state.get("draft_raw_notes", ""),
                    raw_notes=st.session_state.get("draft_raw_notes", ""),
                    source_filename=st.session_state.get("draft_source_filename", ""),
                    ai_mode=st.session_state.get("draft_source_mode", ""),
                )
                st.session_state.pop("draft", None)
                st.success(
                    f"Saved to company #{company_id}. Open **Connection workspace** to generate a POC."
                )


# ---------------------------------------------------------------------------
# Connections (manage + search + delete)
# ---------------------------------------------------------------------------
def connections_page() -> None:
    render_page_header(
        "All connections",
        "Connections",
        "Every company you are pursuing and the people within it. Search, edit any detail, or remove entries.",
    )
    search = st.text_input(
        "Search by company or contact name", placeholder="Start typing…"
    )
    companies = list_companies(include_closed=False, search=search)
    if not companies:
        st.info(
            "No matching active connections."
            if search
            else "No connections saved yet. Capture one first."
        )
        return

    for company in companies:
        header = f"{company['company_name'] or 'Unnamed company'} · {len(company['contacts'])} contact(s) · {company['status']}"
        with st.expander(header):
            with st.form(f"company_{company['id']}"):
                cc1, cc2 = st.columns(2)
                with cc1:
                    cname = st.text_input(
                        "Company name",
                        value=company["company_name"],
                        key=f"cn_{company['id']}",
                    )
                with cc2:
                    ccountry = st.text_input(
                        "Company country",
                        value=company["company_country"],
                        key=f"cc_{company['id']}",
                    )
                if st.form_submit_button("Save company", use_container_width=True):
                    update_company_fields(
                        company["id"],
                        {
                            "company_name": cname.strip(),
                            "company_country": ccountry.strip(),
                        },
                    )
                    st.success("Company updated.")
                    st.rerun()

            st.markdown("**Contacts**")
            for contact in company["contacts"]:
                with st.form(f"contact_{contact['id']}"):
                    d1, d2 = st.columns(2)
                    with d1:
                        name = st.text_input(
                            "Contact name",
                            value=contact["contact_name"],
                            key=f"n_{contact['id']}",
                        )
                        role = st.text_input(
                            "Job position",
                            value=contact["contact_role"],
                            key=f"r_{contact['id']}",
                        )
                        email = st.text_input(
                            "Email address",
                            value=contact["contact_email"],
                            key=f"e_{contact['id']}",
                            placeholder="Leave blank if unknown",
                        )
                    with d2:
                        idea = st.text_area(
                            "Problem / POC focus",
                            value=contact["collaboration_idea"],
                            key=f"i_{contact['id']}",
                            height=100,
                        )
                        nxt = st.text_input(
                            "Next step",
                            value=contact["next_step"],
                            key=f"nx_{contact['id']}",
                        )
                    disc = st.text_area(
                        "Discussion notes",
                        value=contact["discussion"],
                        key=f"d_{contact['id']}",
                        height=90,
                    )
                    bcol1, bcol2 = st.columns([3, 1])
                    with bcol1:
                        saved = st.form_submit_button(
                            "Save contact", type="primary", use_container_width=True
                        )
                    with bcol2:
                        removed = st.form_submit_button(
                            "Delete contact", use_container_width=True
                        )
                    if saved:
                        update_contact_fields(
                            contact["id"],
                            {
                                "contact_name": name.strip(),
                                "contact_role": role.strip(),
                                "contact_email": email.strip(),
                                "collaboration_idea": idea.strip(),
                                "next_step": nxt.strip(),
                                "discussion": disc.strip(),
                            },
                        )
                        st.success("Contact updated.")
                        st.rerun()
                    if removed:
                        delete_contact(contact["id"])
                        st.warning("Contact deleted.")
                        st.rerun()

            st.divider()
            confirm = st.checkbox(
                "Confirm delete this whole company and all its contacts",
                key=f"confirm_{company['id']}",
            )
            if st.button(
                "Delete company", key=f"del_{company['id']}", disabled=not confirm
            ):
                delete_company(company["id"])
                st.warning("Company deleted.")
                st.rerun()


# ---------------------------------------------------------------------------
# Connection workspace (company -> contacts -> POC, stage, outcome, proposal)
# ---------------------------------------------------------------------------
def _render_contact_poc(
    company: dict, contact: dict, mode: str, api_key: str | None
) -> None:
    render_section_header(
        "POC pack", f"For {contact['contact_name'] or 'this contact'}"
    )
    if not contact["poc_plan"]:
        st.write(
            "Generate a narrow pilot plan and a follow-up message for this person."
        )
        if st.button(
            "Generate POC pack",
            type="primary",
            key=f"gen_{contact['id']}",
            use_container_width=True,
        ):
            with st.spinner("Scoping the smallest useful pilot…"):
                try:
                    evidence = {
                        "contact_name": contact["contact_name"],
                        "contact_role": contact["contact_role"],
                        "contact_company": company["company_name"],
                        "contact_country": company["company_country"],
                        "contact_email": contact["contact_email"],
                        "your_company": company["your_company"],
                        "your_country": company["your_country"],
                        "meeting_context": contact["meeting_context"],
                        "collaboration_idea": contact["collaboration_idea"],
                        "next_step": contact["next_step"],
                        "raw_notes": contact["discussion"] or contact["raw_notes"],
                    }
                    if mode == "Gemma 4":
                        plan, message = generate_poc_pack(
                            evidence, api_key=api_key or ""
                        )
                        source_mode = MODEL_ID
                    else:
                        plan, message = demo_poc_pack(evidence)
                        source_mode = "Demo simulation"
                    save_contact_poc(contact["id"], plan, message, ai_mode=source_mode)
                    st.success("POC pack created.")
                    st.rerun()
                except AiServiceError as exc:
                    st.error(str(exc))
    else:
        render_plan(contact["poc_plan"])
        render_section_header(
            "Draft follow-up message", "Edit, then send from your own email"
        )
        edited = st.text_area(
            "Editable copy",
            contact["follow_up_message"],
            height=260,
            key=f"follow_{contact['id']}",
            label_visibility="collapsed",
        )
        subject, body = split_subject_body(edited)
        render_email_actions(contact["contact_email"], subject, body)
        if not contact["contact_email"]:
            st.caption(
                "Add this contact's email on the Connections page to prefill the recipient."
            )
        merged = {
            "poc_plan": contact["poc_plan"],
            "your_company": company["your_company"],
            "company_name": company["company_name"],
            "follow_up_message": edited,
        }
        st.download_button(
            "Download POC pack as Markdown",
            data=plan_as_markdown(merged),
            file_name=f"poc-pack-{contact['id']}.md",
            mime="text/markdown",
            key=f"dl_{contact['id']}",
            use_container_width=True,
        )


def _render_submit_proposal(mode: str, api_key: str | None) -> None:
    render_section_header(
        "Submit a proposal", "Add a new company or contact with fresh context"
    )
    profile = get_profile()
    companies = list_companies(include_closed=False)
    options = {
        0: "➕ New company",
        **{c["id"]: c["company_name"] or "Unnamed" for c in companies},
    }
    with st.form("submit_proposal"):
        target = st.selectbox(
            "Company", list(options), format_func=lambda v: options[v]
        )
        new_company = st.text_input(
            "New company name (if adding)", placeholder="Only needed for a new company"
        )
        new_country = st.text_input("Company country", placeholder="e.g. Vietnam")
        person = st.text_input("Contact person name")
        role = st.text_input("Job position")
        email = st.text_input("Email address", placeholder="Leave blank if unknown")
        context = st.text_area(
            "New context / discussion",
            height=160,
            placeholder="What is the opportunity with this person?",
        )
        submitted = st.form_submit_button(
            "Analyze and add", type="primary", use_container_width=True
        )

    if submitted:
        if not context.strip():
            st.error("Add some context first.")
            return
        company_name = new_company.strip() if target == 0 else options[target]
        if not company_name:
            st.error("Provide a company name.")
            return
        with st.spinner("Analyzing and building a POC…"):
            try:
                draft = _run_analysis(mode, api_key, context, None, profile)
                draft.contact_company = company_name
                draft.contact_name = person.strip() or draft.contact_name
                draft.contact_role = role.strip() or draft.contact_role
                draft.contact_email = email.strip() or draft.contact_email
                draft.contact_country = new_country.strip() or draft.contact_country
                source_mode = MODEL_ID if mode == "Gemma 4" else "Demo simulation"

                if target == 0:
                    existing = find_company_by_name(company_name)
                    company_id = (
                        existing["id"]
                        if existing
                        else create_company(
                            company_name=company_name,
                            company_country=new_country.strip(),
                            your_company=profile["your_company"],
                            your_country=profile["your_country"],
                        )
                    )
                else:
                    company_id = target
                contact_id = add_contact_from_draft(
                    company_id,
                    draft,
                    discussion=context.strip(),
                    raw_notes=context.strip(),
                    source_filename="",
                    ai_mode=source_mode,
                )
                company = get_company(company_id)
                contact = get_contact(contact_id)
                evidence = {
                    "contact_name": contact["contact_name"],
                    "contact_role": contact["contact_role"],
                    "contact_company": company["company_name"],
                    "contact_country": company["company_country"],
                    "contact_email": contact["contact_email"],
                    "your_company": company["your_company"],
                    "your_country": company["your_country"],
                    "meeting_context": contact["meeting_context"],
                    "collaboration_idea": contact["collaboration_idea"],
                    "next_step": contact["next_step"],
                    "raw_notes": context.strip(),
                }
                if mode == "Gemma 4":
                    plan, message = generate_poc_pack(evidence, api_key=api_key or "")
                else:
                    plan, message = demo_poc_pack(evidence)
                save_contact_poc(contact_id, plan, message, ai_mode=source_mode)
                st.success(
                    f"Added to '{company_name}' with a POC pack. Select it above to view."
                )
            except AiServiceError as exc:
                st.error(str(exc))


def workspace_page(mode: str, api_key: str | None) -> None:
    render_page_header(
        "Move it forward",
        "Connection workspace",
        "Pick a company, work with each contact, and keep the relationship moving toward an outcome.",
    )
    companies = list_companies(include_closed=False)
    if companies:
        labels = {
            c["id"]: f"{c['company_name'] or 'Unnamed'} · {c['status']}"
            for c in companies
        }
        selected_id = st.selectbox(
            "Choose a company", list(labels), format_func=lambda v: labels[v]
        )
        company = get_company(selected_id)
        if company:
            render_status_rail(company["status"], STATUSES)
            manage, forward, outcome = st.tabs(
                ("Contacts & POCs", "Move forward", "Record outcome")
            )

            with manage:
                if not company["contacts"]:
                    st.info("No contacts yet. Use Submit a proposal below to add one.")
                contact_labels = {
                    c[
                        "id"
                    ]: f"{c['contact_name'] or 'Unnamed'} · {c['contact_role'] or 'role unknown'}"
                    for c in company["contacts"]
                }
                if contact_labels:
                    chosen = st.radio(
                        "Contact person",
                        list(contact_labels),
                        format_func=lambda v: contact_labels[v],
                        horizontal=True,
                    )
                    contact = get_contact(chosen)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.markdown("**Email**")
                        st.write(contact["contact_email"] or "Not recorded")
                    with cc2:
                        st.markdown("**Next step**")
                        st.write(contact["next_step"] or "Not recorded")
                    if contact["discussion"]:
                        with st.expander("Discussion notes"):
                            st.write(contact["discussion"])
                    st.divider()
                    _render_contact_poc(company, contact, mode, api_key)

            with forward:
                current_index = (
                    STATUSES.index(company["status"])
                    if company["status"] in STATUSES
                    else 0
                )
                new_status = st.selectbox(
                    "Current stage", STATUSES, index=current_index
                )
                st.caption(
                    "Setting the stage to Closed moves this company to the Completed archive."
                )
                if st.button("Update stage"):
                    update_stage(selected_id, new_status)
                    if new_status == "Closed":
                        st.success("Marked Closed and moved to Completed.")
                    else:
                        st.success("Stage updated.")
                    st.rerun()
                render_section_header("Stage history", "Each change is timestamped")
                render_stage_history(company["stage_history"])

            with outcome:
                existing = (
                    company["outcome_type"]
                    if company["outcome_type"] in OUTCOME_TYPES
                    else ""
                )
                selected_outcome = st.selectbox(
                    "Outcome",
                    OUTCOME_TYPES,
                    index=OUTCOME_TYPES.index(existing),
                    format_func=lambda value: value or "No outcome yet",
                )
                vcol, ccol = st.columns([2, 1])
                with vcol:
                    estimated_value = st.number_input(
                        "Estimated commercial value (optional)",
                        min_value=0.0,
                        value=float(company["estimated_value"]),
                        step=100.0,
                    )
                with ccol:
                    currency = st.selectbox(
                        "Currency",
                        CURRENCIES,
                        index=CURRENCIES.index(company["currency"])
                        if company["currency"] in CURRENCIES
                        else 0,
                    )
                if st.button("Save outcome"):
                    save_outcome(
                        selected_id, selected_outcome, estimated_value, currency
                    )
                    st.success("Outcome updated.")
                    st.rerun()
    else:
        st.info(
            "No active companies yet. Add one with Submit a proposal below, or capture a connection."
        )

    st.divider()
    _render_submit_proposal(mode, api_key)


# ---------------------------------------------------------------------------
# Completed archive
# ---------------------------------------------------------------------------
def completed_page() -> None:
    render_page_header(
        "Completed",
        "Completed connections",
        "Closed relationships with their full stage timeline and final outcome.",
    )
    companies = list_completed()
    if not companies:
        st.info("Nothing here yet. Set a company's stage to Closed to archive it.")
        return

    for company in companies:
        contacts = (
            ", ".join(
                c["contact_name"] for c in company["contacts"] if c["contact_name"]
            )
            or "No named contacts"
        )
        outcome = company["outcome_type"] or "No outcome recorded"
        value = (
            f" · {company['currency']} {company['estimated_value']:,.0f}"
            if company["estimated_value"]
            else ""
        )
        with st.expander(
            f"{company['company_name'] or 'Unnamed company'} · {outcome}{value}"
        ):
            st.markdown(f"**Contacts:** {contacts}")
            st.markdown(f"**Outcome:** {outcome}{value}")
            render_section_header("Stage timeline", "")
            render_stage_history(company["stage_history"])


def how_it_works_page() -> None:
    render_page_header(
        "The conversion layer",
        "From handshake to outcome",
        "POC Pact closes the gap between meeting the right person and building something concrete together.",
    )
    render_how_cards()
    render_section_header("Responsible by design", "Useful AI needs visible boundaries")
    responsibility_cols = st.columns(2)
    with responsibility_cols[0], st.container(border=True):
        st.markdown("**Human control**")
        st.markdown(
            "- Review extraction before saving\n- Edit every generated POC\n- Record outcomes manually"
        )
    with responsibility_cols[1], st.container(border=True):
        st.markdown("**Safe boundaries**")
        st.markdown(
            "- Get permission before uploading information\n- Treat plans as drafts, not legal advice\n- Verify all cross-border requirements"
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
elif page == "Connections":
    connections_page()
elif page == "Connection workspace":
    workspace_page(analysis_mode, active_api_key)
elif page == "Completed":
    completed_page()
else:
    how_it_works_page()
