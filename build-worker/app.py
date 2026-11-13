import asyncio
import io
import json
import os
import signal
import shutil
import tempfile
import uuid
import zipfile
from pathlib import Path, PurePosixPath

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(title="PortfolioPilot isolated build worker")
PREVIEWS = Path("/data/previews")
MAX_BYTES = 45 * 1024 * 1024
BUILD_UID = 65534
BUILD_LOCK = asyncio.Lock()


@app.on_event("startup")
async def lock_preview_storage():
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    PREVIEWS.chmod(0o700)


def kill_build_processes() -> None:
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "status").read_text()
            uid_line = next(line for line in status.splitlines() if line.startswith("Uid:"))
            if int(uid_line.split()[1]) == BUILD_UID:
                os.kill(int(entry.name), signal.SIGKILL)
        except (OSError, StopIteration, ValueError, ProcessLookupError):
            continue


async def run_limited(command: list[str], cwd: Path, env: dict, seconds: int) -> bytes:
    process = await asyncio.create_subprocess_exec(*command, cwd=cwd, env=env, user=BUILD_UID, group=BUILD_UID, extra_groups=[],
        start_new_session=True, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT)
    captured = bytearray()

    async def drain_output():
        while chunk := await process.stdout.read(8192):
            captured.extend(chunk)
            if len(captured) > 256_000:
                del captured[:-256_000]

    reader = asyncio.create_task(drain_output())
    try:
        await asyncio.wait_for(process.wait(), timeout=seconds)
    except asyncio.TimeoutError as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        kill_build_processes()
        await process.wait()
        await reader
        raise HTTPException(504, "Workspace build exceeded its time limit") from exc
    finally:
        kill_build_processes()
    await reader
    if process.returncode:
        raise HTTPException(422, captured.decode(errors="replace")[-2000:] or "Workspace command failed")
    return bytes(captured)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/build")
async def build(file: UploadFile = File(...)):
    async with BUILD_LOCK:
        return await build_locked(file)


