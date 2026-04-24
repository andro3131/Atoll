# -*- coding: utf-8 -*-
################################
#   Naredimo shape fileje za potrebe 112 iz dnevnih exportov (25m resolucija)
#   Exporte dela aplikacija Atoll. 
#
#
################################

import df_to_tiff
import tif_to_shp
import funkcije_at
import os
import time
import subprocess
import pyodbc
import threading
import re
import polars as pl
import sql_denali_3794
import sql_atoll_3794
import ericsson_enm_tabele
import geopandas as gpd
import datetime
import io
import numpy as np

folder_pokrivanja = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\"
celice = "D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\Celice_na_dan\\celice_na_dan.txt"
odlozisce = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export\\"
odlozisce_raster = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export\celice_ascii_atoll\\"
odlozisce_shp = r"D:\Atoll_projects_planer01\Avtomatika\Eksport\Celice_na_dan_atoll_export\celice_shp_atoll\\"
sinr_to_bearer = r"G:\Pokrivanja\Stevci\\bearer_mapping_atoll.txt"
bearer_coveri = r"G:\Pokrivanja\Stevci\\C_over_I_mapping_atoll.txt"

shp_crit = False    # Če želimo tudi .shp exporte v EPSG:3912, daj True!
raster_crit = True

conn_atoll = pyodbc.connect('Driver={SQL Server};'
                      'Server=BPW-DENALI;'
                      'Database=atoll_d96;'
                      'UID=beribaze;'
                      'PWD=beribaze')
ci_atoll_query = """with petg as (
select c.TX_ID as cel,  case when CID is Null THEN '-1' ELSE CID END AS CI  from atoll_d96.dbo.xgcells5gnr cells
inner join atoll_d96.dbo.xgcellsuids c on c.CELL_ID = cells.CELL_ID
where ACTIVE = 1 and charindex('_',TX_ID,1) = 0),
petga as (
select cel, CONVERT(bigint, ci) as CI from petg),
dvag as (
select tx_id as cel, CID as CI from atoll_d96.dbo.gtransmitters
where ACTIVE = 1 and charindex('_',TX_ID,1) = 0),
stirig as (
select c.TX_ID as cel, ECI as CI from atoll_d96.dbo.xgcellslte cells
inner join atoll_d96.dbo.xgcellsuids c on c.CELL_ID = cells.CELL_ID
where ACTIVE = 1 and charindex('_',TX_ID,1) = 0),
skupaj as (select * from petga union all select * from  dvag union all select * from stirig)
select * from skupaj"""

def krmili_vbs_skripto():
    if shp_crit == True:
        v = 'shp_crit = True\n'
    else:
        v = 'shp_crit = False\n'
    if raster_crit == True:
        v1 = 'raster_crit = True\n'
    else:
        v1 = 'raster_crit = False\n'
    pprs = []
    with open('C:\\Users\\planer02\\Skripte\\VBasic\\shape_export_112.vbs', 'r') as pp:
        ppr = pp.readlines()
    stev = 0
    for i in ppr:
        if bool(re.search(r"shp_crit\s*=",i)):
            line_s = stev
            break
        else:
            stev = stev + 1
    stev = 0
    for i in ppr:
        if bool(re.search(r"raster_crit\s*=",i)):
            line_r = stev
            break
        else:
            stev = stev + 1  
    ppr[line_s] = v
    ppr[line_r] = v1
    with open('C:\\Users\\planer02\\Skripte\\VBasic\\shape_export_112.vbs', 'w') as pp:
        pp.write("".join(ppr))
    return 0

def vnesi_celico_v_drugi_stolpec(mapa, fajl):
    if ((fajl.find("TXT") >= 0)  | (fajl.find("txt") >= 0)): 
        cel = fajl.split(".")[0]
        with open(mapa + fajl, "r") as dd:
            ddr = dd.readlines()
            ddr1 = ddr[0:11]
            for i in ddr[11:]:
                if i.find("\t") > 0:
                    o = "".join(re.findall(r"[0-9]{2,3}\t|\t-*[0-9]{2,3}.[0-9]|\[0\]|[0-9]{2,3}", i)) + "\n"
                    o = ";".join(o.split("\t"))
                else:
                    if i[0:5].find(".") > 0:
                        o = "".join(re.findall(r"[0-9]{2,3};|;-*[0-9]{2,3}.[0-9]|\[0\]|[0-9]{2,3}", i)) + "\n"
                    else:
                        o = i
                if o.find("[0]") > 0:
                    ddr1.append(o.replace("[0]", cel))
                else:
                    ddr1.append(o)
            dd.close()
        with open(mapa + fajl, "w") as dd:
            dd.write("".join(ddr1))
            dd.close()
    return 0
        
        
        
        
def celice_na_dan():
    with open(celice, "r") as dd:
        ddr = dd.readlines()
        dd.close()
    if len(ddr) > 0:
        a = funkcije_at.pd.read_csv(celice, sep = ";", header = None)
    else:
        a = funkcije_at.pd.DataFrame()
    return a

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

def beri_atoll_txt_export_1_dva_server(atoll_txt_export_file_path, celica = []):
    """
    Funkcija vrne podatke v glavi Atoll .txt exporta in vsebino v dveh filejih
    """
    file_open  = open(atoll_txt_export_file_path, 'r')
    file_read = file_open.readlines()
    file_open.close()
    file_header = file_read[0:11]
    file_ostalo = file_read[11:]
    # preštej ločila v vrstici, če je uprabljeno \t ga spremeni v podpičje
    if len(celica) > 0:
        file_ostalo1 = []
        for i in celica:
            for j in file_ostalo:
                if j.find(i) >= 0:
                    file_ostalo1.append(j)
    else:
        file_ostalo1 = file_ostalo
    file_podpicje = []
    for i in file_ostalo1:
        file_podpicje.append(i.replace("\t",";").strip("\n"))
    # Preštej podpicja v vrsticah. Zanimata nas prvi in drugi best server. 
    file_podp = []
    for i in file_podpicje:
        file_podp.append(i + (5 - i.count(";"))*";")
    t = funkcije_at.pd.DataFrame()
    for j in list(range(6)):
        s = [i.split(";")[j] for i in file_podp]
        se = funkcije_at.pd.Series(s)
        t[j] = se.values
        t.replace("",funkcije_at.np.nan)
    return t.replace("",funkcije_at.np.nan)

def split_stevilo(seznam, m):
    sez = [i.split(";")[m] for i in seznam]
    return sez

# vir: https://alexandra-zaharia.github.io/posts/how-to-return-a-result-from-a-python-thread/   
 
