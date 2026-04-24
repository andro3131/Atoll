# -*- coding: utf-8 -*-

###########################################################
#   Za potrebe reportinga naredimo export 100*100m iz Atoll-a
#   Naredimo export vseh tehnologij: GSM, LTE, NR in nato še NSA (vse frekvence)
#
###########################################################

import subprocess
# import pyodbc
import sql_atoll_3794
import time
import os
import funkcije_at
import pandas as pd
import shutil
import re
import datetime
from df_to_tiff import naredi_tif1
import naredi_shp_za_112


nsa_correction = True # NSA - Non Stand Alone correction - pokrivanje na anchor celici
po_celicah = False  # Za export planiranega stanja ali pa iz seznama celic. Celice, ki niso delujoče. Pred tem jih je potrebno aktivirati/dodati v Atoll-u

t0 = time.time()

odlozisce_2  = "D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\export_zacasni_2.txt"
#ukaz = "C:\\PROGRA~1\\Forsk\\Add-ins\\SIGNAL~1\\signalsexport "    SPREMENJENO ANDREJ 13.4.2026
ukaz = "C:\\PROGRA~1\\Forsk\\Add-ins\\SignalsExport\\signalsexport "
at_dok_3794 = "D:\\Atoll_projects_planer01\\Atoll_exporti_3794_3_5_1.ATL"
#mapa_ini_file = "C:\\PROGRA~1\\Forsk\\Add-ins\\SIGNAL~1\\"     SPREMENJENO ANDREJ 13.4.2026
mapa_ini_file = "C:\\PROGRA~1\\Forsk\\Add-ins\\SignalsExport\\"
# odlozisce_reporting = r"G:\Pokrivanja\Odlozisce_reporting\\"
# odlozisce_reporting = r"G:\Razno\Odlozisce_reporting_1_12_2023\\"
mapa_krmilna_tabela = "D:\\Atoll_projects_planer01\\Export_coverage_krmilna_tabela.xlsx"
celice_seznam = "D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\Planirane_celice\\planirane_celice.csv"


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
    body_df = funkcije_at.pd.DataFrame(body)
    body_df = body_df[0].str.split(r"\t|;", expand = True)
    body_df[0] = body_df[0].str.replace(".","")
    body_df[1] = body_df[1].str.replace(".","")
    return gl, body_df

def stevilo_streznikov():
    pass
    
def export_seznam_celic(seznam_celic, ime_fajla, krmilna_tabela):
    """
    Če je uporabljen filter oziroma predpisan seznam celic
    """
    if type(seznam_celic) == list:
        seznam = seznam_celic
    elif type(seznam_celic) == str:
        celice_df = funkcije_at.pd.read_csv(seznam_celic)
        seznam = celice_df['cell1'].drop_duplicates().tolist()
    else:
        seznam = []

    print("======================") 
    print(seznam)
    print("======================") 
    if len(seznam) > 0:
        for j in seznam:
            sez_zac = ime_fajla.split("|")
            # print(sez_zac)
            if len(sez_zac) > 1:
                file_odpri_2 = open(odlozisce_2,"a")
                file_odpri_2.write("(" + sez_zac[0][0:len(sez_zac[0])-2] + " & ([TX_ID] = " + j + ")) | " + sez_zac[1][0:len(sez_zac[1])-1] + " & ([TX_ID] = " + j + "))) | ")
                print("(" + sez_zac[0][0:len(sez_zac[0])-2] + " & ([TX_ID] = " + j + ")) | " + sez_zac[1][0:len(sez_zac[1])-1] + " & ([TX_ID] = " + j + "))) | ")
                file_odpri_2.close()
            else:
                file_odpri_2 = open(odlozisce_2,"a")
                file_odpri_2.write("(" + sez_zac[0][0:len(sez_zac[0])] + " & ([TX_ID] = " + j + ")) | ")
                print("(" + sez_zac[0][0:len(sez_zac[0])] + " & ([TX_ID] = " + j + ")) | ")
                file_odpri_2.close()
        file_odpri_2 = open(odlozisce_2,"r+")
        f_read = file_odpri_2.readlines()
        file_odpri_2.close()
        f_read = f_read[0][0:len(f_read[0])-2]
        file_odpri_2 = open(odlozisce_2, 'w')
        file_odpri_2.writelines(f_read)
        file_odpri_2.close()
    else:
        pass
    return 0

def naredi_best_server_kompozit(tehnologija, folder, odlozisce, planirano = False, nabor_tehnologij = []):
    """
    Tehnologija: 'GSM','LTE','NR','NSA'
    nabor_tehnologij: tukaj specificiramo točna imena ascii filetov za izračun kompozita
    """
    bs = pd.DataFrame()
    tehnos = []
    for i in os.listdir(folder):
        if (planirano == False) & (i.find(tehnologija) >= 0):  
            if i.find("_1_w")> 0: # trenutno delujoce
                tehnos.append(i)    
                print(tehnos)
            else:
                pass
        elif (planirano == True) & (i.find(tehnologija) >= 0):
            if i.find("_1_p")> 0:    # planirane
                tehnos.append(i) 
                # print(tehnos)                
            else:
                pass
    for i in tehnos:
        if (i.find('RES_50') >= 0) | (i.find('BANDWIDTH') >= 0) | (i.find('filtrirano') >= 0):
            tehnos.remove(i)
    print(tehnos)
    # tehnos = ['LTE_700_1_w.txt', 'LTE_800_1_w.txt', 'LTE_900_1_w.txt', 'LTE_1800_1_w.txt', 'LTE_2100_1_w.txt', 'LTE_2600_1_w.txt']
    for i in tehnos:
        temp = beri_atoll_txt_export(folder + i)[1]
        temp = temp[[0,1,2,3]]
        temp[3] = temp[3].astype(float)
        print(temp.shape)
        bs = funkcije_at.pd.concat([bs, temp])
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
    return bs_.to_csv(odlozisce + tehnologija + ".txt", index = False)     

def naredi_best_server_kompozit1(tehnologija, folder, odlozisce, planirano = False, nabor_tehnologij = [], ime = ''):
    """
    Tehnologija: 'GSM','LTE','NR','NSA'
    nabor_tehnologij: tukaj specificiramo točna imena ascii filetov za izračun kompozita. Mora vsebovati vsaj dve tehnologiji
    """
    bs = pd.DataFrame()
    tehnos = []
    if len(nabor_tehnologij) > 1:
        tehnos = nabor_tehnologij
        ime_ = "__".join([i.split("_1_w.txt")[0] for i in nabor_tehnologij])
    else:
        for i in os.listdir(folder):
            if (planirano == False) & (i.find(tehnologija) >= 0):  
                if i.find("_1_w")> 0: # trenutno delujoce
                    tehnos.append(i)    
                    print(tehnos)
                else:
                    pass
            elif (planirano == True) & (i.find(tehnologija) >= 0):
                if i.find("_1_p")> 0:    # planirane
                    tehnos.append(i) 
                    # print(tehnos)                
                else:
                    pass
    if ime != '':
        ime_ = ime
    else:
        pass
    for i in tehnos:
        if (i.find('RES_50') >= 0) | (i.find('BANDWIDTH') >= 0) | (i.find('filtrirano') >= 0):
            tehnos.remove(i)
    print(tehnos)
    # tehnos = ['LTE_700_1_w.txt', 'LTE_800_1_w.txt', 'LTE_900_1_w.txt', 'LTE_1800_1_w.txt', 'LTE_2100_1_w.txt', 'LTE_2600_1_w.txt']
    for i in tehnos:
        temp = beri_atoll_txt_export(folder + i)[1]
        temp = temp[[0,1,2,3]]
        temp[3] = temp[3].astype(float)
        print(temp.shape)
        bs = funkcije_at.pd.concat([bs, temp])
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
    if len(nabor_tehnologij) > 1:
        return bs_.to_csv(odlozisce + ime_ + ".txt", index = False)
    else:
        return bs_.to_csv(odlozisce + tehnologija + ".txt", index = False)    
    
    
