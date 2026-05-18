# -*- coding: utf-8 -*-

##############################################################################################
#   Skripta, na podlagi sprememb na celicah, določi katera tehnologija/frekvenca je potrebna za ponoven export. To se zapiše v tabelo: G:\\Avtomatika\\Eksport\\Export_coverage_krmilna_tabela.xlsx
#   - Sprememba je lahko, če je celica izbrisana iz SQL baze. To preberemo iz datotek v mapi G:\\Avtomatika\\EPSG_3794\\Brisi\\. Napolni seznam izbor_brisi
#   - Spremmeba je lahko, če Atoll, na podlagi posodobitve ponovno izračuna .los fileje za celice. To je v mapi G:\\Atoll_dokumenti\\Dokument_exporti\\Atoll_exporti_3794.losses\\
#   - Ker Atoll pri spremembi moči na celicah ne izračuna ponovno .los datotek celic, je potrebno  preveriti, ali je v katerem od datotek v mapi G:\\Avtomatika\\EPSG_3794\\Spremeni\\ morebiti prišlo do spremmebo moči. 
##############################################################################################
import funkcije_at
import os
import datetime
import time
import sql_atoll_3794
import shutil

datum = str(datetime.date.today())

def odstrani_celice_podcrtaj(seznam):
    return list(set([u for u in [i.split("_")[0] if i.find("_") > 0 else i for i in seznam] if u.find("_") < 0]))

def odstrani_celice_podcrtaj(seznam):
    """
    Odstrani '_' in '(0)' iz imen celic. 
    """
    uu = []
    uu1 = []
    for i in seznam:
        if i.find("_") >0 :
            uu.append(i.split("_")[0])
        else:
            uu.append(i)
    for i in uu:
        if i.find("(0)") > 0:
            uu1.append(i.split("(0)")[0])
        else:   
            uu1.append(i)
    return uu1

def danes():
    if len(str(datetime.datetime.now().month) ) == 1:
        mesec = "0" + str(datetime.datetime.now().month)
    else:
        mesec = str(datetime.datetime.now().month)
    if len(str(datetime.datetime.now().day) ) == 1:
        dan = "0" + str(datetime.datetime.now().day)
    else:
        dan =  str(datetime.datetime.now().day)
    if len(str(datetime.datetime.now().hour) ) == 1:
        ura = "0" + str(datetime.datetime.now().hour)
    else:
        ura =  str(datetime.datetime.now().hour)
    danes__ = str(datetime.datetime.now().year) + "-" +  mesec + "-" +  dan
    return danes__

def danes_ura():
    return str(datetime.datetime.now()).replace(" ","-").split(":")[0]

def brisi():
    """
    Vrne seznam celic, ki se brišejo iz Atoll. Bere podatke za avtomatiko. 
    """
    odlozisce_brisi = "G:\\Avtomatika\\EPSG_3794\\Brisi\\"
    tabele_brisi = ['gtransmitters', 'gtransmitters_remote', 'grepeaters_atoll','xgtransmitters', 'xgtransmitters_remote', 'xgrepeaters_atoll']
    tabele = ['gtransmitters', 'gtransmitters_remote', 'grepeaters_atoll', 'xgcellslte', 'xgcells5gnr', 'xgrepeaters_atoll']
    izbor_brisi = []
    for i in os.listdir(odlozisce_brisi):
        if i.find('.csv') > 0 and i.find("__NE_BRISI__") < 0:
            if i.split('_')[1].split('.')[0] in tabele_brisi:
                t = funkcije_at.pd.read_csv(odlozisce_brisi + i, sep = ";")
                if t.shape[0] > 0:
                    for k in t.iloc[:,0].drop_duplicates().tolist():
                        izbor_brisi.append(k)
                else:
                    pass
            else:
                pass 
    return list(set(odstrani_celice_podcrtaj(izbor_brisi)))

def brisi_site():
    odlozisce_brisi = "G:\\Avtomatika\\EPSG_3794\\Brisi\\"
    sk = funkcije_at.pd.DataFrame()
    for i in os.listdir(odlozisce_brisi):
        if ((i.find('.csv') > 0) and (i.find("sites") >= 0)):
            s = funkcije_at.pd.read_csv(odlozisce_brisi + i)
            ssez = s['NAME'].tolist()
            if len(ssez) > 0 :
                g = funkcije_at.pd.read_sql(sql_atoll_3794.gtransmitters_atoll, sql_atoll_3794.conn_atoll)
                g = g[['TX_ID','SITE_NAME']][g['SITE_NAME'].isin(ssez)]
                xg = funkcije_at.pd.read_sql(sql_atoll_3794.xgtransmitters_atoll, sql_atoll_3794.conn_atoll)
                xg = xg[['TX_ID','SITE_NAME']][xg['SITE_NAME'].isin(ssez)]
                sk = funkcije_at.pd.concat([g, xg])
            else:
                pass
        else:
            pass
    if sk.shape[0] > 0:
        return list(set(odstrani_celice_podcrtaj(sk['TX_ID'].tolist())))
    else:
        return []
    
