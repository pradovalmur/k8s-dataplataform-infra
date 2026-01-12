#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filtra CSVs (; separado, pt-BR) do Tesouro Direto:
1) Operacoes: mantém apenas um intervalo de datas e (opcional) particiona por ano/mes.
2) Investidores: mantém apenas investidores que aparecem nas operações filtradas.

Resolve CSVs com encoding Windows-1252/Latin-1 (muito comum nesses dados).

Uso:
  python td_filter.py \
    --operacoes operacoes.csv \
    --investidores investidores.csv \
    --outdir out \
    --start 2023-01-01 --end 2024-12-31 \
    --partition year-month

Partition:
  none | year | year-month | day
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Iterable, Set, Tuple, Optional

CSV_DIA_MES_ANO = "%d/%m/%Y"


def parse_date_br(s: str) -> date:
    s = (s or "").strip()
    return datetime.strptime(s, CSV_DIA_MES_ANO).date()


def parse_date_iso(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def normalize_header(h: str) -> str:
    return (h or "").strip()


def partition_key(d: date, mode: str) -> str:
    if mode == "none":
        return "all"
    if mode == "year":
        return f"{d.year:04d}"
    if mode == "year-month":
        return f"{d.year:04d}-{d.month:02d}"
    if mode == "day":
        return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"
    raise ValueError(f"partition inválido: {mode}")


def open_csv(path: Path, mode: str):
    """
    Tesouro Direto costuma vir em Windows-1252/Latin-1.
    latin-1 nunca falha no decode (1:1 bytes->unicode), então evita UnicodeDecodeError.
    """
    return path.open(mode, encoding="latin-1", newline="")


def open_writer(path: Path, fieldnames: Iterable[str]) -> Tuple[object, csv.DictWriter]:
    ensure_dir(path.parent)
    f = path.open("w", encoding="utf-8", newline="")  # saída em UTF-8
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
    w.writeheader()
    return f, w


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--operacoes", required=True, help="CSV de operações (delimiter ';')")
    ap.add_argument("--investidores", required=True, help="CSV de investidores (delimiter ';')")
    ap.add_argument("--outdir", required=True, help="Diretório de saída")
    ap.add_argument("--start", required=True, help="Data inicial ISO (YYYY-MM-DD)")
    ap.add_argument("--end", required=True, help="Data final ISO (YYYY-MM-DD) (inclusive)")
    ap.add_argument(
        "--partition",
        default="year-month",
        choices=["none", "year", "year-month", "day"],
        help="Como particionar o output de operações",
    )
    args = ap.parse_args()

    start = parse_date_iso(args.start)
    end = parse_date_iso(args.end)

    outdir = Path(args.outdir)
    ensure_dir(outdir)

    ops_in = Path(args.operacoes)
    inv_in = Path(args.investidores)

    # -------------------------
    # 1) Filtrar operações
    # -------------------------
    investors_in_period: Set[str] = set()
    writers: Dict[str, Tuple[object, csv.DictWriter]] = {}

    ops_total = 0
    ops_kept = 0

    col_investidor_ops = "Codigo do Investidor"
    col_data_ops = "Data da Operacao"

    with open_csv(ops_in, "r") as f:
        r = csv.DictReader(f, delimiter=";")

        # atenção: isso dispara o read da primeira linha (onde estourava o UnicodeDecodeError)
        if not r.fieldnames:
            raise SystemExit("CSV de operações sem header.")

        fieldnames = [normalize_header(x) for x in r.fieldnames]
        r.fieldnames = fieldnames

        if col_investidor_ops not in fieldnames or col_data_ops not in fieldnames:
            raise SystemExit(
                f"CSV operações precisa ter colunas '{col_investidor_ops}' e '{col_data_ops}'. "
                f"Encontrei: {fieldnames}"
            )

        for row in r:
            ops_total += 1
            try:
                d = parse_date_br(row.get(col_data_ops, ""))
            except Exception:
                # linha inválida, ignora
                continue

            if d < start or d > end:
                continue

            ops_kept += 1
            inv_id = (row.get(col_investidor_ops, "") or "").strip()
            if inv_id:
                investors_in_period.add(inv_id)

            pkey = partition_key(d, args.partition)
            if pkey not in writers:
                out_path = outdir / "operacoes" / f"operacoes_{pkey}.csv"
                fh, w = open_writer(out_path, fieldnames)
                writers[pkey] = (fh, w)

            _, w = writers[pkey]
            w.writerow(row)

    for fh, _ in writers.values():
        fh.close()

    # arquivo consolidado único
    consolidated_path = outdir / "operacoes" / "operacoes_filtradas.csv"
    ensure_dir(consolidated_path.parent)

    with open_csv(ops_in, "r") as fin, consolidated_path.open("w", encoding="utf-8", newline="") as fout:
        rin = csv.DictReader(fin, delimiter=";")
        if not rin.fieldnames:
            raise SystemExit("CSV de operações sem header (na releitura).")
        rin.fieldnames = [normalize_header(x) for x in rin.fieldnames]

        wout = csv.DictWriter(fout, fieldnames=rin.fieldnames, delimiter=";")
        wout.writeheader()

        for row in rin:
            try:
                d = parse_date_br(row.get(col_data_ops, ""))
            except Exception:
                continue
            if start <= d <= end:
                wout.writerow(row)

    # -------------------------
    # 2) Filtrar investidores
    # -------------------------
    inv_total = 0
    inv_kept = 0

    col_investidor_inv = "Codigo do Investidor"
    inv_out_path = outdir / "investidores" / "investidores_filtrados.csv"
    ensure_dir(inv_out_path.parent)

    with open_csv(inv_in, "r") as fin:
        r = csv.DictReader(fin, delimiter=";")
        if not r.fieldnames:
            raise SystemExit("CSV de investidores sem header.")

        fieldnames = [normalize_header(x) for x in r.fieldnames]
        r.fieldnames = fieldnames

        if col_investidor_inv not in fieldnames:
            raise SystemExit(
                f"CSV investidores precisa ter coluna '{col_investidor_inv}'. Encontrei: {fieldnames}"
            )

        with inv_out_path.open("w", encoding="utf-8", newline="") as fout:
            w = csv.DictWriter(fout, fieldnames=fieldnames, delimiter=";")
            w.writeheader()

            for row in r:
                inv_total += 1
                inv_id = (row.get(col_investidor_inv, "") or "").strip()
                if inv_id and inv_id in investors_in_period:
                    inv_kept += 1
                    w.writerow(row)

    # -------------------------
    # 3) Resumo
    # -------------------------
    summary_path = outdir / "summary.txt"
    with summary_path.open("w", encoding="utf-8") as f:
        f.write(f"Periodo: {start.isoformat()} .. {end.isoformat()} (inclusive)\n")
        f.write(f"Operacoes: total={ops_total}, mantidas={ops_kept}\n")
        f.write(f"Investidores (com operacoes no periodo): {len(investors_in_period)}\n")
        f.write(f"Investidores CSV: total={inv_total}, mantidos={inv_kept}\n\n")
        f.write("Saidas:\n")
        f.write(f"- {consolidated_path}\n")
        f.write(f"- {inv_out_path}\n")
        f.write(f"- {outdir / 'operacoes'} (partições)\n")

    print(f"OK. Operacoes mantidas: {ops_kept}/{ops_total}. Investidores mantidos: {inv_kept}/{inv_total}.")
    print(f"Saída em: {outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