def naredi_best_server_kompozit_izvzeto(tehnologija, folder, odlozisce, planirano = False, izvzete_celice = [], izvzete_lokacije= []):
    """
    Tehnologija: 'GSM','LTE','NR','NSA'
    """
    bs = pd.DataFrame()
    tehnos = []
    for i in os.listdir(folder):
        if (planirano == False) & (i.find(tehnologija) >= 0):  
            if i.find("_1_w")> 0: # trenutno delujoce
                tehnos.append(i)    
                print(tehnos)
            else:
                pass
        elif (planirano == True) & (i.find(tehnologija) >= 0):
            if i.find("_1_p")> 0:    # planirane
                tehnos.append(i) 
                # print(tehnos)                
            else:
                pass
    for i in tehnos:
        if (i.find('RES_50') >= 0) | (i.find('BANDWIDTH') >= 0) | (i.find('filtrirano') >= 0):
            tehnos.remove(i)
    print(tehnos)
    # tehnos = ['LTE_700_1_w.txt', 'LTE_800_1_w.txt', 'LTE_900_1_w.txt', 'LTE_1800_1_w.txt', 'LTE_2100_1_w.txt', 'LTE_2600_1_w.txt']
    for i in tehnos:
        # temp = beri_atoll_txt_export(folder + i)[1]
        temp = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(folder + i, n = 2)
        if len(izvzete_lokacije) > 0:
            for j in izvzete_lokacije:
                for k in temp[2].drop_duplicates().tolist():
                    if k.find(j) >= 0:
                        izvzete_celice.append(k)
                    else:
                        pass
                for k in temp[4].dropna().drop_duplicates().tolist():
                    if k.find(j) >= 0:
                        izvzete_celice.append(k)
                    else:
                        pass
        else:
            pass
        if len(izvzete_celice) > 0:
            temp2 = temp[[0,1,4,5]].dropna().rename(columns = {4:2,5:3})
            temp2 = temp2[~temp2[2].isin(izvzete_celice)]
            temp = temp[[0,1,2,3]]
            temp[3] = temp[3].astype(float)
            izb = temp[temp[2].isin(izvzete_celice)]
            if izb.shape[0] > 0:
                temp = temp[~temp.index.isin(izb.index)]
                temp = pd.concat([temp, izb])
            else:
                pass
        else:
            temp = temp[[0,1,2,3]]
            temp[3] = temp[3].astype(float)
        print(temp.shape)
        bs = funkcije_at.pd.concat([bs, temp])
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
    return bs_.to_csv(odlozisce + tehnologija + "_filtrirano.txt", index = False)   

def izvzemi_celice_iz_ascii_exporta(mapa, fajl, seznam_celic = []):
    temp = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(mapa + fajl, n = 6, vsebuje = seznam_celic, header_list = True)
    g = temp[0]
    temp = temp[1]
    s = funckije_at.pd.DataFrame()
    for i in range(2, 14, 2):
        temp_ = temp[[0,1,i,i+1]]
        temp_.columns = [0,1,2,3]
        tmp = funckije_at.pd.concat([tmp,temp_.dropna()])
    skupaj = tmp.groupby([0,1]).agg({2:list, 3:'max'})
    skupaj[2] = skupaj[2].str.join(",")
    skupaj[2] = skupaj[2].str.get(0)
    return g, skupaj
        
def kompozit_iz_dfjev(odlozisce, ime, seznam_dfjev = []):
    tmp = funckije_at.pd.DataFrame()
    g = seznam_dfjev[0][0]
    for i in seznam_dfjev:
        tmp = funckije_at.pd.concat([tmp, i[1]])
    skupaj = tmp.groupby([0,1]).agg({2:list, 3:'max'})
    skupaj[2] = skupaj[2].str.join(",")
    skupaj[2] = skupaj[2].str.get(0)
    with open(odlozisce + ime, "w") as zz:
        zz.write("\n".join(g))
        zz.write("\n")
    return skupaj.to_csv(odlozisce + ime, header = None, index = False, mode = 'a')

def lte_m(mapa, odlozisce, ime): 
    a = naredi_shp_za_112.ericsson_enm_tabele.lte_m_celice()
    df = funkcije_at.pd.DataFrame(a)
    df[['cell','tehnologija','atoll_fband','tehnol', 'frekvenca']] = df[[0]].apply(lambda x: funkcije_at.pripona(x[0]),axis=1, result_type = 'expand')        
    teh = [(i.replace(" ","_") + "_1_w.txt") for i in df['tehnol'].drop_duplicates().tolist()]
    o = []
    for i in teh:
        m = izvzemi_celice_iz_ascii_exporta(mapa, i, seznam_celic = a)
        print(m)
        o.append(m)
    kompozit_iz_dfjev(odlozisce = odlozisce, ime = ime, seznam_dfjev = o)
    return 0
    
