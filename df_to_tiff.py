# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import tifffile as tiff
from PIL import Image
# from export_script_3794_reporting import glava
import re
import random

file = r"G:\Pokrivanja\Splet\\4G_5G_LTE -115 za splet.tif"
# file = r"G:\Razno\\LTE 800 Aster stat L800 5 coverage.tif"            Ne DELA!!!!! Dela samo z 1 barvo. imagecodecs za veÄ barv

# a = tiff.imread(file)
# a.shape

slovar_lte = {-125:(255, 36, 58, 165),
          -115:(255, 173, 156, 165),
          -105:(229, 171, 146, 165),
          -95:(245, 245, 54, 165),
          -85:(36, 255, 51, 165),
          -75:(100, 144, 78, 165)}      # -20:(100, 144, 78, 180)


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

def nivo(vrednost, nivoji):
    sez_dod = [ vrednost - i for i in nivoji]
    sez_min = [i for i in sez_dod if i <= 0]
    vred = sez_dod.index(max(sez_min))
    value = nivoji[vred]
    return value

def nivo1(vrednost, nivoji):
    for i in nivoji:
        while (vrednost - i) > 0:
                value = vrednost - i
    return value


def naredi_tif(file_pokrivanje, odlozisce, tip, resolution = 100, ime = '', treshold = -125):
    """
    Skritpa naredi tif file (sliko) iz podatkovnega inputa. Lahko je ascii, dataframe. Naredi samo dve barvi, vrednost numpy array-a
    so samo True in False (True = bela - brez barve, False = Ärna).
        tip = ascii,
        tip = dataframe. Äe je dataframe je pomembno, da sta v prvih dveh stoplcih koordinati X, Y.
        tip = csv

    """
    if tip == "ascii":
        with open(file_pokrivanje, "r") as fo:
            fo_read = fo.readlines()
            fo_read_str = [re.split(r"\t|;",i.strip("\n")) for i in fo_read]
            fo.close()
            gl = glava(file_pokrivanje)
            body = fo_read_str[11:len(fo_read_str)]
            body_df = pd.DataFrame(body)
            body_df[3] = body_df[3].astype(float)
            print(body_df)
            body_df = body_df[body_df[3] >= treshold]
            body_df[0] = body_df[0].str.replace(".","").astype(int)
            body_df[1] = body_df[1].str.replace(".","").astype(int)
            body_df = body_df[[0,1]].drop_duplicates().dropna()
            resolution = gl['resolution']
            xminn = gl['xmin']
            yminn = gl['ymin']
            xmaxx = gl['xmax']
            ymaxx = gl['ymax']
            ncolss = gl['x_num_pixels']
            nrowss = gl['y_num_pixels']
        name = "Podatek_"
        if ime != '':
            name = ime
        else:
            name = file.split("\\")[-1].split(".")[0]
    elif tip == "df":
        body_df = file_pokrivanje
        body_df = body_df[body_df[3] >= treshold]
        if type(body_df.columns.tolist()[0]) == str:
            print(body_df.shape)
            body_df.columns = [0,1]
        else:
            pass
        name = "Podatek_"
        body_df = body_df[[0,1]].drop_duplicates().dropna()
        xminn = min(body_df[0].astype(int))
        print(xminn)
        yminn = min(body_df[1].astype(int))
        xmaxx = max(body_df[0].astype(int))
        ymaxx = max(body_df[1].astype(int))
        ncolss = int((xmaxx - xminn)/ resolution) +1
        nrowss = int((ymaxx - yminn)/ resolution) +1
        if ime != '':
            name = ime
        else:
            name = file_pokrivanje.split("\\")[-1].split(".")[0]
    elif tip == "csv":
        body_df = pd.read_csv(file, sep = ",")
        body_df = body_df[body_df[3] >= treshold]
        if type(body_df.columns.tolist()[0]) == str:
            print(body_df.shape)
            body_df.columns = [0,1]
        else:
            pass
        body_df = body_df[[0,1]].drop_duplicates().dropna()
        if ime != '':
            name = ime
        else:
            name = file.split("\\")[-1].split(".")[0]
        # resolution = int(body_df[0][0] - body_df[1][0])
        xminn = min(body_df[0].astype(int))
        yminn = min(body_df[1].astype(int))
        xmaxx = max(body_df[0].astype(int))
        ymaxx = max(body_df[1].astype(int))
        ncolss = int((xmaxx - xminn)/ resolution) +1
        nrowss = int((ymaxx - yminn)/ resolution) +1

        # ncolls = 2478
        # nrowss = 1625
    print(resolution, xminn, yminn, xmaxx, ymaxx, ncolss, nrowss, body_df.shape)
    print(body_df)

    xminn =  int(body_df[0].min())
    yminn =  int(body_df[1].min())
    ncolss = int(abs(body_df[0].min() - body_df[0].max()) / resolution) + 1
    nrowss = int(abs(body_df[1].min() - body_df[1].max()) / resolution) + 1
    xmaxx = xminn + (ncolss - 1)*resolution
    ymaxx = yminn + (nrowss - 1)*resolution
    print(resolution, xminn, yminn, xmaxx, ymaxx, ncolss, nrowss, body_df.shape)


    body_df["x_ind"] = ((body_df[0].astype(int) - int(xminn))/resolution).astype(int)
    body_df["y_ind"] = ((int(yminn) - body_df[1].astype(int))/resolution).astype(int)
    body_df.sort_values(by = ['y_ind', 'x_ind'], inplace = True)
    body_df.reset_index(inplace  =True)

    sez1 = []
    sez2 = []
    for i in range(nrowss):
        for j in range(ncolss):
            sez2.append(255)
        sez1.append(sez2)
        sez2 = []
    sez1_np = np.array(sez1, dtype = np.uint8)

    # print(body_df)

    for i in body_df.index.tolist():
        y = body_df.loc[i, 'y_ind']
        x = body_df.loc[i, 'x_ind']
        sez1_np[y][x] = 0
    print(sez1_np)

    im = Image.fromarray(sez1_np)

    with open(odlozisce + "\\" + name + ".tfw", "w") as dd:
        dd.write("{}\n".format(resolution))
        dd.write("0\n")
        dd.write("0\n")
        dd.write("-{}\n".format(resolution))
        dd.write(str(float(body_df[0].min())) + "\n")
        dd.write(str(float(body_df[1].max())))
        dd.close()

    return body_df, sez1_np  , im.save(odlozisce + "\\" + name + ".tif", "TIFF"), x, y

