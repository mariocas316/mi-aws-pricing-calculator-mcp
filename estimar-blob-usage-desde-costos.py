#!/usr/bin/env python3
"""
Estimacion de uso Blob (GB-mes) a partir de costos de Azure CostManagement.

Importante:
- CostManagement no trae cantidad consumida (usage) en estos reportes.
- Este script estima GB-mes usando supuestos de precio por meter.
- Los supuestos estan en PRICE_RANGES_USD_PER_GB_MONTH y se pueden ajustar.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Dict, Iterable, Tuple

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
COST_DIR = BASE_DIR / "archivostcoonnet" / "CostManagement"
OUT_DIR = BASE_DIR

# Rangos aproximados USD por GB-mes para convertir costo -> GB-mes.
# low: precio mas bajo esperado, high: mas alto esperado para ese meter.
PRICE_RANGES_USD_PER_GB_MONTH: Dict[str, Tuple[float, float]] = {
    r"hot lrs data stored": (0.015, 0.024),
    r"hot grs data stored": (0.030, 0.050),
    r"hot ra-grs data stored": (0.035, 0.060),
    r"cool lrs data stored": (0.008, 0.015),
    r"cool grs data stored": (0.016, 0.030),
    r"cool ra-grs data stored": (0.018, 0.035),
    r"lrs data stored": (0.015, 0.024),
    r"grs data stored": (0.030, 0.050),
    r"premium lrs data stored": (0.10, 0.20),
    r"standard zrs data stored": (0.018, 0.035),
    # Si hay snapshot de blob, este rango es conservador. Si es snapshot de disco,
    # se recomienda excluirlo para homologacion estricta a S3.
    r"snapshots.*snapshots": (0.03, 0.08),
}

BLOB_METER_PATTERN = re.compile(
    r"data stored|blob|hot|cool|archive|container|sftp|snapshots",
    re.IGNORECASE,
)

DATA_STORED_PATTERN = re.compile(r"data stored|snapshots", re.IGNORECASE)


@dataclass
class EstimateRow:
    environment: str
    meter: str
    cost_usd: float
    matched_rule: str
    price_low: float
    price_high: float
    gb_month_low: float
    gb_month_high: float


def detect_env(filename: str) -> str:
    n = filename.lower()
    if "centralhub" in n:
        return "HUB"
    if "prod" in n:
        return "PROD"
    if "qa" in n:
        return "QA"
    if "dev" in n:
        return "DEV"
    return "UNKNOWN"


def match_price_range(meter: str) -> Tuple[str, float, float] | None:
    m = meter.lower().strip()
    for rule, (low, high) in PRICE_RANGES_USD_PER_GB_MONTH.items():
        if re.search(rule, m, flags=re.IGNORECASE):
            return rule, low, high
    return None


def load_cost_files() -> pd.DataFrame:
    files = sorted(p for p in COST_DIR.glob("*.xlsx") if "logicapps" not in p.name.lower())
    frames = []

    for fp in files:
        env = detect_env(fp.name)
        df = pd.read_excel(fp, sheet_name=0, dtype=object)
        if "CostUSD" not in df.columns:
            df["CostUSD"] = pd.to_numeric(df.get("Cost", 0), errors="coerce").fillna(0.0)
        else:
            df["CostUSD"] = pd.to_numeric(df["CostUSD"], errors="coerce").fillna(0.0)

        df["ServiceName"] = df.get("ServiceName", "").fillna("").astype(str)
        df["Meter"] = df.get("Meter", "").fillna("").astype(str)
        df["ResourceType"] = df.get("ResourceType", "").fillna("").astype(str)

        # Filtrado enfocado en Storage/Blob
        mask_storage = df["ServiceName"].str.contains("storage", case=False, na=False)
        mask_blob_meter = df["Meter"].str.contains(BLOB_METER_PATTERN, na=False)
        filtered = df[mask_storage & mask_blob_meter].copy()
        filtered["environment"] = env
        frames.append(filtered[["environment", "ServiceName", "Meter", "CostUSD"]])

    if not frames:
        return pd.DataFrame(columns=["environment", "ServiceName", "Meter", "CostUSD"])

    return pd.concat(frames, ignore_index=True)


def estimate_gb_month(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    grouped = (
        df.groupby(["environment", "Meter"], dropna=False)["CostUSD"]
        .sum()
        .reset_index()
        .rename(columns={"Meter": "meter", "CostUSD": "cost_usd"})
    )

    estimates: list[EstimateRow] = []
    non_convertible = []

    for _, row in grouped.iterrows():
        meter = str(row["meter"])
        cost = float(row["cost_usd"])
        env = str(row["environment"])

        # Solo meters que representan almacenamiento de volumen/retencion.
        # Operaciones (read/write/list) no se convierten a GB con precision.
        if not DATA_STORED_PATTERN.search(meter):
            non_convertible.append(
                {
                    "environment": env,
                    "meter": meter,
                    "cost_usd": cost,
                    "reason": "Operacion/transaccion, no volumen almacenado",
                }
            )
            continue

        matched = match_price_range(meter)
        if not matched:
            non_convertible.append(
                {
                    "environment": env,
                    "meter": meter,
                    "cost_usd": cost,
                    "reason": "Sin regla de precio configurada",
                }
            )
            continue

        rule, price_low, price_high = matched

        # Si el precio es menor, produce mayor GB para el mismo costo.
        gb_month_low = cost / price_high
        gb_month_high = cost / price_low

        estimates.append(
            EstimateRow(
                environment=env,
                meter=meter,
                cost_usd=cost,
                matched_rule=rule,
                price_low=price_low,
                price_high=price_high,
                gb_month_low=gb_month_low,
                gb_month_high=gb_month_high,
            )
        )

    est_df = pd.DataFrame([e.__dict__ for e in estimates])
    non_df = pd.DataFrame(non_convertible)
    return est_df, non_df


def summarize(est_df: pd.DataFrame, non_df: pd.DataFrame) -> None:
    if est_df.empty:
        print("No hay medidores convertibles a GB-mes con las reglas actuales.")
        return

    env_sum = (
        est_df.groupby("environment")
        .agg(
            convertible_cost_usd=("cost_usd", "sum"),
            gb_month_low=("gb_month_low", "sum"),
            gb_month_high=("gb_month_high", "sum"),
        )
        .reset_index()
        .sort_values("environment")
    )

    total_convertible = float(env_sum["convertible_cost_usd"].sum())
    total_low = float(env_sum["gb_month_low"].sum())
    total_high = float(env_sum["gb_month_high"].sum())

    non_total = float(non_df["cost_usd"].sum()) if not non_df.empty else 0.0

    print("\n=== ESTIMACION BLOB GB-MES (CONVERTIBLE) ===")
    for _, r in env_sum.iterrows():
        print(
            f"{r['environment']}: cost_usd={r['convertible_cost_usd']:.2f} | "
            f"gb_mes_aprox={r['gb_month_low']:.0f}..{r['gb_month_high']:.0f}"
        )

    print("\n=== TOTALES ===")
    print(f"Costo convertible USD: {total_convertible:.2f}")
    print(f"GB-mes estimado total: {total_low:.0f} .. {total_high:.0f}")
    print(f"Costo no convertible (operaciones) USD: {non_total:.2f}")


def save_outputs(est_df: pd.DataFrame, non_df: pd.DataFrame) -> None:
    out1 = OUT_DIR / "blob-usage-estimado-convertible.csv"
    out2 = OUT_DIR / "blob-usage-no-convertible.csv"
    out3 = OUT_DIR / "blob-usage-resumen-ambiente.csv"

    est_df.sort_values(["environment", "cost_usd"], ascending=[True, False]).to_csv(
        out1, index=False, encoding="utf-8-sig"
    )
    non_df.sort_values(["environment", "cost_usd"], ascending=[True, False]).to_csv(
        out2, index=False, encoding="utf-8-sig"
    )

    if not est_df.empty:
        summary = (
            est_df.groupby("environment")
            .agg(
                convertible_cost_usd=("cost_usd", "sum"),
                gb_month_low=("gb_month_low", "sum"),
                gb_month_high=("gb_month_high", "sum"),
            )
            .reset_index()
            .sort_values("environment")
        )
        summary.to_csv(out3, index=False, encoding="utf-8-sig")

    print("\nArchivos generados:")
    print(f" - {out1.name}")
    print(f" - {out2.name}")
    print(f" - {out3.name}")


def main() -> None:
    df = load_cost_files()
    if df.empty:
        print("No se encontraron filas Blob/Storage en CostManagement.")
        return

    est_df, non_df = estimate_gb_month(df)
    summarize(est_df, non_df)
    save_outputs(est_df, non_df)


if __name__ == "__main__":
    main()