class ReturnValueThread(threading.Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None

    def run(self):
        if self._target is None:
            return  # could alternatively raise an exception, depends on the use case
        try:
            self.result = self._target(*self._args, **self._kwargs)
        except Exception as exc:
            print(f'{type(exc).__name__}: {exc}', file=sys.stderr)  # properly handle the exception

    def join(self, *args, **kwargs):
        super().join(*args, **kwargs)
        return self.result

def splitaj_seznam(seznam, n, slovar):
    slovar[n] = [i.split(";")[n] for i in seznam]
    
def beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path, n, vsebuje = [], header_list = False):
    """
    Funkcija vrne podatke v glavi Atoll .txt exporta in vsebino v dveh filejih
    n: Stevilo serverjev. Max = 6, Min = 1
    Če je seznam prazen, naredi dataframe z vsemi celicami
    """
    stevilo = 2 + n*2

    if  ((n < 1) | (n > 6)):
        return print("Stevilo serverjev ni ustrezno!")
        pass
    else:
        ti0 = time.time()
        file_open  = open(atoll_txt_export_file_path, 'r')
        file_read = file_open.readlines()
        file_open.close()
        file_header = file_read[0:11]
        file_ostalo = file_read[11:]
        # preštej ločila v vrstici, če je uprabljeno \t ga spremeni v podpičje
        # if len(vsebuje) > 0:
            # file_ostalo1 = []
            # for i in vsebuje:
                # for j in file_ostalo:
                    # if j.find(i) >= 0:
                        # file_ostalo1.append(j)
        # else:
            # file_ostalo1 = file_ostalo
            
        if len(vsebuje) > 0:
            file_ostalo1 = []
            uur = file_ostalo
            reg = "|".join(vsebuje)
            for i in uur:
                if re.search(reg, i):
                    file_ostalo1.append(i)
                else:
                    pass
        else:
            file_ostalo1 = file_ostalo  
         
        file_podpicje = []
        for i in file_ostalo1:
            file_podpicje.append(i.strip("\n"))
        body_dl = pl.DataFrame(file_podpicje)
        body_dl = body_dl.select(pl.col("column_0").str.split(";").list.to_struct(n_field_strategy="max_width")).unnest("column_0")
        tzz = body_dl.to_pandas()
        tzz = tzz[[i for i in tzz.columns.tolist()[0:stevilo]]]
        tzz.columns = list(range(0,stevilo))
        tzz.replace(funkcije_at.np.nan,funkcije_at.np.nan, inplace = True)
        if header_list == True:
            return tzz, file_header
        else:
            return tzz


            
def beri_atoll_txt_export_1_n_server_pl(atoll_txt_export_file_path,  n=6, vsebuje = [], output_header_list = False, gabariti = []):
    """
    Funkcija vrne vsebino exporta in/ali  podatke v glavi
    input: če je '', je input atoll.txt export, če je input 'seznam', damo seznam (1 vrstica je 1 bin, podatki na bin ločeni s podpičjem)
    n: Stevilo serverjev. Max = 6, Min = 1
    vsebuje: Če je seznam vsebuje prazen, naredi dataframe z vsemi celicami, drugače filtrira samo celice v seznamu. 
    output_header_list: če je True, naredi v outputu tudi headr, drugače samo vrednosti
    """

    
    stevilo = 2 + n*2

    if  ((n < 1) | (n > 6)):
        return print("Stevilo serverjev ni ustrezno!")
        pass
    else:
        if type(atoll_txt_export_file_path) == list:
            if atoll_txt_export_file_path[1].find("timestamp") >= 0:
                uur = atoll_txt_export_file_path[11:]
                df_header = atoll_txt_export_file_path[0:11]
            else:
                uur = atoll_txt_export_file_path
                df_header = ["MANJKA\n" for i in range(9)]
                df_header.append("\n")
                df_header.append("\n")

        else:
            with open(atoll_txt_export_file_path) as input_file:
                check = [next(input_file) for _ in range(5)]
            if check[0].find('type') >= 0:
                with open(atoll_txt_export_file_path,"r") as uu:
                    uur = uu.readlines()
                    df_header = uur[0:11]
                    uur = uur[11:]
                    uu.close()  
            else:
                df_header = ["MANJKA\n" for i in range(9)]
                df_header.append("\n")
                df_header.append("\n")
                with open(atoll_txt_export_file_path, "r") as uu:
                    uur = uu.readlines()
                    uu.close()
                        
                        


        if len(vsebuje) > 0:
            uur1 = []
            reg = "|".join(vsebuje)
            for i in uur:
                if re.search(reg, i):
                    uur1.append(i)
                else:
                    pass
        else:
            uur1 = uur
        del uur

        df_ostalo = pl.read_csv(io.StringIO("".join(uur1)), has_header = False)
                # preštej ločila v vrstici, če je uprabljeno \t ga spremeni v podpičje

            
        df_ostalo = df_ostalo.with_columns(pl.col('column_1').str.replace("\n",""))
        body_dl = df_ostalo.select(pl.col("column_1").str.split(";").list.to_struct(n_field_strategy="max_width")).unnest("column_1")
        if body_dl.shape[1] == 1:
            body_dl = df_ostalo.select(pl.col("column_1").str.split("\t").list.to_struct(n_field_strategy="max_width")).unnest("column_1")
        else:
            pass
        ti3 = time.time()
        body_dl = body_dl[[i for i in body_dl.columns[0:stevilo]]]
        body_dl.columns = [str(i) for i in list(range(0,stevilo))]
        ssez = []
        for j in body_dl.columns:
            if ((int(j) > 2) & (int(j)%2!= 0)):
                ssez.append(j)
        body_dl = body_dl.with_columns(pl.all().replace({"":None}))
        body_dl = body_dl.with_columns(pl.col(ssez).cast(pl.Float64))
        body_dl = body_dl.with_columns(pl.col(['0','1']).cast(pl.Int64))
        if len(gabariti) == 4:
            body_dl = body_dl.filter((pl.col("0") >= gabariti[0]) & (pl.col("0") < gabariti[1]) & (pl.col("1") >= gabariti[2]) & (pl.col("1") < gabariti[3]))
        else:
            pass
        t1 = time.time()
        # mapper = {funkcije_at.np.nan:funkcije_at.np.nan}
        # tzz.select(pl.all().replace(mapper))
        if output_header_list == True:
            return body_dl, df_header
        else:
            return body_dl

            
            
            
