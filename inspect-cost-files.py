#!/usr/bin/env python3
from pathlib import Path
import pandas as pd

base = Path("archivostcoonnet/CostManagement")
files = sorted(base.glob("*.xlsx"))

for fp in files:
    if "logicapps" in fp.name.lower():
        continue
    print("="*100)
    print(fp.name)
    x = pd.ExcelFile(fp)
    print("Sheets:", x.sheet_names)
    for s in x.sheet_names[:2]:
        df = pd.read_excel(fp, sheet_name=s, dtype=object)
        print(f"\nSheet: {s} | rows={len(df)} cols={len(df.columns)}")
        print("Columns:")
        for c in df.columns:
            print(" -", c)
        print("Sample:")
        print(df.head(5).to_string(index=False))
        break
