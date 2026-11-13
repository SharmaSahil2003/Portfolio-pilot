import io
import html
import json
import base64
import hashlib
import secrets
import zipfile
from datetime import datetime, timezone
from uuid import uuid4

from bson import ObjectId
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorGridFSBucket
from pymongo.errors import DuplicateKeyError
from pypdf import PdfReader
import httpx
from cryptography.fernet import Fernet, InvalidToken

from .agent import workflow
from .config import settings
from .external_db import publish_records, read_records, verify_connection
from .models import Credentials, DatabaseConnectionRequest, DatabaseProposalRequest, DatabasePublishRequest, GenerationRequest, Profile, TokenResponse, VariableGenerationRequest, VariableUpdateRequest, VersionOut
from .security import create_token, decode_token, hash_password, verify_password

app = FastAPI(title="PortfolioPilot API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer(auto_error=False)
mongo: AsyncIOMotorClient | None = None
db = None
bucket: AsyncIOMotorGridFSBucket | None = None
BUILD_WORKER_URL = "http://build-worker:8001"


def credentials_cipher() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(("portfolio-db:" + settings.jwt_secret).encode()).digest())
    return Fernet(key)


def saved_database_config(user: dict) -> dict:
    encrypted = user.get("database_config")
    if not encrypted:
        raise HTTPException(409, "Connect your database before continuing")
    try:
        return json.loads(credentials_cipher().decrypt(encrypted).decode())
    except (InvalidToken, ValueError, TypeError) as exc:
        raise HTTPException(500, "Saved database credentials could not be decrypted") from exc


