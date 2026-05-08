# -*- coding: utf-8 -*-

import sys
sys.path.append(r"D:\Atoll_projects_planer01\Skripte\Python\gis_zadeve")

import funkcije_at
import pyodbc
import pandas as pd
import subprocess
import export_script_3794_reporting
import os
import preverba_upravicenost_bazne_postaje
import zipfile
import traceback
import shutil
from sql_denali_3794 import celice as celice_denali
import csv_atoll_tabele


########################
#   1. Preverimo če lokacija obstaja v Atoll-u in če so celice (transmiterji) definirani
#       - če lokacija ni definirana, izstopimo
#       - če transmiterji niso definirani izstopimo. Nima smisla delati 0, 120, 240 in kar neka izmišljena višina. Če so transmiterji že v SQL bazi in niso v Atoll-u, jih trenutno nafilamo tako, da ločeno zalaufamo update Atoll-a brez exportov
#       - če celice niso definiriane jih ustvarimo
#   2. Naredimo filter 20000m v vse smeri okoli iskane lokacije in naredimo exporte


odlozisce_dnevnik = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\dnevnik.xlsx"
odlozisce_dnevnik = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Dnevnik\\"
odlozisce_novo = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Novo\\"
odlozisce_spremeni = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Spremeni\\"
odlozisce_spremeni_atributi = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Spremeni\\Atributi\\"
odlozisce_brisi_drugo = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Brisi_drugo\\"
odlozisce_brisi = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Brisi\\"
odlozisce_sosede_dodaj = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Sosede\\Dodaj\\"
odlozisce_sosede_brisi = "D:\\Atoll_projects_planer01\\Avtomatika\\EPSG_3794\\Sosede\\Brisi\\"


slovar__ = {'SCVEN':''}

def format_(slovar):
    a = []
    b = []
    c = []
    d = []
    for i in slovar.keys():
        a.append(i)
        b.append(a)
        a = []
    for i in slovar.values():
        c.append(i)
        d.append(c)
        c = []
    return b, d

namesto_lokacije = ['']


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
loks_ = [['AVEVCE'],['MVRBAN']]

loks_ = format_(slovar__)[0]
namesto_lokacije = format_(slovar__)[1]

conn_denali = pyodbc.connect('Driver={SQL Server};'
                      'Server=BPW-DENALI;'
                      'Database=SQLBazne;'
                      'UID=beribaze;'
                      'PWD=beribaze')

conn_atoll = pyodbc.connect('Driver={SQL Server};'
                      'Server=BPW-DENALI;'
                      'Database=atoll_d96;'
                      'UID=beribaze;'
                      'PWD=beribaze')


query_sites = """select * from atoll_d96.dbo.sites"""
query_xgtransmitters = """select * from atoll_d96.dbo.xgtransmitters"""
query_gtransmitters = """select * from atoll_d96.dbo.gtransmitters"""
query_xgcellslte = """select * from atoll_d96.dbo.xgcellslte"""
query_xgcells5gnr = """select * from atoll_d96.dbo.xgcells5gnr"""

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

