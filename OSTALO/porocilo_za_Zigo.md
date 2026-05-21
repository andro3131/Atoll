# Cascade bug v `upravicenost_bazne_postaje_v1.py` — najdba in popravek

**Datum:** 14. 5. 2026  
**Test BP:** PANKAC (substitutna lokacija za PANKAR, 24 celic v Denali: 4×GSM, 8×LTE, 8×NR)  
**Avtor analize:** Andrej (s pomočjo statičnega code-review-a + numerične validacije)

---

## Povzetek

V funkciji `izracunaj_stevilke(...)` se `tocke_df` (data set naslovov za vso Slovenijo) bere **enkrat pred** `for k in scenarij:` loop-om in znotraj loop-a se **muta** preko `tocke_df = tocke_df.merge(omejitev_tock_df, how='inner', ...)`. Posledica: vsaka naslednja iteracija dobi le presek s prejšnjo tehnologijo (GSM → LTE → NR), kar **podvrednoti LTE in NR številke** za vse naslove, ki niso GSM-pokriti, so pa LTE/NR-pokriti (tipično na podeželju, kjer ima Telekom LTE800/NR700 brez sočasne GSM900 pokritosti).

V `v0` (referenčna verzija v `preverba_upravicenost_bazne_postaje.py`) tega buga ni, ker se `tocke_df` bere **sveže znotraj** loop-a.

---

## Dokaz buga — shape progresija na PANKAC

```
--- PANKAC_GSM_[GSM].txt ---
  tocke_df.shape PRED merge = (638529, 10)   ← OK, vsa SLO
  tocke_df.shape PO  merge = (807, 10)

--- PANKAC_LTE_[LTE].txt ---
  tocke_df.shape PRED merge = (807, 10)      ← BUG! podedoval iz GSM, ne sme biti
  tocke_df.shape PO  merge = (572, 10)

--- PANKAC_NR_[5G NR].txt ---
  tocke_df.shape PRED merge = (572, 10)      ← BUG! podedoval iz LTE
  tocke_df.shape PO  merge = (532, 10)
```

Po popravku (`tocke_df` osvežen v vsaki iteraciji):

```
--- PANKAC_GSM_[GSM].txt ---  PRED = 638529   PO = 807
--- PANKAC_LTE_[LTE].txt ---  PRED = 638529   PO = 723   ← +151 lokacij
--- PANKAC_NR_[5G NR].txt ---  PRED = 638529   PO = 759   ← +227 lokacij
```

NR scenarij je v nepopravljeni verziji izgubil **227 lokacij** (532 vs 759), kar potrjuje predpostavko: LTE in NR celice imajo večji domet kot GSM in pokrivajo naslove, ki jih GSM ne.

---

## Dokaz buga — primerjava številk z v0 referenco

Test je pognan z istimi `_[GSM|LTE|5G NR].txt` Atoll exporti, ki jih je generirala produkcijska v0 pipeline za PANKAC (5. 2026).

| Stolpec | v0 LTE | v1 brez fixa | v1 s fixom | Status |
|---|---|---|---|---|
| Izboljsava_Naslovi_best | **506** | 441 (-13%) | **506** | ✓ ujema |
| Izboljsava_Prebivalci_best | 2323 | 2114 | **2323** | ✓ ujema |
| Novi_Naslovi_best_indoor | 148 | 144 | **148** | ✓ ujema |
| Izboljsava_Naslovi_best_indoor | 373 | 367 | **373** | ✓ ujema |
| Izboljsava_Naslovi_second | 712 | 564 (-21%) | **712** | ✓ ujema |
| Novi_Naslovi_second_indoor | 178 | 169 | **178** | ✓ ujema |
| ... vsi ostali ne-FWA stolpci | ... | ... | ✓ ujema | |

Za NR scenarij analogno: `Izboljsava_Naslovi_best` 490 (v0) → 428 (v1 brez fixa, -13%) → **490** (s fixom).

**Rezultat: 21 od 25 stolpcev byte-identičnih z v0** po cascade fixu. Preostale 4 razlike so v FWA stolpcih in imajo drug izvor (glej spodaj).

---

## Popravek (minimal patch)

Edit `upravicenost_bazne_postaje_v1.py`, funkcija `izracunaj_stevilke(...)`:

**Pred:**
```python
def izracunaj_stevilke(mapa = '', lokacija = '', resolucija = 25, celice = [],naredi_slike=False):
    tocke_df = beri_pop_file(tocke_pop)
    resoluc = resolucija
    tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E']%resoluc).astype(int)
    tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N']%resoluc).astype(int)
    tocke_df[['x_stot','y_stot']] = tocke_df[['x_stot','y_stot']].astype(int)
    ...
    for k in scenarij:
        lte800_df = pd.read_csv(mapa + k, sep = ';')
        ...
```

**Po:**
```python
def izracunaj_stevilke(mapa = '', lokacija = '', resolucija = 25, celice = [],naredi_slike=False):
    resoluc = resolucija
    ...
    for k in scenarij:
        tocke_df = beri_pop_file(tocke_pop)
        tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E']%resoluc).astype(int)
        tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N']%resoluc).astype(int)
        tocke_df[['x_stot','y_stot']] = tocke_df[['x_stot','y_stot']].astype(int)

        lte800_df = pd.read_csv(mapa + k, sep = ';')
        ...
```