def naredi_best_server_kompozit_z_bandwithom(tehnologija, folder, odlozisce, planirano = False, bw_min = 20, agregac = 'brez', nabor_tehnologij = []):
    """
    Na vsak bin se preveri skupen bandwidth. Se pravi, če na nek bin pade LTE 800 (10 MHz), LTE 700 (10 MHz) in LTE 1800 (20 MHz) pomeni skupnih 10+10+20 = 40 MHz. 
    Tehnologija: 'LTE','NR','NSA'
    Informacijo o bandwidthu potegnemo iz Atoll-a.
    agregac = 'brez','cosite','cosektor'
        'brez' = upoštevamo katerikoli signal na binu pri agregaciji na bin
        'cosite' = upoštevamo katerikoli signal, ki je na istem site-u kot best server pri agregaciji bin
        'cosektor' = upoštevamo katerikoli signal, ki je na istem sektorju-u kot best server pri agregaciji na bin
    nabor_tehnologij: če je večji od 1 se naredi kompozit tehnologij v seznamu
    """
    bs = pd.DataFrame()
    tehnos = []
    tehnos = []
    if len(nabor_tehnologij) > 1:
        tehnos = nabor_tehnologij
        tehnologija = "__".join([i.split("_1_w.txt")[0] for i in nabor_tehnologij])
    else:
        for i in os.listdir(folder):
            if (planirano == False) & (i.find(tehnologija) >= 0):  
                if i.find("_1_w")> 0: # trenutno delujoce
                    tehnos.append(i)    
                    print(tehnos)
                else:
                    pass
            elif (planirano == True) & (i.find(tehnologija) >= 0):
                if i.find("_1_p")> 0:    # planirane
                    tehnos.append(i) 
                    # print(tehnos)                
                else:
                    pass
    
        teh1 = [i for i in tehnos if i.find("RES_50") < 0]
        teh2 = [i for i in teh1 if i.find("LTE_1_w.") < 0]
        tehnos = teh2
    print(tehnos)
    xgcells = pd.read_sql(sql_atoll_3794.xgcellslte_atoll, sql_atoll_3794.conn_atoll)
    xgcells = xgcells[~xgcells['TX_ID'].str.contains('Copy of')]
    xgcells = xgcells[~xgcells['CARRIER'].str.contains('Copy of')]
    xgcells['BW'] = xgcells['CARRIER'].str.split(" MHz", expand = True)[0].astype(int)
    xgcells = xgcells[['TX_ID','BW']].drop_duplicates()
    xgcelln = pd.read_sql(sql_atoll_3794.xgcells5gnr_atoll, sql_atoll_3794.conn_atoll)
    xgcelln = xgcelln[~xgcelln['TX_ID'].str.contains('Copy of')]
    xgcelln = xgcelln[~xgcelln['CARRIER'].str.contains('Copy of')]
    xgcelln['BW'] = xgcelln['CARRIER'].str.split(" MHz", expand = True)[0].astype(int)
    xgcelln = xgcelln[['TX_ID','BW']].drop_duplicates()
    xgcells = pd.concat([xgcells, xgcelln])
    xgcells_dict = dict(zip(xgcells['TX_ID'].tolist(), xgcells['BW'].tolist()))
        
    # tehnos = ['LTE_700_1_w.txt', 'LTE_800_1_w.txt', 'LTE_900_1_w.txt', 'LTE_1800_1_w.txt', 'LTE_2100_1_w.txt', 'LTE_2600_1_w.txt']
    for i in tehnos:
        temp = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(folder + i,n=1,header_list = True)
        h = temp[1]
        temp = temp[0]  
        temp[3] = temp[3].astype(float)
        # t = beri_atoll_txt_export(folder + i)
        # h= t[0]
        # temp = t[1]
        # temp = temp[[0,1,2,3]]
        temp[3] = temp[3].astype(float)
        temp[4] = temp[2].map(xgcells_dict)
        print(temp.shape)
        bs = funkcije_at.pd.concat([bs, temp])
    bs = bs.reset_index(drop = True)
    # bs[5] = bs[2].str[-1].apply(funkcije_at.sektor)
    # bs[6] = bs[2].str.split(r"\d+", expand = True)[0] + "_" + bs[5].astype(str)
    
    print(bs)
    if agregac == 'brez':
        bs_ = bs.groupby([0,1]).agg({3:'max', 4:'sum'}).reset_index()
        bs_ = bs_[bs_[4]>= bw_min]
        bs_.drop(columns = 4, inplace = True)
        bs_ = bs_.groupby([0,1])[3].max().reset_index()
        # bs_.to_csv(odlozisce +"AAAAAAAA.txt", index = False)
        print("==========")
        print(bs_)
        bs_ = bs_.merge(bs, how = 'inner', left_on = [0,1,3], right_on = [0,1,3])
        bs_['vrstni_red'] = bs_.sort_values(by = [0,1,2,3], ascending = [True, True, False, True]).groupby([0,1,3]).cumcount() + 1
        bs_ = bs_[bs_['vrstni_red'] == 1]
        bs_ = bs_[[0,1,2,3]]
        bs = bs[[0,1]].drop_duplicates()
    elif agregac == 'cosite':
        bs[5] = bs[2].str.split(r"\d+", expand = True)[0]
        bs_ = bs.groupby([0,1,5]).agg({3:'max', 4:'sum'}).reset_index()
        bs_ = bs_[bs_[4]>= bw_min]
        bs_.drop(columns = [4,5], inplace = True)
        bs_ = bs_.groupby([0,1])[3].max().reset_index()
        # bs_.to_csv(odlozisce +"AAAAAAAA.txt", index = False)
        print("==========")
        print(bs_)
        bs_ = bs_.merge(bs, how = 'inner', left_on = [0,1,3], right_on = [0,1,3])
        bs_['vrstni_red'] = bs_.sort_values(by = [0,1,2,3], ascending = [True, True, False, True]).groupby([0,1,3]).cumcount() + 1
        bs_ = bs_[bs_['vrstni_red'] == 1]
        bs_ = bs_[[0,1,2,3]]
        bs = bs[[0,1]].drop_duplicates()
    elif agregac == 'cosektor':
        bs[5] = bs[2].str[-1].apply(funkcije_at.sektor)
        bs[5] = bs[2].str.split(r"\d+", expand = True)[0] + "_" + bs[5].astype(str)
        bs_ = bs.groupby([0,1,5]).agg({3:'max', 4:'sum'}).reset_index()
        bs_ = bs_[bs_[4]>= bw_min]
        bs_.drop(columns = [4,5], inplace = True)
        bs_ = bs_.groupby([0,1])[3].max().reset_index()
        # bs_.to_csv(odlozisce +"AAAAAAAA.txt", index = False)
        print("==========")
        print(bs_)
        bs_ = bs_.merge(bs, how = 'inner', left_on = [0,1,3], right_on = [0,1,3])
        bs_['vrstni_red'] = bs_.sort_values(by = [0,1,2,3], ascending = [True, True, False, True]).groupby([0,1,3]).cumcount() + 1
        bs_ = bs_[bs_['vrstni_red'] == 1]
        bs_ = bs_[[0,1,2,3]]
        bs = bs[[0,1]].drop_duplicates()
    else:
        bs_ = bs
    resolution = int(h[2].split("\t")[1].strip("\n"))
    with open(odlozisce + tehnologija + "_" + str(bw_min) + "_" + agregac + "_BANDWIDTH.txt", "w") as zz:
        zz.write("type\t{}\n".format("KOMPOZIT_" + tehnologija))
        zz.write("timestamp\t{}\n".format('Prazno'))
        zz.write("resolution\t{}\n".format(resolution))
        zz.write("xmin\t{}\n".format(bs_[0].astype(int).min()))
        zz.write("xmax\t{}\n".format(bs_[0].astype(int).max()))
        zz.write("ymin\t{}\n".format(bs_[1].astype(int).min()))
        zz.write("ymax\t{}\n".format(bs_[1].astype(int).max()))
        zz.write("x_num_pixels\t{}\n".format(int((bs_[0].astype(int).max() - bs_[0].astype(int).min())/resolution)))
        zz.write("y_num_pixels\t{}\n".format(int((bs_[1].astype(int).max() - bs_[1].astype(int).min())/resolution)))
        zz.write("\n")
        zz.write("\n")
        zz.close()
    return bs_.to_csv(odlozisce + tehnologija + "_" + str(bw_min) + "_" + agregac + "_BANDWIDTH.txt", sep = ";",mode = 'a', header = None, index = False)     

def nafilaj_prazno(xmin = 322385, xmax = 669485, ymin = 23130, ymax = 201030, resolucija = 25):
    x = list(range(xmin, xmax, resolucija))
    y = list(range(ymin, ymax, resolucija))
    xy = []
    for i in x:
        for j in y:
            xy.append(str(i) + ";" + str(j))
    return xy
    