def beri_atoll_txt_export_1_n_server_pl_lazy(atoll_txt_export_file_path,  n=6, vsebuje = [], output_header_list = False):
    """
    Funkcija vrne vsebino exporta in/ali  podatke v glavi
    input: če je '', je input atoll.txt export, če je input 'seznam', damo seznam (1 vrstica je 1 bin, podatki na bin ločeni s podpičjem)
    n: Stevilo serverjev. Max = 6, Min = 1
    vsebuje: Če je seznam vsebuje prazen, naredi dataframe z vsemi celicami, drugače filtrira samo celice v seznamu. 
    output_header_list: če je True, naredi v outputu tudi headr, drugače samo vrednosti
    """

    
    stevilo = 2 + n*2

    if  ((n < 1) | (n > 6)):
        return print("Stevilo serverjev ni ustrezno!")
        # pass
    else:
        if type(atoll_txt_export_file_path) == str:
            with open(atoll_txt_export_file_path,"r") as uu:
                uur = uu.readlines()
                uu.close()
        elif type(atoll_txt_export_file_path) == list:
            if atoll_txt_export_file_path[1].find("timestamp") >= 0:
                uur = atoll_txt_export_file_path
            else:
                uur = ["MANJKA\n" for i in range(9)]
                uur.append("\n")
                uur.append("\n")
                for i in atoll_txt_export_file_path:
                    uur.append(i)    
        else:
            pass # return ("Napačen vhodni podatek!")

        if len(vsebuje) > 0:
            uur1 = uur[0:11]
            reg = "|".join(vsebuje)
            for i in uur[11:]:
                if re.search(reg, i):
                    uur1.append(i)
                else:
                    pass
        else:
            uur1 = uur
        del uur

        df_header = uur1[0:9]
        
        uur1[10] = '0;1;2;3;4;5;6;7;8;9;10;11;12;13\n'
        body_dl = pl.scan_csv(io.StringIO("".join(uur1[10:])), has_header = True, separator = ';')
        # body_dl = (
            # pl.scan_csv(io.StringIO("".join(uur1[10:])), has_header = True)
            # .with_columns(pl.col('0;1;2;3;4;5;6;7;8;9;10;11;12;13\n').str.replace("\n",""))
            # .select(pl.col("column_1").str.split(";").list.to_struct(n_field_strategy="max_width")).unnest("column_1")
        # )

        # mapper = {funkcije_at.np.nan:funkcije_at.np.nan}
        # tzz.select(pl.all().replace(mapper))
        if output_header_list == True:
            return body_dl, df_header
        else:
            return body_dl
         
            
def beri_atoll_txt_export_1_n_server1(atoll_txt_export_file_path, n, vsebuje = [], header_list = False):
    """
    Funkcija vrne podatke v glavi Atoll .txt exporta in vsebino v dveh filejih
    n: Stevilo serverjev. Max = 6, Min = 1
    Če je seznam prazen, naredi dataframe z vsemi celicami
    """
    stevilo = 2 + n*2

    if  ((n < 1) | (n > 6)):
        return print("Stevilo serverjev ni ustrezno!")
        pass
    else:
        ti0 = time.time()
        file_open  = open(atoll_txt_export_file_path, 'r')
        file_read = file_open.readlines()
        file_open.close()
        file_header = file_read[0:11]
        file_ostalo = file_read[11:]
        # preštej ločila v vrstici, če je uprabljeno \t ga spremeni v podpičje
        if len(vsebuje) > 0:
            file_ostalo1 = []
            for i in vsebuje:
                for j in file_ostalo:
                    if j.find(i) >= 0:
                        file_ostalo1.append(j)
        else:
            file_ostalo1 = file_ostalo
        ti1 = time.time()
        # print("Čas file_open = {}".format(ti1-ti0))
        file_podpicje = []
        for i in file_ostalo1:
            file_podpicje.append(i.replace("\t",";").strip("\n"))
        # Preštej podpicja v vrsticah. Zanima nas n serverjev
        ti2 = time.time()
        # print("Čas file_podpicje = {}".format(ti2-ti1))
        file_podp = []
        for i in file_podpicje:
            file_podp.append(i + ((stevilo - 1) - i.count(";"))*";")
        ti3 = time.time()
        # print("Čas file_podp = {}".format(ti3-ti2))
        dd = {}

        # 1
        for j in list(range(stevilo)):
            tn = time.time()
            dd[j] = [i.split(";")[j] for i in file_podp]
        
        # # 2           Dela zelo počasi!
        # threads = []
        # for j in list(range(stevilo)):
            # tn = time.time()
            # x = threading.Thread(target = splitaj_seznam, args=(file_podp, j, dd))
            # threads.append(x)
        # for i in threads:
            # i.start()
        # for j in threads:
            # j.join()

            # tn1 = time.time()
            # print("Čas splita {} = {}".format(j, tn1 - tn))

        # 3
        
        
        
        ti4 = time.time()
        # print("Čas pd.serie = {}".format(ti4-ti3))
        tzz = funkcije_at.pd.DataFrame(dd)
        tzz = tzz[list(range(tzz.shape[1]))]
        ti5 = time.time()
        # print("Čas dataframe = {}".format(ti5-ti4))
        tzz.replace("",funkcije_at.np.nan, inplace = True)
        ti6 = time.time()
        # print("Čas dataframe replace = {}".format(ti6-ti5))
        if header_list == True:
            return tzz, file_header
        else:
            return tzz
        
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
    t = funkcije_at.pd.DataFrame()
    for j in list(range(14)):
        s = [i.split(";")[j] for i in file_podp]
        se = funkcije_at.pd.Series(s)
        t[j] = se.values
        t.replace("",funkcije_at.np.nan)
    return t.replace("",funkcije_at.np.nan)

