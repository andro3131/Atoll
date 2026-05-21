# -*- coding: utf-8 -*-
"""
analiza_iz_kompozita.py — v1-style upravicenost analiza za OPERATIVNO BP
                          z uporabo lokalnega nacionalnega kompozita (D:\\Pokrivanja\\Kompozit\\).

To je simplified Obstojec=True implementacija — bere kompozit, filtrira na BP cells,
agregira per-tech (5 LTE band-ov → en LTE top-6, podobno za NR + GSM), kliče
cascade-fixed `izracunaj_stevilke` iz test_kaskada_fix.py.

PREJ Obstojec=False (planirana BP) NI podprt — to bi rabilo Atoll driving (Faza 3
polna adaptacija).

Uporaba:
    py -3.10 analiza_iz_kompozita.py PANKAR
    py -3.10 analiza_iz_kompozita.py PANKAR --no-fix       # za demo cascade buga
    py -3.10 analiza_iz_kompozita.py PANKAR --celice "P1,P2,..."  # ročni cell list
"""

import argparse
import os
import sys
import time

import pandas as pd
import numpy as np

sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\gis_zadeve")
sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\upravicenost_bazne_postaje")
sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\atoll_export")

import naredi_shp_za_112
import upravicenost_bp_atoll_datafill as udf
import warnings
warnings.simplefilter("ignore")


KOMPOZIT_MAPA = r"D:\Atoll_projects_planer01\Pokrivanja\Kompozit\\"
TOCKE_POP = r"G:\Geo podatki\Naslovi_optika_baker_6_2_2024\\CRPE_Preb_Optika_Baker_D96_predelano.csv"
NIVOJI = list(range(-70, -126, -1))
RESOLUCIJA = 25  # m

# Band file → tech mapping (file ime brez "_1_w.txt")
BAND_TO_TECH = {
    'GSM_900': 'GSM', 'GSM_1800': 'GSM',
    'LTE_700': 'LTE', 'LTE_800': 'LTE', 'LTE_900': 'LTE',
    'LTE_1800': 'LTE', 'LTE_2100': 'LTE', 'LTE_2600': 'LTE',
    'NR_700': 'NR', 'NR_1500': 'NR', 'NR_2600': 'NR', 'NR_3500': 'NR',
}


# ---------- Vmesne funkcije ----------

def get_bp_cells(bp):
    """Pridobi seznam BP cells iz Denali."""
    print(f"  Pridobivam celice za {bp} iz Denali...")
    df = udf.izbor_celic(seznam_lokacij=[bp], pisi_v_fajl=False)
    cells = df['celica'].drop_duplicates().tolist()
    return cells


def filter_kompozit_band(band_file, cells):
    """Preberi kompozit band file in filtriraj rows kjer je vsaj en top-6 server v cells."""
    full_path = os.path.join(KOMPOZIT_MAPA, band_file)
    if not os.path.isfile(full_path):
        print(f"    NI fajla: {full_path}")
        return None
    print(f"    Bere {band_file}...", end='', flush=True)
    t0 = time.time()
    df = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(full_path, n=6, vsebuje=[], header_list=False)
    df = df.replace('', np.nan)
    df[[0, 1]] = df[[0, 1]].astype(int)
    df[[3, 5, 7, 9, 11, 13]] = df[[3, 5, 7, 9, 11, 13]].astype(float)
    print(f" {len(df)} vrstic ({time.time()-t0:.1f}s).", end=' ')

    mask = df[2].isin(cells)
    for col in [4, 6, 8, 10, 12]:
        mask |= df[col].isin(cells)
    rez = df[mask].copy()
    print(f"Filter: {len(rez)} relevantnih.")
    return rez


