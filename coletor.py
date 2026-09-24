#!/usr/bin/env python3
"""
Coletor de dados do projeto Painel Selic e Crédito.

Baixa as cinco séries do SGS e as expectativas anuais de Selic (Focus, API
Olinda) do Banco Central do Brasil e salva um JSON por série na pasta dados/.

Regras aplicadas:
- dataInicial fixa em 01/01/2017 e dataFinal igual à data de hoje (dd/mm/aaaa).
- A API SGS pode devolver HTTP 200 com uma página HTML quando recusa a
  requisição, então o corpo é validado (precisa começar com "[") e cada
  requisição é tentada até 3 vezes, com pausa entre as tentativas.
- A série diária 432 aceita no máximo 10 anos por requisição, então o período
  é quebrado em janelas de até 10 anos.
- A URL da Olinda é montada à mão, exatamente como no briefing, com %20.
  Não se usa params= do requests.
- Se uma série falhar, o arquivo anterior em dados/ é mantido e marcado como
  não atualizado, e o aviso aparece no resumo final.

Uso: python3 coletor.py
"""

import json
import os
import sys
import time
from datetime import date, datetime, timedelta

import requests

DATA_INICIAL = "01/01/2017"
PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")
TENTATIVAS = 3
PAUSA_SEGUNDOS = 3
TIMEOUT_SEGUNDOS = 30
MAX_ANOS_POR_REQUISICAO = 10

CABECALHOS = {
    "User-Agent": "painel-selic-credito/1.0 (coletor de dados públicos do BCB)",
    "Accept": "application/json",
}

SERIES_SGS = [
    {
        "codigo": 432,
        "arquivo": "selic_432.json",
        "nome": "Selic meta",
        "unidade": "% ao ano",
        "frequencia": "diária",
    },
    {
        "codigo": 13522,
        "arquivo": "ipca12m_13522.json",
        "nome": "IPCA acumulado em 12 meses",
        "unidade": "%",
        "frequencia": "mensal",
    },
    {
        "codigo": 29037,
        "arquivo": "endividamento_29037.json",
        "nome": "Endividamento das famílias com o SFN",
        "unidade": "%",
        "frequencia": "mensal",
    },
    {
        "codigo": 29034,
        "arquivo": "comprometimento_29034.json",
        "nome": "Comprometimento de renda das famílias com o SFN",
        "unidade": "%",
        "frequencia": "mensal",
    },
    {
        "codigo": 21084,
        "arquivo": "inadimplencia_pf_21084.json",
        "nome": "Inadimplência da carteira de crédito de pessoas físicas",
        "unidade": "%",
        "frequencia": "mensal",
    },
]

ARQUIVO_FOCUS = "focus_selic.json"

URL_FOCUS = (
    "https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/"
    "ExpectativasMercadoAnuais?$filter=Indicador%20eq%20'Selic'"
    "&$orderby=Data%20desc&$top=50&$format=json"
)


def url_sgs(codigo, data_inicial, data_final):
    """Monta a URL de uma série do SGS."""
    return (
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados"
        "?formato=json&dataInicial={}&dataFinal={}"
    ).format(codigo, data_inicial, data_final)


def para_data(texto):
    return datetime.strptime(texto, "%d/%m/%Y").date()


def para_texto(dia):
    return dia.strftime("%d/%m/%Y")


def somar_anos(dia, anos):
    try:
        return dia.replace(year=dia.year + anos)
    except ValueError:
        # 29 de fevereiro em ano que não é bissexto.
        return dia.replace(year=dia.year + anos, month=3, day=1)


def janelas(data_inicial, data_final, max_anos=MAX_ANOS_POR_REQUISICAO):
    """Quebra o período em janelas de no máximo max_anos, limite do SGS."""
    inicio = para_data(data_inicial)
    fim = para_data(data_final)
    resultado = []
    while inicio <= fim:
        limite = somar_anos(inicio, max_anos) - timedelta(days=1)
        atual = min(limite, fim)
        resultado.append((para_texto(inicio), para_texto(atual)))
        inicio = atual + timedelta(days=1)
    return resultado


