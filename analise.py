#!/usr/bin/env python3
"""
Gerador do painel.html do projeto Painel Selic e Crédito.

Etapa 3: seção descritiva.

Regras aplicadas:
- Todos os números vêm dos JSON em dados/. A pesquisa nunca altera, completa
  nem substitui um valor.
- Frequência mensal. Para a Selic (série diária 432) usa o último valor de
  cada mês.
- Nenhum dado ausente é preenchido. Lacunas e meses incompletos são avisados.
- Variações de taxas sempre em pontos percentuais.
- Cada gráfico traz unidade, período, fonte e número de observações.
- Cada card traz a data de referência do dado.
- Os dados são embutidos no HTML, então o painel abre sem servidor.

O painel é montado por seções. Cada etapa seguinte acrescenta uma função de
seção à lista SECOES, sem alterar as seções já validadas.

Uso: python3 analise.py
"""

import json
import os
import sys
from datetime import date, datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(RAIZ, "dados")
ARQUIVO_PAINEL = os.path.join(RAIZ, "painel.html")
ARQUIVO_FOCUS = "focus_selic.json"

PERGUNTA_DECISAO = (
    "Um gerente de crédito de uma cooperativa precisa decidir se aperta ou "
    "afrouxa a concessão a pessoas físicas nos próximos seis meses."
)

MESES_CURTOS = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez",
]

# Configuração das cinco séries observadas da seção descritiva.
# O Focus não entra aqui: ele é expectativa, não histórico observado, e será
# usado na seção preditiva.
SERIES = [
    {
        "chave": "selic",
        "arquivo": "selic_432.json",
        "codigo": "432",
        "nome": "Selic meta",
        "unidade": "% ao ano",
        "diaria": True,
        "cor": "#1f4e79",
        "papel": "Preço do dinheiro definido pelo Copom. É a variável de política.",
    },
    {
        "chave": "ipca",
        "arquivo": "ipca12m_13522.json",
        "codigo": "13522",
        "nome": "IPCA acumulado em 12 meses",
        "unidade": "%",
        "diaria": False,
        "cor": "#7f5539",
        "papel": "Inflação ao consumidor. Afeta a renda real e a capacidade de pagamento.",
    },
    {
        "chave": "endividamento",
        "arquivo": "endividamento_29037.json",
        "codigo": "29037",
        "nome": "Endividamento das famílias com o SFN",
        "unidade": "% da renda acumulada em 12 meses",
        "diaria": False,
        "cor": "#2a6f4e",
        "papel": "Estoque de dívida sobre renda. Mede o tamanho da dívida, não o seu custo.",
    },
    {
        "chave": "comprometimento",
        "arquivo": "comprometimento_29034.json",
        "codigo": "29034",
        "nome": "Comprometimento de renda das famílias com o SFN",
        "unidade": "% da renda mensal",
        "diaria": False,
        "cor": "#b45309",
        "papel": "Quanto da renda mensal vai para o serviço da dívida. Sente juros e prazo.",
    },
    {
        "chave": "inadimplencia",
        "arquivo": "inadimplencia_pf_21084.json",
        "codigo": "21084",
        "nome": "Inadimplência da carteira de crédito de pessoas físicas",
        "unidade": "% da carteira",
        "diaria": False,
        "cor": "#9b2226",
        "papel": "Atraso acima de 90 dias. É resultado, não sinal antecedente.",
    },
]

