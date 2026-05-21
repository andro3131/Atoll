# -*- coding: utf-8 -*-
"""
Test za potrditev/ovrženje "cascading tocke_df" buga v Žigovi v1 različici
upravicenost_bazne_postaje.

Logika je verbatim skopirana iz upravicenost_bazne_postaje_v1.py
(funkcija izracunaj_stevilke, vrstice ~181-440) z eno spremembo:

    --fix     (default)  → tocke_df se prebere SVEŽ na vrhu vsake iteracije
                            "for k in scenarij:" loop-a, kot v v0/preverba.
    --no-fix             → originalna v1 logika (kaskadni merge, ki znotraj
                            loop-a mutira tocke_df → vsaka naslednja
                            tehnologija dobi le ∩ s prejšnjo). Za demonstracijo
                            buga.

Vhod: že obstoječi Atoll txt exporti v <mapa>:
    <LOK>_GSM_[GSM].txt
    <LOK>_LTE_[LTE].txt
    <LOK>_NR_[5G NR].txt
(format kot ga producira v0 pipeline)

Output: <LOK>_analiza_v1kaskada.xlsx  (oz. _v1kaskada_nofix.xlsx)

Uporaba:
    py -3.10 test_kaskada_fix.py KJROVT
    py -3.10 test_kaskada_fix.py KJROVT --no-fix
    py -3.10 test_kaskada_fix.py KJROVT --mapa "D:\\Path\\To\\<LOK>\\"
"""

import argparse
import os
import sys
import time
import zipfile
import shutil

import pandas as pd
import numpy as np

import naredi_shp_za_112
import upravicenost_bp_atoll_datafill


# ---------- Konstante (verbatim iz v1 / preverba) ----------

tocke_pop = r"G:\Geo podatki\Naslovi_optika_baker_6_2_2024\\CRPE_Preb_Optika_Baker_D96_predelano.csv"

nivoji = list(range(-70, -126, -1))

# Privzeta osnova mape z že-poračunanimi exporti
DEFAULT_MAPA_BASE = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\"


# ---------- beri_pop_file (skopirana iz v1) ----------

def beri_pop_file(polna_pot_do_fileta):
    tocke_df = pd.read_csv(polna_pot_do_fileta, sep=";")
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
    tocke_df = beri_pop_file(tocke_pop)
    tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E'] % resoluc).astype(int)
    tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N'] % resoluc).astype(int)
    tocke_df[['x_stot', 'y_stot']] = tocke_df[['x_stot', 'y_stot']].astype(int)
    return tocke_df


# ---------- Auto-unzip, če txt-jev ni neposredno v mapi ----------

def zagotovi_txt_exporti(mapa, lokacija):
    """Vrne mapo, kjer dejansko ležijo *_[GSM|LTE|5G NR].txt fajli.
    Če v `mapa` ni .txt-jev, poskuša razpakirati <LOK>.zip ali pogledati v Atoll_export/.
    """
    iskalci = [
        f"{lokacija}_GSM_[GSM].txt",
        f"{lokacija}_LTE_[LTE].txt",
        f"{lokacija}_NR_[5G NR].txt",
    ]

    def ima_vsaj_eno(folder):
        if not os.path.isdir(folder):
            return False
        prisotni = os.listdir(folder)
        return any(p in prisotni for p in iskalci)

    if ima_vsaj_eno(mapa):
        return mapa

    podmapa = os.path.join(mapa, "Atoll_export") + "\\"
    if ima_vsaj_eno(podmapa):
        print(f"Najdeno v Atoll_export podmapi: {podmapa}")
        return podmapa

    zip_kandidati = [
        os.path.join(mapa, f"{lokacija}.zip"),
        os.path.join(mapa, "Atoll_export.zip"),
    ]
    for zip_pot in zip_kandidati:
        if os.path.isfile(zip_pot):
            ciljna = os.path.join(mapa, "_unzipped_za_test") + "\\"
            if os.path.isdir(ciljna):
                shutil.rmtree(ciljna)
            os.makedirs(ciljna, exist_ok=True)
            print(f"Razpakiram {zip_pot} → {ciljna}")
            with zipfile.ZipFile(zip_pot, 'r') as zf:
                zf.extractall(ciljna)
            if ima_vsaj_eno(ciljna):
                return ciljna

    raise FileNotFoundError(
        f"Ne najdem nobenega od {iskalci} v {mapa} (niti v Atoll_export/, "
        f"niti v <LOK>.zip). Premakni .txt fajle v {mapa} ali podaj --mapa."
    )


# ---------- Glavna funkcija: izracunaj_stevilke ----------

