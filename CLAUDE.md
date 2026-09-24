# CLAUDE.md

Painel Selic e Crédito. Contexto permanente do projeto e plano de construção.

## Quem é o usuário e como trabalhamos

O usuário é analista de dados e constrói este projeto em etapas, validando cada
uma antes de avançar.

Regras de trabalho:

- O usuário pede uma etapa por vez, com a frase "Execute a etapa N".
- Ao terminar a etapa, rode o que for preciso, mostre um resumo curto do que fez
  e PARE. Não avance para a etapa seguinte por conta própria.
- Não programe nada antes de receber a frase "Execute a etapa N".
- Cada etapa ACRESCENTA uma seção ao painel. Nunca recrie o painel do zero nem
  altere seções já validadas sem o usuário pedir.

## Decisão que o painel apoia

Um gerente de crédito de uma cooperativa precisa decidir se aperta ou afrouxa a
concessão a pessoas físicas nos próximos seis meses.

## Duas camadas de evidência

### Camada 1: dados oficiais em JSON

Dados reais das APIs do Banco Central. Nunca dados sintéticos.

No coletor, manter `dataInicial=01/01/2017` e calcular `dataFinal` como a data de
hoje no formato dd/mm/aaaa.

| Série | Código | URL |
|---|---|---|
| Selic meta, diária | 432 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados?formato=json&dataInicial=01/01/2017&dataFinal=19/09/2026 |
| IPCA acumulado 12 meses | 13522 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.13522/dados?formato=json&dataInicial=01/01/2017&dataFinal=19/09/2026 |
| Endividamento das famílias | 29037 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.29037/dados?formato=json&dataInicial=01/01/2017&dataFinal=19/09/2026 |
| Comprometimento de renda das famílias | 29034 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.29034/dados?formato=json&dataInicial=01/01/2017&dataFinal=19/09/2026 |
| Inadimplência de pessoa física | 21084 | https://api.bcb.gov.br/dados/serie/bcdata.sgs.21084/dados?formato=json&dataInicial=01/01/2017&dataFinal=19/09/2026 |

Focus, expectativa anual para a Selic (API Olinda):

```
https://olinda.bcb.gov.br/olinda/servico/Expectativas/versao/v1/odata/ExpectativasMercadoAnuais?$filter=Indicador%20eq%20'Selic'&$orderby=Data%20desc&$top=50&$format=json
```

Cuidados com as APIs do BCB:

- A API SGS pode devolver HTTP 200 com uma página HTML quando recusa a
  requisição. Validar que o corpo começa com `[` e tentar até 3 vezes, com pausa
  entre as tentativas e mensagem clara de erro.
- A série diária (432) exige `dataInicial` e `dataFinal` e aceita no máximo
  10 anos por requisição.
- Na API Olinda, montar a URL à mão, exatamente como acima, com `%20`. Não usar
  `params=` do requests. Do retorno, usar `Data`, `DataReferencia` e `Mediana`:
  mediana mais recente para o fim deste ano e do próximo.
- Se uma API falhar, o projeto continua: usar os arquivos já salvos em `dados/`
  e avisar no painel que aquele dado não foi atualizado.

### Camada 2: pesquisa profunda

Arquivo `pesquisa_contexto.md`, produzido na etapa 2, logo após a coleta.

- Ponto de partida: o problema deste briefing e o que os JSON mostram.
- Tema: como a Selic se transmite ao crédito das famílias no Brasil. Defasagens
  documentadas, comprometimento de renda, inadimplência PF e fatores além dos
  juros (emprego, renda, inflação, renegociação, regulação).
- Fontes, nesta ordem: Banco Central (comunicados e atas do Copom, Relatório de
  Política Monetária, Relatório de Economia Bancária, estatísticas de crédito),
  IBGE, Ipea e literatura acadêmica. Imprensa só como complemento.
- Limite: no máximo 8 fontes e cerca de 8 minutos. Preferir poucas fontes boas a
  muitas superficiais.
- Saída: tabela de afirmação, evidência, fonte, URL, data e grau de confiança
  (alto, médio, baixo), seguida de um resumo de até 10 linhas.
- Só registrar o que foi de fato lido na fonte. Nunca inventar URL, número ou
  citação. Sem evidência, escrever "não encontrado".
- Nenhuma análise nesta etapa.
- Se a busca na web não estiver disponível ou o usuário já tiver fornecido um
  `pesquisa_contexto.md`, usar o arquivo existente e avisar.

### Como as duas camadas se combinam

- Números, variações, correlações e projeções vêm SEMPRE dos JSON. A pesquisa
  nunca altera, completa ou substitui um valor.
- A pesquisa serve para contextualizar, discutir mecanismos, defasagens
  plausíveis, variáveis de confusão e riscos.
- Em todo insight do painel, separar visualmente: "Dado observado", "Contexto da
  pesquisa" (com a fonte) e "Interpretação".
- Se o dado e a pesquisa divergirem, mostrar a divergência. Não escolher um lado.

## Entrega final

Um único arquivo `painel.html`, que abre sem servidor, com a pergunta de decisão
e a data de geração no topo e quatro seções:

1. Descritiva: o que aconteceu.
2. Diagnóstica: por que aconteceu (correlação com defasagem de 0 a 18 meses).
3. Preditiva: tendência simples (média móvel de 6 meses, inclinação recente,
   projeção de 6 meses com faixa de incerteza), Focus ao lado, sem machine
   learning. Separar projeção do modelo, consenso externo e incertezas.
