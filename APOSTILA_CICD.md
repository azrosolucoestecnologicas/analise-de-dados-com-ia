# Deploy de aplicações de IA — o que você precisa saber

Apostila do aluno · Instituto NTA

Este material cobre o vocabulário mínimo para acompanhar a aula: Git, GitHub,
linha de comando, CI/CD, Actions, YAML e Pages. Não é um curso de Git — é o
suficiente para entender o que está acontecendo na tela e repetir depois.

---

## 1. O que você precisa hoje

**Um navegador e uma conta no GitHub.** Só isso.

Essa é a parte que surpreende quase todo mundo, e é o coração da aula: o código
do projeto **não roda no seu computador**. Ele roda numa máquina do GitHub, que
nasce quando o processo começa e é destruída quando termina.

Você consegue fazer a aula inteira sem instalar nada:

| Tarefa | Precisa de terminal? |
|---|---|
| Criar o repositório | Não — botão no site |
| Subir os arquivos | Não — "Add file → Upload files" |
| Editar o YAML | Não — lápis de editar no próprio site |
| Rodar o processo | Não — botão "Run workflow" |
| Ver o resultado publicado | Não — é uma URL |

O terminal e a instalação local entram quando você quiser **desenvolver** —
rodar e depurar o código na sua máquina antes de subir. Isso está no apêndice,
no fim desta apostila, e é opcional para hoje.

> **Por que isso importa.** Muita gente desiste de automação achando que precisa
> dominar terminal antes. Precisa dominar o conceito. A ferramenta vem depois.

---

## 2. Git e GitHub: quatro termos

**Git e GitHub são coisas diferentes.** Git é um programa que guarda o
histórico de uma pasta. GitHub é um site que hospeda essas pastas e acrescenta
coisas em volta — entre elas, a capacidade de executar código.

Analogia: Git é o Word (controla as versões do documento). GitHub é o Google
Drive (guarda, compartilha e ainda faz outras coisas com o arquivo).

Os quatro termos que aparecem na aula:

| Termo | O que é |
|---|---|
| **Repositório** | Uma pasta com histórico. "Repo", para os íntimos. |
| **Commit** | Uma fotografia do estado da pasta, com uma mensagem explicando o que mudou. O histórico é uma fila de commits. |
| **Push** | Enviar seus commits para o GitHub. É o verbo que dispara automação. |
| **Branch** | Uma linha paralela de trabalho. Hoje usamos só a principal, a `main`. |

Nada além disso é necessário para acompanhar. Merge, rebase, conflito, pull
request — tudo isso é importante em equipe, e é assunto de outra aula.

### Público ou privado

Repositório **público**: qualquer um vê o código. Automação e publicação saem
de graça.

Repositório **privado**: só quem você autorizar vê. A automação tem cota
mensal gratuita e passa a ser cobrada depois.

Para aprender, use público — e nunca coloque senha, chave ou dado pessoal
dentro dele. Como guardar segredo com segurança está na seção 5.

---

## 3. Por que existe linha de comando

O terminal é uma forma de conversar com o computador escrevendo, em vez de
clicando. Parece antiquado, mas tem três vantagens que a interface gráfica não
tem:

1. **É repetível.** Um comando escrito pode ser guardado, versionado e
   executado de novo, igual, mil vezes.
2. **É automatizável.** Um robô não sabe clicar num botão, mas sabe executar
   um comando.
3. **É o que existe no servidor.** A máquina que roda seu código na nuvem não
   tem tela. Só aceita comandos.

É por isso que o arquivo de automação da aula é uma lista de comandos. Quando
você lê `python coletor.py` dentro do YAML, está lendo exatamente o que você
digitaria no seu terminal — só que quem digita é o GitHub.

**A linha de comando não é um pré-requisito da aula. É o assunto dela**, visto
de outro ângulo: automatizar é escrever o que você faria à mão.

---

## 4. CI/CD: o que significa

A sigla junta duas ideias que costumam andar juntas.

**CI — Integração Contínua.** Toda vez que o código muda, alguma verificação
automática roda: os testes passam? o projeto ainda constrói? Serve para
descobrir que algo quebrou em minutos, não em semanas.

**CD — Entrega ou Implantação Contínua.** Se as verificações passaram, o
resultado vai para o ar sozinho, sem ninguém subir arquivo à mão.

A diferença entre as duas versões do "CD" é quem aperta o botão:

| | Quem publica |
|---|---|
| **Entrega** contínua (*delivery*) | Fica tudo pronto, uma pessoa aprova |
| **Implantação** contínua (*deployment*) | Publica sozinho, sem aprovação |

Essa distinção volta no fim da aula, quando houver um modelo de IA no meio do
processo — porque aí a pergunta "publica sozinho?" fica bem mais delicada.

### O que CI/CD resolve de verdade

Sem automação, publicar é um ritual manual: alguém lembra de rodar o script,
alguém lembra de conferir, alguém lembra de copiar os arquivos para o servidor.
Todo passo que depende de alguém lembrar, uma hora falha.