def naredi_ascii_export_iz_df(df, odlozisce, ime, resolucija = 100):
    mm = df[[2]].apply(lambda x: funkcije_at.pripona(x[2]), axis = 1, result_type = 'expand')
    tehnologija= mm[1].drop_duplicates()[0]
    print(tehnologija)
    timestamp = str(datetime.datetime.now().day) + "." + str(datetime.datetime.now().month) + "." + str(datetime.datetime.now().year)
    print(timestamp)
    res = resolucija
    print(res)
    xmin = int(df[0].min())
    print(xmin)
    ymin = int(df[1].min())
    print(ymin)
    print(df[0].min())
    print(df[0].max())
    ncols = int(abs(df[0].min() - df[0].max()) / res) + 1
    nrows = int(abs(df[1].min() - df[1].max()) / res) + 1
    with open(odlozisce + ime, "w") as zz:
        zz.write("type\t{}\n".format(tehnologija))
        zz.write("timestamp\t{}\n".format(timestamp))
        zz.write("resolution\t{}\n".format(res))
        zz.write("xmin\t{}\n".format(xmin))
        zz.write("xmax\t{}\n".format(xmin + (ncols - 1)*res))
        zz.write("ymin\t{}\n".format(ymin))
        zz.write("ymax\t{}\n".format(ymin + (nrows - 1)*res))
        zz.write("x_num_pixels\t{}\n".format(ncols))
        zz.write("y_num_pixels\t{}\n".format(nrows))
        zz.write("\n")
        zz.write("\n")
        zz.close()
    df.to_csv(odlozisce + ime, mode = "a", header = None, index  =False, sep = ";")
    return 0


def spremeni_resolucijo_ascii(mapa, ascii_file, odlozisce):
    """
    Funkcija spremeni resolucijo fileja. Nova resolucija mora biti mnogokratnik predhodne. 
    Trenutna funckija spremeni samo iz resoloucijo 100 v 50 in samo za 1 server
    """
    temp = beri_atoll_txt_export(mapa + ascii_file)
    temp_ = temp[1]
    temp_ = temp_[[0,1,2,3]]
    temp_[0] = temp_[0].astype(int)
    temp_[1] = temp_[1].astype(int)
    t0 = pd.DataFrame()
    temp_1_0 = temp_.reset_index(drop = True)
    temp_1_0[0] = temp_1_0[0] + 50
    temp_0_1 = temp_.reset_index(drop = True)
    temp_0_1[1] = temp_0_1[1] + 50
    temp_1_1 = temp_.reset_index(drop = True)
    temp_1_1[0] = temp_1_1[0] + 50
    temp_1_1[1] = temp_1_1[1] + 50
    t0 = pd.concat([temp_, temp_1_0, temp_0_1, temp_1_1])
    print(t0[0].min)
    with open(odlozisce + ascii_file.strip(".txt") + "_RES_50.txt", "w") as zz:
        zz.write("type\t{}\n".format(temp[0]['type']))
        zz.write("timestamp\t{}\n".format(temp[0]['timestamp']))
        zz.write("resolution\t{}\n".format(50))
        zz.write("xmin\t{}\n".format(t0[0].min()))
        zz.write("xmax\t{}\n".format(t0[0].max()))
        zz.write("ymin\t{}\n".format(t0[1].min()))
        zz.write("ymax\t{}\n".format(t0[1].max()))
        zz.write("x_num_pixels\t{}\n".format(int((t0[0].max() - t0[0].min())/50)))
        zz.write("y_num_pixels\t{}\n".format(int((t0[1].max() - t0[1].min())/50)))
        zz.write("\n")
        zz.write("\n")
        zz.close()
    t0.to_csv(odlozisce + ascii_file.strip(".txt") + "_RES_50.txt", mode = "a", header = None, index  =False, sep = ";")  
    return t0.dtypes
        
def razlika_pokrivanj_ascii(ascii_file_1, ascii_file_2, odlozisce = "G:\\Razno\\"):
    """
    Vhodna podatka sta polni poti do ascii filejev.
    Izhodni podatki so: razlika celic (best server), razlika pokrivanj (best server)
    """
    ascii1 = beri_atoll_txt_export(ascii_file_1)
    ascii2 = beri_atoll_txt_export(ascii_file_2)
    ascii1_1 = ascii1[1]
    ascii2_1 = ascii2[1]
    ascii1_1 = ascii1_1[[0,1,2,3]]
    ascii2_1 = ascii2_1[[0,1,2,3]]
    outer = pd.merge(ascii1_1, ascii2_1, how = 'outer', left_on = [0,1], right_on = [0,1])
    inner1 = pd.merge(ascii1_1, ascii2_1, how = 'inner', left_on = [0,1], right_on = [0,1])
    inner2 = pd.merge(ascii1_1, ascii2_1, how = 'inner', left_on = [0,1,2], right_on = [0,1,2])
    inner2[['3_y','3_x']] = inner2[['3_y','3_x']].astype(float)
    inner2['razlika_moci'] = inner2['3_y'] - inner2['3_x']
    ascii1_1_celice = ascii1_1[2].drop_duplicates().tolist()
    ascii2_1_celice = ascii2_1[2].drop_duplicates().tolist()
    razlika_celic_plus = [i for i in ascii2_1_celice if i not in ascii1_1_celice]
    razlika_celic_minus  = [i for i in ascii1_1_celice if i not in ascii2_1_celice]
    razlika_pokrivanj_plus = outer[outer['2_x'].isna()]
    razlika_pokrivanj_plus.drop(columns = ['2_x','3_x'], inplace = True)
    razlika_pokrivanj_plus.rename(columns = {'2_y':2,'3_y':3}, inplace = True)
    razlika_pokrivanj_plus[3] = razlika_pokrivanj_plus[3].astype(float)
    razlika_pokrivanj_plus[[0,1]] = razlika_pokrivanj_plus[[0,1]].astype(int)
    print(razlika_pokrivanj_plus.dtypes)
    razlika_pokrivanj_minus = outer[outer['2_y'].isna()]
    razlika_pokrivanj_minus.drop(columns = ['2_y','3_y'], inplace = True)
    razlika_pokrivanj_minus.rename(columns = {'2_x':2,'3_x':3}, inplace = True)
    razlika_pokrivanj_minus[3] = razlika_pokrivanj_minus[3].astype(float)
    razlika_pokrivanj_minus[[0,1]] = razlika_pokrivanj_minus[[0,1]].astype(int)
    naredi_tif1(razlika_pokrivanj_plus, odlozisce = odlozisce, tip = 'df', resolution = 100, ime = 'razlika_plus', treshold = -105, x_offset = 50, y_offset = 200)
    naredi_tif1(razlika_pokrivanj_minus, odlozisce = odlozisce, tip = 'df', resolution = 100, ime = 'razlika_minus', treshold = -105, x_offset = 50, y_offset = 200) 
    return 0

def pop_area_stack(folder, datum, niz = "", odlozisce = ""):
    t = pd.DataFrame()
    for i in os.listdir(folder):
        if i.find(niz) >= 0:
            temp = pd.read_excel(folder + i)
            temp.drop(columns = [i for i in temp.columns.tolist() if i.find("Unname") >= 0], inplace = True)
            temp['TEHNOLOGIJA'] = i.removesuffix(niz)   # strip naredi napako, zamenjamo z removesuffix!!!
            temp['DATUM'] = datum
            temp['RESOLUCIJA'] = 100
            temp['ORODJE'] = 'Atoll'
            t = pd.concat([t, temp])
    date_check = pd.read_csv(odlozisce)
    if datum not in date_check['DATUM'].drop_duplicates().tolist():
        t.to_csv(odlozisce, mode = "a", index = False, header = None)
    else:
        pass
    return 0
    
