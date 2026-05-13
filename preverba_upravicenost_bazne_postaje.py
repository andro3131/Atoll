# -*- coding: utf-8 -*-
###########################################################
#   Skripta vrne upravičenost bazne postaje. Inputi so:
#   1. V Atolu naredimo filtering zone okoli bazne postaje ki nas zanima in izvozimo vsak layer posebej za tehnologije, ki so planirane. 
#   2. Potem izvozimo še skupno pokrivanje po tehnologijah (GSM, LTE, NR). Naredimo ascii exporte. 
#   Nato 
#
#
###########################################################

import re
import pandas as pd
import numpy as np
import time
import pyodbc
import matplotlib.pyplot as plt
import os
import pyodbc
import naredi_shp_za_112
import sql_denali_3794
import funkcije_at
from shapely.geometry import Point
import geopandas as gpd
import df_to_tiff
import manipulacija_slik

conn_atoll = pyodbc.connect('Driver={SQL Server};'
                      'Server=BPW-DENALI;'
                      'Database=atoll_d96;'
                      'UID=beribaze;'
                      'PWD=beribaze')


query_sites = """select * from atoll_d96.dbo.sites"""

# lokacija = 'SCVEN'



# ime = lokacija
# mapa = r"G:\Razno\LUNE 3500 FWA driven radio planning\\"
# mapa = r"G:\Razno\Analiza PRAKIT\\"
# mapa = r"G:\Razno\Analiza GIDRSK\\"
# # mapa = r"G:\Razno\Analiza PGRADI\\"
# mapa = r"G:\Razno\Analiza LOGATZ\\"
# mapa = "G:\\Razno\\Analiza " + lokacija + "\\"
# mapa = r"G:\Pokrivanja\Upravicenost_bazne_postaje\\" +  lokacija + "\\"
# tocke = r"G:\Geo podatki\Naslovi d96 31_08_2023\\naslovi_vsi.csv"
tocke = r"G:\Geo podatki\Naslovi_optika_baker_6_2_2024\\CRPE_Preb_Optika_Baker_D96_predelano.csv"
# fajl_pokrivanje = r"G:\Razno\\GSM LORA KTENET KPODBL KSTARH.txt"
# fajl_pokrivanje = r"G:\Razno\\4G_5G_NR PRAKIT.txt"
# fajl_pokrivanje = r"4G_5G_NR LUNE 3500 zacetno stanje.txt"



# scenarij = ['GSM900_obmocje_PRAKIT_[GSM].txt','LTE700_obmocje_PRAKIT_[LTE].txt','LTE1800_obmocje_PRAKIT_[LTE].txt','LTE800_obmocje_PRAKIT_[LTE].txt','LTE2100_obmocje_PRAKIT_[LTE].txt','NR700_obmocje_PRAKIT_[5G NR].txt', 'LTE_obmocje_PRAKIT_[LTE].txt', 'NR_obmocje_PRAKIT_[5G NR].txt']
# scenarij = ['GSM900_obmocje_PRAKIT_[GSM].txt']
# scenarij = ['LTE_obmocje_PRAKIT_[LTE].txt']
# scenarij = [i for i in os.listdir(mapa) if i.find("].txt") > 0]
# scenarij = ['GIDRSK_LTE_[LTE].txt','GIDRSK_GSM900_[GSM].txt','GIDRSK_NR_[5G NR].txt']
# scenarij = ['CSDRET_GSM_[GSM].txt','CSDRET_LTE_[LTE].txt', 'CSDRET_NR_[5G NR].txt']      # ,'CSDRET_LTE_800_[LTE].txt','CSDRET_LTE_1800_[LTE].txt'
# # scenarij = ['CSDRET_LTE_1800_[LTE].txt']      # ,'CSDRET_LTE_800_[LTE].txt',

# # scenarij = ['PGRADI_LTE_[LTE].txt','PGRADI_GSM900_[GSM].txt','PGRADI_NR_[5G NR].txt']
# # scenarij = ['LTE_obmocje_PRAKIT_[LTE].txt','GSM900_obmocje_PRAKIT_[GSM].txt','NR_obmocje_PRAKIT_[5G NR].txt']

# scenarij = ['LOGATZ_GSM_[GSM].txt','LOGATZ_LTE_[LTE].txt', 'LOGATZ_NR_[5G NR].txt']
# scenarij1 = [lokacija + '_GSM_[GSM].txt',lokacija + '_LTE_[LTE].txt', lokacija + '_NR_[5G NR].txt']
# scenarij = []
# for i in os.listdir(mapa):
    # if (i.find("].txt") >0) & (i in scenarij1):
        # scenarij.append(i)

nivoji_iot = [-90, -100, -105, -115, -125, -140]
nivoji_nr = [-75, -85, -95, -105, -108, -110, -115, -120, -125]
nivoji = list(range(-70, -126, -1))

# RAPLAT nastavitev za indoor in outdoor
gsm_indoor = -85
gsm_outdoor = -96
lte_indoor = -85
lte_outdoor = -108
nr_indoor = -95
nr_outdoor = -108

gsm_indoor = -85
gsm_outdoor = -96
lte_indoor = -85
lte_outdoor = -108
nr_indoor = -95
nr_outdoor = -108