No nosso projeto tem um motivo a mais: **os dados mudam sozinhos.** O Copom
muda a Selic, o Banco Central publica pontos novos. Se ninguém rodar nada, o
painel envelhece sem avisar.

---

## 5. GitHub Actions: a máquina descartável

Aqui está o conceito que mais confunde, e o que mais vale entender.

Quando o processo dispara, o GitHub **liga um computador novo**. Uma máquina
virtual Linux, limpa, que não existia dez segundos antes. Ela:

1. baixa uma cópia do seu repositório
2. executa, em ordem, os comandos que você escreveu no YAML
3. entrega o resultado
4. **é destruída**

Nada sobrevive entre uma execução e outra. Se o processo instalou o Python, a
próxima execução instala de novo. Se ele criou um arquivo, o arquivo some —
a menos que você mande guardar em algum lugar.

> **O erro de raciocínio mais comum:** achar que o Actions roda no seu
> computador, ou que o GitHub "entende" seu Python. Não e não. Ele liga um
> Linux vazio e digita seus comandos. Se o comando funciona no terminal, ele
> funciona ali; se não funciona, ali também não vai funcionar.

### Vocabulário do Actions

| Termo | O que é |
|---|---|
| **Workflow** | O processo inteiro, descrito num arquivo `.yml` |
| **Trigger** (gatilho) | O que faz o processo começar |
| **Job** | Um bloco de trabalho, que roda numa máquina |
| **Step** (passo) | Um comando ou uma ação dentro do job |
| **Runner** | A máquina descartável que executa tudo |
| **Action** | Um pedaço de automação pronto, feito por outra pessoa |

Os gatilhos que usamos hoje:

- `push` — alguém enviou código novo
- `schedule` — horário marcado (formato *cron*)
- `workflow_dispatch` — o botão "Run workflow", apertado por uma pessoa

### Segredos

Chave de API nunca vai dentro do repositório. Vai em
**Settings → Secrets and variables → Actions**, e o workflow a recebe como
variável de ambiente:

```yaml
env:
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

O GitHub guarda o valor cifrado, injeta na hora da execução e **censura o
conteúdo nos logs** — se a chave for impressa por acidente, aparece `***`.

Chave commitada por engano é considerada vazada mesmo depois de apagada: ela
continua no histórico, e robôs varrem repositórios públicos atrás disso o
tempo todo. Se acontecer, o certo é revogar a chave, não tentar esconder.

---

## 6. YAML em cinco regras

YAML é um formato de arquivo de configuração. Não é uma linguagem de
programação — é uma lista de coisas com nome.

**1. `chave: valor`**

```yaml
name: Publicar painel
```

**2. A indentação define o que está dentro de quê.** Só espaços, nunca Tab.
O Tab é erro de sintaxe em YAML, e é o tropeço número um de quem começa.

```yaml
jobs:
  publicar:
    runs-on: ubuntu-latest
```

Aqui `publicar` está dentro de `jobs`, e `runs-on` está dentro de `publicar`.

**3. O hífen cria item de lista.**

```yaml
steps:
  - uses: actions/checkout@v4
  - run: python coletor.py
```

Dois passos, na ordem em que aparecem.

**4. O `|` guarda várias linhas.**

```yaml
run: |
  python build.py
  md5sum public/index.html
```

**5. `#` é comentário.** O YAML do projeto é cheio deles, de propósito.

> **Como conferir antes de subir:** a barra lateral do editor do GitHub acusa
> erro de sintaxe na hora. Aproveite — YAML quebrado só reclama quando o
> processo tenta rodar.

---

## 7. GitHub Pages: o que é e o que não é

O Pages é **hospedagem gratuita de site estático**, ligada ao repositório.

**Estático** quer dizer: o servidor entrega arquivos prontos — HTML, CSS,
JavaScript, imagens — exatamente como estão. Ele não executa nada do lado dele.

| O Pages faz | O Pages **não** faz |
|---|---|
| Entrega HTML, CSS, JS, imagens | Rodar Python, PHP ou qualquer código no servidor |
| Serve por HTTPS, com certificado | Ter banco de dados |
| Aceitar domínio próprio | Guardar segredo de API |
| Publicar direto do Actions | Processar formulário ou login |

O JavaScript do seu site roda, sim — mas **no navegador do visitante**, não no
servidor. É por isso que nosso gráfico funciona: ele é desenhado no navegador,
a partir de números que já estão dentro do HTML.

### Como o endereço é formado

```
https://<seu-usuario>.github.io/<nome-do-repositorio>/
```

### Como o Pages e o Actions se dividem

Esta é a frase para levar para casa:

> **O Actions executa. O Pages entrega.**

O Actions liga a máquina, baixa os dados, roda o Python e **produz** o HTML.
O Pages pega esse HTML pronto e **serve** para quem acessa a URL. Um é
computação, o outro é prateleira.

É por isso que o projeto precisa dos dois. O Python nunca roda no Pages — ele
roda no Actions, e o que chega no Pages já é resultado.

### Limites

Repositório público: publicação gratuita. Há limites brandos de tamanho do
site e de tráfego mensal, folgados para qualquer projeto de aula.

