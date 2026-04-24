# -*- coding: utf-8 -*-
"""
Fail-fast preverba, ce vse pricakovane poti obstajajo na D:\ po migraciji
iz G:\Avtomatika\ -> D:\Atoll_projects_planer01\Avtomatika\.

Uporaba:
    py -3.10 preveri_poti.py

Ne piše nič, samo izpiše. Pokaze katere mape / datoteke manjkajo.
Ce pride do kakrsnegakoli MANJKA, skripta vrne exit code 1 -
primerno za wrapper batch ki prekine preden pozene glavni flow.
"""
import os
import sys

BASE = r"D:\Atoll_projects_planer01\Avtomatika"

# Mape, ki jih Python in VBS skripte pricakujejo. Python pri `open(..,'w')`
# NE ustvari parent mape - crashne. VBS z "On Error Resume Next" silent-fail,
# kar je bil razlog za vse pretekle glavobole.
PRICAKOVANE_MAPE = [
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Novo",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Spremeni",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Brisi",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Export_planirane_celice",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export\celice_ascii_atoll",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export\celice_shp_atoll",
    r"D:\Atoll_projects_planer01\Avtomatika\log",
    # Drugi D:\ resursi
    r"D:\Atoll_projects_planer01\Skripte\VBasic",
    r"D:\Atoll_projects_planer01\Skripte\Python",
    r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje",
    r"D:\Atoll_projects_planer01\Atoll_dokumenti\Dokument_exporti\SharedPathlossData",
]

# Datoteke, ki jih VBS OpenTextFile(..,1) rabi za branje - ce manjkajo,
# VBS silent-fail in ATL ostane nefilter-iran.
# Te datoteke Python flow tekom run-a ZAPISE. Pri praznem repoju
# morajo obstajati (tudi prazne), da prvi VBS klic ne pade.
PRICAKOVANE_DATOTEKE = [
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_sites.txt",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_trans.txt",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\trans_teh.txt",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\trans_teh_filter.txt",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\zone.txt",
    r"D:\Atoll_projects_planer01\Avtomatika\Eksport\export_zacasni_2.txt",
    r"D:\Atoll_projects_planer01\Atoll_exporti_3794_3_5_1.ATL",
    r"D:\Atoll_projects_planer01\Export_coverage_krmilna_tabela.xlsx",
]

manjka = []

print("=" * 70)
print("Preverjanje map...")
print("=" * 70)
for m in PRICAKOVANE_MAPE:
    if os.path.isdir(m):
        print(f"  OK   {m}")
    else:
        print(f"  !!!  {m}  <-- MANJKA")
        manjka.append(("mapa", m))

print()
print("=" * 70)
print("Preverjanje datotek...")
print("=" * 70)
for d in PRICAKOVANE_DATOTEKE:
    if os.path.isfile(d):
        print(f"  OK   {d}")
    else:
        print(f"  !!!  {d}  <-- MANJKA")
        manjka.append(("datoteka", d))

print()
print("=" * 70)
if not manjka:
    print("SVE OK - vse mape in datoteke obstajajo.")
    sys.exit(0)

print(f"MANJKA {len(manjka)} poti - flow bo padel (ali silent-failal).")
print()
print("Za hitro ustvarit manjkajoce poti:")
for tip, pot in manjka:
    if tip == "mapa":
        print(f'  mkdir "{pot}"')
    else:
        # Prazno datoteko ustvarimo z type nul > pot ali echo. > pot
        print(f'  type nul > "{pot}"')
sys.exit(1)
