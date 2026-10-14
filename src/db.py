"""
Camada DuckDB. Um banco de verdade (arquivo .duckdb), não um dict em memória —
o ponto do exercício é ver o agente consultando uma fonte de dados externa,
igual faria num pipeline de verdade.
"""

from __future__ import annotations

import json
from pathlib import Path

import duckdb

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "vagas.duckdb"

# Dataset mínimo de vagas pra demonstração. Em um projeto real isso viria
# de uma tabela Silver/Gold já populada pelo pipeline.
SEED_VAGAS = [
    {
        "cargo": "engenheiro de dados",
        "skills_requeridas": ["python", "sql", "duckdb", "etl"],
        "anos_experiencia_min": 2,
    },
    {
        "cargo": "analista de dados",
        "skills_requeridas": ["sql", "power bi", "dax"],
        "anos_experiencia_min": 1,
    },
    {
        "cargo": "desenvolvedor backend",
        "skills_requeridas": ["python", "api", "docker"],
        "anos_experiencia_min": 2,
    },
]


def seed_database(force: bool = False) -> None:
    """Cria o arquivo .duckdb e popula a tabela `vagas` se ainda não existir."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists() and not force:
        return
    if DB_PATH.exists():
        DB_PATH.unlink()

    con = duckdb.connect(str(DB_PATH))
    con.execute(
        """
        CREATE TABLE vagas (
            cargo VARCHAR PRIMARY KEY,
            skills_requeridas VARCHAR,  -- JSON-encoded list[str]
            anos_experiencia_min INTEGER
        )
        """
    )
    for vaga in SEED_VAGAS:
        con.execute(
            "INSERT INTO vagas VALUES (?, ?, ?)",
            [vaga["cargo"], json.dumps(vaga["skills_requeridas"]), vaga["anos_experiencia_min"]],
        )
    con.close()


def get_job_profile(cargo: str) -> dict | None:
    """
    Busca o perfil de vaga mais parecido com `cargo` (case-insensitive,
    substring). Retorna dict pronto pra virar `JobProfile`, ou None.
    """
    seed_database()
    con = duckdb.connect(str(DB_PATH), read_only=True)
    try:
        row = con.execute(
            "SELECT cargo, skills_requeridas, anos_experiencia_min FROM vagas "
            "WHERE lower(cargo) LIKE '%' || lower(?) || '%' OR lower(?) LIKE '%' || lower(cargo) || '%' "
            "LIMIT 1",
            [cargo, cargo],
        ).fetchone()
    finally:
        con.close()

    if row is None:
        return None

    return {
        "cargo": row[0],
        "skills_requeridas": json.loads(row[1]),
        "anos_experiencia_min": row[2],
    }
