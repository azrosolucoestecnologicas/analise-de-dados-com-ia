# Pesquisa de contexto — Selic e crédito às famílias no Brasil

Camada de **evidência externa** do painel. Não contém nenhum número calculado a
partir das séries do SGS: isso é a camada de evidência dos dados, que vive em
`analise.py`. Aqui só entram afirmações de fontes publicadas, cada uma com origem
verificável.

- **Produzido em:** 18/09/2026, por pesquisa assistida por IA com verificação adversarial.
- **Escopo:** defasagens da transmissão da Selic ao crédito PF; fatores além dos juros;
  por que inadimplência é indicador de resultado e comprometimento de renda é antecedente.
- **Como ler o grau de confiança:**
  - **alta** — trecho citado conferido palavra por palavra no PDF da fonte, em 18/09/2026.
  - **média** — a fonte existe e responde, mas o trecho não foi conferido no documento original.
  - Nenhuma afirmação aqui é de confiança baixa: as que não passaram na verificação foram descartadas.

> **Limitação desta pesquisa.** O processo previa 101 agentes de busca e verificação;
> 31 foram interrompidos por limite de sessão, e a etapa de síntese não rodou. A cobertura
> é menor do que o método pretendia, sobretudo nas afirmações sobre *pass-through* de juros.
> As 35 URLs coletadas foram testadas uma a uma: todas responderam HTTP 200, nenhuma
> é inventada. Mesmo assim, **abra o link antes de citar em aula.**

---

## A · Afirmações verificadas na fonte (confiança alta)

### A1 · A inadimplência é um indicador defasado por construção contábil

- **Afirmação:** uma operação só é classificada como inadimplente depois de três meses de
  atraso. Não é uma escolha estatística: é a definição regulatória. Qualquer defasagem
  medida entre juros e inadimplência já embute esse piso.
- **Evidência:** *"o que ocorre quando há algum pagamento com três meses de atraso"*
- **Fonte:** Banco Central do Brasil, Relatório de Política Monetária, boxe *Impacto na taxa
  de inadimplência decorrente das novas regras de contabilização de instrumentos financeiros*
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf
- **Data:** setembro/2025
- **Confiança:** alta
- **Uso no painel:** sustenta tratar a série 21084 como indicador de resultado (*lagging*),
  na seção diagnóstica.

### A2 · O tempo até a baixa a prejuízo alonga ainda mais a defasagem

- **Afirmação:** sob as regras vigentes desde 2025, o provisionamento integral de uma operação
  inadimplente pode levar até 21 meses na carteira de menor risco e até quinze meses na
  carteira majoritariamente de crédito pessoal.
- **Evidência:** *"pode demorar até 21 meses depois do inadimplemento para ser completamente
  provisionada"* e *"pode demorar até quinze meses para ser completamente provisionada"*
- **Fonte:** idem A1
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf
- **Data:** setembro/2025
- **Confiança:** alta
- **Uso no painel:** explica por que a correlação defasada continua alta em horizontes longos.

### A3 · Boa parte da alta recente da inadimplência é regra contábil, não crédito ruim

- **Afirmação:** cerca de 70% do aumento da inadimplência do SFN observado até junho de 2025
  decorre da mudança das regras de contabilização, em vigor desde 1º de janeiro de 2025.
- **Evidência:** *"Estima-se que a maior parte, cerca de 70%, do aumento da inadimplência
  observado até junho de 2025 esteja associada aos efeitos da mudança regulatória."*
- **Fonte:** idem A1 (a norma citada no boxe é a Resolução BCB 352, no arcabouço da Resolução CMN 4.966)
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf
- **Data:** setembro/2025
- **Confiança:** alta
- **Uso no painel:** **é a ressalva mais importante do painel inteiro.** A série 21084 sobe no
  fim do período em parte por mudança de régua. Ler essa alta como piora do crédito é erro.

### A4 · O tamanho do efeito contábil, quantificado

- **Afirmação:** sem a mudança de regras, a inadimplência do SFN em junho de 2025 seria
  0,53 p.p. menor, contra um aumento observado de 0,78 p.p. no ano.
