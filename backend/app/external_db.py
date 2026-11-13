"""Small, explicit bridge to a user's relational key/response table."""

import json
from typing import Any

from sqlalchemy import JSON, MetaData, Table, URL, create_engine, select


def _table(connection, config: dict[str, Any]) -> Table:
    table = Table(config["table"], MetaData(), schema=config.get("schema") or None, autoload_with=connection)
    mapping = {
        "key": config["key_column"],
        "response": config["response_column"],
        "description": config["description_column"],
        "version": config["version_column"],
    }
    columns = {column.name for column in table.columns}
    if any(name not in columns for name in mapping.values()):
        raise ValueError("A mapped column was not found in the selected table")
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("Map key, response, description, and version to different columns")
    return table


def _engine(config: dict[str, Any]):
    driver = "postgresql+psycopg" if config["engine"] == "postgresql" else "mysql+pymysql"
    query = {"sslmode": "require"} if config.get("ssl") and config["engine"] == "postgresql" else {}
    connect_args = {"connect_timeout": 10}
    if config.get("ssl") and config["engine"] == "mysql":
        connect_args["ssl"] = {}
    url = URL.create(
        drivername=driver,
        username=config["username"],
        password=config["password"],
        host=config["host"],
        port=config["port"],
        database=config["database"],
        query=query,
    )
    return create_engine(url, pool_pre_ping=True, pool_timeout=10, connect_args=connect_args)


def _version_order(value: Any):
    text = str(value if value is not None else "")
    digits = "".join(char for char in text if char.isdigit())
    return (1, int(digits)) if digits else (0, text)


def read_records(config: dict[str, Any]) -> list[dict[str, Any]]:
    engine = _engine(config)
    try:
        with engine.connect() as connection:
            table = _table(connection, config)
            names = [config[name + "_column"] for name in ("key", "response", "description", "version")]
            rows = connection.execute(select(*(table.c[name] for name in names))).mappings().all()
            records = []
            response_is_json = isinstance(table.c[names[1]].type, JSON)
            for row in rows:
                response = row[names[1]]
                if not response_is_json and isinstance(response, str):
                    try:
                        response = json.loads(response)
                    except ValueError:
                        pass
                records.append({"key": row[names[0]], "response": response, "description": row[names[2]] or "", "version": row[names[3]]})
            if not records:
                return []
            latest = max((row["version"] for row in records), key=_version_order)
            return [row for row in records if row["version"] == latest]
    finally:
        engine.dispose()


def verify_connection(config: dict[str, Any]) -> None:
    engine = _engine(config)
    try:
        with engine.connect() as connection:
            table = _table(connection, config)
            connection.execute(select(table.c[config["key_column"]]).limit(1)).first()
    finally:
        engine.dispose()


def publish_records(config: dict[str, Any], records: list[dict[str, Any]], expected_version: Any) -> Any:
    engine = _engine(config)
    try:
        with engine.begin() as connection:
            table = _table(connection, config)
            names = [config[name + "_column"] for name in ("key", "response", "description", "version")]
            existing = connection.execute(select(table.c[names[3]])).scalars().all()
            current = max(existing, key=_version_order) if existing else None
            if current != expected_version:
                raise RuntimeError("The connected table changed after you loaded it. Reload the rows before publishing.")
            next_number = max((_version_order(value)[1] for value in existing), default=0) + 1
            if current is None or isinstance(current, (int, float)):
                next_version: Any = next_number
            elif str(current).isdigit():
                next_version = str(next_number)
            else:
                next_version = f"v{next_number}"
            values = []
            response_is_json = isinstance(table.c[names[1]].type, JSON)
            seen = set()
            for record in records:
                key = str(record.get("key", "")).strip()
                if not key or key in seen:
                    raise ValueError("Every published row needs a unique, non-empty key")
                seen.add(key)
                response = record.get("response")
                if not response_is_json and not isinstance(response, str):
                    response = json.dumps(response, ensure_ascii=False)
                values.append({names[0]: key, names[1]: response, names[2]: str(record.get("description", "")), names[3]: next_version})
            connection.execute(table.insert(), values)
            return next_version
    finally:
        engine.dispose()
