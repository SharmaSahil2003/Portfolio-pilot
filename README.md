# PortfolioPilot

PortfolioPilot updates the versioned key/response table that powers a user's existing portfolio. The flow uploads a resume, connects to the user's PostgreSQL or MySQL database, loads the latest keys/pages and prior responses, generates a reviewable proposal, and writes the complete updated snapshot as a new version. The app includes a React + TypeScript dashboard, a FastAPI API, MongoDB account storage, LangGraph workflows, and an isolated React workspace build worker.

## Run locally with Docker

1. Copy `.env.example` to `.env` and replace `JWT_SECRET` with a random secret. Add a Gemini API key from Google AI Studio as `GEMINI_API_KEY` to enable resume extraction and page/workspace suggestions. The dashboard and deterministic sync flow can also be explored without a key.
2. Start the services:

   ```sh
   docker compose up --build
   ```

3. Open <http://localhost:5173>. Browser API requests go through the web container's `/api` proxy. The API docs are at <http://localhost:8000/docs> and the health endpoint is <http://localhost:8000/api/health>.

The build worker has no MongoDB connection or model credentials. It applies memory, CPU, process, and temporary storage limits; serializes builds under an unprivileged UID, and disables dependency install lifecycle scripts. Only static build output is served. Uploaded project build scripts still execute as untrusted code inside that constrained service; use a separate host for deployments that process untrusted uploads at scale.

## Run the frontend without Docker

Install Node.js 20+, run `npm install`, then `npm run dev`. The API needs Python 3.11+, MongoDB, and the backend packages:

```sh
cp .env.example .env
python -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload --port 8000
```

For standalone backend development, use `cp backend/.env.example .env`; this points MongoDB at localhost. Workspace builds still require the full Compose stack because the API calls the internal build worker service.

## Connect a portfolio database

The dashboard currently supports PostgreSQL and MySQL. Provide a host reachable from the API container, database name, port, username, password, optional schema, table name, and mappings for the key, response, description, and version columns. When the database runs on the same machine as Docker Desktop, use `host.docker.internal` instead of `localhost`. SSL can be enabled for hosted databases. Use a least-privilege database account with `SELECT` and `INSERT` access to the mapped table.

The connector expects one row per key per version. The same key must be insertable again in a later version, so use a composite uniqueness rule such as `(version, key)` rather than making `key` unique by itself. Each published version contains the full set of keys/pages, including unchanged rows. The portfolio should query the rows belonging to the newest version.

Example PostgreSQL schema for data-sync values:

```sql
CREATE TABLE portfolio_content (
  key text NOT NULL,
  response jsonb NOT NULL,
  description text NOT NULL DEFAULT '',
  version integer NOT NULL,
  PRIMARY KEY (version, key)
);
```

For page updates, use the page name as `key` and store the complete HTML/JSX/TSX source in `response`. The page redesign prompt preserves the existing framework and data contracts, and reviews complete replacement source for each selected page. A version column should be numeric or use labels such as `v1`, `v2`, and `v3` so the newest snapshot can be identified reliably.

Database credentials are encrypted in MongoDB using a key derived from `JWT_SECRET`; keep that secret stable and replace the development value before deploying. If the secret changes, previously stored database credentials cannot be decrypted and users will need to reconnect.

## Account data

Resume files and account metadata remain in the application's MongoDB. Database rows and published versions are stored in each user's own PostgreSQL or MySQL table. The application's internal MongoDB versions are not used for these external database updates.

## Configuration

| Variable | Purpose |
| --- | --- |
| `MONGODB_URL` | MongoDB connection string |
| `MONGODB_DATABASE` | Database name |
| `JWT_SECRET` | Signing secret for account tokens |
| `JWT_EXPIRE_MINUTES` | Session lifetime |
| `GEMINI_API_KEY` | Optional server-only Gemini API key for LangGraph LLM steps |
| `GEMINI_MODEL` | Gemini model used by the provider adapter |
| `GEMINI_FALLBACK_MODEL` | Gemini model used if the primary model is temporarily unavailable |
| `MAX_UPLOAD_MB` | PDF and workspace upload limit |
| `FRONTEND_ORIGIN` | CORS origin for the dashboard |
| `PREVIEW_BASE_URL` | Separate-origin URL used for sandboxed static portfolio previews |
| `PUBLIC_API_BASE_URL` | Public base URL used by portfolio data endpoints |

Resume files, workspace archives, variable definitions/values, and version metadata are associated with the owning account. Uploaded files are held in MongoDB GridFS. The build worker is internal to Compose; Nginx exposes only its static preview route on port `8001`, on a different origin from the dashboard, so uploaded JavaScript cannot access the dashboard session.