4. Prescritiva: três cenários de Selic. Para cada ação: dado quantitativo,
   evidência externa, trade-off e condição que invalidaria a recomendação.
   Fechar com as limitações do painel.

## Restrições técnicas

- Python 3 simples: biblioteca padrão e `requests`. Nada de pandas ou numpy.
- Estrutura de arquivos:

```
coletor.py
analise.py
painel.html
pesquisa_contexto.md
dados/
  selic_432.json
  ipca12m_13522.json
  endividamento_29037.json
  comprometimento_29034.json
  inadimplencia_pf_21084.json
  focus_selic.json
```

- Gráficos com Chart.js via CDN (cdnjs), a mesma biblioteca em todas as etapas.
- Tudo em frequência mensal. Para a Selic, último valor de cada mês. Nunca
  preencher dado ausente sem avisar.
- Variações de taxas sempre em pontos percentuais.
- Todo gráfico com unidade, período e fonte (Banco Central do Brasil, SGS,
  código da série). Todo card com a data de referência do dado.
- Textos em português do Brasil, linguagem simples, sem travessões.
- Distinguir sempre associação de causa e informar o número de observações de
  cada cálculo.

## Plano de construção em 6 etapas

Dependência geral: as etapas 3 a 6 dependem dos JSON em `dados/` (etapa 1) e de
`pesquisa_contexto.md` (etapa 2). Nenhuma delas pode gerar número fora dos JSON
nem contexto fora do `pesquisa_contexto.md`.

### Etapa 1: coletor

- Criar `coletor.py`.
- Baixar as 5 séries do SGS e o Focus da Olinda, com `dataInicial=01/01/2017` e
  `dataFinal` igual à data de hoje.
- Aplicar os cuidados com as APIs descritos acima (validar corpo começando com
  `[`, até 3 tentativas com pausa, mensagem clara de erro, URL da Olinda montada
  à mão).
- Salvar um JSON por série em `dados/`, com os nomes definidos na estrutura.
- Se uma API falhar, manter o arquivo anterior e registrar o aviso.
- Entregável: `coletor.py` e a pasta `dados/` preenchida.
- Saída para o usuário: resumo curto com série, período coberto, número de
  observações e data do último dado de cada arquivo.

### Etapa 2: pesquisa profunda

- Depende da etapa 1: partir do problema do briefing e do que os JSON mostram.
- Seguir as regras da Camada 2 (ordem das fontes, máximo 8 fontes, cerca de
  8 minutos, só o que foi lido de fato, "não encontrado" quando faltar
  evidência).
- Entregável: `pesquisa_contexto.md` na raiz, com a tabela de afirmação,
  evidência, fonte, URL, data e grau de confiança, mais o resumo de até
  10 linhas.
- Nenhuma análise e nenhuma alteração no painel nesta etapa.
- Saída para o usuário: resumo curto com quantas fontes foram lidas e quais
  afirmações ficaram com confiança alta, média e baixa.

### Etapa 3: descritiva

- Depende dos JSON de `dados/` e de `pesquisa_contexto.md`.
- Criar `analise.py` e gerar `painel.html` com o cabeçalho (pergunta de decisão
  e data de geração) e a primeira seção.
- Conteúdo: o que aconteceu com Selic, IPCA 12 meses, endividamento,
  comprometimento de renda e inadimplência PF desde 2017, em frequência mensal.
- Cards com valor atual, data de referência e variação em pontos percentuais.
- Gráficos Chart.js com unidade, período e fonte.
- Separar "Dado observado", "Contexto da pesquisa" e "Interpretação".
- Entregável: `analise.py` e `painel.html` com a seção 1.

### Etapa 4: diagnóstica

- Depende dos JSON de `dados/` e de `pesquisa_contexto.md`.
- ACRESCENTAR a seção 2 ao `painel.html` sem alterar a seção 1.
- Conteúdo: correlação entre Selic e cada série de crédito com defasagem de 0 a
  18 meses, informando o número de observações de cada cálculo.
- Confrontar a defasagem observada nos dados com as defasagens documentadas na
  pesquisa. Se divergirem, mostrar a divergência.
- Deixar explícito que correlação não é causa e citar as variáveis de confusão
  levantadas na pesquisa.

### Etapa 5: preditiva

- Depende dos JSON de `dados/` e de `pesquisa_contexto.md`.
- ACRESCENTAR a seção 3 ao `painel.html` sem alterar as seções 1 e 2.
- Conteúdo: média móvel de 6 meses, inclinação recente e projeção de 6 meses com
  faixa de incerteza. Sem machine learning.
- Mostrar o Focus ao lado, com `DataReferencia` e `Mediana` para o fim deste ano
  e do próximo.
- Separar claramente projeção do modelo, consenso externo (Focus) e incertezas.

### Etapa 6: prescritiva

- Depende dos JSON de `dados/` e de `pesquisa_contexto.md`.
- ACRESCENTAR a seção 4 ao `painel.html` sem alterar as seções 1, 2 e 3.
- Conteúdo: três cenários de Selic. Para cada ação recomendada, apresentar dado
  quantitativo (dos JSON), evidência externa (da pesquisa, com fonte),
  trade-off e condição que invalidaria a recomendação.
- Fechar com as limitações do painel.
- Responder de forma direta à pergunta de decisão: apertar ou afrouxar a
  concessão a pessoas físicas nos próximos seis meses.