def second_best_cel_pri_best_server():
    """
    Iz atoll ascii filetov dobimo second best serverje po želenih celicah. Pogoj je, da so celice že v teh exportih. To je star način (v opuščanju)
    """
    celice_df = celice_na_dan()
    teh = celice_df[1].drop_duplicates().tolist()
    for i in teh:
        cel = celice_df[0][celice_df[1] == i].tolist()
        if i.find("GSM") >= 0:
            tresh = -102
        else:
            tresh = -125
        for j in os.listdir(folder_pokrivanja):
            if i == j.strip("_1_w.txt"):
                print(j)
                t1 = time.time()
                # teh_df = beri_atoll_txt_export_1_dva_server(folder_pokrivanja + j, cel)
                teh_df = beri_atoll_txt_export_1_n_server(folder_pokrivanja + j, n=2, vsebuje = [], header_list = False)
                print(teh_df[[0,1,2,3]].dropna())
                print(teh_df[[0,1,4,5]].dropna())
                t2 = time.time()
                print(teh_df)
                print("Čas = {}".format(t2-t1))
                # teh_df = teh_df[1]
                for k in cel:
                    cel_df = teh_df[teh_df[2] == k]
                    cel_df1 = teh_df[teh_df[4] == k]
                    print(cel_df)
                    cel_df_2 = cel_df[4].dropna().drop_duplicates().tolist()
                    cel_df_2a = cel_df1[2].dropna().drop_duplicates().tolist()
                    print(cel_df_2)
                    cel_df_2.append(k)
                    for l in cel_df_2a:
                        cel_df_2.append(l)
                    cel_df_2 = list(set(cel_df_2))
                    print(cel_df_2)
                    string = ""
                    for l in cel_df_2:
                        string = string +  "([TX_ID] = {})|".format(l)
                    string = "(" + string[0:len(string)-1] +  ")"
                    print(string)
                    celice_df.loc[celice_df[0] == k, 'filter'] = string
    return celice_df.to_csv("D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\Celice_na_dan\\celice_na_dan_filter.txt", header = None, index = False, sep = ";")

def omejitev_best_server():

    celice_df = celice_na_dan()
    teh = celice_df[1].drop_duplicates().tolist()

    niz = ""
    for i in teh:
        cel = celice_df[0][celice_df[1] == i].tolist()
        pari = celice_n_razdalja(cel, i.replace("_"," "), n=10)
        for k in pari[0].drop_duplicates().tolist():
            cel_df_2 = pari[1][pari[0] == k].tolist()
            if len(cel_df_2) > 0:
                string = ""
                for l in cel_df_2:
                    string = string +  "([TX_ID] = {})|".format(l)
                if string[-1] == '|':   
                    string = string[0:-1:]
                string = k + ";" + i + ";(" + string + ")"
                niz = niz + string + "\n"
            else:
                pass
    with open("D:\\Atoll_projects_planer01\\Avtomatika\\Eksport\\Celice_na_dan\\celice_na_dan_filter.txt", "w") as dd:
        dd.write(niz)

    return 0

def celice_n_razdalja(seznam_celic, tehnologija, n):
    """
    Funkcija vrača celice iste tehnologije za oddaljenost najbližjih n baznih postaj
    n = število lokacij v range-u
    """
    data = funkcije_at.pd.read_sql(sql_denali_3794.celice_pwas, sql_denali_3794.conn_denali)
    data.loc[data['Ime'].str.contains('NR 2600'), 'Ime'] = 'NR 2600'
    data = data.dropna(subset = ['ImeBSC','celica'])
    # res = [x for x in data['ImeBSC'].drop_duplicates().tolist() if re.search(pattern, x)]
    # data = data[~data['ImeBSC'].isin(res)]
    data = data[((data['Delujoca'] == True) & (data['Type'] == 'Outdoor') & (data['Ime'] == tehnologija))]
    data = data[['ImeBSC', 'Delujoca', 'Type', 'celica','azimut', 'beamwidth','ZSirina','ZVisina','Ime']].reset_index(drop = True)
    data_loks = data[['ImeBSC', 'celica']].rename(columns = {'ImeBSC':'A'})
    data = data[['ImeBSC','ZSirina','ZVisina']].drop_duplicates().reset_index(drop = True)
    data['ZSirina']  =data['ZSirina'].astype(float)
    data['ZVisina']  =data['ZVisina'].astype(float)
    skupaj = funkcije_at.pd.merge(data[['ImeBSC','ZSirina','ZVisina']], data[['ImeBSC','ZSirina','ZVisina']], how = 'cross')
    skupaj['razlika_x'] = funkcije_at.np.power(abs(skupaj['ZSirina_x'] - skupaj['ZSirina_y']), 2)
    skupaj['razlika_y'] = funkcije_at.np.power(abs(skupaj['ZVisina_x'] - skupaj['ZVisina_y']), 2)
    skupaj['razdalja'] = funkcije_at.np.sqrt(skupaj['razlika_x'] + skupaj['razlika_y']).round(1)
    skupaj['vrstni_red'] = skupaj.sort_values(by = ['ImeBSC_x','razdalja'], ascending = [True, True]).groupby(['ImeBSC_x']).cumcount()
    skupaj = skupaj[skupaj['vrstni_red'] <= n]
    skupaj1 = skupaj[['ImeBSC_x','ImeBSC_y']].merge(data_loks, how = 'inner', left_on = 'ImeBSC_x', right_on = 'A').reset_index(drop = True)
    skupaj1.drop(columns = ['A'], inplace = True)
    skupaj1.rename(columns = {'celica':'celica_x'}, inplace = True)
    skupaj2 = skupaj1.merge(data_loks, how = 'inner', left_on = 'ImeBSC_y', right_on = 'A')
    skupaj2.drop(columns = ['A'], inplace = True)
    skupaj2.rename(columns = {'celica':'celica_y'}, inplace = True)

    datag = funkcije_at.pd.read_sql(sql_atoll_3794.gtransmitters_atoll, sql_atoll_3794.conn_atoll)
    datag = datag[['SITE_NAME','TX_ID']][datag['ACTIVE']==1]
    datax = funkcije_at.pd.read_sql(sql_atoll_3794.xgtransmitters_atoll, sql_atoll_3794.conn_atoll)
    datax = datax[['SITE_NAME','TX_ID']][datax['ACTIVE']==1]
    dataa = funkcije_at.pd.concat([datag,datax]).drop_duplicates()

    skupaj2 = skupaj2[((skupaj2['celica_x'].isin(seznam_celic)) & (skupaj2['celica_y'].isin(dataa['TX_ID'].tolist())))]
    return skupaj2[['celica_x','celica_y']].rename(columns = {'celica_x':0, 'celica_y':1})

    
