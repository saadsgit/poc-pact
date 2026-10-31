# POC Pact

**Turn promising ASEAN ecosystem connections into measurable cross-border POCs.**

POC Pact is a hackathon prototype for Startup ASEAN problem statement 1. After a networking conversation, a founder can upload a business card or screenshot, add a meeting note, and use Gemma 4 to turn that loose information into:

- a reviewed connection record;
- a focused proof-of-concept plan;
- an editable follow-up message; and
- a measurable pipeline from introduction to business outcome.

The central idea is simple: ecosystems should measure what connections produce, not only how many introductions they create.

## Main workflow

1. **Set your profile once:** Save your company and country in the sidebar. Every new connection reuses it automatically.
2. **Capture:** Add meeting notes and optionally an image.
3. **Clarify:** Gemma extracts the contact, job position, email, organizations, countries, collaboration idea, and next step.
4. **Review:** The user corrects the extracted information before saving it. Unknown fields stay blank and can be edited later.
5. **Scope:** Gemma proposes a narrow 2–8 week POC with owners, milestones, and success measures.
6. **Send:** Open the drafted follow-up directly in your email app or Gmail, prefilled with the recipient, subject, and body.
7. **Convert:** Track the connection through follow-up, pilot, partnership, investment, or expansion.

## Data model

Connections are organized as **companies that each contain one or more contacts**:

- A **company** holds the relationship — its name, country, overall stage, timestamped stage history, and final outcome.
- Each **contact** within a company has their own job position, email, discussion notes, collaboration idea, next step, POC pack, and follow-up message.

When a company's stage is set to **Closed**, it leaves the active workspace and is archived under **Completed** with its full stage timeline and outcome.

## Pages

- **Dashboard** — pipeline overview across companies, recorded value, and counts.
- **Capture connection** — turn a meeting note or image into a reviewed record (creates or reuses a company and adds a contact).
- **Connections** — search by company or contact name; edit any company or contact field inline; delete a contact or a whole company.
- **Connection workspace** — pick a company, switch between its contacts, generate a per-contact POC pack, update the stage (timestamped), record an outcome, and **Submit a proposal** to add a new company/contact with fresh context.
- **Completed** — archived closed relationships with their stage timeline and outcome.
- **How it works** — the approach and responsible-use notes.

## Stack

- Python 3.11+
- Streamlit
- SQLite
- Google Gen AI Python SDK
- `gemma-4-26b-a4b-it` through the Gemini API

Google documents hosted Gemma 4 access, supported model IDs, and image inputs in its [Gemma on the Gemini API guide](https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api).

## Run locally

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activation is:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start in demo mode

```bash
streamlit run app.py
```

The app works without a key in **Demo simulation** mode. Choose **Use the sample ASEAN meeting** on the Capture page for the intended demo path. Demo mode is deterministic and does not claim to analyze arbitrary content.

## Connect Gemma 4

Do not put an API key directly in source code.

1. Open [Google AI Studio](https://aistudio.google.com/apikey).
2. Sign in and select **Create API key**.
3. Start POC Pact and paste the key into the sidebar's password field.
4. The sidebar should display `Connected · gemma-4-26b-a4b-it · session key`.
5. Select **Gemma 4**, add a meeting note or image, and click **Analyze connection**.

A key pasted into the password field remains in the current Streamlit session and is not written to the database or source files. For regular use, copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder:

```toml
GEMINI_API_KEY = "your-key-here"
```

Restart Streamlit after adding the secrets file. `.streamlit/secrets.toml` is ignored by Git. Never paste the real key into an issue, commit, screenshot, or chat.

You can alternatively set an environment variable:

```bash
export GEMINI_API_KEY="your-key-here"
streamlit run app.py
```

## Demo script

1. Open **Capture connection**.
2. Click **Use the sample ASEAN meeting**.
3. Click **Analyze connection** and explain that Gemma can combine notes with business-card or chat images.
4. Review and save the extracted connection.
5. Open **Connection workspace** and generate the POC pack.
6. Show the proposed hypothesis, scope, responsibilities, metrics, risks, and follow-up message.
7. Move the connection to **POC running**, then record an outcome.
8. Return to **Dashboard** and show that the ecosystem connection is now measurable.

## Data and safety

- Runtime data is stored locally in `data/poc_pact.db` and ignored by Git.
- Uploaded images are sent to the selected model for analysis but are not saved by this app.
- Free-tier Gemini API data may be used by Google to improve its products. Do not upload private, confidential, or regulated material.
- Users must review AI extraction before saving it.
- Generated POC plans are starting points, not contracts, legal advice, or regulatory advice.
- Cross-border details are listed as items to verify rather than asserted as facts.

## Project structure

```text
poc-pact/
├── app.py
├── poc_pact/
│   ├── ai.py          # Gemma calls and response validation
│   ├── config.py      # Model and application settings
│   ├── database.py    # Parameterized SQLite operations
│   ├── demo.py        # Transparent no-key demonstration
│   ├── models.py      # Connection and POC data models
│   └── ui.py          # Reusable presentation helpers
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.example
└── requirements.txt
```

## Current prototype limits

- It is a single-user local prototype, not a production multi-tenant service.
- It supports common image formats but not PDFs or audio yet.
- The dashboard stores values by currency and does not perform currency conversion.
- Generated content is not automatically sent to contacts.

## Suggested next steps

- Authentication and organization workspaces
- Shared approval of POC plans by both parties
- Email and calendar integrations
- Follow-up reminders for stalled connections
- PDF pitch-deck and voice-note support
- Consent, retention, and deletion controls
- Aggregated Startup ASEAN reporting across participating organizations

## License and competition eligibility

This repository does not include an open-source license by default. Add the license required by your team or hackathon before public distribution. Confirm the event's submission and eligibility rules before submitting.