- **Evidência:** *"seria 0,53 p.p. menor caso as mudanças regulatórias não tivessem ocorrido"*
  e *"aumento de 0,78 p.p. da taxa de inadimplência observado neste ano"*
- **Fonte:** idem A1
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf
- **Data:** setembro/2025
- **Confiança:** alta
- **Uso no painel:** dá ordem de grandeza à ressalva A3.

### A5 · Defasagem empírica entre choque de renda e atraso acima de 90 dias: 10 a 11 meses

- **Afirmação:** acompanhando trabalhadores formais demitidos, os valores em atraso acima de
  90 dias atingem pico entre 10 e 11 meses após a demissão.
- **Evidência:** *"Ambos os grupos apresentam um aumento dos valores inadimplidos, com picos
  entre 10 e 11 meses após a demissão."*
- **Fonte:** Banco Central do Brasil, Relatório de Economia Bancária 2023, Boxe 1 —
  *Uso do crédito em torno de episódios de desemprego*
- **URL:** https://www.bcb.gov.br/content/publicacoes/relatorioeconomiabancaria/reb2023p.pdf
- **Data:** 2024 (dados de 2023)
- **Confiança:** alta
- **Uso no painel:** é a melhor âncora externa para a defasagem medida na seção diagnóstica.
  Atenção: mede choque de **emprego**, não de juros — é um mecanismo próximo, não o mesmo.

### A6 · O repasse da Selic ao tomador PF é muito desigual entre modalidades

- **Afirmação:** para uma elevação de 1 p.p. da Selic, o repasse estimado às taxas de crédito
  PF é de 4,43 p.p. no cheque especial, 1,73 p.p. no crédito pessoal, 1,64 p.p. em aquisição
  de outros bens e 0,75 p.p. em veículos; no crédito direcionado PF cai para 0,43 p.p.
  (imobiliário) e 0,41 p.p. (rural).
- **Evidência:** *"Uma elevação de 1 p.p. da Selic se correlaciona a uma elevação de 1,64 p.p.
  nas taxas de crédito às famílias para aquisição de outros bens"*; demais valores lidos na
  tabela de repasse por modalidade do próprio estudo.
- **Fonte:** Banco Central do Brasil, Estudo Especial nº 118/2022 —
  *Repasse da taxa Selic para o mercado de crédito bancário*
- **URL:** https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/EE118_Repasse_da_taxa_Selic_para_o_mercado_de_credito_bancario.pdf
- **Data:** setembro/2022
- **Confiança:** alta
- **Uso no painel:** sustenta, na prescritiva, a recomendação de deslocar a carteira para
  linhas com garantia em vez de mexer no volume total. É o dado que transforma
  "mix importa" em número.

### A7 · O efeito quantidade sobre as concessões PF: −3,7% em 12 meses

- **Afirmação:** cada aumento médio de 1 p.p. na Selic causa queda de 3,7% no nível médio das
  concessões de crédito livre de longo prazo a pessoas físicas ao longo de 12 meses, em
  relação ao contrafactual sem o choque.
- **Evidência:** *"cada aumento médio de 1 p.p. na Selic causa uma queda de 3,7% no nível médio
  das concessões de crédito em relação ao contrafactual em que tal choque não ocorre"*
- **Fonte:** Banco Central do Brasil, Relatório de Política Monetária, boxe sobre transmissão
  da política monetária ao mercado de crédito
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf
- **Data:** março/2026
- **Confiança:** alta

### A8 · A transmissão só fica estatisticamente significativa em horizontes longos

- **Afirmação:** o efeito da Selic sobre as concessões PF de longo prazo não é significativo
  em 3 meses e passa a ser em horizontes mais longos — ordem de grandeza de 6 a 9 meses.
- **Evidência:** *"crédito livre de longo prazo possui relação inversa e estatisticamente
  significativa com a taxa de juros em horizontes mais longos"*
- **Fonte:** idem A7
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf
- **Data:** março/2026
- **Confiança:** alta
- **Uso no painel:** é a fonte externa mais próxima da defasagem de 6 meses que o painel mede
  entre Selic e inadimplência PF. Cuidado: lá é **concessão**, aqui é **inadimplência** —
  convergem em ordem de grandeza, não são a mesma medida.

