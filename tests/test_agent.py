"""
Teste do agente completo, usando o fake_llm (nenhuma chamada de rede,
nenhuma API key necessária). Verifica que o loop de 2 tool calls acontece
na ordem certa e que a resposta final contém o score.
"""

from pydantic_ai.messages import ToolCallPart

from src.agent import build_agent


def test_agente_le_curriculo_e_calcula_score_em_ordem():
    agent = build_agent()
    result = agent.run_sync("Avalie o currículo em data/curriculo_ana.txt")

    tool_calls = [
        part.tool_name
        for msg in result.all_messages()
        for part in msg.parts
        if isinstance(part, ToolCallPart)
    ]

    assert tool_calls == ["ler_curriculo", "calcular_score"]
    assert "Score" in result.output