def povrsina(atoll_txt_export_file_path, n=1, kaj = 'celica', treshold = -125):
    """
    Funkcija vrne površino celice ozirma site-a v m2. 
    atoll_txt_export_file_path: polna pot do ascii exporta
    n: število servejev. Če je n=1 pomeni best server
    kaj: 'celica' ali 'site'. default: 'celica'
    """
    df = beri_atoll_txt_export_1_n_server1(atoll_txt_export_file_path, n = n, vsebuje = [], header_list = True)
    print("n = {}".format(n))
    print(df)
    resolucija = int(df[1][2].strip("\n").split("\t")[1])
    nlist = [i for i in range(4,n*2+2,2)]
    df1 = df[0][[0,1,2,3]]
    if n > 1:
        for i in nlist:
            df1 = funkcije_at.pd.concat([df1, df[0][[0,1,i,i+1]].rename(columns = {i:2,(i+1):3})])
            df1.dropna(inplace = True)
    df1[3] = df1[3].astype(float)
    df1 = df1[df1[3]>= treshold]
    print(df1)
    df1 = df1[[0,1,2]].drop_duplicates()
    if kaj == 'site':
        df1_dict = {}
        for i in df1[2].tolist():
            df1_dict[i] = re.split(r"\d+",i)[0]
        # df1['site'] = df1[2].str.split(r"\d+", expand = True)[0]
        df1['site'] = df1[2].map(df1_dict)
        df1 = df1[[0,1,'site']].drop_duplicates()
        df1_merge = df1.groupby(['site']).agg({1:'count'}).rename(columns = {1:'stevilo', 'site':'lik'}).reset_index()
    else:
        df1_merge = df1.groupby([2]).agg({1:'count'}).rename(columns = {1:'stevilo',2:'lik'}).reset_index()
    df1_merge['povrsina'] = df1_merge['stevilo']*(resolucija**2)
    return df1_merge
    
# import time
# t0 = time.time()
# a = povrsina(file, n=6, kaj = 'site', treshold = -125)    
# t1 = time.time()
# print("Čas = {}".format(t1-t0))
    