def los_fileti():
    """
    Vrne seznam vseh celic, za katere so se poračunali .los fileti
    """
    danes_ = danes()
    izbor_los_fileti =[]            
    for i in os.listdir("G:\\Atoll_dokumenti\\Dokument_exporti\\SharedPathlossData\\"):
        for j in os.listdir("G:\\Atoll_dokumenti\\Dokument_exporti\\SharedPathlossData\\" + i ):
            if str(datetime.datetime.fromtimestamp(os.path.getmtime("G:\\Atoll_dokumenti\\Dokument_exporti\\SharedPathlossData\\" + i+ "\\" + j)).date()) == danes_:
                if j.find(".los") > 0:
                    izbor_los_fileti.append(j.split(".los")[0])
    return list(set(odstrani_celice_podcrtaj(izbor_los_fileti)))

def sprememba_moci():
    """
    Atoll ne poračuna .los datotek, če se na celici spremeni moč ali cable_loss ali stanje active na transmiterjih
    """
    tabele = ['gtransmitters', 'gtransmitters_remote', 'grepeaters_atoll', 'xgcellslte', 'xgcells5gnr', 'xgrepeaters_atoll']
    izbor_moc = []
    slovar_moci = {'gtransmitters':'POWER',
    'gtransmitters_remote': 'POWER',
    'grepeaters_atoll':'EIRP',
    'xgcellslte': 'RS_EPRE',
    'xgcells5gnr':'SSS_POWER',
    'xgrepeaters_atoll': 'TOTAL_GAIN'}
    slovar_active = {'gtransmitters':'ACTIVE',
    'gtransmitters_remote':'ACTIVE',
    'grepeaters_atoll':'ACTIVE',
    'xgcellslte': 'ACTIVE',
    'xgcells5gnr':'ACTIVE',
    'xgrepeaters_atoll': 'ACTIVE',
    'xgtransmitters':'ACTIVE'}
    slovar_cable_loss = {'gtransmitters':'LOSSES',
    'xgtransmitters':'TXLOSSES'}
    for i in os.listdir("G:\\Avtomatika\\EPSG_3794\\Spremeni\\"):
        if i.find(".csv") > 0:
            if i.split("_")[1].strip(".csv") in tabele:
                csv_df = funkcije_at.pd.read_csv("G:\\Avtomatika\\EPSG_3794\\Spremeni\\" + i, sep = ";")
                csv_stolpci = csv_df.columns.tolist()
                for j in  csv_stolpci:
                    try:
                        if j in slovar_moci[i.split("_")[1].strip(".csv")]:
                            izbor_moc.append(csv_df[[csv_df.iloc[:,0].name,j]].dropna().iloc[:,0].tolist())
                        else:
                            pass
                    except:
                        KeyError
                    try:
                        if j in slovar_active[i.split("_")[1].strip(".csv")]:
                            izbor_moc.append(csv_df[[csv_df.iloc[:,0].name,j]].dropna().iloc[:,0].tolist())
                        else:
                            pass 
                    except:
                        KeyError
                    try:
                        if j in slovar_cable_loss[i.split("_")[1].strip(".csv")]:
                            izbor_moc.append(csv_df[[csv_df.iloc[:,0].name,j]].dropna().iloc[:,0].tolist())
                        else:
                            pass    
                    except:
                        KeyError
    izbor_moci = []
    for i in izbor_moc:
        for j in i:
            izbor_moci.append(j)
    return list(set(odstrani_celice_podcrtaj(izbor_moci)))

def novo():
    """
    Vrne seznam vseh novih celic. Bere podatke za avtomatiko. 
    """
    izbor_novo_mapa = []
    for i in os.listdir("G:\\Avtomatika\\EPSG_3794\\Novo\\"):
         if ((i.find("transmitters.csv") > 0) | ((i.find("cells") > 0) & (i.find(".csv") > 0))):
            csv_df = funkcije_at.pd.read_csv("G:\\Avtomatika\\EPSG_3794\\Novo\\" + i, sep = ";")
            novv = csv_df[csv_df.columns.tolist()[0]].tolist()
            for j in novv:
                izbor_novo_mapa.append(j)
    return list(set(odstrani_celice_podcrtaj(izbor_novo_mapa)))

