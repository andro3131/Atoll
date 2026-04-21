# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 10:15:31 2020

@author: kavklerz
"""
import pandas as pd
import polars as pl
import numpy as np
import urllib.request
import urllib.error
import datetime
import os
from collections import Counter
import time


boltzmanova_konstanta = 1.380649 / 10**23  # J/K
T = 290 # 290 K običajna temperatura za računanje 
F_lte = 8 # Noise figure sprejemnika -> različni viri navajajo različno. Preveri na Googlu


pd.options.mode.chained_assignment = None  # default='warn'

def seznam_csv(link):
    webUrl  = urllib.request.urlopen(link, timeout = 30)
    data = webUrl.read()
    lines = data.splitlines(True)
    enm_tabele = []
    for i in lines[20:]:
        enm_tabele.append(i.split(b'></td><td><a href=')[-1].split(b'>')[0].decode('utf-8')[1:-1])
    enm_tabele = list(set(enm_tabele))
    return enm_tabele

def seznam_csv3(mapa = 'LTE', lnk = "http://bpl1-ark.ts.telekom.si/vmib/ulinc/enm_celotni/"):
    webUrl  = urllib.request.urlopen(lnk + mapa + "/", timeout = 30)
    data = webUrl.read()
    lines = data.splitlines(True)
    stev = 0
    for i in lines:
        if i.decode('ascii').find('alt="[TXT]"') > 0:
            break
        else:
            stev = stev + 1
    enm_tabele = []
    for i in lines[stev:]:
        enm_tabele.append(i.split(b'></td><td><a href=')[-1].split(b'>')[0].decode('utf-8')[1:-1])
    enm_tabele = list(set(enm_tabele))
    return enm_tabele

def seznam_csv4():

    webUrl  = urllib.request.urlopen(link1, timeout = 30)
    data = webUrl.read()
    lines = data.splitlines(True)
    stev = 0
    for i in lines:
        if i.decode('ascii').find('alt="[TXT]"') > 0:
            break
        else:
            stev = stev + 1
    enm_mape = []
    for i in range(len(lines)):
        o = lines[i].split(b"></td><td><a href=")[-1].split(b'>')[0].decode('utf-8')[1:-1]
        if ((o[0] != '/') & (o[-1] == '/') ):
            enm_mape.append(o.split('/')[0])
    enm_mape = list(set(enm_mape))
    enm_tabele = {}
    for i in enm_mape:
        tabs = seznam_csv3(mapa = i)
        enm_tabele[i] = tabs
    return enm_tabele
    
def seznam_csv5():

    webUrl  = urllib.request.urlopen(link2, timeout = 30)
    data = webUrl.read()
    lines = data.splitlines(True)
    stev = 0
    for i in lines:
        if i.decode('ascii').find('alt="[TXT]"') > 0:
            break
        else:
            stev = stev + 1
    enm_mape = []
    for i in range(len(lines)):
        o = lines[i].split(b"></td><td><a href=")[-1].split(b'>')[0].decode('utf-8')[1:-1]
        if ((o[0] != '/') & (o[-1] == '/') ):
            enm_mape.append(o.split('/')[0])
    enm_mape = list(set(enm_mape))
    enm_tabele = {}
    for i in enm_mape:
        tabs = seznam_csv3(mapa = i, lnk = "http://bpl1-ark.ts.telekom.si/vmib/ulinc/novi_enm_celotni/")
        enm_tabele[i] = tabs
    return enm_tabele 
 
# link = "http://ark.ts.telekom.si/vmib/ulinc/"
link = "http://bpl1-ark.ts.telekom.si/vmib/ulinc/"
link1 = "http://bpl1-ark.ts.telekom.si/vmib/ulinc/enm_celotni/"
link2 = "http://bpl1-ark.ts.telekom.si/vmib/ulinc/novi_enm_celotni/"
mapa_parser = r"G:\ENM_export\ulinc\ulinc1\\"

def enm_tabela(vir):   
    if vir == link: 
        enm_tabele = seznam_csv(link)
    elif vir == mapa_parser:
        enm_tabele = [i for i in os.listdir(mapa_parser) if i.find(".csv") > 0]
    else:
        enm_tabele = []
    return enm_tabele

def add_semicolons_to_repeats(lst, mark = '_'):      # Hvala Copilot!
    seen = {}
    result = []
    
    for item in lst:
        if item in seen:
            seen[item] += 1
            #result.append(f"{item}{';' * seen[item]}")
            result.append("{}{}".format(item, mark*seen[item]))
        else:
            seen[item] = 0
            result.append(item)
    
    return result
    
    

def slov(seznam):
    slovar = {}
    for i in seznam:
        slovar[i] = i.split('(')[0]
    return slovar

def ustvari_df(ime_tabele, obvezni_stolpci = [], vir = link):
    """
    Če je vir podatkov "http://ark.ts.telekom.si/vmib/ulinc/"
    """
    seznam = []
    enm_tabele = enm_tabela(vir)
    if type(ime_tabele) != list:
	    #enm_tabele  =funkcije_at.seznam_csv("http://ark.ts.telekom.si/vmib/ulinc/")
        for i in enm_tabele:
            if i.split('_')[0] == ime_tabele:
                seznam.append(i)
    else:
        seznam = [i + ".csv" for i in ime_tabele] 
    dfji = []
    dfji2 = []
    stolpci = []
    if len(seznam) > 0:
        for i in seznam:
            vars()['DF_'+i] = pd.read_csv(vir + i, delimiter = ';', low_memory = False)
            vars()['DF_'+i].rename(columns = slov(vars()['DF_'+i].columns.tolist()), inplace = True)
            vars()['DF_'+i] = vars()['DF_'+i].loc[:,~vars()['DF_'+i].columns.duplicated()]
            if len(obvezni_stolpci) > 0:
                for j in obvezni_stolpci:
                    if j in vars()['DF_'+i].columns.tolist():
                        dfji.append(vars()['DF_'+i])
                    else:
                        pass
            else:
                dfji.append(vars()['DF_'+i])
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele))
    
    for i in dfji:
        stolpci.append(i.columns.to_list())
    p = set(stolpci[0]).intersection(*stolpci)
    p1 = list(p)
    p1.sort()
    for i in dfji:
        dfji2.append(i[p1])
    data = pd.concat(dfji2)
    return data

def ustvari_df1(ime_tabele, obvezni_stolpci = [], tip=''):
    """
    Če je vir podatkov "http://ark.ts.telekom.si/vmib/ulinc/"
    """
    seznam = []
    if type(ime_tabele) != list:
	    #enm_tabele  =funkcije_at.seznam_csv("http://ark.ts.telekom.si/vmib/ulinc/")
        for i in enm_tabele:
            if i.split('_')[0] == ime_tabele:
                seznam.append(i)
    else:
        seznam = [i + ".csv" for i in ime_tabele] 
    dfji = []
    dfji2 = []
    stolpci = []
    if len(seznam) > 0:
        for i in seznam:
            if type(tip) == dict:
                vars()['DF_'+i] = pd.read_csv(link + i, delimiter = ';', low_memory = False, dtype = tip)
            else:
                vars()['DF_'+i] = pd.read_csv(link + i, delimiter = ';', low_memory = False)
            
            
# vars()['DF_'+i].rename(columns = slov(vars()['DF_'+i].columns.tolist()), inplace = True)
            vars()['DF_'+i] = vars()['DF_'+i].loc[:,~vars()['DF_'+i].columns.duplicated()]
            if len(obvezni_stolpci) > 0:
                for j in obvezni_stolpci:
                    if j in vars()['DF_'+i].columns.tolist():
                        dfji.append(vars()['DF_'+i])
                    else:
                        pass
            else:
                dfji.append(vars()['DF_'+i])
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele))
    
    for i in dfji:
        stolpci.append(i.columns.to_list())
    p = set(stolpci[0]).intersection(*stolpci)
    for i in dfji:
        dfji2.append(i[p])
    data = pd.concat(dfji2)
    return data





    
def ustvari_df2(ime_tabele, obvezni_stolpci = [], tip=''):
    """
    Če je vir podatkov G:\\ENM_export\\ulinc\\ulinc1\\
    """
    seznam = []
    
    if tip == 'GSM':
        mapa = r"G:\ENM_export\ulinc\GSM\\" 
    else:
        mapa = r"G:\ENM_export\ulinc\ulinc1\\"
    
    for i in os.listdir(mapa):
        if i.split('_')[0] == ime_tabele:
            seznam.append(i)

    dfji = []
    dfji2 = []
    stolpci = []
    if len(seznam) > 0:
        for i in seznam:
            if type(tip) == dict:
                vars()['DF_'+i] = pd.read_csv(mapa + i, delimiter = ';')
            else:
                vars()['DF_'+i] = pd.read_csv(mapa + i, delimiter = ';')
            stolp = [i.split("(")[0] for i in vars()['DF_'+i].columns.tolist()]
            vars()['DF_'+i].columns = stolp
            # vars()['DF_'+i].rename(columns = slov(vars()['DF_'+i].columns.tolist()), inplace = True)
            vars()['DF_'+i] = vars()['DF_'+i].loc[:,~vars()['DF_'+i].columns.duplicated()]
            if len(obvezni_stolpci) > 0:
                for j in obvezni_stolpci:
                    if j in vars()['DF_'+i].columns.tolist():
                        dfji.append(vars()['DF_'+i])
                    else:
                        pass
            else:
                dfji.append(vars()['DF_'+i])
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele))
    
    for i in dfji:
        stolpci.append(i.columns.to_list())
    p = set(stolpci[0]).intersection(*stolpci)
    aa = []
    for i in stolpci:
        for j in i:
            if j not in aa:
                aa.append(j)
    bb = []
    crit = []
    for i in aa:
        for j in stolpci:
            if i in j:
                crit.append(True)
            else:
                crit.append(False)
        if False in crit:
            pass
        else:
            bb.append(i)
        crit = []
    for i in dfji:
        dfji2.append(i[bb])
    data = pd.concat(dfji2)
    return data   
    
def ustvari_df3(ime_tabele, obvezni_stolpci = [], mapa='LTE', join = '', vsi_stolpci = False):
    """
    Če je vir podatkov "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/"
    join: če je outer, ne briše stolpcev
    mapa: katerikoli od folderjev na "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/". Če je mapa = 'povsod', pogleda za iskani MO v vseh mapah v enm_celotni. 
    """
    seznam = []
    enm_tabele = seznam_csv3(mapa)
    if type(ime_tabele) != list:
        #enm_tabele  =funkcije_at.seznam_csv("http://ark.ts.telekom.si/vmib/ulinc/")
        for i in enm_tabele:
            if i.split('_')[0] == ime_tabele:
                seznam.append(i)
    else:
        seznam = [i + ".csv" for i in ime_tabele] 

    dfji = []
    dfji2 = []
    stolpci = []
    if len(seznam) > 0:
        for i in seznam:
            vars()['DF_'+i] = pd.read_csv(link1 + mapa + "/" + i, delimiter = ';', low_memory = False)
            stolp = [i.split("(")[0] for i in vars()['DF_'+i].columns.tolist()]
            stolp1 = add_semicolons_to_repeats(stolp)
            if vsi_stolpci == True:
                vars()['DF_'+i].columns = stolp1
            else:
                vars()['DF_'+i].columns = stolp
            # vars()['DF_'+i].rename(columns = slov(vars()['DF_'+i].columns.tolist()), inplace = True)
            # vars()['DF_'+i] = vars()['DF_'+i].loc[:,~vars()['DF_'+i].columns.duplicated()]
            if len(obvezni_stolpci) > 0:
                for j in obvezni_stolpci:
                    if j in vars()['DF_'+i].columns.tolist():
                        dfji.append(vars()['DF_'+i])
                    else:
                        pass
            else:
                dfji.append(vars()['DF_'+i])
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele))
    
    if join == 'outer':
       for i in dfji:
           dfji2.append(i)
       data = pd.concat(dfji2, axis = 0, join = 'outer').reset_index(drop = True)
       
    else:
        for i in dfji:
            stolpci.append(i.columns.to_list())
        p = set(stolpci[0]).intersection(*stolpci)
        aa = []
        for i in stolpci:
            for j in i:
                if j not in aa:
                    aa.append(j)
        bb = []
        crit = []
        for i in aa:
            for j in stolpci:
                if i in j:
                    crit.append(True)
                else:
                    crit.append(False)
            if False in crit:
                pass
            else:
                bb.append(i)
            crit = []
        for i in dfji:
            dfji2.append(i[bb])
        data = pd.concat(dfji2)
    return data    
    
def ustvari_df4__(ime_tabele, mapa='povsod', exception = '', join = ''):
    """
    Če je vir podatkov "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/"
    join: če je outer, ne briše stolpcev. Če je join = '' se naredi presek vseh stolpcev.
    mapa: katerikoli od folderjev na "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/". Če je mapa = 'povsod', pogleda za iskani MO v vseh mapah v enm_celotni. Lahko je tudi seznam
    exception: mapa, v katerih ne želimo iskati. Lahko je tudi seznam
    
    STARO!!!
    
    """
    seznam = []
    enm_tabele = seznam_csv4()
    enm_skupaj = len(enm_tabele)
    if type(mapa) == list:
        d = {}
        for i in mapa:
            d[i] = enm_tabele[i]
        enm_tabele = d
    else:
        pass
    if exception != '':
        d = {}
        if type(exception) == list:
            for i in enm_tabele.keys():
                if i in exception:
                    pass
                else:
                    d[i] = enm_tabele[i]            
        else:
            for i in enm_tabele.keys():
                if i == exception:
                    pass
                else:
                    d[i] = enm_tabele[i]
        enm_tabele = d
            
    if ((mapa == 'povsod') | (len(enm_tabele) < enm_skupaj)):
        for j in enm_tabele.keys():
            for i in enm_tabele[j]:
                if i.split("_")[0] == ime_tabele:
                    seznam.append(link1 + j + "/" + i)
                else:
                    pass
    else:
        seznam = [(link1 + mapa + "/" + i) for i in enm_tabele[mapa] if i.split("_")[0] == ime_tabele]

    dfji = []
    dfji2 = []
    stolpci = []
    if len(seznam) > 0:
        for i in seznam:
            vars()['DF_'+i] = pd.read_csv(i, delimiter = ';', low_memory = False)
            stolp = [i.split("(")[0] for i in vars()['DF_'+i].columns.tolist()]
            stolp1 = add_semicolons_to_repeats(stolp)
            vars()['DF_'+i].columns = stolp1
            dfji.append(vars()['DF_'+i])
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele))

    if join == 'outer':
       for i in dfji:
           dfji2.append(i.reset_index(drop = True))
       data = pd.concat(dfji2, axis = 0, join = 'outer').reset_index(drop = True)
       
    else:
        for i in dfji:
            stolpci.append(i.columns.to_list())
        a = stolpci[0]
        stevec = len(stolpci)-1
        while stevec:
            a = razlika_seznamov(a,stolpci[stevec], nacin = 'presek')
            stevec = stevec - 1
        # p = set(stolpci[0]).intersection(*stolpci)  # PRESEK stolpcev
        for i in dfji:
            dfji2.append(i[a].reset_index(drop = True))
        data = pd.concat(dfji2)
    return data    
    
    
    
    
    
    
    

def ustvari_df4(ime_tabele, mapa='povsod', exception = '', join = ''):
    """
    Če je vir podatkov "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/" in "http://ark.ts.telekom.si/vmib/ulinc/novi_enm_celotni/"
    join: če je outer, ne briše stolpcev. Če je join = '' se naredi presek vseh stolpcev.
    mapa: katerikoli od folderjev na "http://ark.ts.telekom.si/vmib/ulinc/enm_celotni/". Če je mapa = 'povsod', pogleda za iskani MO v vseh mapah v enm_celotni. Lahko je tudi seznam
    exception: mapa, v katerih ne želimo iskati. Lahko je tudi seznam
    """
    
    # Peverba, če MO še obstaja
    enm_tabele = seznam_csv4()
    enm_tabele2 = seznam_csv5()
    
    if mapa != 'povsod':
        try:
            if ime_tabele in [i.split("_")[0] for i in enm_tabele[mapa]]:
                linkk1 = True
            else:
                linkk1 = False
        except:
            linkk1 = False
        try:
            if ime_tabele in [i.split("_")[0] for i in enm_tabele2[mapa]]:
                linkk2 = True
            else:
                linkk2 = False
        except:
            linkk2 = False
    else:
        ssez1 = []
        for i in list(enm_tabele.values()):
            for j in i:
                ssez1.append(j.split("_")[0])
        if ime_tabele in ssez1:
            linkk1 = True
        else:
            linkk1 = False
        
        ssez2 = []
        for i in list(enm_tabele2.values()):
            for j in i:
                ssez2.append(j.split("_")[0])
        if ime_tabele in ssez2:
            linkk2 = True
        else:
            linkk2 = False
    
    
    # Link1
    if linkk1 == True:
        seznam = []
        enm_tabele = seznam_csv4()
        enm_skupaj = len(enm_tabele)
        if type(mapa) == list:
            d = {}
            for i in mapa:
                d[i] = enm_tabele[i]
            enm_tabele = d
        else:
            pass
        if exception != '':
            d = {}
            if type(exception) == list:
                for i in enm_tabele.keys():
                    if i in exception:
                        pass
                    else:
                        d[i] = enm_tabele[i]            
            else:   
                for i in enm_tabele.keys():
                    if i == exception:
                        pass
                    else:
                        d[i] = enm_tabele[i]
            enm_tabele = d
                
        if ((mapa == 'povsod') | (len(enm_tabele) < enm_skupaj)):
            for j in enm_tabele.keys():
                for i in enm_tabele[j]:
                    if i.split("_")[0] == ime_tabele:
                        seznam.append(link1 + j + "/" + i)
                    else:
                        pass
        else:
            seznam = [(link1 + mapa + "/" + i) for i in enm_tabele[mapa] if i.split("_")[0] == ime_tabele]

         
        dfji = []
        dfji2 = []
        stolpci = []
        if len(seznam) > 0:
            for i in seznam:
                vars()['DF_'+i] = pd.read_csv(i, delimiter = ';', low_memory = False)
                stolp = [i.split("(")[0] for i in vars()['DF_'+i].columns.tolist()]
                stolp1 = add_semicolons_to_repeats(stolp)
                vars()['DF_'+i].columns = stolp1
                dfji.append(vars()['DF_'+i])
        else:
            print ("Tabela {} ne obstaja!".format(ime_tabele))

        if join == 'outer':
            for i in dfji:
               dfji2.append(i.reset_index(drop = True))
            data = pd.concat(dfji2, axis = 0, join = 'outer').reset_index(drop = True)
           
        else:
            for i in dfji:
                stolpci.append(i.columns.to_list())
            a = stolpci[0]
            stevec = len(stolpci)-1
            while stevec:
                a = razlika_seznamov(a,stolpci[stevec], nacin = 'presek')
                stevec = stevec - 1
            # p = set(stolpci[0]).intersection(*stolpci)  # PRESEK stolpcev
            for i in dfji:
                dfji2.append(i[a].reset_index(drop = True))
            data = pd.concat(dfji2)
    else:
        data = pd.DataFrame()
               

    #link2
    if linkk2 == True:
        seznam2 = []
        enm_tabele2 = seznam_csv5()
        enm_skupaj2 = len(enm_tabele2)
        if type(mapa) == list:
            d = {}
            for i in mapa:
                d[i] = enm_tabele2[i]
            enm_tabele2 = d
        else:
            pass
        if exception != '':
            d = {}
            if type(exception) == list:
                for i in enm_tabele2.keys():
                    if i in exception:
                        pass
                    else:
                        d[i] = enm_tabele2[i]            
            else:
                for i in enm_tabele2.keys():
                    if i == exception:
                        pass
                    else:
                        d[i] = enm_tabele2[i]
            enm_tabele2 = d
                
        if ((mapa == 'povsod') | (len(enm_tabele2) < enm_skupaj2)):
            for j in enm_tabele2.keys():
                for i in enm_tabele2[j]:
                    if i.split("_")[0] == ime_tabele:
                        seznam2.append(link2 + j + "/" + i)
                    else:
                        pass
        else:
            seznam2 = [(link2 + mapa + "/" + i) for i in enm_tabele2[mapa] if i.split("_")[0] == ime_tabele]    
            
        dfji = []
        dfji2 = []
        stolpci = []
        if len(seznam2) > 0:
            for i in seznam2:
                vars()['DF_'+i] = pd.read_csv(i, delimiter = ';', low_memory = False)
                stolp = [i.split("(")[0] for i in vars()['DF_'+i].columns.tolist()]
                stolp1 = add_semicolons_to_repeats(stolp)
                vars()['DF_'+i].columns = stolp1
                dfji.append(vars()['DF_'+i])
        else:
            return print ("Tabela {} ne obstaja!".format(ime_tabele))

        if join == 'outer':
           for i in dfji:
               dfji2.append(i.reset_index(drop = True))
           data2 = pd.concat(dfji2, axis = 0, join = 'outer').reset_index(drop = True)
           
        else:
            for i in dfji:
                stolpci.append(i.columns.to_list())
            a = stolpci[0]
            stevec = len(stolpci)-1
            while stevec:
                a = razlika_seznamov(a,stolpci[stevec], nacin = 'presek')
                stevec = stevec - 1
            # p = set(stolpci[0]).intersection(*stolpci)  # PRESEK stolpcev
            for i in dfji:
                dfji2.append(i[a].reset_index(drop = True))
            data2 = pd.concat(dfji2)
    else:
        data2 = pd.DataFrame()
    if ((data.shape[0] > 0) & (data2.shape[0] > 0)): 
    # Iz starega exporta zmečemo ven vse, kar je že v novem in izenačimo stolpce
        data1 = data[~data['MeContext'].isin(data2['MeContext'].tolist())]
        if join == 'outer':
            skupaj = pd.concat([data1, data2])
        else:
            razl = razlika_seznamov(data1.columns.tolist(), data2.columns.tolist(), nacin = 'presek')
            data1 = data1[razl]
            data2 = data2[razl]
            skupaj = pd.concat([data1, data2])
        return skupaj.reset_index(drop = True)
    elif ((data.shape[0] > 0) & (data2.shape[0] == 0)):
        return data.reset_index(drop = True)
    elif ((data.shape[0] == 0) & (data2.shape[0] > 0)):
        return data2.reset_index(drop = True)
    else:
        return print ("Tabela {} ne obstaja!".format(ime_tabele)) 
    
# # # # # # # # # odlozisce_enm = "G:\\ENM_export\\ulinc\\"
# # # # # # # # # enm_tabele = [i.strip(".csv") for i in os.listdir(odlozisce_enm)]   

# # # # # # # # # def ustvari_df(ime_tabele, obvezni_stolpci = []):
    # # # # # # # # # """
    # # # # # # # # # Če je vir podatkov sparsan xml na tem disku. 
    # # # # # # # # # """
    # # # # # # # # # m = pd.read_csv(odlozisce_enm + ime_tabele + ".csv", sep = ";", low_memory=False)
    # # # # # # # # # st = []
    # # # # # # # # # stev = 0
    # # # # # # # # # for i in m.columns.tolist():
        # # # # # # # # # if i.find("ubNetwor") > 0:
            # # # # # # # # # st.append(i.split("(")[0] + "(" + str(stev) + ")")
            # # # # # # # # # stev = stev + 1
        # # # # # # # # # else:
            # # # # # # # # # st.append(i.split("(")[0])
    # # # # # # # # # m.columns = st
    # # # # # # # # # return m
    
    