def sinr_na_bin(atoll_txt_export_file_path, n,  BW = 10000000, vsebuje = [], header_list = False, throughput = False):
    """
    SINR (C/(I+N))
    """
    t = beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path, n=6, vsebuje = [], header_list = False)
    # t[['arfcn_dl','arfcn_ul','BW','band','teh','cell_id_pripona', 'power']] = t[[2]].apply(lambda x: funkcije_at.arfcn(x[2]),axis=1, result_type = 'expand')
    # t.drop(columns = ['arfcn_dl','arfcn_ul','band','teh','cell_id_pripona', 'power'], inplace = True)
    TS = termicni_sum(BW)
    t['TS'] = boltzmanova_konstanta*T*BW
    t['NF'] = 8
    t[5].fillna(-150, inplace = True)
    t[7].fillna(-150, inplace = True)
    t[9].fillna(-150, inplace = True)
    t[11].fillna(-150, inplace = True)
    t[13].fillna(-150, inplace = True)
    t[[3,5,7,9,11,13]] = t[[3,5,7,9,11,13]].astype(float)
    t[14] = t[3].apply(funkcije_at.dbm_v_w)
    t[15] = t[5].apply(funkcije_at.dbm_v_w)
    t[16] = t[7].apply(funkcije_at.dbm_v_w)
    t[17] = t[9].apply(funkcije_at.dbm_v_w)
    t[18] = t[11].apply(funkcije_at.dbm_v_w)
    t[19] = t[13].apply(funkcije_at.dbm_v_w)
    t.drop(columns = [3,5,7,9,11,13], inplace = True)
    t.loc[t[14] < (1/10**17), 14]  = 0
    t.loc[t[15] < (1/10**17), 15]  = 0
    t.loc[t[16] < (1/10**17), 16]  = 0
    t.loc[t[17] < (1/10**17), 17]  = 0
    t.loc[t[18] < (1/10**17), 18]  = 0
    t.loc[t[19] < (1/10**17), 19]  = 0

    t[20] = t[14]/(t[15]  + t[16] + t[17] + t[18] + t[19]+t['TS'])
    t[21] = t[15]/(t[14]  + t[16] + t[17] + t[18] + t[19]+t['TS'])
    t[22] = t[16]/(t[14]  + t[15] + t[17] + t[18] + t[19]+t['TS'])
    t[23] = t[17]/(t[14]  + t[15] + t[16] + t[18] + t[19] +t['TS'])
    t[24] = t[18]/(t[14] + t[15] + t[16] + t[17] + t[19] +t['TS'])
    t[25] = t[19]/(t[14]  + t[15] + t[16] + t[17] + t[18] +t['TS'])

    t[20] = t[20].apply(funkcije_at.w_v_dbm) - t['NF']
    t[21] = t[21].apply(funkcije_at.w_v_dbm) - t['NF']
    t[22] = t[22].apply(funkcije_at.w_v_dbm) - t['NF']
    t[23] = t[23].apply(funkcije_at.w_v_dbm) - t['NF']
    t[24] = t[24].apply(funkcije_at.w_v_dbm) - t['NF']
    t[25] = t[25].apply(funkcije_at.w_v_dbm) - t['NF']

    t.rename(columns = dict(zip([20,21,22,23,24,25],[3,5,7,9,11,13])), inplace = True)
    t = t[[0,1,2,3,4,5,6,7,8,9,10,11,12,13]]

    if throughput == True:
        t[14] = t[[3]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[3]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t[15] = t[[5]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[5]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t[16] = t[[7]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[7]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t[17] = t[[9]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[9]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t[18] = t[[11]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[11]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t[19] = t[[13]].apply(lambda x: vrednost_v_seznamu(list(slovar_spectral_efficiency.keys()), x[13]), axis = 1).map(slovar_spectral_efficiency)*BW/1000000
        t.loc[t[3] == -np.inf, 14] = 0
        t.loc[t[5] == -np.inf, 15] = 0
        t.loc[t[7] == -np.inf, 16] = 0
        t.loc[t[9] == -np.inf, 17] = 0
        t.loc[t[11] == -np.inf,18] = 0
        t.loc[t[13] == -np.inf,19] = 0
        t.drop(columns = [3,5,7,9,11,13], inplace = True)
        t.rename(columns = dict(zip([14,15,16,17,18,19],[3,5,7,9,11,13])), inplace = True)
        t = t[[0,1,2,3,4,5,6,7,8,9,10,11,12,13]]
    return t

def sinr_to_spectral_efficiency(vrednost_sinr, teh = 'LTE'):
    """
    vir: atoll
    """
    if teh == 'LTE':
        sinr_to_bearer = r"G:\Pokrivanja\Stevci\Parametri_throughput_calculation\\C_over_I_mapping_atoll.txt"
        bearer_coveri = r"G:\Pokrivanja\Stevci\Parametri_throughput_calculation\\bearer_mapping_atoll.txt"

        s1 = pd.read_csv(sinr_to_bearer, sep = "\t")
        s1['C/(I+N)dB'] = s1['C/(I+N)dB'].str.replace(",",".").astype(float)
        s2 = pd.read_csv(bearer_coveri, sep = "\t", index_col = False)
        s2['Bearer_Efficiency_(bits/symbol)'] = s2['Bearer_Efficiency_(bits/symbol)'].str.replace(",",".").astype(float)
        s3 = s2.merge(s1, how = 'inner', left_on = 'Radio_Bearer_Index', right_on = 'Bearer')
        slovar_spectral_efficiency = dict(zip(s3['C/(I+N)dB'], s3['Bearer_Efficiency_(bits/symbol)']))
        return slovar_spectral_efficiency
        
def vrednost_v_seznamu(seznam, vrednost):
    if vrednost <= min(seznam):
        a = min(seznam)
    elif vrednost >= max(seznam):
        a = max(seznam)
    else:
        i = 0
        while i <= len(seznam):
            if seznam[i] > vrednost:
                a = seznam[i-1]
                break
            i = i+1
    return a

slovar_spectral_efficiency = {-4.0: 0.2344,
 -2.8: 0.377,
 -1.2: 0.6016,
 0.8: 0.877,
 2.4: 1.1758,
 3.2: 1.4766,
 4.8: 1.6953,
 5.6: 1.9141,
 6.8: 2.1602,
 7.6: 2.4063,
 9.4: 2.5703,
 10.4: 2.7305,
 11.8: 3.0293,
 13.8: 3.3223,
 15.4: 3.6094,
 16.6: 3.9023,
 18.0: 4.2129,
 18.8: 4.5234,
 20.2: 4.8164,
 21.8: 5.1152,
 23.6: 5.332,
 24.6: 5.5547,
 25.6: 5.8906,
 27.2: 6.2266,
 29.0: 6.5703,
 29.8: 6.9141,
 31.8: 7.1602,
 33.8: 7.4063}    

def naredi_dict_za_thresholde(seznam, crit = {-85:0, -100:1, -125:2}):
    d = {}
    for i in seznam:
        for j in list(crit.keys()):
            razlika = i-j
            if razlika >= 0:
                d[i] = crit[j]
                break
            else:
                pass         
    return d
        
    
def uredi_atoll_shp_za_112(mapa, datoteka, slovar_ci):
    data = gpd.read_file(mapa + datoteka)
    data1 = data.to_crs(3912)
    data1 = data1.explode()
    mm = naredi_dict_za_thresholde(data1['THRESHOLD'].tolist())
    data1['value'] = data1['THRESHOLD'].map(mm)
    data1 = data1[['value','geometry']]
    data1 = data1.reset_index(drop = True)
    if datoteka.split(".")[0] in list(slovar_ci.keys()):
        ime = slovar_ci[datoteka.split(".")[0]] + ".SHP"
    else:   
        ime = datoteka.split(".")[0] + "___.SHP"
    return data1.to_file(mapa + ime)

def valid_from_to():
    leto = datetime.datetime.now().year
    mesec = str(datetime.datetime.now().month)
    dan = str(datetime.datetime.now().day)
    ura = str(datetime.datetime.now().hour)
    minuta = str(datetime.datetime.now().minute)
    sekunda = str(datetime.datetime.now().second)
    if len(mesec) < 2:
        mesec = '0' + mesec
    if len(dan) < 2:
        dan = '0' + dan
    if len(ura) < 2:
        ura = '0' + ura
    if len(minuta) < 2:
        minuta = '0' + minuta
    if len(sekunda) < 2:
        sekunda = '0' + sekunda
    niz = "ValidFrom={}.{}.{} {}:{}:{}\n".format(dan, mesec, str(leto), ura, minuta, sekunda)
    niz = niz + "ValidTo={}.{}.{} {}:{}:{}".format(dan, mesec, str(leto + 1), ura, minuta, sekunda)
    return niz

    
def doloci_uo_obmocje(teh = 'GSM_900', jakost = -100):
    """
    Funkcija določi Upravno območje (112 in 113 koda). 
    Vir glej: G:\Geo podatki\RECO_112_113
    Skripta deluje tako, da prešteje bine celic, ki padejo v nek UO. Izberemo tisti UO, ki ima največji best server area pokrivanje te celice znotraj nekega UO, če je slučajno njegovo pokrivanje razdelejeno med 2 ali več UOje. 
    """
    t = beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\" + teh + "_1_w.txt", n=1)
    t[0] = t[0].astype(int)
    t[1] = t[1].astype(int)
    t[3] = t[3].astype(float)
    t = t[t[3]>= jakost]
    uo = funkcije_at.pd.read_csv(r"G:\Geo podatki\RECO_112_113\\RECO_UO_25.txt", sep = ";")
    uo[0] = uo['0'] - 12.5
    uo[1] = uo['1'] - 12.5
    uo[0] = uo[0].astype(int)
    uo[1] = uo[1].astype(int)
    uo.drop(columns = ['0','1'], inplace = True)
    uo = uo.merge(t[[0,1,2]], how = 'inner', left_on = [0,1], right_on = [0,1])
    stev = uo[[2,'UO_ID',0]].groupby([2, 'UO_ID']).agg({0:'count'}).reset_index()
    stev.rename(columns = {0:'Stevilo'}, inplace = True)
    stev_ = uo[[2,'UO_ID']].groupby([2]).agg({'UO_ID':'count'}).reset_index()
    stev_.rename(columns = {'UO_ID':'Skupaj'}, inplace = True)
    stev = stev.merge(stev_, how = 'inner', left_on = 2, right_on = 2)
    stev['odst'] = stev['Stevilo']/stev['Skupaj']*100
    # ziher = stev[stev['odst']==100]
    # ost = stev[stev['odst']<100]
    # ziher_ost = ost[ost['odst'] >= 60]
    # ost_ = ost[~ost[2].isin(ziher_ost[2].tolist())]
    stev['vrstni_red'] = stev.sort_values(by = [2,'odst'], ascending = [False, False]).groupby([2]).cumcount()
    stev = stev[stev['vrstni_red'] == 0]
    return dict(zip(stev[2].tolist(), stev['UO_ID'].tolist()))

def indexed_ascii(koordinate = False, indexed = False):
    """
    Indexiran ascii. Trenutno samo za 25m resolucijo. Vir za index je grid 25m cele Slovenije iz fajla r"G:\Geo podatki\RECO_112_113\\RECO_UO_25.txt"
    koordinate: Če je True so v exportanem fajlu zraven tudi koordinate
    indexed: Če je True, je v exportanem fajlu zraven tudi index
    """
    uo = pl.read_csv(r"G:\Geo podatki\RECO_112_113\\RECO_UO_25.txt", separator = ";")
    uo = uo.with_columns(pl.col("0") - 12.5)
    uo = uo.with_columns(pl.col("1") - 12.5)
    uo = uo.with_columns(pl.col('0').cast(pl.Int64))
    uo = uo.with_columns(pl.col('1').cast(pl.Int64))
    for i in os.listdir(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\"):
        if i.find(".txt") > 0:
            a = beri_atoll_txt_export_1_n_server_pl(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\" + i,  n=6, vsebuje = [], output_header_list = False, gabariti = [])
            uoa = uo.join(a, on = ['0','1'], how = 'left', suffix = '_right', coalesce = True)
            if indexed == True:
                uoa = uoa.with_columns(Index=np.array([i for i in range(uoa.shape[0])]))
            else:
                pass
            if koordinate == True:
                uoa = uoa.drop( ['UO_ID'])
            else:
                uoa = uoa.drop( ['0', '1', 'UO_ID'])
            uoa.write_csv(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\Indexed\\" + i, include_header=False)
            del  a, uoa
            print(i)
    return 0

def naredi_nsa_700():
    """
    
    """
    tt700 = beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\NR_700_1_w.txt", n=6, vsebuje = [], header_list = False)
    tt700 = tt700.astype({i:'float' for i in list(range(3,tt700.shape[1]+1,2))})
    tt1800 = beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\LTE_1800_1_w.txt", n=6, vsebuje = [], header_list = False)
    celice = tt700[2].drop_duplicates().tolist()
    celice18 = [i.replace('07SS','18') for i in celice]
    slovv = dict(zip(celice18,celice))
    ssez = []
    for i in range(2,tt1800.shape[1],2):
        temp = tt1800[[0,1,i,i+1]].dropna()
        temp = temp[temp[i].isin(celice18)]
        temp.columns = [0,1,2,3,]
        ssez.append(temp)
    tt18 = funkcije_at.pd.concat(ssez)
    print(tt18)
    tt18 = tt18[[0,1,2,3]].reset_index(drop = True)
    tt18['vrstni_red'] = tt18.sort_values(by = [0,1,3], ascending = [False, False, False]).groupby([0,1]).cumcount() + 1
    tt18 = tt18[tt18['vrstni_red'] == 1]
    tt18.columns = [0,1,'2_y','3_y','vr_red']
    tt_skupaj = funkcije_at.pd.DataFrame()
    for i in range(2,tt700.shape[1],2):
        temp = tt700[[0,1,i,i+1]]
        temp = temp.merge(tt18, how = 'inner', left_on = [0,1], right_on = [0,1])
        temp = temp[temp[i+1] > -110]
        temp = temp[[0,1,i, i+1]]
        st = []
        for j in temp.columns.tolist():
            if str(j).find('_') >= 0:
                st.append(int(j.split('_')[0]))
            else:
                st.append(j)
        temp.columns = st
        if tt_skupaj.shape[0] == 0:
            tt_skupaj = temp
        else:
            tt_skupaj = tt_skupaj.merge(temp, how = 'left', left_on = [0,1], right_on = [0,1])
    print(tt_skupaj)
    with open (r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\NR_700_1_w.txt", 'w') as aa:
        aa.write('type' + 'NR\n')
        aa.write('timestamp'+ '\n')
        aa.write('resolution\t'  + '25\n')
        aa.write('xmin\t' + str(tt_skupaj[0].astype(int).min())+ '\n')
        aa.write('xmax\t' + str(tt_skupaj[0].astype(int).max() +25)+ '\n')
        aa.write('ymin\t' + str(tt_skupaj[1].astype(int).min())+ '\n')
        aa.write('ymax\t' + str(tt_skupaj[1].astype(int).max() +25)+ '\n')
        aa.write('x_num_pixels\t' + str(int((tt_skupaj[0].astype(int).max() - tt_skupaj[0].astype(int).min()+ 25)/25)) + '\n')
        aa.write('y_num_pixels\t' + str(int((tt_skupaj[1].astype(int).max() - tt_skupaj[1].astype(int).min() + 25)/25)) + '\n')
        aa.write('\n\n')
        aa.close()
    tt_skupaj.to_csv(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\NR_700_1_w.txt", mode = 'a', sep = ";", index = False, header = None)
    print("Posneto v fajl")
    with open(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\NR_700_1_w.txt", 'r') as dd:
        ddr = dd.readlines()
        dd.close()
    ddr1 = []
    for i in ddr:
        ddr1.append(i.rstrip("\n").rstrip(";") + "\n")
    with open (r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\NR_700_1_w.txt", 'w') as aa:
        aa.write("".join(ddr1))
    del ddr1, ddr
    print("Konec!")
    return 0
 

def naredi_iot(teh):
    cel = enm.nbiot_celice()
    cel['cell'] = cel['NbIotCell'].str.replace("IOT","")
    if teh == 'LTE_800':
        fajl = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\LTE_800_1_w.txt"
    elif teh == 'LTE_1800':
        fajl = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\LTE_1800_1_w.txt"
    elif teh == 'LTE_900':
        fajl = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\LTE_900_1_w.txt"
    else:
        return 0
    cov = beri_atoll_txt_export_1_n_server(atoll_txt_export_file_path = fajl, n=6, vsebuje = [], header_list = False)
    vse_cel = cov[2].drop_duplicates().tolist()
    for i in list(range(4,cov.shape[1]+1,2)):
        celt = cov[i].drop_duplicates().tolist()
        for j in celt:
            vse_cel.append(j)
        vse_cel = list(set(vse_cel))
    odpade = funkcije_at.razlika_seznamov(vse_cel,cel['cell'].tolist(),'komplement1')
    if len(odpade) > 0:
        t0 = time.time()
        with open(mapa + file_skupno_pokrivanje, "r") as mm:
            mmr = mm.readlines()
            m_glava = mmr[0:11]
            mmr = mmr[11:]
            mm.close()
        pattern_brisi = "|".join([i + ";-[0-9]*.?[0-9]*;{0,1}" for i in celice_brisi])
        pattern_brisi_prazna_vrstica = "[0-9]{5,7};[0-9]{4,6};+\\n"
        # mmr_brisanje = [re.sub(pattern_brisi,"",x) for x in mmr]
        # mmr_brisanje1 = [x for x in mmr_brisanje if not re.search(pattern_brisi_prazna_vrstica,x)]
        mmr_brisanje = [re.sub(";\\n","\\n",x) for x in [x for x in [re.sub(pattern_brisi,"",x) for x in mmr] if not re.search(pattern_brisi_prazna_vrstica,x)]]
        t1 = time.time()
        # logging.info("Brisanje {} je {}s".format(file_skupno_pokrivanje,(t1-t0)))
        tt1 = time.time()
        print("     Čas brisanja {}".format(tt1 - tt0))
    else:
        with open(mapa+ file_skupno_pokrivanje, "r") as dd:
            mmr_brisanje = dd.readlines()
            m_glava = mmr_brisanje[0:11]
            mmr_brisanje = mmr_brisanje[11:]
            dd.close()
        tt1 = time.time()
        print("     Čas brisanja {}".format(tt1 - tt0))            
    print(celice_brisi)        

# def indexed_np():
    # """
    # Output je numpy array, 
    # """
    # uo = pl.read_csv(r"G:\Geo podatki\RECO_112_113\\RECO_UO_25.txt", separator = ";")
    # uo = uo.with_columns(pl.col("0") - 12.5)
    # uo = uo.with_columns(pl.col("1") - 12.5)
    # uo = uo.with_columns(pl.col('0').cast(pl.Int64))
    # uo = uo.with_columns(pl.col('1').cast(pl.Int64))
    # # for i in os.listdir(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\"):
    # sku = []
    # for i in ['LTE_700_1_w.txt','LTE_800_1_w.txt']:
        # if i.find(".txt") > 0:
            # a = beri_atoll_txt_export_1_n_server_pl(r"G:\Pokrivanja\Arcgis\export_3794\Sestic\\" + i,  n=6, vsebuje = [], output_header_list = False, gabariti = [])
            # uoa = uo.join(a, on = ['0','1'], how = 'left', suffix = '_right', coalesce = True)
            # del a
            # # uoa = uoa.with_columns(Index=np.array([i for i in range(uoa.shape[0])]))
            # uoa = uoa.drop( ['UO_ID'])
            # minx = uoa.select(pl.min('0')).item()
            # miny = uoa.select(pl.min('1')).item()
            # maxx = uoa.select(pl.min('0')).item()
            # maxy = uoa.select(pl.min('1')).item()
            # uoa = uoa.with_columns(((pl.col('0') - minx)/25).alias('ind_x'))
            # uoa = uoa.with_columns(((pl.col('1') - miny)/25).alias('ind_y'))
            # uoa = uoa.with_columns(pl.col(['ind_x','ind_y']).cast(pl.Int64))
            # sez2_np = np.full_like(a = dict, shape = (uoa['1'].unique().shape[0], uoa['0'].unique().shape[0], 1), fill_value = {})
            # # sez1_np[sez1_np == 0] = ''
            # t0 = time.time()
            # # uoap = uoa.to_pandas()
            # for aa in uoa.iter_rows():
                # sez2_np[(aa[15], aa[14],0)] = dict(zip(aa[2:len(aa)-2:2],aa[3:len(aa)-2:2]))
            # t1 = time.time()
            # print(t1-t0)
            # sku.append(sez2_np)
    # return 0
    
    
# import time
# t0 = time.time()
# indexed_ascii()
# t1 = time.time()
# print("Čas = {}".format(t1-t0))
    
def dnevna_procedura():
    
    # Briši obstoječe shape
    if raster_crit == True:
        if len(os.listdir(odlozisce_raster)) > 0:
            for i in os.listdir(odlozisce_raster):
                os.remove(odlozisce_raster + i)
            else:
                pass
    if shp_crit == True:
        if len(os.listdir(odlozisce_shp)) > 0:
            for i in os.listdir(odlozisce_shp):
                os.remove(odlozisce_shp + i)
            else:
                pass            
    # Preveri, če je kakšna nova celica in naredi prceduro
    with open(celice, "r") as dd:
        ddr = dd.readlines()
        dd.close()
    if len(ddr) > 0:
        # celice_df = funkcije_at.pd.read_csv(celice, header  = None, sep = ";")
        # celice_df.sort_values(by = 1, inplace = True)
        # celice_df['filter'] = ""
        # teh = celice_df[1].drop_duplicates().tolist()

        # second_best_cel_pri_best_server() in export shp in raster. V shape_export_112.vbs je shp_crit. Če je ta False, se export shp ne naredi
        omejitev_best_server()
        krmili_vbs_skripto()
        print("omejitev_best_server() Zaključen")
        print("=========================================")
        subprocess.run(['cscript','C:\\Users\\planer02\\Skripte\\VBasic\\shape_export_112.vbs'],  capture_output=True,  text=True)
        
        if raster_crit == True:
            if len(os.listdir(odlozisce_raster)) > 0:
                for i in (os.listdir(odlozisce_raster)):
                    vnesi_celico_v_drugi_stolpec(odlozisce_raster, i)
        
        if shp_crit == True:
            # pass
            ci_df = ericsson_enm_tabele.cgi_vse()
            ci_df['CELLID'] = ci_df['CELLID'].astype(str)
            ci_dict = dict(zip(ci_df['CELICA'].tolist(), ci_df['CELLID'].tolist()))
            if len(os.listdir(odlozisce_shp)) > 0:
                for i in os.listdir(odlozisce_shp):
                    if i.split(".")[0] in ci_df['CELICA'].tolist():
                        if ((i.find("shp") > 0) | (i.find("SHP") > 0)):
                            uredi_atoll_shp_za_112(mapa = odlozisce_shp, datoteka = i, slovar_ci = ci_dict)
            if len(os.listdir(odlozisce_shp)) > 0:                            
                for i in os.listdir(odlozisce_shp):
                    if i.split(".")[0] in ci_df['CELICA'].tolist():
                        os.remove(odlozisce_shp + i)
            # if len(os.listdir(odlozisce_shp)) > 0:                            
                # for i in os.listdir(odlozisce_shp):
                    # if i.find(".prj") > 0:
                        # os.remove(odlozisce_shp + i) 
            if len(os.listdir(odlozisce_shp)) > 0:                            
                for i in os.listdir(odlozisce_shp):
                    if i.find(".cpg") > 0:
                        os.rename(odlozisce_shp + i, odlozisce_shp + i.split(".cpg")[0] + ".info")    
            if len(os.listdir(odlozisce_shp)) > 0:                            
                for i in os.listdir(odlozisce_shp):
                    if i.find(".info") > 0:
                        with open (odlozisce_shp + i, "w") as dd:
                            dd.write("{}".format(valid_from_to()))
                            dd.close()
    else:
        pass
    return 0

if __name__ == '__main__':
    #main()
    #second_best_cel_pri_best_server()
    dnevna_procedura()