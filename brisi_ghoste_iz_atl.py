# -*- coding: utf-8 -*-
"""
brisi_ghoste_iz_atl.py — odstrani "ghost" celice iz LOKALNEGA ATL doc-a.

Ghost celica = celica, ki je v atoll_d96 SQL ampak NI v Denali (planer jo je
odstranil iz nacrta, vendar Zigov nightly se ni sinhroniziral).

Skripta NE pise v atoll_d96 SQL (ne tangira Zigovega ali skupne baze).
Samo modificira lokalni `Atoll_exporti_3794_3_5_1.ATL` preko obstojecega
Brisi/comp_zone.vbs mehanizma.

Workflow:
  1. Poizve atoll_d96 SQL (Atoll cells per BP)
  2. Poizve Denali SQL (kar PLANER zeli per BP)
  3. Diff:
     - BRISI = Atoll \\ Denali  → predlaga za izbris (ghost cells)
     - NOVO  = Denali \\ Atoll  → samo INFO (skripta NE doda; rabi SQL INSERT)
  4. Z `--apply` zapise Brisi CSV-je v ...\\Upravicenost_bazne_postaje\\Brisi\\
     in pozene comp_zone.vbs, ki Brisi aplicira na ATL doc.
  5. Po tem teča v0 pipeline normalno — vidi cista 12 cells per BP namesto 18.

Uporaba:
  py -3.10 brisi_ghoste_iz_atl.py SBOKRA SDOLEN LHOTIC                # dry run
  py -3.10 brisi_ghoste_iz_atl.py SBOKRA SDOLEN LHOTIC --apply        # actually delete

Po `--apply` poženi normalno:
  py -3.10 D:\\Atoll_projects_planer01\\Skripte\\Python\\upravicenost_bazne_postaje\\upravicenost_bazne_postaje.py
"""

import argparse
import os
import sys
import subprocess

import pandas as pd

sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\atoll_export")
sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\upravicenost_bazne_postaje")

import sql_atoll_3794
import sql_denali_3794
import warnings
warnings.simplefilter("ignore")


BRISI = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Brisi\\"
SPREMENI = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Spremeni\\"
NOVO = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Novo\\"
COMP_ZONE_VBS = r"D:\Atoll_projects_planer01\Skripte\VBasic\posodobi_atoll_3794_update_planirano_comp_zone.vbs"


def query_atoll(bps):
    xg = pd.read_sql(sql_atoll_3794.query_xgtransmitters, sql_atoll_3794.conn_atoll)
    g = pd.read_sql(sql_atoll_3794.query_gtransmitters, sql_atoll_3794.conn_atoll)
    return xg[xg['SITE_NAME'].isin(bps)], g[g['SITE_NAME'].isin(bps)]


def query_denali(bps):
    cel_den = pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
    return cel_den[cel_den['rru_ime'].isin(bps)]


def detektiraj_rename(ghost_cell, denali_cells):
    """
    Vrne (True, opis) ce je ghost_cell verjetno preimenovana celica, ki obstaja
    v Denali pod drugim imenom. Vrne (False, None) drugace.

    Razpoznane rename pattern:
    - "07SS" → "07NR" (NR 700 naming change pri Telekomu, ravno se izvaja)

    Ce dodava nove pattern-e, dodaj tukaj.
    """
    if '07SS' in ghost_cell:
        candidate = ghost_cell.replace('07SS', '07NR')
        if candidate in denali_cells:
            return True, f"verjetno rename → {candidate}"
        # Sufiks lahko ni isti, preveri samo prefix
        prefix = ghost_cell.split('07SS')[0]  # npr. "SBOKRA"
        suffix = ghost_cell.split('07SS')[1]  # npr. "A"
        for d in denali_cells:
            if d.startswith(prefix + '07NR') and d.endswith(suffix):
                return True, f"verjetno rename → {d}"
    return False, None