### A9 · O crédito emergencial PF anda na direção contrária

- **Afirmação:** cheque especial, rotativo e cartão parcelado tendem a **subir** quando a Selic
  sobe, porque são usados em situações de estresse financeiro — o canal de juros é contrariado
  pela necessidade de liquidez das famílias.
- **Evidência:** *"parece responder positivamente às elevações da taxa Selic"*
- **Fonte:** idem A7
- **URL:** https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf
- **Data:** março/2026
- **Confiança:** alta
- **Uso no painel:** explicação alternativa legítima para parte do movimento das séries
  agregadas. Bom material para a pergunta "que outra explicação produziria o mesmo gráfico?".

---

## B · Afirmações com fonte confirmada, trecho não conferido (confiança média)

### B1 · O efeito do Desenrola sobre a inadimplência dos beneficiários foi transitório

- **Afirmação:** cerca de 18 meses após o início das renegociações, os níveis de inadimplência
  dos beneficiários do Desenrola Brasil voltaram a subir.
- **Fonte:** Banco Central do Brasil — publicação sobre o programa Desenrola
- **URL:** https://dadosabertos.bcb.gov.br/dataset/desenrola-brasil
- **Confiança:** média — não abri o documento original para conferir o trecho.
- **Uso no painel:** candidata a explicação alternativa para a inflexão da série 21084.
  **Conferir antes de citar.**

### B2 · Comprometimento de renda como indicador antecedente tem respaldo internacional

- **Afirmação:** a razão de serviço da dívida das famílias (DSR), equivalente conceitual ao
  comprometimento de renda, funciona como sinal antecedente de crises bancárias sistêmicas.
- **Fonte:** Bank for International Settlements — base e estudos sobre Debt Service Ratios
- **URL:** https://data.bis.org/topics/DSR
- **Confiança:** média — a fonte responde, mas o trecho citado não foi conferido no documento.
- **Uso no painel:** é o respaldo conceitual para tratar a série 29034 como antecedente.
  Ressalva importante: é literatura **internacional** sobre crises sistêmicas, não sobre
  carteira de cooperativa brasileira. Usar como analogia, não como prova.

---

## C · O que esta pesquisa NÃO estabeleceu

Registrar o vazio é parte do método. Não foi encontrada, nesta rodada:

1. Nenhuma estimativa publicada da defasagem **direta entre Selic e a série 29034**
   (comprometimento de renda). A leitura de que ela reage de forma quase contemporânea
   continua sendo um achado dos dados do painel, apoiado por analogia com A6 e B2 —
   não uma medida replicada da literatura.
2. Nenhuma estimativa da defasagem **direta entre Selic e a série 21084**. As âncoras
   disponíveis são indiretas: emprego → atraso (A5) e Selic → concessões (A8).
3. Nada específico sobre **cooperativas de crédito**. Toda a evidência é do SFN agregado.
4. As afirmações sobre *pass-through* que não entraram aqui caíram na verificação
   adversarial ou ficaram sem verificação por interrupção do processo.

---

## D · Todas as fontes coletadas

As 35 URLs abaixo foram testadas em 18/09/2026: **todas responderam HTTP 200**. Estão aqui
inclusive as que não geraram afirmação, para quem quiser aprofundar.

**Banco Central — relatórios e boxes**
- https://www.bcb.gov.br/content/ri/relatorioinflacao/202509/rpm202509b6p.pdf
- https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603b4p.pdf
- https://www.bcb.gov.br/content/ri/relatorioinflacao/202603/rpm202603p.pdf
- https://www.bcb.gov.br/content/ri/relatorioinflacao/202003/ri202003b9p.pdf
- https://www.bcb.gov.br/content/publicacoes/relatorioeconomiabancaria/reb2023p.pdf
- https://www.bcb.gov.br/content/publications/bankingreport/2023/BAR_2023.pdf
- https://www.bcb.gov.br/publicacoes/relatorioeconomiabancaria
- https://www.bcb.gov.br/content/publicacoes/ref/202510/RELESTAB202510-refPub.pdf
- https://www.bcb.gov.br/content/publicacoes/ref/202310/RELESTAB202310-refPub.pdf
- https://www.bcb.gov.br/content/publicacoes/boletimregional/202512/br202512c3p.pdf