def portfolio_html(profile: dict, page: str | None = None, page_content: dict | None = None) -> str:
    page_content = page_content or {}
    name = html.escape(str(profile.get("name") or "Developer"))
    headline = html.escape(str(page_content.get("headline") or profile.get("headline") or "Building thoughtful digital experiences"))
    intro = html.escape(str(page_content.get("intro") or "Building thoughtful products with technology and care."))
    about = html.escape(str(page_content.get("about") or profile.get("about") or "A software engineer who enjoys turning complex problems into useful products."))
    location = html.escape(str(profile.get("location") or ""))
    skills = "".join(f"<span>{html.escape(str(skill))}</span>" for skill in profile.get("skills", [])[:20])
    projects = "".join(f"<article><h3>{html.escape(str(item.get('name', 'Project')))}</h3><p>{html.escape(str(item.get('description', '')))}</p><small>{html.escape(', '.join(item.get('stack', [])))}</small></article>" for item in profile.get("projects", [])[:12])
    experience = "".join(f"<article><h3>{html.escape(str(item.get('role', 'Role')))}</h3><p>{html.escape(str(item.get('company', '')))} · {html.escape(str(item.get('period', '')))}</p></article>" for item in profile.get("experience", [])[:12])
    focus = html.escape(page or "Portfolio")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{name} — Portfolio</title><meta name="description" content="{headline}"><style>*{{box-sizing:border-box}}body{{margin:0;background:#101512;color:#eef2e7;font:16px/1.6 Inter,system-ui,sans-serif}}main{{max-width:920px;margin:auto;padding:36px 26px 90px}}nav{{display:flex;justify-content:space-between;color:#c8f47b;font-size:13px}}nav a{{color:#c8f47b;text-decoration:none;margin-left:18px}}header{{padding:105px 0 70px;max-width:750px}}small,.eyebrow{{color:#a7ba8a;letter-spacing:.12em;text-transform:uppercase;font-size:11px}}h1{{font-size:clamp(48px,9vw,88px);line-height:.98;letter-spacing:-.065em;margin:20px 0}}header p{{max-width:590px;color:#aab4a9;font-size:18px}}h2{{font-size:25px;letter-spacing:-.04em;margin-top:56px}}.chips{{display:flex;gap:9px;flex-wrap:wrap}}.chips span{{border:1px solid #39433c;padding:6px 10px;border-radius:6px;color:#c6d0c1;font-size:12px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(225px,1fr));gap:12px}}article{{background:#171e19;border:1px solid #303a32;border-radius:10px;padding:18px}}article h3{{font-size:16px;margin:0 0 5px}}article p{{color:#adb8aa;font-size:13px}}article small{{font-size:10px}}footer{{border-top:1px solid #303a32;margin-top:60px;padding-top:18px;color:#829083;font-size:12px}}.focus{{color:#c8f47b}}</style></head><body><main><nav><strong>{name.split(' ')[0].lower()}.</strong><span><a href="#work">Work</a><a href="#about">About</a></span></nav><header><div class="eyebrow">{location} · {focus}</div><h1>{name.split(' ')[0]}<br><span class="focus">{intro}</span></h1><p>{headline}. {about}</p></header><section id="about"><small>TOOLKIT</small><h2>Things I work with</h2><div class="chips">{skills or '<span>Software engineering</span>'}</div></section><section id="work"><small>SELECTED WORK</small><h2>Projects</h2><div class="grid">{projects or '<article><h3>More work in progress</h3><p>Projects will appear here as you add them to your profile.</p></article>'}</div></section><section><small>EXPERIENCE</small><h2>Where I have been</h2><div class="grid">{experience or '<article><p>Add your experience to your profile to show it here.</p></article>'}</div></section><footer>Designed and evolved with PortfolioPilot · {name}</footer></main></body></html>'''


def profile_changes(before: dict, after: dict) -> list[str]:
    changes = []
    for key, label in (("skills", "skills"), ("experience", "experience entries"), ("projects", "projects")):
        old = {str(item).lower() for item in before.get(key, [])}
        new = {str(item).lower() for item in after.get(key, [])}
        if old != new:
            added, removed = len(new - old), len(old - new)
            details = []
            if added:
                details.append(f"+{added}")
            if removed:
                details.append(f"−{removed}")
            changes.append(f"Updated {label} ({', '.join(details)})")
    for key, label in (("headline", "headline"), ("about", "summary"), ("location", "location")):
        if before.get(key) != after.get(key):
            changes.append(f"Updated {label}")
    return changes or ["No profile content differences detected"]


@app.on_event("startup")
async def startup():
    global mongo, db, bucket
    mongo = AsyncIOMotorClient(settings.mongodb_url)
    db = mongo[settings.mongodb_database]
    bucket = AsyncIOMotorGridFSBucket(db)
    await db.users.create_index("email", unique=True)
    await db.profiles.create_index("user_id", unique=True)
    await db.workspaces.create_index("user_id", unique=True)
    await db.versions.create_index([("user_id", 1), ("created_at", -1)])
    await db.versions.create_index([("user_id", 1), ("version_number", -1)], unique=True, partialFilterExpression={"version_number": {"$type": "int"}})
    await db.portfolio_variables.create_index([("user_id", 1), ("version_id", 1), ("key", 1)], unique=True)
    await db.resumes.create_index("user_id", unique=True)


@app.on_event("shutdown")
async def shutdown():
    if mongo:
        mongo.close()


async def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not credentials:
        raise HTTPException(401, "Sign in to access this resource")
    subject = decode_token(credentials.credentials)
    if not subject or not ObjectId.is_valid(subject):
        raise HTTPException(401, "Invalid or expired session")
    user = await db.users.find_one({"_id": ObjectId(subject)})
    if not user:
        raise HTTPException(401, "Account not found")
    return user


def version_out(doc: dict) -> dict:
    return {"id": str(doc["_id"]), "label": doc["label"], "mode": doc["mode"], "createdAt": doc["created_at"].strftime("%b %d · %I:%M %p"), "status": doc["status"], "changes": doc["changes"], "previewUrl": f"{settings.preview_base_url}/preview/{doc['preview_id']}/" if doc.get("preview_id") else None, "versionNumber": doc.get("version_number")}


async def next_version_number(user_id) -> int:
    latest = await db.versions.find_one({"user_id": user_id, "version_number": {"$type": "int"}}, sort=[("version_number", -1)])
    return int(latest.get("version_number", 0)) + 1 if latest else 1


@app.get("/api/health")
async def health():
    await db.command("ping")
    return {"status": "ok", "database": "connected"}


@app.post("/api/auth/register", response_model=TokenResponse)
async def register(payload: Credentials):
    email = payload.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(409, "An account with this email already exists")
    user_id = ObjectId()
    try:
        await db.users.insert_one({"_id": user_id, "email": email, "password_hash": hash_password(payload.password), "public_id": secrets.token_urlsafe(12), "created_at": datetime.now(timezone.utc)})
    except DuplicateKeyError as exc:
        raise HTTPException(409, "An account with this email already exists") from exc
    await db.profiles.insert_one({"user_id": user_id, **Profile(email=email).model_dump()})
    return TokenResponse(access_token=create_token(str(user_id)))


@app.post("/api/auth/login", response_model=TokenResponse)
async def login(payload: Credentials):
    user = await db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(401, "Email or password is incorrect")
    return TokenResponse(access_token=create_token(str(user["_id"])))


@app.get("/api/profile", response_model=Profile)
async def get_profile(user: dict = Depends(current_user)):
    profile = await db.profiles.find_one({"user_id": user["_id"]}, {"_id": 0, "user_id": 0})
    return Profile(**profile) if profile else Profile(email=user["email"])


@app.put("/api/profile", response_model=Profile)
async def put_profile(payload: Profile, user: dict = Depends(current_user)):
    data = payload.model_dump()
    await db.profiles.update_one({"user_id": user["_id"]}, {"$set": data}, upsert=True)
    return payload


@app.post("/api/resume")
async def upload_resume(file: UploadFile = File(...), user: dict = Depends(current_user)):
    if not file.filename or not file.filename.lower().endswith(".pdf") or file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(415, "Upload a PDF resume")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "Resume exceeds the upload limit")
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:20])
    except Exception as exc:
        raise HTTPException(422, "This PDF could not be read") from exc
    if not text.strip():
        raise HTTPException(422, "No selectable text found in this PDF")
    file_id = await bucket.upload_from_stream(file.filename, content, metadata={"user_id": user["_id"], "kind": "resume"})
    await db.resumes.update_one({"user_id": user["_id"]}, {"$set": {"file_id": file_id, "filename": file.filename, "uploaded_at": datetime.now(timezone.utc)}}, upsert=True)
    return {"filename": file.filename, "uploadedAt": datetime.now(timezone.utc).isoformat()}


