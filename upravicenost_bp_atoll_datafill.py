
# -*- coding: utf-8 -*-

import funkcije_at
import pyodbc
import pandas as pd
import subprocess
import export_script_3794_reporting
import os
# import preverba_upravicenost_bazne_postaje
import zipfile
import shutil
import sql_denali_3794
import sql_atoll_3794
import re

########################
#   1. Preverimo če lokacija obstaja v Denali:
#       - Če lokacija ni definirana, izstopimo
#       - Če lokacija obstaja v Denali in ne v ATOLL-U jo skreiramo v atollu
#       - če celice niso definirane v denali, izstopimo
#       - če so celice definirafe v denali in ne v atollu, jih skreiramo v atollu. Če jih ni v denali in so v atollu , jih v atollu deaktivoramo. 
#
#   2. Vhodni podatek je slovar, kjer je ključ lokacije, za katero želimo izračunati upravičenost, vrednost pa morebitna predhodna lokacija (nadomestna). Primer:  vhodni_podatki = {'NVTREB':'NRMAX'}. NVTREB je nadomestna #      lokacija za NRMAX, Če ni nadomestna lokacija, damo v vrednost ''



# planer01 migracija: vse G:\Avtomatika\... -> D:\Atoll_projects_planer01\Avtomatika\...
odlozisce_novo = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Novo\\"
odlozisce_spremeni = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Spremeni\\"
odlozisce_brisi = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\Brisi\\"
odlozisce_filter = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Upravicenost_bazne_postaje\\"


# seznam_lokacij = ['CSDRET','LOGATZ','PSMARP','ALITOS']
loks_ = [['CTUNCO'],
['LTUHIL'],
['NKANIZ'],
['KPOLJA'],
['TGAMBE'],
['PRAKIT'],
['LOGATO'],
['NCRMOT'],
['MPTZAB'],
['LPOLIG'],
['NSLANC'],
['LKALDO'],
['PKOBOL'],
['KBELCA'],
['NCRNEV'],
['LOBOLN']] # ,'TURJE','SKOBIL' ['KLOKCE']
loks_ = [['CSREB']]


vhodni_podatki = {
'LIG':'',
'CMONT':'',
'LKAMG':'',
'MGAJ':'',
'ACERNE':'',
'LAVRI':'',
'CGOTOV':'',
'AKASEL':'',
'AKERS':'',
'APRZAN':'',
'AKOZAR':'',
'SPETR':'',
'ATOPLA':'',
'ATOTRA':'',
'ASMART':'',
'SOBJUG':'',
'GNEBLO':'',
'LMENVR':'',
'GBATE':'',
'GBATU':'',
'KPRED':'',
'MGRAJE':'',
'KRAVNI':'',
'MBETNA':'',
'STROPO':'',
'LTRZV':'',
'CTOMAZ':'',
'MIKLAV':'',
'GMIRS':'',
'CVELTU':'',
'KBESNI':'',
'CSMASI':'',
'WMEZIC':'',
'CSMARD':'',
'LBRST':'',
'AVARNO':'',
'AHOTLI':'',
'KVITRA':'',
'KNAKLO':'',
'AHALA':'',
'ABAZEN':'',
'ASTOZI':'',
'ASTADT':'',
'CPRIMO':'',
'APOPTV':''}

vhodni_podatki = {'KVITRA':''}


propag_model_dict= {'n3 / E-UTRA 3 (1800 MHz)'	:'Aster  D962 G900 za L800 3 stavbe 13',
'n7 / E-UTRA 7 (2600 MHz)'	:'Aster  D962 L2600 del 3_2_9_loss_1',
'n78 (3300 MHz)'	:'Aster  D962 3500 NMTK in CELEKT 7w RT',
'n1 / E-UTRA 1 (2100 MHz)'	:'Aster  D962 U2100 obla 6',
'n20 / E-UTRA 20 (800 MHz)'	:'Aster  D962 L800 del 2_6_CMATKO2',
'n28 / E-UTRA 28 (700 MHz)'	:'Aster  D962 G900 za L700 4c -12 12 stavbe',
'n8 / E-UTRA 8 (900 MHz)'	:'Aster  D962 L800 del 2_8_CMATKO2',
'GSM 1800'	:'Aster  D962 G900 za L800 3 stavbe 13',
'GSM 900'	:'Aster  D962 G900 22',
'n75 / E-UTRA 75 (1500 MHz)':'Aster  D962 G900 za L800 3 stavbe 13'}