def novo_aktivno():
    """
    Vrne seznam vseh novih celic. Bere podatke za avtomatiko. 
    """
    izbor_novo_mapa = []
    for i in os.listdir("G:\\Avtomatika\\EPSG_3794\\Novo\\"):
        if ((i.find("transmitters.csv") > 0) | ((i.find("cells") > 0) & (i.find(".csv") > 0))):
            csv_df = funkcije_at.pd.read_csv("G:\\Avtomatika\\EPSG_3794\\Novo\\" + i, sep = ";")
            csv_df = csv_df[csv_df["ACTIVE"] == 'True']
            novv = csv_df[csv_df.columns.tolist()[0]].tolist()
            for j in odstrani_celice_podcrtaj(novv):
                izbor_novo_mapa.append(j)
        else:
            pass
    return list(set(odstrani_celice_podcrtaj(izbor_novo_mapa)))

def novo_pasivno():
    """
    Vrne seznam vseh novih celic. Bere podatke za avtomatiko. 
    """
    izbor_novo_mapa = []
    for i in os.listdir("G:\\Avtomatika\\EPSG_3794\\Novo\\"):
        if i.find("transmitters.csv") > 0:
            csv_df = funkcije_at.pd.read_csv("G:\\Avtomatika\\EPSG_3794\\Novo\\" + i, sep = ";")
            csv_df = csv_df[csv_df["ACTIVE"] == 'False']
            novv = csv_df[csv_df.columns.tolist()[0]].tolist()
            for j in novv:
                izbor_novo_mapa.append(j)
    return list(set(odstrani_celice_podcrtaj(izbor_novo_mapa)))

def seznam_vseh_celic():
    los = los_fileti()
    moc = sprememba_moci()
    brisi_site = brisi_site()
    brisi = brisi()
    oo = funkcije_at.razlika_seznamov(los, moc, nacin = 'unija')
    oo = funkcije_at.razlika_seznamov(oo, brisi_site, nacin = 'unija')
    oo = funkcije_at.razlika_seznamov(oo, brisi, nacin = 'unija')
    return oo
    
def seznam_vseh_celic_atoll_export():
    los = los_fileti()
    moc = sprememba_moci()
    oo = funkcije_at.razlika_seznamov(los, moc, nacin = 'unija')
    return oo

def brisanje():
    brisi_site = brisi_site()
    brisi = brisi()
    oo = funkcije_at.razlika_seznamov(brisi_site, brisi, nacin = 'unija')
    return oo
    
def tehnologije_na_dan_atoll_export(seznam):
    """
    Seznam vseh spremenjenih celic v dnevu. 
    """
    if len(seznam) > 0:
        izzbor_tehn = funkcije_at.pd.DataFrame([funkcije_at.pripona(i) for i in seznam])
        izzbor_tehn.loc[izzbor_tehn[1] == '5G', 1] = 'NR'
        izzbor_tehn['ime'] = izzbor_tehn[1] + "_" + izzbor_tehn[4].astype(str)
        return izzbor_tehn['ime'].tolist()
    else:
        return []

def celice_na_dan_atoll_export(seznam):
    """
    Seznam vseh spremenjenih celic v dnevu. 
    """
    if len(seznam) > 0:
        izzbor_tehn = funkcije_at.pd.DataFrame([funkcije_at.pripona(i) for i in seznam])
        izzbor_tehn.loc[izzbor_tehn[1] == '5G', 1] = 'NR'
        izzbor_tehn['ime'] = izzbor_tehn[1] + "_" + izzbor_tehn[4].astype(str)
        izzbor_tehn[[0,'ime']].sort_values(by = ['ime',0], ascending = [True, True]).drop_duplicates().to_csv("G:\\Avtomatika\\Eksport\\Celice_na_dan\\celice_na_dan.txt", index = False, header = None, sep = ";")
    else:
        with open("G:\\Avtomatika\\Eksport\\Celice_na_dan\\celice_na_dan.txt", "w") as dd:
            dd.write("")
            dd.close()
    return 0
    
