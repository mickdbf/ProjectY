# EasyNote AI

An AI-powered web application that converts lecture slides (PDF or PowerPoint) into well-organized study notes and saves them directly to Google Drive.

---

## What It Does

Students upload a lecture slide deck, choose a note style, and EasyNote AI:

1. Extracts text from the uploaded PDF or PowerPoint file
2. Sends the content to OpenAI's GPT-4o-mini with a structured prompt
3. Receives notes in **EasyNote Markup (ENM)** — a custom plain-text format with tags like `#SECTION`, `#POINT`, `#CODE`, etc.
4. Formats those notes into a styled Word document (.docx)
5. Uploads the document to a user-organized folder in Google Drive
6. Returns a shareable link to the file

---

## Note Styles

| Style | Description |
|---|---|
| **Simple Outline** | Hierarchical, scannable bullet summaries |
| **Detailed Notes** | Full-sentence notes with explanations and examples |
| **Cheat Sheet** | Ultra-condensed, formula-focused format for exam review |

Additional options include audience level (beginner / college / researcher / professional), depth (concise / balanced / in-depth), tone, and optional extras like a summary, highlighted terms, or a glossary.

---

## Architecture

```
app/
├── main.py                  # FastAPI app, middleware, startup
├── routes/
│   ├── auth_routes.py       # Google OAuth login/callback/logout
│   ├── notes_routes.py      # File upload → note generation pipeline
│   └── drive_routes.py      # Drive folder listing and creation
├── utils/
│   ├── file_extractors.py   # PDF (PyMuPDF) and PowerPoint (pptx) text extraction
│   ├── llm_utils.py         # Prompt engineering and OpenAI API calls
│   ├── doc_utils.py         # ENM parser → styled Word document
│   ├── drive_utils.py       # Google Drive upload and folder management
│   ├── oauth_utils.py       # Session-based credential management
│   └── text_utils.py        # ENM normalization and cleanup
└── templates/
    ├── index.html           # Landing page
    └── app.html             # Main authenticated UI
```

**Key endpoints:**

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/auth/login` | Start Google OAuth flow |
| GET | `/auth/callback` | OAuth redirect handler |
| GET | `/app` | Main app (requires login) |
| POST | `/generate` | Upload file, generate and save notes |
| GET/POST | `/drive/folders` | List or create Drive folders |
| GET | `/health` | Health check |

---

## Tech Stack

- **Backend:** FastAPI, Uvicorn, Starlette
- **AI:** OpenAI GPT-4o-mini
- **File handling:** PyMuPDF (PDF), python-pptx (PowerPoint), python-docx (Word output)
- **Google integration:** google-api-python-client, google-auth-oauthlib
- **Frontend:** Jinja2 templates, Tailwind CSS, vanilla JavaScript
- **Validation:** Pydantic

---

## Setup

### Prerequisites

- Python 3.11+
- An OpenAI API key
- A Google Cloud project with OAuth 2.0 credentials and Drive API enabled

### Google OAuth Setup

1. Create OAuth 2.0 credentials in the [Google Cloud Console](https://console.cloud.google.com/)
2. Set the authorized redirect URI to `http://localhost:8080/auth/callback`
3. Download the credentials JSON file
4. Save it as `client_secret.json` in the project root
5. Required scopes: `openid`, `userinfo.email`, `drive.file`

### Local Development

```bash
# Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Create a .env file with required variables
# OPENAI_API_KEY=your-openai-key
# ENVIRONMENT=development
# SESSION_SECRET=your-secret-key

# Run the app
python app/main.py
```

The app starts at `http://localhost:8080`.

### Docker

```bash
docker build -t easynote-ai .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY="your-key" \
  -e SESSION_SECRET="your-secret" \
  -e PORT=8080 \
  easynote-ai
```

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | Yes | — | OpenAI API key |
| `SESSION_SECRET` | Yes | `dev-session-key-123` | Session encryption key |
| `PORT` | No | `8080` | Server port |
| `ENVIRONMENT` | No | — | `development` or `production` |

---

## EasyNote Markup (ENM)

ENM is a plain-text markup format used as the structured output contract between the LLM and the document formatter. It avoids Markdown to ensure consistent, machine-readable parsing.

Supported tags: `#SECTION`, `#SUBSECTION`, `#POINT`, `#NOTE`, `#CODE`, `#QUOTE`, `#DIVIDER`

The document formatter in `doc_utils.py` parses ENM tags and maps them to styled Word document elements (headings, bullets, code blocks, dividers, etc.).

---

## Drive Folder Structure

Notes are organized in Google Drive under:

```
EasyNote AI/
└── {Term or Semester}/
    └── {Course Name}/
        └── {Generated .docx file}
```

Folders are created automatically if they do not exist.