propag_model_calc_radius_dict= {'n3 / E-UTRA 3 (1800 MHz)'	:20000,
'n7 / E-UTRA 7 (2600 MHz)'	:20000,
'n78 (3300 MHz)'	:20000,
'n1 / E-UTRA 1 (2100 MHz)'	:20000,
'n20 / E-UTRA 20 (800 MHz)'	:35000,
'n28 / E-UTRA 28 (700 MHz)'	:35000,
'n8 / E-UTRA 8 (900 MHz)'	:35000,
'GSM 1800'	:20000,
'GSM 900'	:35000,
'n75 / E-UTRA 75 (1500 MHz)':20000}

def antene_atoll():
    a = pd.read_sql(sql_atoll_3794.antene_atoll, sql_atoll_3794.conn_atoll)
    a.columns = [i.upper() for i in a.columns.tolist()]
    return a

def carriers(tehnologija = 'LTE'):
    a = pd.read_sql(sql_atoll_3794.fband_carriers_atoll, sql_atoll_3794.conn_atoll)
    a = a[a['tehnologija'] == tehnologija]
    return dict(zip(a['fband'].tolist(), a['carrier'].tolist()))
    
def enak_seznam(seznam1, seznam2):
    r1 = True
    r2 = True
    for i in seznam1:
        if i in seznam2:
            pass
        else:
            r1 = False
            break
    for i in seznam2:
        if i in seznam1:
            pass
        else:
            r2 = False
            break
    r = r1 and r2 
    if seznam1 == seznam2:
        r = True
    else:
        pass
    return r

def naredi_atoll_site(ime, X, Y, odlozisce_fajl):
    z = ['NAME;LONGITUDE;LATITUDE\n']
    z.append(ime + ";" + str(X) + ";" + str(Y))
    with open(odlozisce_fajl, "w") as dd:
        dd.write("".join(z))
        dd.close()
    return 0

def naredi_atoll_antenna_name(tip, frekvenca, et, ant_atoll):
    ime = funkcije_at.fiz_antena(tip)
    ant_atoll = ant_atoll[ant_atoll['PHYSICAL_ANTENNA'] == ime]
    ant_atoll['frek_raz'] = abs(ant_atoll['FREQUENCY'] - frekvenca)
    ant_atoll = ant_atoll[ant_atoll['frek_raz'] == ant_atoll['frek_raz'].min()]
    ant_atoll['et_raz'] = abs(ant_atoll['ELECTRICAL_TILT'] - et)
    ant_atoll = ant_atoll[ant_atoll['et_raz'] == ant_atoll['et_raz'].min()]
    return ant_atoll['NAME'][ant_atoll['GAIN'] == ant_atoll['GAIN'].max()].values[0]
    