def df(vir, povezava):
    dataf = pd.read_sql(vir, povezava)
    rez = pd.DataFrame(dataf, columns=dataf.columns.tolist()).rename(str.upper, axis='columns')
    return rez

def razlika_ustvari(tabela_denali,tabela_atoll, datum = False, kaj = None):
    razlik = pd.merge(tabela_denali,tabela_atoll[tabela_atoll.columns[0]], how='left', left_on=tabela_denali[tabela_denali.columns[0]], right_on=tabela_atoll[tabela_atoll.columns[0]], suffixes = [None, '_a'])
    razlikaa = razlik[razlik[razlik.columns[tabela_denali.shape[1]+1]].isna()]
    razlika = razlikaa[tabela_denali.columns]
    if datum == True:
        razlika['Datum_vpisa'] = datetime.datetime.now().strftime('%Y-%m-%d')
    else:
        pass
    if kaj != None:
        razlika['Dodano/Sprememba/Brisi'] = kaj
    else:
        pass
    if type(razlika) == pd.core.series.Series:
        razlika = razlika.to_frame()
    else:
        pass
    return razlika

def razlika_obst(tabela_denali,tabela_atoll, datum = False, kaj = None):
    razlik = pd.merge(tabela_denali,tabela_atoll, how='inner', left_on=tabela_denali[tabela_denali.columns[0]], right_on=tabela_atoll[tabela_atoll.columns[0]], suffixes = ['_denxx', '_atoxx'])
    razlik_den = razlik.filter(regex = '_denxx')
    razlik_den = razlik_den.rename(columns = lambda x: x.split('_denxx')[0])
    razlik_ato = razlik.filter(regex = '_atoxx')
    razlik_ato = razlik_ato.rename(columns = lambda x: x.split('_atoxx')[0])
    razlikaa = razlik_ato.compare(razlik_den)
    stolpci = razlikaa.columns.tolist()
    razlika = razlik.loc[razlikaa.index].filter(regex = '_denxx')
    razlika = razlika.rename(columns = lambda x: x.split('_denxx')[0])
    if datum == True:
        razlika['Datum_vpisa'] = datetime.datetime.now().strftime('%Y-%m-%d')
    else:
        pass
    if kaj != None:
        razlika['Dodano/Sprememba/Brisi'] = kaj
    else:
        pass
    return razlika

