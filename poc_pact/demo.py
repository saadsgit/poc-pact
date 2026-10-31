"""Transparent deterministic demo behavior used when no API key is configured."""

from __future__ import annotations

from poc_pact.models import ConnectionDraft, PocPlan

SAMPLE_NOTES = (
    "Met Siti Rahman, Head of Fleet Operations at Nusantara Fresh Logistics, "
    "during the ASEAN Innovation Mixer in Kuala Lumpur. They operate 120 "
    "refrigerated vehicles in Indonesia and lose visibility when shipments cross "
    "regional depots. Siti wants to test our live temperature alerts on 5 vehicles "
    "for routes between Jakarta and Bandung. We agreed I would send a short pilot "
    "proposal next week."
)


def demo_connection(
    your_company: str, your_country: str, notes: str
) -> ConnectionDraft:
    is_sample = "Siti Rahman" in notes or "Nusantara Fresh" in notes
    if is_sample:
        return ConnectionDraft(
            contact_name="Siti Rahman",
            contact_role="Head of Fleet Operations",
            contact_company="Nusantara Fresh Logistics",
            contact_country="Indonesia",
            contact_email="siti.rahman@nusantarafresh.example",
            your_company=your_company or "ThermaTrack",
            your_country=your_country or "Malaysia",
            meeting_context="ASEAN Innovation Mixer in Kuala Lumpur",
            collaboration_idea=(
                "Test live temperature alerts on five refrigerated vehicles operating "
                "between Jakarta and Bandung."
            ),
            next_step="Send Siti a one-page pilot proposal next week.",
            confidence_notes=[
                "The contact, fleet size, route, and next step came from the meeting note.",
                "Pilot budget and technical integration details were not provided.",
            ],
        )

    summary = (
        notes.strip()[:300]
        or "Potential collaboration discussed; add notes for more detail."
    )
    return ConnectionDraft(
        contact_name="Needs review",
        contact_role="Not provided",
        contact_company="Needs review",
        contact_country="Not provided",
        contact_email="",
        your_company=your_company,
        your_country=your_country,
        meeting_context="Captured from your notes",
        collaboration_idea=summary,
        next_step="Confirm the contact details and agree on one concrete next step.",
        confidence_notes=[
            "Demo mode does not analyze custom content. Connect Gemma 4 for real extraction."
        ],
    )


def demo_poc_pack(connection: dict) -> tuple[PocPlan, str]:
    partner = connection.get("contact_company") or "the partner"
    contact = connection.get("contact_name") or "there"
    yours = connection.get("your_company") or "our team"
    idea = connection.get("collaboration_idea") or "the proposed solution"

    plan = PocPlan(
        title=f"{yours} × {partner}: Small-scale validation pilot",
        problem=(
            "The partner lacks timely visibility into refrigerated shipment conditions, "
            "which delays intervention when temperatures move outside an acceptable range."
        ),
        hypothesis=(
            "If live alerts are introduced on five vehicles, the operations team can respond "
            "to temperature incidents before deliveries reach their destination."
        ),
        scope=[
            "Equip or connect five refrigerated vehicles.",
            "Monitor the Jakarta–Bandung route for four weeks.",
            "Send live alerts to a small operations team.",
            "Review incidents and response times each week.",
        ],
        out_of_scope=[
            "Fleet-wide rollout",
            "Long-term commercial pricing",
            "Automated insurance or compliance decisions",
        ],
        duration="4 weeks, plus 1 week for setup",
        success_metrics=[
            "At least 95% of planned journeys produce complete temperature records.",
            "Operations staff receive alerts within 2 minutes of a threshold breach.",
            "At least 80% of alerts are acknowledged within 10 minutes.",
        ],
        your_responsibilities=[
            "Configure the monitoring solution and alert thresholds.",
            "Train the nominated operations users.",
            "Provide a weekly results summary.",
        ],
        partner_responsibilities=[
            "Provide access to five vehicles and nominate an operations owner.",
            "Confirm acceptable temperature thresholds.",
            "Record actions taken after each alert.",
        ],
        milestones=[
            {
                "when": "Week 0",
                "deliverable": "Confirm scope, owners, data access, and baseline.",
            },
            {
                "when": "Week 1",
                "deliverable": "Install or connect the solution and train users.",
            },
            {
                "when": "Weeks 2–4",
                "deliverable": "Run journeys and review incidents weekly.",
            },
            {
                "when": "Week 5",
                "deliverable": "Compare results with baseline and make a go/no-go decision.",
            },
        ],
        risks_to_verify=[
            "Confirm permission to process operational and location data across both countries.",
            "Confirm device compatibility and connectivity on the selected routes.",
            "Agree who owns pilot data and how long it will be retained.",
        ],
        immediate_next_step=(
            "Schedule a 30-minute scoping call and ask the partner to name one operational owner."
        ),
    )

    message = f"""Subject: A small pilot for {partner}\n\nHi {contact},\n\nIt was good meeting you. I turned our conversation into a small, low-risk pilot for {idea.rstrip(".")}\n\nThe suggestion is to start with five vehicles over four weeks. We would measure data completeness, alert delivery time, and how quickly the operations team can respond. {yours} would handle setup, training, and weekly reporting; your team would provide the vehicles, thresholds, and an operational owner.\n\nWould you be open to a 30-minute call next week to confirm the scope and decide whether it is worth testing?\n\nBest,\n[Your name]"""
    return plan, message