Patchana verzija je v priponki: `upravicenost_bazne_postaje_v1_fixed.py`. Spremembe so na 2 mestih (vse ostalo nedotaknjeno) in jasno označene z `# FIX 2026-05-14 (cascade bug)` komentarji. Časovni overhead: ~zanemarljiv (3× branje populacijskega CSV-ja vs 1× — pri PANKAC pribl. +5s na izvedbo).

---

## Stranska najdba: FWA thresholdi (ne-bug, vprašanje)

V tvoji v1 verziji so `nivo_fwa` vrednosti spremenjene glede na v0:

|  | v0 | v1 |
|---|---|---|
| GSM | -10 dBm | **-30 dBm** |
| LTE | -95 dBm | **-105 dBm** |
| NR  | -95 dBm | **-105 dBm** |

To po cascade fixu povzroči **vse** preostale razlike s PANKAC primerjave:

| Stolpec | v0 LTE | v1 LTE s fixom | razlaga |
|---|---|---|---|
| Naslovi_best_FWA_potencial | 444 | **449** | ohlapnejši threshold → več kvalificira ✓ |
| Naslovi_second_FWA_redundanca | 608 | **630** | isti razlog ✓ |
| Naslovi_best_FWA_izboljsava | 7 | **0** | pri -105 je pogoj `3_ostali < -105` praktično nikdar izpolnjen → 0 |
| Naslovi_second_FWA_izboljsava | 8 | **0** | isti razlog |

**Vprašanje za potrditev:** Predpostavljam, da si thresholde znižal **namensko** (FWA modemi z zunanjo anteno so občutljivejši od mobilnih telefonov), ne pomotoma. Lahko potrdiš? Če ja, je v1 (s cascade fixom) numerično korekten. Če ne, je treba na -95/-95/-10 nazaj.

---

## Ostale najdbe iz statičnega review-a (sekundarne, ne potrjene/ovržene v PANKAC primeru)

Med initial code review-em sem zaznal še 4 razlike v1 vs v0, ki **niso vplivale na PANKAC** test, lahko pa povzročijo intermittent divergenco na drugih lokacijah:

1. **`.astype(str).str[0]` na list-koloni** (vrstica 272): po `groupby([0,1]).agg({3:'max', 2:list})` je kolona `2` seznam imen celic. `.astype(str).str[0]` vrne `'['` (prvi znak string-reprezentacije seznama), ne prvi element seznama. **Kozmetično** (kolona `2_sec` je polna `'['`), na štete ne vpliva, ker se uporabljajo bool-filtri po `3_sec` in `PRIKLJUCEK`. Vrstico nižje (281) za `lte800_dfa_second` uporabljaš `.str[0]` brez `astype(str)` — kar je pravilna varianta.

2. **`isin(celice)` vs `str.contains(lokacija)`**: v1 filtra `lte800_df1 = lte800_df1[lte800_df1[2].isin(celice)]`, v0 uporablja `str.contains(lokacija)`. Tvoja varianta je čistejša, vendar občutljiva, če `izbor_celic()` vrne nepopoln seznam (nova celica še ni v Denali ipd.). Pri PANKAC ni bilo problema, ker so vse PANKAC celice bile v Denali.

3. **Bounding-box filter** (vrstice 197-201, 225): v0 je omejil `tocke_df` in `lte800_df` na `sites_x1..x2, sites_y1..y2`. V v1 to zakomentirano. V praksi inner-merge `tocke_df.merge(omejitev_tock_df, how='inner')` to itak izvrši. Memory aspect: tvoja verzija procesira celotno Slovenijo skozi vsako iteracijo, kar je s cascade fixom **3× težje** (3× full-SLO tocke_df load). Razmisli o optional bounding-boxu, da ne ubije RAM-a pri produkcijskem batch-u.

4. **Stale kompozit**: za `Obstojec=True` v1 bere iz `G:\Pokrivanja\Arcgis\export_3794\Sestic\Kompozit\`. Če je BP imel spremembe v Atollu (azimut, moč, nova frekvenca) po zadnjem nightly buildu kompozita, dobiš stare predikcije, medtem ko bi v0 (signalsexport realtime) imel sveže. Nekontrolirano za bug-hunt, kontroliraj timestamp kompozit fajla pri spornih BP-jih.

---

## Priloge

1. **`upravicenost_bazne_postaje_v1_fixed.py`** — tvoj fajl s patchanim cascade bugom, vse ostalo identično.
2. **`test_kaskada_fix.py`** — standalone test harness (uporablja v0-jeve `_[GSM|LTE|5G NR].txt` exporte namesto kompozita, da test ne potrebuje G:\Pokrivanja\Arcgis pristopa). Zaženeš z `py -3.10 test_kaskada_fix.py <LOK>` (s fixom) ali `... --no-fix` (brez). Output: `<LOK>_analiza_v1kaskada[_nofix].xlsx`.

---

## Lep pozdrav,
Andrej
