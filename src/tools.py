"""
As "ferramentas" (tools) que o agente pode chamar.

Cada função aqui é uma função Python comum — o que as torna "tools" é só
estarem registradas no Agent (ver agent.py) com `@agent.tool_plain`, o que
expõe sua assinatura como um schema JSON que o modelo (ou o fake_llm) decide
quando e como chamar.

Importante: aqui a "extração do currículo" é heurística (regex), não um
segundo LLM. Numa versão de produção, essa função provavelmente seria ela
mesma uma chamada de LLM com saída estruturada — mas isso exigiria uma
API key pra rodar, e o objetivo deste repo é demonstrar o *loop do agente*,
não um extrator de currículo robusto.
"""

from __future__ import annotations

import re
from pathlib import Path

from .db import get_job_profile
from .models import CandidateData, JobProfile, ScoreResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _ler_texto(caminho_arquivo: str) -> str:
    path = Path(caminho_arquivo)
    if not path.is_absolute():
        path = PROJECT_ROOT / path

    if not path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {path}")

    if path.suffix.lower() == ".pdf":
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            return "\n".join(page.extract_text() or "" for page in pdf.pages)

    return path.read_text(encoding="utf-8")


def _campo(texto: str, rotulo: str) -> str:
    match = re.search(rf"{rotulo}\s*:\s*(.+)", texto, flags=re.IGNORECASE)
    if not match:
        raise ValueError(f"Campo '{rotulo}' não encontrado no currículo")
    return match.group(1).strip()


def ler_curriculo(caminho_arquivo: str) -> dict:
    """
    Lê um currículo (.pdf ou .txt) e extrai nome, cargo pretendido,
    anos de experiência e skills.

    O arquivo de exemplo (data/curriculo_ana.txt) segue um formato simples
    de rótulos ("Nome:", "Cargo pretendido:", etc.) pra manter a extração
    determinística sem depender de um LLM.
    """
    texto = _ler_texto(caminho_arquivo)

    nome = _campo(texto, "Nome")
    cargo_pretendido = _campo(texto, "Cargo pretendido")
    anos_experiencia = int(re.search(r"\d+", _campo(texto, "Experiência")).group())
    skills_raw = _campo(texto, "Skills")
    skills = [s.strip().lower() for s in skills_raw.split(",") if s.strip()]

    candidato = CandidateData(
        nome=nome,
        cargo_pretendido=cargo_pretendido,
        anos_experiencia=anos_experiencia,
        skills=skills,
    )
    return candidato.model_dump()


def calcular_score(
    nome: str,
    cargo_pretendido: str,
    anos_experiencia: int,
    skills: list[str],
) -> dict:
    """
    Compara os dados do candidato com o perfil da vaga (consultado no DuckDB)
    e calcula um score de 0 a 100.

    Fórmula (simples de propósito, pra ficar fácil de explicar numa
    entrevista): 70% do peso vem do match de skills, 30% vem de ter
    experiência igual ou acima do mínimo exigido pela vaga.
    """
    perfil = get_job_profile(cargo_pretendido)

    if perfil is None:
        resultado = ScoreResult(
            nome=nome,
            cargo=cargo_pretendido,
            score=0.0,
            skills_match=[],
            skills_faltando=[],
            justificativa=f"Nenhuma vaga cadastrada compatível com '{cargo_pretendido}'.",
        )
        return resultado.model_dump()

    job = JobProfile(**perfil)
    skills_candidato = {s.lower() for s in skills}
    skills_requeridas = {s.lower() for s in job.skills_requeridas}

    skills_match = sorted(skills_candidato & skills_requeridas)
    skills_faltando = sorted(skills_requeridas - skills_candidato)

    skill_score = (len(skills_match) / len(skills_requeridas) * 70) if skills_requeridas else 70.0
    exp_score = min(anos_experiencia / max(job.anos_experiencia_min, 1), 1.0) * 30
    score = round(skill_score + exp_score, 1)

    justificativa = (
        f"{len(skills_match)}/{len(skills_requeridas)} skills exigidas presentes "
        f"para '{job.cargo}'; {anos_experiencia} anos de experiência "
        f"(mínimo exigido: {job.anos_experiencia_min})."
    )

    resultado = ScoreResult(
        nome=nome,
        cargo=job.cargo,
        score=score,
        skills_match=skills_match,
        skills_faltando=skills_faltando,
        justificativa=justificativa,
    )
    return resultado.model_dump()
