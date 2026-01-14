# NewtonX Professional Sign-up Management

A full-stack application for managing professional sign-ups from multiple sources (direct, partner, internal).

**Estimated Time:** ~45 minutes (vibe coded)

## Features

- **Single Professional Add** - Form with all fields including resume upload
- **Bulk Upload** - CSV file upload for adding multiple professionals at once
- **Resume Extraction** - Auto-fill form from PDF resume using:
  - Basic Python extraction (no API key needed)
  - LLM extraction via OpenAI (more accurate)
- **Search** - Search across name, email, and phone
- **Filter** - Filter by signup source
- **Resume Storage** - Upload and download PDF resumes

## Tech Stack

### Backend
- **Python 3.10+** with Django 4.x
- **Django REST Framework** for API
- **SQLite** database (zero config)
- **UV** for package management
- **pdfplumber** for PDF text extraction
- **OpenAI** for LLM-based extraction

### Frontend
- **React 18** with Vite
- **Tailwind CSS** for styling
- Single-page application with form and filterable table

## Quick Start

### Backend Setup

```bash
cd backend

# Install dependencies with UV (creates venv automatically)
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Set up environment variables (optional - for LLM extraction)
cp .env.sample .env
# Edit .env and add your OpenAI API key

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/professionals/`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### 1. Create Professional
```
POST /api/professionals/
```

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+14155551234",
  "source": "direct",
  "company_name": "Acme Inc",
  "job_title": "Engineer"
}
```

**Required Fields:** `first_name`, `last_name`, `email`, `source`

**Optional Fields:** `phone`, `company_name`, `job_title`, `resume` (file)

### 2. List Professionals
```
GET /api/professionals/
GET /api/professionals/?source=direct
GET /api/professionals/?search=john
GET /api/professionals/?source=direct&search=john
```

**Query Parameters:**
- `source` (optional): Filter by source (`direct`, `partner`, `internal`)
- `search` (optional): Search across first_name, last_name, email, phone

### 3. Bulk Create/Update
```
POST /api/professionals/bulk/
```

**Request Body:** Array of professional objects

**Upsert Logic:**
- Uses `email` as the primary unique key
- Falls back to `phone` if email is not provided

**Response Format:**
```json
{
  "results": [
    {"index": 0, "success": true, "action": "created", "data": {...}},
    {"index": 1, "success": true, "action": "updated", "data": {...}},
    {"index": 2, "success": false, "error": {...}}
  ],
  "summary": {"total": 3, "created": 1, "updated": 1, "failed": 1}
}
```

### 4. Extract Resume Data
```
POST /api/professionals/extract-resume/
Content-Type: multipart/form-data
```

**Form Fields:**
- `resume`: PDF file (required)
- `method`: `python` or `llm` (default: `python`)
- `openai_key`: OpenAI API key (required if method is `llm`)

**Response:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john@example.com",
  "phone": "+14155551234",
  "company_name": "Acme Inc",
  "job_title": "Software Engineer"
}
```

## Running Tests

```bash
cd backend
source .venv/bin/activate
python manage.py test professionals
```

## Data Model

| Field | Type | Required | Unique | Notes |
|-------|------|----------|--------|-------|
| `id` | Integer | Auto | Yes | Primary key |
| `first_name` | String (127) | Yes | No | |
| `last_name` | String (127) | Yes | No | |
| `email` | Email | Yes | Yes | Validated format |
| `phone` | String (17) | No | Yes* | E.164 format, *NULL allowed |
| `source` | Enum | Yes | No | `direct`, `partner`, `internal` |
| `company_name` | String (255) | No | No | |
| `job_title` | String (255) | No | No | |
| `resume` | File | No | No | PDF upload |
| `created_at` | DateTime | Auto | No | Auto-generated timestamp |

## CSV Template for Bulk Upload

```csv
first_name,last_name,email,phone,source,company_name,job_title
John,Doe,john@example.com,+14155551234,direct,Acme Inc,Engineer
Jane,Smith,jane@example.com,+14155555678,partner,Tech Corp,Manager
```

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Django settings
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True

# OpenAI API Key (required for LLM-based PDF extraction)
OPENAI_API_KEY=sk-your-openai-api-key-here
```

## Assumptions & Trade-offs

### Assumptions
1. **Email is always required** - Based on the requirements, email serves as the primary unique identifier
2. **Phone uniqueness** - Phone numbers are unique when provided, but multiple records can have null phones
3. **E.164 phone format** - Phone numbers validated against E.164 format (e.g., +14155551234)
4. **Bulk upsert priority** - Email takes precedence over phone for matching existing records

### Trade-offs
1. **SQLite over PostgreSQL** - Chose SQLite for zero-config setup; PostgreSQL recommended for production
2. **No authentication** - Not in requirements scope; would add JWT/session auth for production
3. **No pagination** - Simple list endpoint; would add pagination for larger datasets
4. **Basic PDF extraction** - Python regex-based extraction is simpler but less accurate than LLM

## What I'd Improve With More Time

1. **Testing:**
   - Add frontend unit tests with React Testing Library
   - Add E2E tests with Playwright/Cypress
   - Increase backend test coverage

2. **Features:**
   - Edit/delete professionals
   - Pagination for large datasets
   - Export to CSV
   - Drag-and-drop file upload
   - Resume preview

3. **UX Improvements:**
   - Inline form validation feedback
   - Confirmation dialogs
   - Toast notifications
   - Dark mode support
   - Mobile responsive improvements

4. **Production Readiness:**
   - Docker containerization
   - Environment variable configuration
   - PostgreSQL database
   - Authentication & authorization
   - Rate limiting
   - API documentation (Swagger/OpenAPI)
   - Cloud storage for resumes (S3)

## Project Structure

```
newtonx/
├── backend/
│   ├── config/              # Django project settings
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── professionals/       # Main app
│   │   ├── models.py        # Professional model
│   │   ├── serializers.py   # DRF serializers
│   │   ├── views.py         # API views
│   │   ├── services.py      # PDF extraction services
│   │   ├── urls.py          # API routes
│   │   └── tests.py         # Unit tests
│   ├── media/               # Uploaded files (gitignored)
│   ├── manage.py
│   ├── pyproject.toml       # Python dependencies
│   ├── .env.sample          # Environment template
│   └── .env                 # Environment variables (gitignored)
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── professionals.js  # API client
│   │   ├── components/
│   │   │   ├── ProfessionalForm.jsx
│   │   │   ├── ProfessionalList.jsx
│   │   │   └── BulkUpload.jsx
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css        # Tailwind imports
│   ├── package.json
│   └── vite.config.js
│
├── docs/                    # Requirements document + test data
│   └── test_professionals.csv  # Sample CSV with 15 records for testing
├── .gitignore
└── README.md
```