def naredi_atoll_xgtransmitters(filtered_df, odlozisce_fajl, nacin = 'novo'):
    """
    nacin: 'novo','spremeni'
    """
    ant_atoll = antene_atoll()
    z = ['TX_ID;SITE_NAME;ACTIVE;ABS_X;ABS_Y;USE_ABS_XY;FBAND;AZIMUT;TILT;HEIGHT;ANTENNA_NAME;PROPAG_MODEL;CALC_RADIUS;CALC_RESOLUTION;PROPAG_MODEL2;CALC_RADIUS2;CALC_RESOLUTION2']
    z1 = z[0].split(";")
    filtered_df['TX_ID'] = filtered_df['celica']
    filtered_df['SITE_NAME'] = filtered_df['ImeBSC']
    filtered_df['ACTIVE'] = 1
    filtered_df['ABS_X'] = filtered_df['lokrr_zsirina']
    filtered_df['ABS_Y'] = filtered_df['lokrr_zvisina']
    filtered_df['USE_ABS_XY'] = 1
    filtered_df['FBAND'] = filtered_df['fband']
    filtered_df['AZIMUT'] = filtered_df['azimut']
    filtered_df['TILT'] = filtered_df['nagib']
    filtered_df['HEIGHT'] = filtered_df['Visina']
    try:
        filtered_df['ANTENNA_NAME'] = filtered_df[['TipAntene', 'frekvenca', 'ET']].apply(lambda x: naredi_atoll_antenna_name(x['TipAntene'], x['frekvenca'], x['ET'], ant_atoll = ant_atoll), axis = 1)
    except:
        filtered_df.loc[(filtered_df['Visina'] < 3), 'ANTENNA_NAME'] = 'Indoor SISO'
        filtered_df.loc[(filtered_df['Visina'] >= 3), 'ANTENNA_NAME'] = '736349_0948_X_CO' # Omnica 11 dBi
    filtered_df['PROPAG_MODEL'] = filtered_df['fband'].map(propag_model_dict)
    filtered_df['CALC_RADIUS'] = 5000
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RADIUS']
    filtered_df['CALC_RESOLUTION'] = 5
    filtered_df['PROPAG_MODEL2'] = filtered_df['fband'].map(propag_model_dict)
    filtered_df.loc[(filtered_df['Visina'] < 3), 'PROPAG_MODEL2'] = ''
    filtered_df['CALC_RADIUS2'] = filtered_df['fband'].map(propag_model_calc_radius_dict)
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RADIUS2'] = ''
    filtered_df['CALC_RESOLUTION2'] = 25
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RESOLUTION2'] = ''
    if nacin == 'spremeni':
        xgtransmitters = pd.read_sql(sql_atoll_3794.query_xgtransmitters, sql_atoll_3794.conn_atoll)
        xgtransmitters = xgtransmitters[z1][xgtransmitters['TX_ID'].isin(filtered_df[z1])]
        razlika = xgtransmitters.compare(filtered_df)
    else:
        pass
    filtered_df['AZIMUT'].fillna(0, inplace = True)
    filtered_df['AZIMUT'] = filtered_df['AZIMUT'].astype(int)
    filtered_df['TILT'].fillna(0, inplace = True)
    filtered_df['TILT'] = filtered_df['TILT'].astype(int)
    filtered_df['HEIGHT'].fillna(0,inplace = True)
    filtered_df['HEIGHT'] = filtered_df['HEIGHT'].astype(int) 
    return filtered_df[z1].to_csv(odlozisce_fajl, index = False, sep = ";")

def naredi_atoll_gtransmitters(filtered_df, odlozisce_fajl):
    ant_atoll = antene_atoll()
    z = ['TX_ID;SITE_NAME;ACTIVE;ABS_X;ABS_Y;USE_ABS_XY;FBAND;AZIMUT;TILT;HEIGHT;ANTENNA_NAME;POWER;IO_TYPE;PROPAG_MODEL;CALC_RADIUS;CALC_RESOLUTION;PROPAG_MODEL2;CALC_RADIUS2;CALC_RESOLUTION2']
    z1 = z[0].split(";")
    filtered_df['TX_ID'] = filtered_df['celica']
    filtered_df['SITE_NAME'] = filtered_df['ImeBSC']
    filtered_df['ACTIVE'] = 1
    filtered_df['ABS_X'] = filtered_df['lokrr_zsirina']
    filtered_df['ABS_Y'] = filtered_df['lokrr_zvisina']
    filtered_df['USE_ABS_XY'] = 1
    filtered_df['FBAND'] = filtered_df['fband']
    filtered_df['AZIMUT'] = filtered_df['azimut']
    filtered_df['TILT'] = filtered_df['nagib']
    filtered_df['HEIGHT'] = filtered_df['Visina'] 
    try:
        filtered_df['ANTENNA_NAME'] = filtered_df[['TipAntene', 'frekvenca', 'ET']].apply(lambda x: naredi_atoll_antenna_name(x['TipAntene'], x['frekvenca'], x['ET'], ant_atoll = ant_atoll), axis = 1)
    except:
        filtered_df.loc[(filtered_df['Visina'] < 3), 'ANTENNA_NAME'] = 'Indoor SISO'
        filtered_df.loc[(filtered_df['Visina'] >= 3), 'ANTENNA_NAME'] = '736349_0948_X_CO' # Omnica 11 dBi
    filtered_df['POWER'] = 46
    filtered_df.loc[(filtered_df['Visina'] < 3), 'POWER'] = 26
    filtered_df['IO_TYPE'] = 'Outdoor'
    filtered_df.loc[(filtered_df['Visina'] < 3), 'IO_TYPE'] = 'Indoor'    
    filtered_df['PROPAG_MODEL'] = filtered_df['fband'].map(propag_model_dict)
    filtered_df['CALC_RADIUS'] = 5000
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RADIUS'] = 100
    filtered_df['CALC_RESOLUTION'] = 5
    filtered_df['PROPAG_MODEL2'] = filtered_df['fband'].map(propag_model_dict)
    filtered_df.loc[(filtered_df['Visina'] < 3), 'PROPAG_MODEL2'] = ''
    filtered_df['CALC_RADIUS2'] = filtered_df['fband'].map(propag_model_calc_radius_dict)
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RADIUS2'] = ''
    filtered_df['CALC_RESOLUTION2'] = 25
    filtered_df.loc[(filtered_df['Visina'] < 3), 'CALC_RESOLUTION2'] = ''
    
    filtered_df['AZIMUT'].fillna(0, inplace = True)
    filtered_df['AZIMUT'] = filtered_df['AZIMUT'].astype(int)
    filtered_df['TILT'].fillna(0, inplace = True)
    filtered_df['TILT'] = filtered_df['TILT'].astype(int)
    filtered_df['HEIGHT'].fillna(0,inplace = True)
    filtered_df['HEIGHT'] = filtered_df['HEIGHT'].astype(int) 
    
    return filtered_df[z1].to_csv(odlozisce_fajl, index = False, sep = ";")

