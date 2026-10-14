"""
Modelos Pydantic usados pelo agente.

Isso não é "decoração" — é o motivo de o Pydantic AI se chamar assim: cada
tool declara o formato exato do que espera e do que devolve, e a validação
acontece sozinha. Se o LLM (ou, aqui, o fake_llm) mandar um argumento errado,
o erro aparece aqui, não em produção.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class CandidateData(BaseModel):
    """Dados extraídos do currículo pela tool `ler_curriculo`."""

    nome: str
    cargo_pretendido: str
    anos_experiencia: int = Field(ge=0)
    skills: list[str]


class JobProfile(BaseModel):
    """Perfil de vaga, como está cadastrado no DuckDB."""

    cargo: str
    skills_requeridas: list[str]
    anos_experiencia_min: int = Field(ge=0)


class ScoreResult(BaseModel):
    """Resultado final devolvido pela tool `calcular_score`."""

    nome: str
    cargo: str
    score: float = Field(ge=0, le=100)
    skills_match: list[str]
    skills_faltando: list[str]
    justificativa: str