def preverba_lokacije(ime_lokacije):
    """
    Preverimo če obstaja lokacija in transmiterji in celice v atoll bazi
    ime_lokacije je seznam
    """
    try:
        sites = pd.read_sql(query_sites, conn_atoll)
        sites = sites[sites['NAME'].isin(ime_lokacije)]
        xgtransmitters = pd.read_sql(query_xgtransmitters, conn_atoll)
        xgtransmitters = xgtransmitters[xgtransmitters['SITE_NAME'].isin(ime_lokacije)]
        gtransmitters = pd.read_sql(query_gtransmitters, conn_atoll)
        gtransmitters = gtransmitters[gtransmitters['SITE_NAME'].isin(ime_lokacije)]
        celice_den = pd.read_sql(celice_denali, conn_denali)
        celic_den = celice_den[['ImeBSC','celica', 'rru_ime']][celice_den['ImeBSC'].isin(ime_lokacije)]
        if celic_den.shape[0] == 0:
            celice_den = celice_den[['ImeBSC','celica', 'rru_ime']][celice_den['rru_ime'].isin(ime_lokacije)]
            celice_den['ImeBSC'] =  celice_den['rru_ime']
        else:
            celice_den[['ImeBSC','celica', 'rru_ime']][celice_den['ImeBSC'].isin(ime_lokacije)]
        celice_den.drop(columns = ['rru_ime'], inplace = True)
        site_den = celice_den['ImeBSC'].drop_duplicates().tolist()[0]
        celice_den = celice_den['celica']
        cel_atollx = xgtransmitters['TX_ID'].tolist()
        cel_atollg = gtransmitters['TX_ID'].tolist()
        cel_atoll = cel_atollx
        for i in cel_atollg:
            cel_atoll.append(i)
        crit2 = enak_seznam(celice_den.tolist(), cel_atoll)

        if (sites.shape[0] == 0) & (celice_den.shape[0] == 0):
            crit1 = False
            site = ''
            crit_site = False
        elif (sites.shape[0] == 0) & (celice_den.shape[0] > 0):
            crit1 = True
            site = site_den
            crit_site = True
        # elif (sites.shape[0] > 0) & (celice_den.shape[0] > 0):
            # site = ''
            # crit1 = True
            # crit_site = False
        else:
            crit1 = True
            site = ''
            crit_site = False

        if crit2 == False:
            filt_ven = [i for i in cel_atoll if i not in celice_den]
            dodaj = [i for i in celice_den if i not in cel_atoll]
            if site != '':
                dodaj.append(site)
        else:
            filt_ven = []
            dodaj = []
    except:
        crit1=False
        crit2=False
        crit_site = False
        filt_ven = []
        dodaj = []
        site = ime_lokacije[0]
    return crit1, crit2, crit_site, filt_ven, dodaj, site


def dodaj_ime_celice_v_export(mapa):
    """
    RASTERTXT export iz Atoll-a, ki je omejen na celico, vrne [0] na mestu, kjer bi moralo biti ime celice. Spremenimo za vse celice v folderju.
    """
    for i in os.listdir(mapa):
        ime = i.strip(r".TXT|.txt")
        with open(mapa + i, "r") as zz:
            zzr = zz.readlines()
            zz.close()
        zzr1 = []
        for j in zzr:
            if j.find("[0]") > 0:
                zzr1.append(j.replace("[0]",ime))
            else:
                zzr1.append(j)
        with open(mapa + i, "w") as z:
            z.write("".join(zzr1))
            z.close()
    return 0

