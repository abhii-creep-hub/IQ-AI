from sqlalchemy.engine import make_url


def normalize_database_url(database_url: str) -> str:
    """Adapt Neon/Postgres URLs to the asyncpg driver used by this project."""
    url = make_url(database_url)
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    # asyncpg uses `ssl`; `channel_binding` is a libpq option and isn't accepted.
    query.pop("channel_binding", None)
    if sslmode and "ssl" not in query:
        query["ssl"] = sslmode
    return url.set(query=query).render_as_string(hide_password=False)