def compute_diff(bps, keep_patterns=None):
    """
    keep_patterns: seznam substring-ov, celice, ki vsebujejo katerega koli, niso ghost.
    """
    keep_patterns = keep_patterns or []
    xg, g = query_atoll(bps)
    den = query_denali(bps)

    brisi_g_all, brisi_xg_all = [], []
    novi_g_all, novi_xg_all = [], []
    skip_bps = []  # BP-ji, ki jih preskocimo zaradi safety checka

    print("=" * 75)
    print("DIFF Atoll vs Denali per BP")
    print("=" * 75)

    for bp in bps:
        atoll_g_bp = sorted(g[g['SITE_NAME'] == bp]['TX_ID'].drop_duplicates().tolist())
        atoll_xg_bp = sorted(xg[xg['SITE_NAME'] == bp]['TX_ID'].drop_duplicates().tolist())

        den_bp = den[den['rru_ime'] == bp]
        den_g_bp = sorted(den_bp[den_bp['tehn'] == 'GSM']['celica'].drop_duplicates().tolist())
        den_xg_bp = sorted(den_bp[den_bp['tehn'].isin(['LTE', '5G'])]['celica'].drop_duplicates().tolist())
        den_all_bp = den_g_bp + den_xg_bp

        atoll_total = len(atoll_g_bp) + len(atoll_xg_bp)
        den_total = len(den_g_bp) + len(den_xg_bp)

        print(f"\n  {bp}:")
        print(f"    Atoll : {len(atoll_g_bp)} GSM + {len(atoll_xg_bp)} LTE/NR → {atoll_g_bp + atoll_xg_bp}")
        print(f"    Denali: {len(den_g_bp)} GSM + {len(den_xg_bp)} LTE/NR → {den_g_bp + den_xg_bp}")

        # SAFETY CHECK 1: Denali prazen, Atoll ni → preskoci (da ne brisemo BP)
        if den_total == 0 and atoll_total > 0:
            print(f"    ❌ SAFETY: Denali vrne 0 celic za to BP, Atoll pa {atoll_total}.")
            print(f"       Verjetno je BP odstranjena iz Denali ALI rru_ime se je preimenovan.")
            print(f"       Skripta NE BO brisala te BP. Preveri rocno (npr. za naming v ImeBSC).")
            skip_bps.append(bp)
            continue

        # Razdvoji "ghost" v: real ghost vs rename pending vs --keep override
        def klasificiraj(atoll_list, den_list, label):
            real_ghosts = []
            rename_skipped = []
            keep_skipped = []
            for c in atoll_list:
                if c in den_list:
                    continue  # ujema, ni ghost
                # Preveri --keep
                if any(p in c for p in keep_patterns):
                    keep_skipped.append(c)
                    continue
                # Preveri rename
                is_rename, opis = detektiraj_rename(c, den_all_bp)
                if is_rename:
                    rename_skipped.append((c, opis))
                    continue
                real_ghosts.append(c)
            return real_ghosts, rename_skipped, keep_skipped

        ghost_g_bp, rename_g_bp, keep_g_bp = klasificiraj(atoll_g_bp, den_g_bp, 'GSM')
        ghost_xg_bp, rename_xg_bp, keep_xg_bp = klasificiraj(atoll_xg_bp, den_xg_bp, 'LTE/NR')

        novi_g_bp = [c for c in den_g_bp if c not in atoll_g_bp]
        novi_xg_bp = [c for c in den_xg_bp if c not in atoll_xg_bp]

        # Rename-pending — tudi ti so "manjkajoci v Atollu" iz Denali pogleda,
        # ampak fizicno so isti kot rename-skipped, zato ne stejejo kot Novo
        rename_xg_imena_v_denali = [opis.split('→ ')[1].strip() for _, opis in rename_xg_bp]
        novi_xg_bp = [c for c in novi_xg_bp if c not in rename_xg_imena_v_denali]
        rename_g_imena_v_denali = [opis.split('→ ')[1].strip() for _, opis in rename_g_bp]
        novi_g_bp = [c for c in novi_g_bp if c not in rename_g_imena_v_denali]

        if ghost_g_bp:
            print(f"    BRISI GSM ({len(ghost_g_bp)}): {ghost_g_bp}")
        if ghost_xg_bp:
            print(f"    BRISI LTE/NR ({len(ghost_xg_bp)}): {ghost_xg_bp}")

        if rename_g_bp:
            print(f"    PRESKOK (rename pending) GSM ({len(rename_g_bp)}):")
            for c, opis in rename_g_bp:
                print(f"       {c} ({opis})")
        if rename_xg_bp:
            print(f"    PRESKOK (rename pending) LTE/NR ({len(rename_xg_bp)}):")
            for c, opis in rename_xg_bp:
                print(f"       {c} ({opis})")

        if keep_g_bp or keep_xg_bp:
            print(f"    PRESKOK (--keep override): GSM={keep_g_bp}, LTE/NR={keep_xg_bp}")

        if novi_g_bp or novi_xg_bp:
            print(f"    NOVO (samo INFO — skripta NE doda; rabi Atoll SQL INSERT):")
            if novi_g_bp:
                print(f"       GSM:    {novi_g_bp}")
            if novi_xg_bp:
                print(f"       LTE/NR: {novi_xg_bp}")

        if not (ghost_g_bp or ghost_xg_bp or novi_g_bp or novi_xg_bp or rename_g_bp or rename_xg_bp):
            print(f"    OK: ujemanje")

        brisi_g_all.extend(ghost_g_bp)
        brisi_xg_all.extend(ghost_xg_bp)
        novi_g_all.extend(novi_g_bp)
        novi_xg_all.extend(novi_xg_bp)

    return brisi_g_all, brisi_xg_all, novi_g_all, novi_xg_all, skip_bps


