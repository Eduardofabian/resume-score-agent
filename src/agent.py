"""
Monta o Agent e registra as tools.

A variável de ambiente AGENT_MODEL decide o "cérebro":
  - não setada            -> usa o fake_llm (FunctionModel), roda sem API key
  - "openai:gpt-4o-mini"  -> usa a API da OpenAI de verdade (precisa de OPENAI_API_KEY)
  - "anthropic:claude-sonnet-4-5" -> usa a API da Anthropic (precisa de ANTHROPIC_API_KEY)

Essa é a parte que mostra por que Pydantic AI (e frameworks de agente em
geral) separam "definição do agente" de "qual modelo responde": as tools,
os tipos de retorno e o loop de execução não mudam. Só o que decide a
próxima ação muda.
"""

from __future__ import annotations

import os

from pydantic_ai import Agent
from pydantic_ai.models.function import FunctionModel

from .fake_llm import decidir_proxima_acao
from .tools import calcular_score, ler_curriculo

SYSTEM_PROMPT = (
    "Você é um agente de triagem de currículos. Dado o caminho de um arquivo "
    "de currículo, use as ferramentas disponíveis para ler o currículo e "
    "calcular o score do candidato para a vaga pretendida. Sempre leia o "
    "currículo antes de calcular o score. No final, explique o resultado "
    "de forma objetiva."
)


def build_agent() -> Agent:
    model_name = os.environ.get("AGENT_MODEL")

    if model_name:
        agent = Agent(model_name, system_prompt=SYSTEM_PROMPT)
    else:
        agent = Agent(FunctionModel(decidir_proxima_acao))

    agent.tool_plain(ler_curriculo)
    agent.tool_plain(calcular_score)
    return agent