# def main(export_seznam_celic = False, nsa_corection = False, kopiranje_na_mrezni_disk = "", export_resolucija = 25):
def export_pokrivanj(po_celicah = False, odlozisce_pokrivanja = r"G:\Pokrivanja\Odlozisce_reporting\\"):



    """
    export_seznam_celic:
    nsa_corection:
    kopiranje_na_mrezni_disk:
    export_resolucija:
    """
    # izbrisi obstojece fileje, ki se zaključijo z 1_w.txt
    # po_celicah = True
    # odlozisce_pokrivanja = r"G:\Pokrivanja\Odlozisce_reporting\\"
    # odlozisce_pokrivanja = r"G:\Razno\Odlozisce_reporting_1_12_2023\\"
    for i in os.listdir(odlozisce_pokrivanja):
        if (i.find("_1_w.txt") > 0):
            os.remove(odlozisce_pokrivanja + i)

    krm_tab_df = funkcije_at.pd.read_excel(mapa_krmilna_tabela)
    krm_tab_df["Export_da_ne"] = True
    krm_tab_df.loc[(krm_tab_df["ime_fajla"].isin(['NBIOT_800','NBIOT_900','NBIOT_1800', 'UMTS_2100'])), "Export_da_ne"] = False
    # krm_tab_df["Export_da_ne"] = False
    # krm_tab_df.loc[(krm_tab_df["ime_fajla"].isin(['NR_700'])), "Export_da_ne"] = True
    krm_tab_df = krm_tab_df[krm_tab_df["Export_da_ne"] == True]
    print(krm_tab_df)
    for i in krm_tab_df.index:
        print(i)
        t_a = time.time() 
        file_odpri = open(odlozisce_2,"w")
        file_odpri.write('')
        file_odpri.close()
        if krm_tab_df.loc[i,"Export_da_ne"] == True:
            if po_celicah == True:
                export_seznam_celic(celice_seznam, krm_tab_df.loc[i, 'tehn'], krm_tab_df)    
            else:
                file_odpri_2 = open(odlozisce_2,"w")
                file_odpri_2.write(krm_tab_df.loc[i, "tehn"])
                file_odpri_2.close()
                krm_tab_df.loc[i, "tehn"]

        ini_file = krm_tab_df.loc[i,"ini_file_3794_100_slovar"]
        at_dok_3794 = krm_tab_df.loc[i,"atoll_dokument"]
        # odlozisce_pokrivanja = odlozisce_reporting
        print(ini_file)
        folder = krm_tab_df.loc[i, "folder_slovar"]
        ime = krm_tab_df.loc[i,  "ime_fajla"]
        t_c = time.time()
        print(ime)
        print(krm_tab_df.loc[i,"tehn"])
        print(at_dok_3794)
        print(odlozisce_pokrivanja)
        
        # Nastavitev filtra

        subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\skripta_filter_atoll_iz_aplikacije_3794.vbs'],  capture_output=True,  text=True)
            
        t_d = time.time()
        print(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt")   
        subprocess.run(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt", shell = True)   # Izračun predikcije
        t_b = time.time()
        print("Cas izvajanja izračuna tehnologije {} je {} minut. Cas izvajanja filtra je {} s".format(ime, (t_b - t_a)/60, t_d - t_c))
        print("\n")
    # Rename
    for i in os.listdir(odlozisce_pokrivanja):
        if po_celicah == False:
            if (i.find(".txt") > 0) & (i.find("[") > 0):
                os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + re.sub(r'\[[A-Z|5G NR]+]' , '1_w', i))
        else:
            if (i.find(".txt") > 0) & (i.find("[") > 0):
                os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + re.sub(r'\[[A-Z|5G NR]+]' , '1_p', i))

def presek_pokrivanj(seznam = [], odlozisce = '', ime = '', treshold = -108, razlika = 10):
    """
    seznam: polne poti do ascii filetov pokrivanj
    Resolucija pokrivanj mora biti enaka!
    treshold: zahtevan nivo signala best serverja
    razlika: kakšno razliko med best serverjem in ostalimi prekrivnimi layerji na bin še dovoljujemo. Mora biti 0 ali več (pozitivna vrednost)
    """
    if len(seznam) < 2:
        return print("Potrebni sta vsaj dve datoteki pokrivanj!")
    else:
        uu = pd.DataFrame()
        uuu = pd.DataFrame()
        stevec = 0
        for i in seznam:
            temp = naredi_shp_za_112.beri_atoll_txt_export_1_n_server(i,n=1,header_list = True)
            h = temp[1]
            temp = temp[0]
            # temp[0] = temp[0].astype(int)
            # temp[1] = temp[1].astype(int)    
            temp[3] = temp[3].astype(float)
            # temp = temp[temp[3] >= treshold]
            uuu = pd.concat([uuu,temp])
            if stevec == 0:
                uu = temp
            else:
                uu = uu.merge(temp, how = 'inner', left_on = [0,1], right_on = [0,1])   
            stevec = stevec + 1
        uu = uu[[0,1]].drop_duplicates().reset_index(drop = True)

        uuu = uuu.merge(uu, how = 'inner', left_on = [0,1], right_on = [0,1])
        uuu['koord'] = uuu[0].astype(str) + "_" + uuu[1].astype(str)
        uuu = uuu.sort_values(by = ['koord', 3] , ascending = [True, False])
        uuu['vrstni_red'] = uuu.sort_values(by = ['koord', 3] , ascending = [True, False]).groupby(['koord']).cumcount()
        uuu0 = uuu[uuu['vrstni_red'] == 0]
        uuu1 = uuu[uuu['vrstni_red'] > 0].rename(columns = {2:'2_',3:'3_', 'vrstni_red': 'vrstni_red_'})
        uuu_ = uuu0.merge(uuu1, how = 'inner', left_on = [0,1,'koord'], right_on = [0,1,'koord'])
        uuu_['razlika'] = uuu_[3] - uuu_['3_']
        uuu_= uuu_[uuu_['razlika'] <= razlika ]
        uuu_ = uuu_[uuu_[3] >= treshold]
        uuu2 = pd.concat([uuu_[[0,1,2,3,'koord', 'vrstni_red']], uuu_[[0,1,'2_','3_','koord', 'vrstni_red_']].rename(columns = {'2_':2,'3_':3, 'vrstni_red_': 'vrstni_red'})]).drop_duplicates()
        
        uuu2g = uuu2[['koord',2]].groupby(['koord']).agg({2:list}).reset_index()
        uuu3 = uuu2[uuu2['vrstni_red'] == 0].merge(uuu2g, how = 'inner', left_on = 'koord', right_on = 'koord')
        uuug2 = uuu3[[0,1,'2_y',3]].rename(columns = {'2_y':2})
        resolution = int(h[2].split("\t")[1].strip("\n"))
        # uuug = uuu.groupby([0,1])[3].max().reset_index()
        # uuug = 
        # uuug1 = uuu.merge(uuug, how = 'inner', left_on = [0,1,3], right_on = [0,1,3])
        # uuug1 = uuug1.merge(uu, how = 'inner', left_on = [0,1], right_on = [0,1])
        # uuug1['vrstni_red'] = uuug1.sort_values(by = [0,1,3]).groupby([0,1,3]).cumcount()
        # uuug1_0 = uuug1[uuug1['vrstni_red'] == 0]
        # uuug1_0 = uuug1_0[uuug1_0[3] >= treshold]
        # uuug1_1 = uuug1[uuug1['vrstni_red'] > 0]
        # uuug1_1 = uuug1_1.merge(uuug1_0[[0,1,2,3]].rename(columns = {2:'2_',3:'3_'}), how = 'inner', left_on = [0,1], right_on = [0,1])
        # uuug1_1['razlika'] = uuug1_1['3_'] - uuug1_1[3]
        # uuug1_1 = uuug1_1[uuug1_1['razlika']<= razlika]
        # uuug1_2 = pd.concat([uuug1_1[[0,1,'2_','3_']].rename(columns = {'2_':2,'3_':3}), uuug1_1[[0,1,2,3]]])
        # uuug2 = uuug1_2.groupby([0,1]).agg({2:list, 3:'max'}).reset_index(drop=True)
        with open(odlozisce + ime + ".txt", "w") as zz:
            zz.write("type\t{}\n".format("PRESEK"))
            zz.write("timestamp\t{}\n".format('Prazno'))
            zz.write("resolution\t{}\n".format(resolution))
            zz.write("xmin\t{}\n".format(uuug2[0].astype(int).min()))
            zz.write("xmax\t{}\n".format(uuug2[0].astype(int).max()))
            zz.write("ymin\t{}\n".format(uuug2[1].astype(int).min()))
            zz.write("ymax\t{}\n".format(uuug2[1].astype(int).max()))
            zz.write("x_num_pixels\t{}\n".format(int((uuug2[0].astype(int).max() - uuug2[0].astype(int).min())/resolution)))
            zz.write("y_num_pixels\t{}\n".format(int((uuug2[1].astype(int).max() - uuug2[1].astype(int).min())/resolution)))
            zz.write("\n")
            zz.write("\n")
            zz.close()
        uuug2.to_csv(odlozisce + ime + ".txt", mode = "a", header = None, index  =False, sep = ";") 
        return 0
        
    