@app.get("/api/resume")
async def resume_info(user: dict = Depends(current_user)):
    resume = await db.resumes.find_one({"user_id": user["_id"]}, {"_id": 0, "file_id": 0, "user_id": 0})
    return {"filename": resume.get("filename") if resume else None, "uploadedAt": resume.get("uploaded_at").isoformat() if resume and resume.get("uploaded_at") else None}


@app.get("/api/database/config")
async def database_config(user: dict = Depends(current_user)):
    if not user.get("database_config"):
        return {"connected": False}
    config = saved_database_config(user)
    return {"connected": True, **{key: value for key, value in config.items() if key != "password"}}


@app.post("/api/database/connect")
async def connect_database(payload: DatabaseConnectionRequest, user: dict = Depends(current_user)):
    config = payload.model_dump()
    if not config["password"] and user.get("database_config"):
        config["password"] = saved_database_config(user)["password"]
    if not config["password"]:
        raise HTTPException(422, "Enter the database password")
    try:
        await run_in_threadpool(verify_connection, config)
    except Exception as exc:
        # Keep connection strings and driver details out of API logs and responses.
        raise HTTPException(422, "Could not connect or read the mapped table. Check the engine, credentials, network access, table, and column mappings.") from exc
    encrypted = credentials_cipher().encrypt(json.dumps(config).encode())
    await db.users.update_one({"_id": user["_id"]}, {"$set": {"database_config": encrypted}})
    return {"connected": True, "message": "Database connection verified and saved securely."}


