# Deploy de aplicações de IA — CI/CD na prática

Projeto mínimo para a aula de 90 minutos. Um painel da meta da taxa Selic que
se reconstrói e se republica sozinho.

O projeto inteiro cabe em quatro arquivos Python de ~60 linhas cada. Ele é pequeno
de propósito: o assunto da aula é o pipeline, não o domínio.

## Por que este projeto e não um "hello world"

CI/CD só faz sentido quando existe algo que **precisa mesmo rodar de novo**.
Aqui os dados mudam sozinhos: o Copom altera a Selic, a série do Banco Central
ganha pontos novos todo dia útil. O cron não é enfeite — se ninguém rodar nada,
o painel envelhece.

## Os dois atos

O arco da aula é o contraste entre duas colunas:

| | IA no **build** (ato 1) | IA no **runtime** (ato 2) |
|---|---|---|
| Chave de API | não existe | secret obrigatório |
| Custo | zero por execução | por chamada |
| Mesma entrada | mesma saída | saída diferente |
| Modelo fora do ar | impossível | precisa de fallback |
| O que versionar | o código | código + prompt + saída |
| Teste no CI | `diff` resolve | `diff` não serve para nada |

### Ato 1 — pipeline determinístico

```bash
python3 coletor.py && python3 build.py
```

A demonstração que abre a aula:

```bash
python3 build.py >/dev/null && md5sum public/index.html && python3 build.py >/dev/null && md5sum public/index.html
```

O hash é idêntico. `build.py` não chama `datetime.now()` de propósito — a saída
depende **só** do conteúdo de `dados/`. É isso que torna o CI clássico possível.

Workflow: `.github/workflows/publicar.yml`

### Ato 2 — um modelo dentro do pipeline

```bash
export ANTHROPIC_API_KEY=...
python3 comentario.py && python3 testes.py && python3 build.py
```

Rode `comentario.py` duas vezes e compare o hash. **Agora ele muda.** E com isso
quebram, ao mesmo tempo, quatro coisas que estavam resolvidas no ato 1:

1. **Onde guarda a chave** — secret do GitHub, nunca no repositório
2. **Quanto custou** — `comentario.py` imprime o custo de cada execução
3. **O que publicar se o modelo falhar** — hoje o build quebra; discuta as alternativas
4. **Como testar uma saída que nunca se repete** — é o próximo bloco

Workflow: `.github/workflows/publicar-com-ia.yml` — compare os dois arquivos,
são quatro passos de diferença.

## Testes de propriedade: o coração da aula

Não dá para testar saída de modelo com `diff`. O que dá para testar são
**propriedades** que a saída precisa ter sempre. `testes.py` verifica seis:

1. Todo número citado existe nos dados (pega número inventado)
2. Nenhum verbo causal — "causou", "provocou", "levou a"
3. Variação de taxa em pontos percentuais, não em porcentagem
4. Cita o mês de referência
5. Tamanho plausível
6. Sem markdown nem preâmbulo

Se qualquer uma falhar, o processo sai com código 1, o workflow quebra e
**nada é publicado**. O portão fica antes do deploy, não depois.

### Demonstração ao vivo

Edite `dados/comentario.json` à mão, troque um número por um inventado e rode
`python3 testes.py`. O teste acusa e mostra quais valores seriam aceitos.

## Custos

Cada execução de `comentario.py` imprime o custo real. Com ~300 tokens de entrada
e ~120 de saída no `claude-opus-4-8` (US$ 5 por milhão na entrada, US$ 25 na saída),
dá cerca de **US$ 0,005 por execução** — meio centavo de dólar.

O que muda é a frequência do cron:

| Cadência | Execuções/mês | Custo do modelo |
|---|---|---|
| Diária | 30 | ~US$ 0,15 |
| De hora em hora | 720 | ~US$ 3,60 |
| A cada 5 minutos | 8.640 | ~US$ 43 |

E essa é a pergunta que **não existia** no ato 1, onde a resposta era zero.
A frequência do cron virou uma decisão de engenharia com preço.

Hospedagem, para comparar:

| Serviço | Custo |
|---|---|
| GitHub Pages | grátis |
| GitHub Actions, repositório público | grátis, minutos ilimitados |
| GitHub Actions, repositório privado | cota mensal gratuita, depois por minuto |
| Render, site estático | plano gratuito |

> Confirme os limites de cota e os preços vigentes antes da aula — mudam com
> frequência e não vale citar número velho na frente da turma.

## Antes da aula

1. `git init`, criar o repositório **público** no GitHub e dar push
   (público = Actions e Pages sem cota)
2. Settings → Pages → Source: **GitHub Actions**
3. Settings → Secrets and variables → Actions → novo secret `ANTHROPIC_API_KEY`
4. Rodar o workflow **uma vez** e deixá-lo verde

Ao vivo você dispara de novo pelo botão "Run workflow", não cria do zero.
Deploy ao vivo tem muita superfície de falha: conta, autenticação, DNS,
propagação. Tenha screenshots de cada tela.

## Estrutura

```
coletor.py      baixa a série 432 do SGS/BCB → dados/selic.json
build.py        gera public/index.html (determinístico)
comentario.py   ato 2: chama o modelo → dados/comentario.json
testes.py       testes de propriedade sobre a saída do modelo
.github/workflows/
  publicar.yml          ato 1: coletar → build → Pages
  publicar-com-ia.yml   ato 2: + comentário + testes antes do deploy
```

`dados/` e `public/` estão no `.gitignore`: são artefatos de build, o pipeline
regenera a cada execução. Commitar artefato gera conflito a cada run.

## Uma armadilha da API do BCB, de brinde

O SGS responde **HTTP 200 com uma página HTML** quando recusa a requisição, de
forma intermitente. Código que confia em `raise_for_status()` não detecta.
`coletor.py` valida que o corpo começa com `[` antes de aceitar — vale mostrar,
porque é um erro de retry que quase todo mundo escreve errado.
