"""
Ponto de entrada: `python -m src.main [caminho_do_curriculo]`.
"""

from __future__ import annotations

import os
import sys

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from .agent import build_agent  # noqa: E402  (precisa vir depois do os.environ.setdefault)

CAMINHO_PADRAO = "data/curriculo_ana.txt"


def main() -> None:
    caminho = sys.argv[1] if len(sys.argv) > 1 else CAMINHO_PADRAO
    agent = build_agent()

    print(f"Avaliando currículo: {caminho}\n")
    result = agent.run_sync(f"Avalie o currículo em {caminho} e me diga se é compatível com a vaga.")

    print(result.output)

    print("\n--- Passo a passo do agente (pra estudo) ---")
    for msg in result.all_messages():
        tipo = type(msg).__name__
        for part in msg.parts:
            part_tipo = type(part).__name__
            if part_tipo == "ToolCallPart":
                print(f"[{tipo}] chamou tool '{part.tool_name}' com args={part.args}")
            elif part_tipo == "ToolReturnPart":
                print(f"[{tipo}] tool '{part.tool_name}' retornou: {part.content}")
            elif part_tipo == "TextPart":
                print(f"[{tipo}] texto: {part.content}")


if __name__ == "__main__":
    main()