def podatki_celice(ime_lokacije, odlozisce, nadomesca = []):
    if preverba_lokacije(ime_lokacije)[0] == True:
        xgtransmitters = pd.read_sql(query_xgtransmitters, conn_atoll)
        xgtransmitters = xgtransmitters[xgtransmitters['SITE_NAME'].isin(ime_lokacije)]
        gtransmitters = pd.read_sql(query_gtransmitters, conn_atoll)
        gtransmitters = gtransmitters[gtransmitters['SITE_NAME'].isin(ime_lokacije)]
    else:
        xgtransmitters = pd.Dataframe()
        gtransmitters = pd.Dataframe()
    if xgtransmitters.shape[0] > 0:
        celice = xgtransmitters[['SITE_NAME','TX_ID']]
    if gtransmitters.shape[0] > 0:
        celice = pd.concat([celice, gtransmitters[['SITE_NAME','TX_ID']]])
    celice[['ime_celice', 'tehn', 'fband', 'tehnol', 'frekvenca']] = celice[['TX_ID']].apply(lambda x: funkcije_at.pripona(x['TX_ID']), axis = 1,  result_type = 'expand')
    celice['CELL_ID'] = celice['TX_ID'] + "(0)"
    celice['ACTIVE'] = True
    celice['CARRIER'] = ''
    celice.loc[(celice['tehnol'] == 'NR 700'), 'CARRIER'] = '10 MHz - NR-ARFCN 152600'
    celice.loc[(celice['tehnol'] == 'NR 2600'), 'CARRIER'] = '20 MHz - NR-ARFCN 526020'
    celice.loc[(celice['tehnol'] == 'NR 3500'), 'CARRIER'] = '100 MHz - NR-ARFCN 631334'
    celice.loc[(celice['tehnol'] == 'LTE 700'), 'CARRIER'] = '10 MHz - EARFCN 9260'
    celice.loc[(celice['tehnol'] == 'LTE 800'), 'CARRIER'] = '10 MHz - EARFCN 6201'
    celice.loc[(celice['tehnol'] == 'LTE 900'), 'CARRIER'] = '10 MHz - EARFCN 3696'
    celice.loc[(celice['tehnol'] == 'LTE 1800'), 'CARRIER'] = '20 MHz - EARFCN 1657'
    celice.loc[(celice['tehnol'] == 'LTE 2100'), 'CARRIER'] = '20 MHz - EARFCN 400'
    celice.loc[(celice['tehnol'] == 'LTE 2600'), 'CARRIER'] = '15 MHz - EARFCN 3023'
    celice['RS_EPRE'] = 15
    celice['MAX_POWER'] = 46
    celice['EQUIPMENT'] = ''
    celice.loc[(celice['tehn'] == '5G'), 'EQUIPMENT'] = '5G NR Radio Equipment'
    celice.loc[(celice['tehn'] == 'LTE'), 'EQUIPMENT'] = 'LTE Radio Equipment'
    celice['filt'] = "([TX_ID] = " + celice['TX_ID'] + ")"
    manjkajoci_nr = []
    manjkajoci_lte = []
    if 'LTE' in celice['tehn'].drop_duplicates().tolist():
        xgcellslte = pd.read_sql(query_xgcellslte, conn_atoll)
        xgcellslte['TX_ID'] = xgcellslte['CELL_ID'].str.replace('(0)','')
        for i in celice['TX_ID'][celice['tehn'] == 'LTE'].tolist():
            if i not in xgcellslte['TX_ID'].tolist():
                manjkajoci_lte.append(i)

    if '5G' in celice['tehn'].drop_duplicates().tolist():
        xgcells5gnr = pd.read_sql(query_xgcells5gnr, conn_atoll)
        xgcells5gnr['TX_ID'] = xgcells5gnr['CELL_ID'].str.replace('(0)','')
        for i in celice['TX_ID'][celice['tehn'] == '5G'].tolist():
            if i not in xgcells5gnr['TX_ID'].tolist():
                manjkajoci_nr.append(i)

    for i in os.listdir(odlozisce + "Spremeni\\" ):
        os.remove(odlozisce + "Spremeni\\"  + i)
    for i in os.listdir(odlozisce + "Novo\\" ):
        os.remove(odlozisce + "Novo\\"  + i)


    # Spremeni 23_xgtransmitters.csv - VEDNO zapise (ne samo ko manjkajo celice),
    # da se ACTIVE=True zagotovo postavi tudi za planirane lokacije, katerih
    # transmitterji so ze v ATL. Brez tega podrunhi ostanejo ACTIVE=False.
    if ((celice['tehn'] == 'LTE') | (celice['tehn'] == '5G')).any():
        if len(nadomesca) > 0:
            celice_lte = celice[['TX_ID','ACTIVE']][((celice['tehn'] == 'LTE') | (celice['tehn'] == '5G'))]
            xgtr = pd.read_sql(query_xgtransmitters, conn_atoll)
            xgtr = xgtr[xgtr['SITE_NAME'].isin(nadomesca)]
            xgtr = xgtr[['TX_ID','ACTIVE']]
            xgtr['ACTIVE'] = False
            celice_lte = pd.concat([celice_lte, xgtr])
            celice_lte.to_csv(odlozisce + "Spremeni\\" + "23_xgtransmitters.csv", index = False, sep = ';', decimal = ',')
        else:
            celice[['TX_ID','ACTIVE']][((celice['tehn'] == 'LTE') | (celice['tehn'] == '5G'))].to_csv(odlozisce + "Spremeni\\" + "23_xgtransmitters.csv", index = False, sep = ';', decimal = ',')

    # Novo - samo ce celice manjkajo v ATL
    if len(manjkajoci_lte) > 0:
        celice[['CELL_ID','TX_ID','ACTIVE','CARRIER','EQUIPMENT']][celice['TX_ID'].isin(manjkajoci_lte)].to_csv(odlozisce + "Novo\\" + "25_xgcellslte.csv", index = False, sep = ';', decimal = ',')
    if len(manjkajoci_nr) > 0:
        celice_nr = celice[['CELL_ID','TX_ID','ACTIVE','CARRIER','EQUIPMENT']][celice['TX_ID'].isin(manjkajoci_nr)].to_csv(odlozisce + "Novo\\" + "26_xgcells5gnr.csv", index = False, sep = ';', decimal = ',')
    else:
        pass
    if gtransmitters.shape[0] > 0:
        if len(nadomesca) > 0:
            gtransmitters['POWER'] = 46
            gtransmitters['ACTIVE'] = True
            gsm_export = gtransmitters[['TX_ID','ACTIVE','POWER']]
            gtr = pd.read_sql(query_gtransmitters, conn_atoll)
            gtr = gtr[gtr['SITE_NAME'].isin(nadomesca)]
            gtr = gtr[['TX_ID','ACTIVE', 'POWER']]
            gtr['ACTIVE'] = False
            gsm_export = pd.concat([gsm_export, gtr])
            gsm_export.to_csv(odlozisce  + "Spremeni\\" + "21_gtransmitters.csv", index = False, sep = ';', decimal = ',')
        else:
            gtransmitters['POWER'] = 46
            gtransmitters['ACTIVE'] = True
            gtransmitters[['TX_ID','ACTIVE','POWER']].to_csv(odlozisce  + "Spremeni\\" + "21_gtransmitters.csv", index = False, sep = ';', decimal = ',')
    string = ""
    for l in ime_lokacije:
        string = string +  "([NAME] = {})|".format(l)
    string = string[:-2] + ")"
    with open(odlozisce + "filter_sites.txt", "w") as mm:
        mm.write(string)
        mm.close()

    string = ""
    for l in celice['TX_ID'].drop_duplicates().tolist():
        string = string +  "([TX_ID] = {})|".format(l)
    string = string[:-2] + ")"
    with open(odlozisce + "filter_trans.txt", "w") as mm:
        mm.write(string)
        mm.close()
    celice[['SITE_NAME','TX_ID','tehnol', 'filt']].to_csv(odlozisce + "trans_teh.txt", index = False, sep = ";", header = None)

    return celice

