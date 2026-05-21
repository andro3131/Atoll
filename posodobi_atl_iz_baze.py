# -*- coding: utf-8 -*-
"""
Ad-hoc posodobitev .atl dokumenta iz planerske SQL baze (Denali).

Uporaba (na planer01):
  py -3.10 D:\\Atoll_projects_planer01\\Skripte\\Python\\atoll_import_at\\posodobi_atl_iz_baze.py

Kdaj zagnati:
  - Ko se v Denali (planerska SQL baza) zgodi sprememba, ki jo zelis takoj v .atl
    ne da bi cakal na Zigov nocni avtomatski cikel.

Kaj naredi (4 koraki):
  1. csv_atoll_tabele.main()     - bere Denali SQL, gradi CSV-je
                                   (Spremeni\\, Novo\\, Brisi\\) v Avtomatika\\Eksport\\...
  2. posodobi_atoll_3794.vbs     - VBS odpre .atl, aplicira CSV-je, shrani .atl
  3. arhiv_sprememb.main()       - belezi spremembe v arhiv log
  4. krmilna_tabela1.main()      - osvezi Excel krmilno tabelo za tech filtre

Preskoceno glede na Zigov glavno.py:
  - ENM xml download (parsanje se dela na Ark strezniku)
  - Pathloss sync (Zigov dnevni script ze sinhronizira na planer01)
  - Export Atoll pokrivanj (export_script_3794)
  - Kompozit
  - Coverage reporting (1./15. v mesecu)
  - Mail (drugace bi sel iz Zigovega naslova)

Pre-condition checks pred zagonom:
  - Atoll.exe NE sme teci (drugace VBS ne more odpreti .atl)
  - Excel kontrolne tabele zaprt (krmilna_tabela1 jih piše)
"""

import os
import sys
import subprocess
import time
import traceback

# Modulim Žigovega atoll_import_at - dodaj v path, da skripta dela tudi
# ce je drugje na disku.
ATOLL_IMPORT_AT = r"D:\Atoll_projects_planer01\Skripte\Python\atoll_import_at"
if ATOLL_IMPORT_AT not in sys.path:
    sys.path.append(ATOLL_IMPORT_AT)

import csv_atoll_tabele
import arhiv_sprememb
import krmilna_tabela1


# ============= TEST_MODE =============
# True  = samo korak 1 (csv_atoll_tabele.main()) - VARNO, samo gradi CSV-je
#         v Avtomatika\Eksport\... mapah. Ne dotakne se .atl ne atoll_d96 SQL.
#         Po test runu pojdi pogledat Brisi\, Spremeni\, Novo\ mape - kaj bi sla v .atl.
# False = polni flow (csv -> VBS -> arhiv -> krmilna). VBS spremeni .atl in mozno atoll_d96 SQL.
TEST_MODE = True


# ============= Poti (planer01) =============
LOG_FAJL = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\fajl.txt"
LOG_ERR = r"D:\Atoll_projects_planer01\Avtomatika\log\Atoll_import_vbs_log.txt"
VBS_POSODOBI = r"D:\Atoll_projects_planer01\Skripte\VBasic\posodobi_atoll_3794_planer01.vbs"


def loguj(msg):
    """Vzporedno na konzolo in v fajl.txt log."""
    print(msg)
    try:
        with open(LOG_FAJL, "a", encoding="utf-8") as f:
            f.write(time.asctime() + "  " + msg + "\n")
    except Exception:
        pass  # ce log fajl ne dela, nadaljuj


def loguj_napako(faza, sporocilo):
    """Zapise v error log v istem formatu kot Zigov glavno.py."""
    try:
        with open(LOG_ERR, "a", encoding="utf-8") as f:
            f.write(time.asctime() + "\t" + faza + "\t" + sporocilo + "\n")
    except Exception:
        pass


def main():
    loguj("=" * 60)
    loguj("POSODOBI .atl IZ PLANERSKE BAZE - zacetek")
    loguj("=" * 60)

    if TEST_MODE:
        loguj("!!! TEST_MODE = True - tece SAMO korak 1 (csv_atoll_tabele). VBS NE bo poklican. !!!")

    # ---------- 1. csv_atoll_tabele - branje Denali, gradnja CSV ----------
    loguj("[1/4] csv_atoll_tabele.main() - branje Denali SQL + gradnja CSV")
    try:
        csv_atoll_tabele.main()
        loguj("[1/4] OK")
    except Exception as e:
        loguj("[1/4] NAPAKA: " + repr(e))
        loguj_napako("csv_atoll_tabele", traceback.format_exc())
        loguj("Prekinjam - brez CSV-jev nima smisla nadaljevati.")
        sys.exit(1)

    if TEST_MODE:
        loguj("=" * 60)
        loguj("TEST_MODE konec. CSV-ji so v Avtomatika\\Eksport\\Planirane_celice\\...")
        loguj("Preglej Brisi\\, Spremeni\\, Novo\\ mape preden tece full flow.")
        loguj("Za polni run nastavi TEST_MODE = False na vrhu skripte.")
        loguj("=" * 60)
        sys.exit(0)

    # ---------- 2. VBS - aplicira CSV v .atl ----------
    loguj("[2/4] posodobi_atoll_3794.vbs - aplikacija CSV v .atl")
    if not os.path.exists(VBS_POSODOBI):
        loguj("[2/4] NAPAKA: VBS ne obstaja: " + VBS_POSODOBI)
        loguj_napako("VBS_check", "missing: " + VBS_POSODOBI)
        sys.exit(1)
    try:
        result = subprocess.run(
            ["cscript", VBS_POSODOBI],
            capture_output=True,
            text=True,
        )
        if result.stderr.strip():
            loguj("[2/4] VBS stderr: " + result.stderr.strip())
            loguj_napako("posodobi_atoll_3794.vbs", result.stderr)
        if result.stdout.strip():
            loguj("[2/4] VBS stdout: " + result.stdout.strip()[:500])
        loguj("[2/4] OK (returncode={})".format(result.returncode))
    except Exception as e:
        loguj("[2/4] NAPAKA: " + repr(e))
        loguj_napako("VBS_run", traceback.format_exc())
        sys.exit(1)

    # ---------- 3. arhiv_sprememb - belezenje (non-critical) ----------
    loguj("[3/4] arhiv_sprememb.main() - belezenje sprememb v arhiv")
    try:
        arhiv_sprememb.main()
        loguj("[3/4] OK")
    except Exception as e:
        loguj("[3/4] OPOZORILO (non-critical): " + repr(e))
        loguj_napako("arhiv_sprememb", traceback.format_exc())
        # nadaljujemo - arhiv napaka ne ovira osnove

    # ---------- 4. krmilna_tabela1 - osvezitev Excel-a (non-critical) ----------
    loguj("[4/4] krmilna_tabela1.main() - osvezitev krmilne tabele")
    try:
        krmilna_tabela1.main()
        loguj("[4/4] OK")
    except Exception as e:
        loguj("[4/4] OPOZORILO (non-critical): " + repr(e))
        loguj_napako("krmilna_tabela", traceback.format_exc())
        # nadaljujemo

    loguj("=" * 60)
    loguj("KONEC - .atl posodobljen iz planerske baze")
    loguj("=" * 60)


if __name__ == "__main__":
    main()