def razlika_spremeni(tabela_denali,tabela_atoll, datum = False, kaj = None):
    razlik = pd.merge(tabela_denali,tabela_atoll, how='inner', left_on=tabela_denali[tabela_denali.columns[0]], right_on=tabela_atoll[tabela_atoll.columns[0]], suffixes = ['_denxx', '_atoxx'])
    razlik_den = razlik.filter(regex = '_denxx')
    razlik_den = razlik_den.rename(columns = lambda x: x.split('_denxx')[0])
    razlik_ato = razlik.filter(regex = '_atoxx')
    razlik_ato = razlik_ato.rename(columns = lambda x: x.split('_atoxx')[0])
    razlikaa = razlik_ato.compare(razlik_den)
    razlikap = razlikaa.filter(regex = 'other').dropna(how  ='all')
    razlikap.columns = razlikap.columns.get_level_values(0)
    raz = razlik[tabela_denali.columns[0]+'_denxx'].to_frame().join(razlikap)
    raz = raz.rename(columns = lambda x: x.split('_denxx')[0])
    if datum == True:
        raz['Datum_vpisa'] = datetime.datetime.now().strftime('%Y-%m-%d')
    else:
        pass
    if kaj != None:
        raz['Dodano/Sprememba/Brisi'] = kaj
    else:
        pass
    return raz
                      
