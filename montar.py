"""Monta public/index.html a partir do painel.html e da leitura do modelo.

Não altera nenhuma seção do painel. Só insere um bloco de interpretação
logo antes da seção 1, usando as mesmas variáveis de cor do painel, e
copia o resultado para public/ — que é o que o GitHub Pages publica.
"""

import json
from pathlib import Path

RAIZ = Path(__file__).parent
PAINEL = RAIZ / "painel.html"
COMENTARIO = RAIZ / "dados" / "comentario.json"
SAIDA = RAIZ / "public" / "index.html"

ANCORA = '<section id="descritiva"'


def bloco(dado: dict) -> str:
    custo = dado["tokens_entrada"] / 1e6 * 5 + dado["tokens_saida"] / 1e6 * 25
    return f"""<section class="leitura-ia">
<header class="secao-cabecalho">
  <span class="secao-numero">Interpretação</span>
  <h2>Leitura do dia</h2>
  <p class="secao-resumo">Escrita por um modelo a cada execução do pipeline, a partir
  dos números das séries. É a terceira camada do painel: não é dado, não é pesquisa
  publicada — é leitura, e muda a cada dia.</p>
</header>
<p class="texto-ia">{dado["texto"]}</p>
<p class="credito-ia">Gerado por {dado["modelo"]} ·
{dado["tokens_entrada"]} tokens de entrada, {dado["tokens_saida"]} de saída ·
custo desta execução: US$ {custo:.4f} ·
verificado por testes automáticos antes da publicação</p>
</section>

"""


ESTILO = """<style>
.leitura-ia { border-left: 4px solid var(--interp, #3f3f46); background: var(--papel, #fff);
  border-radius: 0 10px 10px 0; padding: 22px 26px; margin: 28px 0; }
.leitura-ia .texto-ia { font-size: 17px; line-height: 1.65; margin: 0; }
.leitura-ia .credito-ia { font-size: 12px; color: var(--tinta-fraca, #5b6b7b);
  margin: 14px 0 0; }
</style>
"""


def main() -> None:
    if not PAINEL.exists():
        raise SystemExit(f"{PAINEL} não existe. Rode analise.py antes.")

    html = PAINEL.read_text(encoding="utf-8")

    if COMENTARIO.exists():
        dado = json.loads(COMENTARIO.read_text(encoding="utf-8"))
        if ANCORA not in html:
            raise SystemExit(f"âncora {ANCORA!r} não encontrada no painel.html — "
                             "o gerador mudou de estrutura.")
        html = html.replace("</head>", ESTILO + "</head>", 1)
        html = html.replace(ANCORA, bloco(dado) + ANCORA, 1)
        aviso = "com a leitura do modelo"
    else:
        aviso = "SEM a leitura do modelo (dados/comentario.json não existe)"

    SAIDA.parent.mkdir(exist_ok=True)
    # O Pages passa o site pelo Jekyll, que ignora nomes começando com _.
    (SAIDA.parent / ".nojekyll").touch()
    SAIDA.write_text(html, encoding="utf-8")

    print(f"{SAIDA} · {len(html) / 1024:.0f} KB · {aviso}")


if __name__ == "__main__":
    main()