def naredi_atoll_xgcellslte(filtered_df, odlozisce_fajl):
    carr = carriers(tehnologija = 'LTE')
    z = ['CELL_ID;TX_ID;ACTIVE;CARRIER;RS_EPRE;MAX_POWER;EQUIPMENT']
    z1 = z[0].split(";")
    filtered_df['CELL_ID'] = filtered_df['celica'] + "(0)"
    filtered_df['TX_ID'] = filtered_df['celica']
    filtered_df['ACTIVE'] = 1
    filtered_df['CARRIER'] = filtered_df['fband'].map(carr)
    filtered_df['MIMO'] = 2
    filtered_df['RS_EPRE'] = 15
    filtered_df.loc[filtered_df['fband'].isin(['n7 / E-UTRA 7 (2600 MHz)','n1 / E-UTRA 1 (2100 MHz)','n3 / E-UTRA 3 (1800 MHz)']),'RS_EPRE'] = 13
    filtered_df.loc[filtered_df['Type'].isin(['Indoor','Tunnel']),'RS_EPRE'] = 1
    filtered_df['MAX_POWER'] = 46
    # LTE rule za nastavljanje moči v Atollu! Glej G:\Atoll dokumentacija\TN068_LTE_Cell_Transmit_Power_Settings.pdf. 
    filtered_df['EQUIPMENT'] = 'LTE Radio Equipment'
    return filtered_df[z1].to_csv(odlozisce_fajl, index = False, sep = ";")

def naredi_atoll_xgcells5gnr(filtered_df, odlozisce_fajl):
    carr = carriers(tehnologija = 'NR')
    z = ['CELL_ID;TX_ID;ACTIVE;CARRIER;SSS_POWER;MAX_POWER;EQUIPMENT']
    z1 = z[0].split(";")
    filtered_df['CELL_ID'] = filtered_df['celica'] + "(0)"
    filtered_df['TX_ID'] = filtered_df['celica']
    filtered_df['ACTIVE'] = 1
    filtered_df['CARRIER'] = filtered_df['fband'].map(carr)
    filtered_df['SSS_POWER'] = 15
    filtered_df.loc[filtered_df['Type'].isin(['Indoor','Tunnel']),'SSS_POWER'] = 1
    filtered_df['MAX_POWER'] = 46
    filtered_df['EQUIPMENT'] = '5G NR Radio Equipment'
    return filtered_df[z1].to_csv(odlozisce_fajl, index = False, sep = ";")

def izvzeta_lokacija_gtransmitters(lokac, odlozisce_fajl):
    a = funkcije_at.pd.read_sql("""select TX_ID, ACTIVE from atoll_d96.dbo.gtransmitters where active = 1 and site_name = {}""".format(lokac),sql_atoll_3794.conn_atoll )
    if a.shape[0] > 0:
        a['ACTIVE'] = 0
        return a.to_csv(odlozisce_fajl, index = False, sep = ";")
    else:
        return 0