def razlika_stolpec(df, df_name, stolpec, atoll_primary_key, folder):
    if df.shape[0] > 0:
        if atoll_primary_key != stolpec:
            return df[[atoll_primary_key, stolpec]].dropna().to_csv(folder + df_name + '__' + stolpec, index = False, sep = ';', decimal = ',')

def razlika_brisi(tabela_denali,tabela_atoll, datum = False, kaj = None):
    razlik = pd.merge(tabela_denali[tabela_denali.columns[0]],tabela_atoll[tabela_atoll.columns[0]], how='right', left_on=tabela_denali[tabela_denali.columns[0]], right_on=tabela_atoll[tabela_atoll.columns[0]], suffixes = [None, '_a'])
    razlikaa = razlik[razlik[razlik.columns[1]].isna()]
    razlika = razlikaa[razlikaa.columns[2]]
    razlika = razlika.rename(tabela_atoll.columns[0])
    if datum == True:
        razlika['Datum_vpisa'] = datetime.datetime.now().strftime('%Y-%m-%d')
    else:
        pass
    if kaj != None:
        razlika['Dodano/Sprememba/Brisi'] = kaj
    else:
        pass
    if type(razlika) == pd.core.series.Series:
        razlika = razlika.to_frame()
    else:
        pass
    return razlika

def frek_pod_dl(frekvenca):
    if frekvenca >= 1920 and frekvenca <= 2170:
        frek_pod = 2100
    elif frekvenca >= 1710 and frekvenca <= 1880:
        frek_pod = 1800
    elif frekvenca >= 2620 and frekvenca <= 2690:
        frek_pod = 2600
    elif frekvenca >= 880 and frekvenca <= 960:
        frek_pod = 900
    elif frekvenca >= 790 and frekvenca <= 862:
        frek_pod = 800
    elif frekvenca >= 2570 and frekvenca <= 2620:
        frek_pod = 2600
    elif frekvenca >= 3300 and frekvenca <= 3800:
        frek_pod = 3500
    elif frekvenca >= 690 and frekvenca <= 788:
        frek_pod = 700
    elif frekvenca >= 1432 and frekvenca <= 1517:
        frek_pod = 1500        
    else:
        frek_pod = 0
    return frek_pod

def frek_dl(kanal):
    ### GSM
    if kanal in range(0,124,1):
        # GSM 900 PBAND
        frek_dl = kanal/5 + 890 + 45
        frek_ul = kanal/5 + 890
    elif kanal in range(975,1023,1):
        # GSM 900 EBAND
        frek_dl = 890 + 0.2*(kanal - 1024) + 45
        frek_ul = 890 + 0.2*(kanal - 1024)
    elif kanal in range(512,885,1):
        # GSM 1800
        frek_dl =  1710.2 + 0.2*(kanal-512) + 95
        frek_ul =  1710.2 + 0.2*(kanal-512)
    ### LTE
    elif kanal in range(10550,10850,1):
        # UMTS 2100 band 1
        frek_dl = kanal / 5
        frek_ul = frek_dl - 190
    elif kanal in range(0,599,1):
        # LTE 2100 band 1 FDD
        frek_dl = 2110 + 0.1*(kanal)
        frek_ul = frek_dl - 190
    elif kanal in range(1200,1949,1):
        # LTE 1800 band 3
        frek_dl = 1805 + 0.1*(kanal - 1200)
        frek_ul = frek_dl - 95
    elif kanal in range(2750,3449,1):
        # LTE 2600 FDD band 7
        frek_dl = 2620 + 0.1*(kanal - 2750)
        frek_ul = frek_dl - 120
    elif kanal in range(3450,3799,1):
        # LTE 900 band 8
        frek_dl = 925 + 0.1*(kanal - 3450)
        frek_ul = frek_dl - 45
    elif kanal in range(6150,6449,1):
        # LTE 800 band 20
        frek_dl = 791 + 0.1*(kanal - 6150)
        frek_ul = frek_dl + 41
    elif kanal in range(9210,9659,1):
        # LTE 700 band 28
        frek_dl = 758 + 0.1*(kanal - 9210)
        frek_ul = frek_dl - 55 
    ### NR
    elif kanal in range(620000,653333,1):
        # NR 3500 TDD band 78
        frek_dl = 3000 + 0.015*(kanal - 600000)
        frek_ul = frek_dl
    elif kanal in range(524000,538000,1):
        # NR 2600 band n7 FDD
        frek_dl = 0 + 0.005*(kanal - 0)
        frek_ul = frek_dl - 120
    elif kanal in range(151600,160600,1):
        # NR 700 band n28 FDD
        frek_dl = 0 + 0.005*(kanal - 0)
        frek_ul = frek_dl - 55
    elif kanal in range(286400,303400,1):
        # NR 700 band n28 FDD
        frek_dl = 0 + 0.005*(kanal - 0)
        frek_ul = 0
    else:
        frek_dl = 1
        frek_ul = 1
    return round(frek_dl,1), round(frek_ul,1)
