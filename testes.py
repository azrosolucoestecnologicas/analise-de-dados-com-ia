"""Testes de propriedade sobre a saída do modelo.

O ponto da aula: você NÃO pode testar uma saída não determinística com diff,
porque ela nunca se repete. O que dá para testar são propriedades que a saída
precisa ter, aconteça o que acontecer.

Sai com código 1 se qualquer propriedade falhar — assim o CI quebra e nada
é publicado.
"""

import json
import re
import sys
from pathlib import Path

ARQUIVO = Path(__file__).parent / "dados" / "comentario.json"

VERBOS_CAUSAIS = ["causou", "causa ", "provocou", "provoca ", "levou a",
                  "resultou em", "fez com que", "por causa d", "devido a"]


def numeros_permitidos(fatos: dict) -> set[str]:
    """Todo número citado tem que ser um destes — ou o modelo inventou."""
    brutos = [fatos["atual"], fatos["ha_12_meses"], fatos["minimo"], fatos["maximo"]]
    if fatos["ha_12_meses"] is not None:
        brutos.append(abs(fatos["atual"] - fatos["ha_12_meses"]))

    # "12" é a janela de comparação ("em 12 meses"), não um valor da série.
    permitidos = {str(fatos["meses_observados"]), "12"}
    for valor in brutos:
        if valor is None:
            continue
        permitidos.add(f"{valor:.2f}".replace(".", ","))
        permitidos.add(f"{valor:.1f}".replace(".", ","))
        permitidos.add(f"{valor:g}".replace(".", ","))
    return permitidos


def main() -> None:
    if not ARQUIVO.exists():
        sys.exit(f"{ARQUIVO} não existe. Rode comentario.py antes.")

    dado = json.loads(ARQUIVO.read_text(encoding="utf-8"))
    texto, fatos = dado["texto"], dado["fatos"]
    baixo = texto.lower()
    falhas = []

    # 1. Todo número citado existe nos dados.
    # Datas (set/2026, 09/2026) saem antes da varredura: o ano não é um valor da série.
    permitidos = numeros_permitidos(fatos)
    sem_datas = re.sub(r"\b\w{3,10}[/-]\d{4}\b|\b\d{1,2}[/-]\d{4}\b", " ", texto)
    citados = re.findall(r"\d+(?:,\d+)?", sem_datas)
    inventados = [n for n in citados if n not in permitidos]
    if inventados:
        falhas.append(f"números que não existem nos dados: {inventados} "
                      f"(permitidos: {sorted(permitidos)})")

    # 2. Nenhuma afirmação de causa
    causais = [v for v in VERBOS_CAUSAIS if v in baixo]
    if causais:
        falhas.append(f"linguagem causal encontrada: {causais}")

    # 3. Variação de taxa em pontos percentuais, não em porcentagem
    if "%" in texto and re.search(r"(caiu|subiu|aumentou|recuou|variou)[^.]{0,40}%", baixo):
        if "p.p." not in baixo and "pontos percentuais" not in baixo:
            falhas.append("variação expressa em % sem usar pontos percentuais")

    # 4. Cita o mês de referência
    if fatos["mes"].split("/")[0] not in baixo:
        falhas.append(f"não menciona o mês de referência ({fatos['mes']})")

    # 5. Tamanho plausível (2 a 3 frases)
    if not 80 <= len(texto) <= 700:
        falhas.append(f"tamanho fora do esperado: {len(texto)} caracteres")

    # 6. Sem markdown nem preâmbulo
    if re.match(r"^\s*(#|\*|-|\d\.|aqui est|segue)", baixo):
        falhas.append("começa com markdown ou preâmbulo")

    print(f"texto avaliado:\n  {texto}\n")
    if falhas:
        print(f"FALHOU em {len(falhas)} propriedade(s):")
        for f in falhas:
            print(f"  ✗ {f}")
        sys.exit(1)

    print("todas as 6 propriedades passaram ✓")


if __name__ == "__main__":
    main()