def baixar(url, rotulo, inicio_esperado):
    """
    Baixa uma URL e devolve o JSON decodificado, ou None se falhar.

    Valida que o corpo começa com inicio_esperado ("[" no SGS, "{" na Olinda),
    porque a API pode devolver HTTP 200 com uma página HTML de recusa.
    Tenta até TENTATIVAS vezes, com pausa entre as tentativas.
    """
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(
                url, headers=CABECALHOS, timeout=TIMEOUT_SEGUNDOS
            )
        except requests.RequestException as erro:
            problema = "falha de rede: {}".format(erro)
        else:
            corpo = resposta.text.strip()
            if resposta.status_code != 200:
                problema = "HTTP {}".format(resposta.status_code)
            elif not corpo.startswith(inicio_esperado):
                amostra = corpo[:80].replace("\n", " ").replace("\r", " ")
                problema = (
                    "corpo não começa com '{}', a API recusou a requisição e "
                    "devolveu outro conteúdo. Início do corpo: {}"
                ).format(inicio_esperado, amostra)
            else:
                try:
                    return json.loads(corpo)
                except json.JSONDecodeError as erro:
                    problema = "JSON inválido: {}".format(erro)

        print(
            "    tentativa {}/{} falhou: {}".format(tentativa, TENTATIVAS, problema)
        )
        if tentativa < TENTATIVAS:
            time.sleep(PAUSA_SEGUNDOS)

    print("    ERRO: {} não foi baixado após {} tentativas.".format(rotulo, TENTATIVAS))
    return None


def deduplicar(observacoes, campo="data"):
    """Remove datas repetidas na junção das janelas, preservando a ordem."""
    vistos = set()
    resultado = []
    for item in observacoes:
        chave = item.get(campo)
        if chave in vistos:
            continue
        vistos.add(chave)
        resultado.append(item)
    return resultado


def salvar(caminho, conteudo):
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)


def ler_se_existir(caminho):
    if not os.path.exists(caminho):
        return None
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return None


def marcar_nao_atualizado(caminho, hoje):
    """Registra no arquivo antigo que ele não foi atualizado nesta execução."""
    conteudo = ler_se_existir(caminho)
    if not isinstance(conteudo, dict):
        return None
    conteudo["atualizado_nesta_execucao"] = False
    conteudo["verificado_em"] = hoje
    conteudo["aviso"] = (
        "A API do Banco Central não respondeu em {}. Este arquivo é a coleta "
        "anterior e pode estar desatualizado.".format(hoje)
    )
    salvar(caminho, conteudo)
    return conteudo


def coletar_sgs(serie, data_final):
    """Baixa uma série do SGS, quebrando o período em janelas de até 10 anos."""
    rotulo = "série {} ({})".format(serie["codigo"], serie["nome"])
    observacoes = []
    urls = []
    for data_de, data_ate in janelas(DATA_INICIAL, data_final):
        url = url_sgs(serie["codigo"], data_de, data_ate)
        urls.append(url)
        print("  baixando {} de {} a {}".format(rotulo, data_de, data_ate))
        dados = baixar(url, rotulo, "[")
        if dados is None:
            return None, urls
        observacoes.extend(dados)
    return deduplicar(observacoes, "data"), urls


def medianas_focus(registros, hoje):
    """
    Extrai a mediana mais recente para o fim deste ano e do próximo.

    Não faz análise: apenas seleciona, para cada DataReferencia, o registro com
    a Data de divulgação mais recente. Em caso de empate, prefere baseCalculo 0
    (últimos 30 dias), que é a base padrão do Focus.
    """
    melhores = {}
    for registro in registros:
        referencia = str(registro.get("DataReferencia", "")).strip()
        divulgacao = str(registro.get("Data", "")).strip()
        if not referencia or not divulgacao:
            continue
        base = registro.get("baseCalculo", 0)
        chave_ordem = (divulgacao, base == 0)
        atual = melhores.get(referencia)
        if atual is None or chave_ordem > atual[0]:
            melhores[referencia] = (chave_ordem, registro)

    resumo = {}
    for rotulo, ano in (
        ("fim_deste_ano", hoje.year),
        ("fim_do_proximo_ano", hoje.year + 1),
    ):
        escolhido = melhores.get(str(ano))
        if escolhido is None:
            resumo[rotulo] = {
                "ano_referencia": str(ano),
                "mediana": None,
                "data_divulgacao": None,
                "observacao": "não encontrado no retorno da API",
            }
        else:
            registro = escolhido[1]
            resumo[rotulo] = {
                "ano_referencia": str(ano),
                "mediana": registro.get("Mediana"),
                "data_divulgacao": registro.get("Data"),
                "base_calculo": registro.get("baseCalculo"),
                "numero_respondentes": registro.get("numeroRespondentes"),
            }
    return resumo


