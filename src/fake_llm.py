"""
O "cérebro" do agente quando rodamos sem chave de API.

Isso usa o `FunctionModel` do Pydantic AI: em vez de mandar a conversa pra
OpenAI/Anthropic decidirem a próxima ação, a gente escreve a própria lógica
de decisão em Python puro. O Agent por fora não sabe a diferença — ele só
enxerga "o modelo decidiu chamar esta tool com estes argumentos".

É o jeito mais direto de estudar o loop ReAct (Reason → Act → Observe) sem
gastar tokens: a cada chamada, a função abaixo olha pro histórico de
mensagens, vê quais tools já retornaram resultado, e decide o próximo passo.

Pra trocar isso por um modelo de verdade, veja agent.py — é uma linha.
"""

from __future__ import annotations

import re

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo

CAMINHO_PADRAO = "data/curriculo_ana.txt"


def _tool_returns(messages: list[ModelMessage]) -> dict[str, dict]:
    """Varre o histórico e devolve {nome_da_tool: resultado} das que já rodaram."""
    returns: dict[str, dict] = {}
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if isinstance(part, ToolReturnPart):
                    returns[part.tool_name] = part.content
    return returns


def _caminho_do_prompt(messages: list[ModelMessage]) -> str:
    """Extrai um caminho de arquivo (.txt ou .pdf) da primeira mensagem do usuário, se houver."""
    for msg in messages:
        if isinstance(msg, ModelRequest):
            for part in msg.parts:
                if hasattr(part, "content") and isinstance(part.content, str):
                    match = re.search(r"\S+\.(txt|pdf)", part.content)
                    if match:
                        return match.group(0)
    return CAMINHO_PADRAO


def decidir_proxima_acao(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
    """
    A função que o FunctionModel chama no lugar de um LLM real.

    Reproduz um agente de 2 passos clássico:
      1. ainda não li o currículo?            -> chama `ler_curriculo`
      2. já li, mas ainda não calculei score?  -> chama `calcular_score` com
                                                   os dados extraídos no passo 1
      3. já tenho os dois resultados           -> responde em texto pro usuário
    """
    resultados = _tool_returns(messages)

    if "ler_curriculo" not in resultados:
        caminho = _caminho_do_prompt(messages)
        return ModelResponse(
            parts=[ToolCallPart(tool_name="ler_curriculo", args={"caminho_arquivo": caminho})]
        )

    if "calcular_score" not in resultados:
        dados = resultados["ler_curriculo"]
        return ModelResponse(
            parts=[
                ToolCallPart(
                    tool_name="calcular_score",
                    args={
                        "nome": dados["nome"],
                        "cargo_pretendido": dados["cargo_pretendido"],
                        "anos_experiencia": dados["anos_experiencia"],
                        "skills": dados["skills"],
                    },
                )
            ]
        )

    score = resultados["calcular_score"]
    resposta = (
        f"Candidato: {score['nome']}\n"
        f"Vaga avaliada: {score['cargo']}\n"
        f"Score: {score['score']}/100\n"
        f"Skills que batem: {', '.join(score['skills_match']) or 'nenhuma'}\n"
        f"Skills faltando: {', '.join(score['skills_faltando']) or 'nenhuma'}\n"
        f"Justificativa: {score['justificativa']}"
    )
    return ModelResponse(parts=[TextPart(resposta)])