def aggregate_bands_to_tech(band_dfs):
    """
    Zdruzi vec per-band DFjev v en per-tech top-6 per (x, y).
    Vsak input: 14 stolpcev (0..13) Atoll top-6 format.
    Output: 14 stolpcev top-6 across all input bands.
    """
    if not band_dfs:
        return pd.DataFrame(columns=list(range(14)))

    # Long format: vsak rank → ena vrstica (x, y, server, signal)
    long_records = []
    for df in band_dfs:
        if len(df) == 0:
            continue
        for rank in range(6):
            srv_col = 2 + rank * 2
            sig_col = 3 + rank * 2
            sub = df[[0, 1, srv_col, sig_col]].copy()
            sub.columns = ['x', 'y', 'server', 'signal']
            sub = sub.dropna(subset=['server'])
            long_records.append(sub)

    if not long_records:
        return pd.DataFrame(columns=list(range(14)))

    long_df = pd.concat(long_records, ignore_index=True)
    long_df['signal'] = pd.to_numeric(long_df['signal'], errors='coerce')
    long_df = long_df.dropna(subset=['signal'])

    # Top-6 per (x, y) by signal desc
    long_df = long_df.sort_values(['x', 'y', 'signal'], ascending=[True, True, False])
    long_df['rank'] = long_df.groupby(['x', 'y']).cumcount()
    long_df = long_df[long_df['rank'] < 6]

    # Pivot back to wide
    pivoted_srv = long_df.pivot(index=['x', 'y'], columns='rank', values='server')
    pivoted_sig = long_df.pivot(index=['x', 'y'], columns='rank', values='signal')

    # Stolpci: 2 + rank*2 za server, 3 + rank*2 za signal
    pivoted_srv.columns = [2 + r * 2 for r in pivoted_srv.columns]
    pivoted_sig.columns = [3 + r * 2 for r in pivoted_sig.columns]

    result = pd.concat([pivoted_srv, pivoted_sig], axis=1).reset_index()
    result.columns = ['x', 'y'] + list(result.columns[2:])
    result.rename(columns={'x': 0, 'y': 1}, inplace=True)

    # Zagotovi vse stolpce 0..13
    for col in range(14):
        if col not in result.columns:
            result[col] = np.nan
    result = result[list(range(14))]

    return result


# ---------- Cascade-fixed izracunaj_stevilke (iz test_kaskada_fix.py) ----------

def beri_pop_file(polna_pot):
    tocke_df = pd.read_csv(polna_pot, sep=";")
    tocke_df = tocke_df[['E', 'N', 'HS_TID', 'HS_MID', 'PREB_STAL', 'PREB_ZAC', 'NASLOV', 'PRIKLJUCEK']]
    tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
    tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
    if tocke_df['E'].dtypes == float:
        pass
    else:
        tocke_df['E'] = tocke_df['E'].str.replace(",", ".").astype(float)
        tocke_df['N'] = tocke_df['N'].str.replace(",", ".").astype(float)
    tocke_df.dropna(inplace=True)
    return tocke_df


def pripravi_tocke_df(resoluc):
    tocke_df = beri_pop_file(TOCKE_POP)
    tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E'] % resoluc).astype(int)
    tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N'] % resoluc).astype(int)
    tocke_df[['x_stot', 'y_stot']] = tocke_df[['x_stot', 'y_stot']].astype(int)
    return tocke_df