**Banco Central — estudos especiais**
- https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/EE118_Repasse_da_taxa_Selic_para_o_mercado_de_credito_bancario.pdf
- https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/EE080_Indicadores_de_endividamento_de_risco_e_perfil_do_tomador_de_credito.pdf
- https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/EE077_Potencia_da_politica_monetaria.pdf
- https://www.bcb.gov.br/conteudo/relatorioinflacao/EstudosEspeciais/Efeito_mudancas_taxa_Selic_taxas_juros_operacoes_credito.pdf

**Banco Central — Working Paper Series**
- https://bcb.gov.br/content/publicacoes/WorkingPaperSeries/WP616v2.pdf
- https://bcb.gov.br/content/publicacoes/WorkingPaperSeries/WP649.pdf
- https://www.bcb.gov.br/content/publicacoes/WorkingPaperSeries/WP636.pdf
- https://www.bcb.gov.br/content/publicacoes/WorkingPaperSeries/WP642.pdf
- https://www.bcb.gov.br/pec/wps/ingl/wps505.pdf
- https://www.bcb.gov.br/pec/wps/port/TD304.pdf

**Banco Central — cidadania financeira, normas e estatísticas**
- https://www.bcb.gov.br/content/cidadaniafinanceira/documentos_cidadania/serie_cidadania/serie_cidadania_financeira_8_endividamento_risco_2ed.pdf
- https://www.bcb.gov.br/content/cidadaniafinanceira/documentos_cidadania/serie_cidadania/serie_cidadania_financeira_6_endividamento_risco.pdf
- https://www.bcb.gov.br/content/estatisticas/hist_estatisticasmonetariascredito/202112_Texto_de_estatisticas_monetarias_e_de_credito.pdf
- https://www.bcb.gov.br/pre/normativos/res/1999/pdf/res_2682_v2_l.pdf
- https://www3.bcb.gov.br/aplica/cosif/manual/09021771869a1c3e.htm

**Dados abertos (as próprias séries do painel)**
- https://dadosabertos.bcb.gov.br/dataset/21084-inadimplencia-da-carteira-de-credito---pessoas-fisicas---total
- https://dadosabertos.bcb.gov.br/dataset/29034-comprometimento-de-renda-das-familias-com-o-servico-da-divida-com-o-sistema-financeiro-nacion
- https://dadosabertos.bcb.gov.br/dataset/20716-taxa-media-de-juros-das-operacoes-de-credito---pessoas-fisicas---total
- https://dadosabertos.bcb.gov.br/dataset/desenrola-brasil

**Internacional e acadêmico**
- https://data.bis.org/topics/DSR
- https://www.bis.org/publications/how-much-income-used-debt-payments-new-database-debt-service-ratios.pdf
- https://www.bis.org/publ/qtrpdf/r_qt1209e.pdf
- https://www.bis.org/publ/work421.pdf
- https://www.scielo.br/j/neco/a/mKXnDJdq3b3wYMTQgGm7gZc/?lang=pt
- https://www.scielo.br/j/rec/a/hPB6FT3Ncp5Lf3nWjPRqvLJ/?lang=pt

---

## E · As três frases que o painel pode afirmar com esta pesquisa

Para uso direto na seção diagnóstica, já com a fonte colada:

1. *"A inadimplência é um indicador de resultado por definição regulatória: uma operação só
   é considerada inadimplente após três meses de atraso (BCB, RPM set/2025)."*
2. *"Parte relevante da alta recente da inadimplência não é piora do crédito: cerca de 70% do
   aumento até junho de 2025 vem de mudança nas regras de contabilização (BCB, RPM set/2025)."*
3. *"A defasagem de cerca de 6 meses medida neste painel é compatível com o que o Banco Central
   observa em episódios de desemprego, em que o atraso acima de 90 dias tem pico entre 10 e
   11 meses (BCB, REB 2023, Boxe 1)."*

E a que o painel **não** pode afirmar: que a Selic causou a variação da inadimplência.
Nenhuma fonte desta lista sustenta identificação causal com dados agregados.
