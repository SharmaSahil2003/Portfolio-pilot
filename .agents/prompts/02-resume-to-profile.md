# Step 2: Resume to Profile

**Prerequisite:** Step 1 done.

```text
Using the portfoliopilot-dev skill, implement Step 2: Resume to Profile (SKILL.md Sections 4, 5.1, 8).

Backend:
- Models + migrations: Resume, Profile. Pydantic ProfileSchema exactly as in SKILL.md Section 4, with stable item ids.
- storage/ S3 abstraction (MinIO locally) with random keys and short-lived signed URLs.
- llm/ LLMClient interface with Anthropic and OpenAI adapters, structured-output mode, timeouts, bounded retries, and a FakeLLMClient for tests.
- POST /resumes (multipart): max 5 MB, validate PDF/DOCX by magic bytes, store file, extract text (pdfplumber/pypdf, python-docx), mark needs_ocr if text is near-empty.
- agents/resume_parser.py: one LLM call returning ProfileSchema JSON; validate with Pydantic; on failure retry up to 2 times with the validation error appended. Treat resume text as untrusted (prompt-injection safe delimiters, data-only instruction).
- Deterministic post-processing: normalize dates to YYYY-MM, dedupe skills case-insensitively, alias table (JS -> JavaScript, K8s -> Kubernetes, etc.), assign stable ids, compute content_hash.
- Persist as a new Profile with incremented version_no.
- Endpoints: GET /resumes/{id}, GET /profiles/latest, GET /profiles/{id}, PUT /profiles/{id} (user corrections create a new Profile version).
- For now run parsing as a FastAPI BackgroundTask behind a JobQueue interface so Step 5 can swap in the real queue. Return a job-like status via GET /resumes/{id}.
- Tests: valid resume, corrupt file, wrong MIME, oversize, LLM returns invalid JSON then valid (retry), injection text inside resume is ignored, user A cannot read user B's resume.

Frontend:
- Resume upload page (drag and drop, type/size validation, progress).
- Parse status view (poll GET /resumes/{id}).
- Profile review page: editable form with react-hook-form + Zod covering every ProfileSchema section, add/remove list items, save creates a new profile version.
- Tests with MSW for upload, polling, and form validation.

Run all checks, then update .agents/PROGRESS.md.
```

**Acceptance checks**
- Upload a real resume PDF and see an editable, correct profile.
- Invalid LLM output is retried and tested.
- Cross-user access test passes.