def izracunaj_stevilke_iz_dfs(tech_dfs, celice, lokacija, mapa, fix_kaskada=True, resolucija=25):
    """
    tech_dfs: dict {'GSM': df_gsm, 'LTE': df_lte, 'NR': df_nr}
              vsak DF z 14 stolpci (0..13), top-6 servers per (x, y).
    celice: list of BP cell names (uporabljen za isin filter v lte800_df1)
    lokacija: BP ime
    mapa: output mapa za Excel
    fix_kaskada: True = sveži tocke_df per iteracija (cascade fix)
    """
    resoluc = resolucija

    scenarij = []  # list of (tech_name, df)
    for teh in ['GSM', 'LTE', 'NR']:
        if teh in tech_dfs and len(tech_dfs[teh]) > 0:
            scenarij.append((teh, tech_dfs[teh]))

    if not scenarij:
        print("Nobenega scenarija ni za izračun. Konec.")
        return None

    print(f"\nScenariji za izračun: {[s[0] for s in scenarij]}")

    # Brez fix-a: tocke_df enkrat pred loop
    if not fix_kaskada:
        tocke_df = pripravi_tocke_df(resoluc)

    temp_a = pd.DataFrame()
    stevec = 0

    for teh, lte800_df in scenarij:
        if fix_kaskada:
            tocke_df = pripravi_tocke_df(resoluc)

        print(f"\n--- {teh} ---")
        print(f"  tocke_df.shape PRED merge = {tocke_df.shape}")

        # Reuse v1 logic
        if teh == 'GSM':
            nivo_indoor = -85
            nivo_outdoor = -96
            nivo_fwa = -30
        elif teh == 'LTE':
            nivo_indoor = -85
            nivo_outdoor = -108
            nivo_fwa = -105
        elif teh == 'NR':
            nivo_indoor = -95
            nivo_outdoor = -108
            nivo_fwa = -105

        lte800_df1 = lte800_df[[0, 1, 2, 3]]
        lte800_df1 = lte800_df1[lte800_df1[2].isin(celice)]
        lte800_df1_second = lte800_df[[0, 1, 4, 5]].loc[
            lte800_df1[lte800_df1[2].isin(celice)].index
        ].rename(columns={4: 2, 5: 3}).dropna()
        lte800_df1_second[3] = lte800_df1_second[3].astype(float)
        lte800_df1_second_a = lte800_df[[0, 1, 6, 7]].loc[
            lte800_df1_second[lte800_df1_second[2].isin(celice)].index
        ].rename(columns={6: 2, 7: 3}).dropna()
        lte800_df1_second = lte800_df1_second[~lte800_df1_second[2].isin(celice)]
        lte800_df1_second = pd.concat([lte800_df1_second, lte800_df1_second_a])

        lte800_df2 = lte800_df[[0, 1, 4, 5]].rename(columns={4: 2, 5: 3}).dropna()
        lte800_df2 = lte800_df2[lte800_df2[2].isin(celice)]
        lte800_df2_second = lte800_df[[0, 1, 6, 7]].loc[
            lte800_df2[lte800_df2[2].isin(celice)].index
        ].rename(columns={6: 2, 7: 3}).dropna()
        lte800_df2_second[3] = lte800_df2_second[3].astype(float)
        lte800_df2_second_a = lte800_df[[0, 1, 8, 9]].loc[
            lte800_df2_second[lte800_df2_second[2].isin(celice)].index
        ].rename(columns={8: 2, 9: 3}).dropna()
        lte800_df2_second = lte800_df2_second[~lte800_df2_second[2].isin(celice)]
        lte800_df2_second = pd.concat([lte800_df2_second, lte800_df2_second_a])

        lte800_df_sec = pd.concat([lte800_df1, lte800_df2])
        lte800_df_second = pd.concat([lte800_df1_second, lte800_df2_second])

        lte800_df_sec = lte800_df_sec.dropna()
        lte800_df_sec = lte800_df_sec[lte800_df_sec[2].isin(celice)]
        lte800_df_sec[3] = lte800_df_sec[3].astype(float)
        lte800_dfa_sec = lte800_df_sec.groupby([0, 1]).agg({3: 'max', 2: list}).reset_index()
        lte800_dfa_sec[6] = lte800_dfa_sec[2].astype(str).str[0]
        lte800_dfa_sec.drop(columns=2, inplace=True)
        lte800_dfa_sec.rename(columns={6: 2}, inplace=True)
        lte800_dfa_sec = lte800_dfa_sec[[0, 1, 2, 3]]

        lte800_df_second = lte800_df_second.dropna()
        lte800_df_second[3] = lte800_df_second[3].astype(float)
        lte800_dfa_second = lte800_df_second.groupby([0, 1]).agg({3: 'max', 2: list}).reset_index()
        lte800_dfa_second[6] = lte800_dfa_second[2].str[0]
        lte800_dfa_second.drop(columns=2, inplace=True)
        lte800_dfa_second.rename(columns={6: 2}, inplace=True)
        lte800_dfa_second = lte800_dfa_second[[0, 1, 2, 3]]

        omejitev_tock_df = pd.concat([
            lte800_df1[[0, 1]], lte800_df1_second[[0, 1]],
            lte800_dfa_sec[[0, 1]], lte800_dfa_second[[0, 1]],
        ]).drop_duplicates()

        tocke_df = tocke_df.merge(
            omejitev_tock_df, how='inner', left_on=['x_stot', 'y_stot'], right_on=[0, 1]
        )
        tocke_df.drop(columns=[0, 1], inplace=True)
        print(f"  tocke_df.shape PO  merge = {tocke_df.shape}  (teh={teh}, fwa={nivo_fwa})")

        presek = tocke_df.merge(lte800_df1, how='left', left_on=['x_stot', 'y_stot'], right_on=[0, 1])
        presek.drop(columns=[0, 1], inplace=True)
        presek.rename(columns={2: '2_prim', 3: '3_prim'}, inplace=True)
        presek = presek.merge(lte800_df1_second, how='left', left_on=['x_stot', 'y_stot'], right_on=[0, 1])
        presek.drop(columns=[0, 1], inplace=True)
        presek.rename(columns={2: '2_ostali', 3: '3_ostali'}, inplace=True)
        presek = presek.merge(lte800_dfa_sec, how='left', left_on=['x_stot', 'y_stot'], right_on=[0, 1])
        presek.drop(columns=[0, 1], inplace=True)
        presek.rename(columns={2: '2_sec', 3: '3_sec'}, inplace=True)
        presek = presek.merge(lte800_dfa_second, how='left', left_on=['x_stot', 'y_stot'], right_on=[0, 1])
        presek.drop(columns=[0, 1], inplace=True)
        presek.rename(columns={2: '2_sec_ostali', 3: '3_sec_ostali'}, inplace=True)

        presek['rangiranje'] = 0
        n = 0
        for m in NIVOJI:
            presek.loc[(presek['3_sec'] < n) & (presek['3_sec'] >= m), 'rangiranje'] = m
            n = m

        seznam = [
            'scenarij', 'celica', 'rangiranje', 'Naslovi_best', 'Prebivalci_best',
            'Naslovi_best_indoor', 'Naslovi_best_outdoor', 'Prebivalci_best_indoor',
            'Prebivalci_best_outdoor', 'Izboljsava_Naslovi_best', 'Izboljsava_Prebivalci_best',
            'Novi_Naslovi_best_indoor', 'Novi_Prebivalci_best_indoor', 'Novi_Naslovi_best_outdoor',
            'Novi_Prebivalci_best_outdoor', 'Izboljsava_Naslovi_best_indoor',
            'Izboljsava_Prebivalci_best_indoor', 'Izboljsava_Naslovi_best_outdoor',
            'Izboljsava_Prebivalci_best_outdoor', 'Naslovi_best_FWA potencial',
            'Naslovi_best_FWA_izboljsava', 'Naslovi_best_optika', 'Naslovi_best_neoptika',
            'Naslovi_second', 'Prebivalci_second', 'Naslovi_second_indoor', 'Naslovi_second_outdoor',
            'Prebivalci_second_indoor', 'Prebivalci_second_outdoor', 'Izboljsava_Naslovi_second',
            'Izboljsava_Prebivalci_second', 'Izboljsava_Naslovi_second_indoor',
            'Novi_Naslovi_second_indoor', 'Novi_Prebivalci_second_indoor',
            'Novi_Naslovi_second_outdoor', 'Novi_Prebivalci_second_outdoor',
            'Izboljsava_Prebivalci_second_indoor', 'Izboljsava_Naslovi_second_outdoor',
            'Izboljsava_Prebivalci_second_outdoor', 'Naslovi_second_FWA_redundanca',
            'Naslovi_second_FWA_izboljsava', 'Naslovi_second_optika', 'Naslovi_second_neoptika',
        ]
        temp = pd.DataFrame(columns=seznam)

        col = tocke_df.columns.tolist() + ['2_prim', '3_prim', '2_ostali', '3_ostali', 'rangiranje']
        col1 = tocke_df.columns.tolist() + ['2_sec', '3_sec', '2_sec_ostali', '3_sec_ostali', 'rangiranje']

        presek1 = presek[col].dropna(subset=['2_prim'], how='all')
        presek2 = presek[col1].dropna(subset=['2_sec'], how='all')

        stevec2 = len(presek2['2_sec'].drop_duplicates().tolist())
        for _ in presek1['2_prim'].drop_duplicates().tolist():
            stevec = stevec + 1 + stevec2

        temp.loc[stevec, 'scenarij'] = teh
        temp.loc[stevec, 'celica'] = 'Skupaj'
        temp.loc[stevec, 'Naslovi_best'] = presek1['HS_MID'].drop_duplicates().shape[0]
        temp.loc[stevec, 'Prebivalci_best'] = presek1['PREB_STAL'].sum()
        temp.loc[stevec, 'Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor)].sum()
        temp.loc[stevec, 'Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor)].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_best'] = presek1['HS_MID'].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_best'] = presek1['PREB_STAL'].sum()
        temp.loc[stevec, 'Novi_Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_ostali'] < nivo_indoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Novi_Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_ostali'] < nivo_indoor)].sum()
        temp.loc[stevec, 'Novi_Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_ostali'] < nivo_outdoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Novi_Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_ostali'] < nivo_outdoor)].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_prim'] > presek1['3_ostali'])].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_prim'] > presek1['3_ostali'])].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_prim'] > presek1['3_ostali'])].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_prim'] > presek1['3_ostali'])].sum()
        temp.loc[stevec, 'Naslovi_best_FWA potencial'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] == 'BAKER')].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_best_FWA_izboljsava'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] == 'BAKER') & (presek1['3_ostali'] < nivo_fwa)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_best_optika'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] == 'OPTIKA')].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_best_neoptika'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] != 'OPTIKA')].drop_duplicates().shape[0]

        temp.loc[stevec, 'Naslovi_second'] = presek2['HS_MID'].drop_duplicates().shape[0]
        temp.loc[stevec, 'Prebivalci_second'] = presek2['PREB_STAL'].sum()
        temp.loc[stevec, 'Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor)].sum()
        temp.loc[stevec, 'Prebivalci_second_outdoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor)].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_second'] = presek2['HS_MID'].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_second'] = presek2['PREB_STAL'].sum()
        temp.loc[stevec, 'Novi_Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec_ostali'] < nivo_indoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Novi_Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec_ostali'] < nivo_indoor)].sum()
        temp.loc[stevec, 'Novi_Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec_ostali'] < nivo_outdoor)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Novi_Prebivalci_second_outdoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec_ostali'] < nivo_outdoor)].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].sum()
        temp.loc[stevec, 'Izboljsava_Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].drop_duplicates().shape[0]
        temp.loc[stevec, 'Izboljsava_Prebivalci_second_outdoor'] = presek1['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].sum()
        temp.loc[stevec, 'Naslovi_second_FWA_redundanca'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] == 'BAKER')].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_second_FWA_izboljsava'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] == 'BAKER') & (presek2['3_sec_ostali'] < nivo_fwa)].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_second_optika'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] == 'OPTIKA')].drop_duplicates().shape[0]
        temp.loc[stevec, 'Naslovi_second_neoptika'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] != 'OPTIKA')].drop_duplicates().shape[0]

        stevec += 1
        temp_a = pd.concat([temp_a, temp])

    stolpci_koncno = [
        'scenarij', 'celica', 'Izboljsava_Naslovi_best', 'Izboljsava_Prebivalci_best',
        'Novi_Naslovi_best_indoor', 'Novi_Prebivalci_best_indoor', 'Novi_Naslovi_best_outdoor',
        'Novi_Prebivalci_best_outdoor', 'Izboljsava_Naslovi_best_indoor',
        'Izboljsava_Prebivalci_best_indoor', 'Izboljsava_Naslovi_best_outdoor',
        'Izboljsava_Prebivalci_best_outdoor', 'Naslovi_best_FWA potencial',
        'Naslovi_best_FWA_izboljsava', 'Izboljsava_Naslovi_second', 'Izboljsava_Prebivalci_second',
        'Izboljsava_Naslovi_second_indoor', 'Novi_Naslovi_second_indoor',
        'Novi_Prebivalci_second_indoor', 'Novi_Naslovi_second_outdoor',
        'Novi_Prebivalci_second_outdoor', 'Izboljsava_Prebivalci_second_indoor',
        'Izboljsava_Naslovi_second_outdoor', 'Izboljsava_Prebivalci_second_outdoor',
        'Naslovi_second_FWA_redundanca', 'Naslovi_second_FWA_izboljsava',
    ]

    suffix = "_v1lokalni" if fix_kaskada else "_v1lokalni_nofix"
    out_path = os.path.join(mapa, lokacija + "_analiza" + suffix + ".xlsx")
    temp_a[stolpci_koncno][temp_a['celica'] == 'Skupaj'].to_excel(out_path, index=False)
    print(f"\nShranjeno: {out_path}")
    return out_path


