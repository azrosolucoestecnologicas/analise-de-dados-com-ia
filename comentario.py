"""Gera a leitura diária do painel chamando um modelo.

É a terceira camada de evidência do projeto. O painel já separa
  dado      — o que as séries do BCB mostram (analise.py)
  pesquisa  — o que a literatura estabelece (pesquisa_contexto.md)
  interpretação — esta camada, escrita por um modelo a cada execução

Lê dados/*.json, escreve dados/comentario.json.
"""

import json
import sys
from datetime import date
from pathlib import Path

import anthropic

RAIZ = Path(__file__).parent
PASTA = RAIZ / "dados"
SAIDA = PASTA / "comentario.json"

MODELO = "claude-opus-4-8"
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

SERIES = {
    "selic": ("selic_432.json", "Meta Selic", "% ao ano"),
    "ipca": ("ipca12m_13522.json", "IPCA em 12 meses", "%"),
    "endividamento": ("endividamento_29037.json", "Endividamento das famílias", "% da renda anual"),
    "comprometimento": ("comprometimento_29034.json", "Comprometimento de renda", "% da renda mensal"),
    "inadimplencia": ("inadimplencia_pf_21084.json", "Inadimplência PF", "% da carteira"),
}

INSTRUCOES = """Você escreve a leitura diária de um painel público sobre Selic e crédito
às famílias no Brasil, dirigido a um gerente de crédito de cooperativa.

Escreva UM parágrafo de 3 a 4 frases situando o quadro atual para quem decide
política de crédito.

ESCOLHA os números que importam — normalmente três ou quatro. Não repita todos os
que eu mandei: uma lista completa não é leitura, é inventário, e o painel já mostra
todos os valores nos cards logo abaixo. Prefira apontar o contraste entre o que a
Selic faz e o que os indicadores de crédito mostram.

Regras rígidas:
- Use somente os números que eu forneço. Não calcule nem estime nenhum outro valor.
- Não repita a palavra "referência" em toda frase. Cite o mês de forma natural.
- Números no formato brasileiro, com vírgula decimal (13,75).
- Variação de taxa sempre em pontos percentuais (p.p.), nunca em porcentagem.
- NÃO afirme causa, em nenhuma hipótese. Não use "causou", "provocou", "levou a",
  "resultou em", "devido a", "por causa de", "em razão de" nem "graças a" — nem mesmo
  para explicar o atraso de divulgação de uma série. Descreva a defasagem sem
  justificá-la: escreva "com referência mais antiga", não "mais antiga porque...".
  As séries se movem juntas; o painel não identifica causalidade.
- Não recomende ação. A seção prescritiva do painel já faz isso.
- Não use markdown, títulos, listas nem aspas.
- Responda apenas com o parágrafo final. Sem preâmbulo, sem explicar seu raciocínio."""


def mensalizar(chave: str) -> dict[str, float]:
    arquivo = PASTA / SERIES[chave][0]
    if not arquivo.exists():
        raise SystemExit(f"{arquivo} não existe. Rode coletor.py antes.")
    envelope = json.loads(arquivo.read_text(encoding="utf-8"))

    mensal: dict[str, float] = {}
    for ponto in envelope["observacoes"]:
        _, mes, ano = ponto["data"].split("/")
        valor = float(ponto["valor"])
        if chave == "selic":
            mensal[f"{ano}-{mes}"] = valor          # diária: último valor do mês
        else:
            mensal.setdefault(f"{ano}-{mes}", valor)  # já mensal
    return dict(sorted(mensal.items()))


def rotulo(chave_mes: str) -> str:
    ano, mes = chave_mes.split("-")
    return f"{MESES[int(mes) - 1]}/{ano}"


def coletar_fatos() -> dict:
    fatos = {}
    for chave in SERIES:
        serie = mensalizar(chave)
        meses = list(serie)
        ultimo = meses[-1]
        ano_passado = f"{int(ultimo[:4]) - 1}-{ultimo[5:]}"
        fatos[chave] = {
            "nome": SERIES[chave][1],
            "unidade": SERIES[chave][2],
            "atual": serie[ultimo],
            "mes": rotulo(ultimo),
            "ha_12_meses": serie.get(ano_passado),
            "variacao_12m": (serie[ultimo] - serie[ano_passado]) if ano_passado in serie else None,
        }
    return fatos


def valor_focus() -> dict | None:
    """Mediana do Focus para o ano corrente, como dado estruturado."""
    arquivo = PASTA / "focus_selic.json"
    if not arquivo.exists():
        return None
    envelope = json.loads(arquivo.read_text(encoding="utf-8"))
    ano = str(date.today().year)
    candidatos = [r for r in (envelope.get("observacoes") or [])
                  if str(r.get("DataReferencia")) == ano]
    if not candidatos:
        return None
    r = max(candidatos, key=lambda x: x.get("Data", ""))
    return {"nome": "Mediana do Focus para a Selic", "unidade": "% ao ano",
            "atual": float(r["Mediana"]), "mes": ano,
            "ha_12_meses": None, "variacao_12m": None,
            "coleta": r.get("Data"), "respondentes": r.get("numeroRespondentes")}


def linha_focus() -> str | None:
    """Mediana do Focus para o ANO CORRENTE, da coleta mais recente.

    O arquivo traz vários anos de referência (2026 a 2030) e várias datas de
    coleta. Pegar o último registro da lista devolve 2030 — horizonte longo
    demais para a decisão de seis meses que o painel apoia.
    """
    arquivo = PASTA / "focus_selic.json"
    if not arquivo.exists():
        return None
    envelope = json.loads(arquivo.read_text(encoding="utf-8"))
    registros = envelope.get("observacoes") or []
    if not registros:
        return None

    ano_corrente = str(date.today().year)
    candidatos = [r for r in registros if str(r.get("DataReferencia")) == ano_corrente]
    if not candidatos:
        return None

    r = max(candidatos, key=lambda x: x.get("Data", ""))
    return (f"Mediana do Boletim Focus para a Selic no fim de {ano_corrente}: "
            f"{r['Mediana']:.2f}% ao ano (coleta de {r['Data']}, "
            f"{r.get('numeroRespondentes')} respondentes).")


def main() -> None:
    fatos = coletar_fatos()

    linhas = []
    for f in fatos.values():
        linha = f"{f['nome']}: {f['atual']:.2f} {f['unidade']} (referência {f['mes']})"
        if f["variacao_12m"] is not None:
            linha += f", variação de {f['variacao_12m']:+.2f} pontos percentuais em 12 meses"
        linhas.append(linha + ".")

    focus = linha_focus()
    if focus:
        linhas.append(focus)
        # entra nos fatos para que testes.py aceite a mediana como número legítimo
        fatos["focus"] = valor_focus()

    pergunta = ("\n".join(linhas)).replace(".", ",", 0)  # números já vêm com ponto; o modelo converte
    pergunta += ("\n\nAtenção: as séries de endividamento, comprometimento de renda e "
                 "inadimplência são divulgadas com atraso, então a referência delas é "
                 "mais antiga que a da Selic. Respeite as datas acima.")

    cliente = anthropic.Anthropic()  # lê ANTHROPIC_API_KEY do ambiente

    try:
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=1200,
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
        "fatos": fatos,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    custo = resposta.usage.input_tokens / 1e6 * 5 + resposta.usage.output_tokens / 1e6 * 25
    print(f"{texto}\n")
    print(f"modelo: {resposta.model} · tokens: {resposta.usage.input_tokens} entrada / "
          f"{resposta.usage.output_tokens} saída · custo: US$ {custo:.4f}")


if __name__ == "__main__":
    main()