# """
    # else:
        # if kanal in range(0,599999,1):
            # frek_dl = 5*(kanal)
        # elif kanal in range(600000,2016666,1):
            # frek_dl = 3000 + 15*(kanal - 600000)
        # elif kanal in range(2016667,3279165,1):
            # frek_dl = 24250.08 + 60*(kanal - 2016667)
        # else:
            # frek_dl = 1
    # return frek_dl
# """            

pomozni_dict_uarfcn = {'GSM 1800': 666,
'GSM 900':110,
'LTE 1800':1657,
'LTE 900':3696,
'LTE 800':6201,
'LTE 700':9260,
'LTE 2600':3023,
'LTE 2700':3023,
'LTE 2100':400,
'NR 2600':526020,
'NR 2100':0,
'NR 3500':631334,
'NR 700':152600,
'NR 1500':288400}



def fiz_antena(ime):
    vrni = ''
    if ime[0:11] == 'Indoor MIMO':
        vrni = 'Indoor MIMO'
    elif ime[-2:-1] == 'X' or ime[-2:-1] == 'x':
        vrni = ime[0:-2]
    elif ime[-5:-4]=='x' or ime[-5:-4]=='X':
        vrni = ime[0:ime.find('MIMO')-2]
    elif ime[-3:-2] == 'v':
        vrni = ime[0:ime.find('v')]
    elif ime[-3:-2] == 'V':
        vrni = ime[0:ime.find('V')]
    else: 
        vrni = ime
    vrni = vrni.replace(' ','')
    vrni = vrni.replace('-','')
    vrni = vrni.replace('/','')
    if vrni[0] == 'K' or vrni[0] == 'k':
        if vrni[2].isnumeric() == False:
            vrni = vrni
        else:
            vrni = vrni[1:]
    return str.upper(vrni)

"""
    if vrni[-3] == 'v' or vrni[-3] == 'V':
        vrni = vrni[len(vrni)-3]
    else:
        vrni = vrni
"""


antene_izjeme = {'Indoor SISO': 'Indoor SISO',
                 'Indoor MIMO 2x2': 'Indoor MIMO',
                 'RadioDot4442 x2': 'RadioDot4442',
                 'RadioDot2243 x2': 'RadioDot2243',
                 'APX18206515-0T2': 'APX18206515-0T2_2140_X_CO_M45_02T',
                 'APX182065150T6': 'APX182065150T6_2140_X_CO_M45_06T',
                 'Huawei Pico Int': 'Huawei Pico Int',
                 'Huawei MicroInt': 'Huawei MicroInt',
                 'DB844H35E-SY':    'DB844H35E-SY_00DT_0910',
                 'K 736 349 x2':    '736349_0948_X_CO',
                 'CMA-B/3324':      'CMA3324_0_1860',
                 'RadioDot4442':    'RadioDot4442',
                 'RadioDot2243':    'RadioDot2243',
                 'AIRSPANAV1200':'AIRSPANAV1200',
                 'Airspan AV1200':'Airspan AV1200',
                 'AIRSPANAV600':'AIRSPANAV1200',
                 'Airspan AV600':'Airspan AV1200',
                 'MICROE6503':'MICROE6503', 
                 'K 738 445':'738445',
                 'K 738 445 x2':'738445',
                 'K 738 447':'738445'}

def et_prev(et, et_spodnji, et_zgornji):
    if et <= et_spodnji:
        rez = et_spodnji
    elif et >= et_zgornji:
        rez = et_zgornji
    else:
        rez = et
    return rez

def et_prev1(et, et_spodnji, et_zgornji):
    if et <= et_spodnji:
        rez = et_spodnji
    elif et >= et_zgornji:
        rez = et_zgornji
    else:
        rez = et
    return np.ceil(rez)
    
def port(antenski_diagram_ime, seznam):
   """Funkcija port na vseh antenskih diagramih iz Atoll-a preveri če sta zadnja dva znaka imena
   antenskega diagrama v seznamu. Seznam je seznam vseh simbolov za porte iz denali baze. Poleg tega
   določi kot ime porta črko P za vse E/// AIR antene. """
   if (antenski_diagram_ime[len(antenski_diagram_ime)-2:len(antenski_diagram_ime)]) in seznam:
       p = (antenski_diagram_ime[len(antenski_diagram_ime)-2:len(antenski_diagram_ime)])
   elif antenski_diagram_ime[0:3] == 'AIR':
       p = 'P'
   elif antenski_diagram_ime[-5:-1] == 'Port':
       p = antenski_diagram_ime[-5:] 
   else:
       p = 'port'
   return p
    
def mimo(ime):
    if ime[:-2] == 'X' or ime[:-2] == 'x':
        mimo = ime[-2:-1]
    elif ime[-5:-4]=='x' or ime[-5:-4]=='X':
        mimo = ime[-5:-4]
    else:
        mimo = 1
    return mimo

def prazno(polje):
    if polje.isna()==True:
        vred = 3
    else:
        vred = polje
    return vred

def naslednja_vrstica(excel, sheet):
    p = pd.read_excel(excel, sheet)
    if p.shape[0] == 0:
        value = 0
    else:
        value = p.shape[0]+1
    del p
    return value

def head(excel, sheet):
    p = pd.read_excel(excel, sheet)
    if p.shape[0] == 0:
        value =  True
    else:
        value =  False
    del p
    return value

def vrstice_excel(excel, stevec = False):
    slovar = {}
    if stevec == True:
        for sheet in pd.ExcelFile(excel).sheet_names:
            slovar[sheet] = pd.read_excel(excel, sheet_name = sheet).shape[0]
    else:
        for sheet in pd.ExcelFile(excel).sheet_names:
            slovar[sheet] = pd.read_excel(excel, sheet_name = sheet).title
    return slovar

def razdalja (long1, lati1, long2, lati2):
    R = 6373.0
    pi = 3.141592653589793

    lat1 = long1*pi/180
    lon1 = lati1*pi/180
    lat2 = long2*pi/180
    lon2 = lati2*pi/180
    
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    distance = R * c * 1000
    return distance

def razdalja_gk (long1, lati1, long2, lati2):
    distance = np.sqrt((long1-long2)*(long1-long2) + (lati1-lati2)*(lati1-lati2))
    return distance
    