def odd_bp_od_naslov(lokacija):
    maximum = 25000
    oddaljenost = 5 * preverba_upravicenost_bazne_postaje.razdalja_med_lokacijami(n = 12, lokacija = lokacija)
    if oddaljenost < maximum:
        a = int(oddaljenost)
    else:
        a= maximum
    return a

def podatki_comp_zone(ime_lokacije, odlozisce):
    sites = pd.read_sql(query_sites, conn_atoll)
    sites = sites[sites['NAME'] == ime_lokacije]
    oddaljenost_BP_od_naslova = odd_bp_od_naslov(ime_lokacije)
    oddaljenost_BP_od_naslova = 25000
    sites_x1 = int(sites['LONGITUDE'].values[0]) - oddaljenost_BP_od_naslova
    sites_x2 = int(sites['LONGITUDE'].values[0]) + oddaljenost_BP_od_naslova
    sites_y1 = int(sites['LATITUDE'].values[0]) - oddaljenost_BP_od_naslova
    sites_y2 = int(sites['LATITUDE'].values[0]) + oddaljenost_BP_od_naslova
    string_comp_zone = "(([LONGITUDE]>" +  str(sites_x1) + ") & ([LONGITUDE]<" +  str(sites_x2) + ") & ([LATITUDE]>" +  str(sites_y1) + ") & ([LATITUDE]<" +  str(sites_y2) + "))"
    with open (odlozisce + 'zone.txt', "w") as dd:
        dd.write(string_comp_zone)
        dd.close()
    return 0