@app.post("/api/database/records")
async def database_records(user: dict = Depends(current_user)):
    config = saved_database_config(user)
    try:
        records = await run_in_threadpool(read_records, config)
    except Exception as exc:
        raise HTTPException(502, "Could not load records from the connected table. Recheck the connection and column mapping.") from exc
    return {"records": records, "version": records[0]["version"] if records else None}


@app.post("/api/database/propose")
async def database_propose(payload: DatabaseProposalRequest, user: dict = Depends(current_user)):
    config = saved_database_config(user)
    try:
        current = await run_in_threadpool(read_records, config)
    except Exception as exc:
        raise HTTPException(502, "Could not load records from the connected table") from exc
    actual_version = current[0]["version"] if current else None
    if actual_version != payload.expected_version:
        raise HTTPException(409, "The connected table changed. Reload its latest records before generating a proposal.")
    existing = {str(row["key"]): row for row in current}
    requested: dict[str, dict] = {}
    for row in payload.records:
        key = str(row.get("key", "")).strip()
        if not key or len(key) > 128 or key in requested:
            raise HTTPException(422, "Every row needs a unique key (up to 128 characters)")
        requested[key] = row
    selected = []
    merged = []
    for key, row in requested.items():
        old = existing.get(key, {})
        item = {"key": key, "description": str(row.get("description", old.get("description", "")))[:500], "response": old.get("response")}
        if row.get("selected", True):
            selected.append(item)
        merged.append(item)
    if not selected:
        raise HTTPException(422, "Select at least one key or page to update")
    resume_text = await read_latest_resume(user["_id"])
    result = await workflow.ainvoke({"task": "database", "mode": payload.mode, "records": selected, "text": resume_text})
    generated = result.get("result", {})
    if not generated.get("ai_enabled"):
        raise HTTPException(503, "The AI provider could not return a complete proposal. Check model access and try again.")
    updates = {row["key"]: row for row in generated["updates"]}
    final_records = []
    for row in merged:
        update = updates.get(row["key"])
        final_records.append({**row, "previous_response": row["response"], "response": update["response"] if update else row["response"], "selected": row["key"] in updates})
    return {"records": final_records, "version": actual_version, "changes": generated.get("changes", [])}


@app.post("/api/database/publish")
async def database_publish(payload: DatabasePublishRequest, user: dict = Depends(current_user)):
    config = saved_database_config(user)
    try:
        version = await run_in_threadpool(publish_records, config, payload.records, payload.expected_version)
    except RuntimeError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(502, "Could not publish the new version to the connected table") from exc
    return {"published": True, "version": version, "message": "A new version was published to your database."}


async def read_latest_resume(user_id) -> str:
    resume = await db.resumes.find_one({"user_id": user_id})
    if not resume:
        raise HTTPException(409, "Upload a resume before generating portfolio data")
    download = await bucket.open_download_stream(resume["file_id"])
    content = await download.read()
    try:
        reader = PdfReader(io.BytesIO(content))
        text = "\n".join((page.extract_text() or "") for page in reader.pages[:20])
    except Exception as exc:
        raise HTTPException(422, "The saved resume could not be read") from exc
    if not text.strip():
        raise HTTPException(422, "No selectable text found in the saved resume")
    return text