def izvzeta_lokacija_xgtransmitters(lokac, odlozisce_fajl):
    a = funkcije_at.pd.read_sql("""select TX_ID, ACTIVE from atoll_d96.dbo.xgtransmitters where active = 1 and site_name = {}""".format(lokac),sql_atoll_3794.conn_atoll )
    if a.shape[0] > 0:
        a['ACTIVE'] = 0
        return a.to_csv(odlozisce_fajl, index = False, sep = ";")
    else:
        return 0
        
def aktivirana_lokacija_trans(seznam, odlozisce_fajl, atoll_tabela = 'gtransmitters'):
    a = funkcije_at.pd.read_sql("""select TX_ID, ACTIVE from atoll_d96.dbo.{} where active = 0""".format(atoll_tabela),sql_atoll_3794.conn_atoll )
    a = a[a['TX_ID'].isin(seznam)]
    if a.shape[0] > 0:
        a['ACTIVE'] = 1
        if atoll_tabela == 'gtransmitters':
            a['POWER'] = 43
        else:
            pass
        return a.to_csv(odlozisce_fajl, index = False, sep = ";")
    else:
        return 0

def aktivirana_lokacija_xcells(seznam, odlozisce_fajl, atoll_tabela = 'xgcells5gnr'):
    a = funkcije_at.pd.read_sql("""select CELL_ID, ACTIVE from atoll_d96.dbo.{} where active = 0""".format(atoll_tabela),sql_atoll_3794.conn_atoll )
    a = a[a['TX_ID'].isin(seznam)]
    if a.shape[0] > 0:
        a['ACTIVE'] = 1
        a['TX_ID'] = a['CELL_ID'].str.split("(", expand = True)[0]
        return a.to_csv(odlozisce_fajl, index = False, sep = ";")
    else:
        return 0

        

def filter_sites(seznam, odlozisce_fajl):
    trans_text = "([NAME] = " + ")|([NAME] = ".join(seznam) + ")"
    with open(odlozisce_fajl, "w") as dd:
        dd.write(trans_text)
        dd.close()
    return 0

def filter_trans(filtered_df, odlozisce_fajl):
    trans = filtered_df['celica'].tolist()
    trans_text = "([TX_ID] = " + ")|([TX_ID] = ".join(trans) + ")" 
    with open(odlozisce_fajl, "w") as dd:
        dd.write(trans_text)
        dd.close()
    return 0
        
