# -*- coding: utf-8 -*-
r"""
Dumpa VSE NR/LTE-povezane parametre + dependency tabele iz .atl dokumenta v CSV-je
za primerjavo med dvema .atl projektoma (planer01 vs planer02).

Vse v ENEM Atoll Open() ciklu - vkljucno z antennas filtered po dejanskih ANTENNA_NAME
vrednostih iz xgtransmitters dump-a.

Uporaba:
  py -3.10 dump_atl_nr_parametri.py

Predpogoji:
  - Atoll.exe NE sme teci (skripta sama odpre programsko)
  - py -3.10 -m pip install pywin32

Output v OUTPUT_DIR:
  xgcells5gnr_NR_dump.csv     - NR cells (filtrirane po site prefiksu)
  xgcellslte_NR_dump.csv      - LTE cells (filtrirane)
  xgtransmitters_NR_dump.csv  - transmitters (filtrirani)
  sites_NR_dump.csv           - sites (filtrirani)
  xgcarriers_FULL.csv         - vsi carriers
  xgfreqbands_FULL.csv        - vsi frequency bands
  xgequipments_FULL.csv       - equipment templates (ce uspe)
  antennas_USED.csv           - antennas FILTRIRANE samo na tiste iz xgtransmitters
  propagationmodels_FULL.csv  - propag models (ce uspe)
  Networks_FULL.csv           - networks
  coordsys_FULL.csv           - coordinate systems
  tables_found.txt            - seznam vseh uspesno dumpanih tabel

Za Zigov planer02:
  na vrhu skripte prilagodi:
    ATL_PATH = r"G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794_3_5_1.ATL"
    OUTPUT_DIR = Path(r"G:\diag_atl_dump")  # ali C:\Users\planer02\diag_atl_dump
  pozeni isto skripto, posljes mi celotno OUTPUT_DIR mapo.
"""

import os
import sys
import time
from pathlib import Path

try:
    import win32com.client
except ImportError:
    print("MANJKA pywin32. Namesti z: py -3.10 -m pip install pywin32")
    sys.exit(1)


# ============= Nastavitve =============
# PRILAGODI ZA TVOJ STROJ:
ATL_PATH = r"D:\Atoll_projects_planer01\Atoll_exporti_3794_3_5_1.ATL"
OUTPUT_DIR = Path(r"D:\Atoll_projects_planer01\diag_atl_dump")

# Katere BP zanimajo (CELL_ID / TX_ID / SITE_NAME prefiks)
SITES_INTEREST = ("SBOKRA", "SDOLEN", "LHOTIC", "PANKAR", "SCVEN")


def is_interesting_site(name):
    if not name:
        return False
    n = str(name).upper()
    return any(n.startswith(s) for s in SITES_INTEREST)


def get_attr_safely(obj, *names):
    for n in names:
        try:
            return getattr(obj, n)
        except AttributeError:
            continue
    return None


def get_table_dim(tbl):
    n_cols = get_attr_safely(tbl, "ColumnCount", "columnCount")
    n_rows = get_attr_safely(tbl, "RecordCount", "recordCount", "RowCount", "rowCount")
    return n_cols, n_rows


def read_headers(tbl, n_cols):
    headers = []
    for c in range(n_cols):
        try:
            h = tbl.GetValue(0, c)
        except Exception:
            h = None
        headers.append(str(h) if h is not None else f"col{c}")
    return headers


def csv_escape(s):
    if s is None:
        return ""
    s = str(s)
    if ";" in s or '"' in s or "\n" in s or "\r" in s:
        s = '"' + s.replace('"', '""') + '"'
    return s


def write_row(f, vals):
    f.write(";".join(csv_escape(v) for v in vals) + "\n")