async def build_locked(file: UploadFile):
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "Workspace exceeds build worker limit")
    build_id = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="portfolio-build-") as temp:
        root = Path(temp)
        job_uid = BUILD_UID
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if len(archive.infolist()) > 2500:
                    raise HTTPException(413, "Workspace contains too many files")
                total_size = 0
                for entry in archive.infolist():
                    path = PurePosixPath(entry.filename.replace("\\", "/"))
                    if path.is_absolute() or ".." in path.parts:
                        raise HTTPException(422, "Workspace contains an unsafe path")
                    total_size += entry.file_size
                    if total_size > 120 * 1024 * 1024:
                        raise HTTPException(413, "Uncompressed workspace exceeds the build limit")
                    if entry.is_dir():
                        continue
                    target = root.joinpath(*path.parts)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(entry))
            for directory in (path for path in root.rglob("*") if path.is_dir()):
                directory.chmod(0o755)
        except zipfile.BadZipFile as exc:
            raise HTTPException(422, "Invalid workspace ZIP") from exc

        packages = list(root.rglob("package.json"))
        packages = [path for path in packages if "node_modules" not in path.parts]
        if not packages:
            raise HTTPException(422, "No package.json found")
        package_file = packages[0]
        project = package_file.parent
        project.chmod(0o777)
        cache_dir = project / ".npm-cache"
        home_dir = project / ".build-home"
        cache_dir.mkdir(exist_ok=True)
        home_dir.mkdir(exist_ok=True)
        for path in root.rglob("*"):
            os.chown(path, job_uid, job_uid)
        root.chmod(0o711)
        project.chmod(0o777)
        try:
            manifest = json.loads(package_file.read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(422, "Invalid package.json") from exc
        dependencies = {**manifest.get("dependencies", {}), **manifest.get("devDependencies", {})}
        if "react" not in dependencies or "react-dom" not in dependencies:
            raise HTTPException(422, "This project does not appear to use React")
        if not manifest.get("scripts", {}).get("build"):
            raise HTTPException(422, "No build script found in package.json")
        manifest_manager = str(manifest.get("packageManager", "")).split("@")[0]
        if manifest_manager not in ("npm", "pnpm", "yarn"):
            manifest_manager = "pnpm" if (project / "pnpm-lock.yaml").exists() else "yarn" if (project / "yarn.lock").exists() else "npm"
        frozen = any((project / lock).exists() for lock in ("package-lock.json", "npm-shrinkwrap.json", "pnpm-lock.yaml", "yarn.lock"))
        try:
            env = {"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "HOME": str(home_dir), "npm_config_cache": str(cache_dir), "CI": "true"}
            if manifest_manager == "pnpm":
                install_command = ["corepack", "pnpm", "install", "--ignore-scripts"] + (["--frozen-lockfile"] if frozen else [])
                build_command = ["corepack", "pnpm", "run", "build"]
            elif manifest_manager == "yarn":
                install_command = ["corepack", "yarn", "install", "--ignore-scripts"]
                build_command = ["corepack", "yarn", "build"]
            else:
                install_command = ["npm", "ci" if frozen else "install", "--ignore-scripts", "--no-audit", "--no-fund"]
                build_command = ["npm", "run", "build"]
            await run_limited(install_command, project, env, 100)
            await run_limited(build_command, project, env, 90)
        except HTTPException:
            raise
        except FileNotFoundError as exc:
            raise HTTPException(503, "Node.js/npm is unavailable in the build worker") from exc

        output_dir = next((project / name for name in ("dist", "build", "out") if (project / name).is_dir() and not (project / name).is_symlink()), None)
        if not output_dir:
            raise HTTPException(422, "Build passed but no dist, build, or out folder was created")
        try:
            output_dir.resolve().relative_to(project.resolve())
        except ValueError as exc:
            raise HTTPException(422, "Build output points outside the workspace") from exc
        destination = PREVIEWS / build_id
        destination.mkdir(parents=True, exist_ok=True)
        destination.chmod(0o700)
        total_output = 0
        for current, dirs, files in os.walk(output_dir, followlinks=False):
            current_path = Path(current)
            safe_dirs = []
            for dirname in dirs:
                entry = current_path / dirname
                if entry.is_symlink():
                    raise HTTPException(422, "Build output contains a symbolic link")
                safe_dirs.append(dirname)
            dirs[:] = safe_dirs
            relative = current_path.relative_to(output_dir)
            target_dir = destination / relative
            target_dir.mkdir(parents=True, exist_ok=True)
            for filename in files:
                source = current_path / filename
                if source.is_symlink() or not source.is_file():
                    raise HTTPException(422, "Build output contains an unsafe file")
                total_output += source.stat().st_size
                if total_output > 100 * 1024 * 1024:
                    raise HTTPException(413, "Static build output is too large")
                shutil.copyfile(source, target_dir / filename)
    return {"build_id": build_id, "preview_url": f"http://localhost:8001/preview/{build_id}/", "message": "Static build succeeded"}


@app.post("/publish")
async def publish(html: str = Form(...)):
    if len(html.encode("utf-8")) > 2 * 1024 * 1024:
        raise HTTPException(413, "Generated preview is too large")
    build_id = uuid.uuid4().hex
    destination = PREVIEWS / build_id
    destination.mkdir(parents=True, exist_ok=False)
    destination.chmod(0o700)
    (destination / "index.html").write_text(html, encoding="utf-8")
    return {"build_id": build_id, "preview_url": f"http://localhost:8001/preview/{build_id}/", "message": "Portfolio preview generated"}


@app.get("/preview/{build_id}/{asset_path:path}")
async def preview(build_id: str, asset_path: str = ""):
    if not build_id.isalnum() or len(build_id) != 32:
        raise HTTPException(404, "Preview not found")
    base = (PREVIEWS / build_id).resolve()
    requested = (base / asset_path).resolve()
    if base not in requested.parents and requested != base:
        raise HTTPException(404, "Preview not found")
    target = requested if requested.is_file() else requested / "index.html"
    if not target.is_file():
        target = base / "index.html"
    if not target.is_file():
        raise HTTPException(404, "Preview not found")
    return FileResponse(target)