def krmilna_tabela(seznam):
    """
    Krmiljenje tabele "G:\\Avtomatika\\Eksport\\Export_coverage_krmilna_tabela.xlsx". Ta tabela se bere v primeru, če gre za skupen export iz atolla po tehnologiji/frekvenci. 
    """
    k_tab = funkcije_at.pd.read_excel("G:\\Avtomatika\\Eksport\\Export_coverage_krmilna_tabela.xlsx")
    k_tab['Export_da_ne'] = False
    if len(seznam) > 0:
        k_tab.loc[k_tab['ime_fajla'].isin(seznam), 'Export_da_ne'] = True
    else:
        pass
    k_tab.loc[((k_tab['frek_tehn'] == 'UTRA Band I')), 'Export_da_ne'] = False
    k_tab.to_excel("G:\\Avtomatika\\Eksport\\Export_coverage_krmilna_tabela.xlsx", index = False)
    if k_tab[k_tab['Export_da_ne'] == True].shape[0] > 0:
        m = open("G:\\Avtomatika\\Eksport\\fajl.txt", "a")
        m.write(time.asctime() + "\nTehnologije pripravljene za export: \n{}".format(k_tab['ime_fajla'][k_tab['Export_da_ne'] == True]))
        m.close()
    return 0


def kopiraj_datoteke_v_privatno_mapo(shared_mapa, privat_mapa):
    """
    Po sestanku s Forskom (2.9.2025, prisotni: Forsk: Camille Davila (MyForsk) <support@forsk.com>; TS: Andrej.Mezan@telekom.si, Ziga.Kavkler@telekom.si):
    Priporočilo Forsk-a za uporabo skupnih .los datotek je, da so le-te shranjene v ločeni mapi od privatne mape. To pomeni, da tudi primarni .ATL dokumnet, s katerim preračunavamo .los filete vsako noč, uporablja dve ločeni mapi za privat in shared. Glej aplikacijo Atoll, zavihek Network/Predictions/Properties. 
    Nočni .los fileti se bodo odlagali v shared mapo, zato je potrebno po tem procesu v privatno mapo presneti vse novo izračunane .los filete.  
    """
    # privat_mapa = r"G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794_3_5_1.losses\\"
    # shared_mapa = r"G:\Atoll_dokumenti\Dokument_exporti\SharedPathlossData\\"
    for folder, subfolders, files in os.walk(shared_mapa):
        for i in files:
            if (os.path.isfile(folder.replace(shared_mapa, privat_mapa) + "\\" + i)):
                if (os.stat(folder + "\\" + i).st_mtime > os.stat(folder.replace(shared_mapa, privat_mapa) + "\\" + i).st_mtime):
                    try:
                        shutil.copy((folder + "\\" + i), (folder.replace(shared_mapa, privat_mapa) + "\\" + i))
                        print(i)
                    except:
                        pass
            else:
                try:
                    shutil.copy((folder + "\\" + i), (folder.replace(shared_mapa, privat_mapa) + "\\" + i))
                    print(i)
                except:
                    pass
    return 0
    
    
def main():
    
    los_ = los_fileti()
    moc_ = sprememba_moci()
    brisi_site_ = brisi_site()
    novo_ = novo()
    novo_akt = novo_aktivno()
    novo_pas = novo_pasivno()
    brisi_ = brisi()
    brisanje = funkcije_at.razlika_seznamov(brisi_site_, brisi_, nacin = 'unija')
    seznam_vseh_celic = funkcije_at.razlika_seznamov(los_, moc_, nacin = 'unija')
    seznam_vseh_celic = funkcije_at.razlika_seznamov(seznam_vseh_celic, brisanje, nacin = 'unija')
    krmilna_tabela(tehnologije_na_dan_atoll_export(seznam_vseh_celic))
    seznam_vseh_celic_atoll_export = funkcije_at.razlika_seznamov(los_, moc_, nacin = 'unija')
    celice_na_dan_atoll_export(seznam_vseh_celic_atoll_export)
    spremeni = funkcije_at.razlika_seznamov(seznam_vseh_celic_atoll_export, novo_, nacin = 'komplement1')
    with open(r"G:\Avtomatika\Eksport\Celice_dnevna_sprememba\\brisi.txt", "w") as dd:
        dd.write("\n".join(brisanje))
        dd.close()
    with open(r"G:\Avtomatika\Eksport\Celice_dnevna_sprememba\\novo.txt", "w") as dd:
        dd.write("\n".join(novo_))
        dd.close()    
    with open(r"G:\Avtomatika\Eksport\Celice_dnevna_sprememba\\spremeni.txt", "w") as dd:
        dd.write("\n".join(spremeni))
        dd.close()   
        
if __name__ == '__main__':
    main()
    
    
    
    
    
    
    
    