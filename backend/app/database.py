from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

if settings.database_url:
    DATABASE_URL = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://", 1
    )
else:
    DATABASE_URL = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
    )

engine = create_async_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=5)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def init_extensions_and_schema() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        if settings.enable_apache_age:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS age"))
        await conn.run_sync(Base.metadata.create_all)
        await _ensure_graph_schema_upgrades(conn)


async def init_pgvector() -> None:
    await init_extensions_and_schema()


async def _ensure_graph_schema_upgrades(conn) -> None:
    graph_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes (node_type)",
        "CREATE INDEX IF NOT EXISTS idx_graph_nodes_source ON graph_nodes (source_type, source_id)",
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_from_node ON graph_edges (from_node_id)",
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_to_node ON graph_edges (to_node_id)",
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges (source_type, source_id)",
        "CREATE INDEX IF NOT EXISTS idx_graph_edges_relation ON graph_edges (relation_type)",
    ]
    for statement in graph_indexes:
        await conn.execute(text(statement))

    await conn.execute(
        text(
            """
            DO $$
            BEGIN
                IF to_regclass('public.graph_edges') IS NOT NULL THEN
                    DELETE FROM graph_edges
                    WHERE id IN (
                        SELECT id
                        FROM (
                            SELECT
                                id,
                                row_number() OVER (
                                    PARTITION BY
                                        from_node_id,
                                        relation_type,
                                        to_node_id,
                                        source_type,
                                        source_id
                                    ORDER BY updated_at DESC, created_at DESC, id DESC
                                ) AS duplicate_rank
                            FROM graph_edges
                        ) ranked
                        WHERE duplicate_rank > 1
                    );

                    IF EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'uq_graph_edge_fact'
                          AND conrelid = 'public.graph_edges'::regclass
                          AND pg_get_constraintdef(oid) NOT ILIKE '%NULLS NOT DISTINCT%'
                    ) THEN
                        ALTER TABLE graph_edges DROP CONSTRAINT uq_graph_edge_fact;
                        ALTER TABLE graph_edges
                            ADD CONSTRAINT uq_graph_edge_fact
                            UNIQUE NULLS NOT DISTINCT (
                                from_node_id,
                                relation_type,
                                to_node_id,
                                source_type,
                                source_id
                            );
                    END IF;
                END IF;
            END $$;
            """
        )
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