def dump_table_filtered(doc, table_name, key_column, filter_fn, out_path,
                        collect_col=None, log_prefix=""):
    """Dumpa rows kjer filter_fn(row[key_column])==True.

    Ce je collect_col podan, vrne tudi set unikatnih vrednosti iz tega stolpca
    (za naknadno filter-anje druge tabele - npr. ANTENNA_NAME).
    """
    collected = set()
    try:
        tbl = doc.GetRecords(table_name, False)
    except Exception as e:
        print(f"{log_prefix}[{table_name}] NAPAKA pri GetRecords: {e}")
        return None
    try:
        tbl.Filter = ""
    except Exception:
        pass

    n_cols, n_rows = get_table_dim(tbl)
    if n_cols is None or n_rows is None:
        print(f"{log_prefix}[{table_name}] NAPAKA: ne dobim dimensions")
        return None

    headers = read_headers(tbl, n_cols)
    if key_column not in headers:
        print(f"{log_prefix}[{table_name}] OPOZORILO: key column '{key_column}' ni najden")
        return None
    key_idx = headers.index(key_column)

    collect_idx = None
    if collect_col and collect_col in headers:
        collect_idx = headers.index(collect_col)

    print(f"{log_prefix}[{table_name}] {n_rows} vrstic, {n_cols} stolpcev -> filtriram po {key_column}")
    n_dumped = 0
    with open(out_path, "w", encoding="utf-8") as f:
        write_row(f, headers)
        for r in range(1, n_rows + 1):
            try:
                key_val = tbl.GetValue(r, key_idx)
            except Exception:
                continue
            if not filter_fn(key_val):
                continue
            row = []
            for c in range(n_cols):
                try:
                    row.append(tbl.GetValue(r, c))
                except Exception:
                    row.append("")
            write_row(f, row)
            n_dumped += 1
            if collect_idx is not None:
                try:
                    v = tbl.GetValue(r, collect_idx)
                    if v is not None and str(v).strip():
                        collected.add(str(v).strip())
                except Exception:
                    pass

    msg = f"{log_prefix}[{table_name}] dumpano {n_dumped} vrstic -> {out_path.name}"
    if collect_col:
        msg += f" (zbral {len(collected)} unikatnih {collect_col})"
    print(msg)
    return collected if collect_col else set()


def dump_table_full(doc, table_name, out_path, max_rows=5000, log_prefix=""):
    try:
        tbl = doc.GetRecords(table_name, False)
    except Exception as e:
        print(f"{log_prefix}[{table_name}] NAPAKA pri GetRecords: {e}")
        return False
    try:
        tbl.Filter = ""
    except Exception:
        pass

    n_cols, n_rows = get_table_dim(tbl)
    if n_cols is None or n_rows is None:
        print(f"{log_prefix}[{table_name}] NAPAKA: ne dobim dimensions")
        return False

    headers = read_headers(tbl, n_cols)
    print(f"{log_prefix}[{table_name}] {n_rows} vrstic, {n_cols} stolpcev (FULL)")
    truncated = False
    if n_rows > max_rows:
        print(f"{log_prefix}[{table_name}] OPOZORILO: truncating na prvih {max_rows}")
        n_rows = max_rows
        truncated = True

    with open(out_path, "w", encoding="utf-8") as f:
        write_row(f, headers)
        for r in range(1, n_rows + 1):
            row = []
            for c in range(n_cols):
                try:
                    row.append(tbl.GetValue(r, c))
                except Exception:
                    row.append("")
            write_row(f, row)
    print(f"{log_prefix}[{table_name}] dumpano {n_rows} vrstic -> {out_path.name}")
    return not truncated


def dump_antennas_filtered(doc, antenna_names, out_path, log_prefix=""):
    """Dumpa SAMO tiste antennas, ki so v antenna_names set."""
    if not antenna_names:
        print(f"{log_prefix}[antennas] OPOZORILO: nicemur ne filtriram, preskakam.")
        return False

    print(f"{log_prefix}[antennas] iscem {len(antenna_names)} unikatnih antenn:")
    for n in sorted(antenna_names):
        print(f"  {n}")

    try:
        tbl = doc.GetRecords("antennas", False)
    except Exception as e:
        print(f"{log_prefix}[antennas] NAPAKA pri GetRecords: {e}")
        return False
    try:
        tbl.Filter = ""
    except Exception:
        pass

    n_cols, n_rows = get_table_dim(tbl)
    if n_cols is None or n_rows is None:
        print(f"{log_prefix}[antennas] NAPAKA: ne dobim dimensions")
        return False

    headers = read_headers(tbl, n_cols)
    name_idx = None
    for cand in ("NAME", "ANTENNA_NAME", "Name", "name"):
        if cand in headers:
            name_idx = headers.index(cand)
            break
    if name_idx is None:
        print(f"{log_prefix}[antennas] NAPAKA: ne najdem NAME stolpca.")
        print(f"   Headers: {headers}")
        return False

    print(f"{log_prefix}[antennas] {n_rows} vrstic skupaj, iteriram in matcham po '{headers[name_idx]}'...")
    n_dumped = 0
    found = set()
    with open(out_path, "w", encoding="utf-8") as f:
        write_row(f, headers)
        for r in range(1, n_rows + 1):
            try:
                name = tbl.GetValue(r, name_idx)
            except Exception:
                continue
            name_str = str(name) if name is not None else ""
            if name_str not in antenna_names:
                continue
            row = []
            for c in range(n_cols):
                try:
                    row.append(tbl.GetValue(r, c))
                except Exception:
                    row.append("")
            write_row(f, row)
            n_dumped += 1
            found.add(name_str)

    print(f"{log_prefix}[antennas] dumpano {n_dumped} match-ov -> {out_path.name}")

    not_found = antenna_names - found
    if not_found:
        print(f"{log_prefix}[antennas] OPOZORILO: {len(not_found)} anten NI najdenih v 'antennas' tabeli:")
        for n in sorted(not_found):
            print(f"  {n}")
    return True


