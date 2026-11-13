import json
import logging
import asyncio
from pathlib import Path
from typing import Protocol, TypedDict

from langgraph.graph import END, StateGraph

from .config import settings


class AgentState(TypedDict, total=False):
    task: str
    text: str
    profile: dict
    mode: str
    page: str
    current: dict
    build_error: str
    definitions: list[dict]
    records: list[dict]
    result: dict


async def _invoke(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            # Gemini can temporarily return 503 when a model is overloaded.
            # Retry once against the lower-cost Flash-Lite model in that case.
            is_unavailable = getattr(exc, "code", None) == 503 or "503 UNAVAILABLE" in str(exc)
            if not is_unavailable or settings.gemini_fallback_model == settings.gemini_model:
                raise
            logging.getLogger(__name__).warning(
                "Gemini model %s unavailable; retrying with %s",
                settings.gemini_model,
                settings.gemini_fallback_model,
            )
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=settings.gemini_fallback_model,
                contents=prompt,
            )
        return response.text
    except Exception:
        # Provider outages, invalid credentials, and rate limits should not
        # prevent users from reviewing and editing the generated JSON shape.
        logging.getLogger(__name__).exception("Gemini request failed")
        return None


class ModelProvider(Protocol):
    async def complete(self, prompt: str) -> str | None: ...


class GeminiProvider:
    async def complete(self, prompt: str) -> str | None:
        return await _invoke(prompt)


provider: ModelProvider = GeminiProvider()


def _blank_like(sample):
    if isinstance(sample, dict):
        return {key: _blank_like(value) for key, value in sample.items()}
    if isinstance(sample, list):
        return []
    if isinstance(sample, str):
        return ""
    return None


async def variable_node(state: AgentState) -> AgentState:
    definitions = state.get("definitions", [])
    schema = [{"key": item["key"], "description": item["description"], "example_response_shape": item.get("sample_json")} for item in definitions]
    raw = await provider.complete(
        "Extract values from the resume for a developer's existing portfolio database. Return one JSON object whose keys exactly match the requested variable keys. "
        "Each value must match its example response shape when supplied, otherwise choose a useful JSON type from the key and description. "
        "Never invent facts; use null, an empty string, or an empty list for unsupported details. Preserve all relevant resume items in arrays. "
        "Definitions: " + json.dumps(schema, ensure_ascii=False) + "\nResume text:\n" + state.get("text", "")[:24000]
    )
    values = {}
    parsed_ok = False
    if raw:
        try:
            parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```"))
            if isinstance(parsed, dict) and isinstance(parsed.get("values"), dict):
                parsed = parsed["values"]
            if isinstance(parsed, dict):
                values = {item["key"]: parsed[item["key"]] for item in definitions if item["key"] in parsed}
                parsed_ok = len(values) == len(definitions)
        except (json.JSONDecodeError, TypeError):
            values = {}
    rows = []
    for item in definitions:
        key = item["key"]
        rows.append({**item, "value": values.get(key, _blank_like(item.get("sample_json")))})
    return {"result": {"variables": rows, "ai_enabled": parsed_ok}}


async def extract_node(state: AgentState) -> AgentState:
    raw = await provider.complete("Extract the resume into JSON with name, headline, email, location, about, skills (array), experience (array of company/role/period), projects (array of name/description/stack). Do not invent facts. Resume text:\n" + state["text"][:24000])
    if raw:
        cleaned = raw.strip().removeprefix("```json").removesuffix("```").strip()
        try:
            return {"profile": json.loads(cleaned)}
        except json.JSONDecodeError:
            pass
    text = state["text"]
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return {"profile": {"name": lines[0][:100] if lines else "", "headline": "", "email": "", "location": "", "about": " ".join(lines[1:4])[:500], "skills": [], "experience": [], "projects": []}}


async def sync_node(state: AgentState) -> AgentState:
    profile = state.get("profile", {})
    changes = []
    for field, label in (("skills", "skills"), ("experience", "experience entries"), ("projects", "projects")):
        if profile.get(field):
            changes.append(f"Synced {len(profile[field])} {label}")
    return {"result": {"changes": changes or ["Refreshed portfolio profile content"]}}


async def page_node(state: AgentState) -> AgentState:
    page = state.get("page") or "Home"
    raw = await provider.complete("You are evolving the content of one developer portfolio page. Return JSON only: {changes:[short factual edits], content:{headline:string, intro:string, about:string}}. Use only the supplied profile facts, do not invent claims. Preserve the meaning of existing facts. Page: " + page + ". Profile: " + json.dumps(state.get("profile", {}), ensure_ascii=False) + ". Existing page context: " + json.dumps(state.get("current", {}), ensure_ascii=False)[:12000])
    changes = [f"Updated {page} page with current profile details", "Improved content hierarchy and responsive presentation"]
    content = {}
    if raw:
        try:
            candidate = json.loads(raw.strip().removeprefix("```json").removesuffix("```"))
            if isinstance(candidate.get("changes"), list):
                changes = [str(item)[:160] for item in candidate["changes"][:8]]
            if isinstance(candidate.get("content"), dict):
                content = {key: str(value)[:500] for key, value in candidate["content"].items() if key in ("headline", "intro", "about") and isinstance(value, str)}
        except (json.JSONDecodeError, AttributeError):
            pass
    return {"result": {"changes": changes, "content": content}}


async def database_node(state: AgentState) -> AgentState:
    records = state.get("records", [])
    mode = state.get("mode", "sync")
    if mode == "page":
        skill = (Path(__file__).parent / "skills" / "page-redesign.md").read_text(encoding="utf-8")
        instruction = (
            "Apply the portfolio page redesign skill below to every supplied page source. "
            "Return JSON with updates, an array of {key, description, response}; response must be the complete updated source code. "
            "Preserve each page key and return exactly one update for each input record. "
            "Use only factual resume details.\nSKILL:\n" + skill
        )
    else:
        instruction = (
            "Update the supplied portfolio database values using the latest resume, each key, its description, and its previous response. "
            "Return JSON with updates, an array of {key, description, response}. Keep response JSON types and shapes consistent with each previous response. "
            "Preserve useful existing facts, change only facts supported by the resume, and return exactly one row per input key. "
            "Do not invent facts.\n"
        )
    raw = await provider.complete(
        instruction + "\nLATEST RESUME:\n" + state.get("text", "")[:24000] +
        "\nINPUT RECORDS:\n" + json.dumps(records, ensure_ascii=False, default=str)[:50000]
    )
    if not raw:
        return {"result": {"updates": [], "ai_enabled": False, "changes": []}}
    try:
        parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```").strip())
        updates = parsed.get("updates", [])
        allowed = {row["key"] for row in records}
        normalized = [
            {"key": item["key"], "description": str(item.get("description", ""))[:500], "response": item["response"]}
            for item in updates if isinstance(item, dict) and item.get("key") in allowed and "response" in item
        ]
        if len(normalized) != len(records) or len({item["key"] for item in normalized}) != len(records):
            raise ValueError("The model did not return exactly one update for each selected key")
        changes = parsed.get("changes", [])
        return {"result": {"updates": normalized, "ai_enabled": True, "changes": [str(item)[:180] for item in changes[:20]] if isinstance(changes, list) else []}}
    except (json.JSONDecodeError, AttributeError, KeyError, TypeError, ValueError):
        logging.getLogger(__name__).exception("Database update model returned an invalid proposal")
        return {"result": {"updates": [], "ai_enabled": False, "changes": []}}


