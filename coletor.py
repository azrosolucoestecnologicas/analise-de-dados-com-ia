"""Baixa a meta da taxa Selic (série 432 do SGS/BCB) e salva em dados/selic.json."""

import json
import time
from datetime import date
from pathlib import Path

import requests

URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.432/dados"
DESTINO = Path(__file__).parent / "dados" / "selic.json"
TENTATIVAS = 3


def baixar() -> list[dict]:
    params = {
        "formato": "json",
        "dataInicial": "01/01/2017",
        "dataFinal": date.today().strftime("%d/%m/%Y"),
    }

    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.get(URL, params=params, timeout=60)
            resposta.raise_for_status()

            # A API do BCB responde HTTP 200 com uma página HTML quando recusa a
            # requisição. Checar só o status_code não detecta a falha.
            if not resposta.text.lstrip().startswith("["):
                raise ValueError("resposta não é JSON (a API devolveu HTML)")

            return resposta.json()

        except (requests.RequestException, ValueError) as erro:
            print(f"  tentativa {tentativa}/{TENTATIVAS} falhou: {erro}")
            if tentativa < TENTATIVAS:
                time.sleep(2**tentativa)

    raise SystemExit(f"não foi possível baixar a série. Abra no navegador: {URL}?formato=json")


def main() -> None:
    dados = baixar()
    DESTINO.parent.mkdir(exist_ok=True)
    DESTINO.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
    print(f"{len(dados)} pontos · {dados[0]['data']} a {dados[-1]['data']} → {DESTINO}")


if __name__ == "__main__":
    main()