def main():
    if not os.path.exists(ATL_PATH):
        print(f"NAPAKA: .atl ne obstaja: {ATL_PATH}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Odpiram Atoll + .atl: {ATL_PATH}")
    print("(traja 10-30s)")
    atoll = win32com.client.Dispatch("Atoll.Application")
    doc = atoll.Documents.Open(ATL_PATH)
    try:
        atoll.Visible = True
    except Exception:
        pass

    print("Cakam, da se .atl konca nalagati (max 60s)...")
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            if not doc.HasRunningTask:
                break
        except Exception:
            break
        time.sleep(0.3)
    print("OK, dokument nalozen.\n")

    successful = []

    # ============= 1. Filtrirane tabele =============
    print("--- Filtrirane tabele (samo SITES_INTEREST) ---")
    if dump_table_filtered(doc, "xgcells5gnr", "CELL_ID",
                           is_interesting_site,
                           OUTPUT_DIR / "xgcells5gnr_NR_dump.csv") is not None:
        successful.append("xgcells5gnr")

    if dump_table_filtered(doc, "xgcellslte", "CELL_ID",
                           is_interesting_site,
                           OUTPUT_DIR / "xgcellslte_NR_dump.csv") is not None:
        successful.append("xgcellslte")

    # xgtransmitters + ZBIRANJE ANTENNA_NAME za naknadni antennas dump
    antenna_names = dump_table_filtered(
        doc, "xgtransmitters", "TX_ID",
        is_interesting_site,
        OUTPUT_DIR / "xgtransmitters_NR_dump.csv",
        collect_col="ANTENNA_NAME"
    )
    if antenna_names is not None:
        successful.append("xgtransmitters")
    else:
        antenna_names = set()

    if dump_table_filtered(doc, "sites", "NAME",
                           is_interesting_site,
                           OUTPUT_DIR / "sites_NR_dump.csv") is not None:
        successful.append("sites")

    # ============= 2. Definition tables (FULL) =============
    print("\n--- Definition tabele (FULL dump) ---")
    if dump_table_full(doc, "xgcarriers", OUTPUT_DIR / "xgcarriers_FULL.csv"):
        successful.append("xgcarriers")
    if dump_table_full(doc, "xgfreqbands", OUTPUT_DIR / "xgfreqbands_FULL.csv"):
        successful.append("xgfreqbands")

    # ============= 3. Equipment templates =============
    print("\n--- Equipment templates (probam vec imen) ---")
    for tn in ("xgequipments", "xgequipment", "equipments", "equipment",
               "xgcellequipments", "xgradioequipments", "xgnequipments"):
        if dump_table_full(doc, tn, OUTPUT_DIR / f"{tn}_FULL.csv"):
            successful.append(tn)
            break

    # ============= 4. Antennas FILTRIRANE po ANTENNA_NAME iz xgtransmitters =============
    print("\n--- Antennas (filtrirane po ANTENNA_NAME) ---")
    if dump_antennas_filtered(doc, antenna_names, OUTPUT_DIR / "antennas_USED.csv"):
        successful.append("antennas_USED")

    # ============= 5. Propagation models =============
    print("\n--- Propagation models ---")
    for tn in ("propagationmodels", "propagmodels", "xgpropagmodels", "propag_models"):
        if dump_table_full(doc, tn, OUTPUT_DIR / f"{tn}_FULL.csv"):
            successful.append(tn)
            break

    # ============= 6. Bonus tables =============
    print("\n--- Bonus tables ---")
    if dump_table_full(doc, "Networks", OUTPUT_DIR / "Networks_FULL.csv"):
        successful.append("Networks")
    if dump_table_full(doc, "coordsys", OUTPUT_DIR / "coordsys_FULL.csv"):
        successful.append("coordsys")

    # ============= Close =============
    print("\nZapiram dokument (brez shranjevanja)...")
    try:
        doc.Close(0)
    except Exception as e:
        print(f"  Close error: {e}")
    try:
        atoll.Quit()
    except Exception:
        pass

    # Meta fajl
    meta_path = OUTPUT_DIR / "tables_found.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        f.write("Uspesno dumpane tabele:\n")
        for t in successful:
            f.write(f"  - {t}\n")

    print(f"\n=== KONEC ===")
    print(f"CSV fajli v: {OUTPUT_DIR}")
    print(f"Uspesno: {len(successful)} tabel")
    print(f"  {', '.join(successful)}")


if __name__ == "__main__":
    main()