# Citações extraídas de pesquisa_contexto.md (etapa 2).
# Aqui não se calcula nada: isto é contexto externo, com fonte e URL.
PESQUISA = {
    "A1": {
        "texto": (
            "Uma operação só é classificada como inadimplente depois de três "
            "meses de atraso. É definição regulatória, não escolha estatística. "
            "Qualquer defasagem medida entre juros e inadimplência já embute "
            "esse piso."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre as novas regras de contabilização",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf",
        "data": "setembro de 2025",
        "confianca": "alta",
    },
    "A3": {
        "texto": (
            "Cerca de 70% do aumento da inadimplência do Sistema Financeiro "
            "Nacional observado até junho de 2025 decorre da mudança das regras "
            "de contabilização, em vigor desde 1º de janeiro de 2025."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre as novas regras de contabilização",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf",
        "data": "setembro de 2025",
        "confianca": "alta",
    },
    "A4": {
        "texto": (
            "Sem a mudança de regras, a inadimplência do Sistema Financeiro "
            "Nacional em junho de 2025 seria 0,53 p.p. menor, contra um aumento "
            "observado de 0,78 p.p. no ano."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre as novas regras de contabilização",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf",
        "data": "setembro de 2025",
        "confianca": "alta",
    },
    "A5": {
        "texto": (
            "Acompanhando trabalhadores formais demitidos, os valores em atraso "
            "acima de 90 dias atingem pico entre 10 e 11 meses após a demissão. "
            "Mede choque de emprego, não de juros."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Economia Bancária 2023, Boxe 1",
        "url": "https://www.bcb.gov.br/content/publicacoes/relatorioeconomiabancaria/reb2023p.pdf",
        "data": "2024, com dados de 2023",
        "confianca": "alta",
    },
    "A6": {
        "texto": (
            "Para uma elevação de 1 p.p. da Selic, o repasse estimado às taxas "
            "de crédito a pessoas físicas é de 4,43 p.p. no cheque especial, "
            "1,73 p.p. no crédito pessoal e 0,75 p.p. em veículos. No crédito "
            "direcionado cai para 0,43 p.p. no imobiliário."
        ),
        "fonte": "Banco Central do Brasil, Estudo Especial nº 118/2022, repasse da taxa Selic para o mercado de crédito bancário",
        "url": "https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/EE118_Repasse_da_taxa_Selic_para_o_mercado_de_credito_bancario.pdf",
        "data": "setembro de 2022",
        "confianca": "alta",
    },
    "A7": {
        "texto": (
            "Cada aumento médio de 1 p.p. na Selic causa queda de 3,7% no nível "
            "médio das concessões de crédito livre de longo prazo a pessoas "
            "físicas ao longo de 12 meses, em relação ao contrafactual sem o "
            "choque."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre transmissão ao mercado de crédito",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf",
        "data": "março de 2026",
        "confianca": "alta",
    },
    "A8": {
        "texto": (
            "O efeito da Selic sobre as concessões a pessoas físicas de longo "
            "prazo não é estatisticamente significativo em 3 meses e passa a ser "
            "em horizontes mais longos, na ordem de 6 a 9 meses."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre transmissão ao mercado de crédito",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf",
        "data": "março de 2026",
        "confianca": "alta",
    },
    "A9": {
        "texto": (
            "Cheque especial, rotativo e cartão parcelado tendem a subir quando "
            "a Selic sobe, porque são usados em situações de estresse "
            "financeiro. O canal de juros é contrariado pela necessidade de "
            "liquidez das famílias."
        ),
        "fonte": "Banco Central do Brasil, Relatório de Política Monetária, boxe sobre transmissão ao mercado de crédito",
        "url": "https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf",
        "data": "março de 2026",
        "confianca": "alta",
    },
    "B1": {
        "texto": (
            "Cerca de 18 meses após o início das renegociações, os níveis de "
            "inadimplência dos beneficiários do programa Desenrola Brasil "
            "voltaram a subir."
        ),
        "fonte": "Banco Central do Brasil, publicação sobre o programa Desenrola Brasil",
        "url": "https://dadosabertos.bcb.gov.br/dataset/desenrola-brasil",
        "data": "consultado em 18 de setembro de 2026",
        "confianca": "média, o trecho não foi conferido no documento original",
    },
    "B2": {
        "texto": (
            "A razão de serviço da dívida das famílias, equivalente conceitual "
            "ao comprometimento de renda, funciona como sinal antecedente de "
            "crises bancárias sistêmicas. É literatura internacional sobre "
            "crises sistêmicas, não sobre carteira de cooperativa brasileira."
        ),
        "fonte": "Bank for International Settlements, base e estudos sobre Debt Service Ratios",
        "url": "https://data.bis.org/topics/DSR",
        "data": "consultado em 18 de setembro de 2026",
        "confianca": "média, o trecho não foi conferido no documento original",
    },
    "C1": {
        "texto": (
            "A pesquisa não encontrou estimativa publicada da defasagem direta "
            "entre a Selic e o comprometimento de renda das famílias (série "
            "29034), nem entre a Selic e a inadimplência de pessoas físicas "
            "(série 21084). As âncoras disponíveis são indiretas."
        ),
        "fonte": "pesquisa_contexto.md, seção C, o que a pesquisa não estabeleceu",
        "url": "",
        "data": "18 de setembro de 2026",
        "confianca": "registro de ausência de evidência",
    },
    "C3": {
        "texto": (
            "A pesquisa não encontrou nada específico sobre cooperativas de "
            "crédito. Toda a evidência reunida é do Sistema Financeiro Nacional "
            "agregado."
        ),
        "fonte": "pesquisa_contexto.md, seção C, o que a pesquisa não estabeleceu",
        "url": "",
        "data": "18 de setembro de 2026",
        "confianca": "registro de ausência de evidência",
    },
}


# ----------------------------------------------------------------------
# Leitura e preparo dos dados
# ----------------------------------------------------------------------

def carregar(arquivo):
    caminho = os.path.join(PASTA_DADOS, arquivo)
    if not os.path.exists(caminho):
        raise SystemExit(
            "Arquivo ausente: {}. Rode coletor.py antes de analise.py.".format(caminho)
        )
    with open(caminho, encoding="utf-8") as origem:
        return json.load(origem)


def rotulo_mes(ano, mes):
    return "{}/{}".format(MESES_CURTOS[mes - 1], ano)


def para_mensal(bruto, diaria):
    """
    Converte a série para frequência mensal.

    Em série diária usa o último valor de cada mês, conforme a regra do
    projeto. Em série mensal apenas reorganiza. Nenhum valor é criado.
    """
    por_mes = {}
    for item in bruto.get("observacoes", []):
        texto_data = item.get("data")
        texto_valor = item.get("valor")
        if not texto_data or texto_valor in (None, "", "null"):
            continue
        dia = datetime.strptime(texto_data, "%d/%m/%Y").date()
        chave = (dia.year, dia.month)
        valor = float(texto_valor)
        anterior = por_mes.get(chave)
        if anterior is None or dia >= anterior["origem"]:
            por_mes[chave] = {"origem": dia, "valor": valor}

    serie = []
    for (ano, mes) in sorted(por_mes):
        ponto = por_mes[(ano, mes)]
        serie.append(
            {
                "ano": ano,
                "mes": mes,
                "rotulo": rotulo_mes(ano, mes),
                "valor": ponto["valor"],
                "data_origem": ponto["origem"].strftime("%d/%m/%Y"),
            }
        )
    return serie


def meses_faltando(serie):
    """Lista os meses ausentes entre o primeiro e o último ponto."""
    if not serie:
        return []
    presentes = {(p["ano"], p["mes"]) for p in serie}
    faltando = []
    ano, mes = serie[0]["ano"], serie[0]["mes"]
    fim = (serie[-1]["ano"], serie[-1]["mes"])
    while (ano, mes) <= fim:
        if (ano, mes) not in presentes:
            faltando.append(rotulo_mes(ano, mes))
        mes += 1
        if mes == 13:
            ano, mes = ano + 1, 1
    return faltando


def variacao_12_meses(serie):
    """
    Diferença em pontos percentuais entre o último mês e o mesmo mês do ano
    anterior. Usa exatamente 2 observações. Devolve None se o par não existir.
    """
    if not serie:
        return None, None
    ultimo = serie[-1]
    alvo = (ultimo["ano"] - 1, ultimo["mes"])
    for ponto in serie:
        if (ponto["ano"], ponto["mes"]) == alvo:
            return ultimo["valor"] - ponto["valor"], ponto
    return None, None


def extremo(serie, maior=True):
    escolhido = serie[0]
    for ponto in serie[1:]:
        if (ponto["valor"] > escolhido["valor"]) == maior and ponto["valor"] != escolhido["valor"]:
            escolhido = ponto
    return escolhido


def mes_em_curso(serie, hoje):
    """Indica se o último mês da série ainda não fechou."""
    if not serie:
        return False
    ultimo = serie[-1]
    return ultimo["ano"] == hoje.year and ultimo["mes"] == hoje.month


# ----------------------------------------------------------------------
# Formatação em português do Brasil
# ----------------------------------------------------------------------

def num(valor, casas=2):
    if valor is None:
        return "sem dado"
    texto = "{:,.{}f}".format(valor, casas)
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def num_sinal(valor, casas=2):
    if valor is None:
        return "sem dado"
    return ("+" if valor > 0 else "") + num(valor, casas)


def escapar(texto):
    return (
        str(texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def lista_pt(itens):
    """Formata uma lista como '3, 4 e 5'."""
    textos = [str(i) for i in itens]
    if not textos:
        return "nenhuma"
    if len(textos) == 1:
        return textos[0]
    return ", ".join(textos[:-1]) + " e " + textos[-1]


# ----------------------------------------------------------------------
# Estatística. Só biblioteca padrão, sem pandas e sem numpy.
# ----------------------------------------------------------------------

# t crítico aproximado para 5%, bilateral. Entre 78 e 115 graus de liberdade
# o valor varia de 1,991 a 1,981, então 1,98 serve para todas as contas
# desta seção. É aproximação assumida, não valor exato por grau de liberdade.
T_CRITICO_5 = 1.98


def pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return None
    media_x = sum(xs) / n
    media_y = sum(ys) / n
    sxy = sum((a - media_x) * (b - media_y) for a, b in zip(xs, ys))
    sxx = sum((a - media_x) ** 2 for a in xs)
    syy = sum((b - media_y) ** 2 for b in ys)
    if sxx <= 0 or syy <= 0:
        return None
    return sxy / ((sxx * syy) ** 0.5)


def r_critico(n):
    """Correlação mínima para significância a 5%, dado n, sob independência."""
    if n < 4:
        return None
    return T_CRITICO_5 / ((T_CRITICO_5 ** 2 + n - 2) ** 0.5)


def deslocar_mes(chave, passos):
    ano, mes = chave
    mes -= passos
    while mes < 1:
        mes += 12
        ano -= 1
    return (ano, mes)


def como_dicionario(serie):
    return {(p["ano"], p["mes"]): p["valor"] for p in serie}


def correlograma(fonte, alvo, defasagens, diferenca=False, ate=None):
    """
    Correlação de Pearson entre a fonte defasada em k meses e o alvo.

    defasagem k significa: fonte do mês t menos k contra alvo do mês t.
    Com diferenca=True usa a variação mensal em pontos percentuais das duas
    séries, em vez do nível. Nenhum valor é interpolado: um mês só entra no
    cálculo quando os dois lados existem.
    """
    resultado = []
    for k in defasagens:
        xs = []
        ys = []
        for chave in sorted(alvo):
            if ate is not None and chave > ate:
                continue
            chave_fonte = deslocar_mes(chave, k)
            if chave_fonte not in fonte:
                continue
            if diferenca:
                anterior_alvo = deslocar_mes(chave, 1)
                anterior_fonte = deslocar_mes(chave_fonte, 1)
                if anterior_alvo not in alvo or anterior_fonte not in fonte:
                    continue
                xs.append(fonte[chave_fonte] - fonte[anterior_fonte])
                ys.append(alvo[chave] - alvo[anterior_alvo])
            else:
                xs.append(fonte[chave_fonte])
                ys.append(alvo[chave])
        resultado.append(
            {
                "defasagem": k,
                "r": pearson(xs, ys),
                "n": len(xs),
                "limiar": r_critico(len(xs)),
            }
        )
    return resultado


def avancar_mes(chave, passos):
    ano, mes = chave
    mes += passos
    while mes > 12:
        mes -= 12
        ano += 1
    return (ano, mes)


def percentil(valores, p):
    """Percentil por interpolação linear. p entre 0 e 1."""
    if not valores:
        return None
    ordenados = sorted(valores)
    if len(ordenados) == 1:
        return ordenados[0]
    posicao = (len(ordenados) - 1) * p
    baixo = int(posicao)
    alto = min(baixo + 1, len(ordenados) - 1)
    return ordenados[baixo] + (ordenados[alto] - ordenados[baixo]) * (posicao - baixo)


def media_movel(valores, janela):
    """Média móvel simples. Os primeiros meses ficam sem valor, não são preenchidos."""
    saida = []
    for i in range(len(valores)):
        if i < janela - 1:
            saida.append(None)
        else:
            saida.append(sum(valores[i - janela + 1 : i + 1]) / janela)
    return saida


def inclinacao(valores):
    """
    Inclinação por mínimos quadrados, em unidade da série por mês.

    É uma reta ajustada aos pontos, nada além disso. Sem machine learning.
    """
    n = len(valores)
    if n < 2:
        return None
    xs = list(range(n))
    media_x = sum(xs) / n
    media_y = sum(valores) / n
    sxx = sum((x - media_x) ** 2 for x in xs)
    if sxx <= 0:
        return None
    return sum((x - media_x) * (y - media_y) for x, y in zip(xs, valores)) / sxx


def backtest(valores, janela, horizontes):
    """
    Testa o próprio método no passado, para medir o erro que ele costuma cometer.

    Para cada mês t com histórico suficiente, projeta t mais h usando a
    inclinação dos últimos 'janela' meses até t, e compara com o valor que de
    fato ocorreu. Compara também com a referência ingênua de supor que o valor
    não muda. Devolve, por horizonte, o erro absoluto médio dos dois métodos e
    os percentis 10 e 90 dos erros do modelo.
    """
    saida = {}
    for h in horizontes:
        erros_modelo = []
        erros_sem_mudanca = []
        for t in range(janela - 1, len(valores) - h):
            inc = inclinacao(valores[t - janela + 1 : t + 1])
            if inc is None:
                continue
            realizado = valores[t + h]
            erros_modelo.append(realizado - (valores[t] + inc * h))
            erros_sem_mudanca.append(realizado - valores[t])
        if not erros_modelo:
            saida[h] = None
            continue
        eam_modelo = sum(abs(e) for e in erros_modelo) / len(erros_modelo)
        eam_ingenuo = sum(abs(e) for e in erros_sem_mudanca) / len(erros_sem_mudanca)
        saida[h] = {
            "n": len(erros_modelo),
            "eam": eam_modelo,
            "eam_sem_mudanca": eam_ingenuo,
            "ganho": (eam_ingenuo - eam_modelo) / eam_ingenuo if eam_ingenuo else None,
            "p10": percentil(erros_modelo, 0.10),
            "p90": percentil(erros_modelo, 0.90),
        }
    return saida


def pico(correl):
    validos = [c for c in correl if c["r"] is not None]
    if not validos:
        return None
    return max(validos, key=lambda c: abs(c["r"]))


def plato(correl, margem=0.02):
    """Defasagens cuja correlação fica a menos de 'margem' do pico."""
    topo = pico(correl)
    if topo is None:
        return []
    return [
        c["defasagem"]
        for c in correl
        if c["r"] is not None and abs(c["r"]) >= abs(topo["r"]) - margem
    ]


# ----------------------------------------------------------------------
# Blocos de texto reutilizáveis
# ----------------------------------------------------------------------

def bloco_pesquisa(chaves):
    """Monta o bloco 'Contexto da pesquisa' com uma ou mais citações."""
    partes = []
    for chave in chaves:
        item = PESQUISA[chave]
        if item["url"]:
            fonte = '<a href="{}" target="_blank" rel="noopener">{}</a>'.format(
                item["url"], escapar(item["fonte"])
            )
        else:
            fonte = escapar(item["fonte"])
        partes.append(
            '<p class="citacao"><span class="tag-ref">{}</span> {}'
            '<span class="fonte">Fonte: {}. Data: {}. Confiança: {}.</span></p>'.format(
                chave,
                escapar(item["texto"]),
                fonte,
                escapar(item["data"]),
                escapar(item["confianca"]),
            )
        )
    return "".join(partes)


def acao(titulo, frase, dado, chaves_pesquisa, tradeoff, invalida):
    """Card de ação com os quatro campos exigidos pelo briefing."""
    return (
        '<article class="acao">'
        "<h4>{titulo}</h4>"
        '<p class="acao-frase">{frase}</p>'
        '<div class="acao-campos">'
        '<div class="campo campo-dado">'
        "<span>1. Dado quantitativo</span>{dado}</div>"
        '<div class="campo campo-evidencia">'
        "<span>2. Evidência externa</span>{evidencia}</div>"
        '<div class="campo campo-tradeoff">'
        "<span>3. Trade-off</span>{tradeoff}</div>"
        '<div class="campo campo-invalida">'
        "<span>4. Condição que invalidaria</span>{invalida}</div>"
        "</div></article>"
    ).format(
        titulo=escapar(titulo),
        frase=escapar(frase),
        dado=dado,
        evidencia=bloco_pesquisa(chaves_pesquisa),
        tradeoff=tradeoff,
        invalida=invalida,
    )


def insight(titulo, dado_observado, chaves_pesquisa, interpretacao):
    return (
        '<article class="insight">'
        '<h4>{titulo}</h4>'
        '<div class="camada camada-dado">'
        '<span class="rotulo-camada">Dado observado</span>{dado}'
        "</div>"
        '<div class="camada camada-pesquisa">'
        '<span class="rotulo-camada">Contexto da pesquisa</span>{pesquisa}'
        "</div>"
        '<div class="camada camada-interpretacao">'
        '<span class="rotulo-camada">Interpretação</span>{interpretacao}'
        "</div>"
        "</article>"
    ).format(
        titulo=escapar(titulo),
        dado=dado_observado,
        pesquisa=bloco_pesquisa(chaves_pesquisa),
        interpretacao=interpretacao,
    )


# ----------------------------------------------------------------------
# SEÇÃO 1: DESCRITIVA
# Validada na etapa 3. As etapas seguintes não devem alterar esta função.
# ----------------------------------------------------------------------

def secao_1_descritiva(dados, hoje):
    cartoes = []
    figuras = []
    configuracoes = []

    for serie in SERIES:
        info = dados[serie["chave"]]
        pontos = info["mensal"]
        ultimo = pontos[-1]
        variacao, base = info["variacao_12m"]
        maximo = extremo(pontos, maior=True)
        minimo = extremo(pontos, maior=False)
        parcial = info["parcial"]

        no_maximo = ultimo["valor"] == maximo["valor"]

        aviso_card = ""
        if parcial:
            aviso_card = (
                '<p class="aviso-card">Mês em curso. O valor é o mais recente '
                "disponível, não o fechamento de {}.</p>".format(escapar(ultimo["rotulo"]))
            )

        if variacao is None:
            texto_variacao = "sem par de 12 meses"
            classe_variacao = "neutro"
        else:
            texto_variacao = "{} p.p.".format(num_sinal(variacao))
            classe_variacao = "sobe" if variacao > 0 else ("cai" if variacao < 0 else "neutro")

        cartoes.append(
            '<div class="card">'
            '<p class="card-serie">Série {codigo}</p>'
            "<h3>{nome}</h3>"
            '<p class="card-valor">{valor}<span class="card-unidade">{unidade}</span></p>'
            '<p class="card-ref">Data de referência: {ref}</p>'
            '<p class="card-var {classe}">Variação em 12 meses: {variacao}</p>'
            '<p class="card-base">Comparado com {base}, que era {valor_base}. '
            "Cálculo com 2 observações.</p>"
            "{marca_maximo}"
            "{aviso}"
            "</div>".format(
                codigo=serie["codigo"],
                nome=escapar(serie["nome"]),
                valor=num(ultimo["valor"]),
                unidade=escapar(serie["unidade"]),
                ref=escapar(ultimo["data_origem"]),
                classe=classe_variacao,
                variacao=texto_variacao,
                base=escapar(base["rotulo"]) if base else "sem base",
                valor_base=num(base["valor"]) if base else "sem dado",
                marca_maximo=(
                    '<p class="card-extremo">Maior valor de toda a série desde jan/2017.</p>'
                    if no_maximo
                    else ""
                ),
                aviso=aviso_card,
            )
        )

        nota_parcial = ""
        if parcial:
            nota_parcial = (
                " O último ponto ({}) é mês em curso e não representa o "
                "fechamento do mês.".format(ultimo["rotulo"])
            )

        figuras.append(
            '<figure class="grafico">'
            "<figcaption>"
            "<h4>{nome}</h4>"
            '<p class="grafico-papel">{papel}</p>'
            "</figcaption>"
            '<div class="tela"><canvas id="gr_{chave}"></canvas></div>'
            '<p class="ficha">'
            "<strong>Unidade:</strong> {unidade}. "
            "<strong>Período:</strong> {de} a {ate}. "
            "<strong>Observações mensais:</strong> {n}. "
            "<strong>Critério:</strong> {criterio}. "
            "<strong>Fonte:</strong> Banco Central do Brasil, SGS, série {codigo}."
            "{parcial}"
            "</p>"
            "<p class=\"ficha ficha-extremos\">Mínimo do período: {minimo} em {mes_min}. "
            "Máximo do período: {maximo} em {mes_max}.</p>"
            "</figure>".format(
                nome=escapar(serie["nome"]),
                papel=escapar(serie["papel"]),
                chave=serie["chave"],
                unidade=escapar(serie["unidade"]),
                de=pontos[0]["rotulo"],
                ate=pontos[-1]["rotulo"],
                n=len(pontos),
                criterio=(
                    "último valor de cada mês, série de origem diária"
                    if serie["diaria"]
                    else "valor mensal divulgado pela fonte"
                ),
                codigo=serie["codigo"],
                parcial=escapar(nota_parcial),
                minimo=num(minimo["valor"]),
                mes_min=minimo["rotulo"],
                maximo=num(maximo["valor"]),
                mes_max=maximo["rotulo"],
            )
        )

        configuracoes.append(
            {
                "alvo": "gr_" + serie["chave"],
                "rotulos": [p["rotulo"] for p in pontos],
                "valores": [p["valor"] for p in pontos],
                "nome": serie["nome"],
                "cor": serie["cor"],
                "unidade": serie["unidade"],
            }
        )

    # Valores usados nos insights, todos vindos dos JSON.
    selic = dados["selic"]
    ipca = dados["ipca"]
    endiv = dados["endividamento"]
    compr = dados["comprometimento"]
    inad = dados["inadimplencia"]

    pico_selic = extremo(selic["mensal"], maior=True)
    max_compr = extremo(compr["mensal"], maior=True)
    max_inad = extremo(inad["mensal"], maior=True)
    max_endiv = extremo(endiv["mensal"], maior=True)

    meses_desde_pico = (
        (selic["mensal"][-1]["ano"] - pico_selic["ano"]) * 12
        + selic["mensal"][-1]["mes"]
        - pico_selic["mes"]
    )
    queda_desde_pico = selic["mensal"][-1]["valor"] - pico_selic["valor"]

    insights = []

    insights.append(
        insight(
            "A Selic já caiu, o custo da dívida das famílias ainda não",
            "<p>A Selic meta atingiu o máximo do período em <strong>{mes_pico}</strong>, "
            "com {v_pico}% ao ano, e está em <strong>{v_atual}% ao ano</strong> em {ref_selic}, "
            "uma queda de {queda} p.p. em {meses} meses. No mesmo intervalo, o comprometimento "
            "de renda das famílias <strong>subiu</strong> para {v_compr}% em {ref_compr}, "
            "que é o maior valor de toda a série desde jan/2017. "
            "A variação de 12 meses do comprometimento é de {var_compr} p.p. "
            "Cálculo da variação com 2 observações. Série de comprometimento com {n_compr} "
            "observações mensais.</p>".format(
                mes_pico=pico_selic["rotulo"],
                v_pico=num(pico_selic["valor"]),
                v_atual=num(selic["mensal"][-1]["valor"]),
                ref_selic=selic["mensal"][-1]["data_origem"],
                queda=num(abs(queda_desde_pico)),
                meses=meses_desde_pico,
                v_compr=num(compr["mensal"][-1]["valor"]),
                ref_compr=compr["mensal"][-1]["data_origem"],
                var_compr=num_sinal(compr["variacao_12m"][0]),
                n_compr=len(compr["mensal"]),
            ),
            ["A8", "A6", "C1"],
            "<p>A pesquisa descreve um canal que leva meses para aparecer e que é desigual "
            "entre modalidades. Isso torna plausível que uma queda da Selic ainda não tenha "
            "chegado ao bolso das famílias. Mas a pesquisa não oferece estimativa da defasagem "
            "direta entre Selic e comprometimento de renda, então o tamanho e o momento desse "
            "repasse ainda não estão medidos. A seção diagnóstica vai medir a associação nos "
            "dados. Aqui só se registra que os dois movimentos apontam em direções contrárias "
            "no mesmo intervalo, o que é uma observação, não uma relação de causa.</p>",
        )
    )

    insights.append(
        insight(
            "A inadimplência está no topo da série, e parte disso é mudança de régua",
            "<p>A inadimplência de pessoas físicas está em <strong>{v_inad}% da carteira</strong> "
            "em {ref_inad}, que é o maior valor de toda a série desde jan/2017. "
            "A variação em 12 meses é de {var_inad} p.p., calculada com 2 observações. "
            "O mínimo do período foi {min_inad}% em {mes_min}. "
            "Série com {n_inad} observações mensais.</p>".format(
                v_inad=num(inad["mensal"][-1]["valor"]),
                ref_inad=inad["mensal"][-1]["data_origem"],
                var_inad=num_sinal(inad["variacao_12m"][0]),
                min_inad=num(extremo(inad["mensal"], maior=False)["valor"]),
                mes_min=extremo(inad["mensal"], maior=False)["rotulo"],
                n_inad=len(inad["mensal"]),
            ),
            ["A3", "A4", "A1"],
            "<p>Esta é a ressalva mais importante desta seção. A régua que define inadimplência "
            "mudou em 1º de janeiro de 2025, e o Banco Central estima que cerca de 70% da alta "
            "até junho de 2025 venha dessa mudança, e não de piora do crédito. "
            "Duas diferenças de escopo precisam ficar claras: a estimativa dos 70% é para o "
            "Sistema Financeiro Nacional agregado, enquanto a série 21084 é só de pessoas "
            "físicas, e o número se refere ao acumulado até junho de 2025, enquanto a série "
            "aqui vai até {ate_inad}. O painel não ajusta a série, porque o número teria de "
            "vir dos JSON e essa correção não existe nos dados coletados. Fica o aviso: ler a "
            "alta recente como piora integral do crédito é erro.</p>".format(
                ate_inad=inad["mensal"][-1]["rotulo"]
            ),
        )
    )

    insights.append(
        insight(
            "Endividamento perto do teto, com a inflação em queda",
            "<p>O endividamento das famílias está em <strong>{v_endiv}%</strong> da renda "
            "acumulada em 12 meses em {ref_endiv}, com variação de {var_endiv} p.p. em 12 meses. "
            "O máximo da série foi {max_endiv}% em {mes_max_endiv}, então o indicador está "
            "{dist} p.p. abaixo do próprio topo. "
            "O IPCA acumulado em 12 meses está em {v_ipca}% em {ref_ipca}, com variação de "
            "{var_ipca} p.p. em 12 meses. Séries com {n_endiv} e {n_ipca} observações mensais. "
            "Cada variação de 12 meses usa 2 observações.</p>".format(
                v_endiv=num(endiv["mensal"][-1]["valor"]),
                ref_endiv=endiv["mensal"][-1]["data_origem"],
                var_endiv=num_sinal(endiv["variacao_12m"][0]),
                max_endiv=num(max_endiv["valor"]),
                mes_max_endiv=max_endiv["rotulo"],
                dist=num(abs(max_endiv["valor"] - endiv["mensal"][-1]["valor"])),
                v_ipca=num(ipca["mensal"][-1]["valor"]),
                ref_ipca=ipca["mensal"][-1]["data_origem"],
                var_ipca=num_sinal(ipca["variacao_12m"][0]),
                n_endiv=len(endiv["mensal"]),
                n_ipca=len(ipca["mensal"]),
            ),
            ["B2", "A9"],
            "<p>Endividamento e comprometimento não são a mesma coisa. O primeiro é estoque de "
            "dívida sobre renda, o segundo é o fluxo mensal de pagamento. A pesquisa traz "
            "respaldo internacional para tratar o comprometimento como sinal antecedente, mas "
            "é literatura sobre crises sistêmicas, não sobre carteira de cooperativa, e serve "
            "como analogia. A pesquisa também registra que o crédito emergencial pode se mover "
            "na direção contrária à esperada, o que é uma explicação alternativa legítima para "
            "parte do movimento das séries agregadas. Nenhuma dessas hipóteses foi testada com "
            "os dados até aqui.</p>",
        )
    )

    insights.append(
        insight(
            "As cinco séries não terminam no mesmo mês",
            "<p>As datas de referência são diferentes: Selic em {r_selic}, IPCA em {r_ipca}, "
            "inadimplência em {r_inad}, endividamento e comprometimento em {r_endiv}. "
            "O período em que as cinco séries existem ao mesmo tempo vai de "
            "<strong>{comum_de} a {comum_ate}</strong>, com {n_comum} meses. "
            "Nenhum mês foi preenchido e nenhuma série tem lacuna interna: a verificação de "
            "continuidade mensal não encontrou meses ausentes em nenhuma das cinco séries.</p>".format(
                r_selic=selic["mensal"][-1]["data_origem"],
                r_ipca=ipca["mensal"][-1]["data_origem"],
                r_inad=inad["mensal"][-1]["data_origem"],
                r_endiv=endiv["mensal"][-1]["data_origem"],
                comum_de=dados["periodo_comum"]["de"],
                comum_ate=dados["periodo_comum"]["ate"],
                n_comum=dados["periodo_comum"]["n"],
            ),
            ["C3"],
            "<p>Isso não é defeito dos dados, é o calendário de divulgação do Banco Central. "
            "A consequência prática aparece nas próximas etapas: qualquer cálculo que combine "
            "as cinco séries fica limitado a {n_comum} meses, e não aos {n_selic} meses da "
            "Selic. Some-se a isso que toda a evidência externa reunida é do sistema "
            "agregado, não de cooperativas, o que limita a transferência direta das conclusões "
            "para a carteira de quem vai decidir.</p>".format(
                n_comum=dados["periodo_comum"]["n"],
                n_selic=len(selic["mensal"]),
            ),
        )
    )

    corpo = (
        '<section id="descritiva" class="secao">'
        '<header class="secao-cabecalho">'
        '<span class="secao-numero">Seção 1</span>'
        "<h2>Descritiva: o que aconteceu</h2>"
        "<p class=\"secao-resumo\">Comportamento observado da Selic, da inflação e de três "
        "indicadores de crédito às famílias, de {de} a {ate}, em frequência mensal. "
        "Todos os números desta seção vêm dos arquivos JSON coletados das APIs do Banco "
        "Central. A pesquisa entra apenas como contexto, identificada em blocos próprios.</p>"
        "</header>"
        '<div class="avisos">'
        "<h3>Antes de ler os números</h3>"
        "<ul>"
        "<li>Cada card mostra a <strong>data de referência do próprio dado</strong>. "
        "As séries têm calendários de divulgação diferentes e não terminam no mesmo mês.</li>"
        "<li>A variação em 12 meses é a diferença em <strong>pontos percentuais</strong> entre "
        "o último mês e o mesmo mês do ano anterior. Usa 2 observações.</li>"
        "<li>A Selic é série diária e foi convertida para mensal pelo "
        "<strong>último valor de cada mês</strong>. {nota_curso}</li>"
        "<li><strong>Nenhum valor ausente foi preenchido.</strong> A verificação de continuidade "
        "não encontrou meses faltando em nenhuma das cinco séries.</li>"
        "<li>Esta seção descreve, não explica. Movimentos que ocorrem juntos são "
        "<strong>associação, não causa</strong>.</li>"
        "</ul>"
        "</div>"
        '<h3 class="titulo-grupo">Onde cada indicador está agora</h3>'
        '<div class="cards">{cards}</div>'
        '<h3 class="titulo-grupo">Uma série de cada vez</h3>'
        '<div class="graficos">{graficos}</div>'
        '<h3 class="titulo-grupo">Leitura da seção</h3>'
        '<div class="insights">{insights}</div>'
        "</section>"
    ).format(
        de=dados["periodo_total"]["de"],
        ate=dados["periodo_total"]["ate"],
        nota_curso=(
            "O último mês da Selic ainda está em curso e aparece marcado como tal."
            if selic["parcial"]
            else "O último mês da Selic está fechado."
        ),
        cards="".join(cartoes),
        graficos="".join(figuras),
        insights="".join(insights),
    )

    return corpo, configuracoes


# ----------------------------------------------------------------------
# SEÇÃO 2: DIAGNÓSTICA
# Acrescentada na etapa 4. Não altera a seção 1.
# ----------------------------------------------------------------------

DEFASAGENS = list(range(0, 19))
CORTE_CONTABIL = (2024, 12)

ALVOS_DIAGNOSTICO = [
    {
        "chave": "inadimplencia",
        "curto": "Inadimplência PF",
        "codigo": "21084",
        "cor": "#9b2226",
    },
    {
        "chave": "comprometimento",
        "curto": "Comprometimento de renda",
        "codigo": "29034",
        "cor": "#b45309",
    },
]


def secao_2_diagnostica(dados, hoje):
    selic = como_dicionario(dados["selic"]["mensal"])
    ipca = como_dicionario(dados["ipca"]["mensal"])

    calculos = {}
    for alvo in ALVOS_DIAGNOSTICO:
        serie = como_dicionario(dados[alvo["chave"]]["mensal"])
        calculos[alvo["chave"]] = {
            "config": alvo,
            "niveis": correlograma(selic, serie, DEFASAGENS),
            "difs": correlograma(selic, serie, DEFASAGENS, diferenca=True),
            "niveis_ate_2024": correlograma(selic, serie, DEFASAGENS, ate=CORTE_CONTABIL),
        }

    # Confusão concreta: Selic e IPCA se movem juntos, com sinal que muda
    # conforme a defasagem, porque a política responde à inflação.
    correl_ipca = correlograma(selic, ipca, [0, 6, 12])

    # Cards de resultado
    cartoes = []
    for alvo in ALVOS_DIAGNOSTICO:
        calc = calculos[alvo["chave"]]
        for rotulo_tipo, chave_tipo, explica in (
            ("Em níveis", "niveis", "valor do indicador contra valor da Selic"),
            (
                "Em variações mensais",
                "difs",
                "variação em p.p. do indicador contra variação em p.p. da Selic",
            ),
        ):
            topo = pico(calc[chave_tipo])
            faixa = plato(calc[chave_tipo])
            significativo = abs(topo["r"]) >= topo["limiar"]
            cartoes.append(
                '<div class="card card-diag">'
                '<p class="card-serie">{curto}, série {codigo}</p>'
                "<h3>{tipo}</h3>"
                '<p class="card-valor">{r}<span class="card-unidade">correlação no pico</span></p>'
                '<p class="card-ref">Defasagem do pico: <strong>{lag} meses</strong>. '
                "n = {n} pares.</p>"
                '<p class="card-base">{explica}.</p>'
                '<p class="card-base">Limiar de 5% para este n: {limiar}. '
                "Resultado {sig}.</p>"
                '<p class="card-base">Defasagens a menos de 0,02 do pico: {faixa}. '
                "{leitura_faixa}</p>"
                "</div>".format(
                    curto=escapar(alvo["curto"]),
                    codigo=alvo["codigo"],
                    tipo=rotulo_tipo,
                    r=num(topo["r"], 3),
                    lag=topo["defasagem"],
                    n=topo["n"],
                    explica=escapar(explica),
                    limiar=num(topo["limiar"], 3),
                    sig="acima do limiar" if significativo else "abaixo do limiar",
                    faixa=lista_pt(faixa),
                    leitura_faixa=(
                        "O pico é isolado."
                        if len(faixa) == 1
                        else "O dado não distingue uma defasagem única."
                    ),
                )
            )

    # Gráficos
    rotulos_lag = [str(k) for k in DEFASAGENS]
    configuracoes = []

    configuracoes.append(
        {
            "alvo": "gr_correl_niveis",
            "tipo": "bar",
            "rotulos": rotulos_lag,
            "casas": 3,
            "min": 0,
            "max": 1,
            "maxticks": 19,
            "tituloX": "Defasagem da Selic, em meses",
            "tituloY": "Correlação de Pearson",
            "series": [
                {
                    "nome": alvo["curto"] + " (" + alvo["codigo"] + ")",
                    "valores": [c["r"] for c in calculos[alvo["chave"]]["niveis"]],
                    "cor": alvo["cor"],
                }
                for alvo in ALVOS_DIAGNOSTICO
            ]
            + [
                {
                    "nome": "Limiar de significância a 5%",
                    "valores": [
                        c["limiar"] for c in calculos["inadimplencia"]["niveis"]
                    ],
                    "cor": "#5b6b7b",
                    "tipo": "line",
                    "tracejado": True,
                }
            ],
        }
    )

    configuracoes.append(
        {
            "alvo": "gr_correl_difs",
            "tipo": "bar",
            "rotulos": rotulos_lag,
            "casas": 3,
            "min": -0.4,
            "max": 0.5,
            "maxticks": 19,
            "tituloX": "Defasagem da Selic, em meses",
            "tituloY": "Correlação de Pearson",
            "series": [
                {
                    "nome": alvo["curto"] + " (" + alvo["codigo"] + ")",
                    "valores": [c["r"] for c in calculos[alvo["chave"]]["difs"]],
                    "cor": alvo["cor"],
                }
                for alvo in ALVOS_DIAGNOSTICO
            ]
            + [
                {
                    "nome": "Limiar de 5%, positivo",
                    "valores": [c["limiar"] for c in calculos["inadimplencia"]["difs"]],
                    "cor": "#5b6b7b",
                    "tipo": "line",
                    "tracejado": True,
                },
                {
                    "nome": "Limiar de 5%, negativo",
                    "valores": [
                        -c["limiar"] for c in calculos["inadimplencia"]["difs"]
                    ],
                    "cor": "#5b6b7b",
                    "tipo": "line",
                    "tracejado": True,
                },
            ],
        }
    )

    configuracoes.append(
        {
            "alvo": "gr_correl_robustez",
            "tipo": "line",
            "rotulos": rotulos_lag,
            "casas": 3,
            "min": 0,
            "max": 1,
            "maxticks": 19,
            "tituloX": "Defasagem da Selic, em meses",
            "tituloY": "Correlação de Pearson",
            "series": [
                {
                    "nome": "Amostra completa, até jul/2026",
                    "valores": [c["r"] for c in calculos["inadimplencia"]["niveis"]],
                    "cor": "#9b2226",
                    "pontos": True,
                },
                {
                    "nome": "Até dez/2024, antes da mudança contábil",
                    "valores": [
                        c["r"] for c in calculos["inadimplencia"]["niveis_ate_2024"]
                    ],
                    "cor": "#1f4e79",
                    "pontos": True,
                    "tracejado": True,
                },
            ],
        }
    )

    # Tabela completa, com n de cada cálculo
    linhas = []
    for i, k in enumerate(DEFASAGENS):
        celulas = ["<td><strong>{}</strong></td>".format(k)]
        for alvo in ALVOS_DIAGNOSTICO:
            calc = calculos[alvo["chave"]]
            for chave_tipo in ("niveis", "difs"):
                item = calc[chave_tipo][i]
                forte = (
                    item["r"] is not None
                    and item["limiar"] is not None
                    and abs(item["r"]) >= item["limiar"]
                )
                celulas.append(
                    '<td class="{}">{}</td><td class="n">{}</td>'.format(
                        "acima" if forte else "abaixo",
                        num(item["r"], 3),
                        item["n"],
                    )
                )
        linhas.append("<tr>" + "".join(celulas) + "</tr>")

    tabela = (
        '<div class="rolagem"><table class="tabela">'
        "<thead>"
        '<tr><th rowspan="2">Defasagem<br>(meses)</th>'
        '<th colspan="4">Inadimplência PF (21084)</th>'
        '<th colspan="4">Comprometimento de renda (29034)</th></tr>'
        "<tr><th>r níveis</th><th>n</th><th>r variações</th><th>n</th>"
        "<th>r níveis</th><th>n</th><th>r variações</th><th>n</th></tr>"
        "</thead><tbody>{}</tbody></table></div>"
        '<p class="ficha">Correlação de Pearson entre a Selic meta do mês t menos k e o '
        "indicador do mês t. Em azul, valores acima do limiar de 5% para o n da linha. "
        "Fonte dos dados: Banco Central do Brasil, SGS, séries 432, 21084 e 29034. "
        "Nenhum mês foi interpolado: um par só entra no cálculo quando os dois lados existem.</p>"
    ).format("".join(linhas))

    # Números usados nos textos
    inad = calculos["inadimplencia"]
    comp = calculos["comprometimento"]
    pico_inad_niveis = pico(inad["niveis"])
    pico_inad_difs = pico(inad["difs"])
    pico_comp_niveis = pico(comp["niveis"])
    pico_comp_difs = pico(comp["difs"])
    pico_inad_2024 = pico(inad["niveis_ate_2024"])
    plato_inad = plato(inad["niveis"])
    plato_inad_difs = plato(inad["difs"])
    plato_comp = plato(comp["niveis"])

    ipca_12 = correl_ipca[2]
    ipca_0 = correl_ipca[0]

    insights = []

    insights.append(
        insight(
            "A correlação alta some quando se olha variação em vez de nível",
            "<p>Em níveis, a Selic tem correlação de <strong>{r_in}</strong> com a "
            "inadimplência PF na defasagem de {l_in} meses (n = {n_in}) e de "
            "<strong>{r_co}</strong> com o comprometimento de renda na defasagem de "
            "{l_co} meses (n = {n_co}).</p>"
            "<p>Refazendo a mesma conta com a <strong>variação mensal em pontos "
            "percentuais</strong> das duas séries, o pico cai para {rd_in} na inadimplência "
            "(defasagem de {ld_in} meses, n = {nd_in}) e para {rd_co} no comprometimento "
            "(defasagem de {ld_co} meses, n = {nd_co}). "
            "O limiar de 5% para esses tamanhos de amostra fica perto de {limiar}, "
            "então as correlações em variação continuam acima do limiar, mas explicam por "
            "volta de {var_in}% e {var_co}% da variação do indicador.</p>".format(
                r_in=num(pico_inad_niveis["r"], 3),
                l_in=pico_inad_niveis["defasagem"],
                n_in=pico_inad_niveis["n"],
                r_co=num(pico_comp_niveis["r"], 3),
                l_co=pico_comp_niveis["defasagem"],
                n_co=pico_comp_niveis["n"],
                rd_in=num(pico_inad_difs["r"], 3),
                ld_in=pico_inad_difs["defasagem"],
                nd_in=pico_inad_difs["n"],
                rd_co=num(pico_comp_difs["r"], 3),
                ld_co=pico_comp_difs["defasagem"],
                nd_co=pico_comp_difs["n"],
                limiar=num(pico_inad_difs["limiar"], 3),
                var_in=num(100 * pico_inad_difs["r"] ** 2, 0),
                var_co=num(100 * pico_comp_difs["r"] ** 2, 0),
            ),
            ["A8", "A7"],
            "<p>Este é o resultado mais importante da seção. As duas séries sobem ao longo "
            "de quase todo o período, e correlação entre séries que sobem juntas mede "
            "tendência comum antes de medir relação entre elas. Quando se remove o nível e "
            "se compara movimento com movimento, o que sobra é fraco.</p>"
            "<p>A pesquisa é compatível com um efeito real, porém lento e parcial, e não com "
            "um efeito forte e imediato. Ela fala em queda de 3,7% nas concessões por 1 p.p. "
            "de Selic ao longo de 12 meses, e em significância apenas em horizontes mais "
            "longos. Um efeito desse tamanho, diluído em 12 meses, é exatamente o tipo de "
            "relação que aparece forte em níveis e fraca em variações mensais. "
            "A leitura honesta é: há associação, ela é pequena mês a mês, e o número alto "
            "em níveis não deve ser usado para dimensionar decisão.</p>",
        )
    )

    insights.append(
        insight(
            "A defasagem da inadimplência não é um número, é uma faixa de 3 a 8 meses",
            "<p>Em níveis, a correlação com a inadimplência PF sobe de {r0} na defasagem "
            "zero até o pico de {rmax} em {lmax} meses, e depois cai. "
            "Só que as defasagens de <strong>{faixa} meses</strong> ficam todas a menos de "
            "0,02 do pico. O dado, sozinho, não escolhe entre elas. "
            "Em variação mensal, o quadro é pior para identificação: os valores próximos do "
            "pico estão nas defasagens de {faixa_dif} meses, que nem são vizinhas.</p>"
            "<p>Na subamostra que termina em dez/2024, antes da mudança das regras de "
            "contabilização, o pico vai para {lmax24} meses e a correlação sobe para "
            "{rmax24} (n = {n24}), contra {rmax} na amostra completa (n = {nmax}).</p>".format(
                r0=num(inad["niveis"][0]["r"], 3),
                rmax=num(pico_inad_niveis["r"], 3),
                lmax=pico_inad_niveis["defasagem"],
                nmax=pico_inad_niveis["n"],
                faixa=lista_pt(plato_inad),
                faixa_dif=lista_pt(plato_inad_difs),
                lmax24=pico_inad_2024["defasagem"],
                rmax24=num(pico_inad_2024["r"], 3),
                n24=pico_inad_2024["n"],
            ),
            ["A1", "A8", "A5", "A3"],
            "<p>A faixa medida contém o que a pesquisa sugere, mas por caminhos diferentes. "
            "Existe um piso de 3 meses que é definição regulatória, não comportamento: uma "
            "operação só é inadimplente depois de 90 dias de atraso, então nenhuma defasagem "
            "abaixo disso poderia mesmo aparecer. A referência de 6 a 9 meses da pesquisa é "
            "sobre <strong>concessões</strong>, não sobre inadimplência, e a de 10 a 11 meses "
            "é sobre choque de <strong>emprego</strong>, não de juros. Convergem em ordem de "
            "grandeza, não são a mesma medida.</p>"
            "<p>O resultado da subamostra merece atenção. Excluindo o período afetado pela "
            "mudança contábil, a associação com a Selic fica <strong>mais forte</strong>, não "
            "mais fraca. Isso é o que se esperaria se parte da alta recente da inadimplência "
            "tiver origem regulatória e não em juros, como a pesquisa indica. É consistência, "
            "não prova: a subamostra também é menor e termina em outro ponto do ciclo.</p>",
        )
    )

    insights.append(
        insight(
            "O comprometimento de renda reage quase junto com a Selic",
            "<p>O comprometimento de renda tem o pico de correlação na <strong>defasagem "
            "zero</strong>, com {rmax} (n = {nmax}), e a correlação cai de forma contínua "
            "conforme a defasagem aumenta, chegando a {r18} em 18 meses (n = {n18}). "
            "As defasagens a menos de 0,02 do pico são {faixa} meses. "
            "É o oposto do perfil da inadimplência, que sobe até o meio da faixa e depois "
            "desce.</p>".format(
                rmax=num(pico_comp_niveis["r"], 3),
                nmax=pico_comp_niveis["n"],
                r18=num(comp["niveis"][18]["r"], 3),
                n18=comp["niveis"][18]["n"],
                faixa=lista_pt(plato_comp),
            ),
            ["C1", "A6", "B2"],
            "<p>Um perfil que decai desde a defasagem zero é o que se esperaria de uma "
            "variável que sente o preço do crédito rápido, e não de uma que depende de "
            "comportamento acumulado. A pesquisa dá um mecanismo plausível: o repasse da "
            "Selic às taxas ao tomador é rápido e desigual, chegando a 4,43 p.p. no cheque "
            "especial contra 0,43 p.p. no imobiliário.</p>"
            "<p>Mas aqui é preciso ser explícito sobre o vazio: a pesquisa <strong>não "
            "encontrou</strong> nenhuma estimativa publicada da defasagem direta entre Selic "
            "e comprometimento de renda. Este perfil quase contemporâneo é um achado dos "
            "dados deste painel, sem âncora externa que o confirme ou desminta. "
            "Deve ser tratado como hipótese a monitorar, não como fato estabelecido.</p>",
        )
    )

    insights.append(
        insight(
            "Quatro explicações alternativas que este cálculo não consegue descartar",
            "<p>A correlação mede associação entre duas séries e ignora tudo o mais. "
            "Um exemplo concreto está nos próprios dados coletados: a Selic e o IPCA "
            "acumulado em 12 meses têm correlação de {r_ipca0} na defasagem zero "
            "(n = {n_ipca0}) e de <strong>{r_ipca12}</strong> na defasagem de 12 meses "
            "(n = {n_ipca12}). Ou seja, a Selic de hoje carrega informação sobre a inflação "
            "de doze meses atrás, porque a política responde à inflação. "
            "Qualquer correlação entre Selic e crédito contém esse pedaço.</p>".format(
                r_ipca0=num(ipca_0["r"], 3),
                n_ipca0=ipca_0["n"],
                r_ipca12=num(ipca_12["r"], 3),
                n_ipca12=ipca_12["n"],
            ),
            ["A3", "B1", "A9", "A5"],
            "<p>As quatro candidatas, em ordem de impacto sobre a leitura:</p>"
            "<p><strong>1. Mudança contábil.</strong> A régua da inadimplência mudou em "
            "jan/2025 e cerca de 70% da alta até jun/2025 viria daí. Afeta diretamente o fim "
            "da série 21084.</p>"
            "<p><strong>2. Renegociação.</strong> O efeito do Desenrola sobre a inadimplência "
            "dos beneficiários teria se revertido após cerca de 18 meses, o que produz "
            "movimento na série sem qualquer relação com a Selic. Confiança média: o trecho "
            "não foi conferido no documento original.</p>"
            "<p><strong>3. Crédito emergencial na direção contrária.</strong> Cheque especial "
            "e rotativo tendem a subir quando a Selic sobe, por necessidade de liquidez. Isso "
            "infla a correlação positiva por um canal que não é o de custo do crédito.</p>"
            "<p><strong>4. Emprego e renda.</strong> A pesquisa mostra pico de atraso acima de "
            "90 dias entre 10 e 11 meses após demissão. <strong>O painel não coletou nenhuma "
            "série de emprego ou renda</strong>, então não há como separar o efeito de juros "
            "do efeito de mercado de trabalho. Essa é uma limitação dos dados escolhidos na "
            "etapa 1, não da estatística usada aqui.</p>",
        )
    )

    limites = (
        '<div class="limites">'
        "<h3>O que este cálculo permite e não permite concluir</h3>"
        '<div class="limites-colunas">'
        '<div class="permite">'
        "<h4>Permite dizer</h4>"
        "<ul>"
        "<li>Que Selic e os dois indicadores de crédito <strong>se movem juntos</strong> no "
        "período de jan/2017 em diante, com correlação alta em níveis.</li>"
        "<li>Que os dois indicadores têm <strong>perfis de defasagem diferentes</strong>: o "
        "comprometimento tem pico em zero e decai, a inadimplência tem pico no meio da "
        "faixa de 3 a 8 meses.</li>"
        "<li>Que a associação medida em <strong>variação mensal é fraca</strong>, ainda que "
        "acima do limiar de 5%.</li>"
        "<li>Que excluir o período da mudança contábil <strong>fortalece</strong> a "
        "associação entre Selic e inadimplência, em vez de enfraquecê-la.</li>"
        "</ul>"
        "</div>"
        '<div class="nao-permite">'
        "<h4>Não permite dizer</h4>"
        "<ul>"
        "<li><strong>Que a Selic causou</strong> a variação da inadimplência ou do "
        "comprometimento. Correlação com defasagem não é identificação causal.</li>"
        "<li>Qual é a defasagem verdadeira. A faixa de 3 a 8 meses é estatisticamente "
        "indistinguível dentro dos dados.</li>"
        "<li>Qual a contribuição isolada dos juros, já que inflação, emprego, renegociação e "
        "mudança de regra atuam ao mesmo tempo e nenhum deles foi controlado.</li>"
        "<li>Que o resultado vale para a carteira de uma cooperativa. Todas as séries são do "
        "sistema agregado, e a pesquisa não encontrou nada específico sobre cooperativas.</li>"
        "<li>Que o limiar de 5% é exato. Ele supõe observações independentes, e séries "
        "mensais de macroeconomia são altamente persistentes, o que <strong>infla</strong> a "
        "significância aparente. O n informado é o número de pares, não de informação "
        "independente.</li>"
        "</ul>"
        "</div>"
        "</div>"
        "</div>"
    )

    corpo = (
        '<section id="diagnostica" class="secao">'
        '<header class="secao-cabecalho">'
        '<span class="secao-numero">Seção 2</span>'
        "<h2>Diagnóstica: por que aconteceu</h2>"
        '<p class="secao-resumo">Correlação entre a Selic meta e os dois indicadores de '
        "crédito às famílias, com defasagens de 0 a 18 meses. Todos os coeficientes vêm dos "
        "JSON coletados. A pesquisa entra para discutir mecanismos, defasagens plausíveis e "
        "variáveis de confusão, nunca para alterar um número.</p>"
        "</header>"
        '<div class="avisos">'
        "<h3>Como foi calculado</h3>"
        "<ul>"
        "<li><strong>Medida:</strong> correlação de Pearson entre a Selic meta do mês t menos "
        "k e o indicador do mês t, para k de 0 a 18 meses.</li>"
        "<li><strong>Duas formas:</strong> em <strong>níveis</strong>, comparando valor com "
        "valor, e em <strong>variações mensais em pontos percentuais</strong>, comparando "
        "movimento com movimento. As duas aparecem lado a lado de propósito.</li>"
        "<li><strong>n cai conforme a defasagem cresce</strong>, porque pares sem os dois "
        "lados são descartados. O n de cada cálculo está na tabela e nos cards.</li>"
        "<li><strong>Limiar de 5%:</strong> calculado como t crítico de 1,98 sobre a raiz de "
        "t ao quadrado mais n menos 2. É aproximação, e supõe observações independentes.</li>"
        "<li><strong>Robustez:</strong> a inadimplência foi recalculada numa subamostra que "
        "termina em dez/2024, antes da mudança das regras de contabilização.</li>"
        "<li><strong>Correlação não é causa.</strong> Esta seção mede associação e lista o que "
        "ela não consegue separar.</li>"
        "</ul>"
        "</div>"
        '<h3 class="titulo-grupo">Onde cada correlação chega ao máximo</h3>'
        '<div class="cards">{cards}</div>'
        '<h3 class="titulo-grupo">Perfil da correlação por defasagem</h3>'
        '<figure class="grafico">'
        "<figcaption><h4>Em níveis: valor da Selic contra valor do indicador</h4>"
        '<p class="grafico-papel">Barras mais altas indicam associação mais forte. '
        "A linha tracejada é o limiar de 5%.</p></figcaption>"
        '<div class="tela"><canvas id="gr_correl_niveis"></canvas></div>'
        '<p class="ficha"><strong>Unidade:</strong> correlação de Pearson, de 0 a 1. '
        "<strong>Período:</strong> jan/2017 a jul/2026 na inadimplência e a jun/2026 no "
        "comprometimento. <strong>Observações:</strong> de {n_max} a {n_min} pares conforme a "
        "defasagem. <strong>Fonte:</strong> Banco Central do Brasil, SGS, séries 432, 21084 e "
        "29034.</p></figure>"
        '<figure class="grafico">'
        "<figcaption><h4>Em variações mensais: movimento contra movimento</h4>"
        '<p class="grafico-papel">Mesma conta, aplicada à variação de cada mês em pontos '
        "percentuais. É o teste que remove a tendência comum.</p></figcaption>"
        '<div class="tela"><canvas id="gr_correl_difs"></canvas></div>'
        '<p class="ficha"><strong>Unidade:</strong> correlação de Pearson. '
        "<strong>Período:</strong> o mesmo, menos um mês perdido no cálculo da variação. "
        "<strong>Observações:</strong> de {nd_max} a {nd_min} pares conforme a defasagem. "
        "<strong>Fonte:</strong> Banco Central do Brasil, SGS, séries 432, 21084 e 29034.</p>"
        "</figure>"
        '<figure class="grafico">'
        "<figcaption><h4>Robustez: a inadimplência antes e depois da mudança contábil</h4>"
        '<p class="grafico-papel">A mesma correlação em níveis, calculada na amostra completa '
        "e numa subamostra que termina em dez/2024.</p></figcaption>"
        '<div class="tela"><canvas id="gr_correl_robustez"></canvas></div>'
        '<p class="ficha"><strong>Unidade:</strong> correlação de Pearson. '
        "<strong>Períodos:</strong> jan/2017 a jul/2026 e jan/2017 a dez/2024. "
        "<strong>Observações:</strong> até {n_max} e até {n_max24} pares. "
        "<strong>Fonte:</strong> Banco Central do Brasil, SGS, séries 432 e 21084. "
        "O corte em dez/2024 vem da pesquisa, que data a mudança de regra em 1º de janeiro de "
        "2025. O dado não foi alterado, apenas recortado.</p></figure>"
        '<h3 class="titulo-grupo">Todos os coeficientes, com o n de cada conta</h3>'
        "{tabela}"
        '<h3 class="titulo-grupo">Leitura da seção</h3>'
        '<div class="insights">{insights}</div>'
        "{limites}"
        "</section>"
    ).format(
        cards="".join(cartoes),
        n_max=inad["niveis"][0]["n"],
        n_min=inad["niveis"][18]["n"],
        nd_max=inad["difs"][0]["n"],
        nd_min=inad["difs"][18]["n"],
        n_max24=inad["niveis_ate_2024"][0]["n"],
        tabela=tabela,
        insights="".join(insights),
        limites=limites,
    )

    return corpo, configuracoes


# ----------------------------------------------------------------------
# SEÇÃO 3: PREDITIVA
# Acrescentada na etapa 5. Não altera as seções 1 e 2.
# ----------------------------------------------------------------------

JANELA_MM = 6
JANELA_INCLINACAO = 6
HORIZONTE = 6
HORIZONTES_TESTE = [1, 2, 3, 4, 5, 6]
MESES_HISTORICO_GRAFICO = 36

SERIES_PREDITIVAS = [
    {
        "chave": "selic",
        "curto": "Selic meta",
        "codigo": "432",
        "unidade": "% ao ano",
        "cor": "#1f4e79",
        "tem_consenso": True,
    },
    {
        "chave": "inadimplencia",
        "curto": "Inadimplência PF",
        "codigo": "21084",
        "unidade": "% da carteira",
        "cor": "#9b2226",
        "tem_consenso": False,
    },
    {
        "chave": "comprometimento",
        "curto": "Comprometimento de renda",
        "codigo": "29034",
        "unidade": "% da renda mensal",
        "cor": "#b45309",
        "tem_consenso": False,
    },
    {
        "chave": "endividamento",
        "curto": "Endividamento",
        "codigo": "29037",
        "unidade": "% da renda em 12 meses",
        "cor": "#2a6f4e",
        "tem_consenso": False,
    },
]


def calcular_previsao(pontos):
    """Média móvel, inclinação recente, projeção de 6 meses e faixa por backtest."""
    valores = [p["valor"] for p in pontos]
    mm = media_movel(valores, JANELA_MM)
    inc_curta = inclinacao(valores[-JANELA_INCLINACAO:])
    inc_longa = inclinacao(valores[-12:]) if len(valores) >= 12 else None
    teste = backtest(valores, JANELA_INCLINACAO, HORIZONTES_TESTE)

    ultimo = pontos[-1]
    ultimo_valor = valores[-1]
    projecao = []
    for h in range(1, HORIZONTE + 1):
        chave = avancar_mes((ultimo["ano"], ultimo["mes"]), h)
        central = ultimo_valor + inc_curta * h
        faixa = teste.get(h)
        projecao.append(
            {
                "h": h,
                "ano": chave[0],
                "mes": chave[1],
                "rotulo": rotulo_mes(chave[0], chave[1]),
                "central": central,
                "baixo": central + faixa["p10"] if faixa else None,
                "alto": central + faixa["p90"] if faixa else None,
            }
        )

    return {
        "pontos": pontos,
        "valores": valores,
        "mm": mm,
        "inclinacao_6m": inc_curta,
        "inclinacao_12m": inc_longa,
        "teste": teste,
        "projecao": projecao,
        "ultimo": ultimo,
    }


def secao_3_preditiva(dados, hoje):
    previsoes = {}
    for serie in SERIES_PREDITIVAS:
        previsoes[serie["chave"]] = calcular_previsao(dados[serie["chave"]]["mensal"])

    configuracoes = []
    blocos_modelo = []

    for serie in SERIES_PREDITIVAS:
        prev = previsoes[serie["chave"]]
        pontos = prev["pontos"]
        corte = max(0, len(pontos) - MESES_HISTORICO_GRAFICO)
        hist = pontos[corte:]
        mm_hist = prev["mm"][corte:]
        n_proj = len(prev["projecao"])

        rotulos = [p["rotulo"] for p in hist] + [p["rotulo"] for p in prev["projecao"]]
        historico = [p["valor"] for p in hist] + [None] * n_proj
        mm_linha = mm_hist + [None] * n_proj
        # A projeção começa no último ponto observado para a linha não ficar solta.
        base = [None] * (len(hist) - 1) + [hist[-1]["valor"]]
        central = base + [p["central"] for p in prev["projecao"]]
        alto = base + [p["alto"] for p in prev["projecao"]]
        baixo = base + [p["baixo"] for p in prev["projecao"]]

        configuracoes.append(
            {
                "alvo": "gr_prev_" + serie["chave"],
                "tipo": "line",
                "rotulos": rotulos,
                "casas": 2,
                "unidade": serie["unidade"],
                "maxticks": 10,
                "series": [
                    {
                        "nome": "Faixa de incerteza, limite superior",
                        "valores": alto,
                        "cor": "#c7d6e4",
                        "tracejado": True,
                        "preencherAte": 2,
                        "corPreenchimento": "rgba(31,78,121,0.10)",
                    },
                    {
                        "nome": "Faixa de incerteza, limite inferior",
                        "valores": baixo,
                        "cor": "#c7d6e4",
                        "tracejado": True,
                    },
                    {
                        "nome": "Observado",
                        "valores": historico,
                        "cor": serie["cor"],
                    },
                    {
                        "nome": "Média móvel de 6 meses",
                        "valores": mm_linha,
                        "cor": "#5b6b7b",
                        "tracejado": True,
                    },
                    {
                        "nome": "Projeção do modelo",
                        "valores": central,
                        "cor": "#111827",
                        "pontos": True,
                    },
                ],
            }
        )

        final = prev["projecao"][-1]
        teste6 = prev["teste"].get(HORIZONTE)
        direcao = (
            "queda" if prev["inclinacao_6m"] < 0 else
            "alta" if prev["inclinacao_6m"] > 0 else "estabilidade"
        )
        virada = (
            prev["inclinacao_12m"] is not None
            and prev["inclinacao_6m"] * prev["inclinacao_12m"] < 0
        )

        blocos_modelo.append(
            '<figure class="grafico">'
            "<figcaption><h4>{curto} (série {codigo})</h4>"
            '<p class="grafico-papel">Observado, média móvel de 6 meses e projeção de '
            "6 meses com faixa de incerteza.</p></figcaption>"
            '<div class="numeros-prev">'
            '<div class="num-item"><span>Último observado</span><strong>{ult}</strong>'
            "<small>{ref}</small></div>"
            '<div class="num-item"><span>Média móvel de 6 meses</span><strong>{mm}</strong>'
            "<small>até {rot_ult}</small></div>"
            '<div class="num-item"><span>Inclinação recente</span>'
            '<strong class="{classe}">{inc} p.p. por mês</strong>'
            "<small>últimos 6 meses, ou seja {inc6} p.p. em meio ano</small></div>"
            '<div class="num-item"><span>Projeção para {rot_fim}</span><strong>{proj}</strong>'
            "<small>faixa de {baixo} a {alto}</small></div>"
            "</div>"
            '<div class="tela tela-alta"><canvas id="gr_prev_{chave}"></canvas></div>'
            '<p class="ficha"><strong>Unidade:</strong> {unidade}. '
            "<strong>Período mostrado:</strong> {de} a {ate}, mais 6 meses projetados. "
            "<strong>Observações usadas:</strong> {n_total} meses na série, {jan} meses na "
            "inclinação, {n_teste} origens no teste da faixa. "
            "<strong>Fonte:</strong> Banco Central do Brasil, SGS, série {codigo}. "
            "A projeção não é dado do Banco Central, é cálculo deste painel.</p>"
            "{nota_virada}"
            "</figure>".format(
                curto=escapar(serie["curto"]),
                codigo=serie["codigo"],
                ult=num(prev["valores"][-1]),
                ref=escapar(prev["ultimo"]["data_origem"]),
                mm=num(prev["mm"][-1]) if prev["mm"][-1] is not None else "sem dado",
                rot_ult=prev["ultimo"]["rotulo"],
                classe="sobe" if prev["inclinacao_6m"] > 0 else "cai",
                inc=num_sinal(prev["inclinacao_6m"], 3),
                inc6=num_sinal(prev["inclinacao_6m"] * 6),
                rot_fim=final["rotulo"],
                proj=num(final["central"]),
                baixo=num(final["baixo"]),
                alto=num(final["alto"]),
                chave=serie["chave"],
                unidade=escapar(serie["unidade"]),
                de=hist[0]["rotulo"],
                ate=hist[-1]["rotulo"],
                n_total=len(prev["valores"]),
                jan=JANELA_INCLINACAO,
                n_teste=teste6["n"] if teste6 else 0,
                nota_virada=(
                    '<p class="ficha nota-virada">Atenção: a inclinação dos últimos 6 meses '
                    "({inc6} p.p. por mês) tem sinal contrário à dos últimos 12 meses "
                    "({inc12} p.p. por mês). A tendência recente virou, e projetar a reta "
                    "recente para a frente é especialmente frágil aqui.</p>".format(
                        inc6=num_sinal(prev["inclinacao_6m"], 3),
                        inc12=num_sinal(prev["inclinacao_12m"], 3),
                    )
                    if virada
                    else ""
                ),
            )
        )

    # --- Consenso externo: Focus ---
    focus = dados.get("focus")
    prev_selic = previsoes["selic"]
    comparacao = None
    cartoes_focus = []

    if focus and focus.get("medianas"):
        for rotulo_item, item in focus["medianas"].items():
            ano_ref = item.get("ano_referencia")
            mediana = item.get("mediana")
            alvo_mes = (int(ano_ref), 12) if ano_ref and ano_ref.isdigit() else None
            equivalente = None
            if alvo_mes:
                for p in prev_selic["projecao"]:
                    if (p["ano"], p["mes"]) == alvo_mes:
                        equivalente = p
            if rotulo_item == "fim_deste_ano" and equivalente and mediana is not None:
                comparacao = {
                    "mes": equivalente["rotulo"],
                    "focus": mediana,
                    "modelo": equivalente["central"],
                    "baixo": equivalente["baixo"],
                    "alto": equivalente["alto"],
                    "dentro": equivalente["baixo"] <= mediana <= equivalente["alto"],
                    "diferenca": equivalente["central"] - mediana,
                    "respondentes": item.get("numero_respondentes"),
                    "divulgacao": item.get("data_divulgacao"),
                }
            cartoes_focus.append(
                '<div class="card card-focus">'
                '<p class="card-serie">Focus, mediana de mercado</p>'
                "<h3>Selic no fim de {ano}</h3>"
                '<p class="card-valor">{mediana}<span class="card-unidade">% ao ano</span></p>'
                '<p class="card-ref">Divulgação de {divulgacao}. {respondentes} respondentes.</p>'
                '<p class="card-base">{situacao}</p>'
                "</div>".format(
                    ano=escapar(ano_ref or "sem referência"),
                    mediana=num(mediana) if mediana is not None else "não encontrado",
                    divulgacao=escapar(item.get("data_divulgacao") or "não encontrado"),
                    respondentes=escapar(item.get("numero_respondentes") or "sem"),
                    situacao=(
                        "Dentro do horizonte de 6 meses do modelo, dá para comparar."
                        if equivalente
                        else "Fora do horizonte de 6 meses do modelo. Serve de direção, "
                        "não de comparação direta."
                    ),
                )
            )

    if comparacao:
        bloco_comparacao = (
            '<div class="comparacao">'
            "<h4>Modelo e consenso lado a lado, para {mes}</h4>"
            '<div class="comparacao-linha">'
            '<div class="lado lado-modelo"><span>Projeção do modelo</span>'
            "<strong>{modelo}</strong><small>faixa de {baixo} a {alto}</small></div>"
            '<div class="lado lado-focus"><span>Consenso Focus</span>'
            "<strong>{focus}</strong><small>mediana de {resp} respondentes, "
            "divulgada em {div}</small></div>"
            '<div class="lado lado-dif"><span>Diferença</span>'
            "<strong>{dif} p.p.</strong><small>modelo menos Focus</small></div>"
            "</div>"
            "<p>{leitura}</p>"
            "</div>"
        ).format(
            mes=escapar(comparacao["mes"]),
            modelo=num(comparacao["modelo"]),
            baixo=num(comparacao["baixo"]),
            alto=num(comparacao["alto"]),
            focus=num(comparacao["focus"]),
            resp=escapar(comparacao["respondentes"]),
            div=escapar(comparacao["divulgacao"]),
            dif=num_sinal(comparacao["diferenca"]),
            leitura=(
                "A mediana do Focus está <strong>dentro</strong> da faixa de incerteza do "
                "modelo, então os dois não se contradizem em termos estatísticos. "
                "Mas apontam coisas diferentes: o modelo apenas estende a queda recente, "
                "enquanto o Focus reúne {resp} projeções de instituições que acompanham o "
                "Copom e incorporam informação que este painel não tem. "
                "Para a Selic, o consenso externo é a referência mais confiável das duas."
                if comparacao["dentro"]
                else "A mediana do Focus está <strong>fora</strong> da faixa de incerteza do "
                "modelo. Quando isso acontece, a divergência é mostrada e não se escolhe um "
                "lado: o modelo só estende a tendência recente, o Focus reúne {resp} "
                "projeções de instituições que acompanham o Copom."
            ).format(resp=escapar(comparacao["respondentes"])),
        )
    else:
        bloco_comparacao = (
            '<div class="comparacao"><p>Não foi possível comparar modelo e Focus: '
            "a mediana para o fim deste ano não caiu dentro do horizonte de 6 meses da "
            "projeção, ou não veio no retorno da API.</p></div>"
        )

    # --- Tabela de erro do backtest ---
    linhas_teste = []
    for h in HORIZONTES_TESTE:
        celulas = ["<td><strong>{}</strong></td>".format(h)]
        for serie in SERIES_PREDITIVAS:
            item = previsoes[serie["chave"]]["teste"].get(h)
            if not item:
                celulas.append('<td colspan="3">sem dado</td>')
                continue
            ganho = item["ganho"]
            celulas.append(
                '<td>{eam}</td><td class="n">{ing}</td>'
                '<td class="{classe}">{ganho}</td>'.format(
                    eam=num(item["eam"], 3),
                    ing=num(item["eam_sem_mudanca"], 3),
                    classe="acima" if ganho and ganho > 0 else "pior",
                    ganho=num_sinal(100 * ganho, 0) + "%" if ganho is not None else "sem dado",
                )
            )
        linhas_teste.append("<tr>" + "".join(celulas) + "</tr>")

    cabecalho_teste = "".join(
        '<th colspan="3">{} ({})</th>'.format(escapar(s["curto"]), s["codigo"])
        for s in SERIES_PREDITIVAS
    )
    sub_teste = "".join(
        "<th>Erro do modelo</th><th>Erro sem mudança</th><th>Ganho</th>"
        for _ in SERIES_PREDITIVAS
    )

    tabela_teste = (
        '<div class="rolagem"><table class="tabela">'
        '<thead><tr><th rowspan="2">Horizonte<br>(meses)</th>{cab}</tr>'
        "<tr>{sub}</tr></thead><tbody>{linhas}</tbody></table></div>"
        '<p class="ficha">Erro absoluto médio em pontos percentuais, medido testando o '
        "próprio método em todos os meses passados com histórico suficiente. "
        '"Erro sem mudança" é o erro de simplesmente supor que o indicador fica parado no '
        "último valor. \"Ganho\" positivo significa que o modelo errou menos que essa "
        "referência, e negativo significa que errou mais. "
        "Número de origens testadas: de {n1} a {n6} conforme a série e o horizonte. "
        "Fonte dos dados: Banco Central do Brasil, SGS.</p>"
    ).format(
        cab=cabecalho_teste,
        sub=sub_teste,
        linhas="".join(linhas_teste),
        n1=min(
            previsoes[s["chave"]]["teste"][1]["n"] for s in SERIES_PREDITIVAS
        ),
        n6=max(
            previsoes[s["chave"]]["teste"][HORIZONTE]["n"] for s in SERIES_PREDITIVAS
        ),
    )

    # --- Insights ---
    p_selic = previsoes["selic"]
    p_inad = previsoes["inadimplencia"]
    p_comp = previsoes["comprometimento"]
    p_endiv = previsoes["endividamento"]

    piores = []
    for serie in SERIES_PREDITIVAS:
        item = previsoes[serie["chave"]]["teste"][HORIZONTE]
        if item["ganho"] is not None and item["ganho"] < 0:
            piores.append((serie["curto"], item["ganho"]))
    piores.sort(key=lambda t: t[1])

    insights = []

    insights.append(
        insight(
            "O modelo perde para supor que nada muda",
            "<p>Testando o método em todos os meses passados, no horizonte de 6 meses ele "
            "erra em média {eam_sel} p.p. na Selic, contra {ing_sel} p.p. de quem "
            "simplesmente supõe que a taxa fica parada. "
            "No comprometimento de renda a diferença é maior: {eam_comp} p.p. contra "
            "{ing_comp} p.p., ou seja, o modelo erra <strong>{pior_comp}% mais</strong> "
            "que a referência ingênua.</p>"
            "<p>Em 6 meses, das {n_series} séries projetadas, {n_piores} têm desempenho pior "
            "que supor estabilidade: {lista_piores}. "
            "O teste usa de {n_min} a {n_max} origens, conforme a série.</p>".format(
                eam_sel=num(p_selic["teste"][6]["eam"], 3),
                ing_sel=num(p_selic["teste"][6]["eam_sem_mudanca"], 3),
                eam_comp=num(p_comp["teste"][6]["eam"], 3),
                ing_comp=num(p_comp["teste"][6]["eam_sem_mudanca"], 3),
                pior_comp=num(abs(100 * p_comp["teste"][6]["ganho"]), 0),
                n_series=len(SERIES_PREDITIVAS),
                n_piores=len(piores),
                lista_piores=lista_pt([p[0] for p in piores]) if piores else "nenhuma",
                n_min=min(previsoes[s["chave"]]["teste"][6]["n"] for s in SERIES_PREDITIVAS),
                n_max=max(previsoes[s["chave"]]["teste"][6]["n"] for s in SERIES_PREDITIVAS),
            ),
            ["A8", "A9"],
            "<p>Este resultado é desconfortável e por isso está no topo da seção. "
            "Uma reta ajustada aos últimos 6 meses supõe que o movimento recente continua, e "
            "as séries de crédito não se comportam assim: elas viram. "
            "A pesquisa reforça o motivo. A transmissão da Selic ao crédito é lenta e só "
            "aparece em horizontes mais longos, e há modalidades que andam na direção "
            "contrária, então a inclinação de um semestre mistura canais com sinais opostos "
            "e não é uma boa base para extrapolar.</p>"
            "<p>A consequência prática para a decisão: <strong>use a faixa, não o número "
            "central</strong>, e trate a projeção como cenário de referência, não como "
            "previsão. A etapa 6 vai trabalhar com cenários por esse motivo.</p>",
        )
    )

    insights.append(
        insight(
            "Para a Selic, o Focus vale mais que o modelo",
            "<p>A Selic caiu {inc6} p.p. por mês nos últimos 6 meses. Estendendo essa reta, o "
            "modelo projeta <strong>{proj}</strong>% ao ano em {mes_fim}, com faixa de "
            "{baixo} a {alto}. A faixa tem <strong>{largura} p.p. de largura</strong>, o que "
            "para uma decisão de crédito é quase tão útil quanto não ter projeção.</p>"
            "<p>O Focus, por sua vez, traz mediana de {focus_ano}% para o fim de {ano_focus} "
            "e {focus_prox}% para o fim de {ano_prox}, com divulgação de {div} e "
            "{resp} respondentes.</p>".format(
                inc6=num(abs(p_selic["inclinacao_6m"]), 3),
                proj=num(p_selic["projecao"][-1]["central"]),
                mes_fim=p_selic["projecao"][-1]["rotulo"],
                baixo=num(p_selic["projecao"][-1]["baixo"]),
                alto=num(p_selic["projecao"][-1]["alto"]),
                largura=num(
                    p_selic["projecao"][-1]["alto"] - p_selic["projecao"][-1]["baixo"]
                ),
                focus_ano=num(focus["medianas"]["fim_deste_ano"]["mediana"])
                if focus else "sem dado",
                ano_focus=escapar(focus["medianas"]["fim_deste_ano"]["ano_referencia"])
                if focus else "",
                focus_prox=num(focus["medianas"]["fim_do_proximo_ano"]["mediana"])
                if focus else "sem dado",
                ano_prox=escapar(focus["medianas"]["fim_do_proximo_ano"]["ano_referencia"])
                if focus else "",
                div=escapar(focus["medianas"]["fim_deste_ano"]["data_divulgacao"])
                if focus else "",
                resp=escapar(focus["medianas"]["fim_deste_ano"]["numero_respondentes"])
                if focus else "",
            ),
            ["A6", "A7"],
            "<p>São duas coisas diferentes e o painel não as mistura. O modelo é aritmética "
            "sobre a série histórica e não sabe que existe Copom. O Focus é a mediana de "
            "instituições que acompanham a política monetária e incorporam comunicado, ata e "
            "cenário fiscal. Para projetar uma taxa que é <strong>decidida por um comitê</strong>, "
            "e não por inércia, o consenso externo é a referência mais confiável.</p>"
            "<p>A pesquisa acrescenta o que fazer com essa informação: o repasse ao tomador é "
            "desigual por modalidade, chegando a 4,43 p.p. no cheque especial contra 0,43 p.p. "
            "no imobiliário, e o efeito sobre concessões é de cerca de 3,7% por 1 p.p. ao "
            "longo de 12 meses. Ou seja, mesmo acertando a Selic, o efeito na carteira depende "
            "do mix de linhas.</p>",
        )
    )

    virou = [
        s["curto"]
        for s in SERIES_PREDITIVAS
        if previsoes[s["chave"]]["inclinacao_12m"] is not None
        and previsoes[s["chave"]]["inclinacao_6m"]
        * previsoes[s["chave"]]["inclinacao_12m"]
        < 0
    ]

    insights.append(
        insight(
            "Os indicadores de crédito ainda apontam para cima, com uma exceção",
            "<p>Inclinação dos últimos 6 meses, em pontos percentuais por mês: "
            "inadimplência PF {inc_inad}, comprometimento {inc_comp}, endividamento "
            "{inc_endiv}. "
            "Projetando 6 meses: inadimplência vai a {pr_inad}% em {m_inad} "
            "(faixa de {b_inad} a {a_inad}), comprometimento a {pr_comp}% em {m_comp} "
            "(faixa de {b_comp} a {a_comp}) e endividamento a {pr_endiv}% em {m_endiv} "
            "(faixa de {b_endiv} a {a_endiv}).</p>"
            "<p>A inadimplência desacelerou: a inclinação de 6 meses ({inc_inad}) é menor que "
            "a de 12 meses ({inc12_inad}). O endividamento {texto_virada}</p>".format(
                inc_inad=num_sinal(p_inad["inclinacao_6m"], 3),
                inc_comp=num_sinal(p_comp["inclinacao_6m"], 3),
                inc_endiv=num_sinal(p_endiv["inclinacao_6m"], 3),
                pr_inad=num(p_inad["projecao"][-1]["central"]),
                m_inad=p_inad["projecao"][-1]["rotulo"],
                b_inad=num(p_inad["projecao"][-1]["baixo"]),
                a_inad=num(p_inad["projecao"][-1]["alto"]),
                pr_comp=num(p_comp["projecao"][-1]["central"]),
                m_comp=p_comp["projecao"][-1]["rotulo"],
                b_comp=num(p_comp["projecao"][-1]["baixo"]),
                a_comp=num(p_comp["projecao"][-1]["alto"]),
                pr_endiv=num(p_endiv["projecao"][-1]["central"]),
                m_endiv=p_endiv["projecao"][-1]["rotulo"],
                b_endiv=num(p_endiv["projecao"][-1]["baixo"]),
                a_endiv=num(p_endiv["projecao"][-1]["alto"]),
                inc12_inad=num_sinal(p_inad["inclinacao_12m"], 3),
                texto_virada=(
                    "é o caso a observar: a inclinação de 6 meses ({i6}) tem sinal contrário "
                    "à de 12 meses ({i12}), ou seja, a série parou de subir e começou a ceder. "
                    "Uma virada recente é justamente o que este tipo de projeção captura "
                    "pior.".format(
                        i6=num_sinal(p_endiv["inclinacao_6m"], 3),
                        i12=num_sinal(p_endiv["inclinacao_12m"], 3),
                    )
                    if "Endividamento" in virou
                    else "segue na mesma direção dos últimos 12 meses."
                ),
            ),
            ["A1", "A3", "A5"],
            "<p>Três qualificações da pesquisa mudam a leitura destes números.</p>"
            "<p><strong>A projeção da inadimplência herda a régua nova.</strong> A série já "
            "incorpora a mudança contábil de jan/2025, que responderia por cerca de 70% da "
            "alta até jun/2025. Projetar a partir de um nível inflado por mudança de "
            "definição estende esse efeito para a frente, e o painel não tem como separar "
            "isso porque a correção não existe nos JSON.</p>"
            "<p><strong>O piso de 90 dias atrasa qualquer melhora.</strong> Mesmo que a "
            "concessão melhore hoje, a inadimplência só reflete isso depois de três meses de "
            "atraso acumulado. O que vai aparecer nos próximos 6 meses já está em grande "
            "parte contratado.</p>"
            "<p><strong>O risco que o modelo não vê é emprego.</strong> A pesquisa mostra "
            "pico de atraso acima de 90 dias entre 10 e 11 meses após demissão. Um choque de "
            "emprego hoje só apareceria depois do horizonte desta projeção, e nenhuma série "
            "de emprego foi coletada neste painel.</p>",
        )
    )

    corpo = (
        '<section id="preditiva" class="secao">'
        '<header class="secao-cabecalho">'
        '<span class="secao-numero">Seção 3</span>'
        "<h2>Preditiva: para onde aponta</h2>"
        '<p class="secao-resumo">Tendência simples calculada sobre os JSON, sem machine '
        "learning. A seção separa de propósito três coisas que costumam ser confundidas: "
        "o que o modelo projeta, o que o mercado espera e o que nenhum dos dois sabe.</p>"
        "</header>"
        '<div class="avisos">'
        "<h3>Como foi calculado</h3>"
        "<ul>"
        "<li><strong>Média móvel de 6 meses:</strong> média simples dos 6 meses até cada "
        "ponto. Os 5 primeiros meses ficam sem valor e não foram preenchidos.</li>"
        "<li><strong>Inclinação recente:</strong> reta por mínimos quadrados sobre os últimos "
        "6 meses, em pontos percentuais por mês. A inclinação de 12 meses aparece junto para "
        "mostrar quando a tendência virou.</li>"
        "<li><strong>Projeção:</strong> último valor observado mais a inclinação recente "
        "multiplicada pelo número de meses à frente. É extrapolação de reta, nada além.</li>"
        "<li><strong>Faixa de incerteza:</strong> não é suposição. O método foi testado em "
        "todos os meses passados com histórico suficiente, e a faixa vai do percentil 10 ao "
        "90 dos erros que ele de fato cometeu naquele horizonte. Cobre 80% dos casos "
        "históricos.</li>"
        "<li><strong>Sem machine learning</strong> e sem variável explicativa. A projeção de "
        "cada série usa apenas o passado dela mesma.</li>"
        "</ul>"
        "</div>"
        '<div class="bloco bloco-a">'
        '<div class="bloco-titulo"><span class="bloco-tag">A</span>'
        "<h3>Projeção do modelo</h3>"
        "<p>Aritmética sobre as séries do Banco Central. Não sabe que existe Copom, não "
        "conhece cenário fiscal e não usa nenhuma informação externa.</p></div>"
        '<div class="graficos">{modelo}</div>'
        "</div>"
        '<div class="bloco bloco-b">'
        '<div class="bloco-titulo"><span class="bloco-tag">B</span>'
        "<h3>Consenso externo</h3>"
        "<p>Mediana das projeções de mercado coletadas pelo Banco Central na pesquisa Focus. "
        "É informação de fora do painel, e existe apenas para a Selic. "
        "Para inadimplência, comprometimento e endividamento <strong>não há consenso externo "
        "nos dados coletados</strong>, então essas projeções não têm contraponto.</p></div>"
        '<div class="cards">{focus}</div>'
        "{comparacao}"
        '<p class="ficha">Fonte: Banco Central do Brasil, API Olinda, Expectativas de Mercado '
        "Anuais, indicador Selic. Mediana mais recente por ano de referência, base de cálculo "
        "dos últimos 30 dias.</p>"
        "</div>"
        '<div class="bloco bloco-c">'
        '<div class="bloco-titulo"><span class="bloco-tag">C</span>'
        "<h3>Incertezas</h3>"
        "<p>O quanto este método costuma errar, medido nele mesmo, e o que pode quebrar a "
        "tendência segundo a pesquisa.</p></div>"
        "{teste}"
        '<div class="insights">{insights}</div>'
        "</div>"
        "</section>"
    ).format(
        modelo="".join(blocos_modelo),
        focus="".join(cartoes_focus) if cartoes_focus else
        '<div class="card"><p>Focus não disponível nos dados coletados.</p></div>',
        comparacao=bloco_comparacao,
        teste=tabela_teste,
        insights="".join(insights),
    )

    return corpo, configuracoes


# ----------------------------------------------------------------------
# SEÇÃO 4: PRESCRITIVA
# Acrescentada na etapa 6. Não altera as seções 1, 2 e 3.
# ----------------------------------------------------------------------

def secao_4_prescritiva(dados, hoje):
    prev_selic = calcular_previsao(dados["selic"]["mensal"])
    prev_inad = calcular_previsao(dados["inadimplencia"]["mensal"])
    prev_comp = calcular_previsao(dados["comprometimento"]["mensal"])
    prev_endiv = calcular_previsao(dados["endividamento"]["mensal"])

    selic_dic = como_dicionario(dados["selic"]["mensal"])
    correl_inad = correlograma(
        selic_dic, como_dicionario(dados["inadimplencia"]["mensal"]), DEFASAGENS
    )
    correl_comp = correlograma(
        selic_dic, como_dicionario(dados["comprometimento"]["mensal"]), DEFASAGENS
    )
    pico_inad = pico(correl_inad)
    pico_comp = pico(correl_comp)
    plato_inad = plato(correl_inad)

    focus = dados.get("focus") or {}
    medianas = focus.get("medianas") or {}
    focus_ano = medianas.get("fim_deste_ano", {})
    focus_prox = medianas.get("fim_do_proximo_ano", {})

    ultimo_selic = prev_selic["ultimo"]
    valor_selic = prev_selic["valores"][-1]
    final_selic = prev_selic["projecao"][-1]
    teste6_selic = prev_selic["teste"][HORIZONTE]

    # Trajetória do consenso: os dois pontos do Focus são anuais, então o
    # caminho mensal é interpolação linear feita aqui, não dado do Focus.
    meses_proj = [(p["ano"], p["mes"]) for p in prev_selic["projecao"]]
    rotulos_proj = [p["rotulo"] for p in prev_selic["projecao"]]

    def caminho_focus():
        if focus_ano.get("mediana") is None or focus_prox.get("mediana") is None:
            return None
        fim_ano = (int(focus_ano["ano_referencia"]), 12)
        fim_prox = (int(focus_prox["ano_referencia"]), 12)
        v_ano = focus_ano["mediana"]
        v_prox = focus_prox["mediana"]
        total = (fim_prox[0] - fim_ano[0]) * 12 + fim_prox[1] - fim_ano[1]
        caminho = []
        for chave in meses_proj:
            distancia = (chave[0] - fim_ano[0]) * 12 + chave[1] - fim_ano[1]
            if distancia <= 0:
                caminho.append(v_ano)
            elif total > 0:
                caminho.append(v_ano + (v_prox - v_ano) * distancia / total)
            else:
                caminho.append(v_ano)
        return caminho

    trajetoria_focus = caminho_focus()
    selic_central_focus = trajetoria_focus[-1] if trajetoria_focus else None

    def reta(destino):
        return [
            valor_selic + (destino - valor_selic) * (h + 1) / HORIZONTE
            for h in range(HORIZONTE)
        ]

    cenarios = [
        {
            "id": "a",
            "nome": "Cenário A: queda mais rápida",
            "destino": final_selic["baixo"],
            "caminho": reta(final_selic["baixo"]),
            "cor": "#2a6f4e",
            "origem": (
                "Limite inferior da faixa de 80% do modelo em {}, calculada sobre os erros "
                "históricos do próprio método em {} origens.".format(
                    final_selic["rotulo"], teste6_selic["n"]
                )
            ),
            "variacao": final_selic["baixo"] - valor_selic,
        },
        {
            "id": "b",
            "nome": "Cenário B: consenso de mercado",
            "destino": selic_central_focus,
            "caminho": trajetoria_focus,
            "cor": "#1f4e79",
            "origem": (
                "Medianas do Focus de {} para o fim de {} e {}, ligadas por interpolação "
                "linear. O caminho mensal é construção deste painel, o Focus publica "
                "apenas os pontos anuais.".format(
                    focus_ano.get("data_divulgacao", "sem data"),
                    focus_ano.get("ano_referencia", ""),
                    focus_prox.get("ano_referencia", ""),
                )
                if trajetoria_focus
                else "Focus não disponível nos dados coletados."
            ),
            "variacao": (
                selic_central_focus - valor_selic if selic_central_focus is not None else None
            ),
        },
        {
            "id": "c",
            "nome": "Cenário C: parada ou reversão",
            "destino": final_selic["alto"],
            "caminho": reta(final_selic["alto"]),
            "cor": "#9b2226",
            "origem": (
                "Limite superior da faixa de 80% do modelo em {}, pela mesma medida de "
                "erro histórico.".format(final_selic["rotulo"])
            ),
            "variacao": final_selic["alto"] - valor_selic,
        },
    ]

    # Gráfico dos cenários
    corte = max(0, len(prev_selic["pontos"]) - 24)
    hist = prev_selic["pontos"][corte:]
    base = [None] * (len(hist) - 1) + [valor_selic]
    series_cenarios = [
        {
            "nome": "Selic observada",
            "valores": [p["valor"] for p in hist] + [None] * HORIZONTE,
            "cor": "#16202b",
        }
    ]
    for cen in cenarios:
        if cen["caminho"] is None:
            continue
        series_cenarios.append(
            {
                "nome": cen["nome"],
                "valores": base + cen["caminho"],
                "cor": cen["cor"],
                "pontos": True,
                "tracejado": True,
            }
        )

    configuracoes = [
        {
            "alvo": "gr_cenarios",
            "tipo": "line",
            "rotulos": [p["rotulo"] for p in hist] + rotulos_proj,
            "casas": 2,
            "unidade": "% ao ano",
            "maxticks": 10,
            "series": series_cenarios,
        }
    ]

    cartoes_cenario = "".join(
        '<div class="card card-cenario cen-{id}">'
        "<h3>{nome}</h3>"
        '<p class="card-valor">{destino}<span class="card-unidade">% ao ano em {mes}</span></p>'
        '<p class="card-var {classe}">{variacao} p.p. em relação a hoje</p>'
        '<p class="card-base">{origem}</p>'
        "</div>".format(
            id=cen["id"],
            nome=escapar(cen["nome"]),
            destino=num(cen["destino"]) if cen["destino"] is not None else "sem dado",
            mes=escapar(final_selic["rotulo"]),
            classe=(
                "cai" if cen["variacao"] and cen["variacao"] < 0
                else "sobe" if cen["variacao"] and cen["variacao"] > 0
                else "neutro"
            ),
            variacao=num_sinal(cen["variacao"]) if cen["variacao"] is not None else "sem dado",
            origem=escapar(cen["origem"]),
        )
        for cen in cenarios
    )

    # ---------------- Ações ----------------
    acoes_transversais = []

    acoes_transversais.append(
        acao(
            "Trocar o indicador que dispara o aperto",
            "Usar o comprometimento de renda como gatilho mensal, e a inadimplência apenas "
            "como confirmação posterior.",
            "<p>Na seção diagnóstica, a correlação da Selic com o comprometimento de renda "
            "tem pico na <strong>defasagem zero</strong> (r = {r_comp}, n = {n_comp}) e cai "
            "de forma contínua daí em diante. Com a inadimplência, o pico está em "
            "{lag_inad} meses (r = {r_inad}, n = {n_inad}), e as defasagens de {plato} meses "
            "são estatisticamente indistinguíveis entre si.</p>"
            "<p>Hoje o comprometimento está em <strong>{v_comp}%</strong> ({ref_comp}), o "
            "maior valor da série desde jan/2017, com alta de {var_comp} p.p. em 12 meses.</p>".format(
                r_comp=num(pico_comp["r"], 3),
                n_comp=pico_comp["n"],
                lag_inad=pico_inad["defasagem"],
                r_inad=num(pico_inad["r"], 3),
                n_inad=pico_inad["n"],
                plato=lista_pt(plato_inad),
                v_comp=num(prev_comp["valores"][-1]),
                ref_comp=escapar(prev_comp["ultimo"]["data_origem"]),
                var_comp=num_sinal(dados["comprometimento"]["variacao_12m"][0]),
            ),
            ["A1", "B2"],
            "<p>O comprometimento é divulgado com atraso maior que a inadimplência: hoje ele "
            "vai até {ate_comp} e a inadimplência até {ate_inad}. Trocar o gatilho significa "
            "decidir com dado mais antigo, em troca de decidir com dado que reage antes. "
            "Além disso, o respaldo para tratar o comprometimento como antecedente vem de "
            "literatura internacional sobre crises bancárias sistêmicas, não sobre carteira "
            "de cooperativa.</p>".format(
                ate_comp=prev_comp["ultimo"]["rotulo"],
                ate_inad=prev_inad["ultimo"]["rotulo"],
            ),
            "<p>Se o comprometimento de renda parar de acompanhar a Selic, a base da "
            "recomendação cai. O sinal de alerta é a correlação contemporânea deixar de "
            "aparecer em uma atualização futura deste painel. Vale lembrar que a correlação "
            "em variação mensal já é fraca (pico de {r_dif}), então essa troca de gatilho se "
            "apoia no comportamento de nível, não no de curto prazo.</p>".format(
                r_dif=num(
                    pico(
                        correlograma(
                            selic_dic,
                            como_dicionario(dados["comprometimento"]["mensal"]),
                            DEFASAGENS,
                            diferenca=True,
                        )
                    )["r"],
                    3,
                )
            ),
        )
    )

    acoes_transversais.append(
        acao(
            "Descontar a mudança contábil antes de apertar por inadimplência",
            "Não tratar a alta recente da série 21084 como piora integral do crédito, e "
            "recalibrar o limite interno que dispara restrição.",
            "<p>A inadimplência de pessoas físicas está em <strong>{v_inad}%</strong> "
            "({ref_inad}), o maior valor da série, com alta de {var_inad} p.p. em 12 meses. "
            "Mas a inclinação desacelerou: {inc6} p.p. por mês nos últimos 6 meses contra "
            "{inc12} p.p. por mês nos últimos 12.</p>"
            "<p>Na seção diagnóstica, excluir o período da mudança de regra "
            "<strong>aumenta</strong> a correlação com a Selic, de {r_cheio} para {r_antes}. "
            "Ou seja, o pedaço recente da série é o que menos se explica por juros.</p>".format(
                v_inad=num(prev_inad["valores"][-1]),
                ref_inad=escapar(prev_inad["ultimo"]["data_origem"]),
                var_inad=num_sinal(dados["inadimplencia"]["variacao_12m"][0]),
                inc6=num_sinal(prev_inad["inclinacao_6m"], 3),
                inc12=num_sinal(prev_inad["inclinacao_12m"], 3),
                r_cheio=num(pico_inad["r"], 3),
                r_antes=num(
                    pico(
                        correlograma(
                            selic_dic,
                            como_dicionario(dados["inadimplencia"]["mensal"]),
                            DEFASAGENS,
                            ate=CORTE_CONTABIL,
                        )
                    )["r"],
                    3,
                ),
            ),
            ["A3", "A4"],
            "<p>Descontar a régua nova reduz o aperto agora, e com ele a proteção caso a "
            "deterioração seja real. A estimativa dos 70% é do sistema agregado, não só de "
            "pessoas físicas, e vale para o acumulado até junho de 2025, não até "
            "{ate_inad}. O painel não tem como aplicar esse desconto à série, porque a "
            "correção não existe nos dados coletados: qualquer ajuste seria número inventado "
            "a partir da pesquisa, o que este painel não faz.</p>".format(
                ate_inad=prev_inad["ultimo"]["rotulo"]
            ),
            "<p>Se a carteira da própria cooperativa mostrar piora de safra recente, com "
            "atraso subindo em operações originadas depois de jan/2025, o argumento contábil "
            "deixa de explicar e a alta passa a ser crédito ruim de verdade. "
            "Dado interno vence dado agregado nesse caso.</p>",
        )
    )

    acoes_cenario = {
        "a": acao(
            "Afrouxar por mix, não por volume",
            "Ampliar originação nas linhas com garantia antes de ampliar o limite geral de "
            "concessão.",
            "<p>Neste cenário a Selic cai {var} p.p. até {mes}, indo a {destino}% ao ano. "
            "Mesmo assim, o comprometimento de renda projetado para {mes_comp} é de "
            "{proj_comp}%, com faixa de {b_comp} a {a_comp}, ou seja, o cenário central "
            "ainda fica <strong>acima</strong> do nível atual de {v_comp}%.</p>".format(
                var=num(abs(cenarios[0]["variacao"])),
                mes=escapar(final_selic["rotulo"]),
                destino=num(cenarios[0]["destino"]),
                mes_comp=prev_comp["projecao"][-1]["rotulo"],
                proj_comp=num(prev_comp["projecao"][-1]["central"]),
                b_comp=num(prev_comp["projecao"][-1]["baixo"]),
                a_comp=num(prev_comp["projecao"][-1]["alto"]),
                v_comp=num(prev_comp["valores"][-1]),
            ),
            ["A6", "A8"],
            "<p>Linhas com garantia têm spread menor, então a margem por real emprestado cai "
            "justamente quando a queda de juros já comprime receita. É trocar rentabilidade "
            "por qualidade de safra, e a troca aparece no resultado antes de aparecer na "
            "inadimplência.</p>",
            "<p>Se a queda da Selic vier acompanhada de piora do emprego, o alívio de juros "
            "não se converte em capacidade de pagamento e afrouxar vira erro. "
            "O painel <strong>não consegue ver isso</strong>: nenhuma série de emprego ou "
            "renda foi coletada na etapa 1.</p>",
        ),
        "b": acao(
            "Manter o volume e recompor o mix",
            "Não mexer no limite agregado de concessão nos próximos seis meses, e usar o "
            "período para reduzir a fatia de crédito emergencial na carteira.",
            "<p>Neste cenário a Selic vai a {destino}% ao ano em {mes}, {var} p.p. em relação "
            "a hoje, seguindo a mediana de {resp} respondentes do Focus. "
            "É o cenário mais próximo de estabilidade: a variação projetada é menor que o "
            "erro típico do próprio modelo em seis meses, que é de {eam} p.p.</p>"
            "<p>O endividamento já virou: inclinação de {inc6_e} p.p. por mês nos últimos 6 "
            "meses contra {inc12_e} nos últimos 12.</p>".format(
                destino=num(cenarios[1]["destino"]) if cenarios[1]["destino"] else "sem dado",
                mes=escapar(final_selic["rotulo"]),
                var=num_sinal(cenarios[1]["variacao"]) if cenarios[1]["variacao"] else "sem dado",
                resp=escapar(focus_ano.get("numero_respondentes", "sem")),
                eam=num(teste6_selic["eam"], 2),
                inc6_e=num_sinal(prev_endiv["inclinacao_6m"], 3),
                inc12_e=num_sinal(prev_endiv["inclinacao_12m"], 3),
            ),
            ["A7", "A9"],
            "<p>Recompor mix sem mexer em volume exige recusar originação boa em linhas caras "
            "e substituí-la por originação mais barata, o que leva tempo e pode não ser "
            "possível no ritmo desejado. Enquanto a substituição não acontece, a cooperativa "
            "perde receita sem ganhar proteção.</p>",
            "<p>Se o Focus for revisado para fora da faixa do modelo, isto é, para menos de "
            "{baixo}% ou mais de {alto}% em {mes}, o cenário central deixa de ser central e a "
            "recomendação de não mexer perde a base. "
            "A mediana do Focus é revisada semanalmente e o painel usa a divulgação de "
            "{div}.</p>".format(
                baixo=num(final_selic["baixo"]),
                alto=num(final_selic["alto"]),
                mes=escapar(final_selic["rotulo"]),
                div=escapar(focus_ano.get("data_divulgacao", "sem data")),
            ),
        ),
        "c": acao(
            "Apertar o emergencial, preservar o consignado e o com garantia",
            "Se a Selic parar de cair ou subir, cortar limite de cheque especial e rotativo "
            "antes de cortar concessão nova com garantia.",
            "<p>Neste cenário a Selic vai a {destino}% ao ano em {mes}, {var} p.p. em relação "
            "a hoje. O comprometimento de renda responde à Selic de forma quase "
            "contemporânea (pico em defasagem zero, r = {r_comp}), então o aperto aparece no "
            "orçamento das famílias quase imediatamente, enquanto a inadimplência só reage "
            "na faixa de {plato} meses.</p>"
            "<p>Partindo de {v_comp}% hoje, o limite superior da faixa projetada de "
            "comprometimento é {a_comp}% em {mes_comp}.</p>".format(
                destino=num(cenarios[2]["destino"]),
                mes=escapar(final_selic["rotulo"]),
                var=num_sinal(cenarios[2]["variacao"]),
                r_comp=num(pico_comp["r"], 3),
                plato=lista_pt(plato_inad),
                v_comp=num(prev_comp["valores"][-1]),
                a_comp=num(prev_comp["projecao"][-1]["alto"]),
                mes_comp=prev_comp["projecao"][-1]["rotulo"],
            ),
            ["A9", "A6", "A5"],
            "<p>Cortar crédito emergencial de quem está sob estresse empurra o associado para "
            "fora da cooperativa ou para o atraso, e o efeito aparece na própria carteira "
            "com defasagem. É proteção de balanço que pode custar relacionamento e, no "
            "limite, aumentar a perda que se queria evitar.</p>",
            "<p>Se a alta da Selic vier com emprego e renda em expansão, a capacidade de "
            "pagamento sobe junto e o aperto vira perda de mercado sem ganho de qualidade. "
            "Essa é a condição mais provável de invalidar a recomendação, e também a que "
            "este painel <strong>não tem dado para verificar</strong>.</p>",
        ),
    }

    blocos_cenario = "".join(
        '<div class="cenario cen-{id}">'
        '<div class="cenario-cabeca"><h4>{nome}</h4>'
        "<p>Selic em {destino}% ao ano em {mes}, {var} p.p. ante hoje. {origem}</p></div>"
        "{acao}"
        "</div>".format(
            id=cen["id"],
            nome=escapar(cen["nome"]),
            destino=num(cen["destino"]) if cen["destino"] is not None else "sem dado",
            mes=escapar(final_selic["rotulo"]),
            var=num_sinal(cen["variacao"]) if cen["variacao"] is not None else "sem dado",
            origem=escapar(cen["origem"]),
            acao=acoes_cenario[cen["id"]],
        )
        for cen in cenarios
    )

    # ---------------- Painel de monitoramento ----------------
    monitorar = [
        {
            "indicador": "Comprometimento de renda (29034)",
            "atual": "{}% em {}".format(
                num(prev_comp["valores"][-1]), prev_comp["ultimo"]["rotulo"]
            ),
            "gatilho": "Passar de {}%, limite superior da faixa projetada para {}.".format(
                num(prev_comp["projecao"][-1]["alto"]), prev_comp["projecao"][-1]["rotulo"]
            ),
            "acao": "Apertar, mesmo que a Selic esteja caindo.",
        },
        {
            "indicador": "Inadimplência PF (21084)",
            "atual": "{}% em {}".format(
                num(prev_inad["valores"][-1]), prev_inad["ultimo"]["rotulo"]
            ),
            "gatilho": "Passar de {}%, limite superior da faixa projetada para {}.".format(
                num(prev_inad["projecao"][-1]["alto"]), prev_inad["projecao"][-1]["rotulo"]
            ),
            "acao": "Confirmar o aperto que o comprometimento já sinalizou antes.",
        },
        {
            "indicador": "Endividamento (29037)",
            "atual": "{}% em {}, inclinação {} p.p. por mês".format(
                num(prev_endiv["valores"][-1]),
                prev_endiv["ultimo"]["rotulo"],
                num_sinal(prev_endiv["inclinacao_6m"], 3),
            ),
            "gatilho": "A inclinação de 6 meses voltar a ficar positiva.",
            "acao": "Rever a leitura de que o estoque de dívida parou de crescer.",
        },
        {
            "indicador": "Focus, Selic no fim de {}".format(
                focus_ano.get("ano_referencia", "")
            ),
            "atual": "{}% na divulgação de {}".format(
                num(focus_ano["mediana"]) if focus_ano.get("mediana") is not None else "sem dado",
                escapar(focus_ano.get("data_divulgacao", "sem data")),
            ),
            "gatilho": "Sair da faixa de {}% a {}%.".format(
                num(final_selic["baixo"]), num(final_selic["alto"])
            ),
            "acao": "Trocar de cenário.",
        },
    ]

    tabela_monitor = (
        '<div class="rolagem"><table class="tabela tabela-monitor">'
        "<thead><tr><th>Indicador</th><th>Onde está</th>"
        "<th>Gatilho que muda a decisão</th><th>O que fazer</th></tr></thead>"
        "<tbody>{}</tbody></table></div>"
        '<p class="ficha">Os gatilhos são os limites superiores das faixas calculadas na '
        "seção preditiva, e não metas definidas por julgamento. Fonte dos níveis: Banco "
        "Central do Brasil, SGS e API Olinda. As faixas são cálculo deste painel.</p>"
    ).format(
        "".join(
            "<tr><td class='esq'><strong>{}</strong></td><td class='esq'>{}</td>"
            "<td class='esq'>{}</td><td class='esq'>{}</td></tr>".format(
                escapar(m["indicador"]), m["atual"], escapar(m["gatilho"]), escapar(m["acao"])
            )
            for m in monitorar
        )
    )

    # ---------------- Resposta à pergunta ----------------
    resposta = (
        '<div class="resposta">'
        "<h3>Resposta à pergunta de decisão</h3>"
        "<p class=\"resposta-frase\">Nem apertar nem afrouxar o volume total. "
        "Manter a concessão agregada e mudar o mix, com o comprometimento de renda como "
        "gatilho mensal.</p>"
        "<p>Os dados não sustentam uma virada em nenhuma das duas direções, e o painel "
        "prefere dizer isso a produzir uma recomendação mais firme do que a evidência "
        "permite. De um lado, a Selic caiu {queda} p.p. em 12 meses, o que puxaria para "
        "afrouxar. Do outro, comprometimento de renda e inadimplência estão no "
        "<strong>maior valor da série desde jan/2017</strong>, o que puxaria para apertar.</p>"
        "<p>Três resultados das seções anteriores explicam por que a resposta não é mais "
        "forte que isso:</p>"
        "<ul>"
        "<li>A associação entre Selic e crédito, medida em variação mensal, é fraca: "
        "o pico é {r_dif_inad} na inadimplência e {r_dif_comp} no comprometimento. "
        "A correlação alta em níveis é tendência comum.</li>"
        "<li>A projeção de 6 meses <strong>perde para supor que nada muda</strong> nas quatro "
        "séries testadas. A faixa da Selic em {mes_fim} tem {largura} p.p. de largura.</li>"
        "<li>Parte da alta da inadimplência é mudança de régua contábil, não piora de "
        "crédito, e o painel não consegue separar quanto.</li>"
        "</ul>"
        "<p>Decisão de volume exige previsão confiável, e este painel mostrou que não tem "
        "uma. Decisão de mix exige saber onde o repasse de juros dói mais, e isso a pesquisa "
        "fornece com número. Por isso a recomendação está em mix, e não em volume.</p>"
        "</div>"
    ).format(
        queda=num(abs(dados["selic"]["variacao_12m"][0])),
        r_dif_inad=num(
            pico(
                correlograma(
                    selic_dic,
                    como_dicionario(dados["inadimplencia"]["mensal"]),
                    DEFASAGENS,
                    diferenca=True,
                )
            )["r"],
            3,
        ),
        r_dif_comp=num(
            pico(
                correlograma(
                    selic_dic,
                    como_dicionario(dados["comprometimento"]["mensal"]),
                    DEFASAGENS,
                    diferenca=True,
                )
            )["r"],
            3,
        ),
        mes_fim=escapar(final_selic["rotulo"]),
        largura=num(final_selic["alto"] - final_selic["baixo"]),
    )

    # ---------------- Limitações ----------------
    limitacoes = (
        '<div class="limites limites-finais">'
        "<h3>Limitações do painel</h3>"
        '<div class="limites-lista">'
        "<h4>Do que os dados não cobrem</h4>"
        "<ul>"
        "<li><strong>Nenhuma série de emprego ou renda foi coletada.</strong> É a variável "
        "que a pesquisa aponta como determinante do atraso acima de 90 dias, com pico entre "
        "10 e 11 meses após a demissão, e o painel simplesmente não a enxerga.</li>"
        "<li><strong>Todas as séries são do sistema agregado.</strong> A pesquisa não "
        "encontrou nada específico sobre cooperativas de crédito. A carteira de quem vai "
        "decidir pode se comportar de forma diferente do Sistema Financeiro Nacional.</li>"
        "<li><strong>Não há abertura por modalidade.</strong> A recomendação de mudar o mix "
        "se apoia em estimativas de repasse por modalidade que vêm da pesquisa, não dos "
        "JSON. O painel não mede o mix da carteira de ninguém.</li>"
        "<li><strong>As séries terminam em meses diferentes</strong>, de {ate_comp} a "
        "{ate_selic}. O período comum às cinco séries tem {n_comum} meses.</li>"
        "</ul>"
        "<h4>Do que o método não permite</h4>"
        "<ul>"
        "<li><strong>Nada aqui é identificação causal.</strong> Toda a seção diagnóstica é "
        "correlação com defasagem, e inflação, emprego, renegociação e mudança de regra "
        "atuam ao mesmo tempo sem nenhum controle.</li>"
        "<li><strong>A defasagem não é identificável.</strong> As defasagens de {plato} meses "
        "são indistinguíveis entre si nos dados.</li>"
        "<li><strong>A projeção é extrapolação de reta</strong> e foi reprovada no próprio "
        "teste: perde para supor estabilidade em 6 meses nas quatro séries.</li>"
        "<li><strong>O limiar de significância supõe observações independentes</strong>, e "
        "séries mensais de macroeconomia são persistentes, o que infla a significância "
        "aparente. O n informado é número de pares, não de informação independente.</li>"
        "<li><strong>O painel não atribui probabilidade aos cenários.</strong> A faixa cobre "
        "80% dos erros históricos do método, e nada além disso está sendo afirmado.</li>"
        "</ul>"
        "<h4>Da evidência externa</h4>"
        "<ul>"
        "<li>A pesquisa usou <strong>6 fontes</strong> para gerar afirmações, e duas delas "
        "(Desenrola e razão de serviço da dívida do BIS) estão com confiança média, porque o "
        "trecho não foi conferido no documento original.</li>"
        "<li>A estimativa de que cerca de 70% da alta da inadimplência é contábil vale para o "
        "<strong>sistema agregado até junho de 2025</strong>, não para a série de pessoas "
        "físicas até {ate_inad}.</li>"
        "<li>O próprio arquivo de pesquisa registra que o processo foi interrompido antes da "
        "síntese, com cobertura menor do que o método pretendia.</li>"
        "<li><strong>A pesquisa nunca alterou um número deste painel.</strong> Onde ela "
        "sugeriria uma correção que os dados não têm, o painel manteve o dado e escreveu o "
        "aviso.</li>"
        "</ul>"
        "<h4>Da validade no tempo</h4>"
        "<ul>"
        "<li>O painel foi gerado em {gerado}. A mediana do Focus é revisada semanalmente e a "
        "que está aqui é de {div_focus}.</li>"
        "<li>O último mês da Selic ({mes_selic}) estava em curso na geração, com valor de "
        "{ref_selic}.</li>"
        "<li>As recomendações têm horizonte de seis meses, que é o da pergunta de decisão. "
        "Fora dele, nada do que está aqui foi testado.</li>"
        "</ul>"
        "</div></div>"
    ).format(
        ate_comp=prev_comp["ultimo"]["rotulo"],
        ate_selic=prev_selic["ultimo"]["rotulo"],
        n_comum=dados["periodo_comum"]["n"],
        plato=lista_pt(plato_inad),
        ate_inad=prev_inad["ultimo"]["rotulo"],
        gerado=hoje.strftime("%d/%m/%Y"),
        div_focus=escapar(focus_ano.get("data_divulgacao", "sem data")),
        mes_selic=ultimo_selic["rotulo"],
        ref_selic=escapar(ultimo_selic["data_origem"]),
    )

    corpo = (
        '<section id="prescritiva" class="secao">'
        '<header class="secao-cabecalho">'
        '<span class="secao-numero">Seção 4</span>'
        "<h2>Prescritiva: o que fazer</h2>"
        '<p class="secao-resumo">Três cenários de Selic e as ações que cada um sugere para a '
        "concessão a pessoas físicas nos próximos seis meses. Cada ação traz o dado que a "
        "sustenta, a evidência externa com fonte, o que se perde ao adotá-la e a condição "
        "que a derrubaria.</p>"
        "</header>"
        "{resposta}"
        '<h3 class="titulo-grupo">Os três cenários</h3>'
        '<div class="cards">{cartoes}</div>'
        '<figure class="grafico">'
        "<figcaption><h4>Trajetórias de Selic consideradas</h4>"
        '<p class="grafico-papel">Observado nos últimos {n_hist} meses e os três cenários até '
        "{mes_fim}.</p></figcaption>"
        '<div class="tela tela-alta"><canvas id="gr_cenarios"></canvas></div>'
        '<p class="ficha"><strong>Unidade:</strong> % ao ano. '
        "<strong>Observado:</strong> {de} a {ate}, fonte Banco Central do Brasil, SGS, série "
        "432. <strong>Cenários A e C:</strong> limites da faixa de 80% calculada sobre "
        "{n_teste} origens históricas do método. <strong>Cenário B:</strong> medianas do "
        "Focus, API Olinda, ligadas por interpolação linear feita neste painel. "
        "O painel não atribui probabilidade a nenhum dos três.</p></figure>"
        '<h3 class="titulo-grupo">Ações que valem nos três cenários</h3>'
        '<div class="acoes">{transversais}</div>'
        '<h3 class="titulo-grupo">Ação específica de cada cenário</h3>'
        '<div class="cenarios">{cenarios}</div>'
        '<h3 class="titulo-grupo">O que acompanhar todo mês</h3>'
        "{monitor}"
        "{limitacoes}"
        "</section>"
    ).format(
        resposta=resposta,
        cartoes=cartoes_cenario,
        n_hist=len(hist),
        mes_fim=escapar(final_selic["rotulo"]),
        de=hist[0]["rotulo"],
        ate=hist[-1]["rotulo"],
        n_teste=teste6_selic["n"],
        transversais="".join(acoes_transversais),
        cenarios=blocos_cenario,
        monitor=tabela_monitor,
        limitacoes=limitacoes,
    )

    return corpo, configuracoes


# ----------------------------------------------------------------------
# Montagem do painel
# ----------------------------------------------------------------------

ESTILO = """
:root{
  --tinta:#16202b; --tinta-fraca:#5b6b7b; --linha:#dde4ea; --fundo:#f6f8fa;
  --papel:#ffffff; --dado:#1f4e79; --pesquisa:#7a5c00; --interp:#3f3f46;
  --sobe:#9b2226; --cai:#2a6f4e;
}
*{box-sizing:border-box}
body{margin:0;background:var(--fundo);color:var(--tinta);
  font-family:"Segoe UI",system-ui,-apple-system,Helvetica,Arial,sans-serif;
  line-height:1.6;font-size:16px}
.envelope{max-width:1180px;margin:0 auto;padding:0 20px 80px}
header.topo{background:var(--papel);border-bottom:3px solid var(--dado);
  padding:34px 0 26px;margin-bottom:28px}
header.topo .envelope{padding-bottom:0}
.chapeu{text-transform:uppercase;letter-spacing:.14em;font-size:12px;
  color:var(--tinta-fraca);margin:0 0 10px}
header.topo h1{margin:0 0 14px;font-size:30px;line-height:1.25}
.pergunta{background:#eef4fa;border-left:5px solid var(--dado);padding:14px 18px;
  margin:0 0 16px;font-size:17px}
.pergunta strong{display:block;font-size:13px;text-transform:uppercase;
  letter-spacing:.08em;color:var(--dado);margin-bottom:4px}
.meta-topo{font-size:14px;color:var(--tinta-fraca);margin:0}
.indice{margin:16px 0 0;padding:0;list-style:none;display:flex;flex-wrap:wrap;gap:10px}
.indice li a{display:inline-block;padding:6px 12px;border:1px solid var(--linha);
  border-radius:999px;font-size:14px;text-decoration:none;color:var(--dado);background:#fff}
.indice li.pendente span{display:inline-block;padding:6px 12px;border:1px dashed var(--linha);
  border-radius:999px;font-size:14px;color:#9aa7b3}
.secao{background:var(--papel);border:1px solid var(--linha);border-radius:10px;
  padding:28px;margin-bottom:28px}
.secao-numero{display:inline-block;background:var(--dado);color:#fff;font-size:12px;
  letter-spacing:.1em;text-transform:uppercase;padding:4px 10px;border-radius:4px}
.secao h2{margin:12px 0 10px;font-size:25px}
.secao-resumo{margin:0;color:var(--tinta-fraca);max-width:80ch}
.avisos{background:#fbf9f1;border:1px solid #ece3c8;border-radius:8px;
  padding:16px 20px;margin:24px 0}
.avisos h3{margin:0 0 8px;font-size:15px;text-transform:uppercase;
  letter-spacing:.06em;color:#7a5c00}
.avisos ul{margin:0;padding-left:20px}
.avisos li{margin-bottom:6px;font-size:15px}
.titulo-grupo{margin:34px 0 16px;font-size:19px;padding-bottom:8px;
  border-bottom:1px solid var(--linha)}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(238px,1fr));gap:16px}
.card{border:1px solid var(--linha);border-radius:8px;padding:16px;background:#fff;
  display:flex;flex-direction:column}
.card-serie{margin:0;font-size:11px;letter-spacing:.1em;text-transform:uppercase;
  color:var(--tinta-fraca)}
.card h3{margin:4px 0 10px;font-size:15px;line-height:1.35;min-height:3em}
.card-valor{margin:0;font-size:34px;font-weight:700;line-height:1}
.card-unidade{display:block;font-size:12px;font-weight:400;color:var(--tinta-fraca);
  margin-top:4px}
.card-ref{margin:10px 0 0;font-size:13px;color:var(--tinta-fraca)}
.card-var{margin:8px 0 0;font-size:15px;font-weight:600}
.card-var.sobe{color:var(--sobe)} .card-var.cai{color:var(--cai)}
.card-var.neutro{color:var(--tinta-fraca)}
.card-base{margin:4px 0 0;font-size:12.5px;color:var(--tinta-fraca)}
.card-extremo{margin:8px 0 0;font-size:12.5px;font-weight:600;color:var(--sobe);
  background:#fdf0f0;border-radius:4px;padding:5px 8px}
.aviso-card{margin:8px 0 0;font-size:12.5px;color:#7a5c00;background:#fbf9f1;
  border-radius:4px;padding:5px 8px}
.graficos{display:grid;gap:22px}
.grafico{margin:0;border:1px solid var(--linha);border-radius:8px;padding:18px;background:#fff}
.grafico figcaption h4{margin:0 0 4px;font-size:17px}
.grafico-papel{margin:0 0 12px;font-size:14px;color:var(--tinta-fraca)}
.tela{position:relative;height:270px}
.ficha{margin:12px 0 0;font-size:12.5px;color:var(--tinta-fraca);
  border-top:1px solid var(--linha);padding-top:10px}
.ficha-extremos{border-top:none;padding-top:2px}
.insights{display:grid;gap:20px}
.insight{border:1px solid var(--linha);border-radius:8px;overflow:hidden;background:#fff}
.insight h4{margin:0;padding:14px 18px;font-size:17px;background:#f1f5f9;
  border-bottom:1px solid var(--linha)}
.camada{padding:14px 18px;border-bottom:1px solid var(--linha)}
.camada:last-child{border-bottom:none}
.camada p{margin:0 0 8px} .camada p:last-child{margin-bottom:0}
.rotulo-camada{display:inline-block;font-size:11px;letter-spacing:.1em;
  text-transform:uppercase;font-weight:700;margin-bottom:8px;padding:3px 8px;border-radius:4px}
.camada-dado{border-left:5px solid var(--dado)}
.camada-dado .rotulo-camada{background:#e8f0f8;color:var(--dado)}
.camada-pesquisa{border-left:5px solid var(--pesquisa);background:#fdfbf4}
.camada-pesquisa .rotulo-camada{background:#f6eccd;color:var(--pesquisa)}
.camada-interpretacao{border-left:5px solid var(--interp);background:#fafafa}
.camada-interpretacao .rotulo-camada{background:#e8e8ea;color:var(--interp)}
.citacao{font-size:15px}
.tag-ref{display:inline-block;background:var(--pesquisa);color:#fff;font-size:11px;
  font-weight:700;padding:2px 7px;border-radius:4px;margin-right:8px;vertical-align:1px}
.fonte{display:block;font-size:12.5px;color:var(--tinta-fraca);margin-top:6px}
.fonte a{color:var(--dado)}
.card-diag .card-valor{font-size:30px}
.card-diag h3{min-height:2.2em}
.rolagem{overflow-x:auto;border:1px solid var(--linha);border-radius:8px}
.tabela{border-collapse:collapse;width:100%;font-size:13.5px;background:#fff}
.tabela th,.tabela td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--linha)}
.tabela thead th{background:#f1f5f9;text-align:center;font-size:12.5px;
  border-bottom:2px solid var(--linha);position:sticky;top:0}
.tabela tbody tr:nth-child(even){background:#fafbfc}
.tabela td:first-child{text-align:center}
.tabela td.n{color:var(--tinta-fraca);font-size:12px;border-right:1px solid var(--linha)}
.tabela td.acima{color:var(--dado);font-weight:600}
.tabela td.abaixo{color:#9aa7b3}
.tabela td.pior{color:var(--sobe);font-weight:600}
.tela-alta{height:300px}
.bloco{margin:26px 0;border:1px solid var(--linha);border-radius:10px;overflow:hidden}
.bloco-titulo{padding:16px 20px;border-bottom:1px solid var(--linha)}
.bloco-titulo h3{margin:6px 0 6px;font-size:20px;border:none;padding:0}
.bloco-titulo p{margin:0;font-size:14.5px;color:var(--tinta-fraca);max-width:85ch}
.bloco-tag{display:inline-block;width:26px;height:26px;line-height:26px;text-align:center;
  border-radius:50%;font-weight:700;font-size:13px;color:#fff}
.bloco-a{border-left:6px solid var(--dado)}
.bloco-a .bloco-titulo{background:#eef4fa} .bloco-a .bloco-tag{background:var(--dado)}
.bloco-b{border-left:6px solid var(--cai)}
.bloco-b .bloco-titulo{background:#f2f8f4} .bloco-b .bloco-tag{background:var(--cai)}
.bloco-c{border-left:6px solid var(--pesquisa)}
.bloco-c .bloco-titulo{background:#fbf9f1} .bloco-c .bloco-tag{background:var(--pesquisa)}
.bloco>.graficos,.bloco>.cards,.bloco>.insights,.bloco>.rolagem,.bloco>.ficha,
.bloco>.comparacao{margin:18px 20px}
.bloco>.rolagem{margin-bottom:8px}
.numeros-prev{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:12px;margin:0 0 16px;padding:12px;background:#f8fafb;border-radius:6px}
.num-item{display:flex;flex-direction:column}
.num-item span{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--tinta-fraca)}
.num-item strong{font-size:20px;margin:2px 0}
.num-item strong.sobe{color:var(--sobe)} .num-item strong.cai{color:var(--cai)}
.num-item small{font-size:12px;color:var(--tinta-fraca)}
.nota-virada{color:#7a5c00;background:#fbf9f1;border-radius:6px;padding:8px 12px;
  border-top:none}
.card-focus{border-left:4px solid var(--cai)}
.comparacao{border:2px solid var(--cai);border-radius:8px;padding:16px 20px;background:#f7fcf9}
.comparacao h4{margin:0 0 12px;font-size:16px}
.comparacao p{margin:12px 0 0;font-size:14.5px}
.comparacao-linha{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px}
.lado{background:#fff;border:1px solid var(--linha);border-radius:6px;padding:12px;
  display:flex;flex-direction:column}
.lado span{font-size:11.5px;text-transform:uppercase;letter-spacing:.06em;
  color:var(--tinta-fraca)}
.lado strong{font-size:26px;margin:4px 0}
.lado small{font-size:12px;color:var(--tinta-fraca)}
.lado-modelo{border-top:3px solid var(--dado)}
.lado-focus{border-top:3px solid var(--cai)}
.lado-dif{border-top:3px solid var(--tinta-fraca)}
.resposta{border:2px solid var(--dado);border-radius:8px;background:#eef4fa;
  padding:18px 22px;margin:24px 0}
.resposta h3{margin:0 0 10px;font-size:13px;text-transform:uppercase;letter-spacing:.08em;
  color:var(--dado);border:none;padding:0}
.resposta-frase{font-size:20px;font-weight:700;line-height:1.4;margin:0 0 14px}
.resposta p{margin:0 0 10px;font-size:15px}
.resposta ul{margin:0 0 10px;padding-left:20px} .resposta li{margin-bottom:6px;font-size:15px}
.card-cenario h3{min-height:2.6em}
.card-cenario.cen-a{border-top:4px solid var(--cai)}
.card-cenario.cen-b{border-top:4px solid var(--dado)}
.card-cenario.cen-c{border-top:4px solid var(--sobe)}
.acoes,.cenarios{display:grid;gap:20px}
.acao{border:1px solid var(--linha);border-radius:8px;overflow:hidden;background:#fff}
.acao h4{margin:0;padding:13px 18px 4px;font-size:17px}
.acao-frase{margin:0;padding:0 18px 13px;font-size:15px;color:var(--tinta-fraca);
  border-bottom:1px solid var(--linha)}
.acao-campos{display:grid;grid-template-columns:1fr 1fr}
.campo{padding:14px 18px;border-bottom:1px solid var(--linha)}
.campo:nth-child(odd){border-right:1px solid var(--linha)}
.campo>span{display:block;font-size:11px;letter-spacing:.09em;text-transform:uppercase;
  font-weight:700;margin-bottom:8px}
.campo p{margin:0 0 8px;font-size:14.5px} .campo p:last-child{margin-bottom:0}
.campo-dado{border-left:4px solid var(--dado)} .campo-dado>span{color:var(--dado)}
.campo-evidencia{background:#fdfbf4;border-left:4px solid var(--pesquisa)}
.campo-evidencia>span{color:var(--pesquisa)}
.campo-tradeoff{border-left:4px solid #6d28d9} .campo-tradeoff>span{color:#6d28d9}
.campo-invalida{background:#fdf6f6;border-left:4px solid var(--sobe)}
.campo-invalida>span{color:var(--sobe)}
.cenario{border:1px solid var(--linha);border-radius:8px;overflow:hidden}
.cenario-cabeca{padding:14px 18px;border-bottom:1px solid var(--linha)}
.cenario-cabeca h4{margin:0 0 6px;font-size:18px}
.cenario-cabeca p{margin:0;font-size:14px;color:var(--tinta-fraca)}
.cenario.cen-a .cenario-cabeca{background:#f2f8f4;border-left:6px solid var(--cai)}
.cenario.cen-b .cenario-cabeca{background:#eef4fa;border-left:6px solid var(--dado)}
.cenario.cen-c .cenario-cabeca{background:#fdf0f0;border-left:6px solid var(--sobe)}
.cenario .acao{border:none;border-radius:0}
.tabela-monitor td.esq,.tabela-monitor th{text-align:left}
.tabela-monitor td{font-size:14px;vertical-align:top}
.limites-finais{margin-top:34px}
.limites-lista{padding:18px 22px;background:#fff}
.limites-lista h4{margin:14px 0 8px;font-size:13px;text-transform:uppercase;
  letter-spacing:.07em;color:var(--dado)}
.limites-lista h4:first-child{margin-top:0}
.limites-lista ul{margin:0;padding-left:20px}
.limites-lista li{margin-bottom:7px;font-size:14.5px}
@media (max-width:760px){.acao-campos{grid-template-columns:1fr}
  .campo:nth-child(odd){border-right:none}}
.limites{margin-top:30px;border:2px solid var(--dado);border-radius:8px;overflow:hidden}
.limites h3{margin:0;padding:14px 18px;background:var(--dado);color:#fff;font-size:17px}
.limites-colunas{display:grid;grid-template-columns:1fr 1fr;gap:0}
.limites-colunas>div{padding:16px 20px}
.permite{background:#f2f8f4;border-right:1px solid var(--linha)}
.nao-permite{background:#fdf6f6}
.limites h4{margin:0 0 10px;font-size:14px;text-transform:uppercase;letter-spacing:.06em}
.permite h4{color:var(--cai)} .nao-permite h4{color:var(--sobe)}
.limites ul{margin:0;padding-left:20px} .limites li{margin-bottom:8px;font-size:14.5px}
@media (max-width:760px){.limites-colunas{grid-template-columns:1fr}
  .permite{border-right:none;border-bottom:1px solid var(--linha)}}
.sem-grafico{background:#fdf0f0;border:1px solid #f0d0d0;border-radius:8px;padding:14px 18px;
  font-size:14px;color:var(--sobe);margin:0 0 22px;display:none}
.rodape{font-size:13px;color:var(--tinta-fraca);text-align:center;padding-top:10px}
@media (max-width:640px){
  .secao{padding:18px} header.topo h1{font-size:23px} .card-valor{font-size:28px}
  .tela{height:230px}
}
"""

SCRIPT = """
(function(){
  var configs = __CONFIGS__;
  var alerta = document.getElementById("sem-grafico");
  if (typeof Chart === "undefined") {
    if (alerta) { alerta.style.display = "block"; }
    return;
  }
  Chart.defaults.font.family = "Segoe UI, system-ui, Helvetica, Arial, sans-serif";

  function formatar(valor, casas){
    if (valor === null || valor === undefined) { return "sem dado"; }
    return Number(valor).toFixed(casas).replace(".", ",");
  }

  configs.forEach(function(cfg){
    var alvo = document.getElementById(cfg.alvo);
    if (!alvo) { return; }
    var casas = (cfg.casas === undefined) ? 2 : cfg.casas;
    var unidade = cfg.unidade || "";
    var series = cfg.series ||
      [{ nome: cfg.nome, valores: cfg.valores, cor: cfg.cor }];
    var varias = series.length > 1;

    var datasets = series.map(function(s){
      var d = {
        label: s.nome,
        data: s.valores,
        borderColor: s.cor,
        backgroundColor: s.cor,
        borderWidth: 2,
        pointRadius: s.pontos ? 3 : 0,
        pointHoverRadius: 4,
        tension: 0.15,
        fill: false
      };
      if (s.tipo) { d.type = s.tipo; }
      if (s.tracejado) { d.borderDash = [6, 4]; }
      if (s.preencherAte !== undefined) {
        d.fill = { target: s.preencherAte, above: s.corPreenchimento,
                   below: s.corPreenchimento };
        d.borderWidth = 1;
      }
      return d;
    });

    new Chart(alvo, {
      type: cfg.tipo || "line",
      data: { labels: cfg.rotulos, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            display: varias,
            position: "bottom",
            labels: { boxWidth: 12, usePointStyle: true, padding: 14 }
          },
          tooltip: {
            callbacks: {
              label: function(ctx){
                var prefixo = (varias && ctx.dataset.label)
                  ? ctx.dataset.label + ": " : "";
                var sufixo = unidade ? " " + unidade : "";
                return prefixo + formatar(ctx.parsed.y, casas) + sufixo;
              }
            }
          }
        },
        scales: {
          x: {
            ticks: { maxTicksLimit: cfg.maxticks || 12, autoSkip: true, maxRotation: 0 },
            grid: { display: false },
            title: cfg.tituloX ? { display: true, text: cfg.tituloX } : { display: false }
          },
          y: {
            ticks: { callback: function(v){ return formatar(v, casas); } },
            grid: { color: "#eef2f5" },
            suggestedMin: cfg.min,
            suggestedMax: cfg.max,
            title: cfg.tituloY ? { display: true, text: cfg.tituloY } : { display: false }
          }
        }
      }
    });
  });
})();
"""


def montar_painel(secoes_html, configuracoes, gerado_em, coletas, registro, pendentes):
    itens = [
        '<li><a href="#{}">{}</a></li>'.format(s["id"], escapar(s["rotulo"]))
        for s in registro
    ]
    itens += [
        '<li class="pendente"><span>{}</span></li>'.format(escapar(p))
        for p in pendentes
    ]
    indice = '<ul class="indice">' + "".join(itens) + "</ul>"

    avisos_coleta = ""
    desatualizadas = [c for c in coletas if not c["atualizado"]]
    if desatualizadas:
        itens = "".join(
            "<li>{} (série {}), coleta de {}.</li>".format(
                escapar(c["nome"]), escapar(c["codigo"]), escapar(c["coletado_em"])
            )
            for c in desatualizadas
        )
        avisos_coleta = (
            '<div class="avisos"><h3>Dados não atualizados nesta coleta</h3>'
            "<ul>{}</ul></div>".format(itens)
        )

    partes = [
        "<!DOCTYPE html>",
        '<html lang="pt-BR">',
        "<head>",
        '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>Painel Selic e Crédito</title>",
        '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>',
        "<style>" + ESTILO + "</style>",
        "</head>",
        "<body>",
        '<header class="topo"><div class="envelope">',
        '<p class="chapeu">Painel de apoio à decisão</p>',
        "<h1>Selic e crédito às famílias no Brasil</h1>",
        '<div class="pergunta"><strong>Pergunta de decisão</strong>{}</div>'.format(
            escapar(PERGUNTA_DECISAO)
        ),
        '<p class="meta-topo">Gerado em {}. Dados: Banco Central do Brasil, '
        "APIs SGS e Olinda. Contexto externo: pesquisa_contexto.md.</p>".format(gerado_em),
        indice,
        "</div></header>",
        '<div class="envelope">',
        '<div class="sem-grafico" id="sem-grafico">Os gráficos não carregaram. '
        "O painel usa Chart.js pela CDN e precisa de conexão com a internet na "
        "primeira abertura. Os números dos cards e dos textos não dependem disso.</div>",
        avisos_coleta,
    ]
    partes.extend(secoes_html)
    partes.extend(
        [
            '<p class="rodape">Painel gerado por analise.py. '
            "Números das séries do SGS e da API Olinda. "
            "Contexto externo com fonte e URL em cada citação.</p>",
            "</div>",
            "<script>" + SCRIPT.replace("__CONFIGS__", json.dumps(configuracoes)) + "</script>",
            "</body>",
            "</html>",
        ]
    )
    return "\n".join(partes)


# Registro das seções do painel. Cada etapa acrescenta uma entrada aqui e
# remove o título correspondente de SECOES_PENDENTES. As seções já validadas
# não são alteradas.
REGISTRO_SECOES = [
    {"id": "descritiva", "rotulo": "1. Descritiva", "fn": secao_1_descritiva},
    {"id": "diagnostica", "rotulo": "2. Diagnóstica", "fn": secao_2_diagnostica},
    {"id": "preditiva", "rotulo": "3. Preditiva", "fn": secao_3_preditiva},
    {"id": "prescritiva", "rotulo": "4. Prescritiva", "fn": secao_4_prescritiva},
]

SECOES_PENDENTES = []


def main():
    hoje = date.today()
    dados = {}
    coletas = []

    for serie in SERIES:
        bruto = carregar(serie["arquivo"])
        mensal = para_mensal(bruto, serie["diaria"])
        if not mensal:
            raise SystemExit(
                "Série {} sem observações utilizáveis.".format(serie["codigo"])
            )
        faltando = meses_faltando(mensal)
        dados[serie["chave"]] = {
            "config": serie,
            "mensal": mensal,
            "variacao_12m": variacao_12_meses(mensal),
            "faltando": faltando,
            "parcial": mes_em_curso(mensal, hoje) if serie["diaria"] else False,
        }
        coletas.append(
            {
                "nome": serie["nome"],
                "codigo": serie["codigo"],
                "atualizado": bruto.get("atualizado_nesta_execucao", True),
                "coletado_em": bruto.get("coletado_em", "desconhecida"),
            }
        )

    # Focus. É expectativa, não série observada, então entra separado.
    caminho_focus = os.path.join(PASTA_DADOS, ARQUIVO_FOCUS)
    if os.path.exists(caminho_focus):
        bruto_focus = carregar(ARQUIVO_FOCUS)
        dados["focus"] = {
            "medianas": bruto_focus.get("medianas_selecionadas"),
            "coletado_em": bruto_focus.get("coletado_em", "desconhecida"),
        }
        coletas.append(
            {
                "nome": "Focus, expectativa anual para a Selic",
                "codigo": "Olinda",
                "atualizado": bruto_focus.get("atualizado_nesta_execucao", True),
                "coletado_em": bruto_focus.get("coletado_em", "desconhecida"),
            }
        )
    else:
        dados["focus"] = None
        print("AVISO: {} não encontrado. A seção preditiva vai sem o Focus.".format(
            ARQUIVO_FOCUS
        ))

    inicios = [dados[s["chave"]]["mensal"][0] for s in SERIES]
    fins = [dados[s["chave"]]["mensal"][-1] for s in SERIES]
    de_comum = max(inicios, key=lambda p: (p["ano"], p["mes"]))
    ate_comum = min(fins, key=lambda p: (p["ano"], p["mes"]))
    n_comum = (
        (ate_comum["ano"] - de_comum["ano"]) * 12 + ate_comum["mes"] - de_comum["mes"] + 1
    )
    dados["periodo_comum"] = {
        "de": de_comum["rotulo"],
        "ate": ate_comum["rotulo"],
        "n": n_comum,
    }
    dados["periodo_total"] = {
        "de": min(inicios, key=lambda p: (p["ano"], p["mes"]))["rotulo"],
        "ate": max(fins, key=lambda p: (p["ano"], p["mes"]))["rotulo"],
    }

    corpos = []
    configuracoes = []
    for secao in REGISTRO_SECOES:
        corpo, config = secao["fn"](dados, hoje)
        corpos.append(corpo)
        configuracoes.extend(config)

    html = montar_painel(
        corpos,
        configuracoes,
        hoje.strftime("%d/%m/%Y"),
        coletas,
        REGISTRO_SECOES,
        SECOES_PENDENTES,
    )
    with open(ARQUIVO_PAINEL, "w", encoding="utf-8") as destino:
        destino.write(html)

    print("Painel gerado: {}".format(ARQUIVO_PAINEL))
    print(
        "Seções no painel: {} de 4 ({})".format(
            len(REGISTRO_SECOES),
            ", ".join(s["id"] for s in REGISTRO_SECOES),
        )
    )
    print("")
    print("{:<52} {:>10} {:>12} {:>14}".format("Série", "Último", "Referência", "Var. 12 meses"))
    print("-" * 92)
    for serie in SERIES:
        info = dados[serie["chave"]]
        ultimo = info["mensal"][-1]
        variacao = info["variacao_12m"][0]
        print(
            "{:<52} {:>10} {:>12} {:>14}".format(
                serie["nome"][:52],
                num(ultimo["valor"]),
                ultimo["data_origem"],
                num_sinal(variacao) + " p.p." if variacao is not None else "sem par",
            )
        )
    print("-" * 92)
    print(
        "Período comum às cinco séries: {} a {} ({} meses).".format(
            dados["periodo_comum"]["de"],
            dados["periodo_comum"]["ate"],
            dados["periodo_comum"]["n"],
        )
    )
    for serie in SERIES:
        faltando = dados[serie["chave"]]["faltando"]
        if faltando:
            print(
                "AVISO: série {} com {} meses faltando: {}".format(
                    serie["codigo"], len(faltando), ", ".join(faltando)
                )
            )
    if not any(dados[s["chave"]]["faltando"] for s in SERIES):
        print("Nenhum mês faltando nas cinco séries. Nenhum valor foi preenchido.")
    if dados["selic"]["parcial"]:
        print(
            "AVISO: o último mês da Selic ({}) está em curso e foi marcado no painel.".format(
                dados["selic"]["mensal"][-1]["rotulo"]
            )
        )

    print("")
    print("Diagnóstica: correlação da Selic defasada de 0 a 18 meses")
    print("-" * 92)
    selic_dic = como_dicionario(dados["selic"]["mensal"])
    for alvo in ALVOS_DIAGNOSTICO:
        serie = como_dicionario(dados[alvo["chave"]]["mensal"])
        niveis = correlograma(selic_dic, serie, DEFASAGENS)
        difs = correlograma(selic_dic, serie, DEFASAGENS, diferenca=True)
        antes = correlograma(selic_dic, serie, DEFASAGENS, ate=CORTE_CONTABIL)
        p_niveis, p_difs, p_antes = pico(niveis), pico(difs), pico(antes)
        print("{} (série {})".format(alvo["curto"], alvo["codigo"]))
        print(
            "  níveis:    pico r = {} em {} meses, n = {}, limiar 5% = {}. Platô: {} meses.".format(
                num(p_niveis["r"], 3),
                p_niveis["defasagem"],
                p_niveis["n"],
                num(p_niveis["limiar"], 3),
                lista_pt(plato(niveis)),
            )
        )
        print(
            "  variações: pico r = {} em {} meses, n = {}, limiar 5% = {}. Platô: {} meses.".format(
                num(p_difs["r"], 3),
                p_difs["defasagem"],
                p_difs["n"],
                num(p_difs["limiar"], 3),
                lista_pt(plato(difs)),
            )
        )
        print(
            "  até dez/2024: pico r = {} em {} meses, n = {}.".format(
                num(p_antes["r"], 3), p_antes["defasagem"], p_antes["n"]
            )
        )
    ipca_dic = como_dicionario(dados["ipca"]["mensal"])
    conf = correlograma(selic_dic, ipca_dic, [0, 12])
    print(
        "Confusão medida: Selic vs IPCA 12m, r = {} em 0 meses (n = {}) e "
        "r = {} em 12 meses (n = {}).".format(
            num(conf[0]["r"], 3), conf[0]["n"], num(conf[1]["r"], 3), conf[1]["n"]
        )
    )

    print("")
    print("Preditiva: inclinação de 6 meses, projeção de 6 meses e teste do método")
    print("-" * 92)
    for serie in SERIES_PREDITIVAS:
        prev = calcular_previsao(dados[serie["chave"]]["mensal"])
        final = prev["projecao"][-1]
        teste = prev["teste"][HORIZONTE]
        print(
            "{:<26} inclinação {} p.p./mês | projeção {} em {} | faixa {} a {}".format(
                serie["curto"][:26],
                num_sinal(prev["inclinacao_6m"], 3),
                num(final["central"]),
                final["rotulo"],
                num(final["baixo"]),
                num(final["alto"]),
            )
        )
        print(
            "{:<26} teste em 6 meses: erro do modelo {} p.p. contra {} p.p. sem mudança "
            "({} em {} origens)".format(
                "",
                num(teste["eam"], 3),
                num(teste["eam_sem_mudanca"], 3),
                num_sinal(100 * teste["ganho"], 0) + "%",
                teste["n"],
            )
        )
    if dados.get("focus") and dados["focus"].get("medianas"):
        for rotulo_item, item in dados["focus"]["medianas"].items():
            print(
                "Focus {}: mediana {} para {} (divulgado em {}, {} respondentes).".format(
                    rotulo_item,
                    num(item["mediana"]) if item.get("mediana") is not None else "sem dado",
                    item.get("ano_referencia"),
                    item.get("data_divulgacao"),
                    item.get("numero_respondentes"),
                )
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
