# -*- coding: utf-8 -*-
"""
naredi_kompozit.py — generira nacionalni per-band Atoll coverage kompozit.

Wrappa `export_script_3794_reporting.export_pokrivanj()` s pre-checki, plan-povzetkom,
confirm prompt-om in koncnim porocilom o producirjanih fajlih.

Output: `<BAND>_1_w.txt` (npr. LTE_800_1_w.txt) v ciljni mapi.
        Format = standardni Atoll signalsexport ASCII (top-6 strezniki per piksel).
        Direktno berljiv s strani Zigovega `kompozit_od_zacetka()` in v1 pipeline-a.

Bandi: vsi vrstice v Export_coverage_krmilna_tabela.xlsx, RAZEN NBIOT_*+UMTS_2100
(ki rabijo ATL doc na G:\\, kar nimas).

Predviden cas: ~10-30 min na band x ~12 bandov = 2-6 h. Pusti cez noc.

NSA correction (NR_700 nad LTE anchor): NI vkljucen v tej skripti.
Output je raw signalsexport, kompatibilen z dosedanjo v0 produkcijo na planer01.

Uporaba:
    py -3.10 naredi_kompozit.py                                # vsi bandi
    py -3.10 naredi_kompozit.py --bands LTE_800                # samo en band (test)
    py -3.10 naredi_kompozit.py --bands GSM_900,LTE_800,NR_700 # subset
    py -3.10 naredi_kompozit.py --no-confirm                   # preskoci y/n prompt
"""

import argparse
import os
import sys
import subprocess
import time

import pandas as pd

sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\atoll_export")
import export_script_3794_reporting as esr

OUTPUT_MAPA = r"D:\Atoll_projects_planer01\Pokrivanja\Kompozit\\"
NBIOT_UMTS_IZLOCENI = ['NBIOT_800', 'NBIOT_900', 'NBIOT_1800', 'UMTS_2100']
PATHLOSS_FOLDER = r"D:\Atoll_projects_planer01\Atoll_dokumenti\Dokument_exporti\SharedPathlossData"


def is_process_running(name):
    try:
        rez = subprocess.run(
            ['tasklist', '/FI', f'IMAGENAME eq {name}'],
            capture_output=True, text=True, timeout=10,
        )
        return name.lower() in rez.stdout.lower()
    except Exception as e:
        print(f"  OPOZORILO: tasklist preverba ni uspela ({e}), nadaljujem...")
        return False


def signalsexport_path():
    sig = esr.ukaz.strip()
    if not sig.lower().endswith(".exe"):
        sig += ".exe"
    return sig


def pre_checks():
    print("=" * 60)
    print("PRE-CHECKS")
    print("=" * 60)

    if is_process_running("Atoll.exe"):
        raise RuntimeError(
            "Atoll.exe je se zagnan. Zapri ga (signalsexport rabi exclusive access do ATL doc-a)."
        )
    print("  OK: Atoll.exe ni zagnan")

    if is_process_running("signalsexport.exe"):
        raise RuntimeError(
            "signalsexport.exe se tece (verjetno orphan iz prejsnjega runa). "
            "Ubij ga preko Task Manager-ja, potem znova zazeni."
        )
    print("  OK: signalsexport.exe ni zagnan")

    if not os.path.isfile(esr.at_dok_3794):
        raise RuntimeError(f"ATL doc ne obstaja: {esr.at_dok_3794}")
    print(f"  OK: ATL doc = {esr.at_dok_3794}")

    sig_exe = signalsexport_path()
    if not os.path.isfile(sig_exe):
        raise RuntimeError(f"signalsexport.exe ne obstaja: {sig_exe}")
    print(f"  OK: signalsexport = {sig_exe}")

    if not os.path.isfile(esr.mapa_krmilna_tabela):
        raise RuntimeError(f"krm_tab Excel ne obstaja: {esr.mapa_krmilna_tabela}")
    print(f"  OK: krm_tab = {esr.mapa_krmilna_tabela}")

    odlozisce_2_dir = os.path.dirname(esr.odlozisce_2)
    if not os.path.isdir(odlozisce_2_dir):
        raise RuntimeError(
            f"Mapa za filter file ne obstaja: {odlozisce_2_dir} (pricakovan {esr.odlozisce_2})"
        )
    print(f"  OK: filter-file mapa obstaja ({esr.odlozisce_2})")

    if not os.path.isdir(PATHLOSS_FOLDER):
        print(f"  OPOZORILO: pathloss folder ne obstaja: {PATHLOSS_FOLDER}")
        print(f"            Brez pathloss matric bo signalsexport proizvedel prazne fajle.")
    else:
        nfiles = len(os.listdir(PATHLOSS_FOLDER))
        print(f"  OK: pathloss folder ({nfiles} fajlov v {PATHLOSS_FOLDER})")

    os.makedirs(OUTPUT_MAPA, exist_ok=True)
    print(f"  OK: output mapa = {OUTPUT_MAPA}")
    print()


