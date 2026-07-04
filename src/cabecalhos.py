import os
import pandas as pd

BASE_DIR = "../data"

for root, _, files in os.walk(BASE_DIR):
    for file in files:
        if file.lower().endswith(".csv"):
            path = os.path.join(root, file)
            try:
                df = pd.read_csv(path, nrows=0, sep=None, engine="python", encoding="utf-8")
            except:
                df = pd.read_csv(path, nrows=0, sep=None, engine="python", encoding="latin1")

            print("\n" + "=" * 80)
            print(file)
            print(list(df.columns))