@app.post("/api/variables/generate")
async def generate_variables(payload: VariableGenerationRequest, user: dict = Depends(current_user)):
    keys = [item.key for item in payload.definitions]
    if len(set(keys)) != len(keys):
        raise HTTPException(422, "Variable keys must be unique")
    text = await read_latest_resume(user["_id"])
    definitions = [item.model_dump() for item in payload.definitions]
    result = await workflow.ainvoke({"task": "variables", "text": text, "definitions": definitions})
    extracted = result.get("result", {})
    rows = extracted.get("variables", [])
    number = await next_version_number(user["_id"])
    version_id = ObjectId()
    version = {
        "_id": version_id, "user_id": user["_id"], "label": f"Resume data v{number}", "mode": "sync",
        "version_number": number, "created_at": datetime.now(timezone.utc), "status": "pending",
        "changes": [f"Generated {len(rows)} database variables", "Values are editable before activation"],
        "profile_snapshot": {}, "preview_id": None,
    }
    await db.versions.insert_one(version)
    variable_rows = [{
        "user_id": user["_id"], "version_id": version_id, "version": f"v{number}",
        "key": item["key"], "description": item["description"], "sample_json": item.get("sample_json"),
        "value": item.get("value"), "created_at": datetime.now(timezone.utc),
    } for item in rows]
    if variable_rows:
        await db.portfolio_variables.insert_many(variable_rows)
    response_rows = [{key: row.get(key) for key in ("version", "key", "description", "sample_json", "value")} for row in variable_rows]
    return {
        "id": str(version_id), "status": "pending_review", "message": "Review and edit each generated database value before activating this version.",
        "version": version_out(version), "variables": response_rows, "aiEnabled": extracted.get("ai_enabled", False),
    }


@app.get("/api/variables/definitions")
async def list_variable_definitions(user: dict = Depends(current_user)):
    latest = await db.versions.find_one({"user_id": user["_id"], "mode": "sync", "version_number": {"$type": "int"}}, sort=[("version_number", -1)])
    if not latest:
        return {"definitions": []}
    rows = await db.portfolio_variables.find({"user_id": user["_id"], "version_id": latest["_id"]}, {"_id": 0, "user_id": 0, "version_id": 0, "value": 0, "created_at": 0}).to_list(100)
    return {"definitions": rows}