# levo zoraj:  EPSG 3794: 374158.24262494675,195909.49944601022         374200,195900
# levo spodaj: EPSG 3794: 370721.4658977066,30598.456832747906          370700,30600
# desno zgoraj: EPSG 3794: 624664.5709171672,195884.838174114           624700,195900
# desno spodaj: EPSG 3794: 628069.1811375208,30573.745820118114         628100,30600
# ADDPARAM="-c 100 --najdisi -x 374550 -X 625050 -y 30050 -Y 194050"

# ADDPARAM="-c 100 --najdisi -x 374550 -X 625050 -y 30050 -Y 194050"
# mgisbase.geosoc.border=Slovenija=xMin,yMin 375208.06,30851.3 : xMax,yMax 624068.86,193269.23
# 1485958.0805046076420695
# 5685250.9888262674212456
# 1851906.9351446076761931      Star sistemm!!!!!!!!!!!!!!!!!
# 5924264.4898662678897381
# LL=13.3485878Â°,45.4033767Â°
# UR=16.6359636Â°,46.8907752Â°


# Uporabimo naredi_tif1("G:\\Pokrivanja\\LTE_1_w_RES_50.txt", "G:\\Pokrivanja\\", tip = 'ascii', resolution = 100, ime = 'LTE_1_w_RES_50_yoffset_150.tif', treshold = -115, x_offset = 0, y_offset = 150)
# v Qgisu pa: Raster/Reproject/ Konverzija iz EPSG:3794 v EPSG:3857
# v polju Georeferenced extents of output file to be created:  1485958.0805,1851406.9351,5685250.9888,5924564.4899 [EPSG:3857]

