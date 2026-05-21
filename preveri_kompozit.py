# -*- coding: utf-8 -*-
"""
preveri_kompozit.py — diagnostika kompozit fajlov in prisotnosti BP-jev.

Za podane BP lokacije izpise:
  1. Velikost vsakega <BAND>_1_w.txt fajla v kompozit mapi
  2. Najdene celice te BP per band (regex match na ime BP)
  3. Iz Denali (preko izbor_celic) izpise pricakovane celice za primerjavo

Uporaba:
  py -3.10 preveri_kompozit.py LHOTIC SDOLEN SBOKRA
  py -3.10 preveri_kompozit.py SBOKRA --mapa D:\\custom\\path\\
"""

import argparse
import os
import re
import sys
import warnings

warnings.simplefilter("ignore")

DEFAULT_MAPA = r"D:\Atoll_projects_planer01\Pokrivanja\Kompozit\\"


def file_sizes(mapa):
    print("=" * 60)
    print(f"VSEBINA KOMPOZIT MAPE: {mapa}")
    print("=" * 60)
    if not os.path.isdir(mapa):
        print(f"  MAPA NE OBSTAJA!")
        return []
    fajli = sorted([f for f in os.listdir(mapa) if f.endswith("_1_w.txt")])
    if not fajli:
        print("  Ni nobenega _1_w.txt fajla.")
        return []
    for f in fajli:
        size_mb = os.path.getsize(os.path.join(mapa, f)) / (1024 * 1024)
        print(f"  {f:30s}  {size_mb:8.1f} MB")
    print(f"  ({len(fajli)} fajlov skupaj)")
    return fajli


def cells_in_kompozit(mapa, fajli, bp_imena):
    print()
    print("=" * 60)
    print(f"PRISOTNOST BP V KOMPOZIT FAJLIH")
    print("=" * 60)
    pattern = "|".join(re.escape(b) + r"\w*" for b in bp_imena)
    rgx = re.compile(pattern)

    for f in fajli:
        full = os.path.join(mapa, f)
        try:
            with open(full, "r", encoding="utf-8", errors="ignore") as fp:
                text = fp.read()
        except Exception as e:
            print(f"\n  {f}: NAPAKA pri branju ({e})")
            continue

        cells = sorted(set(rgx.findall(text)))
        print(f"\n  {f}:")
        if not cells:
            print(f"    (nobene celice teh {len(bp_imena)} BP-jev)")
        else:
            # Group by BP
            by_bp = {}
            for c in cells:
                for b in bp_imena:
                    if c.startswith(b):
                        by_bp.setdefault(b, []).append(c)
                        break
            for b in bp_imena:
                if b in by_bp:
                    print(f"    {b}: {by_bp[b]}")
                else:
                    print(f"    {b}: (ni)")


def cells_in_denali(bp_imena):
    print()
    print("=" * 60)
    print(f"DENALI - PRICAKOVANE CELICE PO BP")
    print("=" * 60)
    sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\upravicenost_bazne_postaje")
    try:
        import upravicenost_bp_atoll_datafill as udatafill
    except Exception as e:
        print(f"  NAPAKA pri import-u upravicenost_bp_atoll_datafill: {e}")
        return

    for b in bp_imena:
        try:
            df = udatafill.izbor_celic(seznam_lokacij=[b], pisi_v_fajl=False)
            celice = df['celica'].drop_duplicates().tolist()
            print(f"\n  {b} ({len(celice)} celic):")
            # Group by tehnologija
            if 'teh' in df.columns:
                for teh in df['teh'].drop_duplicates().tolist():
                    sub = df[df['teh'] == teh]['celica'].tolist()
                    print(f"    {teh}: {sub}")
            else:
                print(f"    {celice}")
        except Exception as e:
            print(f"\n  {b}: NAPAKA ({e})")


def cells_in_atoll_sql(bp_imena):
    print()
    print("=" * 60)
    print(f"ATOLL SQL - DEJANSKE CELICE V ATL DOC PER BP")
    print("=" * 60)
    sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\atoll_export")
    try:
        import sql_atoll_3794
        import pandas as pd
    except Exception as e:
        print(f"  NAPAKA pri import-u sql_atoll_3794: {e}")
        return

    try:
        # GSM transmiterji
        gtrans = pd.read_sql(sql_atoll_3794.query_gtransmitters, sql_atoll_3794.conn_atoll)
        # LTE/NR transmiterji
        xgtrans = pd.read_sql(sql_atoll_3794.query_xgtransmitters, sql_atoll_3794.conn_atoll)
    except Exception as e:
        print(f"  NAPAKA pri SQL queryju: {e}")
        return

    for b in bp_imena:
        gsm = gtrans[gtrans['SITE_NAME'] == b]['TX_ID'].tolist()
        xg = xgtrans[xgtrans['SITE_NAME'] == b]['TX_ID'].tolist()
        active_g = gtrans[(gtrans['SITE_NAME'] == b) & (gtrans['ACTIVE'] == 1)]['TX_ID'].tolist()
        active_xg = xgtrans[(xgtrans['SITE_NAME'] == b) & (xgtrans['ACTIVE'] == 1)]['TX_ID'].tolist()

        print(f"\n  {b}:")
        print(f"    GSM transmiterji ({len(gsm)}, active={len(active_g)}): {gsm}")
        print(f"    LTE/NR transmiterji ({len(xg)}, active={len(active_xg)}): {xg}")
        # Highlight inactive
        inactive_g = [c for c in gsm if c not in active_g]
        inactive_xg = [c for c in xg if c not in active_xg]
        if inactive_g or inactive_xg:
            print(f"    NEAKTIVNI: GSM={inactive_g}, LTE/NR={inactive_xg}")


def main():
    p = argparse.ArgumentParser(description="Diagnostika kompozit fajlov za podane BP.")
    p.add_argument("bp", nargs="+", help="Imena BP lokacij (npr. LHOTIC SDOLEN SBOKRA)")
    p.add_argument("--mapa", default=DEFAULT_MAPA, help=f"Pot do kompozit mape (default {DEFAULT_MAPA})")
    p.add_argument("--no-denali", action="store_true", help="Preskoci Denali query")
    p.add_argument("--no-sql", action="store_true", help="Preskoci Atoll SQL query")
    args = p.parse_args()

    bp_imena = [b.strip().upper() for b in args.bp]
    print(f"BP za preverbo: {bp_imena}\n")

    fajli = file_sizes(args.mapa)
    if fajli:
        cells_in_kompozit(args.mapa, fajli, bp_imena)

    if not args.no_sql:
        cells_in_atoll_sql(bp_imena)

    if not args.no_denali:
        cells_in_denali(bp_imena)


if __name__ == "__main__":
    main()