def export_pokrivanj_1(po_celicah = False, odlozisce_pokrivanja = r"G:\Pokrivanja\Odlozisce_reporting\\", krm_tab_set = False, ime_lokacije = '', ime_fajla = '', ini_file_set = ''):
    """
    export_seznam_celic:
    nsa_corection:
    kopiranje_na_mrezni_disk:
    export_resolucija:
    """
    # izbrisi obstojece fileje, ki se zaključijo z 1_w.txt
    # po_celicah = True
    # odlozisce_pokrivanja = r"G:\Pokrivanja\Odlozisce_reporting\\"
    # odlozisce_pokrivanja = r"G:\Razno\Odlozisce_reporting_1_12_2023\\"
    for i in os.listdir(odlozisce_pokrivanja):
        if (i.find("_1_w.txt") > 0):
            os.remove(odlozisce_pokrivanja + i)
    if krm_tab_set == True:
        krm_tab_df = funkcije_at.pd.read_excel(mapa_krmilna_tabela)
    else:
        krm_tab_df = funkcije_at.pd.read_excel(mapa_krmilna_tabela)
        krm_tab_df["Export_da_ne"] = True
        krm_tab_df.loc[(krm_tab_df["ime_fajla"].isin(['NBIOT_800','NBIOT_900','NBIOT_1800', 'UMTS_2100'])), "Export_da_ne"] = False
    # krm_tab_df["Export_da_ne"] = False
    # krm_tab_df.loc[(krm_tab_df["ime_fajla"].isin(['NR_3500'])), "Export_da_ne"] = True
    krm_tab_df = krm_tab_df[krm_tab_df["Export_da_ne"] == True]
    print(krm_tab_df)
    for i in krm_tab_df.index:
        print(i)
        t_a = time.time() 
        file_odpri = open(odlozisce_2,"w")
        file_odpri.write('')
        file_odpri.close()
        if krm_tab_df.loc[i,"Export_da_ne"] == True:
            if po_celicah == True:
                export_seznam_celic(celice_seznam, krm_tab_df.loc[i, 'tehn'], krm_tab_df)    
            else:
                file_odpri_2 = open(odlozisce_2,"w")
                file_odpri_2.write(krm_tab_df.loc[i, "tehn"])
                file_odpri_2.close()
                krm_tab_df.loc[i, "tehn"]
        if ini_file_set != '':
            ini_file = krm_tab_df.loc[i,"ini_file_3794_slovar"]
        else:
            ini_file = krm_tab_df.loc[i,"ini_file_3794_100_slovar"]
        at_dok_3794 = krm_tab_df.loc[i,"atoll_dokument"]
        # odlozisce_pokrivanja = odlozisce_reporting
        print(ini_file)
        folder = krm_tab_df.loc[i, "folder_slovar"]
        if ime_fajla == 'tehnologija':
            ime = krm_tab_df.loc[i,  "tehnologija"]
        else:
            ime = krm_tab_df.loc[i,  "ime_fajla"]
        t_c = time.time()
        print(ime)
        print(krm_tab_df.loc[i,"tehn"])
        print(at_dok_3794)
        print(odlozisce_pokrivanja)
        
        # Nastavitev filtra
        if krm_tab_set == True:
            subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\posodobi_atoll_3794_update_planirano_nastavi_filt_zone.vbs'],  capture_output=True,  text=True)
        else:
            subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\skripta_filter_atoll_iz_aplikacije_3794.vbs'],  capture_output=True,  text=True)
            
        t_d = time.time()
        print(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt")
        if ime_lokacije != '':
            subprocess.run(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime_lokacije + "_" + ime + ".txt", shell = True)
        else:    
            subprocess.run(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt", shell = True)   # Izračun predikcije
        subprocess.run(['cscript','D:\\Atoll_projects_planer01\\Skripte\\VBasic\\refresh.vbs'],  capture_output=True,  text=True)
        t_b = time.time()
        print("Cas izvajanja izračuna tehnologije {} je {} minut. Cas izvajanja filtra je {} s".format(ime, (t_b - t_a)/60, t_d - t_c))
        print("\n")
    # Rename
    for i in os.listdir(odlozisce_pokrivanja):
        if ime_lokacije == '':
            if po_celicah == False:
                if (i.find(".txt") > 0) & (i.find("[") > 0):
                    os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + re.sub(r'\[[A-Z|5G NR]+]' , '1_w', i))
            else:
                if (i.find(".txt") > 0) & (i.find("[") > 0):
                    os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + re.sub(r'\[[A-Z|5G NR]+]' , '1_p', i))
        else:
            pass

def nastavi_datum_na_filete_v_mapi(mapa, datum):
    """
    mapa: ponastavi datum za vse podmape in datoteke v mapi mapa
    datum: oblika zapisa: '2025-04-01' (leto-mesec-dan)
    https://www.tutorialspoint.com/How-to-set-creation-and-modification-date-time-of-a-file-using-Python
    """
    cas = datum.split("-")
    modification_datetime = datetime.datetime(int(cas[0]), int(cas[1]), int(cas[2]))
    modification_time = modification_datetime.timestamp()
    for r, d, f in os.walk(mapa):
        for file in f:
            if os.path.isfile(mapa + file):
                print (os.path.getmtime(os.path.join(mapa, file)))
                os.utime(mapa + file, ((os.path.getmtime(os.path.join(mapa, file))), modification_time))
    
        
            