def clear_csv_folders():
    print("\nBrišem obstoječe CSV iz Brisi/Spremeni/Novo folderjev...")
    for d in [BRISI, SPREMENI, NOVO]:
        if not os.path.isdir(d):
            print(f"  Folder ne obstaja: {d}")
            continue
        for f in os.listdir(d):
            if f.endswith('.csv'):
                os.remove(os.path.join(d, f))
                print(f"  zbrisan: {os.path.join(d, f)}")


def write_brisi_csvs(ghosts_g, ghosts_xg):
    """
    Zapiše Brisi CSV-je v formatu, ki ga prebere comp_zone.vbs.
    21_gtransmitters.csv  → TX_ID rows za izbris GSM transmiterjev
    23_xgtransmitters.csv → TX_ID rows za izbris LTE/NR transmiterjev
    25_xgcellslte.csv     → CELL_ID rows za izbris LTE celic (CELL_ID = TX_ID + "(0)")
    26_xgcells5gnr.csv    → CELL_ID rows za izbris NR celic
    Pišemo CELL_ID v oba 25 in 26 — VBS bo zbrisal samo, kjer obstaja.
    """
    print("\nPišem Brisi CSV-je...")

    if ghosts_g:
        df = pd.DataFrame({'TX_ID': ghosts_g})
        path = os.path.join(BRISI, "21_gtransmitters.csv")
        df.to_csv(path, index=False, sep=';')
        print(f"  Napisan: {path} ({len(ghosts_g)} GSM transmiterjev)")

    if ghosts_xg:
        df = pd.DataFrame({'TX_ID': ghosts_xg})
        path = os.path.join(BRISI, "23_xgtransmitters.csv")
        df.to_csv(path, index=False, sep=';')
        print(f"  Napisan: {path} ({len(ghosts_xg)} LTE/NR transmiterjev)")

        cell_ids = [c + "(0)" for c in ghosts_xg]
        for fname, label in [
            ("25_xgcellslte.csv", "LTE celice"),
            ("26_xgcells5gnr.csv", "NR celice"),
        ]:
            df = pd.DataFrame({'CELL_ID': cell_ids})
            path = os.path.join(BRISI, fname)
            df.to_csv(path, index=False, sep=';')
            print(f"  Napisan: {path} ({len(cell_ids)} {label} — brisanje kjer obstaja)")