# ---------- Main ----------

def main():
    p = argparse.ArgumentParser(description="v1-style upravicenost analiza za operativno BP iz lokalnega kompozita.")
    p.add_argument("bp", help="BP ime (npr. PANKAR)")
    p.add_argument("--no-fix", action="store_true", help="Pusti v1 cascade bug aktiven (za demo)")
    p.add_argument("--celice", default=None, help="Komaseparirani cell list (preskoci Denali)")
    p.add_argument("--out", default=None, help="Output mapa za Excel (default: <KOMPOZIT_MAPA>/_analize)")
    args = p.parse_args()

    bp = args.bp.upper()
    fix = not args.no_fix
    out_mapa = args.out or os.path.join(KOMPOZIT_MAPA, "_analize")
    os.makedirs(out_mapa, exist_ok=True)

    print(f"BP        : {bp}")
    print(f"Kompozit  : {KOMPOZIT_MAPA}")
    print(f"Output    : {out_mapa}")
    print(f"Fix       : {'DA (sveža tocke_df)' if fix else 'NE (cascade bug)'}")

    # 1. Pridobi BP cells
    if args.celice:
        cells = [c.strip() for c in args.celice.split(',') if c.strip()]
        print(f"\nCelice (--celice): {cells}")
    else:
        cells = get_bp_cells(bp)
        print(f"\nCelice ({len(cells)}): {cells}")

    if not cells:
        print("Ni celic. Konec.")
        return

    # 2. Filter kompozit per band
    print(f"\n{'='*60}\nFILTER KOMPOZIT PER BAND\n{'='*60}")
    bands_per_tech = {'GSM': [], 'LTE': [], 'NR': []}
    t0 = time.time()
    for band, teh in BAND_TO_TECH.items():
        band_file = f"{band}_1_w.txt"
        df = filter_kompozit_band(band_file, cells)
        if df is not None and len(df) > 0:
            bands_per_tech[teh].append(df)
    print(f"\nFilter čas: {time.time()-t0:.1f}s")

    for teh, dfs in bands_per_tech.items():
        n_rows = sum(len(df) for df in dfs)
        print(f"  {teh}: {len(dfs)} band(ov), {n_rows} relevantnih vrstic skupno")

    # 3. Per-tech agregacija
    print(f"\n{'='*60}\nPER-TECH AGREGACIJA\n{'='*60}")
    t0 = time.time()
    tech_dfs = {}
    for teh in ['GSM', 'LTE', 'NR']:
        if bands_per_tech[teh]:
            print(f"  Agregiram {teh}...", end=' ', flush=True)
            tt0 = time.time()
            tech_dfs[teh] = aggregate_bands_to_tech(bands_per_tech[teh])
            print(f"{len(tech_dfs[teh])} agregiranih vrstic ({time.time()-tt0:.1f}s)")
    print(f"\nAgregacija čas: {time.time()-t0:.1f}s")

    # 4. izracunaj_stevilke
    print(f"\n{'='*60}\nANALIZA (izracunaj_stevilke)\n{'='*60}")
    t0 = time.time()
    izracunaj_stevilke_iz_dfs(tech_dfs, cells, bp, out_mapa, fix_kaskada=fix)
    print(f"Analiza čas: {time.time()-t0:.1f}s")


if __name__ == "__main__":
    main()