@app.get("/api/versions/{version_id}/variables")
async def list_version_variables(version_id: str, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    version = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not version:
        raise HTTPException(404, "Version not found")
    return {"variables": await db.portfolio_variables.find({"user_id": user["_id"], "version_id": version["_id"]}, {"_id": 0, "user_id": 0, "version_id": 0, "created_at": 0}).to_list(100)}


@app.put("/api/versions/{version_id}/variables")
async def update_version_variables(version_id: str, payload: VariableUpdateRequest, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    version = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not version:
        raise HTTPException(404, "Version not found")
    if version["status"] != "pending":
        raise HTTPException(409, "Only pending version values can be edited")
    keys = [item.key for item in payload.variables]
    if len(set(keys)) != len(keys):
        raise HTTPException(422, "Variable keys must be unique")
    existing = await db.portfolio_variables.find({"user_id": user["_id"], "version_id": version["_id"]}).to_list(100)
    old_values = {row["key"]: row.get("value") for row in existing}
    new_values = {item.key: item.value for item in payload.variables}
    changes = [f"Added {key}" for key in new_values.keys() - old_values.keys()]
    changes += [f"Removed {key}" for key in old_values.keys() - new_values.keys()]
    changes += [f"Updated {key}" for key in new_values.keys() & old_values.keys() if new_values[key] != old_values[key]]
    if not changes:
        changes = [f"Reviewed {len(payload.variables)} variables; values unchanged"]
    await db.portfolio_variables.delete_many({"user_id": user["_id"], "version_id": version["_id"]})
    rows = [{"user_id": user["_id"], "version_id": version["_id"], "version": f"v{version.get('version_number', 1)}", **item.model_dump(), "created_at": datetime.now(timezone.utc)} for item in payload.variables]
    if rows:
        await db.portfolio_variables.insert_many(rows)
    await db.versions.update_one({"_id": version["_id"]}, {"$set": {"changes": changes}})
    return {"variables": [{key: value for key, value in row.items() if key not in ("_id", "user_id", "version_id", "created_at")} for row in rows]}


@app.get("/api/variables/active")
async def get_active_variables(user: dict = Depends(current_user)):
    version = await db.versions.find_one({"user_id": user["_id"], "mode": "sync", "status": "active"})
    if not version:
        return {"version": None, "variables": []}
    rows = await db.portfolio_variables.find({"user_id": user["_id"], "version_id": version["_id"]}, {"_id": 0, "user_id": 0, "version_id": 0, "created_at": 0}).to_list(100)
    return {"version": version_out(version), "variables": rows}


@app.get("/api/portfolio/integration")
async def portfolio_integration(user: dict = Depends(current_user)):
    public_id = user.get("public_id")
    if not public_id:
        public_id = secrets.token_urlsafe(12)
        await db.users.update_one({"_id": user["_id"]}, {"$set": {"public_id": public_id}})
    return {"public_id": public_id, "endpoint": f"{settings.public_api_base_url}/api/public/portfolio/{public_id}"}


@app.get("/api/public/portfolio/{public_id}")
async def public_portfolio_data(public_id: str):
    user = await db.users.find_one({"public_id": public_id}, {"_id": 1})
    if not user:
        raise HTTPException(404, "Portfolio data not found")
    version = await db.versions.find_one({"user_id": user["_id"], "mode": "sync", "status": "active"})
    if not version:
        return {"version": None, "variables": {}}
    rows = await db.portfolio_variables.find({"user_id": user["_id"], "version_id": version["_id"]}, {"_id": 0, "key": 1, "value": 1}).to_list(100)
    return {"version": f"v{version.get('version_number', 1)}", "variables": {item["key"]: item.get("value") for item in rows}}


@app.post("/api/workspace")
async def upload_workspace(file: UploadFile = File(...), user: dict = Depends(current_user)):
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(415, "Upload a ZIP archive of a React project")
    content = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "Workspace exceeds the upload limit")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 2500:
                raise HTTPException(413, "Workspace contains too many files")
            for entry in entries:
                normalized = entry.filename.replace("\\", "/")
                if normalized.startswith("/") or ".." in normalized.split("/"):
                    raise HTTPException(422, "Workspace contains an unsafe file path")
            package_entry = next((entry for entry in entries if entry.filename.endswith("package.json")), None)
            if not package_entry:
                raise HTTPException(422, "No package.json found; upload a React project")
            package = json.loads(archive.read(package_entry))
            if not isinstance(package, dict):
                raise HTTPException(422, "Invalid package.json")
            if not any(dep in {**package.get("dependencies", {}), **package.get("devDependencies", {})} for dep in ("react", "react-dom")):
                raise HTTPException(422, "This project does not appear to use React")
            scripts = package.get("scripts", {})
            if not scripts.get("build"):
                raise HTTPException(422, "No build script found in package.json")
    except zipfile.BadZipFile as exc:
        raise HTTPException(422, "The uploaded ZIP archive is invalid") from exc
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        raise HTTPException(422, "The project's package.json is invalid") from exc
    file_id = await bucket.upload_from_stream(file.filename, content, metadata={"user_id": user["_id"], "kind": "workspace"})
    await db.workspaces.update_one({"user_id": user["_id"]}, {"$set": {"file_id": file_id, "filename": file.filename, "uploaded_at": datetime.now(timezone.utc)}}, upsert=True)
    return {"filename": file.filename, "framework": "React", "build_script": scripts["build"], "message": "Project validated and uploaded"}


@app.post("/api/generations")
async def generate(payload: GenerationRequest, user: dict = Depends(current_user)):
    profile = await db.profiles.find_one({"user_id": user["_id"]}, {"_id": 0, "user_id": 0}) or Profile(email=user["email"]).model_dump()
    if payload.mode != "sync":
        resume_text = await read_latest_resume(user["_id"])
        extracted = await workflow.ainvoke({"task": "extract", "text": resume_text})
        profile = Profile(**extracted.get("profile", {})).model_dump()
    if payload.mode == "workspace" and not await db.workspaces.find_one({"user_id": user["_id"]}):
        raise HTTPException(409, "Upload a React workspace before using workspace evolution")
    task_state = {"task": payload.mode, "profile": profile, "page": payload.page or "Home"}
    if payload.mode == "workspace":
        workspace = await db.workspaces.find_one({"user_id": user["_id"]})
        active_workspace = await db.versions.find_one({"user_id": user["_id"], "mode": "workspace", "status": "active", "workspace_file_id": {"$ne": None}})
        source_file_id = active_workspace.get("workspace_file_id") if active_workspace else workspace["file_id"]
        download = await bucket.open_download_stream(source_file_id)
        archive_bytes = await download.read()
        try:
            with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
                safe_files = {}
                for entry in archive.infolist():
                    name = entry.filename.replace("\\", "/")
                    if entry.is_dir() or ".." in name.split("/") or name.startswith("/"):
                        continue
                    if name.lower().endswith((".tsx", ".ts", ".jsx", ".js")) and entry.file_size < 120_000:
                        safe_files[name] = archive.read(entry).decode("utf-8", errors="ignore")[:20_000]
            task_state["current"] = {"files": dict(list(safe_files.items())[:12])}
        except zipfile.BadZipFile as exc:
            raise HTTPException(422, "The stored workspace archive is invalid") from exc
    if payload.mode == "page":
        active = await db.versions.find_one({"user_id": user["_id"], "status": "active"})
        task_state["current"] = {"page_content": active.get("page_content", {}) if active else {}, "profile": active.get("profile_snapshot", {}) if active else {}}
    result = await workflow.ainvoke(task_state)
    changes = result.get("result", {}).get("changes", [])
    page_content = result.get("result", {}).get("content", {})
    if payload.mode == "sync":
        previous = await db.versions.find_one({"user_id": user["_id"], "status": "active"})
        changes = profile_changes(previous.get("profile_snapshot", {}) if previous else {}, profile)
    preview_id = None
    artifact_id = None
    if payload.mode == "workspace":
        generated = dict(result.get("result", {}).get("files", {}))
        build_error = "Workspace build failed"
        try:
            async with httpx.AsyncClient(timeout=240) as client:
                for attempt in range(2):
                    changed_archive = io.BytesIO()
                    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as original, zipfile.ZipFile(changed_archive, "w", zipfile.ZIP_DEFLATED) as output:
                        for entry in original.infolist():
                            name = entry.filename.replace("\\", "/")
                            if entry.is_dir() or ".." in name.split("/") or name.startswith("/"):
                                continue
                            if name in generated:
                                output.writestr(entry, generated[name])
                            else:
                                output.writestr(entry, original.read(entry))
                    response = await client.post(f"{BUILD_WORKER_URL}/build", files={"file": ("workspace.zip", changed_archive.getvalue(), "application/zip")})
                    if response.status_code == 200:
                        preview_id = response.json()["build_id"]
                        artifact_id = await bucket.upload_from_stream(f"{uuid4().hex}.zip", changed_archive.getvalue(), metadata={"user_id": user["_id"], "kind": "version-workspace"})
                        break
                    try:
                        build_error = str(response.json().get("detail", "Workspace build failed"))[:3000]
                    except (ValueError, AttributeError):
                        build_error = "Workspace build failed"
                    if attempt == 0:
                        repair = await workflow.ainvoke({"task": "repair", "profile": profile, "current": {"files": {**safe_files, **generated}}, "build_error": build_error})
                        repair_result = repair.get("result", {})
                        if not repair_result.get("files"):
                            break
                        generated.update(repair_result["files"])
                        changes.extend(repair_result.get("changes", []))
            if not preview_id:
                raise HTTPException(422, build_error)
            changes.append("React production build passed")
        except httpx.ConnectError as exc:
            raise HTTPException(503, "Build worker unavailable; start the local Docker services") from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(504, "Workspace build exceeded the time limit") from exc
    else:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(f"{BUILD_WORKER_URL}/publish", data={"html": portfolio_html(profile, payload.page, page_content)})
            if response.status_code != 200:
                raise HTTPException(503, "Preview service could not publish the portfolio")
            preview_id = response.json()["build_id"]
        except httpx.ConnectError as exc:
            raise HTTPException(503, "Preview worker unavailable; start the local Docker services") from exc
    version_id = ObjectId()
    mode_label = {"sync": "Profile sync", "page": f"{payload.page or 'Home'} page evolution", "workspace": "Workspace evolution"}[payload.mode]
    version = {"_id": version_id, "user_id": user["_id"], "label": mode_label, "mode": payload.mode, "created_at": datetime.now(timezone.utc), "status": "pending", "changes": changes, "profile_snapshot": profile, "page": payload.page, "page_content": page_content, "preview_id": preview_id, "workspace_file_id": artifact_id}
    await db.versions.insert_one(version)
    public_version = version_out(version)
    return {"id": str(version_id), "status": "pending_review", "message": "Proposal generated. Review it before activation.", "version": public_version}


@app.get("/api/versions", response_model=list[VersionOut])
async def list_versions(user: dict = Depends(current_user)):
    docs = await db.versions.find({"user_id": user["_id"]}).sort("created_at", -1).limit(50).to_list(50)
    return [version_out(doc) for doc in docs]


@app.get("/api/versions/{version_id}/diff")
async def version_diff(version_id: str, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    version = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not version:
        raise HTTPException(404, "Version not found")
    previous = await db.versions.find_one({"user_id": user["_id"], "created_at": {"$lt": version["created_at"]}}, sort=[("created_at", -1)])
    return {"version": version_out(version), "previousVersion": version_out(previous) if previous else None, "changes": version["changes"], "profileChanges": profile_changes(previous.get("profile_snapshot", {}) if previous else {}, version.get("profile_snapshot", {}))}


@app.post("/api/versions/{version_id}/approve", response_model=VersionOut)
async def approve_version(version_id: str, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    doc = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not doc:
        raise HTTPException(404, "Version not found")
    if doc["status"] != "pending":
        raise HTTPException(409, "Only a pending proposal can be approved")
    active_modes = ["sync"] if doc["mode"] == "sync" else ["page", "workspace"]
    await db.versions.update_many({"user_id": user["_id"], "mode": {"$in": active_modes}, "status": "active"}, {"$set": {"status": "archived"}})
    await db.versions.update_one({"_id": doc["_id"]}, {"$set": {"status": "active"}})
    doc["status"] = "active"
    return version_out(doc)


@app.post("/api/versions/{version_id}/rollback", response_model=VersionOut)
async def rollback_version(version_id: str, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    source = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not source:
        raise HTTPException(404, "Version not found")
    active_modes = ["sync"] if source["mode"] == "sync" else ["page", "workspace"]
    await db.versions.update_many({"user_id": user["_id"], "mode": {"$in": active_modes}, "status": "active"}, {"$set": {"status": "archived"}})
    new_version = {key: value for key, value in source.items() if key not in ("_id",)}
    new_version.update({"_id": ObjectId(), "created_at": datetime.now(timezone.utc), "status": "active", "label": f"Restore · {source['label']}", "changes": [f"Restored from {source['label']}"]})
    if source.get("version_number") is not None:
        new_number = await next_version_number(user["_id"])
        new_version.update({"version_number": new_number, "label": f"Restore · v{new_number}"})
        old_rows = await db.portfolio_variables.find({"user_id": user["_id"], "version_id": source["_id"]}, {"_id": 0}).to_list(100)
        restored_rows = [{**row, "version_id": new_version["_id"], "version": f"v{new_number}", "created_at": datetime.now(timezone.utc)} for row in old_rows]
        if restored_rows:
            await db.portfolio_variables.insert_many(restored_rows)
    await db.versions.insert_one(new_version)
    return version_out(new_version)


@app.get("/api/preview/{version_id}")
async def preview(version_id: str, user: dict = Depends(current_user)):
    if not ObjectId.is_valid(version_id):
        raise HTTPException(404, "Version not found")
    version = await db.versions.find_one({"_id": ObjectId(version_id), "user_id": user["_id"]})
    if not version:
        raise HTTPException(404, "Version not found")
    return {"version": version_out(version), "profile": version.get("profile_snapshot", {}), "page": version.get("page"), "preview": version_out(version).get("previewUrl")}
