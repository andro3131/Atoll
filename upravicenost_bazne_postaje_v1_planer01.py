
# -*- coding: utf-8 -*-
r"""
upravicenost_bazne_postaje_v1_planer01.py
==========================================
Planer01 adaptacija od Zigove upravicenost_bazne_postaje_v1_fixed.py (cascade fix vkljucen).

Razlike vs Zigov v1_fixed.py:
- vse G:\Avtomatika\... in G:\Pokrivanja\... poti => D:\Atoll_projects_planer01\...
- mapa_kompozit kaze na D:\Atoll_projects_planer01\Pokrivanja\Kompozit\ (Zigov auto-copy destinacija)
- VBS pot => D:\Atoll_projects_planer01\Skripte\VBasic\...
- tocke_pop OSTANE na G:\Geo podatki (deluje v v0)
- sys.path dodan za module na D:\

Uporaba (na planer01):
  py -3.10 D:\Atoll_projects_planer01\Skripte\Python\upravicenost_bazne_postaje\upravicenost_bazne_postaje_v1_planer01.py

Krmilna tabela: D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bp_krmilna_tabela.xlsx
Stolpci: Lokacija, Obstojec, Izvzeto_celica, Izvzeto_lokacija

Output:  D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje_v1\<LOK>\
"""

import sys
import os

# Modul setup - vse poti do siblings, ki jih v1 importa (gleda planer02 strukturo)
_PLANER01_MODULI = [
    r"D:\Atoll_projects_planer01\Skripte\Python\atoll_import_at",
    r"D:\Atoll_projects_planer01\Skripte\Python\upravicenost_bazne_postaje",
    r"D:\Atoll_projects_planer01\Skripte\Python\gis_zadeve",
]
for _p in _PLANER01_MODULI:
    if _p not in sys.path:
        sys.path.append(_p)

import pandas as pd
import polars as pl
import numpy as np
import subprocess
import zipfile
import re
import shutil
import time
import io
import funkcije_at
import upravicenost_bp_atoll_datafill
import posodobitev_ascii_exportov
import naredi_shp_za_112
import sql_atoll_3794
import sql_denali_3794
import df_to_tiff
import manipulacija_slik



########################
#   1. Preverimo Äe lokacija obstaja v Denali:
#       - Äe lokacija ni definirana, izstopimo
#       - Äe lokacija obstaja v Denali in ne v ATOLL-U jo skreiramo v atollu
#       - Äe celice niso definirane v denali, izstopimo
#       - Äe so celice definirafe v denali in ne v atollu, jih skreiramo v atollu. Äe jih ni v denali in so v atollu , jih v atollu deaktivoramo.
#
#   2. Vhodni podatek je slovar, kjer je kljuÄ lokacije, za katero Å¾elimo izraÄunati upraviÄenost, vrednost pa morebitna predhodna lokacija (nadomestna). Primer:  vhodni_podatki = {'NVTREB':'NRMAX'}. NVTREB je nadomestna #      lokacija za NRMAX, Äe ni nadomestna lokacija, damo v vrednost ''


# tocke_pop OSTANE na G:\ - tocno isti naslovi fajl kot v0 (deluje)
tocke_pop = r"G:\Geo podatki\Naslovi_optika_baker_6_2_2024\\CRPE_Preb_Optika_Baker_D96_predelano.csv"

# Upravicenost CSV input/output mape - migrirane z G:\ na D:\Atoll_projects_planer01\
odlozisce_novo = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Novo\\"
odlozisce_spremeni = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Spremeni\\"
odlozisce_brisi = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Brisi\\"
odlozisce_filter = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\\"

mapa_upravicenost = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje_v1\\"
mapa_upravicenost_temp = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje_temp\\"
fajl_celice = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\\Upravicenost_bp_celice.txt"
fajl_lokacija = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\\Upravicenost_bp_krmilna_tabela.xlsx"
# KOMPOZIT: Zigov auto-copy destinacija. Trenutno 4 fajli: GSM.txt, LTE.txt, NR.txt, NSA.txt (~12 GB skupaj)
mapa_kompozit = r"D:\Atoll_projects_planer01\Pokrivanja\Kompozit\\"


nivoji_iot = [-90, -100, -105, -115, -125, -140]
nivoji_nr = [-75, -85, -95, -105, -108, -110, -115, -120, -125]
nivoji = list(range(-70, -126, -1))

izberi_v_radiju  = 25000     # Äe Å¾elimo, da so v izraÄunu samo celice v nekem doloÄenem radij-u. Äe je veÄji od 0 ga upoÅ¡teva, drugaÄe ne


def naredi_folder(folder, ime):
    try:
        os.mkdir(folder + ime)
    except:
        FileExistsError
    return 0

def razvrscevalnik_exportov_celic(lokacija = ''):
    crit = True
    if lokacija == '':
        crit = crit & False
    if os.path.isdir(mapa_upravicenost + lokacija + "\\") == False:
        crit = crit & False
    if len(mapa_upravicenost + lokacija + "\\") == 0:
        crit = crit & False
    a = pd.read_csv(fajl_celice, sep = ';', header = None)
    a = a[a[3] == lokacija]
    if lokacija not in a[3].drop_duplicates().tolist():
        crit = crit & False

    if crit == True:
        a[4] = a[1].str.split("_", expand = True)[0]
        slovv = {}
        for i in a[4].drop_duplicates().tolist():
            temp = a[a[4] == i]
            cells = [(mapa_upravicenost + lokacija + "\\" + k + ".TXT") for k in temp[0].drop_duplicates().tolist()]
            slovv[i] = cells
        return slovv
    else:
        pass