def planned_bands(only_bands=None):
    df = pd.read_excel(esr.mapa_krmilna_tabela)
    df["Export_da_ne"] = True
    df.loc[df["ime_fajla"].isin(NBIOT_UMTS_IZLOCENI), "Export_da_ne"] = False
    df = df[df["Export_da_ne"] == True]
    if only_bands:
        available = df["ime_fajla"].tolist()
        missing = [b for b in only_bands if b not in available]
        if missing:
            raise ValueError(
                f"Bandi {missing} niso v krm_tab. Razpolozljivi: {available}"
            )
        df = df[df["ime_fajla"].isin(only_bands)]
    return df["ime_fajla"].tolist()


def preveri_ini_files(bandi):
    df = pd.read_excel(esr.mapa_krmilna_tabela)
    df = df[df["ime_fajla"].isin(bandi)]
    ini_files = df["ini_file_3794_100_slovar"].unique().tolist()
    manjkajoci = []
    for ini in ini_files:
        full = esr.mapa_ini_file + ini
        if not os.path.isfile(full):
            manjkajoci.append(full)
    if manjkajoci:
        print(f"  OPOZORILO: manjkajo ini files (signalsexport bo verjetno padel za pripadajoce bande):")
        for m in manjkajoci:
            print(f"            {m}")


def produciraj_kompozite(only_bands=None):
    """
    Klice esr.export_pokrivanj_1() (NE _pokrivanj() brez _1!) z ini_file_set='Ziga',
    ker to preklopi na ini_file_3794_slovar (= 25m resolucija) namesto
    ini_file_3794_100_slovar (= 100m). v0 produkcija v upravicenost_bazne_postaje.py:508
    uporablja isti pristop. 25m je potreben za pravilen tocke_df merge v izracunaj_stevilke.

    Ce only_bands podan, zacasno predela krm_tab Excel na podset (rebind
    esr.mapa_krmilna_tabela na temp pot, finally restore).
    """
    kwargs = dict(
        po_celicah=False,
        odlozisce_pokrivanja=OUTPUT_MAPA,
        krm_tab_set=False,    # → resetira Export_da_ne (kot export_pokrivanj brez _1)
        ime_lokacije='',      # → no BP-prefix v output filename, rename na _1_w.txt
        ime_fajla='',         # → uporabi krm_tab "ime_fajla" stolpec (npr. "LTE_800")
        ini_file_set='Ziga',  # → 25m ini file (ne 100m kot pri export_pokrivanj brez _1)
    )

    if only_bands is None:
        esr.export_pokrivanj_1(**kwargs)
        return

    df_full = pd.read_excel(esr.mapa_krmilna_tabela)
    df_subset = df_full[df_full["ime_fajla"].isin(only_bands)]
    temp_excel = os.path.join(
        os.path.dirname(esr.mapa_krmilna_tabela),
        "Export_coverage_krmilna_tabela_TEMP_kompozit.xlsx",
    )
    df_subset.to_excel(temp_excel, index=False)
    original_path = esr.mapa_krmilna_tabela
    try:
        esr.mapa_krmilna_tabela = temp_excel
        esr.export_pokrivanj_1(**kwargs)
    finally:
        esr.mapa_krmilna_tabela = original_path
        if os.path.isfile(temp_excel):
            os.remove(temp_excel)