def v_snopu(X, Y, X_antene, Y_antene, azimut, sirina_ant_snopa = 100):
    """
    Funkcija vrne TRUE ali FALSE glede na to, ali je točka (X,Y) v snopu antene ali ne
    """

    ats = np.arctan2((Y_antene - Y),(X_antene - X))
    arcts = 90 - 180/np.pi*ats
    if arcts < 0:
        arcts = 360 + arcts
    else:
        pass
    if (Y_antene == Y) & (X_antene == X):
        arcts = 0.0
    else:
        pass        
    kot = arcts
    
    #kot = kot*180/np.pi
    ant_1 = np.mod(azimut + sirina_ant_snopa/2,360)
    ant_2 = np.mod(azimut - sirina_ant_snopa/2,360)
    if np.mod(ant_1-kot,360) <= sirina_ant_snopa:
        snop = True
    else:
        snop = False
    return snop

def func(x):
    return print(x*x)
    
def pripona(ime_celice):
    """
    Funkcija vrne tehnologijo in Atoll FBAND celice glede na pripono v imenu. Npr: ABEZIT2 -> 2 predstavlja GSM 900 itd.
    primer uporabe: df[['cell','tehnologija','atoll_fband','tehnol', 'frekvenca']] = df[['Cell']].apply(lambda x: funkcije_at.pripona(x['Cell']),axis=1, result_type = 'expand')
    """
    if list(ime_celice)[-1] in ('1','2','3','7','8'):
        fband = 'GSM 900'
        tehn = 'GSM'
        tehnol = 'GSM 900'
        frekvenca = 900
    elif list(ime_celice)[-1] in ('4','5','6','9'):
        fband = 'GSM 1800'
        tehn = 'GSM'
        tehnol = 'GSM 1800'
        frekvenca = 1800
    elif "".join(list(ime_celice)[-3:-1]) == '08':
        fband = 'n20 / E-UTRA 20 (800 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 800'
        frekvenca = 800
    elif "".join(list(ime_celice)[-3:-1]) == '18':
        fband = 'n3 / E-UTRA 3 (1800 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 1800'
        frekvenca = 1800
    elif "".join(list(ime_celice)[-3:-1]) == '27':
        fband = 'n7 / E-UTRA 7 (2600 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 2600'
        frekvenca = 2600
    elif "".join(list(ime_celice)[-3:-1]) == '26':      # izjema!!!!!!
        fband = 'n7 / E-UTRA 7 (2600 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 2600'
        frekvenca = 2600
    elif "".join(list(ime_celice)[-3:-1]) == '09':
        fband = 'n8 / E-UTRA 8 (900 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 900'
        frekvenca = 900
    elif "".join(list(ime_celice)[-3:-1]) == '21':
        fband = 'n1 / E-UTRA 1 (2100 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 2100'
        frekvenca = 2100
    elif "".join(list(ime_celice)[-3:-1]) == '07':
        fband = 'n28 / E-UTRA 28 (700 MHz)'
        tehn = 'LTE'
        tehnol = 'LTE 700'
        frekvenca = 700
    elif "".join(list(ime_celice)[-5:-1]) == '35NR':
        fband = 'n78 (3300 MHz)'
        tehn = '5G'
        tehnol = 'NR 3500'
        frekvenca = 3500
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':
        fband = 'n75 / E-UTRA 75 (1500 MHz)'
        tehn = '5G'
        tehnol = 'NR 1500'
        frekvenca = 1500
    elif "".join(list(ime_celice)[-5:-1]) == '21NR':
        fband = 'n1 / E-UTRA 1 (2100 MHz)'
        tehn = '5G'
        tehnol = 'NR 2100'
        frekvenca = 2100                  
    elif "".join(list(ime_celice)[-5:-1]) == '07NR':
        fband = 'n28 / E-UTRA 28 (700 MHz)'
        tehn = '5G'
        tehnol = 'NR 700'
        frekvenca = '700'
    elif "".join(list(ime_celice)[-5:-1]) == '07SS':
        fband = 'n28 / E-UTRA 28 (700 MHz)'
        tehn = '5G'
        tehnol = 'NR 700'
        frekvenca = 700
    elif "".join(list(ime_celice)[-5:-1]) == '26NR':
        fband = 'n7 / E-UTRA 7 (2600 MHz)'
        tehn = '5G'
        tehnol = 'NR 2600'
        frekvenca = 2600
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':
        fband = 'n75 / E-UTRA 75 (1500 MHz)'
        tehn = '5G'
        tehnol = 'NR 1500'
        frekvenca = 1500
    else:
        fband = ''
        tehn = ''
        tehnol = ''
        frekvenca = ''
    return ime_celice, tehn, fband, tehnol, frekvenca

def glava_ascii(fr):
    """
    Bere glavo ascii exporta iz atoll-a
    """
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
    return sl    #, typeo, timestamp, resolution, xmin, xmax, ymin, ymax, x_num_pixels, y_num_pixels
    
def beri_atoll_ascii(file):
    with open(file, "r") as fo:
        fo_read = fo.readlines()
        fo_read_str = [i.strip("\n") for i in fo_read]
        fo.close()
    gl = glava_ascii(fo_read_str)
    body = fo_read_str[11:len(fo_read_str)]
    body_df = pd.DataFrame(body)
    body_df = body_df[0].str.split(r"\t|;", expand = True)
    body_df[0] = body_df[0].str.replace(".","")
    body_df[1] = body_df[1].str.replace(".","")
    return(gl, body_df)

def sektor(zadnja_crka):
    if zadnja_crka == '1':
        sektor = 1
    elif zadnja_crka == '2':
        sektor = 2
    elif zadnja_crka == '3':
        sektor = 3
    elif zadnja_crka == '4':
        sektor = 1
    elif zadnja_crka == '5':
        sektor = 2
    elif zadnja_crka == '6':
        sektor = 3
    elif zadnja_crka == '7':
        sektor = 4
    elif zadnja_crka == '8':
        sektor = 5
    elif zadnja_crka == 'A':
        sektor = 1
    elif zadnja_crka == 'B':
        sektor = 2
    elif zadnja_crka == 'C':
        sektor = 3
    elif zadnja_crka == 'D':
        sektor = 4
    elif zadnja_crka == 'E':
        sektor = 5
    elif zadnja_crka == 'F':
        sektor = 6
    elif zadnja_crka == 'G':
        sektor = 7
    else:
        sektor = 1
    return sektor


def inverse_sektor(tehnologija, sektor):
    """Na podlagi sektorja in tehnologije vrne zadnjo črko celice."""
    if tehnologija.find('LTE') >= 0:
        if sektor == 1:
            vii = 'A'
        elif sektor == 2:
            vii = 'B'
        elif sektor == 3:
            vii = 'C'
        elif sektor == 4:
            vii = 'D'
        elif sektor == 5:
            vii = 'E'
        else:
            pass
    elif tehnologija.find('NR') >= 0:
        if sektor == 1:
            vii = 'A'
        elif sektor == 2:
            vii = 'B'
        elif sektor == 3:
            vii = 'C'
        elif sektor == 4:
            vii = 'D'
        elif sektor == 5:
            vii = 'E'
        else:
            pass
    elif tehnologija.find('GSM 900') >= 0:
        if sektor == 1:
            vii = '1'
        elif sektor == 2:
            vii = '2'
        elif sektor == 3:
            vii = '3'
        elif sektor == 7:
            vii = '4'
        elif sektor == 8:
            vii = '5'
        else:
            pass 
    elif tehnologija.find('GSM 1800') >= 0:
        if sektor == 1:
            vii = '4'
        elif sektor == 2:
            vii = '5'
        elif sektor == 3:
            vii = '6'
        elif sektor == 4:
            vii = '9'
        else:
            pass 
    else:
        vii = 1
    return vii