def uredi_exporte(mapa, celice = []):
    if len(celice) == 0:
        cel = os.listdir(mapa)
    else:
        cel = []
        for i in os.listdir(mapa):
            if ((i.split('.')[0] in sez) & (i.split(".")[1] in ['txt','TXT'])):
                cel.append(i)
    for i in cel:
        naredi_shp_za_112.vnesi_celico_v_drugi_stolpec(mapa, i)
    return 0

def beri_pop_file(polna_pot_do_fileta):
    """
    Koordinatni sistem = D96
    """

    tocke_df = pd.read_csv(polna_pot_do_fileta, sep = ";")
    tocke_df=  tocke_df[['E', 'N','HS_TID', 'HS_MID','PREB_STAL', 'PREB_ZAC','NASLOV', 'PRIKLJUCEK']]
    tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
    tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
    if tocke_df['E'].dtypes == float:
        pass
    else:
        tocke_df['E'] = tocke_df['E'].str.replace(",",".").astype(float)
        tocke_df['N'] = tocke_df['N'].str.replace(",",".").astype(float)
    tocke_df.dropna(inplace  =True)
    return tocke_df

def subfolders(path_to_parent):
    """
    https://stackoverflow.com/questions/27789665/check-if-a-given-directory-contains-any-directory-in-python
    """
    try:
        return next(os.walk(path_to_parent))[1]
    except StopIteration:
        return []

def zipaj_txt_v_mapi_in_brisi(mapa, lokacija):
    # Zipaj .txt fileje in jih zbrisi
    file_list = [ii for ii in os.listdir(mapa + lokacija + "\\") if ((ii.find(".txt") > 0) | (ii.find(".TXT") > 0))]
    if len(file_list) > 0:
        naredi_folder(mapa  + lokacija, "\\Atoll_export\\")
        for ii in file_list:
            shutil.move(mapa + lokacija + "\\" + ii, mapa + lokacija + "\\Atoll_export\\" + ii)
        shutil.make_archive(mapa + lokacija + "\\" + lokacija, 'zip', mapa + lokacija + "\\Atoll_export\\")
        for ii in file_list:
            os.remove(mapa + lokacija + "\\Atoll_export\\" + ii)
        shutil.rmtree(mapa + lokacija + "\\Atoll_export\\")
    return 0

def razdalja_med_lokacijami(n, lokacija = ''):
    """
    n = Å¡tevilo lokacij v range-u
    """
    data = funkcije_at.pd.read_sql(sql_denali_3794.celice_pwas, sql_denali_3794.conn_denali)
    data1 = data[(((data['Delujoca'] == True) & (data['Type'] == 'Outdoor') & (data['tehn'] != 'UMTS')))].reset_index(drop = True)
    data2 = data[(data['ImeBSC'] == lokacija)]
    data = funkcije_at.pd.concat([data1, data2])
    data = data[['ImeBSC', 'Delujoca', 'Type', 'celica','azimut', 'beamwidth','ZSirina','ZVisina']]
    data_loks = data[['ImeBSC','celica']]
    data = data[['ImeBSC','ZSirina','ZVisina']].drop_duplicates()
    data['ZSirina']  =data['ZSirina'].astype(int)
    data['ZVisina']  =data['ZVisina'].astype(int)
    skupaj = funkcije_at.pd.merge(data[['ImeBSC','ZSirina','ZVisina']][data['ImeBSC'] == lokacija], data[['ImeBSC','ZSirina','ZVisina']], how = 'cross')
    skupaj['razdalja'] = funkcije_at.np.sqrt((skupaj['ZSirina_x'] - skupaj['ZSirina_y'])*(skupaj['ZSirina_x'] - skupaj['ZSirina_y']) + (skupaj['ZVisina_x'] - skupaj['ZVisina_y'])*(skupaj['ZVisina_x'] - skupaj['ZVisina_y']))
    skupaj = skupaj[skupaj['razdalja'] > 0]
    skupaj['vrstni_red'] = skupaj.sort_values(by = ['ImeBSC_x','razdalja'], ascending = [True, True]).groupby(['ImeBSC_x']).cumcount() + 1
    skupaj = skupaj[skupaj['vrstni_red'] <= n]
    skupaj_povprecje = skupaj[['ImeBSC_x','razdalja']].groupby(['ImeBSC_x']).agg({'razdalja':'mean'}).reset_index()
    skupaj_povprecje['razdalja'] = skupaj_povprecje['razdalja'].round(1)
    # data_loks = data_loks.merge(skupaj_povprecje, how = 'inner', left_on = 'ImeBSC', right_on = 'ImeBSC_x')
    return skupaj_povprecje['razdalja'].values[0]

def odd_bp_od_naslov(lokacija):
    maximum = 25000
    oddaljenost = 5 * razdalja_med_lokacijami(n = 12, lokacija = lokacija)
    if oddaljenost < maximum:
        a = int(oddaljenost)
    else:
        a=maximum
    return a


def shape_tocke(df, odlozisce, ime_fajla):
    gdf_points = gpd.GeoDataFrame(
        df,
        # geometry=[Point(xy) for xy in zip(df["GKe"], df["GKn"])],
        geometry=[Point(xy) for xy in zip(df["E"], df["N"])],
        crs="EPSG:3794"
    )
    return gdf_points.to_file(odlozisce + ime_fajla, driver='ESRI Shapefile')