def sprememeba_rezultata_v_PopArea_tabeli(tehnologija = '', datum = '', nivo = 0):
    """
    Funkcija prebere ustrezen fajl iz mape G:\Pokrivanja\Odlozisce_reporting\Pop_Area ali G:\Pokrivanja\Odlozisce_reporting\Pop_Area\Drugo. V teh mapah so shranjeni rezultati pokrivanj za vsaka 2 tedna. Posodabljajo se datoteke v mapi G:\Pokrivanja\Stevci\\. Ce beremo iz mape r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\\", se posodobi fajl G:\Pokrivanja\Stevci\\PopArea_skupaj_Atoll_reporting.csv, ce pa beremo iz r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\Drugo\\", se posodobi ustrezen eden od preostalih fajlov. Pri posodobitvi se najprej poisce ustrezen rezultat v razultatski tabeli in se pobrise, nato pa se nadomesti z ustrezno vrstico iz fajla pokrivanj. 
    
    -datum: oblika zapisa: '2025-04-01' (leto-mesec-dan)
    
    -tehnologija (Lahko da se kaksen doda):
 mapa r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\\"
 'GSM_1800',
 'GSM',
 'GSM_900',
 'LTE_1800',
 'LTE',
 'LTE_2100',
 'LTE_2600',
 'LTE_700',
 'LTE_800',
 'LTE_900',
 'NR',
 'NR_2600',
 'NR_3500',
 'NR_700',
 'NSA',
 'NSA_2600',
 'NSA_3500',
 'NSA_700',
 'CA',
 ...
 v mapi r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\Drugo\\" pa
 'Ceste_I_in_II_reda',
 'AKOS_mesta',
 'AC_in_HC_brez_tunelov',   
 'zeleznica'
    
    -nivo: npr: -100 (opcijsko)
    """
    mapa_poparea = r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\\"
    mapa_drugo = r"G:\Pokrivanja\Odlozisce_reporting\Pop_Area\Drugo\\"
    fajl_poparea = r"G:\Pokrivanja\Stevci\\PopArea_skupaj_Atoll_reporting.csv"
    mapa_poparea_rezultat = r"G:\Pokrivanja\Stevci\\"
    poparea_rez_df = pd.read_csv(fajl_poparea)
    tehnol_list = poparea_rez_df['TEHNOLOGIJA'].drop_duplicates().tolist()
    drugo_list = [ 'Ceste_I_in_II_reda','AKOS_mesta','AC_in_HC_brez_tunelov','zeleznica']
    skupaj_list = tehnol_list
    for i in drugo_list:
        skupaj_list.append(i)
    slovar_niz = {}
    for i in skupaj_list:
        slovar_niz[i] = "_1_w_pop_area_rezultat.xlsx"
    slovar_niz['Ceste_I_in_II_reda'] = "_Ceste_I_in_II_reda.xlsx"
    slovar_niz['AC_in_HC_brez_tunelov'] = "_AC_in_HC_brez_tunelov.xlsx"
    slovar_niz['AKOS_mesta'] = "_AKOS_mesta.xlsx"
    slovar_niz['zeleznica'] = "_zeleznica.xlsx"
    if (tehnologija not in skupaj_list):
        return print("Dodaj tehnologijo! Možnosti so:\n{}".format("\n".join(skupaj_list)))
    else:
        filter_teh = ''
        if tehnologija in tehnol_list:
            filter_teh = tehnologija
            mapa = mapa_poparea
            fajl = fajl_poparea
            for i in os.listdir(mapa_poparea):
                if i.find(tehnologija + "_1_w_pop_area_rezultat.xlsx") >= 0:
                    fajl_input = mapa_poparea + i
        if tehnologija in drugo_list:
            filter_teh = tehnologija
            mapa = mapa_drugo
            drugo_opcije = list(set([i.split('_')[0] for i in os.listdir(mapa_drugo)]))
            teh = input("Vnesi tehnologijo (možnosti so {}): ".format(", ".join(drugo_opcije)))
            for i in os.listdir(mapa_drugo):
                if i.find(teh + "_" + tehnologija) >= 0:
                    fajl_input = mapa_drugo + i
            for i in os.listdir(mapa_poparea_rezultat):
                if i.find(tehnologija) >= 0:
                    fajl = mapa_poparea_rezultat + i
            tehnologija = teh
    poparea_rez_df = pd.read_csv(fajl)
    nivoji = poparea_rez_df['Nivo'][poparea_rez_df['TEHNOLOGIJA'] == tehnologija].drop_duplicates().tolist()
    if datum not in poparea_rez_df['DATUM'].drop_duplicates().tolist():
        return print("Tega datuma ni v tabeli {}!\n Format vpisa je npr: 2025-04-01".format(fajl))
    else:
        if nivo != 0:
            if nivo not in nivoji:
                return print("Tega nivoja ni v tabeli {}! Mozni nivoji so {}\n.".format(fajl, "\n".join([str(i) for i in nivoji])))
            else:
                poparea_rez_df__ = poparea_rez_df[((poparea_rez_df['TEHNOLOGIJA'] == tehnologija) & (poparea_rez_df['DATUM'] == datum) & (poparea_rez_df['Nivo'] == nivo))]
        else:
            poparea_rez_df__ = poparea_rez_df[((poparea_rez_df['TEHNOLOGIJA'] == tehnologija) & (poparea_rez_df['DATUM'] == datum))]
        poparea_rez_df = poparea_rez_df[~poparea_rez_df.index.isin(poparea_rez_df__.index)]
        # Preberemo nov fajl
        temp = pd.read_excel(fajl_input)
        if nivo != 0:
            temp = temp[temp['Nivo'] == nivo]
        razlika_index = len(temp.index) - len(poparea_rez_df__.index)
        if razlika_index != 0:
            ind_min = poparea_rez_df__.index.min()
            ind_max = poparea_rez_df__.index.max()
            ind_list = poparea_rez_df.loc[poparea_rez_df.index < ind_min].index.tolist()
            ind_list_ = poparea_rez_df.loc[poparea_rez_df.index > ind_max].index + razlika_index
            for i in ind_list_.tolist():
                ind_list.append(i)
            poparea_rez_df = poparea_rez_df.reindex(ind_list)
            temp.index = list(range(ind_min, (ind_max + razlika_index),1))
        else:
            temp.index = poparea_rez_df__.index
        temp.drop(columns = [i for i in temp.columns.tolist() if i.find("Unname") >= 0], inplace = True)
        temp['TEHNOLOGIJA'] = tehnologija 
        temp['DATUM'] = datum
        temp['RESOLUCIJA'] = 100
        temp['ORODJE'] = 'Atoll'
        poparea_rez_df = pd.concat([poparea_rez_df,temp])
        return poparea_rez_df.sort_index().to_csv(fajl, index = False)
    

if __name__ == '__main__':
    pass
    

            
#######################################
# NR 700 coverage naredimo na LTE 1800
# Izrišemo samo best server 1800 layerja (vzamemo vseh 6 layerejev in nato uparimo z 700 pokrivanjem, kjer nastavimo max moč na NR 700 na -110 dbm. )
#######################################



