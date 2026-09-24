"""Etapa 2 da aula: gera o comentário do painel chamando um modelo.

É aqui que o pipeline deixa de ser determinístico. A partir deste script:
  - existe uma chave de API (secret, nunca no repositório)
  - existe custo por execução
  - a mesma entrada produz saídas diferentes
  - o modelo pode falhar ou inventar

Lê dados/selic.json, escreve dados/comentario.json.
"""

import json
import os
import sys
from pathlib import Path

import anthropic

RAIZ = Path(__file__).parent
ENTRADA = RAIZ / "dados" / "selic.json"
SAIDA = RAIZ / "dados" / "comentario.json"

MODELO = "claude-opus-4-8"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

INSTRUCOES = """Você comenta um painel público sobre a meta da taxa Selic.

Escreva UM parágrafo de 2 a 3 frases sobre a situação atual da Selic.

Regras rígidas:
- Use somente os números que eu forneço. Não calcule nem estime nenhum outro valor.
- Escreva números no formato brasileiro, com vírgula decimal (13,75).
- Variação de taxa é sempre em pontos percentuais (p.p.), nunca em porcentagem.
- NÃO afirme causa. Não escreva que algo "causou", "provocou" ou "levou a" outra coisa.
- Não use markdown, títulos, listas nem aspas.
- Responda apenas com o parágrafo final. Sem preâmbulo, sem explicar seu raciocínio."""


def fatos() -> dict:
    dados = json.loads(ENTRADA.read_text(encoding="utf-8"))
    mensal: dict[str, float] = {}
    for p in dados:
        _, mes, ano = p["data"].split("/")
        mensal[f"{ano}-{mes}"] = float(p["valor"])
    mensal = dict(sorted(mensal.items()))

    meses = list(mensal)
    ultimo = meses[-1]
    ano_passado = f"{int(ultimo[:4]) - 1}-{ultimo[5:]}"
    return {
        "atual": mensal[ultimo],
        "mes": f"{MESES[int(ultimo[5:]) - 1]}/{ultimo[:4]}",
        "ha_12_meses": mensal.get(ano_passado),
        "minimo": min(mensal.values()),
        "maximo": max(mensal.values()),
        "meses_observados": len(meses),
    }


def main() -> None:
    if not ENTRADA.exists():
        raise SystemExit(f"{ENTRADA} não existe. Rode coletor.py antes.")

    f = fatos()
    variacao = f["atual"] - f["ha_12_meses"] if f["ha_12_meses"] is not None else None

    pergunta = (
        f"Meta Selic hoje: {f['atual']:.2f}% ao ano (referência {f['mes']}).\n"
        f"Há 12 meses: {f['ha_12_meses']:.2f}%.\n"
        f"Variação em 12 meses: {variacao:+.2f} pontos percentuais.\n"
        f"Mínimo desde jan/2017: {f['minimo']:.2f}%. Máximo: {f['maximo']:.2f}%.\n"
        f"Total de meses observados: {f['meses_observados']}."
    ).replace(".", ",").replace(",\n", ".\n")

    cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    try:
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=1000,
            system=INSTRUCOES,
            output_config={"effort": "low"},
            messages=[{"role": "user", "content": pergunta}],
        )
    except anthropic.AuthenticationError:
        sys.exit("ANTHROPIC_API_KEY ausente ou inválida. No GitHub, configure o secret.")
    except anthropic.RateLimitError as erro:
        sys.exit(f"rate limit atingido: {erro}")
    except anthropic.APIStatusError as erro:
        sys.exit(f"erro da API ({erro.status_code}): {erro.message}")
    except anthropic.APIConnectionError:
        sys.exit("falha de rede ao chamar a API.")

    if resposta.stop_reason == "refusal":
        sys.exit("o modelo recusou a requisição.")

    texto = "".join(b.text for b in resposta.content if b.type == "text").strip()
    if not texto:
        sys.exit("o modelo devolveu uma resposta vazia.")

    SAIDA.write_text(json.dumps({
        "texto": texto,
        "modelo": resposta.model,
        "tokens_entrada": resposta.usage.input_tokens,
        "tokens_saida": resposta.usage.output_tokens,
        "fatos": f,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    custo = resposta.usage.input_tokens / 1e6 * 5 + resposta.usage.output_tokens / 1e6 * 25
    print(f"{texto}\n")
    print(f"modelo: {resposta.model}")
    print(f"tokens: {resposta.usage.input_tokens} entrada / {resposta.usage.output_tokens} saída")
    print(f"custo estimado desta execução: US$ {custo:.4f}")


if __name__ == "__main__":
    main()