def izracunaj_stevilke(mapa = '', lokacija = '', resolucija = 25, celice = [],naredi_slike=False):
    # FIX 2026-05-14 (cascade bug):
    # Tocke_df se NE bere več tukaj (pred for-loop-om).
    # Ker spodaj `tocke_df = tocke_df.merge(omejitev_tock_df, how='inner', ...)`
    # MUTIRA tocke_df znotraj loop-a, je vsaka naslednja iteracija dobila le
    # presek s prejšnjo tehnologijo (npr. LTE je dobil samo točke, kjer obstaja
    # tudi GSM coverage → naslovi z LTE-only ali NR-only pokrivanjem so izpadli).
    # Branje + x_stot/y_stot je premaknjeno na vrh for-loop-a spodaj.
    resoluc = resolucija

    # sites = funkcije_at.pd.read_sql(sql_atoll_3794.query_sites, sql_atoll_3794.conn_atoll)
    # sites = sites[sites['NAME'] == lokacija]
    # if sites.shape[0] == 0:
        # sites = funkcije_at.pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
        # sites = sites[['rru_ime','ZSirina','ZVisina']][sites['rru_ime'] == lokacija]
        # sites.columns = ['NAME','LONGITUDE','LATITUDE']
    # oddaljenost_BP_od_naslova = odd_bp_od_naslov(lokacija)


    # sites_x1 = int(sites['LONGITUDE'].values[0]) - oddaljenost_BP_od_naslova
    # sites_x2 = int(sites['LONGITUDE'].values[0]) + oddaljenost_BP_od_naslova
    # sites_y1 = int(sites['LATITUDE'].values[0]) - oddaljenost_BP_od_naslova
    # sites_y2 = int(sites['LATITUDE'].values[0]) + oddaljenost_BP_od_naslova
    # tocke_df = tocke_df[(tocke_df['E'] > sites_x1) & (tocke_df['E'] < sites_x2) & (tocke_df['N'] > sites_y1) & (tocke_df['N'] < sites_y2)]

    scenarij1 = [lokacija + '_GSM.txt',lokacija + '_LTE.txt', lokacija + '_NR.txt']
    scenarij = []

    # mapa = 'G:\\Pokrivanja\\Upravicenost_bazne_postaje\\SLEMBR\\SLEMBR\\\\'

    for i in os.listdir(mapa):
        if i in scenarij1:
            scenarij.append(i)

    temp_a = pd.DataFrame()
    temp_b = pd.DataFrame()
    kompozit_lte = []

    stevec = 0

    for k in scenarij:

        # FIX 2026-05-14 (cascade bug): osveži tocke_df za vsako iteracijo, da
        # ne nadaljujemo s presek-om iz prejšnje tehnologije.
        tocke_df = beri_pop_file(tocke_pop)
        tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E']%resoluc).astype(int)
        tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N']%resoluc).astype(int)
        tocke_df[['x_stot','y_stot']] = tocke_df[['x_stot','y_stot']].astype(int)

        lte800_df = pd.read_csv(mapa + k, sep = ';')
        # lte800_df = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path = mapa + k, n = 6, vsebuje=[], header_list=False)
        lte800_df.columns = [int(i) for i in lte800_df.columns.tolist()]
        lte800_df = lte800_df.replace('', np.nan)
        lte800_df[[0,1]] = lte800_df[[0,1]].astype(int)
        # lte800_df = lte800_df[(lte800_df[0]> sites_x1) & (lte800_df[0] < sites_x2) & (lte800_df[1] > sites_y1) & (lte800_df[1] < sites_y2)]
        lte800_df[[3,5,7,9,11,13]] = lte800_df[[3,5,7,9,11,13]].astype(float)

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

        lte800_df1 = lte800_df[[0,1,2,3]]   # source best server
        lte800_df1 = lte800_df1[lte800_df1[2].isin(celice)]
        lte800_df1_second = lte800_df[[0,1,4,5]].loc[lte800_df1[lte800_df1[2].isin(celice)].index].rename(columns = {4:2, 5:3}).dropna()  # source na mestu iskanega best server-ja
        lte800_df1_second[3] = lte800_df1_second[3].astype(float)
        lte800_df1_second_a = lte800_df[[0,1,6,7]].loc[lte800_df1_second[lte800_df1_second[2].isin(celice)].index].rename(columns = {6:2, 7:3}).dropna()
        lte800_df1_second = lte800_df1_second[~lte800_df1_second[2].isin(celice)]
        lte800_df1_second = pd.concat([lte800_df1_second, lte800_df1_second_a])

        lte800_df2 = lte800_df[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        lte800_df2 = lte800_df2[lte800_df2[2].isin(celice)]
        lte800_df2_second = lte800_df[[0,1,6,7]].loc[lte800_df2[lte800_df2[2].isin(celice)].index].rename(columns = {6:2, 7:3}).dropna()
        lte800_df2_second[3] = lte800_df2_second[3].astype(float)
        lte800_df2_second_a = lte800_df[[0,1,8,9]].loc[lte800_df2_second[lte800_df2_second[2].isin(celice)].index].rename(columns = {8:2, 9:3}).dropna()
        lte800_df2_second = lte800_df2_second[~lte800_df2_second[2].isin(celice)]
        lte800_df2_second = pd.concat([lte800_df2_second, lte800_df2_second_a])

        lte800_df_sec = pd.concat([lte800_df1, lte800_df2])
        lte800_df_second = pd.concat([lte800_df1_second, lte800_df2_second])

        lte800_df_sec = lte800_df_sec.dropna()
        lte800_df_sec = lte800_df_sec[lte800_df_sec[2].isin(celice)]
        lte800_df_sec[3] = lte800_df_sec[3].astype(float)
        lte800_dfa_sec = lte800_df_sec.groupby([0,1]).agg({3:'max', 2:list}).reset_index()
        lte800_dfa_sec[6] = lte800_dfa_sec[2].astype(str).str[0]
        lte800_dfa_sec.drop(columns = 2, inplace = True)
        lte800_dfa_sec.rename(columns = {6:2}, inplace = True)
        lte800_dfa_sec = lte800_dfa_sec[[0,1,2,3]]  # source second best server
        lte800_dfa_sec.columns = [0,1,2,3]

        lte800_df_second = lte800_df_second.dropna()
        lte800_df_second[3] = lte800_df_second[3].astype(float)
        lte800_dfa_second = lte800_df_second.groupby([0,1]).agg({3:'max', 2:list}).reset_index()
        lte800_dfa_second[6] = lte800_dfa_second[2].str[0]
        lte800_dfa_second.drop(columns = 2, inplace = True)
        lte800_dfa_second.rename(columns = {6:2}, inplace = True)
        lte800_dfa_second = lte800_dfa_second[[0,1,2,3]]    # source na mestu iskanega second best server-ja
        lte800_dfa_second.columns = [0,1,2,3]

        # lte800_df2_ = lte800_df[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        # lte800_df3_ = lte800_df[[0,1,6,7]].rename(columns = {6:2, 7:3}).dropna()
        # lte800_df4_ = lte800_df[[0,1,8,9]].rename(columns = {8:2, 9:3}).dropna()
        # lte800_df5_ = lte800_df[[0,1,10,11]].rename(columns = {10:2, 11:3}).dropna()
        # lte800_df6_ = lte800_df[[0,1,12,13]].rename(columns = {12:2, 13:3}).dropna()
        # lte800_vse = pd.concat([lte800_df1, lte800_df2_, lte800_df3_, lte800_df4_, lte800_df5_, lte800_df6_]).drop_duplicates().dropna()

        omejitev_tock_df = pd.concat([lte800_df1[[0,1]], lte800_df1_second[[0,1]], lte800_dfa_sec[[0,1]], lte800_dfa_second[[0,1]]]).drop_duplicates()
        # omejitev_tock_df = lte800_vse[[0,1]].drop_duplicates()
        tocke_df = tocke_df.merge(omejitev_tock_df, how = 'inner', left_on = ['x_stot','y_stot'], right_on = [0,1])
        tocke_df.drop(columns = [0,1], inplace = True)
        # tocke_df_columns = tocke_df.columns.tolist()

        presek = tocke_df.merge(lte800_df1, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek.drop(columns = [0,1], inplace = True)
        presek.rename(columns = {2:'2_prim',3:'3_prim'}, inplace = True)
        presek = presek.merge(lte800_df1_second, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek.drop(columns = [0,1], inplace = True)
        presek.rename(columns = {2:'2_ostali',3:'3_ostali'}, inplace = True)
        presek = presek.merge(lte800_dfa_sec, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek.drop(columns = [0,1], inplace = True)
        presek.rename(columns = {2:'2_sec',3:'3_sec'}, inplace = True)
        presek = presek.merge(lte800_dfa_second, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek.drop(columns = [0,1], inplace = True)
        presek.rename(columns = {2:'2_sec_ostali',3:'3_sec_ostali'}, inplace = True)
        # presek = presek.merge(lte800_vse, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # presek.drop(columns = [0,1], inplace = True)
        # presek.rename(columns = {2:'2_vsi',3:'3_vsi'}, inplace = True)



        presek['rangiranje'] = 0
        n = 0
        for m in nivoji:
            presek.loc[(presek['3_sec'] < n)&(presek['3_sec'] >= m), 'rangiranje'] = m
            n = m

        seznam = ['scenarij','celica','rangiranje','Naslovi_best','Prebivalci_best','Naslovi_best_indoor','Naslovi_best_outdoor',
            'Prebivalci_best_indoor','Prebivalci_best_outdoor','Izboljsava_Naslovi_best','Izboljsava_Prebivalci_best',
            'Novi_Naslovi_best_indoor','Novi_Prebivalci_best_indoor','Novi_Naslovi_best_outdoor','Novi_Prebivalci_best_outdoor',
            'Izboljsava_Naslovi_best_indoor', 'Izboljsava_Prebivalci_best_indoor', 'Izboljsava_Naslovi_best_outdoor', 'Izboljsava_Prebivalci_best_outdoor',
            'Naslovi_best_FWA potencial','Naslovi_best_FWA_izboljsava','Naslovi_best_optika', 'Naslovi_best_neoptika',
            'Naslovi_second','Prebivalci_second','Naslovi_second_indoor','Naslovi_second_outdoor', 'Prebivalci_second_indoor',
            'Prebivalci_second_outdoor', 'Izboljsava_Naslovi_second','Izboljsava_Prebivalci_second','Izboljsava_Naslovi_second_indoor',
            'Novi_Naslovi_second_indoor', 'Novi_Prebivalci_second_indoor', 'Novi_Naslovi_second_outdoor', 'Novi_Prebivalci_second_outdoor',
            'Izboljsava_Prebivalci_second_indoor','Izboljsava_Naslovi_second_outdoor','Izboljsava_Prebivalci_second_outdoor',
            'Naslovi_second_FWA_redundanca','Naslovi_second_FWA_izboljsava','Naslovi_second_optika', 'Naslovi_second_neoptika']

        temp = pd.DataFrame(columns = seznam)
        # 1. primer best server
        col = tocke_df.columns.tolist()
        col.append('2_prim')
        col.append('3_prim')
        col.append('2_ostali')
        col.append('3_ostali')
        col.append('rangiranje')

        col1 = tocke_df.columns.tolist()
        col1.append('2_sec')
        col1.append('3_sec')
        col1.append('2_sec_ostali')
        col1.append('3_sec_ostali')
        col1.append('rangiranje')


        presek1 = presek[col]
        presek1 = presek1.dropna(subset = ['2_prim'], how = 'all')
        presek2 = presek[col1]
        presek2 = presek2.dropna(subset = ['2_sec'], how = 'all')


        stevec2 = 0
        for i in presek2['2_sec'].drop_duplicates().tolist():
            stevec2 = stevec2 + 1


        stevec1 = 0
        for i in presek1['2_prim'].drop_duplicates().tolist():
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

# Slikice
        if (naredi_slike == True) & ((k.find('LTE') >= 0) | (k.find('NR.') >=0)):
            try:
                os.mkdir(mapa + "Slike\\")
            except:
                pass

            # 'Izboljsava_Naslovi_best_outdoor'
            ime__ = lokacija + "_Izboljsava_Naslovi_best_outdoor_" + k.split("_")[1]
            shape_tocke(df = presek1[['E','N']][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_prim'] > presek1['3_ostali'])].drop_duplicates(), odlozisce = mapa + "Slike\\", ime_fajla = ime__ + "_naslovi.shp")
            df__ = presek1__[['x_stot',  'y_stot' ,  '2_prim' , '3_prim']][(presek1__['3_prim'] >= nivo_outdoor) & (presek1__['3_prim'] > presek1__['3_ostali'])].drop_duplicates()
            df__.columns = [0,1,2,3]
            df_to_tiff.naredi_tif1(file_pokrivanje = df__, odlozisce = mapa + "Slike\\", tip = 'df', resolution = 25, ime = ime__ , treshold = nivo_outdoor, x_offset = 12.5, y_offset = 12.5)
            manipulacija_slik.transparent2(mapa = mapa + "Slike\\", slika = ime__ + ".tif", odlozisce = mapa + "Slike\\")
            os.remove(mapa + "Slike\\" + ime__ + '.tif')
            os.rename(mapa + "Slike\\" + ime__ + '__TRANSPARENT.tif', mapa + "Slike\\" + ime__ + '.tif')



        stevec = stevec + 1
        temp_a = pd.concat([temp_a, temp])

    stolpci_koncno = ['scenarij',	'celica',	'Izboljsava_Naslovi_best',	'Izboljsava_Prebivalci_best',	'Novi_Naslovi_best_indoor',	'Novi_Prebivalci_best_indoor'	,'Novi_Naslovi_best_outdoor',	'Novi_Prebivalci_best_outdoor',	'Izboljsava_Naslovi_best_indoor'	,'Izboljsava_Prebivalci_best_indoor'	,'Izboljsava_Naslovi_best_outdoor'	,'Izboljsava_Prebivalci_best_outdoor'	,'Naslovi_best_FWA potencial','Naslovi_best_FWA_izboljsava','Izboljsava_Naslovi_second',	'Izboljsava_Prebivalci_second'	,'Izboljsava_Naslovi_second_indoor'	,'Novi_Naslovi_second_indoor'	,'Novi_Prebivalci_second_indoor'	,'Novi_Naslovi_second_outdoor',	'Novi_Prebivalci_second_outdoor'	,'Izboljsava_Prebivalci_second_indoor',	'Izboljsava_Naslovi_second_outdoor',	'Izboljsava_Prebivalci_second_outdoor',	'Naslovi_second_FWA_redundanca','Naslovi_second_FWA_izboljsava']
    temp_a[stolpci_koncno][temp_a['celica'] == 'Skupaj'].to_excel(mapa + lokacija  + "_analiza_v1a.xlsx", index = False)

    # PNG/JPG generacija iz TIF+SHP (lazy import - ne ubije skripte ce contextily/pip-system-certs
    # ali OSM tile fetch padejo - TIF+SHP+analiza so ze varni).
    if naredi_slike:
        try:
            import narisi_pokrivanje
            narisi_pokrivanje.obdelaj_lokacijo(lokacija, slike_dir=mapa + "Slike\\")
        except Exception as e:
            print(f"OPOZORILO: PNG generacija ni uspela za {lokacija}: {e}")
            print(f"  TIF+SHP+analiza so OK. PNG-je lahko rocno re-generiras z: py -3.10 narisi_pokrivanje.py {lokacija}")

    return 0


def brisi_izvzeto(vhodni_seznam, celice_brisi):

    pattern_brisi = "|".join([i + ";-[0-9]*.?[0-9]*;{0,1}" for i in celice_brisi])
    pattern_brisi_prazna_vrstica = "[0-9]{5,7};[0-9]{4,6};+\\n"
    mmr_brisanje = [re.sub(";\\n","\\n",x) for x in [x for x in [re.sub(pattern_brisi,"",x) for x in vhodni_seznam] if not re.search(pattern_brisi_prazna_vrstica,x)]]
    return mmr_brisanje

def vse_celice_atoll_denali(lokacija = []):
    if len(lokacija) == 0:
        return []
    else:
        if lokacija[0] == '':
            return []
        else:
            cel_atoll = pd.read_sql(sql_atoll_3794.vse_celice, sql_atoll_3794.conn_atoll)
            cel_atoll = cel_atoll['CELICA'][cel_atoll['SITE_NAME'].isin(lokacija)].drop_duplicates().tolist()
            cel_denali = pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
            cel_denali = cel_denali['celica'][((cel_denali['ImeBSC'].isin(lokacija)) | (cel_denali['rru_ime'].isin(lokacija)))].drop_duplicates().tolist()
            cel_ = list(set(funkcije_at.razlika_seznamov(cel_atoll,cel_denali, nacin = 'unija')))
        return cel_

def vse_celice_radij(lokacija = '', radij = 25000, nacin = 'notri'):
    """
    nacin: notri ali izven
    """
    if lokacija == '':
        return []
    else:
        cel_atoll = pd.read_sql(sql_atoll_3794.vse_celice, sql_atoll_3794.conn_atoll)
        try:
            lon = cel_atoll['ABS_X'][cel_atoll['SITE_NAME'] == lokacija].drop_duplicates().values[0]
            lat = cel_atoll['ABS_Y'][cel_atoll['SITE_NAME'] == lokacija].drop_duplicates().values[0]
            cel_atoll_ = cel_atoll[['CELICA','TEHN']][( (cel_atoll['ABS_X'] < (lon + radij)) & (cel_atoll['ABS_X'] > (lon- radij)) & (cel_atoll['ABS_Y'] > (lat - radij)) & (cel_atoll['ABS_Y'] < (lat + radij)))].drop_duplicates()
        except:
            cel_atoll_ = pd.DataFrame(columns = ['CELICA','TEHN'])
        cel_denali = pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
        try:
            lon_ = cel_denali['ZSirina'][((cel_denali['ImeBSC'] == lokacija) | (cel_denali['rru_ime'] == lokacija))].drop_duplicates().values[0]
            lat_ = cel_denali['ZVisina'][((cel_denali['ImeBSC'] == lokacija) | (cel_denali['rru_ime'] == lokacija))].drop_duplicates().values[0]
            cel_denali_ = cel_denali[['celica','tehn']][( (cel_denali['ZSirina'] < (lon_ + radij)) & (cel_denali['ZSirina'] > (lon_ - radij)) & (cel_denali['ZVisina'] > (lat_ - radij)) & (cel_denali['ZVisina'] < (lat_ + radij)))].drop_duplicates()
        except:
            cel_denali_ = pd.DataFrame(columns = ['celica','tehn'])
        skupaj = funkcije_at.pd.concat([cel_atoll_,cel_denali_.rename(columns = {'celica':'CELICA','tehn':'TEHN'})]).drop_duplicates()
        skupaj['TEHN'] = skupaj['TEHN'].str.replace('5G','NR')
        if nacin == 'izven':
            skupaj_ = list(set(funkcije_at.razlika_seznamov(cel_atoll['CELICA'].drop_duplicates().tolist(),cel_denali['celica'].drop_duplicates().tolist(), nacin = 'unija')))
            skupaj = skupaj[~skupaj['CELICA'].isin(skupaj_)]
        else:
            pass
        d = {}
        for i in skupaj['TEHN'].drop_duplicates().tolist():
            d[i] = [j for j in skupaj['CELICA'][skupaj['TEHN'] == i].tolist() if j.find('*')<0]
        return d

def main():
    t0 = time.time()
    print("ZaÄetek")
    # planer01 dodatek: zagotovi obstoj vseh map (idempotentno) - VBS pricakuje da obstajajo
    for _d in (odlozisce_novo, odlozisce_spremeni, odlozisce_brisi, odlozisce_filter,
               mapa_upravicenost, mapa_upravicenost_temp,
               r"D:\Atoll_projects_planer01\Pokrivanja\Planirane_celice"):
        os.makedirs(_d, exist_ok=True)
    if len(os.listdir(mapa_upravicenost_temp))> 0:
        for i in os.listdir(mapa_upravicenost_temp):
            os.remove(mapa_upravicenost_temp + i)
    tabela = pd.read_excel(fajl_lokacija)
    tabela['Izvzeto_celica'].fillna('', inplace = True)
    tabela['Izvzeto_lokacija'].fillna('', inplace = True)
    tabela['Obstojec'].fillna(False, inplace = True)
    tabela['Obstojec'].replace(1, True, inplace = True)
    # tabela_dict = dict(zip(tabela['Lokacija'], tabela['Izvzeto']))
    for i in tabela['Lokacija'].tolist():
        naredi_folder(folder = mapa_upravicenost, ime = i)
    # Podatke iz Atolla damo samo za lokacije, za katere raÄunamo planirano stanje
    if (tabela[tabela['Obstojec'] == False].shape[0] > 0):
        upravicenost_bp_atoll_datafill.izbor_celic(tabela['Lokacija'][tabela['Obstojec'] == False].tolist())
        upravicenost_bp_atoll_datafill.atoll_datafill_podatki(dict(zip(tabela['Lokacija'][tabela['Obstojec'] == False].tolist(), [[] for i in range(tabela['Lokacija'][tabela['Obstojec'] == False].shape[0])])))
        t1 = time.time()
        print("     Priprava podatkov je {}s".format(t1 - t0))
        # VBS migriran na D:\ - planer01 verzija ima Refresh disablane (memory 2026-04-24).
        # NO Archive klicev v _v1 VBS (preverjeno) - brez kontaminacije atoll_d96.
        subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano_v1_planer01.vbs'],   capture_output=True,  text=True)
        t2 = time.time()
        print("     Atoll {}s".format(t2-t1))

    for i in tabela.index:
        key = tabela.loc[i,'Lokacija']
        izvzet = tabela.loc[i,'Izvzeto_celica'].split(",")
        nadomesca = tabela.loc[i,'Izvzeto_lokacija'].split(",")
        obstojec = tabela.loc[i,'Obstojec']
        if ((len(nadomesca) >= 1)  & (nadomesca[0] != '')):
            tt = vse_celice_atoll_denali(lokacija = nadomesca)
        else:
            pass
        t3 = time.time()
        exporti = razvrscevalnik_exportov_celic(lokacija = key)
        try:
            uredi_exporte(mapa = mapa_upravicenost + key + "\\")
        except:
            pass
        ssez1 = []
        ssez1.append(key)
        celice_ = upravicenost_bp_atoll_datafill.izbor_celic(seznam_lokacij = ssez1, pisi_v_fajl = False)['celica'].tolist()
        if obstojec == True:
            for key1 in os.listdir(mapa_kompozit):
                komp = pl.read_csv(mapa_kompozit + key1 , separator = ';')
                stolpci = komp.columns
                if len(stolpci) == 4:
                    skupaj = komp.filter(pl.col("2").is_in(celice_))
                elif len(stolpci) == 6:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_))
                elif len(stolpci) == 8:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_) | pl.col("6").is_in(celice_))
                elif len(stolpci) == 10:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_) | pl.col("6").is_in(celice_) | pl.col("8").is_in(celice_))
                elif len(stolpci) == 12:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_) | pl.col("6").is_in(celice_) | pl.col("8").is_in(celice_) | pl.col("10").is_in(celice_))
                elif len(stolpci) == 14:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_) | pl.col("6").is_in(celice_) | pl.col("8").is_in(celice_) | pl.col("10").is_in(celice_)  | pl.col("12").is_in(celice_))
                else:
                    skupaj = komp.filter(pl.col("2").is_in(celice_) | pl.col("4").is_in(celice_) | pl.col("6").is_in(celice_) | pl.col("8").is_in(celice_) | pl.col("10").is_in(celice_)  | pl.col("12").is_in(celice_))
                if skupaj.shape[0] > 0:
                    skupaj.write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1, separator = ';')
        else:

            for key1, value1 in exporti.items():
                cel_komp = posodobitev_ascii_exportov.kompozit_od_zacetka(seznam_txt_exportov = value1)
                komp = pl.read_csv(mapa_kompozit + key1 + ".txt", separator = ';')
                skupaj = cel_komp.join(komp, how = 'left', on=['0','1'])
                print(skupaj)
                print(skupaj.dtypes)
                if '0_right' in skupaj.columns:
                    skupaj = skupaj.drop(['0_right'])
                if '1_right' in skupaj.columns:
                    skupaj = skupaj.drop(['1_right'])
                skupaj.columns = [str(i) for i in range(0,skupaj.shape[1],1)]
                print(skupaj.dtypes)
                sku_raz = posodobitev_ascii_exportov.razvrstitev_po_velikosti(skupaj)
                stolpci = sku_raz.columns



                if len(stolpci) == 4:
                    skupaj = sku_raz.filter(pl.col("2").is_in(celice_))
                elif len(stolpci) == 6:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)))
                elif len(stolpci) == 8:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)) | (pl.col("6").is_in(celice_)))
                elif len(stolpci) == 10:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)) | (pl.col("6").is_in(celice_)) | (pl.col("8").is_in(celice_)))
                elif len(stolpci) == 12:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)) | (pl.col("6").is_in(celice_)) | (pl.col("8").is_in(celice_)) | (pl.col("10").is_in(celice_)))
                elif len(stolpci) == 14:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)) | (pl.col("6").is_in(celice_)) | (pl.col("8").is_in(celice_)) | (pl.col("10").is_in(celice_))  | (pl.col("12").is_in(celice_)))
                else:
                    skupaj = sku_raz.filter((pl.col("2").is_in(celice_)) | (pl.col("4").is_in(celice_)) | (pl.col("6").is_in(celice_)) | (pl.col("8").is_in(celice_)) | (pl.col("10").is_in(celice_))  | (pl.col("12").is_in(celice_)))
                if sku_raz.shape[1] > 14:
                    skupaj.select(pl.col([str(i) for i in range(14)])).write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1 + ".txt", separator = ';')
                else:
                    skupaj.write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1 + ".txt", separator = ';')

        # BRISANJE, NADOMESCA, IZVZETO
        if ((len(izvzet) >= 1)  & (izvzet[0] != '')) | ((len(nadomesca) >= 1)  & (nadomesca[0] != '')):
            celice_brisi = []
            if ((len(nadomesca) >= 1)  & (nadomesca[0] != '')):
                celice_brisi = upravicenost_bp_atoll_datafill.izbor_celic(seznam_lokacij = nadomesca, pisi_v_fajl = False)['celica'].tolist()
                celice_brisi = funkcije_at.razlika_seznamov(celice_brisi, tt, nacin = 'unija')
            if ((len(izvzet) >= 1)  & (izvzet[0] != '')):
                celice_brisi = celice_brisi + izvzet
            for key2,celice_1 in vse_celice_za_radij.items():
                komp = pl.read_csv(mapa_upravicenost + key + '\\' + key + "_" + key2 + ".txt" , separator = ';')
                stolpci = [ii for ii in komp.columns if ((int(ii)%2 == 0) & (int(ii)>= 2))]
                komp_ = pl.DataFrame()
                for ii in stolpci:
                    komp_temp = komp.select(pl.col(['0','1',ii,str(int(ii)+1)]))
                    komp_temp = komp_temp.filter(pl.col(ii).is_in(celice_1))    #.drop_nans().drop_nulls()
                    if komp_.shape[0] == 0:
                        komp_ = komp_temp
                    else:
                        komp_ = komp_.join(komp_temp, how = 'full', on = ['0','1'])
                        komp_right = komp_.filter(pl.col("0").is_null())
                        komp_left = komp_.filter(pl.col("0_right").is_null())
                        komp_inner = komp_.filter(pl.col('0').is_not_null() & pl.col('0_right').is_not_null())
                        # komp_ = pl.concat([komp_left, komp_right, komp_inner])
                        # print(komp_)
                        # komp_ = komp_.select(pl.col([mm for mm in komp_.columns if mm.find("_")<0]))
                        # print(komp_)

                        if komp_right.shape[0] > 0:
                            komp_right_stolp = ['0_right','1_right',ii,str(int(ii)+1)]
                            komp_right = komp_right.select(komp_right_stolp)
                            komp_right.columns = ['0','1','2','3']
                            komp_right_razlika_stolp = funkcije_at.razlika_seznamov(komp_right.columns, komp_.columns, nacin = 'komplement2')
                            if len(komp_right_razlika_stolp) > 0:
                                for ppp in komp_right_razlika_stolp:
                                    komp_right = komp_right.with_columns(pl.lit(None).alias(ppp))
                        else:
                            pass
                        komp_ = pl.concat([komp_left, komp_right, komp_inner])
                        komp_ = komp_.select(pl.col([mm for mm in komp_.columns if mm.find("_")<0]))
            if komp_.shape[0] > 0:
                komp_.write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1 + "_.txt", separator = ';')
        else:
            pass

        if izberi_v_radiju > 0:
            vse_celice_za_radij = vse_celice_radij(lokacija = key, radij = izberi_v_radiju, nacin = 'notri')

            for key2,celice_1 in vse_celice_za_radij.items():
                komp = pl.read_csv(mapa_upravicenost + key + '\\' + key + "_" + key2 + ".txt" , separator = ';')
                stolpci = [ii for ii in komp.columns if ((int(ii)%2 == 0) & (int(ii)>= 2))]
                komp_ = pl.DataFrame()
                for ii in stolpci:
                    komp_temp = komp.select(pl.col(['0','1',ii,str(int(ii)+1)]))
                    komp_temp = komp_temp.filter(pl.col(ii).is_in(celice_1))    #.drop_nans().drop_nulls()
                    if komp_.shape[0] == 0:
                        komp_ = komp_temp
                    else:
                        komp_ = komp_.join(komp_temp, how = 'full', on = ['0','1'])
                        komp_right = komp_.filter(pl.col("0").is_null())
                        komp_left = komp_.filter(pl.col("0_right").is_null())
                        komp_inner = komp_.filter(pl.col('0').is_not_null() & pl.col('0_right').is_not_null())
                        # komp_ = pl.concat([komp_left, komp_right, komp_inner])
                        # print(komp_)
                        # komp_ = komp_.select(pl.col([mm for mm in komp_.columns if mm.find("_")<0]))
                        # print(komp_)

                        if komp_right.shape[0] > 0:
                            komp_right_stolp = ['0_right','1_right',ii,str(int(ii)+1)]
                            komp_right = komp_right.select(komp_right_stolp)
                            komp_right.columns = ['0','1','2','3']
                            komp_right_razlika_stolp = funkcije_at.razlika_seznamov(komp_right.columns, komp_.columns, nacin = 'komplement2')
                            if len(komp_right_razlika_stolp) > 0:
                                for ppp in komp_right_razlika_stolp:
                                    komp_right = komp_right.with_columns(pl.lit(None).alias(ppp))
                            komp_right = komp_right.cast(komp_.schema)
                        else:
                            pass
                        komp_ = pl.concat([komp_left, komp_right, komp_inner])
                        komp_ = komp_.select(pl.col([mm for mm in komp_.columns if mm.find("_")<0]))

            if komp_.shape[0] > 0:
                komp_.write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1 + "_.txt", separator = ';')
        else:
            pass


                # with open(mapa_upravicenost + key + '\\' + key + "_" + key2 + ".txt", 'r') as mm:
                    # mmr = mm.readlines()
                    # mm.close()
                # mmr_izberi = []
                # mmr_izberi.append(mmr[0])
                # pattern_izberi = r'(?:' + "|".join(value2) + r');-?\d+(?:\.\d+)?;' # Copilot
                # for m in mmr[1:]:
                    # parts = m.split(';')
                    # first_two = ";".join(parts[0:2])
                    # rezz = "".join(re.findall(re.escape(pattern_izberi),m))
                    # result = first_two + ";" +  rezz + "\n"
                    # if rezz == '':
                        # pass
                    # else:
                        # mmr_izberi.append(result)
                # with open(mapa_upravicenost + key + '\\' + key + "_" + key2 + ".txt", 'w') as ww:
                    # ww.write("".join(mmr_izberi))
                    # ww.close()
                # # skupaj.write_csv(mapa_upravicenost + key + '\\' + key + "_" + key1 + ".txt", separator = ';')

        izracunaj_stevilke(mapa = mapa_upravicenost + key + '\\', lokacija = key, resolucija = 25, celice = celice_, naredi_slike = True)
        zipaj_txt_v_mapi_in_brisi(mapa = mapa_upravicenost + '\\', lokacija = key)
        # for ii in os.listdir(mapa_upravicenost + key + '\\'):
            # if ii.find(".xlsx") > 0:
                # shutil.copy(mapa_upravicenost + key + '\\' + ii, mapa_upravicenost_temp + ii)
        t4 = time.time()
        print("         Äas {} {}s".format(key, t4-t3))
        t5 = time.time()
        print("     Äas skupaj {}s".format(t5 - t0))
        print("KONEC!")

if __name__ == '__main__':
    main()
