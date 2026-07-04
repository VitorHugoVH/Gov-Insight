import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")


def analisar_csv(caminho):
    print("\n" + "=" * 80)
    print(f"Arquivo: {caminho}")

    try:
        df = pd.read_csv(
            caminho,
            sep=None,
            engine="python",
            encoding="utf-8"
        )
    except:
        df = pd.read_csv(
            caminho,
            sep=None,
            engine="python",
            encoding="latin1"
        )

    print(f"Linhas: {len(df)}")
    print(f"Colunas: {len(df.columns)}")

    for coluna in df.columns:
        nulos = (
            df[coluna]
            .astype(str)
            .str.strip()
            .isin(["", "-", " -", "nan", "None"])
            .sum()
        )

        percentual = (nulos / len(df)) * 100

        if percentual > 0:
            print(
                f"{coluna}: "
                f"{nulos} registros vazios "
                f"({percentual:.2f}%)"
            )


for root, _, files in os.walk(DATA_DIR):
    for arquivo in files:
        if arquivo.lower().endswith(".csv"):
            caminho = os.path.join(root, arquivo)
            analisar_csv(caminho)