> Os números exatos mudam. Confira em *docs.github.com → Pages → limites* antes
> de usar em algo sério.

---

## 8. O mapa do projeto da aula

```
  você edita o código
          │
          │  push  (ou botão, ou horário marcado)
          ▼
  ┌──────────────────────────┐
  │  GitHub Actions          │   máquina Linux nova, descartável
  │                          │
  │  1. baixa o repositório  │
  │  2. instala o Python     │
  │  3. coletor.py  ────────────►  API do Banco Central
  │  4. comentario.py ──────────►  API do modelo   (chave via secret)
  │  5. testes.py            │   ← portão: se falhar, para aqui
  │  6. build.py             │   → produz public/index.html
  └───────────┬──────────────┘
              │  envia o resultado
              ▼
  ┌──────────────────────────┐
  │  GitHub Pages            │   só entrega o arquivo pronto
  └───────────┬──────────────┘
              ▼
   https://usuario.github.io/repositorio/
```

Repare na ordem dos passos 5 e 6: o teste vem **antes** do build. Se a saída do
modelo não passar na verificação, nada é construído e nada é publicado. O portão
fica antes da porta, não depois.

---

## 9. Erros comuns na primeira vez

| Sintoma | Causa | Conserto |
|---|---|---|
| `Get Pages site failed... Not Found` | O Pages nunca foi ligado no repositório | Settings → Pages → Source: **GitHub Actions** |
| `Error: Process completed with exit code 1` | Um comando falhou | Abra o passo vermelho no log e leia a última linha antes do erro |
| O workflow não aparece na aba Actions | O arquivo está no lugar errado | Tem que ser exatamente `.github/workflows/*.yml` |
| `did not find expected key` | Indentação com Tab, ou desalinhada | Só espaços. Confira o alinhamento da linha citada |
| A chave "some" no log, vira `***` | Nada quebrado — é proteção | É o comportamento esperado |
| Publicou, mas a página está velha | Cache do navegador, ou o deploy ainda rodando | Recarregue sem cache; confira se o job terminou |
| `403` ao publicar | Faltou permissão no workflow | O bloco `permissions:` precisa de `pages: write` e `id-token: write` |

**Aviso que não é erro:** mensagens sobre versão do Node ou migração do Ubuntu
aparecem em amarelo, não em vermelho. São avisos de manutenção futura. O que
importa é a marca do job: verde passou, vermelho falhou.

---

## 10. Apêndice: instalar na sua máquina

**Opcional.** Nada disso é necessário para a aula — serve para quando você
quiser desenvolver localmente antes de subir.

### Windows

O caminho mais curto é instalar o **Git for Windows**
(`git-scm.com/download/win`), que já traz o Git Bash — um terminal decente,
porque o Prompt de Comando do Windows não entende os mesmos comandos dos
exemplos.

O **Python** vem de `python.org/downloads`. No instalador, marque
**"Add Python to PATH"** na primeira tela. Se esquecer, o terminal responde
"python não é reconhecido" e a correção é reinstalar marcando a caixa.

### macOS

Abra o Terminal e digite `git --version`. Se o Git não estiver instalado, o
próprio macOS oferece instalar as ferramentas de desenvolvedor.

O Python do sistema é antigo. Instale um atual por `python.org/downloads` ou,
se você usa Homebrew, `brew install python git`.

### Linux

```bash
sudo apt update && sudo apt install git python3 python3-pip   # Debian, Ubuntu
sudo dnf install git python3 python3-pip                      # Fedora
```

### Conferindo

```bash
git --version
python3 --version    # no Windows, use: python --version
```

Se os dois responderem com um número de versão, está pronto.

### Rodando o projeto localmente

```bash
git clone https://github.com/<usuario>/<repositorio>.git
cd <repositorio>
pip install requests anthropic
python coletor.py
python build.py
```

Abra `public/index.html` com dois cliques. Para a parte de IA, você precisa da
sua própria chave numa variável de ambiente — e ela nunca entra num arquivo do
repositório.

---

## 11. Glossário

**Action** — automação pronta de terceiros, reaproveitada no seu workflow.
**Artefato** — arquivo produzido por uma execução e guardado para depois.
**Branch** — linha paralela de desenvolvimento.
**CD** — entrega ou implantação contínua.
**CI** — integração contínua.
**Commit** — fotografia do estado do repositório, com mensagem.
**Cron** — formato para marcar horário de execução recorrente.
**Deploy** — colocar no ar.
**Determinístico** — mesma entrada, sempre a mesma saída.
**Job** — bloco de trabalho dentro de um workflow.
**Pipeline** — a sequência automatizada inteira.
**Push** — enviar commits para o GitHub.
**Repositório** — pasta com histórico.
**Runner** — máquina descartável que executa o workflow.
**Secret** — valor sensível guardado cifrado pelo GitHub.
**Site estático** — site de arquivos prontos, sem código no servidor.
**Workflow** — o processo automatizado, descrito em YAML.
**YAML** — formato de arquivo de configuração, sensível a indentação.
