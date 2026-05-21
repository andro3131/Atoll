# OSTALO

Arhiv neaktivnih fajlov — ostanejo dosegljivi za referenco / zgodovino, niso pa del trenutne produkcije.

## Vsebina

### Žigov upstream (predhodne verzije, danes superseded)
- `upravicenost_bazne_postaje_v1.py` — Žigov v1 pre-cascade-fix (ima bug). `upravicenost_bazne_postaje_v1_fixed.py` v root je verzija z mojim fix-om, ki je osnova za produkcijski `upravicenost_bazne_postaje_v1_planer01.py`.
- `csv_atoll_tabele.py` — Žigova workspace verzija z G:\ poti. Production verzija (z D:\ migracijo) je na user-jevi planer01 mašini. Pomembno: na planer01 se v1_planer01 in posodobi_atl_iz_baze importajo iz D:\ preko `sys.path`, ne iz workspace.

### Dev artefakti (delo opravljeno, ni več potrebno)
- `analiza_iz_kompozita.py` — moj standalone Obstojec=True path (untested). Funkcionalnost je integrirana v `upravicenost_bazne_postaje_v1_planer01.py` Obstojec=True branch.
- `test_kaskada_fix.py` — harness za validacijo cascade fix-a (2026-05-14, PANKAC). Fix je validiran in v produkciji.
- `test_narisi_pokrivanje.py` — hardcoded PANKAC dev iteracije; production je `narisi_pokrivanje.py`.

### Backup pristopi (nekoč potencialno koristni)
- `prefetch_osm_slovenia.py` — backup za SSL probleme z OSM tile fetch. Trenutno irelevantno (corporate maps iz GIS oddelka uporablja Žiga; user-jev planer01 ima pip-system-certs nameščen).

### Stari baseline / report
- `Export_coverage_krmilna_tabela.xlsx` — April 2026 verzija. User uporablja sveže verzije na D:\.
- `porocilo_za_Zigo.md` — star report (14.5.2026) za Žigo.

## Ali kaj pogrešam?

Če pri delu opaziš, da nekaj iz OSTALO/ rabiš, premakni nazaj v root:
```cmd
git mv OSTALO/<fajl> .
```