async def workspace_node(state: AgentState) -> AgentState:
    files = state.get("current", {}).get("files", {})
    raw = await provider.complete(
        "Review this React workspace and propose a small factual update using the supplied profile. "
        "Return JSON only with keys files (object of changed existing relative paths to full replacement text) "
        "and changes (short list). Never edit package manifests, lock files, config, or public assets. "
        "Do not invent profile facts. Keep edits limited to at most 3 existing source files. "
        "PROFILE: " + json.dumps(state.get("profile", {}), ensure_ascii=False) +
        "\nSOURCE FILES: " + json.dumps(files, ensure_ascii=False)[:18000]
    )
    if raw:
        try:
            parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```"))
            edited = parsed.get("files", {})
            allowed = {name: content[:50000] for name, content in list(edited.items())[:3] if name in files and isinstance(content, str)}
            changes = parsed.get("changes", [])
            if allowed:
                return {"result": {"files": allowed, "changes": [str(item)[:160] for item in changes[:8]] or ["Updated selected React components"]}}
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
    return {"result": {"files": {}, "changes": ["Workspace analyzed", "No safe source changes could be produced", "Add a Gemini API key to enable code evolution"]}}


async def repair_node(state: AgentState) -> AgentState:
    files = state.get("current", {}).get("files", {})
    raw = await provider.complete(
        "Repair this React build failure. Return JSON only with files (object of changed existing relative paths to full replacement text) "
        "and changes (short list). Fix only the reported error, preserve profile facts, do not edit manifests, lock files, or config, "
        "and change at most 3 existing files. Build error: " + state.get("build_error", "Unknown build error")[:3000] +
        "\nPROFILE: " + json.dumps(state.get("profile", {}), ensure_ascii=False) +
        "\nSOURCE FILES: " + json.dumps(files, ensure_ascii=False)[:18000]
    )
    if raw:
        try:
            parsed = json.loads(raw.strip().removeprefix("```json").removesuffix("```"))
            edited = parsed.get("files", {})
            allowed = {name: content[:50000] for name, content in list(edited.items())[:3] if name in files and isinstance(content, str)}
            changes = parsed.get("changes", [])
            if allowed:
                return {"result": {"files": allowed, "changes": [str(item)[:160] for item in changes[:8]] or ["Repaired the reported build issue"]}}
        except (json.JSONDecodeError, AttributeError, TypeError):
            pass
    return {"result": {"files": {}, "changes": []}}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("extract", extract_node)
    graph.add_node("sync", sync_node)
    graph.add_node("page_agent", page_node)
    graph.add_node("workspace", workspace_node)
    graph.add_node("repair", repair_node)
    graph.add_node("variable_agent", variable_node)
    graph.add_node("database_update", database_node)
    graph.set_conditional_entry_point(lambda state: state["task"], {"extract": "extract", "sync": "sync", "page": "page_agent", "workspace": "workspace", "repair": "repair", "variables": "variable_agent", "database": "database_update"})
    graph.add_edge("extract", END)
    graph.add_edge("sync", END)
    graph.add_edge("page_agent", END)
    graph.add_edge("workspace", END)
    graph.add_edge("repair", END)
    graph.add_edge("variable_agent", END)
    graph.add_edge("database_update", END)
    return graph.compile()


workflow = build_graph()