def atoll_datafill_podatki(slovar): 
    """
    Preverimo če obstaja lokacija in transmiterji in celice v atoll bazi
    slovar ima obliko: {lokacija:[seznam_celic], lokacija1:[seznam_celic1]...}         primer: {'LSENTJ':['LSENTJ1','LSENTJ2','LSENTJ3'],'AMOBI':['AMOBI18A','AMOBI2','AMOBI3'], 'ATLK':[],....}
    Če je seznam celic prazen, vzamemo vse celice na tisti lokaciji
    """
    # Pobrišemo trenutne tabele
    for i in os.listdir(odlozisce_novo):
        os.remove(odlozisce_novo + i)
    for i in os.listdir(odlozisce_spremeni):
        os.remove(odlozisce_spremeni + i) 
    for i in os.listdir(odlozisce_brisi):
        os.remove(odlozisce_brisi + i) 

    seznam_kljuc = list(slovar.keys() )
    seznam_vrednost = list(slovar.values())
    vse_celice = []
    vse_celice_dodati = []
    for i in slovar.keys():
        if len(slovar[i]) > 0:
            for j in slovar[i]:
                vse_celice.append(j)
        else:
            vse_celice_dodati.append(i)
    crit_end = False# Če se ta postavi na True



    # 1. Preverimo, ali so lokacije v bazi in v Atoll-u
    sites_den = pd.read_sql(sql_denali_3794.sites_denali_za_upravicenost_bazne_postaje, sql_denali_3794.conn_denali).dropna()
    sites_ato = pd.read_sql(sql_atoll_3794.query_sites, sql_atoll_3794.conn_atoll)
    site_ni_v_denali = funkcije_at.razlika_seznamov(sites_den['ImeBSC'][sites_den['ImeBSC'].isin(seznam_kljuc)].tolist(), seznam_kljuc, nacin = 'komplement2')
    site_je_v_denali = funkcije_at.razlika_seznamov(sites_den['ImeBSC'][sites_den['ImeBSC'].isin(seznam_kljuc)].tolist(), seznam_kljuc, nacin = 'presek')
    site_ni_v_atollu = funkcije_at.razlika_seznamov(sites_ato['NAME'][sites_ato['NAME'].isin(seznam_kljuc)].tolist(), site_je_v_denali, nacin = 'komplement2') 

    if len(site_ni_v_denali) > 0:
        print("Lokacij/e {} ni v denali bazi!".format(",".join(site_ni_v_denali)))
    if len(site_ni_v_atollu) > 0:
        print("Lokacij/e {} ni v atoll bazi!".format(",".join(site_ni_v_atollu)))

    # 2. Preverimo transmiterje/celice
    celice_den = pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
    if len(vse_celice_dodati) > 0:
        celice_den1 = celice_den[((celice_den['ImeBSC'].isin(vse_celice_dodati)) | (celice_den['rru_ime'].isin(vse_celice_dodati)))]
        for i in celice_den1['celica'].drop_duplicates().tolist():
            vse_celice.append(i)
    celice_den = celice_den[(celice_den['celica'].isin(vse_celice))]
    celice_den['CELL_ID'] = celice_den['celica'] + "(0)"
    celice_den = celice_den[((celice_den['rru_ime'].isin(seznam_kljuc)) )]  # Gledamo samo potencial outdoor celic - Odstranimo pogoj            & (celice_den['Type'] == 'Outdoor')
    celice_den_gsm = celice_den[celice_den['tehn'] == 'GSM']
    celice_den_xg = celice_den[celice_den['tehn'].isin(['LTE','5G'])]

        
    if celice_den.shape[0] == 0:
        print("Celic za lokacijo/e {} ni v denali bazi!".format(",".join(list(slovar.keys()))))
        crit_end = True
        pass
    else:
        if len(site_ni_v_atollu) > 0:
            uu = sites_den[['ImeBSC','GKe','GKn']][sites_den['ImeBSC'].isin(site_ni_v_atollu)]
            uu.columns = ['NAME','LONGITUDE','LATITUDE']
            uu.to_csv(odlozisce_novo + "20_sites.csv", index = False, sep= ";")
            filter_sites(site_ni_v_atollu, odlozisce_fajl = odlozisce_filter + "filter_sites.txt")
            
        xgtransmitters = pd.read_sql(sql_atoll_3794.query_xgtransmitters, sql_atoll_3794.conn_atoll)
        xgtransmitters = xgtransmitters[xgtransmitters['SITE_NAME'].isin(seznam_kljuc)]
        gtransmitters = pd.read_sql(sql_atoll_3794.query_gtransmitters, sql_atoll_3794.conn_atoll)
        gtransmitters = gtransmitters[gtransmitters['SITE_NAME'].isin(seznam_kljuc)]
        xgcellslte = pd.read_sql(sql_atoll_3794.query_xgcellslte, sql_atoll_3794.conn_atoll)
        pattern = "|".join([i + "[0-9].+" for i in seznam_kljuc])
        xgcellslte = xgcellslte[xgcellslte['CELL_ID'].isin([x for x in xgcellslte['CELL_ID'].drop_duplicates().tolist() if re.search(pattern, x)])]
        xgcells5gnr = pd.read_sql(sql_atoll_3794.query_xgcells5gnr, sql_atoll_3794.conn_atoll)
        xgcells5gnr = xgcells5gnr[xgcells5gnr['CELL_ID'].isin([x for x in xgcells5gnr['CELL_ID'].drop_duplicates().tolist() if re.search(pattern, x)])]
        trans_atollx = xgtransmitters['TX_ID'].tolist()
        trans_atollg = gtransmitters['TX_ID'].tolist()

        gtransmiters_ni_v_atollu = funkcije_at.razlika_seznamov(celice_den_gsm['celica'].tolist(), trans_atollg, nacin = 'komplement1')
        gtransmiters_ni_v_denali = funkcije_at.razlika_seznamov(celice_den_gsm['celica'].tolist(), trans_atollg, nacin = 'komplement2')
        xgtransmiters_ni_v_atollu = funkcije_at.razlika_seznamov(celice_den_xg['celica'].tolist(), trans_atollx, nacin = 'komplement1')
        xgtransmiters_ni_v_denali = funkcije_at.razlika_seznamov(celice_den_xg['celica'].tolist(), trans_atollx, nacin = 'komplement2')        
        xgcellslte_ni_v_atollu = funkcije_at.razlika_seznamov(celice_den_xg['CELL_ID'][celice_den_xg['tehn'] == 'LTE'].tolist(), xgcellslte['CELL_ID'].tolist(), nacin = 'komplement1')
        xgcells5gnr_ni_v_atollu = funkcije_at.razlika_seznamov(celice_den_xg['CELL_ID'][celice_den_xg['tehn'] == '5G'].tolist(), xgcells5gnr['CELL_ID'].tolist(), nacin = 'komplement1')
        gtransmitters_neaktivna_atoll = gtransmitters['TX_ID'][gtransmitters['ACTIVE'] == 0].tolist()
        xgtransmitters_neaktivna_atoll = xgtransmitters['TX_ID'][xgtransmitters['ACTIVE'] == 0].tolist()
        xgcells5gnr_neaktivna_atoll = xgcells5gnr['CELL_ID'][xgcells5gnr['ACTIVE'] == 0].tolist()
        xgcellslte_neaktivna_atoll = xgcellslte['CELL_ID'][xgcellslte['ACTIVE'] == 0].tolist()
        
        if len(gtransmiters_ni_v_atollu) > 0:
            naredi_atoll_gtransmitters(celice_den_gsm[celice_den_gsm['celica'].isin(gtransmiters_ni_v_atollu)], odlozisce_fajl = odlozisce_novo + "21_gtransmitters.csv")
            filter_trans(celice_den_gsm, odlozisce_fajl = odlozisce_filter + "filter_gtrans.txt")
            
        if len(xgtransmiters_ni_v_atollu) > 0:
            naredi_atoll_xgtransmitters(celice_den_xg[celice_den_xg['celica'].isin(xgtransmiters_ni_v_atollu)], odlozisce_fajl = odlozisce_novo + "23_xgtransmitters.csv")
            filter_trans(celice_den_xg, odlozisce_fajl = odlozisce_filter + "filter_xgtrans.txt")
            
        # if nadomesca != '':
            # izvzeta_lokacija_gtransmitters(nadomesca, odlozisce_fajl = odlozisce_spremeni + "21_gtransmitters.csv") 
            # izvzeta_lokacija_xgtransmitters(nadomesca, odlozisce_fajl = odlozisce_spremeni + "23_xgtransmitters.csv")
            
        # if (len(gtransmiters_ni_v_denali) > 0) :
            # if "21_gtransmitters.csv" in os.listdir(odlozisce_spremeni):
                # a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "21_gtransmitters.csv")
                # b = funkcije_at.pd.DataFrame(gtransmiters_ni_v_denali, columns = ['TX_ID'])
                # b['ACTIVE'] = 0
                # a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                # a.to_csv(odlozisce_spremeni+  "21_gtransmitters.csv", index = False)
            # else:
                # b = funkcije_at.pd.DataFrame(gtransmiters_ni_v_denali, columns = ['TX_ID'])
                # b['ACTIVE'] = 0
                # b.to_csv(odlozisce_spremeni+  "21_gtransmitters.csv", index = False)
                
        # if (len(xgtransmiters_ni_v_denali) > 0) :
            # if "23_xgtransmitters.csv" in os.listdir(odlozisce_spremeni):
                # a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "23_xgtransmitters.csv")
                # b = funkcije_at.pd.DataFrame(xgtransmiters_ni_v_denali, columns = ['TX_ID'])
                # b['ACTIVE'] = 0
                # a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                # a.to_csv(odlozisce_spremeni+  "23_xgtransmitters.csv", index = False)
            # else:
                # b = funkcije_at.pd.DataFrame(xgtransmiters_ni_v_denali, columns = ['TX_ID'])
                # b['ACTIVE'] = 0
                # b.to_csv(odlozisce_spremeni+  "23_xgtransmitters.csv", index = False) 
                
        if len(xgcellslte_ni_v_atollu) > 0:
            naredi_atoll_xgcellslte(celice_den_xg[celice_den_xg['CELL_ID'].isin(xgcellslte_ni_v_atollu)], odlozisce_fajl = odlozisce_novo + "25_xgcellslte.csv")
            
        if len(xgcells5gnr_ni_v_atollu) > 0:
            naredi_atoll_xgcells5gnr(celice_den_xg[celice_den_xg['CELL_ID'].isin(xgcells5gnr_ni_v_atollu)], odlozisce_fajl = odlozisce_novo + "26_xgcells5gnr.csv")
            
        if len(gtransmitters_neaktivna_atoll) > 0:
            if "21_gtransmitters.csv" in os.listdir(odlozisce_spremeni):
                a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "21_gtransmitters.csv")
                b = funkcije_at.pd.DataFrame(gtransmitters_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                a.to_csv(odlozisce_spremeni+  "21_gtransmitters.csv", index = False, sep = ";")
            else:
                b = funkcije_at.pd.DataFrame(gtransmitters_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                b.to_csv(odlozisce_spremeni+  "21_gtransmitters.csv", index = False, sep = ";")
                
        if (len(xgtransmitters_neaktivna_atoll) > 0) :
            if "23_xgtransmitters.csv" in os.listdir(odlozisce_spremeni):
                a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "23_xgtransmitters.csv")
                b = funkcije_at.pd.DataFrame(xgtransmitters_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                a.to_csv(odlozisce_spremeni+  "23_xgtransmitters.csv", index = False, sep = ";")
            else:
                b = funkcije_at.pd.DataFrame(xgtransmitters_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                b.to_csv(odlozisce_spremeni+  "23_xgtransmitters.csv", index = False, sep = ";")   

        if len(xgcells5gnr_neaktivna_atoll) > 0:
            if "25_xgcellslte.csv" in os.listdir(odlozisce_spremeni):
                a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "25_xgcellslte.csv")
                b = funkcije_at.pd.DataFrame(xgcells5gnr_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                a.to_csv(odlozisce_spremeni+  "25_xgcellslte.csv", index = False, sep = ";")
            else:
                b = funkcije_at.pd.DataFrame(xgcells5gnr_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                b.to_csv(odlozisce_spremeni+  "25_xgcellslte.csv", index = False, sep = ";")
                
        if (len(xgcellslte_neaktivna_atoll) > 0) :
            if "26_xgcells5gnr.csv" in os.listdir(odlozisce_spremeni):
                a= funkcije_at.pd.read_csv(odlozisce_spremeni+  "26_xgcells5gnr.csv")
                b = funkcije_at.pd.DataFrame(xgcellslte_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                a = funkcije_at.pd.concat([a,b]).drop_duplicates()
                a.to_csv(odlozisce_spremeni+  "26_xgcells5gnr.csv", index = False, sep = ";")
            else:
                b = funkcije_at.pd.DataFrame(xgcellslte_neaktivna_atoll, columns = ['TX_ID'])
                b['ACTIVE'] = 1
                b.to_csv(odlozisce_spremeni+  "26_xgcells5gnr.csv", index = False, sep = ";")
    return 0


def izbor_celic(seznam_lokacij, pisi_v_fajl = True):
    celice_den = pd.read_sql(sql_denali_3794.celice, sql_denali_3794.conn_denali)
    celice_den['teh'] =  celice_den['Ime'].str.replace(" ","_")
    celice_den = celice_den[celice_den['rru_ime'].isin(seznam_lokacij)].sort_values(by = ['teh','celica'], ascending = [True, False])
    celice_den['filt'] = "([TX_ID]=" + celice_den['celica'] + ")"
    if pisi_v_fajl == True:
        return celice_den[['celica', 'teh', 'filt', 'rru_ime']][celice_den['rru_ime'].isin(seznam_lokacij)].drop_duplicates().to_csv(r"D:\Atoll_projects_planer01\Avtomatika\Eksport\\Upravicenost_bp_celice.txt", sep = ";",header = None, index = False)
    else: 
        return celice_den

def atoll_update_in_export_celic():
    pass