# # # # # # # # # # # # if ((nsa_correction == True) & (nr700_da_ne == True)):
    # # # # # # # # # # # # if po_celicah == True:
        # # # # # # # # # # # # file700 = odlozisce_pokrivanja + 'NR_700_1_p.txt'
        # # # # # # # # # # # # if 'LTE_1800_1_p.txt' in os.listdir(odlozisce_pokrivanja):
            # # # # # # # # # # # # tt1800_p = beri_atoll_txt_export(odlozisce_pokrivanja + 'LTE_1800_1_p.txt')[1]
        # # # # # # # # # # # # else:
            # # # # # # # # # # # # tt1800_p = pd.DataFrame(columns = list(range(0,13)))
    # # # # # # # # # # # # else:
        # # # # # # # # # # # # file700 = odlozisce_pokrivanja + 'NR_700_1_w.txt'
    # # # # # # # # # # # # tt700  = beri_atoll_txt_export(file700)
    # # # # # # # # # # # # tt700_1 = tt700[1][[0,1,2,3]]
    # # # # # # # # # # # # tt700_1[3] = tt700_1[3].astype(float)
    # # # # # # # # # # # # celice = tt700[1][2].drop_duplicates().tolist()
    # # # # # # # # # # # # celice18 = [i.replace('07SS','18') for i in celice]
    # # # # # # # # # # # # slovv = dict(zip(celice18,celice))
    # # # # # # # # # # # # tt1800 = beri_atoll_txt_export(odlozisce_pokrivanja + 'LTE_1800_1_w.txt')[1]
    # # # # # # # # # # # # # # # # # tt1800_1 = tt1800[[0,1,2,3]][tt1800[2].isin(celice)].dropna()
    # # # # # # # # # # # # # # # # # tt1800_1 = tt1800[(tt1800[2].isin(celice18)) | (tt1800[4].isin(celice18)) | (tt1800[6].isin(celice18)) | (tt1800[8].isin(celice18)) | (tt1800[10].isin(celice18)) | (tt1800[12].isin(celice18))]
    # # # # # # # # # # # # tt1800_1 = tt1800[[0,1,2,3]][tt1800[2].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_1.columns = [0,1,2,3]
    # # # # # # # # # # # # tt1800_2 = tt1800[[0,1,4,5]][tt1800[4].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_2.columns = [0,1,2,3]
    # # # # # # # # # # # # tt1800_3 = tt1800[[0,1,6,7]][tt1800[6].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_3.columns = [0,1,2,3]
    # # # # # # # # # # # # tt1800_4 = tt1800[[0,1,8,9]][tt1800[8].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_4.columns = [0,1,2,3]
    # # # # # # # # # # # # tt1800_5 = tt1800[[0,1,10,11]][tt1800[10].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_5.columns = [0,1,2,3]
    # # # # # # # # # # # # tt1800_6 = tt1800[[0,1,12,13]][tt1800[12].isin(celice18)].dropna()
    # # # # # # # # # # # # tt1800_6.columns = [0,1,2,3]
    # # # # # # # # # # # # tt18 = pd.concat([tt1800_1, tt1800_2 , tt1800_3 , tt1800_4 , tt1800_5 , tt1800_6 ])
    # # # # # # # # # # # # if po_celicah == True:
        # # # # # # # # # # # # tt1800_p_1 = tt1800_p[[0,1,2,3]][tt1800_p[2].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_1.columns = [0,1,2,3]
        # # # # # # # # # # # # tt1800_p_2 = tt1800_p[[0,1,4,5]][tt1800_p[4].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_2.columns = [0,1,2,3]
        # # # # # # # # # # # # tt1800_p_3 = tt1800_p[[0,1,6,7]][tt1800_p[6].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_3.columns = [0,1,2,3]
        # # # # # # # # # # # # tt1800_p_4 = tt1800_p[[0,1,8,9]][tt1800_p[8].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_4.columns = [0,1,2,3]
        # # # # # # # # # # # # tt1800_p_5 = tt1800_p[[0,1,10,11]][tt1800_p[10].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_5.columns = [0,1,2,3]
        # # # # # # # # # # # # tt1800_p_6 = tt1800_p[[0,1,12,13]][tt1800_p[12].isin(celice18)].dropna()
        # # # # # # # # # # # # tt1800_p_6.columns = [0,1,2,3]
        # # # # # # # # # # # # tt18_p = pd.concat([tt1800_p_1, tt1800_p_2 , tt1800_p_3 , tt1800_p_4 , tt1800_p_5 , tt1800_p_6 ])
        # # # # # # # # # # # # tt18 = pd.concat([tt18, tt18_p])
    
    # # # # # # # # # # # # tt18 = tt18.reset_index()
    # # # # # # # # # # # # tt18.drop(columns = 'index', inplace = True)
    # # # # # # # # # # # # tt18[3] = tt18[3].astype(float)
    # # # # # # # # # # # # # # # # tt18g = tt18.groupby([0,1])[3].max()
    # # # # # # # # # # # # # # # # tt18gr = tt18g.reset_index()
    # # # # # # # # # # # # # # # # tt18gr.drop(columns = 'index', inplace = True)
    # # # # # # # # # # # # ######tt18 = tt1800_1
    # # # # # # # # # # # # # # # # # # tt18.drop(columns = [2], inplace = True)
    # # # # # # # # # # # # # # # # # # tt18.rename(columns = {4:2}, inplace  =True)
    
    # # # # # # # # # # # # tt18 = tt18[[0,1,2,3]].reset_index()
    # # # # # # # # # # # # tt18.drop(columns = ['index'], inplace = True)
    # # # # # # # # # # # # tt18['vrstni_red'] = tt18.sort_values(by = [0,1,3], ascending = [False, False, False]).groupby([0,1]).cumcount() + 1
    # # # # # # # # # # # # tt18 = tt18[tt18['vrstni_red'] == 1]
    
    # # # # # # # # # # # # tt_skupaj = tt700_1.merge(tt18, how = 'inner', left_on = [0,1], right_on = [0,1])
    # # # # # # # # # # # # tt_skupaj = tt_skupaj[[0,1,'2_x', '3_x']]
    # # # # # # # # # # # # tt_skupaj.rename(columns = {'2_x':2, '3_x':3}, inplace = True)
    # # # # # # # # # # # # tt_skupaj = tt_skupaj[tt_skupaj[3] > -110]


    # # # # # # # # # # # # with open (file700, 'w') as aa:
        # # # # # # # # # # # # aa.write(tt700[0]['type'] + '\n')
        # # # # # # # # # # # # aa.write(tt700[0]['timestamp']+ '\n')
        # # # # # # # # # # # # aa.write('resolution\t' + str(tt700[0]['resolution']) + '\n')
        # # # # # # # # # # # # aa.write('xmin\t' + str(tt_skupaj[0].astype(int).min())+ '\n')
        # # # # # # # # # # # # aa.write('xmax\t' + str(tt_skupaj[0].astype(int).max() +25)+ '\n')
        # # # # # # # # # # # # aa.write('ymin\t' + str(tt_skupaj[1].astype(int).min())+ '\n')
        # # # # # # # # # # # # aa.write('ymax\t' + str(tt_skupaj[1].astype(int).max() +25)+ '\n')
        # # # # # # # # # # # # aa.write('x_num_pixels\t' + str(int((tt_skupaj[0].astype(int).max() - tt_skupaj[0].astype(int).min()+ 25)/25)) + '\n')
        # # # # # # # # # # # # aa.write('y_num_pixels\t' + str(int((tt_skupaj[1].astype(int).max() - tt_skupaj[1].astype(int).min() + 25)/25)))
        # # # # # # # # # # # # aa.write('\n\n')
        # # # # # # # # # # # # aa.close()
    # # # # # # # # # # # # tt_skupaj.to_csv(file700, mode = 'a', sep = ";", index = False, header = None)

#######################################
# Konverzija v D48
#######################################   

# for i in os.listdir(mapa_shrani_arcgis_3794):
    # print( os.path.getmtime(mapa_shrani_arcgis_3794 + i)
    
# if __name__ == '__main__':
    # main()