# meje_okvirja = [[370700,30600],[624700,195900]],

def barva(seznam = [], prazno = ''):
    p = {}
    for i in seznam:
        p[i] = (random.randrange(1,254,1),random.randrange(1,254,1),random.randrange(1,254,1),180)
    p[prazno] = (255, 255, 255, 0)
    return p

def naredi_tif1(file_pokrivanje, odlozisce, tip, resolution = 100, ime = '', treshold = -125, x_offset = 0, y_offset = 0, slovar_barv = {}, slovar_celica = {}):      # 373900, 193300      , [374200,195900],[628100,30600]
    """
    Skritpa naredi tif file (sliko) iz podatkovnega inputa. Lahko je ascii, dataframe. Naredi samo dve barvi, vrednost numpy array-a
    so samo True in False (True = bela - brez barve, False = Ärna).
        tip = ascii,
        tip = dataframe. Äe je dataframe je pomembno, da sta v prvih dveh stoplcih koordinati X, Y.
        tip = csv
    Naredi se Å¡e tfw.
    slovar_barv: -> ta se dela glede na stolpec jakost signala
    maping nivo: barva npr:
    slovar_lte = {-125:(255, 255, 255, 0),
              -115:(255, 36, 58, 180),
              -105:(255, 105, 59, 180),
              -95:(171, 181, 93, 180),
              -85:(255, 255, 74, 180),
              -75:(36, 255, 51, 180),
              -20:(100, 144, 78, 180)}
    slovar_celica: ta se dela glede na ime celice.
    npr: {'ATLK1':1, 'CELJE3':6, ....}. Dictionary value je lahko int ali string. mora biti isto v istem slovarju.

    Äe se uporabi slovar_barv, se slovar_celica ne more. Vsaj zaenkrat ne :)
    """
    if tip == "ascii":
        with open(file_pokrivanje, "r") as fo:
            fo_read = fo.readlines()
            fo_read_str = [re.split(r"\t|;",i.strip("\n")) for i in fo_read]
            fo.close()
            gl = glava(file_pokrivanje)
            body = fo_read_str[11:len(fo_read_str)]
            body_df = pd.DataFrame(body)
            body_df[3] = body_df[3].astype(float)
            print(body_df)
            body_df = body_df[body_df[3] >= treshold]
            body_df[0] = body_df[0].str.replace(".","").astype(int)
            body_df[1] = body_df[1].str.replace(".","").astype(int)
            if ((len(slovar_barv) > 0) | (len(slovar_celica) > 0)):
                body_df = body_df[[0,1,2,3]].drop_duplicates().dropna()
            else:
                body_df = body_df[[0,1]].drop_duplicates().dropna()
            resolution = gl['resolution']
            xminn = gl['xmin']
            yminn = gl['ymin']
            xmaxx = gl['xmax']
            ymaxx = gl['ymax']
            ncolss = gl['x_num_pixels']
            nrowss = gl['y_num_pixels']
        name = "Podatek_"
        if ime != '':
            name = ime
        else:
            name = file.split("\\")[-1].split(".")[0]
    elif tip == "df":
        body_df = file_pokrivanje
        body_df = body_df[body_df[3] >= treshold]
        if type(body_df.columns.tolist()[0]) == str:
            print(body_df.shape)
            body_df.columns = [0,1]
        else:
            pass
        name = "Podatek_"
        if ((len(slovar_barv) > 0) | (len(slovar_celica) > 0)):
            body_df = body_df[[0,1,2,3]].drop_duplicates().dropna()
        else:
            body_df = body_df[[0,1]].drop_duplicates().dropna()
        xminn = min(body_df[0].astype(int))
        print(xminn)
        yminn = min(body_df[1].astype(int))
        xmaxx = max(body_df[0].astype(int))
        ymaxx = max(body_df[1].astype(int))
        ncolss = int((xmaxx - xminn)/ resolution) +1
        nrowss = int((ymaxx - yminn)/ resolution) +1
        if ime != '':
            name = ime
        else:
            name = file.split("\\")[-1].split(".")[0]
    elif tip == "csv":
        body_df = pd.read_csv(file, sep = ",")
        body_df = body_df[body_df[3] >= treshold]
        if type(body_df.columns.tolist()[0]) == str:
            print(body_df.shape)
            body_df.columns = [0,1]
        else:
            pass
        if ((len(slovar_barv) > 0) | (len(slovar_celica) > 0)):
            body_df = body_df[[0,1,2,3]].drop_duplicates().dropna()
        else:
            body_df = body_df[[0,1]].drop_duplicates().dropna()
        if ime != '':
            name = ime
        else:
            name = file.split("\\")[-1].split(".")[0]
        # resolution = int(body_df[0][0] - body_df[1][0])
        xminn = min(body_df[0].astype(int))
        yminn = min(body_df[1].astype(int))
        xmaxx = max(body_df[0].astype(int))
        ymaxx = max(body_df[1].astype(int))
        ncolss = int((xmaxx - xminn)/ resolution) +1
        nrowss = int((ymaxx - yminn)/ resolution) +1

        # ncolls = 2478
        # nrowss = 1625

    # # # # # # # # # # # # # # # # # # new_row = {0: meje_okvirja[0][0] , 1: meje_okvirja[0][1]}

    # # # # # # # # # # # # # # # # # # new_row1 = {0: meje_okvirja[1][0] , 1: meje_okvirja[1][1]}


    # # # # # # # # # # # # # # # # # # print(resolution, xminn, yminn, xmaxx, ymaxx, ncolss, nrowss, body_df.shape)
    # # # # # # # # # # # # # # # # # # print(body_df)
    # # # # # # # # # # # # # # # # # # body_df.loc[len(body_df)] = new_row
    # # # # # # # # # # # # # # # # # # body_df.loc[len(body_df)] = new_row1

    body_df = body_df.reset_index(drop = True)
    body_df[1] = body_df[1] + y_offset
    body_df[0] = body_df[0] + x_offset

    print("===========")
    print(body_df)
    xminn =  int(body_df[0].min())
    yminn =  int(body_df[1].min())
    ncolss = int(abs(body_df[0].min() - body_df[0].max()) / resolution) + 1
    nrowss = int(abs(body_df[1].min() - body_df[1].max()) / resolution) + 1
    xmaxx = xminn + (ncolss - 1)*resolution
    ymaxx = yminn + (nrowss - 1)*resolution
    print(resolution, xminn, yminn, xmaxx, ymaxx, ncolss, nrowss, body_df.shape)


    body_df["x_ind"] = ((body_df[0].astype(int) - int(xminn))/resolution).astype(int)
    body_df["y_ind"] = ((body_df[1].astype(int) - int(yminn))/resolution).astype(int)
    body_df.sort_values(by = ['y_ind', 'x_ind'], inplace = True)
    print(body_df["x_ind"].drop_duplicates())
    print(body_df["y_ind"].drop_duplicates())
    #body_df.reset_index(inplace  =True)
    body_df["y_ind"] = body_df["y_ind"].abs()
    #body_df.sort_values(by = ['y_ind', 'x_ind'], ascending = [False, True], inplace = True)
    # nivo

    if len(slovar_barv) > 0:
        print(slovar_barv)
        print("==========")
        print(list(slovar_barv.keys()))
        print("==========")
        m = (list(slovar_barv.keys()))
        m.sort()
        print(m)
        print(min(m))
        body_df['nivo'] = min(m)
        print(body_df)
        for i in range(len(m)):
            body_df.loc[body_df[3] >= m[i], 'nivo'] = m[i]
        body_df['vrednost'] = body_df['nivo'].map(slovar_barv)

        print(body_df['vrednost'])
        sez1 = []
        sez2 = []
        for i in range(nrowss):
            for j in range(ncolss):
                sez2.append((255,255,255,0))
            sez1.append(sez2)
            sez2 = []
        sez1_np = np.array(sez1, dtype = np.uint8)

        # print(body_df)

        for i in body_df.index.tolist():
            y =  sez1_np.shape[0] -1 - body_df.loc[i, 'y_ind']
            x = body_df.loc[i, 'x_ind']
            sez1_np[y][x] = body_df.loc[i,'vrednost']



        print(sez1_np)


    elif len(slovar_celica) > 0:
        # print(slovar_celica)
        print("==========")
        print(list(slovar_celica.keys()))
        print("==========")
        m = (list(slovar_celica.keys()))
        m.sort()
        print(body_df)
        tt = type(list(slovar_celica.values())[0])
        body_df['vrednost1'] = body_df[2].map(slovar_celica)
        if tt == str:
            fil = '____'
            body_df['vrednost1'].fillna(fil, inplace = True)
        elif tt == int:
            fil = -9999
            body_df['vrednost1'].fillna(fil, inplace = True)
        elif tt == float:
            fil = -9999.0
            body_df['vrednost1'].fillna(fil, inplace = True)
        else:
            pass

        # v_barvo = barva(body_df['vrednost1'].drop_duplicates().tolist(), prazno = fil)
        # fil = v_barvo[fil]
        # body_df['vrednost'] = body_df['vrednost1'].map(v_barvo)


        print(body_df['vrednost1'])
        body_df['vrednost1'] = body_df['vrednost1'].astype(np.int16)
        sez1 = []
        sez2 = []
        for i in range(nrowss):
            for j in range(ncolss):
                sez2.append(fil)
            sez1.append(sez2)
            sez2 = []
        sez1_np = np.array(sez1, dtype = np.int16)

        # print(body_df)

        for i in body_df.index.tolist():
            y =  sez1_np.shape[0] -1 - body_df.loc[i, 'y_ind']
            x = body_df.loc[i, 'x_ind']
            sez1_np[y][x] = body_df.loc[i,'vrednost1']



        print(sez1_np)


    else:
        sez1 = []
        sez2 = []
        for i in range(nrowss):
            for j in range(ncolss):
                sez2.append(255)
            sez1.append(sez2)
            sez2 = []
        sez1_np = np.array(sez1, dtype = np.uint8)

                # print(body_df)

        for i in body_df.index.tolist():
            y = sez1_np.shape[0] -1 - body_df.loc[i, 'y_ind']
            x = body_df.loc[i, 'x_ind']
            sez1_np[y][x] = 0
        print(sez1_np)

    with open(odlozisce + "\\" + name + ".tfw", "w") as dd:
        dd.write("{}\n".format(resolution))
        dd.write("0\n")
        dd.write("0\n")
        dd.write("-{}\n".format(resolution))
        dd.write(str(float(body_df[0].min())) + "\n")
        dd.write(str(float(body_df[1].max())))
        dd.close()

    if len(slovar_barv) > 0:
        im = Image.fromarray(sez1_np,  'RGBA')
    else:
        im = Image.fromarray(sez1_np)
    return body_df, sez1_np  , im.save(odlozisce + "\\" + name + ".tif", "TIFF"), x, y


# file = "G:\\razno\\ca_izracun_konec_29_6_2023_2_best_serverja.csv"
# file = "G:\\razno\\ca_izracun_konec_31_7_2023_1_best_server.csv"
# file = "G:\\razno\\ca_izracun_konec_31_7_2023_2_best_serverja.csv"
# file = "G:\\Razno\\nas_2_best_serve_minus_115.csv"
# df1 = pd.read_csv(file)
# t = naredi_tif(file, "G:\\Razno\\", tip = "csv")