def invoke_comp_zone_vbs():
    print(f"\nKličem {COMP_ZONE_VBS}...")
    print("(VBS naredi: Brisi → Spremeni → Novo → set computation zone. Ker imamo")
    print(" samo Brisi, le tisto bo aplicirano. Computation zone se postavi privzeto,")
    print(" ampak naslednji v0 run jo bo prilagodil za svojo BP.)")

    if not os.path.isfile(COMP_ZONE_VBS):
        print(f"NAPAKA: VBS ne obstaja: {COMP_ZONE_VBS}")
        return False

    rez = subprocess.run(
        ['cscript', '//Nologo', COMP_ZONE_VBS],
        capture_output=True, text=True, timeout=600,
    )
    print("\n--- VBS stdout (zadnjih 2000 chars) ---")
    print(rez.stdout[-2000:] if len(rez.stdout) > 2000 else rez.stdout)
    if rez.returncode != 0:
        print(f"\nVBS returncode: {rez.returncode}")
        print(f"VBS stderr: {rez.stderr}")
        return False
    print(f"\nVBS končan uspešno.")
    return True


def main():
    p = argparse.ArgumentParser(
        description="Odstrani ghost celice iz LOKALNEGA ATL doc-a (NE atoll_d96 SQL).",
    )
    p.add_argument("bps", nargs="+", help="BP imena (npr. SBOKRA SDOLEN LHOTIC)")
    p.add_argument("--apply", action="store_true",
                   help="Dejansko aplicira Brisi v ATL doc (drugace samo dry run).")
    p.add_argument("--no-confirm", action="store_true",
                   help="Preskoci confirm prompt pred apply.")
    p.add_argument("--keep", default="",
                   help="Komaseparirani substring patterni — celice z njimi se NE brisejo. "
                        "Npr. --keep \"07SS\" obdrzi vse celice z '07SS' v imenu (uporabno za rename pending).")
    args = p.parse_args()

    keep_patterns = [p.strip() for p in args.keep.split(",") if p.strip()] if args.keep else []
    if keep_patterns:
        print(f"KEEP patterni (te celice se NE brisejo): {keep_patterns}\n")

    bps = [b.upper() for b in args.bps]
    print(f"BP za diff: {bps}\n")

    brisi_g, brisi_xg, novi_g, novi_xg, skip_bps = compute_diff(bps, keep_patterns=keep_patterns)

    print("\n" + "=" * 75)
    print(f"POVZETEK")
    print("=" * 75)
    print(f"Skupno za izbris: {len(brisi_g)} GSM + {len(brisi_xg)} LTE/NR transmiterjev")
    print(f"Manjka v Atollu (samo INFO): {len(novi_g)} GSM + {len(novi_xg)} LTE/NR")
    if skip_bps:
        print(f"PRESKOCENI BP-ji (Denali prazen, safety check): {skip_bps}")
        print(f"  Te BP NIKAR ne brisi rocno — najprej preveri zakaj Denali nima podatkov.")

    if not (brisi_g or brisi_xg):
        print("\nNi ghost celic za izbris. Konec.")
        return

    if not args.apply:
        print("\nDRY RUN — nobena sprememba narejena.")
        print(f"Z `--apply` se Brisi CSV-ji zapišejo in apply-jajo na ATL doc.")
        return

    if not args.no_confirm:
        try:
            ans = input(f"\nBrisem {len(brisi_g)+len(brisi_xg)} ghost celic iz LOKALNEGA ATL doc-a? (y/N): ").strip().lower()
        except EOFError:
            ans = 'n'
        if ans != 'y':
            print("Prekinjeno.")
            return

    clear_csv_folders()
    write_brisi_csvs(brisi_g, brisi_xg)
    success = invoke_comp_zone_vbs()

    if success:
        print(f"\n{'=' * 75}")
        print(f"KONČANO")
        print(f"{'=' * 75}")
        print(f"ATL doc je očiščen ghost celic.")
        print(f"Sedaj poženi v0 pipeline normalno:")
        print(f"  py -3.10 D:\\Atoll_projects_planer01\\Skripte\\Python\\upravicenost_bazne_postaje\\upravicenost_bazne_postaje.py")
        print(f"\nOPOMBA: Žigov nightly nocoč bo verjetno sinhroniziral atoll_d96 SQL z Denali.")
        print(f"Po tem ghost-i bodo izginili iz SQL-a, in ti pre-step (Brisi) ne bo več potreben.")
    else:
        print(f"\nVBS je padel — preveri stdout zgoraj. ATL doc morda ni bil pravilno modificiran.")


if __name__ == "__main__":
    main()