def razdalja_med_lokacijami(n, lokacija = ''):
    """
    n = število lokacij v range-u
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


def glava(fr):
    with open(fr, "r") as fo:
        fr = fo.readlines()
        fo.close()
    sl = {}
    sl[fr[0].split("\t")[0]] = fr[0].strip("\n")
    sl[fr[1].split("\t")[0]] = fr[1].strip("\n")
    sl[fr[2].split("\t")[0]] = int(fr[2].split("\t")[1].strip("\n"))
    sl[fr[3].split("\t")[0]] = int(fr[3].split("\t")[1].strip("\n").replace(".",""))
    sl[fr[4].split("\t")[0]] = int(fr[4].split("\t")[1].strip("\n").replace(".",""))
    sl[fr[5].split("\t")[0]] = int(fr[5].split("\t")[1].strip("\n").replace(".",""))
    sl[fr[6].split("\t")[0]] = int(fr[6].split("\t")[1].strip("\n").replace(".",""))
    sl[fr[7].split("\t")[0]] = int(fr[7].split("\t")[1].strip("\n"))
    sl[fr[8].split("\t")[0]] = int(fr[8].split("\t")[1].strip("\n"))
    typeo = fr[0].strip("\n")
    timestamp = fr[1]
    resolution = int(fr[2].split("\t")[1].strip("\n"))
    xmin = int(fr[3].split("\t")[1].strip("\n").replace(".",""))
    xmax = int(fr[4].split("\t")[1].strip("\n").replace(".",""))
    ymin = int(fr[5].split("\t")[1].strip("\n").replace(".",""))
    ymax = int(fr[6].split("\t")[1].strip("\n").replace(".",""))
    x_num_pixels = int(fr[7].split("\t")[1].strip("\n"))
    y_num_pixels = int(fr[8].split("\t")[1].strip("\n"))
    return sl 

def beri_atoll_txt_export(atoll_txt_export_file_path):
    """
    Funkcija vrne podatke v glavi Atoll .txt exporta in vsebino v dveh filejih
    servers: katere serverje vrne. Če jih vrne več, jih je treba specificirati v seznamu. Npr: [1,2,5] -> vrne serverje 1, 2 in 5. 
    """
    with open(atoll_txt_export_file_path, "r") as fo:
        fo_read = fo.readlines()
        fo_read_str = [i.strip("\n") for i in fo_read]
        fo.close()
    gl = glava(atoll_txt_export_file_path)
    body = fo_read_str[11:len(fo_read_str)]
    body_df = pd.DataFrame(body)
    body_df = body_df[0].str.split(r"\t|;", expand = True)
    body_df[0] = body_df[0].str.replace(".","")
    body_df[1] = body_df[1].str.replace(".","")
    return gl, body_df

def beri_atoll_txt_export_1(atoll_txt_export_file_path):
    """
    Funkcija vrne podatke v glavi Atoll .txt exporta in vsebino v dveh filejih
    """
    file_open  = open(atoll_txt_export_file_path, 'r')
    file_read = file_open.readlines()
    file_open.close()
    file_header = file_read[0:11]
    file_ostalo = file_read[11:]
    # preštej ločila v vrstici, če je uprabljeno \t ga spremeni v podpičje
    file_podpicje = []
    for i in file_ostalo:
        file_podpicje.append(i.replace("\t",";").strip("\n"))
    # Preštej podpicja v vrsticah. Če jih je manj kot 13 jih dodaj toliko, da jih bo 13. 
    file_podp = []
    for i in file_podpicje:
        file_podp.append(i + (13 - i.count(";"))*";")
    t = pd.DataFrame()
    for j in list(range(14)):
        s = [i.split(";")[j] for i in file_podp]
        se = pd.Series(s)
        t[j] = se.values
    return t
    
def nivo(vrednost, nivoji):
    t = []
    ti = []
    v = min(nivoji)
    for i in nivoji:
        v = i - vrednost
        if v > 0:
            t.append(v)
            ti.append(i)
    if len(t) == 0:
        z = nivoji[0]
    else:
        z = ti[t.index(min(t))]
    return z

def naredi_best_server_kompozit(seznam):
    """
    Tehnologija: 'GSM','LTE','NR','NSA'
    """
    bs = pd.DataFrame()
    for i in seznam:
        temp = i[[0,1,2,3]]
        temp[3] = temp[3].astype(float)
        print(temp.shape)
        bs = pd.concat([bs, temp])
    bs = bs.reset_index(drop = True)
    print(bs)
    bs_ = bs.groupby([0,1])[3].max().reset_index()
    # bs_.to_csv(odlozisce +"AAAAAAAA.txt", index = False)
    print("==========")
    print(bs_)
    bs_ = bs_.merge(bs, how = 'inner', left_on = [0,1,3], right_on = [0,1,3])
    bs_['vrstni_red'] = bs_.sort_values(by = [0,1,2,3], ascending = [True, True, False, True]).groupby([0,1,3]).cumcount() + 1
    bs_ = bs_[bs_['vrstni_red'] == 1]
    bs_ = bs_[[0,1,2,3]]
    bs = bs[[0,1]].drop_duplicates()
    return bs_
    
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
        geometry=[Point(xy) for xy in zip(df["E"], df["N"])],
        crs="EPSG:3794"
    )
    return gdf_points.to_file(odlozisce + ime_fajla, driver='ESRI Shapefile')

def izracunaj_stevilke(mapa = '', lokacija = '', naredi_slike = False):
    tocke_df = pd.read_csv(tocke, sep = ";")
    tocke_df=  tocke_df[['E', 'N','HS_TID', 'HS_MID','PREB_STAL', 'PREB_ZAC','NASLOV', 'PRIKLJUCEK']]
    tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
    tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
    if tocke_df['E'].dtypes == float:
        pass
    else:
        tocke_df['E'] = tocke_df['E'].str.replace(",",".").astype(float)
        tocke_df['N'] = tocke_df['N'].str.replace(",",".").astype(float)
    tocke_df.dropna(inplace  =True)
    sites = funkcije_at.pd.read_sql(query_sites, conn_atoll)
    sites = sites[sites['NAME'] == lokacija]
    oddaljenost_BP_od_naslova = odd_bp_od_naslov(lokacija)

    sites_x1 = int(sites['LONGITUDE'].values[0]) - oddaljenost_BP_od_naslova
    sites_x2 = int(sites['LONGITUDE'].values[0]) + oddaljenost_BP_od_naslova
    sites_y1 = int(sites['LATITUDE'].values[0]) - oddaljenost_BP_od_naslova
    sites_y2 = int(sites['LATITUDE'].values[0]) + oddaljenost_BP_od_naslova
    tocke_df = tocke_df[(tocke_df['E'] > sites_x1) & (tocke_df['E'] < sites_x2) & (tocke_df['N'] > sites_y1) & (tocke_df['N'] < sites_y2)]

    # tocke_df['x_stot'] = (tocke_df['X'] - tocke_df['X']%100).astype(int)
    # tocke_df['y_stot'] = (tocke_df['Y'] - tocke_df['Y']%100).astype(int)

    scenarij1 = [lokacija + '_GSM_[GSM].txt',lokacija + '_LTE_[LTE].txt', lokacija + '_NR_[5G NR].txt']
    scenarij = []
    for i in os.listdir(mapa):
        if (i.find("].txt") >0) & (i in scenarij1):
            scenarij.append(i)


    temp_a = pd.DataFrame()
    temp_b = pd.DataFrame()
    kompozit_lte = []

    stevec = 0

    for k in scenarij:
        with open (mapa + k, "r") as ff:
            ffr = ff.readlines()
            ff.close()
        resoluc = int(int(ffr[2].strip("\n").split("\t")[1]))
        del(ffr)
        # lte800_df = beri_atoll_txt_export_1(mapa + k)
        lte800_df = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(mapa + k, n=6, vsebuje = [], header_list = False)
        print(lte800_df)
        print(mapa)
        print(k)
        # lte800_df = beri_atoll_txt_export(mapa + k)
        # lte800_df = lte800_df[1]
        lte800_df = lte800_df.replace('', np.nan)
        lte800_df[[0,1]] = lte800_df[[0,1]].astype(int)
        lte800_df = lte800_df[(lte800_df[0]> sites_x1) & (lte800_df[0] < sites_x2) & (lte800_df[1] > sites_y1) & (lte800_df[1] < sites_y2)]
        lte800_df[[3,5,7,9,11,13]] = lte800_df[[3,5,7,9,11,13]].astype(float)


        tocke_df = pd.read_csv(tocke, sep = ";")
        tocke_df=  tocke_df[['E', 'N','HS_TID', 'HS_MID','PREB_STAL', 'PREB_ZAC','NASLOV', 'PRIKLJUCEK']]
        tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
        tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
        if tocke_df['E'].dtypes == float:
            pass
        else:
            tocke_df['E'] = tocke_df['E'].str.replace(",",".").astype(float)
            tocke_df['N'] = tocke_df['N'].str.replace(",",".").astype(float)
        tocke_df.dropna(inplace  =True)
        tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E']%resoluc).astype(int)
        tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N']%resoluc).astype(int)
        tocke_df[['x_stot','y_stot']] = tocke_df[['x_stot','y_stot']].astype(int)

        if k.find("GSM") >= 0:
            teh = 'GSM'
            nivo_indoor = -85
            nivo_outdoor = -96
            nivo_fwa = -10
        elif k.find("LTE") >= 0:
            teh = 'LTE'
            nivo_indoor = -85
            nivo_outdoor = -108
            nivo_fwa = -95
        elif k.find("NR") >= 0:
            teh = 'NR'
            nivo_indoor = -95
            nivo_outdoor = -108
            nivo_fwa = -95
        else:
            teh = 'LTE'
            nivo_indoor = -85
            nivo_outdoor = -108
            nivo_fwa = -95


        lte800_df1 = lte800_df[[0,1,2,3]]   # source best server
        lte800_df1 = lte800_df1[lte800_df1[2].str.contains(lokacija)]
        lte800_df1_second = lte800_df[[0,1,4,5]].loc[lte800_df1[lte800_df1[2].str.contains(lokacija)].index].rename(columns = {4:2, 5:3}).dropna()  # source na mestu iskanega best server-ja
        lte800_df1_second[3] = lte800_df1_second[3].astype(float)
        lte800_df1_second_a = lte800_df[[0,1,6,7]].loc[lte800_df1_second[lte800_df1_second[2].str.contains(lokacija)].index].rename(columns = {6:2, 7:3}).dropna()
        lte800_df1_second = lte800_df1_second[~lte800_df1_second[2].str.contains(lokacija)]
        lte800_df1_second = pd.concat([lte800_df1_second, lte800_df1_second_a])

        lte800_df2 = lte800_df[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        lte800_df2 = lte800_df2[lte800_df2[2].str.contains(lokacija)]
        lte800_df2_second = lte800_df[[0,1,6,7]].loc[lte800_df2[lte800_df2[2].str.contains(lokacija)].index].rename(columns = {6:2, 7:3}).dropna()
        lte800_df2_second[3] = lte800_df2_second[3].astype(float)
        lte800_df2_second_a = lte800_df[[0,1,8,9]].loc[lte800_df2_second[lte800_df2_second[2].str.contains(lokacija)].index].rename(columns = {8:2, 9:3}).dropna()
        lte800_df2_second = lte800_df2_second[~lte800_df2_second[2].str.contains(lokacija)]
        lte800_df2_second = pd.concat([lte800_df2_second, lte800_df2_second_a])

        lte800_df_sec = pd.concat([lte800_df1, lte800_df2])
        lte800_df_second = pd.concat([lte800_df1_second, lte800_df2_second])

        lte800_df_sec = lte800_df_sec.dropna()
        lte800_df_sec = lte800_df_sec[lte800_df_sec[2].str.contains(lokacija)]
        lte800_df_sec[3] = lte800_df_sec[3].astype(float)
        lte800_dfa_sec = lte800_df_sec.groupby([0,1]).agg({3:'max', 2:list}).reset_index()
        lte800_dfa_sec[6] = lte800_dfa_sec[2].str[0]
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

        presek__ = tocke_df.merge(lte800_df1, how = 'right', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek__.drop(columns = [0,1], inplace = True)
        presek__.rename(columns = {2:'2_prim',3:'3_prim'}, inplace = True)
        presek__ = presek__.merge(lte800_df1_second, how = 'right', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek__.drop(columns = [0,1], inplace = True)
        presek__.rename(columns = {2:'2_ostali',3:'3_ostali'}, inplace = True)
        presek__ = presek__.merge(lte800_dfa_sec, how = 'right', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek__.drop(columns = [0,1], inplace = True)
        presek__.rename(columns = {2:'2_sec',3:'3_sec'}, inplace = True)
        presek__ = presek__.merge(lte800_dfa_second, how = 'right', left_on = ['x_stot','y_stot'], right_on = [0,1])
        presek__.drop(columns = [0,1], inplace = True)
        presek__.rename(columns = {2:'2_sec_ostali',3:'3_sec_ostali'}, inplace = True)


        presek['rangiranje'] = 0
        n = 0
        for m in nivoji:
            presek.loc[(presek['3_sec'] < n)&(presek['3_sec'] >= m), 'rangiranje'] = m
            n = m

        presek__['rangiranje'] = 0
        n = 0
        for m in nivoji:
            presek__.loc[(presek__['3_sec'] < n)&(presek__['3_sec'] >= m), 'rangiranje'] = m
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

        presek1__ = presek__[col]
        presek1__ = presek1__.dropna(subset = ['2_prim'], how = 'all')
        presek2__ = presek__[col1]
        presek2__ = presek2__.dropna(subset = ['2_sec'], how = 'all')


        stevec2 = 0
        for i in presek2['2_sec'].drop_duplicates().tolist():
            # presekk = presek2[presek2['2_sec'] == i]
            
            # t_indoor = presekk[presekk['rangiranje'] >= nivo_indoor]
            # t_outdoor = presekk[presekk['rangiranje'] >= nivo_outdoor]
            # temp.loc[stevec + stevec2, 'scenarij'] = k
            # temp.loc[stevec + stevec2, 'celica'] = i
            # temp.loc[stevec + stevec2, 'Naslovi_second'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Prebivalci_second'] = presekk['PREB_STAL'].sum()
            # temp.loc[stevec + stevec2, 'Naslovi_second_indoor'] = t_indoor['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Naslovi_second_outdoor'] = t_outdoor['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Prebivalci_second_indoor'] = t_indoor['PREB_STAL'].sum()
            # temp.loc[stevec + stevec2, 'Prebivalci_second_outdoor'] = t_outdoor['PREB_STAL'].sum()
            # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second'] = presekk['PREB_STAL'].sum()
            # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second_indoor'] = t_indoor['HS_MID'][(t_indoor['2_sec_ostali'].isna()) | ((t_indoor['3_sec_ostali'] <= nivo_indoor))].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second_indoor'] = t_indoor['PREB_STAL'][(t_indoor['2_sec_ostali'].isna()) | ((t_indoor['3_sec_ostali'] <= nivo_indoor) )].sum()
            # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second_outdoor'] = t_outdoor['HS_MID'][(t_outdoor['2_sec_ostali'].isna()) | ((t_outdoor['3_sec_ostali'] <= nivo_outdoor) )].drop_duplicates().shape[0]
            # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second_outdoor'] = t_outdoor['PREB_STAL'][(t_outdoor['2_sec_ostali'].isna()) | ((t_outdoor['3_sec_ostali'] <= nivo_outdoor))].sum()
            stevec2 = stevec2 + 1

            
        stevec1 = 0
        for i in presek1['2_prim'].drop_duplicates().tolist():
            # presekk = presek1[presek1['2_prim'] == i]
            # stevecc = temp[temp['celica'] == i].index[0]
            # t_indoor = presekk[presekk['rangiranje'] >= nivo_indoor]
            # t_outdoor = presekk[presekk['rangiranje'] >= nivo_outdoor]
            # temp.loc[stevecc, 'scenarij'] = k
            # temp.loc[stevecc, 'celica'] = i
            # temp.loc[stevecc, 'Naslovi_best'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Prebivalci_best'] = presekk['PREB_STAL'].sum()
            # temp.loc[stevecc, 'Naslovi_best_indoor'] = t_indoor['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Naslovi_best_outdoor'] = t_outdoor['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Prebivalci_best_indoor'] = t_indoor['PREB_STAL'].sum()
            # temp.loc[stevecc, 'Prebivalci_best_outdoor'] = t_outdoor['PREB_STAL'].sum()
            # temp.loc[stevecc, 'Izboljsava_Naslovi_best'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Izboljsava_Prebivalci_best'] = presekk['PREB_STAL'].sum()
            # temp.loc[stevecc, 'Izboljsava_Naslovi_best_indoor'] = t_indoor['HS_MID'][(t_indoor['2_ostali'].isna()) | ((t_indoor['3_ostali'] <= nivo_indoor))].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Izboljsava_Prebivalci_best_indoor'] = t_indoor['PREB_STAL'][(t_indoor['2_ostali'].isna()) | ((t_indoor['3_ostali'] <= nivo_indoor))].sum()
            # temp.loc[stevecc, 'Izboljsava_Naslovi_best_outdoor'] = t_outdoor['HS_MID'][(t_outdoor['2_ostali'].isna()) | ((t_outdoor['3_ostali'] <= nivo_outdoor) )].drop_duplicates().shape[0]
            # temp.loc[stevecc, 'Izboljsava_Prebivalci_best_outdoor'] = t_outdoor['PREB_STAL'][(t_outdoor['2_ostali'].isna()) | ((t_outdoor['3_ostali'] <= nivo_outdoor) )].sum()
            
            
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
        if (naredi_slike == True) & ((k.find('LTE') >= 0) | (k.find('NR') >=0)):
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

    # PNG generacija (vse + zoom variant za vsako tehnologijo) iz ze ustvarjenih TIF+SHP.
    # Lazy import, da preverba ne pada ce PNG dependencies (contextily, pip-system-certs ...)
    # niso na voljo. Failure tukaj ne sme ubiti pipelina - analiza Excel in TIF+SHP so ze varni.
    if naredi_slike:
        try:
            import narisi_pokrivanje
            narisi_pokrivanje.obdelaj_lokacijo(lokacija, slike_dir=mapa + "Slike\\")
        except Exception as e:
            print(f"OPOZORILO: PNG generacija ni uspela za {lokacija}: {e}")
            print(f"  TIF+SHP+analiza so OK. PNG-je lahko rocno re-generiras z: py -3.10 narisi_pokrivanje.py {lokacija}")

    stolpci_koncno = ['scenarij',	'celica',	'Izboljsava_Naslovi_best',	'Izboljsava_Prebivalci_best',	'Novi_Naslovi_best_indoor',	'Novi_Prebivalci_best_indoor'	,'Novi_Naslovi_best_outdoor',	'Novi_Prebivalci_best_outdoor',	'Izboljsava_Naslovi_best_indoor'	,'Izboljsava_Prebivalci_best_indoor'	,'Izboljsava_Naslovi_best_outdoor'	,'Izboljsava_Prebivalci_best_outdoor'	,'Naslovi_best_FWA potencial','Naslovi_best_FWA_izboljsava','Izboljsava_Naslovi_second',	'Izboljsava_Prebivalci_second'	,'Izboljsava_Naslovi_second_indoor'	,'Novi_Naslovi_second_indoor'	,'Novi_Prebivalci_second_indoor'	,'Novi_Naslovi_second_outdoor',	'Novi_Prebivalci_second_outdoor'	,'Izboljsava_Prebivalci_second_indoor',	'Izboljsava_Naslovi_second_outdoor',	'Izboljsava_Prebivalci_second_outdoor',	'Naslovi_second_FWA_redundanca','Naslovi_second_FWA_izboljsava']
    temp_a[stolpci_koncno][temp_a['celica'] == 'Skupaj'].to_excel(mapa + lokacija  + "_analiza.xlsx", index = False)
    return 0

def brisi_izvzeto(vhodni_seznam, celice_brisi):
    
    pattern_brisi = "|".join([i + ";-[0-9]*.?[0-9]*;{0,1}" for i in celice_brisi])
    pattern_brisi_prazna_vrstica = "[0-9]{5,7};[0-9]{4,6};+\\n"
    mmr_brisanje = [re.sub(";\\n","\\n",x) for x in [x for x in [re.sub(pattern_brisi,"",x) for x in vhodni_seznam] if not re.search(pattern_brisi_prazna_vrstica,x)]]
    return mmr_brisanje

    
# def izracunaj_stevilke2(mapa = '', lokacija = ''):
    # tocke_df = pd.read_csv(tocke, sep = ";")
    # tocke_df=  tocke_df[['E', 'N','HS_TID', 'HS_MID','PREB_STAL', 'PREB_ZAC','NASLOV', 'PRIKLJUCEK']]
    # tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
    # tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
    # if tocke_df['E'].dtypes == float:
        # pass
    # else:
        # tocke_df['E'] = tocke_df['E'].str.replace(",",".").astype(float)
        # tocke_df['N'] = tocke_df['N'].str.replace(",",".").astype(float)
    # tocke_df.dropna(inplace  =True)
    # sites = funkcije_at.pd.read_sql(query_sites, conn_atoll)
    # sites = sites[sites['NAME'] == lokacija]
    # oddaljenost_BP_od_naslova = odd_bp_od_naslov(lokacija)

    # sites_x1 = int(sites['LONGITUDE'].values[0]) - oddaljenost_BP_od_naslova
    # sites_x2 = int(sites['LONGITUDE'].values[0]) + oddaljenost_BP_od_naslova
    # sites_y1 = int(sites['LATITUDE'].values[0]) - oddaljenost_BP_od_naslova
    # sites_y2 = int(sites['LATITUDE'].values[0]) + oddaljenost_BP_od_naslova
    # tocke_df = tocke_df[(tocke_df['E'] > sites_x1) & (tocke_df['E'] < sites_x2) & (tocke_df['N'] > sites_y1) & (tocke_df['N'] < sites_y2)]

    # # tocke_df['x_stot'] = (tocke_df['X'] - tocke_df['X']%100).astype(int)
    # # tocke_df['y_stot'] = (tocke_df['Y'] - tocke_df['Y']%100).astype(int)

    # scenarij1 = [lokacija + '_GSM_[GSM].txt',lokacija + '_LTE_[LTE].txt', lokacija + '_NR_[5G NR].txt']
    # scenarij = []
    # for i in os.listdir(mapa):
        # if (i.find("].txt") >0) & (i in scenarij1):
            # scenarij.append(i)


    # temp_a = pd.DataFrame()
    # temp_b = pd.DataFrame()
    # kompozit_lte = []

    # stevec = 0
    

    
    # for k in scenarij:
        # with open (mapa + k, "r") as ff:
            # ffr = ff.readlines()
            # ff.close()
        # resoluc = int(int(ffr[2].strip("\n").split("\t")[1]))
        
        # ffr1 = brisi_izvzeto(vhodni_seznam = ffr[11:], celice_brisi = vse_cel)
        # vse_brez = pd.DataFrame(ffr1)
        # del(ffr)
        # vse = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(mapa + k, n=6, vsebuje = [], header_list = False)
        # vse = vse.replace('', np.nan)
        # vse[[0,1]] = vse[[0,1]].astype(int)
        # vse = vse[(vse[0]> sites_x1) & (vse[0] < sites_x2) & (vse[1] > sites_y1) & (vse[1] < sites_y2)]
        # vse[[3,5,7,9,11,13]] = vse[[3,5,7,9,11,13]].astype(float)


        # tocke_df = pd.read_csv(tocke, sep = ";")
        # tocke_df=  tocke_df[['E', 'N','HS_TID', 'HS_MID','PREB_STAL', 'PREB_ZAC','NASLOV', 'PRIKLJUCEK']]
        # tocke_df['PREB_STAL'] = tocke_df['PREB_STAL'].fillna(0)
        # tocke_df['PREB_ZAC'] = tocke_df['PREB_ZAC'].fillna(0)
        # if tocke_df['E'].dtypes == float:
            # pass
        # else:
            # tocke_df['E'] = tocke_df['E'].str.replace(",",".").astype(float)
            # tocke_df['N'] = tocke_df['N'].str.replace(",",".").astype(float)
        # tocke_df.dropna(inplace  =True)
        # tocke_df['x_stot'] = (tocke_df['E'] - tocke_df['E']%resoluc).astype(int)
        # tocke_df['y_stot'] = (tocke_df['N'] - tocke_df['N']%resoluc).astype(int)
        # tocke_df[['x_stot','y_stot']] = tocke_df[['x_stot','y_stot']].astype(int)

        # if k.find("GSM") >= 0:
            # teh = 'GSM'
            # nivo_indoor = -85
            # nivo_outdoor = -96
            # nivo_fwa = -30
        # elif k.find("LTE") >= 0:
            # teh = 'LTE'
            # nivo_indoor = -85
            # nivo_outdoor = -108
            # nivo_fwa = -100
        # elif k.find("NR") >= 0:
            # teh = 'NR'
            # nivo_indoor = -95
            # nivo_outdoor = -108
            # nivo_fwa = -100
        # else:
            # teh = 'LTE'
            # nivo_indoor = -85
            # nivo_outdoor = -108
            # nivo_fwa = -100

        # vse_best = vse[vse[2].isin(vse_cel)]
        # vse_best = vse_best[[0,1,2,3]]
        # vse_best_merge = vse_best.merge(vse_brez[[0,1,2,3]].dropna(), how = left, left_on = [0,1], right_on = [0,1])
        
        # vse_second = vse[((vse[4].isin(vse_cel)) & (~vse.index.isin(vse_best.index.tolist())))]
        # vse_second = vse_second[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        # vse_second_merge = vse_second.merge(vse_brez[[0,1,4,5]].dropna(), how = left, left_on = [0,1], right_on = [0,1])
        
        
        # lte800_df1 = lte800_df[[0,1,2,3]]   # source best server
        # lte800_df1 = lte800_df1[lte800_df1[2].str.contains(lokacija)]
        # lte800_df1_second = lte800_df[[0,1,4,5]].loc[lte800_df1[lte800_df1[2].str.contains(lokacija)].index].rename(columns = {4:2, 5:3}).dropna()  # source na mestu iskanega best server-ja
        # lte800_df1_second[3] = lte800_df1_second[3].astype(float)
        # lte800_df1_second_a = lte800_df[[0,1,6,7]].loc[lte800_df1_second[lte800_df1_second[2].str.contains(lokacija)].index].rename(columns = {6:2, 7:3}).dropna()
        # lte800_df1_second = lte800_df1_second[~lte800_df1_second[2].str.contains(lokacija)]
        # lte800_df1_second = pd.concat([lte800_df1_second, lte800_df1_second_a])

        # lte800_df2 = lte800_df[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        # lte800_df2 = lte800_df2[lte800_df2[2].str.contains(lokacija)]
        # lte800_df2_second = lte800_df[[0,1,6,7]].loc[lte800_df2[lte800_df2[2].str.contains(lokacija)].index].rename(columns = {6:2, 7:3}).dropna()
        # lte800_df2_second[3] = lte800_df2_second[3].astype(float)
        # lte800_df2_second_a = lte800_df[[0,1,8,9]].loc[lte800_df2_second[lte800_df2_second[2].str.contains(lokacija)].index].rename(columns = {8:2, 9:3}).dropna()
        # lte800_df2_second = lte800_df2_second[~lte800_df2_second[2].str.contains(lokacija)]
        # lte800_df2_second = pd.concat([lte800_df2_second, lte800_df2_second_a])

        # lte800_df_sec = pd.concat([lte800_df1, lte800_df2])
        # lte800_df_second = pd.concat([lte800_df1_second, lte800_df2_second])

        # lte800_df_sec = lte800_df_sec.dropna()
        # lte800_df_sec = lte800_df_sec[lte800_df_sec[2].str.contains(lokacija)]
        # lte800_df_sec[3] = lte800_df_sec[3].astype(float)
        # lte800_dfa_sec = lte800_df_sec.groupby([0,1]).agg({3:'max', 2:list}).reset_index()
        # lte800_dfa_sec[6] = lte800_dfa_sec[2].str[0]
        # lte800_dfa_sec.drop(columns = 2, inplace = True)
        # lte800_dfa_sec.rename(columns = {6:2}, inplace = True)
        # lte800_dfa_sec = lte800_dfa_sec[[0,1,2,3]]  # source second best server
        # lte800_dfa_sec.columns = [0,1,2,3]

        # lte800_df_second = lte800_df_second.dropna()
        # lte800_df_second[3] = lte800_df_second[3].astype(float)
        # lte800_dfa_second = lte800_df_second.groupby([0,1]).agg({3:'max', 2:list}).reset_index()
        # lte800_dfa_second[6] = lte800_dfa_second[2].str[0]
        # lte800_dfa_second.drop(columns = 2, inplace = True)
        # lte800_dfa_second.rename(columns = {6:2}, inplace = True)
        # lte800_dfa_second = lte800_dfa_second[[0,1,2,3]]    # source na mestu iskanega second best server-ja
        # lte800_dfa_second.columns = [0,1,2,3]

        # # lte800_df2_ = lte800_df[[0,1,4,5]].rename(columns = {4:2, 5:3}).dropna()
        # # lte800_df3_ = lte800_df[[0,1,6,7]].rename(columns = {6:2, 7:3}).dropna()
        # # lte800_df4_ = lte800_df[[0,1,8,9]].rename(columns = {8:2, 9:3}).dropna()
        # # lte800_df5_ = lte800_df[[0,1,10,11]].rename(columns = {10:2, 11:3}).dropna()
        # # lte800_df6_ = lte800_df[[0,1,12,13]].rename(columns = {12:2, 13:3}).dropna()
        # # lte800_vse = pd.concat([lte800_df1, lte800_df2_, lte800_df3_, lte800_df4_, lte800_df5_, lte800_df6_]).drop_duplicates().dropna()

        # omejitev_tock_df = pd.concat([lte800_df1[[0,1]], lte800_df1_second[[0,1]], lte800_dfa_sec[[0,1]], lte800_dfa_second[[0,1]]]).drop_duplicates()
        # # omejitev_tock_df = lte800_vse[[0,1]].drop_duplicates()
        # tocke_df = tocke_df.merge(omejitev_tock_df, how = 'inner', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # tocke_df.drop(columns = [0,1], inplace = True)
        # # tocke_df_columns = tocke_df.columns.tolist()

        # presek = tocke_df.merge(lte800_df1, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # presek.drop(columns = [0,1], inplace = True)
        # presek.rename(columns = {2:'2_prim',3:'3_prim'}, inplace = True)
        # presek = presek.merge(lte800_df1_second, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # presek.drop(columns = [0,1], inplace = True)
        # presek.rename(columns = {2:'2_ostali',3:'3_ostali'}, inplace = True)
        # presek = presek.merge(lte800_dfa_sec, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # presek.drop(columns = [0,1], inplace = True)
        # presek.rename(columns = {2:'2_sec',3:'3_sec'}, inplace = True)
        # presek = presek.merge(lte800_dfa_second, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # presek.drop(columns = [0,1], inplace = True)
        # presek.rename(columns = {2:'2_sec_ostali',3:'3_sec_ostali'}, inplace = True)
        # # presek = presek.merge(lte800_vse, how = 'left', left_on = ['x_stot','y_stot'], right_on = [0,1])
        # # presek.drop(columns = [0,1], inplace = True)
        # # presek.rename(columns = {2:'2_vsi',3:'3_vsi'}, inplace = True)



        # presek['rangiranje'] = 0
        # n = 0
        # for m in nivoji:
            # presek.loc[(presek['3_sec'] < n)&(presek['3_sec'] >= m), 'rangiranje'] = m
            # n = m

        # seznam = ['scenarij','celica','rangiranje','Naslovi_best','Prebivalci_best','Naslovi_best_indoor','Naslovi_best_outdoor',
            # 'Prebivalci_best_indoor','Prebivalci_best_outdoor','Izboljsava_Naslovi_best','Izboljsava_Prebivalci_best',
            # 'Novi_Naslovi_best_indoor','Novi_Prebivalci_best_indoor','Novi_Naslovi_best_outdoor','Novi_Prebivalci_best_outdoor',
            # 'Izboljsava_Naslovi_best_indoor', 'Izboljsava_Prebivalci_best_indoor', 'Izboljsava_Naslovi_best_outdoor', 'Izboljsava_Prebivalci_best_outdoor',
            # 'Naslovi_best_FWA potencial','Naslovi_best_optika', 'Naslovi_best_neoptika', 
            # 'Naslovi_second','Prebivalci_second','Naslovi_second_indoor','Naslovi_second_outdoor', 'Prebivalci_second_indoor',
            # 'Prebivalci_second_outdoor', 'Izboljsava_Naslovi_second','Izboljsava_Prebivalci_second','Izboljsava_Naslovi_second_indoor',
            # 'Novi_Naslovi_second_indoor', 'Novi_Prebivalci_second_indoor', 'Novi_Naslovi_second_outdoor', 'Novi_Prebivalci_second_outdoor',
            # 'Izboljsava_Prebivalci_second_indoor','Izboljsava_Naslovi_second_outdoor','Izboljsava_Prebivalci_second_outdoor',
            # 'Naslovi_second_FWA_redundanca','Naslovi_second_optika', 'Naslovi_second_neoptika']


        # temp = pd.DataFrame(columns = seznam)
        # # 1. primer best server
        # col = tocke_df.columns.tolist()
        # col.append('2_prim')
        # col.append('3_prim')
        # col.append('2_ostali')
        # col.append('3_ostali')
        # col.append('rangiranje')

        # col1 = tocke_df.columns.tolist()
        # col1.append('2_sec')
        # col1.append('3_sec')
        # col1.append('2_sec_ostali')
        # col1.append('3_sec_ostali')
        # col1.append('rangiranje')


        # presek1 = presek[col]
        # presek1 = presek1.dropna(subset = ['2_prim'], how = 'all')
        # presek2 = presek[col1]
        # presek2 = presek2.dropna(subset = ['2_sec'], how = 'all')

          
        # stevec2 = 0  
        # for i in presek2['2_sec'].drop_duplicates().tolist():
            # # presekk = presek2[presek2['2_sec'] == i]
            
            # # t_indoor = presekk[presekk['rangiranje'] >= nivo_indoor]
            # # t_outdoor = presekk[presekk['rangiranje'] >= nivo_outdoor]
            # # temp.loc[stevec + stevec2, 'scenarij'] = k
            # # temp.loc[stevec + stevec2, 'celica'] = i
            # # temp.loc[stevec + stevec2, 'Naslovi_second'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Prebivalci_second'] = presekk['PREB_STAL'].sum()
            # # temp.loc[stevec + stevec2, 'Naslovi_second_indoor'] = t_indoor['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Naslovi_second_outdoor'] = t_outdoor['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Prebivalci_second_indoor'] = t_indoor['PREB_STAL'].sum()
            # # temp.loc[stevec + stevec2, 'Prebivalci_second_outdoor'] = t_outdoor['PREB_STAL'].sum()
            # # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second'] = presekk['PREB_STAL'].sum()
            # # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second_indoor'] = t_indoor['HS_MID'][(t_indoor['2_sec_ostali'].isna()) | ((t_indoor['3_sec_ostali'] <= nivo_indoor))].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second_indoor'] = t_indoor['PREB_STAL'][(t_indoor['2_sec_ostali'].isna()) | ((t_indoor['3_sec_ostali'] <= nivo_indoor) )].sum()
            # # temp.loc[stevec + stevec2, 'Izboljsava_Naslovi_second_outdoor'] = t_outdoor['HS_MID'][(t_outdoor['2_sec_ostali'].isna()) | ((t_outdoor['3_sec_ostali'] <= nivo_outdoor) )].drop_duplicates().shape[0]
            # # temp.loc[stevec + stevec2, 'Izboljsava_Prebivalci_second_outdoor'] = t_outdoor['PREB_STAL'][(t_outdoor['2_sec_ostali'].isna()) | ((t_outdoor['3_sec_ostali'] <= nivo_outdoor))].sum()
            # stevec2 = stevec2 + 1

            
        # stevec1 = 0
        # for i in presek1['2_prim'].drop_duplicates().tolist():
            # # presekk = presek1[presek1['2_prim'] == i]
            # # stevecc = temp[temp['celica'] == i].index[0]
            # # t_indoor = presekk[presekk['rangiranje'] >= nivo_indoor]
            # # t_outdoor = presekk[presekk['rangiranje'] >= nivo_outdoor]
            # # temp.loc[stevecc, 'scenarij'] = k
            # # temp.loc[stevecc, 'celica'] = i
            # # temp.loc[stevecc, 'Naslovi_best'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Prebivalci_best'] = presekk['PREB_STAL'].sum()
            # # temp.loc[stevecc, 'Naslovi_best_indoor'] = t_indoor['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Naslovi_best_outdoor'] = t_outdoor['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Prebivalci_best_indoor'] = t_indoor['PREB_STAL'].sum()
            # # temp.loc[stevecc, 'Prebivalci_best_outdoor'] = t_outdoor['PREB_STAL'].sum()
            # # temp.loc[stevecc, 'Izboljsava_Naslovi_best'] = presekk['HS_MID'].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Izboljsava_Prebivalci_best'] = presekk['PREB_STAL'].sum()
            # # temp.loc[stevecc, 'Izboljsava_Naslovi_best_indoor'] = t_indoor['HS_MID'][(t_indoor['2_ostali'].isna()) | ((t_indoor['3_ostali'] <= nivo_indoor))].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Izboljsava_Prebivalci_best_indoor'] = t_indoor['PREB_STAL'][(t_indoor['2_ostali'].isna()) | ((t_indoor['3_ostali'] <= nivo_indoor))].sum()
            # # temp.loc[stevecc, 'Izboljsava_Naslovi_best_outdoor'] = t_outdoor['HS_MID'][(t_outdoor['2_ostali'].isna()) | ((t_outdoor['3_ostali'] <= nivo_outdoor) )].drop_duplicates().shape[0]
            # # temp.loc[stevecc, 'Izboljsava_Prebivalci_best_outdoor'] = t_outdoor['PREB_STAL'][(t_outdoor['2_ostali'].isna()) | ((t_outdoor['3_ostali'] <= nivo_outdoor) )].sum()
            
            
            # stevec = stevec + 1 + stevec2

        # temp.loc[stevec, 'scenarij'] = k
        # temp.loc[stevec, 'celica'] = 'Skupaj'
        # temp.loc[stevec, 'Naslovi_best'] = presek1['HS_MID'].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Prebivalci_best'] = presek1['PREB_STAL'].sum()
        # temp.loc[stevec, 'Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor)].sum()
        # temp.loc[stevec, 'Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor)].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_best'] = presek1['HS_MID'].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_best'] = presek1['PREB_STAL'].sum()
        # temp.loc[stevec, 'Novi_Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_ostali'] < nivo_indoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Novi_Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_ostali'] < nivo_indoor)].sum()
        # temp.loc[stevec, 'Novi_Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_ostali'] < nivo_outdoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Novi_Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_ostali'] < nivo_outdoor)].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_best_indoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_prim'] > presek1['3_ostali'])].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_best_indoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_indoor) & (presek1['3_prim'] > presek1['3_ostali'])].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_best_outdoor'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_prim'] > presek1['3_ostali'])].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_best_outdoor'] = presek1['PREB_STAL'][(presek1['3_prim'] >= nivo_outdoor) & (presek1['3_prim'] > presek1['3_ostali'])].sum()
        # temp.loc[stevec, 'Naslovi_best_FWA potencial'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] == 'BAKER')].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_best_optika'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] == 'OPTIKA')].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_best_neoptika'] = presek1['HS_MID'][(presek1['3_prim'] >= nivo_fwa) & (presek1['PRIKLJUCEK'] != 'OPTIKA')].drop_duplicates().shape[0]




        # temp.loc[stevec, 'Naslovi_second'] = presek2['HS_MID'].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Prebivalci_second'] = presek2['PREB_STAL'].sum()
        # temp.loc[stevec, 'Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor)].sum()
        # temp.loc[stevec, 'Prebivalci_second_outdoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor)].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_second'] = presek2['HS_MID'].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_second'] = presek2['PREB_STAL'].sum()
        # temp.loc[stevec, 'Novi_Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec_ostali'] < nivo_indoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Novi_Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec_ostali'] < nivo_indoor)].sum()
        # temp.loc[stevec, 'Novi_Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec_ostali'] < nivo_outdoor)].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Novi_Prebivalci_second_outdoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec_ostali'] < nivo_outdoor)].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_second_indoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_second_indoor'] = presek2['PREB_STAL'][(presek2['3_sec'] >= nivo_indoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].sum()
        # temp.loc[stevec, 'Izboljsava_Naslovi_second_outdoor'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Izboljsava_Prebivalci_second_outdoor'] = presek1['PREB_STAL'][(presek2['3_sec'] >= nivo_outdoor) & (presek2['3_sec'] > presek2['3_sec_ostali'])].sum()
        # temp.loc[stevec, 'Naslovi_second_FWA_redundanca'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] == 'BAKER')].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_second_optika'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] == 'OPTIKA')].drop_duplicates().shape[0]
        # temp.loc[stevec, 'Naslovi_second_neoptika'] = presek2['HS_MID'][(presek2['3_sec'] >= nivo_fwa) & (presek2['PRIKLJUCEK'] != 'OPTIKA')].drop_duplicates().shape[0]



        # stevec = stevec + 1        
        # temp_a = pd.concat([temp_a, temp])

    # stolpci_koncno = ['scenarij',	'celica',	'Izboljsava_Naslovi_best',	'Izboljsava_Prebivalci_best',	'Novi_Naslovi_best_indoor',	'Novi_Prebivalci_best_indoor'	,'Novi_Naslovi_best_outdoor',	'Novi_Prebivalci_best_outdoor',	'Izboljsava_Naslovi_best_indoor'	,'Izboljsava_Prebivalci_best_indoor'	,'Izboljsava_Naslovi_best_outdoor'	,'Izboljsava_Prebivalci_best_outdoor'	,'Naslovi_best_FWA potencial'	,'Izboljsava_Naslovi_second',	'Izboljsava_Prebivalci_second'	,'Izboljsava_Naslovi_second_indoor'	,'Novi_Naslovi_second_indoor'	,'Novi_Prebivalci_second_indoor'	,'Novi_Naslovi_second_outdoor',	'Novi_Prebivalci_second_outdoor'	,'Izboljsava_Prebivalci_second_indoor',	'Izboljsava_Naslovi_second_outdoor',	'Izboljsava_Prebivalci_second_outdoor',	'Naslovi_second_FWA_redundanca']
    # temp_a[stolpci_koncno][temp_a['celica'] == 'Skupaj'].to_excel(mapa + lokacija  + "_analiza.xlsx", index = False)       
    # return 0   