def report_results(planned):
    print("\n" + "=" * 60)
    print("REZULTAT")
    print("=" * 60)
    print(f"Output mapa: {OUTPUT_MAPA}")

    files = os.listdir(OUTPUT_MAPA) if os.path.isdir(OUTPUT_MAPA) else []
    produced_w = sorted([f for f in files if f.endswith("_1_w.txt")])
    print(f"Producirjanih _1_w.txt fajlov: {len(produced_w)}\n")

    for f in produced_w:
        full = OUTPUT_MAPA + f
        size_mb = os.path.getsize(full) / (1024 * 1024)
        print(f"  {f}  ({size_mb:.1f} MB)")

    expected = [b + "_1_w.txt" for b in planned]
    missing = [e for e in expected if e not in produced_w]
    if missing:
        print(f"\nMANJKAJOCI fajli (band v planu ampak signalsexport ni proizvedel):")
        for m in missing:
            print(f"  {m}")
        print(
            "\n  Mozni vzroki:\n"
            "   - ATL doc nima predikcije za ta band (preveri Atoll Predictions tab)\n"
            "   - pathloss matrice za celice tega banda manjkajo\n"
            "   - band nima nobenih aktivnih celic v Atollu\n"
            "   - signalsexport je crknil (poglej console output zgoraj)"
        )

    leftover = sorted([f for f in files if "[" in f and f.endswith(".txt")])
    if leftover:
        print(f"\nZAOSTALI _[BAND].txt fajli (rename na _1_w.txt ni uspel):")
        for f in leftover:
            print(f"  {f}")
        print("  Lahko jih ros rocno preimenujes ali ponovno pozenes skripto.")


def main():
    p = argparse.ArgumentParser(
        description="Generira nacionalni Atoll coverage kompozit per band.",
    )
    p.add_argument(
        "--bands", default=None,
        help="Komaseparirani bandi (npr. GSM_900,LTE_800). Default: vsi razen NBIOT/UMTS.",
    )
    p.add_argument(
        "--no-confirm", action="store_true",
        help="Preskoci y/n confirm prompt.",
    )
    args = p.parse_args()

    only_bands = None
    if args.bands:
        only_bands = [b.strip() for b in args.bands.split(",") if b.strip()]

    pre_checks()

    bandi = planned_bands(only_bands)
    if not bandi:
        print("Noben band ni v planu. Konec.")
        return

    print("PLAN")
    print("-" * 60)
    print(f"Bandi za zagon ({len(bandi)}):")
    for b in bandi:
        print(f"  - {b}")
    preveri_ini_files(bandi)
    # Pri 25m resoluciji (ini_file_set='Ziga') je per-band cas ~30-60 min,
    # ne 10-20 min kot pri 100m. LTE_800 test pri 100m bil 13 min, pri 25m
    # pricakovano 40-60 min.
    estimated_min = len(bandi) * 45
    print(f"\nPredviden cas: ~{estimated_min} min (~{estimated_min/60:.1f} h) pri 25m resoluciji")
    print(f"Predvidena velikost outputa: ~700 MB - 1.5 GB per band (12 bandov = 8-15 GB)")
    print(f"Output: {OUTPUT_MAPA}")
    print(f"NSA correction (NR_700 nad LTE anchor): NI vkljucen v tej skripti.")
    print("Med izvajanjem ne odpiraj Atoll-a ali drugih signalsexport instanc.")
    print()

    if not args.no_confirm:
        try:
            ans = input("Zazenem? (y/N): ").strip().lower()
        except EOFError:
            ans = 'n'
        if ans != 'y':
            print("Prekinjeno.")
            return

    print()
    print("=" * 60)
    print(f"START: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    t0 = time.time()
    try:
        produciraj_kompozite(only_bands)
    except KeyboardInterrupt:
        print("\nPREKINJENO s strani uporabnika (Ctrl+C).")
    finally:
        elapsed_min = (time.time() - t0) / 60
        print(f"\nCas izvajanja: {elapsed_min:.1f} min ({elapsed_min/60:.2f} h)")
        report_results(bandi)


if __name__ == "__main__":
    main()
