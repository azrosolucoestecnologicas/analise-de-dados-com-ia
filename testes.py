"""Testes de propriedade sobre a leitura gerada pelo modelo.

A saída de um modelo não se repete, então diff não serve como teste.
O que dá para verificar são propriedades que a saída precisa ter sempre.

Sai com código 1 se qualquer uma falhar — o CI quebra e nada é publicado.
"""

import json
import re
import sys
from pathlib import Path

ARQUIVO = Path(__file__).parent / "dados" / "comentario.json"

VERBOS_CAUSAIS = ["causou", "causa ", "causam", "provocou", "provoca ", "levou a",
                  "resultou em", "fez com que", "por causa d", "devido a",
                  "em razão d", "graças a"]

VERBOS_PRESCRITIVOS = ["recomend", "deve ", "deveria", "sugere-se", "aconselh"]


def numeros_permitidos(fatos: dict) -> set[str]:
    """Todo número citado tem que sair daqui — senão o modelo inventou."""
    permitidos = {"12"}  # a janela de comparação ("em 12 meses")
    for f in fatos.values():
        for valor in (f["atual"], f["ha_12_meses"], f["variacao_12m"]):
            if valor is None:
                continue
            for v in (valor, abs(valor)):
                permitidos.add(f"{v:.2f}".replace(".", ","))
                permitidos.add(f"{v:.1f}".replace(".", ","))
                permitidos.add(f"{v:g}".replace(".", ","))
    return permitidos


def main() -> None:
    if not ARQUIVO.exists():
        sys.exit(f"{ARQUIVO} não existe. Rode comentario.py antes.")

    dado = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    texto, fatos = dado["texto"], dado["fatos"]
    baixo = texto.lower()
    falhas = []

    # 1. Todo número citado existe nos dados.
    # Datas saem antes: o ano não é um valor de série.
    permitidos = numeros_permitidos(fatos)
    sem_datas = re.sub(r"\b\w{3,10}[/-]\d{4}\b|\b\d{1,2}[/-]\d{4}\b|\b(?:19|20)\d{2}\b",
                       " ", texto)
    inventados = [n for n in re.findall(r"\d+(?:,\d+)?", sem_datas) if n not in permitidos]
    if inventados:
        falhas.append(f"números que não existem nos dados: {sorted(set(inventados))}")

    # 2. Nenhuma afirmação de causa — o painel mede associação, não causalidade.
    causais = [v for v in VERBOS_CAUSAIS if v in baixo]
    if causais:
        falhas.append(f"linguagem causal: {causais}")

    # 3. Nenhuma recomendação — a seção prescritiva do painel é que faz isso.
    prescritivos = [v for v in VERBOS_PRESCRITIVOS if v in baixo]
    if prescritivos:
        falhas.append(f"linguagem prescritiva: {prescritivos}")

    # 4. Variação de taxa em pontos percentuais, não em porcentagem.
    if re.search(r"(caiu|subiu|aumentou|recuou|variou|avançou)[^.]{0,40}%", baixo):
        if "p.p." not in baixo and "pontos percentuais" not in baixo:
            falhas.append("variação expressa em % sem usar pontos percentuais")

    # 5. Cita pelo menos um mês de referência (as séries têm defasagens diferentes).
    meses_citados = [f["mes"] for f in fatos.values() if f["mes"].split("/")[0] in baixo]
    if not meses_citados:
        falhas.append("não menciona nenhum mês de referência")

    # 6. Tamanho plausível para 3 a 4 frases.
    if not 150 <= len(texto) <= 1200:
        falhas.append(f"tamanho fora do esperado: {len(texto)} caracteres")

    # 7. Sem markdown nem preâmbulo.
    if re.match(r"^\s*(#|\*|-|\d\.|aqui est|segue|com base)", baixo):
        falhas.append("começa com markdown ou preâmbulo")

    print(f"leitura avaliada:\n  {texto}\n")
    if falhas:
        print(f"FALHOU em {len(falhas)} propriedade(s):")
        for f in falhas:
            print(f"  ✗ {f}")
        sys.exit(1)

    print(f"todas as 7 propriedades passaram ✓  (meses citados: {', '.join(meses_citados)})")


if __name__ == "__main__":
    main()