def atoll_exporti():
    subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano.vbs'],  capture_output=True,  text=True)
    return 0

def naredi_folder(folder, ime):
    try:
        os.mkdir(folder + ime)
    except:
        FileExistsError
    return 0



if __name__ == '__main__':
    zone = 'zone'
    stev = 0
    ni_slo_skozi = []
    for seznam_lokacij in loks_:
        try:
            if preverba_lokacije(seznam_lokacij)[0] == True:
                # # if preverba_lokacije(seznam_lokacij)[1] == False:
                # if False:
                    # # import csv_3794
                    # csv_atoll_tabele.main()
                    # if len(os.listdir(odlozisce_spremeni_atributi)) > 0:
                        # for i in os.listdir(odlozisce_spremeni_atributi):
                            # os.remove(odlozisce_spremeni_atributi+i)
                        # else:
                            # pass

                    # if len(os.listdir(odlozisce_spremeni)) > 0:
                        # for i in os.listdir(odlozisce_spremeni):
                            # if i.find('.csv') > 0:
                                # os.remove(odlozisce_spremeni+i)
                            # else:
                                # pass

                    # if len(os.listdir(odlozisce_brisi)) > 0:
                        # for i in os.listdir(odlozisce_brisi):
                            # os.remove(odlozisce_brisi+i)
                        # else:
                            # pass

                    # if len(os.listdir(odlozisce_sosede_dodaj)) > 0:
                        # for i in os.listdir(odlozisce_sosede_dodaj):
                            # os.remove(odlozisce_sosede_dodaj+i)
                        # else:
                            # pass

                    # if len(os.listdir(odlozisce_sosede_brisi)) > 0:
                        # for i in os.listdir(odlozisce_sosede_brisi):
                            # os.remove(odlozisce_sosede_brisi+i)
                        # else:
                            # pass

                    # if len(os.listdir(odlozisce_brisi_drugo)) > 0:
                        # for i in os.listdir(odlozisce_brisi_drugo):
                            # os.remove(odlozisce_brisi_drugo+i)
                        # else:
                            # pass

                    # sez_update = ['xgtransmitters','gtransmitters','xgcellslte','xgcells5gnr']
                    # if preverba_lokacije(seznam_lokacij)[2] == True:
                            # sez_update.append('sites')
                    # else:
                        # pass

                    # for i in os.listdir(odlozisce_novo):
                        # if i.split("_")[1].split(".csv")[0] in sez_update:
                            # pass
                        # else:
                            # os.remove(odlozisce_novo + i)

                    # for i in os.listdir(odlozisce_novo):
                        # temp = pd.read_csv(odlozisce_novo + i, sep = ";")
                        # temp = temp[temp['TX_ID'].isin(preverba_lokacije(seznam_lokacij)[4])]
                        # if temp.shape[0] > 0:
                            # temp.to_csv(odlozisce_novo + i, index=False, sep = ';', decimal = ',')
                        # else:
                            # os.remove(odlozisce_novo + i)

                    # # Preverba vsebine cells tabel v atollu
                    # if '23_xgtransmitters.csv' in os.listdir(odlozisce_novo):
                        # tempxg = pd.DataFrame(preverba_lokacije(seznam_lokacij)[4], columns = ['TX_ID'])
                        # tempxg[['cell','tehnologija','atoll_fband','tehnol', 'frekvenca']] = tempxg[['TX_ID']].apply(lambda x: funkcije_at.pripona(x['TX_ID']),axis=1, result_type = 'expand')
                        # tempxg['CARRIER'] = tempxg['TX_ID'].apply(funkcije_at.carrier_atoll)
                        # # CELL_ID	TX_ID	PCI	ACTIVE	CARRIER	RS_EPRE	ECI	TAC	PRACH_RSI_LIST	EQUIPMENT	LTE_M

                        # xgclte = tempxg[['TX_ID', 'CARRIER']][tempxg['tehnologija'] == 'LTE']
                        # xgclte['CELL_ID'] = xgclte['TX_ID'] + "(0)"
                        # xgclte['PCI'] = 1
                        # xgclte['ACTIVE'] = 1
                        # xgclte['EQUIPMENT'] = 'LTE Radio Equipment'
                        # xgclte['RS_EPRE'] = 13
                        # xgclte['MAX_POWER'] = 20
                        # xgclte['ECI'] = 0
                        # xgclte['TAC'] = 0
                        # xgclte['PRACH_RSI_LIST'] = 0
                        # xgclte['LTE_M'] = False
                        # xgclte[['CELL_ID', 'TX_ID', 'PCI', 'ACTIVE', 'CARRIER', 'RS_EPRE', 'MAX_POWER', 'ECI', 'TAC', 'PRACH_RSI_LIST', 'EQUIPMENT', 'LTE_M']].to_csv(odlozisce_novo + "25_xgcellslte.csv", index = False, sep = ";")

                        # # CELL_ID	TX_ID	ACTIVE	PCI	NRTAC	CID	CARRIER	SSS_POWER	MAX_POWER	PDCCH_POWER_OFFSET	PDSCH_POWER_OFFSET	CSIRS_POWER_OFFSET	EQUIPMENT


                        # xgcnr = tempxg[['TX_ID', 'CARRIER']][tempxg['tehnologija'] == '5G']
                        # xgcnr['CELL_ID'] = xgcnr['TX_ID'] + "(0)"
                        # xgcnr['PCI'] = 1
                        # xgcnr['ACTIVE'] = 1
                        # xgcnr['EQUIPMENT'] = '5G NR Radio Equipment'
                        # xgcnr['SSS_POWER'] = 16
                        # xgcnr['CID'] = 0
                        # xgcnr['NRTAC'] = 0
                        # xgcnr['PRACH_RSI_LIST'] = 0
                        # xgcnr['MAX_POWER'] = 46
                        # xgcnr['PDCCH_POWER_OFFSET'] = 0
                        # xgcnr['PDSCH_POWER_OFFSET'] = 3
                        # xgcnr['CSIRS_POWER_OFFSET'] = 3
                        # xgcnr[['CELL_ID', 'TX_ID', 'ACTIVE', 'PCI','NRTAC','CID', 'CARRIER', 'SSS_POWER', 'MAX_POWER', 'PDCCH_POWER_OFFSET', 'PDSCH_POWER_OFFSET', 'CSIRS_POWER_OFFSET' ,'EQUIPMENT']].to_csv(odlozisce_novo + "26_xgcells5gnr.csv", index = False, sep = ";")

                    # if len(os.listdir(odlozisce_novo)) > 0:
                        # subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_brez_archive.vbs'],  capture_output=True,  text=True)
                        # import arhiv_sprememb
                # else:
                    # pass

                podatki_celice(seznam_lokacij, odlozisce = "D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\Planirane_celice\\Update_planirane_celice\\",nadomesca = namesto_lokacije[stev])
                if zone == 'zone':
                    subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano_comp_zone.vbs'],  capture_output=True,  text=True)
                    for i in seznam_lokacij:
                        podatki_comp_zone(i, odlozisce = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\\")
                        teh = pd.read_csv(r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\\trans_teh.txt", sep = ";", names =  [0,1,2,3])
                        print(teh)
                        teh = teh[teh[0] == i]
                        teh['teh'] = teh[2].str.replace(" ","_")
                        teh['tehnologija'] = teh['teh'].str.split("_", expand = True)[0]
                        teha = teh[[0,'tehnologija']].drop_duplicates().rename(columns = {'tehnologija':'teh'})
                        teh.drop(columns = 'tehnologija', inplace = True)
                        teh = teh[[0,'teh']].drop_duplicates()
                        teh = pd.concat([teh,teha])
                        teh = teha
                        print(teh)
                        for j in teh['teh'].tolist():
                            sitee = teh[0][teh['teh'] == j].values[0]
                            naredi_folder(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" , teh[0][teh['teh'] == j].values[0])
                            krm_tab = pd.read_excel(r"D:\Atoll_projects_planer01\\Export_coverage_krmilna_tabela.xlsx")
                            krm_tab['Export_da_ne'] = False
                            if j.find("_") > 0:
                                krm_tab.loc[(krm_tab['ime_fajla'] == j), 'Export_da_ne'] = True
                                filter = krm_tab.loc[(krm_tab['ime_fajla'] == j), 'tehn'].values[0]
                                ime_fajl = ''
                            else:
                                krm_tab.loc[(krm_tab['tehnologija'] == j), 'Export_da_ne'] = True
                                minn = krm_tab.loc[krm_tab['Export_da_ne'] == True].index.min()
                                minn_ = krm_tab.loc[(krm_tab['Export_da_ne'] == True) & (krm_tab.index > minn)].index
                                krm_tab.loc[minn_,'Export_da_ne'] = False
                                filter = krm_tab.loc[((krm_tab['Export_da_ne'] == True)), 'filter_tehn'].values[0]
                                ime_fajl = 'tehnologija'
                            print("=================")
                            print(filter)
                            print(ime_fajl)
                            print("=================")
                            with open (r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\\trans_teh_filter.txt", "w") as dd:
                                dd.write(filter)
                                dd.close()
                            krm_tab.to_excel("D:\\Atoll_projects_planer01\\Export_coverage_krmilna_tabela.xlsx", index = False)
                            subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano_nastavi_filt_zone.vbs'],  capture_output=True,  text=True)
                            export_script_3794_reporting.export_pokrivanj_1(po_celicah = False, odlozisce_pokrivanja = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + teh[0][teh['teh'] == j].values[0] + "\\", krm_tab_set = True, ime_lokacije = teh[0][teh['teh'] == j].values[0], ime_fajla = ime_fajl,  ini_file_set = 'Ziga')

                        preverba_upravicenost_bazne_postaje.izracunaj_stevilke(mapa = r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\", lokacija = sitee, naredi_slike = True)

                    string_comp_zone = ""
                    with open (r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\\" + 'zone.txt', "w") as dd:
                        dd.write(string_comp_zone)
                        dd.close()
                    with open (r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\\trans_teh_filter.txt", "w") as dd:
                        dd.write(string_comp_zone)
                        dd.close()
                    subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano_nastavi_filt_zone.vbs'],  capture_output=True,  text=True)
                else:
                    atoll_exporti('zone')
                    dodaj_ime_celice_v_export(r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Export_planirane_celice\\")
                # Zipaj .txt fileje in jih zbrisi
                file_list = [ii for ii in os.listdir(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\") if ii.find("].txt") > 0]
                if len(file_list) > 0:
                    naredi_folder(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" , sitee + "\\Atoll_export\\")
                    for ii in file_list:
                        shutil.move(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\" + ii, r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\Atoll_export\\" + ii)
                    shutil.make_archive(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\" + sitee, 'zip', r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\Atoll_export\\")
                    for ii in file_list:
                        os.remove(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\Atoll_export\\" + ii)
                    shutil.rmtree(r"D:\Atoll_projects_planer01\Pokrivanja\Upravicenost_bazne_postaje\\" + sitee + "\\Atoll_export\\")
                stev = stev + 1

            else:
                ni_slo_skozi.append(preverba_lokacije(seznam_lokacij)[5])
        except:
            print("=== NAPAKA pri lokaciji ===")
            print(traceback.format_exc())
            ni_slo_skozi.append(preverba_lokacije(seznam_lokacij)[5])

    print("================== KONEC ====================")
    print("Spodnje lokacije niso izračunane:\n")
    for i in ni_slo_skozi:
        print(i)
        # else:
            # print("Lokacija ne obstaja!")