def arfcn(ime_celice):
    """
    Funkcija na podlagi celice oziroma dela v njenem imenu vrne e-nr-arfcn. 
    Ne dela pravilno za GSM. 
    """
    if list(ime_celice)[-1] in ('1','2','3','7','8'):
        arfcn_dl = 124
        arfcn_ul = 124
        BW= 0.2
        band = 8
        teh = 'GSM'
        cell_id_pripona = ''
        power = 0
    elif list(ime_celice)[-1] in ('4','5','6','9'):
        arfcn_dl = 1000
        arfcn_ul = 1000
        BW = 0.2
        band = 3
        teh = 'GSM'
        cell_id_pripona = ''
        power = 0
    elif "".join(list(ime_celice)[-3:-1]) == '08':
        arfcn_dl = 6201
        arfcn_ul = 24201
        BW = 10
        band = 20
        teh = 'LTE'
        cell_id_pripona = '20'
        power = 40000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '18':
        arfcn_dl = 1657
        arfcn_ul = 19657
        BW = 20
        band = 3
        teh = 'LTE'
        cell_id_pripona = '3'
        power = 160000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '27':
        arfcn_dl = 3023
        arfcn_ul = 21023
        BW = 15
        band = 7
        teh = 'LTE'
        cell_id_pripona = '7'
        power = 70000   # W
        power = 160000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '26':
        arfcn_dl = 3023
        arfcn_ul = 21023
        BW = 15
        band = 7
        teh = 'LTE'
        cell_id_pripona = '7'
        power = 70000   # W
        power = 160000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '09':
        arfcn_dl = 3696
        arfcn_ul = 21696
        BW = 10
        band = 8
        teh = 'LTE'
        cell_id_pripona = '8'
        power = 40000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '21':
        arfcn_dl = 400
        arfcn_ul = 18400
        BW = 20
        band = 1
        teh = 'LTE'
        cell_id_pripona = '1'
        power = 160000   # W
    elif "".join(list(ime_celice)[-3:-1]) == '07':
        arfcn_dl = 9260
        arfcn_ul = 27260
        BW = 10
        band = 28
        teh = 'LTE'
        cell_id_pripona = '18'
        power = 40000   # W
    elif "".join(list(ime_celice)[-5:-1]) == '35NR':
        arfcn_dl = 631334
        arfcn_ul = 631334
        BW = 100
        band = 78
        teh = 'NR'
        cell_id_pripona = '24'      # 78 je v navodilih
        power = 140000  # W
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':
        arfcn_dl = 288400
        arfcn_ul = 0
        BW = 20
        band = 75
        teh = 'NR'
        cell_id_pripona = '75'
        power = 40000  # W    
    elif "".join(list(ime_celice)[-5:-1]) == '21NR':
        arfcn_dl = 430000
        arfcn_ul = 392000
        BW = 20
        band = 1
        teh = 'NR'
        cell_id_pripona = '1'
        power = 40000  # W                 
    elif "".join(list(ime_celice)[-5:-1]) == '07NR':
        arfcn_dl = 152600
        arfcn_ul = 141600
        BW = 10
        band = 28
        teh = 'NR'
        cell_id_pripona = '28'
        power = 40000   # W
    elif "".join(list(ime_celice)[-5:-1]) == '07SS':
        arfcn_dl = 152600
        arfcn_ul = 141600
        BW = 10
        band = 28
        teh = 'NR'
        cell_id_pripona = '28'
        power = 40000   # W
    elif "".join(list(ime_celice)[-5:-1]) == '26NR':
        arfcn_dl = 526020
        arfcn_ul = 502020
        BW = 20
        band = 7
        teh = 'NR'
        cell_id_pripona = '6'
        power = 90000   # W
    elif "".join(list(ime_celice)[-5:-1]) == '21NR':    # Potrebo popraviti!!!!                                                            
        arfcn_dl = 526020
        arfcn_ul = 502020
        BW = 20
        band = 1
        teh = 'NR'
        cell_id_pripona = '1'
        power = 90000   # W
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':                                                           
        arfcn_dl = 288400
        arfcn_ul = 0
        BW = 20
        band = 75
        teh = 'NR'
        cell_id_pripona = '75'
        power = 80000   # W
    else:
        arfcn_dl = 0
        arfcn_ul = 0
        BW = 0
        band = 0
        teh = '___'
        cell_id_pripona = '___'
        power = 0
    return arfcn_dl, arfcn_ul, BW, band, teh, cell_id_pripona, power
    
def carrier_atoll(ime_celice):
    """
    Funkcija na podlagi celice oziroma dela v njenem imenu vrne carrier za uvoz v atoll
    Ne dela pravilno za GSM. 
    """
    if list(ime_celice)[-1] in ('1','2','3','7'):
        carrier = ''
    elif list(ime_celice)[-1] in ('4','5','6','8'):
        carrier = ''
    elif "".join(list(ime_celice)[-3:-1]) == '08':
        carrier = '10 MHz - EARFCN 6201'
    elif "".join(list(ime_celice)[-3:-1]) == '18':
        carrier = '20 MHz - EARFCN 1657'
    elif "".join(list(ime_celice)[-3:-1]) == '27':
        carrier = '15 MHz - EARFCN 3023'
    elif "".join(list(ime_celice)[-3:-1]) == '26':
        carrier = '15 MHz - EARFCN 3023'
    elif "".join(list(ime_celice)[-3:-1]) == '09':
        carrier = '10 MHz - EARFCN 3696'
    elif "".join(list(ime_celice)[-3:-1]) == '21':
        carrier = '20 MHz - EARFCN 400'
    elif "".join(list(ime_celice)[-3:-1]) == '07':
        carrier = '10 MHz - EARFCN 9260'
    elif "".join(list(ime_celice)[-5:-1]) == '35NR':
        carrier = '100 MHz - NR-ARFCN 631334'
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':
        carrier = '20 MHz - NR-ARFCN 288400'  
    elif "".join(list(ime_celice)[-5:-1]) == '21NR':
        carrier = '20 MHz - NR-ARFCN 430000'          
    elif "".join(list(ime_celice)[-5:-1]) == '07NR':
        carrier = '10 MHz - NR-ARFCN 152600'
    elif "".join(list(ime_celice)[-5:-1]) == '07SS':
        carrier = '10 MHz - NR-ARFCN 152600'
    elif "".join(list(ime_celice)[-5:-1]) == '26NR':
        carrier = '20 MHz - NR-ARFCN 526020'
    elif "".join(list(ime_celice)[-5:-1]) == '15NR':
        carrier = '20 MHz - NR-ARFCN 288400'
    else:
        carrier = ''
    return carrier

def cell_id(tehnol):
    sl = {'GSM 900':'','GSM 1800':'','LTE 700':'18','LTE 800':'20','LTE 900':'8','LTE 1800':'3','LTE 2100':'1','LTE 2600':'7','NR 700':'28','NR 2600':'6','NR 3500':'24', 'NR 1500':'75'}
    return sl[tehnol]

def dbm_v_w(moc_dbm):
    return 0.001*np.power(10,(moc_dbm/10))
    
def w_v_dbm(moc_w):
    return 10*np.log10(moc_w/0.001)


def termicni_sum(BW, enota = 'W'):
    """
    BW = bandwidth v Hz
    """
    if enota == 'W':
        return boltzmanova_konstanta * T* BW
    else:
        return funkcije_at.np.log10(boltzmanova_konstanta * T* BW/0.001)*10

# def sinr_to_thr(sinr, teh = 'LTE'):
    # if teh == 'LTE':

def enak_seznam(seznam1, seznam2):
    if seznam1 == seznam2:
        return True
    else:
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
        return r