def izracunaj_stevilke(mapa, lokacija, celice, resolucija=25, fix_kaskada=True):
    """
    Skopirano iz upravicenost_bazne_postaje_v1.py izracunaj_stevilke(...)
    z dvema spremembama:
      1. Vhodne txt fajle bere preko naredi_shp_za_112.beri_atoll_txt_export_1_n_server
         (Atoll raw format, kot v v0/preverba), namesto pd.read_csv kompozit formata.
      2. Če je fix_kaskada=True → tocke_df se osveži na vrhu vsake iteracije
         loop-a (kot v v0/preverba). Drugače → originalna v1 logika z mutiranim
         tocke_df med iteracijami (bug).
    Slike (TIFF) so namensko izpuščene (v1 je tam imel napako na presek1__).
    """
    resoluc = resolucija

    scenarij1 = [
        lokacija + '_GSM_[GSM].txt',
        lokacija + '_LTE_[LTE].txt',
        lokacija + '_NR_[5G NR].txt',
    ]
    scenarij = [i for i in os.listdir(mapa) if i in scenarij1]
    print(f"Najdeni scenariji: {scenarij}")
    if not scenarij:
        raise FileNotFoundError(f"V {mapa} ni nobenega od {scenarij1}")

    # Prvotno (brez fix-a) v1 prebere tocke_df samo enkrat tukaj:
    if not fix_kaskada:
        tocke_df = pripravi_tocke_df(resoluc)

    temp_a = pd.DataFrame()
    stevec = 0

    for k in scenarij:
        # ===== FIX: osveži tocke_df na vrhu vsake iteracije =====
        if fix_kaskada:
            tocke_df = pripravi_tocke_df(resoluc)

        print(f"\n--- {k} ---")
        print(f"  tocke_df.shape PRED merge = {tocke_df.shape}")

        # Atoll raw format (kot v0/preverba), ne kompozit (kot v1):
        lte800_df = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(
            mapa + k, n=6, vsebuje=[], header_list=False,
        )
        lte800_df = lte800_df.replace('', np.nan)
        lte800_df[[0, 1]] = lte800_df[[0, 1]].astype(int)
        lte800_df[[3, 5, 7, 9, 11, 13]] = lte800_df[[3, 5, 7, 9, 11, 13]].astype(float)

        if k.find("GSM") >= 0:
            teh = 'GSM'
            nivo_indoor = -85
            nivo_outdoor = -96
            nivo_fwa = -30
        elif k.find("LTE") >= 0:
            teh = 'LTE'
            nivo_indoor = -85
            nivo_outdoor = -108
            nivo_fwa = -105
        elif k.find("NR") >= 0:
            teh = 'NR'
            nivo_indoor = -95
            nivo_outdoor = -108
            nivo_fwa = -105
        else:
            teh = 'LTE'
            nivo_indoor = -85
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
        lte800_dfa_sec.columns = [0, 1, 2, 3]

        lte800_df_second = lte800_df_second.dropna()
        lte800_df_second[3] = lte800_df_second[3].astype(float)
        lte800_dfa_second = lte800_df_second.groupby([0, 1]).agg({3: 'max', 2: list}).reset_index()
        lte800_dfa_second[6] = lte800_dfa_second[2].str[0]
        lte800_dfa_second.drop(columns=2, inplace=True)
        lte800_dfa_second.rename(columns={6: 2}, inplace=True)
        lte800_dfa_second = lte800_dfa_second[[0, 1, 2, 3]]
        lte800_dfa_second.columns = [0, 1, 2, 3]

        omejitev_tock_df = pd.concat([
            lte800_df1[[0, 1]],
            lte800_df1_second[[0, 1]],
            lte800_dfa_sec[[0, 1]],
            lte800_dfa_second[[0, 1]],
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
        for m in nivoji:
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
        # (ohranjam v1-jevo logiko, čeprav stevec1 ni uporabljen pravilno —
        # to ni vplivalo na končne številke)
        for _ in presek1['2_prim'].drop_duplicates().tolist():
            stevec = stevec + 1 + stevec2

        temp.loc[stevec, 'scenarij'] = k
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

    suffix = "_v1kaskada" if fix_kaskada else "_v1kaskada_nofix"
    out_path = mapa + lokacija + "_analiza" + suffix + ".xlsx"
    temp_a[stolpci_koncno][temp_a['celica'] == 'Skupaj'].to_excel(out_path, index=False)
    print(f"\nShranjeno: {out_path}")
    return out_path


# ---------- CLI ----------

def main():
    p = argparse.ArgumentParser(description="Test cascade fix za Žigov v1.")
    p.add_argument("lokacija", help="Ime lokacije (npr. KJROVT)")
    p.add_argument("--mapa", default=None,
                   help=r"Pot do mape z _[GSM|LTE|5G NR].txt fajli. "
                        r"Default: D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\<LOK>\\")
    p.add_argument("--no-fix", action="store_true",
                   help="Pusti v1 bug aktiven (kaskadni tocke_df merge).")
    p.add_argument("--celice", default=None,
                   help="Komaseparirani seznam celic — preskoči SQL lookup. "
                        "Privzeto: izbor_celic() iz Denali za to lokacijo.")
    args = p.parse_args()

    lokacija = args.lokacija
    fix = not args.no_fix
    mapa = args.mapa or (DEFAULT_MAPA_BASE + lokacija + "\\")
    if not mapa.endswith("\\") and not mapa.endswith("/"):
        mapa += "\\"

    print(f"Lokacija : {lokacija}")
    print(f"Mapa     : {mapa}")
    print(f"Fix      : {'DA (tocke_df sveže v vsaki iteraciji)' if fix else 'NE (originalni v1 bug — kaskada)'}")

    mapa = zagotovi_txt_exporti(mapa, lokacija)

    if args.celice:
        celice = [c.strip() for c in args.celice.split(",") if c.strip()]
    else:
        print(f"Pridobivam seznam celic iz Denali (izbor_celic)...")
        df_cel = upravicenost_bp_atoll_datafill.izbor_celic(
            seznam_lokacij=[lokacija], pisi_v_fajl=False,
        )
        celice = df_cel['celica'].tolist()
    print(f"Celice ({len(celice)}): {celice}")

    t0 = time.time()
    izracunaj_stevilke(mapa=mapa, lokacija=lokacija, celice=celice, fix_kaskada=fix)
    print(f"\nKonec, čas = {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
