"""
Testes das tools isoladas — não precisam de agente nem de LLM.
Rodar com: python -m pytest tests/ -v
"""

from src.tools import calcular_score, ler_curriculo


def test_ler_curriculo_extrai_campos_corretamente():
    dados = ler_curriculo("data/curriculo_ana.txt")

    assert dados["nome"] == "Ana Ribeiro"
    assert dados["cargo_pretendido"] == "Engenheiro de Dados"
    assert dados["anos_experiencia"] == 3
    assert "python" in dados["skills"]
    assert "duckdb" in dados["skills"]


def test_calcular_score_candidato_forte():
    resultado = calcular_score(
        nome="Ana Ribeiro",
        cargo_pretendido="Engenheiro de Dados",
        anos_experiencia=3,
        skills=["python", "sql", "duckdb", "etl", "docker"],
    )

    assert resultado["score"] > 90
    assert "python" in resultado["skills_match"]
    assert resultado["skills_faltando"] == []


def test_calcular_score_candidato_fraco():
    resultado = calcular_score(
        nome="Bruno Alves",
        cargo_pretendido="Analista de Dados",
        anos_experiencia=0,
        skills=["excel", "power bi"],
    )

    assert resultado["score"] < 50
    assert "sql" in resultado["skills_faltando"]
    assert "dax" in resultado["skills_faltando"]


def test_calcular_score_vaga_inexistente():
    resultado = calcular_score(
        nome="Carlos",
        cargo_pretendido="Astronauta",
        anos_experiencia=10,
        skills=["foguete"],
    )

    assert resultado["score"] == 0.0
    assert "Nenhuma vaga cadastrada" in resultado["justificativa"]
