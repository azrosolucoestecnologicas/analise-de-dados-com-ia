"""Gera public/index.html a partir de dados/selic.json.

Determinístico de propósito: a saída depende SÓ do conteúdo de dados/.
Nada de datetime.now() aqui — rodar duas vezes com o mesmo dado tem que
produzir exatamente os mesmos bytes. É isso que o md5 da aula demonstra.
"""

import json
from pathlib import Path

RAIZ = Path(__file__).parent
ENTRADA = RAIZ / "dados" / "selic.json"
COMENTARIO = RAIZ / "dados" / "comentario.json"
SAIDA = RAIZ / "public" / "index.html"

MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]


def mensalizar(dados: list[dict]) -> dict[str, float]:
    """Último valor de cada mês. A Selic é diária; o painel é mensal."""
    mensal: dict[str, float] = {}
    for ponto in dados:
        dia, mes, ano = ponto["data"].split("/")
        mensal[f"{ano}-{mes}"] = float(ponto["valor"])
    return dict(sorted(mensal.items()))


def rotulo(chave: str) -> str:
    ano, mes = chave.split("-")
    return f"{MESES[int(mes) - 1]}/{ano}"


def main() -> None:
    if not ENTRADA.exists():
        raise SystemExit(f"{ENTRADA} não existe. Rode coletor.py antes.")

    serie = mensalizar(json.loads(ENTRADA.read_text(encoding="utf-8")))
    meses = list(serie)
    atual = serie[meses[-1]]
    ha_um_ano = serie.get(f"{int(meses[-1][:4]) - 1}-{meses[-1][5:]}")
    variacao = f"{atual - ha_um_ano:+.2f}".replace(".", ",") if ha_um_ano else "—"

    # Camada de IA (etapa 2 da aula). Se não existir, o painel sai sem ela.
    if COMENTARIO.exists():
        c = json.loads(COMENTARIO.read_text(encoding="utf-8"))
        bloco = (f'<section class="ia"><h2>Leitura do modelo</h2><p>{c["texto"]}</p>'
                 f'<p class="credito">Gerado por {c["modelo"]} · '
                 f'{c["tokens_entrada"]} tokens de entrada, {c["tokens_saida"]} de saída</p></section>')
    else:
        bloco = ('<section class="ia vazio"><h2>Leitura do modelo</h2>'
                 '<p>Ainda não gerada — este painel é 100% determinístico.</p></section>')

    SAIDA.parent.mkdir(exist_ok=True)

    # O GitHub Pages passa o site pelo Jekyll por padrão, e o Jekyll ignora
    # arquivos e pastas que começam com _ — sem erro nenhum, eles só somem.
    # Este arquivo vazio desliga isso.
    (SAIDA.parent / ".nojekyll").touch()

    SAIDA.write_text(f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meta Selic</title>
<style>
  :root {{ --tinta:#14213d; --suave:#5c6b80; --linha:#e1e6ec; --destaque:#c1121f; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#f7f8fa; color:var(--tinta);
    font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif; }}
  main {{ max-width:760px; margin:0 auto; padding:48px 24px 64px; }}
  h1 {{ font-size:15px; text-transform:uppercase; letter-spacing:.12em;
    color:var(--suave); font-weight:600; margin:0 0 24px; }}
  .numero {{ font-size:76px; font-weight:700; line-height:1; letter-spacing:-.03em; margin:0; }}
  .numero span {{ font-size:24px; font-weight:400; color:var(--suave); margin-left:8px; }}
  .ref {{ color:var(--suave); margin:8px 0 4px; }}
  .var {{ font-weight:600; color:var(--destaque); margin:0 0 32px; }}
  canvas {{ width:100%; height:260px; display:block; }}
  .fonte {{ font-size:13px; color:var(--suave); margin-top:12px; }}
  section.ia {{ margin-top:40px; padding:20px 24px; background:#fff;
    border:1px solid var(--linha); border-radius:10px; }}
  section.ia h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.08em;
    color:var(--suave); margin:0 0 10px; }}
  section.ia p {{ margin:0; }}
  section.vazio p {{ color:var(--suave); font-style:italic; }}
  .credito {{ font-size:12px; color:var(--suave); margin-top:12px !important; }}
</style>
</head>
<body>
<main>
  <h1>Meta da taxa Selic · Banco Central do Brasil</h1>
  <p class="numero">{f"{atual:.2f}".replace(".", ",")}<span>% a.a.</span></p>
  <p class="ref">referência: {rotulo(meses[-1])}</p>
  <p class="var">{variacao} p.p. em 12 meses</p>

  <canvas id="g" width="720" height="260"></canvas>
  <p class="fonte">Fonte: BCB/SGS, série 432 · {rotulo(meses[0])} a {rotulo(meses[-1])} ·
  {len(meses)} meses · último valor de cada mês</p>

  {bloco}
</main>
<script>
const V = {json.dumps(list(serie.values()))};
const c = document.getElementById("g"), x = c.getContext("2d");
const w = c.width, h = c.height, p = 28;
const min = Math.min(...V), max = Math.max(...V);
const px = i => p + i * (w - 2 * p) / (V.length - 1);
const py = v => h - p - (v - min) * (h - 2 * p) / (max - min || 1);
x.strokeStyle = "#e1e6ec"; x.beginPath();
x.moveTo(p, h - p); x.lineTo(w - p, h - p); x.stroke();
x.beginPath(); x.moveTo(px(0), py(V[0]));
V.forEach((v, i) => x.lineTo(px(i), py(v)));
x.strokeStyle = "#14213d"; x.lineWidth = 2; x.stroke();
x.lineTo(px(V.length - 1), h - p); x.lineTo(p, h - p); x.closePath();
x.fillStyle = "rgba(20,33,61,.07)"; x.fill();
x.beginPath(); x.arc(px(V.length - 1), py(V[V.length - 1]), 4, 0, 7);
x.fillStyle = "#c1121f"; x.fill();
</script>
</body>
</html>
""", encoding="utf-8")

    print(f"{SAIDA} · {len(meses)} meses · Selic {atual:.2f}% em {rotulo(meses[-1])}")


if __name__ == "__main__":
    main()