def razlika_seznamov(seznam1, seznam2, nacin = 'komplement2'):
    """
    vsebuje: Če je vrednost nacin = 'komplement1', potem funkcija vrne vse elemente, ki so samo v 1. seznamu
             Če je vrednost nacin = 'komplement2', potem funkcija vrne vse elemente, ki so samo v 2. seznamu
             Če je vrednost nacin = 'presek', potem funkcija vrne vse elemente, ki so v obeh seznamih(presek)
             Če je vrednost nacin = 'unija', potem funkcija vrne vse elemente v obeh seznamih(unija) - brez podvojenih vrednosti
    """
    razlika = []
    if nacin == 'komplement2':
        if seznam1 == seznam2:
            razlika = []
        else:
            for i in seznam2:
                if i not in seznam1:
                    razlika.append(i)
                
    elif nacin == 'komplement1':
        if seznam1 == seznam2:
            razlika = []
        else:
            for i in seznam1:
                if i not in seznam2:
                    razlika.append(i)             
    elif nacin == 'presek':
        if seznam1 == seznam2:
            razlika = seznam1
        else:
            for i in seznam1:
                if i in seznam2:
                    razlika.append(i)                    
    elif nacin == 'unija':
        if seznam1 == seznam2:
            razlika = seznam1
        else:
            razlika = list(set(seznam1+ seznam2))
    else:
        pass
    return razlika

def elementi_v_seznamu(seznam1, seznam2):
    """
    Funkcija vrne True, če so vsi elementi iz seznama1 v seznamu2, drugače False. 
    """
    for i in seznam1:
        if i not in seznam2:
            r = False
            break
        else:
            r = True
    return r
    
def list_n(seznam, n):
    """
    Funkcija vrne seznam seznamov iz vhodnega seznama, in vsak seznam v novem seznamu vsebuje po n elementov vhodnega seznama
    """
    s1 = []
    s1_ = []
    s2 = []
    for i in seznam:
        s1.append(i)
        s1_.append(i)
        if len(s1) == n:
            s2.append(s1)
            s1 = []
            s1_ = []
    if len(s1_) > 0:
        s2.append(s1_)
    if len(s2) == 1:
        s2 = s2[0]
    else:
        pass
    return(s2)
    
def izracun_parov(slovar_scheduler, slovar_lte_niti_, slovar_nr_niti_,  oznaka = '0', razlika = 0):
    rez = pd.DataFrame()
    scheduler = slovar_scheduler
    slovar_lte_niti = slovar_lte_niti_
    slovar_nr_niti = slovar_nr_niti_
    
    for nrcell in scheduler['NRCellCU'].tolist():
        ti0 = time.time()    
        lte_c = scheduler.loc[scheduler['NRCellCU'] == nrcell, 'EUtranCellFDD'].values[0]
        nrc = slovar_nr_niti[slovar_nr_niti[2] == nrcell]
        lc = slovar_lte_niti[slovar_lte_niti[2].isin(lte_c)]
        if razlika != 0:
            sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            # sk['razlika'] = sk[]
            rez = pd.concat([rez, sk])            
        else:
            lc = lc[[0,1]].drop_duplicates()
            sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            rez = pd.concat([rez, sk])
        ti1 = time.time()
        print("Čas celice {} je {} s".format(nrcell, ti1-ti0))
    return rez.to_csv(r"G:\Pokrivanja\NSA_pomozni\\NSApar" + oznaka + ".csv", index = False)    

# def izracun_parov_proc(slovar_scheduler, slovar_lte_niti_, slovar_nr_niti_,  oznaka_proc = '0', oznaka_nit = '0', razlika = 0):
    # """
    # Ne dela!
    # """
    # rez = pd.DataFrame()
    # scheduler = slovar_scheduler
    # slovar_lte_niti = slovar_lte_niti_
    # slovar_nr_niti = slovar_nr_niti_
    
    # for nrcell in scheduler['NRCellCU'].tolist():
        # ti0 = time.time()    
        # lte_c = scheduler.loc[scheduler['NRCellCU'] == nrcell, 'EUtranCellFDD'].values[0]
        # nrc = slovar_nr_niti[slovar_nr_niti[2] == nrcell]
        # lc = slovar_lte_niti[slovar_lte_niti[2].isin(lte_c)]
        # if razlika != 0:
            # sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            # # sk['razlika'] = sk[]
            # rez = pd.concat([rez, sk])            
        # else:
            # lc = lc[[0,1]].drop_duplicates()
            # sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            # rez = pd.concat([rez, sk])
        # ti1 = time.time()
        # print("Čas celice {} je {} s".format(nrcell, ti1-ti0))
    # return rez.to_csv(r"G:\Pokrivanja\NSA_pomozni\\NSApar" + oznaka + ".csv", index = False)   
    
def izracun_parov_ca(slovar_scheduler, slovar_lte_niti_, slovar_nr_niti_,  oznaka = '0', razlika = 0):
    rez = pd.DataFrame()
    scheduler = slovar_scheduler
    slovar_lte_niti = slovar_lte_niti_
    slovar_nr_niti = slovar_nr_niti_
    
    for nrcell in scheduler['P'].tolist():
        ti0 = time.time()    
        lte_c = scheduler.loc[scheduler['P'] == nrcell, 'S'].values[0]
        nrc = slovar_nr_niti[slovar_nr_niti[2] == nrcell]
        lc = slovar_lte_niti[slovar_lte_niti[2].isin(lte_c)]
        if razlika != 0:
            sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            sk['razlika'] = abs(sk['3_x'] - sk['3_y'])
            sk = sk[sk['razlika'] <= razlika]
            sk.drop(columns = ['razlika', '2_y','3_y'], inplace = True)
            sk.rename(columns = {'2_x':2, '3_x':3}, inplace = True)
            rez = pd.concat([rez, sk])            
        else:
            lc = lc[[0,1]].drop_duplicates()
            sk = pd.merge(nrc, lc, how = 'inner', left_on = [0,1], right_on = [0,1])
            rez = pd.concat([rez, sk])
        ti1 = time.time()
        print("Čas celice {} je {} s".format(nrcell, ti1-ti0))
    return rez.to_csv(r"G:\Pokrivanja\CA_pomozni\\parCA" + oznaka + ".csv", index = False) 
    
def izracun_parov_ca1(input_df, dfji_P, dfji_S, oznaka = '0', razlika = 0):
    rez = pd.DataFrame()

    
    for kk in input_df['P'].tolist():
        ti0 = time.time()    
        p = dfji_P[dfji_P[2] == kk]
        s = dfji_S[dfji_S[2].isin(input_df['S'][input_df['P'] == kk].values[0])]

        sk = pd.merge(p, s, how = 'inner', left_on = [0,1], right_on = [0,1])
        if sk.shape[0] > 0:
            sk['razlika'] = abs(sk['3_x'] - sk['3_y'])
            sk = sk[sk['razlika'] <= razlika]
            sk.drop(columns = ['razlika', '2_y','3_y'], inplace = True)
            sk.rename(columns = {'2_x':2, '3_x':3}, inplace = True)
            rez = pd.concat([rez, sk])  
        else:
            pass

        ti1 = time.time()
        print("Čas celice {} je {} s".format(kk, ti1-ti0))
    return rez.to_csv(r"G:\Pokrivanja\CA_pomozni\\parCA" + oznaka + ".csv", index = False)     
    
def vse_mozne_celice_na_lokacijo(lokacija):
    """
    Funkcija vrne vse možna imena celic v skladu z našim naming conventionom s korenom lokacije. 
    """
    vse_cel = []
    for i in ['07','08','09','18','21','26','27','35']:
        for j in ['','NR','SS']:
            for k in ['A','B','C','D','E','F','G','H']:
                vse_cel.append(lokacija + i + j + k)
    for i in ['1','2','3','4','5','6','7','8']:
        vse_cel.append(lokacija + i)
    return vse_cel
    
def pisi_v_csv(tehn, temp, meje, proc):
    temp_ = temp.filter((pl.col("0") >= meje[0]) & (pl.col("0") < meje[1]) & (pl.col("1") >= meje[2]) & (pl.col("1") < meje[3]))
    return temp_.write_csv(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\Indexed\Pomozno\\" + tehn + "_" + str(proc) + ".txt")
    