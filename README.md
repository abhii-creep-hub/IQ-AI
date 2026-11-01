# IQ-AI — AI-Powered Resume Screening & Candidate Intelligence Platform

A recruitment platform that automates resume screening using Large Language Models (LLMs) and NLP. Upload resumes, match against job descriptions, generate ATS scores, rank candidates, and get AI-powered hiring recommendations.

---

## Features

- **AI Resume Parsing** — Extract structured data from PDF/DOCX resumes using Google Gemini
- **ATS Compatibility Scoring** — Detailed score breakdown (0–100) across skills, experience, education, projects, formatting, certifications
- **Job Description Matching** — AI-powered matching of candidates against JDs
- **Candidate Ranking** — Gold / Silver / Bronze / Shortlisted / Rejected / Pending tiers
- **Skill Gap Analysis** — Matched, missing, and recommended skills with a learning roadmap
- **AI Resume Summary** — Professional summary, strengths, weaknesses, career highlights
- **Interview Question Generator** — HR, technical, scenario, behavioral, and coding questions at easy/medium/hard difficulty
- **Hiring Recommendations** — AI-driven strong_hire / hire / maybe / reject decisions with reasoning
- **Recruiter Dashboard** — Stat cards, hiring funnel charts, skill distribution, top candidates
- **Search & Filters** — Full-text search, rank filters, job-based filtering
- **Report Export** — CSV export with ranking data
- **JWT Authentication** — Access + refresh tokens, role-based access (Admin / Recruiter / Viewer)
- **Activity Logs** — Track uploads, logins, analyses, exports

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, React Query, Framer Motion, Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| Database | PostgreSQL 16 |
| AI | Google Gemini API, spaCy, Sentence Transformers |
| Auth | JWT (python-jose), Passlib (bcrypt) |
| Infra | Docker, Docker Compose, GitHub Actions CI/CD |

---

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- PostgreSQL 16+
- Google Gemini API key (needed for resume parsing and AI analysis; a free tier is available with quotas)
- Tesseract OCR executable (only needed for scanned PDF resumes)

### 1. Clone & configure

```bash
git clone https://github.com/your-org/iq-ai.git
cd iq-ai
cp .env.example backend/.env
# Edit backend/.env with your values
# Set GEMINI_API_KEY from https://aistudio.google.com/app/apikey
```

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Project Structure

```
iq-ai/
├── backend/
│   └── app/
│       ├── api/v1/          # FastAPI route handlers
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic request/response schemas
│       ├── services/        # Business logic layer
│       ├── repositories/    # Data access layer
│       ├── database/        # Engine, session, base
│       ├── core/            # Config, security, enums
│       ├── middleware/       # Auth, rate limiting
│       ├── ai/              # Gemini integration, resume parser
│       ├── prompts/         # LLM prompt templates
│       ├── utils/           # Helpers
│       └── main.py
├── frontend/
│   └── src/
│       ├── pages/           # Route-level components
│       ├── layouts/         # Dashboard layout with sidebar
│       ├── context/         # Auth context provider
│       ├── hooks/           # React Query hooks
│       ├── services/        # Axios API client
│       ├── routes/          # React Router config
│       └── utils/           # Helpers, constants
├── .github/workflows/       # CI/CD pipeline
└── README.md
```

---

## Environment Variables

For a free online demo deployment on Render and Neon, see [docs/free-deployment.md](docs/free-deployment.md). Deployment secrets belong in the hosting dashboards, not in this repository.

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `JWT_SECRET_KEY` | JWT signing key | Required |
| `GEMINI_API_KEY` | Google AI Studio API key | Required for AI analysis |
| `GEMINI_MODEL` | Gemini model to use | `gemini-3.5-flash-lite` |
| `GEMINI_BASE_URL` | Gemini OpenAI-compatible API endpoint | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `AI_TEMPERATURE`, `AI_MAX_TOKENS` | Generation settings | `0.3`, `4096` |
| `FRONTEND_URL` | Frontend origin used to build password reset links | `http://localhost:5173` |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | SMTP delivery for password reset links | SMTP credentials required |
| `CORS_ORIGINS` | Allowed origins (JSON array) | `["http://localhost:5173"]` |
| `RATE_LIMIT_PER Minute` | Requests per IP per minute | `60` |
| `MAX_UPLOAD_SIZE_MB` | Max upload file size | `20` |
| `USE_S3` | Use AWS S3 for storage | `false` |

---

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

With Docker Compose, the API docs are available at http://localhost/docs.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register user |
| POST | `/api/v1/auth/login` | Login |
| POST | `/api/v1/auth/refresh` | Refresh token |
| GET | `/api/v1/dashboard/stats` | Dashboard statistics |
| POST | `/api/v1/candidates/upload` | Upload resume |
| POST | `/api/v1/candidates/upload-multiple` | Bulk upload |
| POST | `/api/v1/candidates/{id}/parse` | Parse resume with AI |
| POST | `/api/v1/candidates/{id}/analyze` | Full AI analysis |
| POST | `/api/v1/candidates/{id}/parse-and-analyze` | Parse + analyze |
| GET | `/api/v1/candidates/{id}` | Get candidate detail |
| POST | `/api/v1/jobs/` | Create job |
| GET | `/api/v1/reports/candidate/{id}/full` | Full candidate report |
| GET | `/api/v1/reports/ranking` | Ranking report |

---

## Database Tables

`users` · `jobs` · `candidates` · `resumes` · `skills` · `candidate_skills` · `education` · `experience` · `projects` · `certifications` · `interview_questions` · `ats_results` · `ai_analysis` · `activity_logs` · `reports`

---

## Testing

```bash
cd backend
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Deployment

### Docker Compose

From the repository root, create a root `.env` file and set `POSTGRES_PASSWORD` to a long URL-safe random value and `JWT_SECRET_KEY` to a separate random secret of at least 32 characters. Configure SMTP credentials if password reset emails should be delivered, and add a Google Gemini API key to enable AI analysis. The Gemini free tier has quotas and may use submitted prompts to improve Google products, so test with sample resumes rather than real candidate data.

```bash
cp .env.example .env
docker compose up --build -d
```

Open the app at http://localhost. To create the first administrator, set `IQAI_ADMIN_EMAIL`, `IQAI_ADMIN_USERNAME`, and a 12-character-or-longer `IQAI_ADMIN_PASSWORD` in `.env`, recreate the backend with `docker compose up -d backend`, then run `docker compose exec backend python seed.py`.

Configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM` to enable password recovery email. The reset link points to `FRONTEND_URL`.

### Manual
1. Set up PostgreSQL and create the database
2. Run `alembic upgrade head`
3. Start backend: `uvicorn main:app --host 0.0.0.0 --port 8000`
4. Build frontend: `cd frontend && npm run build`
5. Serve `frontend/dist` with nginx or any static server

### CI/CD
GitHub Actions pipeline automatically runs on push to `main`:
1. Backend tests against PostgreSQL
2. Frontend build verification
3. Docker image build and push to GitHub Container Registry

---

## License

MIT