def extremos(valores):
    """Menor e maior valor de uma lista de datas já comparáveis como texto."""
    if not valores:
        return None, None
    return min(valores), max(valores)


def periodo_sgs(observacoes):
    datas = [para_data(o["data"]) for o in observacoes if o.get("data")]
    if not datas:
        return None, None
    return para_texto(min(datas)), para_texto(max(datas))


def main():
    hoje = date.today()
    data_final = para_texto(hoje)
    hoje_iso = hoje.isoformat()

    os.makedirs(PASTA_DADOS, exist_ok=True)

    print("Coletor do Painel Selic e Crédito")
    print("Período solicitado: {} a {}".format(DATA_INICIAL, data_final))
    print("Pasta de destino: {}".format(PASTA_DADOS))
    print("")

    relatorio = []
    avisos = []

    for serie in SERIES_SGS:
        caminho = os.path.join(PASTA_DADOS, serie["arquivo"])
        observacoes, urls = coletar_sgs(serie, data_final)

        if observacoes is None:
            anterior = marcar_nao_atualizado(caminho, hoje_iso)
            if anterior is None:
                avisos.append(
                    "Série {}: falhou e não há coleta anterior em dados/. "
                    "O arquivo {} não existe.".format(serie["codigo"], serie["arquivo"])
                )
                relatorio.append(
                    {
                        "nome": serie["nome"],
                        "codigo": str(serie["codigo"]),
                        "arquivo": serie["arquivo"],
                        "situacao": "FALHOU, sem dado",
                        "n": 0,
                        "de": None,
                        "ate": None,
                    }
                )
            else:
                antigas = anterior.get("observacoes", [])
                de, ate = periodo_sgs(antigas)
                avisos.append(
                    "Série {}: falhou nesta execução. Mantido o arquivo anterior "
                    "de {}.".format(serie["codigo"], anterior.get("coletado_em", "data desconhecida"))
                )
                relatorio.append(
                    {
                        "nome": serie["nome"],
                        "codigo": str(serie["codigo"]),
                        "arquivo": serie["arquivo"],
                        "situacao": "MANTIDO o anterior",
                        "n": len(antigas),
                        "de": de,
                        "ate": ate,
                    }
                )
            continue

        de, ate = periodo_sgs(observacoes)
        salvar(
            caminho,
            {
                "serie": str(serie["codigo"]),
                "nome": serie["nome"],
                "unidade": serie["unidade"],
                "frequencia_original": serie["frequencia"],
                "fonte": "Banco Central do Brasil, SGS, série {}".format(serie["codigo"]),
                "urls": urls,
                "data_inicial_solicitada": DATA_INICIAL,
                "data_final_solicitada": data_final,
                "coletado_em": hoje_iso,
                "atualizado_nesta_execucao": True,
                "numero_observacoes": len(observacoes),
                "primeira_data": de,
                "ultima_data": ate,
                "observacoes": observacoes,
            },
        )
        relatorio.append(
            {
                "nome": serie["nome"],
                "codigo": str(serie["codigo"]),
                "arquivo": serie["arquivo"],
                "situacao": "atualizado",
                "n": len(observacoes),
                "de": de,
                "ate": ate,
            }
        )

    # Focus, API Olinda. O retorno é um objeto com a lista em "value".
    caminho_focus = os.path.join(PASTA_DADOS, ARQUIVO_FOCUS)
    print("  baixando Focus, expectativa anual para a Selic (API Olinda)")
    payload = baixar(URL_FOCUS, "Focus Selic", "{")

    if payload is None or not isinstance(payload.get("value"), list):
        if payload is not None:
            print("    ERRO: o retorno da Olinda não tem a lista 'value'.")
        anterior = marcar_nao_atualizado(caminho_focus, hoje_iso)
        if anterior is None:
            avisos.append(
                "Focus: falhou e não há coleta anterior em dados/. "
                "O arquivo {} não existe.".format(ARQUIVO_FOCUS)
            )
            relatorio.append(
                {
                    "nome": "Focus, expectativa anual para a Selic",
                    "codigo": "Olinda",
                    "arquivo": ARQUIVO_FOCUS,
                    "situacao": "FALHOU, sem dado",
                    "n": 0,
                    "de": None,
                    "ate": None,
                }
            )
        else:
            registros = anterior.get("observacoes", [])
            de, ate = extremos([r.get("Data") for r in registros if r.get("Data")])
            avisos.append(
                "Focus: falhou nesta execução. Mantido o arquivo anterior de {}.".format(
                    anterior.get("coletado_em", "data desconhecida")
                )
            )
            relatorio.append(
                {
                    "nome": "Focus, expectativa anual para a Selic",
                    "codigo": "Olinda",
                    "arquivo": ARQUIVO_FOCUS,
                    "situacao": "MANTIDO o anterior",
                    "n": len(registros),
                    "de": de,
                    "ate": ate,
                }
            )
    else:
        registros = payload["value"]
        de, ate = extremos([r.get("Data") for r in registros if r.get("Data")])
        resumo = medianas_focus(registros, hoje)
        salvar(
            caminho_focus,
            {
                "serie": "Focus, expectativa anual para a Selic",
                "nome": "Expectativas de Mercado Anuais, indicador Selic",
                "unidade": "% ao ano",
                "frequencia_original": "divulgação diária de estatísticas das expectativas",
                "fonte": "Banco Central do Brasil, API Olinda, ExpectativasMercadoAnuais",
                "urls": [URL_FOCUS],
                "coletado_em": hoje_iso,
                "atualizado_nesta_execucao": True,
                "numero_observacoes": len(registros),
                "primeira_data": de,
                "ultima_data": ate,
                "medianas_selecionadas": resumo,
                "observacoes": registros,
            },
        )
        relatorio.append(
            {
                "nome": "Focus, expectativa anual para a Selic",
                "codigo": "Olinda",
                "arquivo": ARQUIVO_FOCUS,
                "situacao": "atualizado",
                "n": len(registros),
                "de": de,
                "ate": ate,
            }
        )

    print("")
    print("=" * 96)
    print("RESUMO DA COLETA")
    print("=" * 96)
    cabecalho = "{:<50} {:>8} {:>7} {:>12} {:>12}".format(
        "Série", "Código", "Pontos", "De", "Até"
    )
    print(cabecalho)
    print("-" * 96)
    for linha in relatorio:
        print(
            "{:<50} {:>8} {:>7} {:>12} {:>12}".format(
                linha["nome"][:50],
                linha["codigo"],
                linha["n"],
                linha["de"] or "sem dado",
                linha["ate"] or "sem dado",
            )
        )
    print("-" * 96)
    for linha in relatorio:
        print("  {} -> {} ({})".format(linha["arquivo"], linha["situacao"], linha["codigo"]))

    focus = ler_se_existir(caminho_focus)
    if isinstance(focus, dict) and focus.get("medianas_selecionadas"):
        print("")
        print("Focus, mediana mais recente:")
        for rotulo, item in focus["medianas_selecionadas"].items():
            print(
                "  {}: ano {} = {} (divulgado em {})".format(
                    rotulo,
                    item.get("ano_referencia"),
                    item.get("mediana", "não encontrado"),
                    item.get("data_divulgacao", "não encontrado"),
                )
            )

    if avisos:
        print("")
        print("AVISOS")
        for aviso in avisos:
            print("  - {}".format(aviso))

    sem_dado = [l for l in relatorio if l["n"] == 0]
    if sem_dado:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
