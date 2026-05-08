# -*- coding: utf-8 -*-
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import numpy as np
try:
    import scipy.misc  # odstranjen v scipy >= 1.12; modul ni nikjer uporabljen
except ImportError:
    pass
from scipy import ndimage
import matplotlib.pyplot as plt
import os
import pandas as pd

# folder = r"G:\Pokrivanja\Splet\\"
# folder = "G:\\Razno\\"
# ime_slike= "GSM 900 -101.tif"
# ime_slike= "ska_108.tif"
# ime_slike = "CA.tif"

def inverse(array):
    """
    vir: https://www.includehelp.com/python/fast-replacement-of-values-in-a-numpy-array.aspx
    Konkretna funkcija dela samo z vrednostmi od 0:255
    Input je np.array
    """
    d= dict(zip(list(range(0,256,1)),list(reversed(list(range(0,256,1))))))
    new = np.copy(array)
    for i,j in d.items():
        new[array==i] = j
    return new

def blur(mapa, slika, odlozisce):
    """
    mapa: kje se slika nahaja - polna pot
    slika: ime slik brez polne poti.  Format mora biti tif
    odlozisce: kam naj se slika odlozi. Ime slike bo enako izvirni sliki s pripisom "__BLUR".
    """
    im0 = Image.open(mapa + slika)
    face = np.array(im0)
    face1 = inverse(face)
    blurred_face1 = ndimage.gaussian_filter(face1, sigma=1.2)
    # blurred_face2 = np.where(blurred_face1 < 230, blurred_face1, 255)
    blurred_face2 = np.where(blurred_face1 > 10, blurred_face1, 0)

    blurred_face3 = inverse(blurred_face2)
    blurred_face4 = np.where(blurred_face3 > 50, 255, blurred_face3)


    im1 = Image.fromarray(blurred_face1)
    im2 = Image.fromarray(blurred_face2)
    im3 = Image.fromarray(blurred_face4)
    if (slika.strip("tif").strip(".") + ".tfw") in os.listdir(mapa):
        with open(mapa + (slika.strip("tif").strip(".") + ".tfw"), "r") as uu:
            uur = uu.read()
            uu.close()
        with open(odlozisce + (slika.strip("tif").strip(".") + "__BLUR.tfw"), "w") as pp:
            pp.write(uur)
            pp.close()
    else:
        pass
    return im3.save(odlozisce + slika.strip("tif").strip(".") + "__BLUR.tif", format = "TIFF")

def blur_transparent(mapa, slika, odlozisce, tfw_splet = False):
    """
    mapa: kje se slika nahaja - polna pot
    slika: ime slik brez polne poti.  Format mora biti tif
    odlozisce: kam naj se slika odlozi. Ime slike bo enako izvirni sliki s pripisom "__BLUR".
    """
    img = Image.open(mapa + slika)
    face = np.array(img)
    blurred_face1 = ndimage.gaussian_filter(face, sigma=1.05)
    blurred_face2 = np.where(blurred_face1 < 230, blurred_face1, 255)

    im1 = Image.fromarray(blurred_face1)
    im2 = Image.fromarray(blurred_face2)
    img = im2.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)


    if (slika.strip(".tif") + ".tfw") in os.listdir(mapa):
        with open(mapa + (slika.strip(".tif") + ".tfw"), "r") as uu:
            uur = uu.read()
            uu.close()
        with open(odlozisce + (slika.strip(".tif") + "__TRANSPARENT_BLUR.tfw"), "w") as pp:
            pp.write(uur)
            pp.close()
    else:
        pass
    if tfw_splet == True:
        with open(odlozisce + (slika.strip(".tif") + "__TRANSPARENT_BLUR.tfw"), "w") as pp:
            pp.write("72.1223600000\n")
            pp.write("0.0000000000\n")
            pp.write("0.0000000000\n")
            pp.write("-72.1223600000\n")
            pp.write("1485994.1416846076\n")
            pp.write("5924228.4286862677")
            pp.close()
    return img.save(odlozisce + slika.strip(".tif") + "__TRANSPARENT_BLUR.tif", format = "TIFF")

def transparent(mapa, slika, odlozisce, transparentnost = 0):
    img = Image.open(mapa + slika)
    img.putalpha(transparentnost)
    if (slika.strip("tif").strip(".") + ".tfw") in os.listdir(mapa):
        with open(mapa + (slika.strip("tif").strip(".") + ".tfw"), "r") as uu:
            uur = uu.read()
            uu.close()
        with open(odlozisce + (slika.strip("tif").strip(".") + "__TRANSPARENT.tfw"), "w") as pp:
            pp.write(uur)
            pp.close()
    else:
        pass
    return img.save(odlozisce + slika.strip('.tif') + "__TRANSPARENT.tif")

def transparent2(mapa, slika, odlozisce, tfw_splet = False, format_export = "TIFF"):
    """
    mapa: kje se slika nahaja - polna pot
    slika: ime slik brez polne poti.  Format mora biti tif
    odlozisce: kam naj se slika odlozi. Ime slike bo enako izvirni sliki s pripisom "__TRANSPARENT".
    """
    im2 = Image.open(mapa + slika)
    img = im2.convert("RGBA")
    datas = img.getdata()
    newData = []
    for item in datas:
        if item[0] == 255 and item[1] == 255 and item[2] == 255:
            newData.append((255, 255, 255, 0))
        else:
            newData.append(item)
    img.putdata(newData)


    if (slika.strip(r"[TtIiFf]").strip(".") + ".tfw") in os.listdir(mapa):
        with open(mapa + (slika.strip(r"[TtIiFf]").strip(".") + ".tfw"), "r") as uu:
            uur = uu.read()
            uu.close()
        with open(odlozisce + (slika.strip(r"[TtIiFf]").strip(".") + "__TRANSPARENT.tfw"), "w") as pp:
            pp.write(uur)
            pp.close()
    else:
        pass

    if (slika.strip(r"[PpNnGg]").strip(".") + ".pgw") in os.listdir(mapa):
        print("OOKK")
        with open(mapa + (slika.strip(r"[PpNnGg]").strip(".") + ".pgw"), "r") as uu:
            uur = uu.read()
            uu.close()
        with open(odlozisce + (slika.strip(r"[PpNnGg]").strip(".") + "__TRANSPARENT.pgw"), "w") as pp:
            pp.write(uur)
            pp.close()
    else:
        pass

    informat =  slika.split(".")[1]
    print(informat)
    if format_export == "TIFF":
        koncnica = "tif"
    elif format_export == "PNG":
        koncnica = "png"
    else:
        koncnica = "tif"

    if tfw_splet == True:
        with open(odlozisce + (slika.strip(".tif") + "__TRANSPARENT.tfw"), "w") as pp:
            pp.write("72.1223600000\n")
            pp.write("0.0000000000\n")
            pp.write("0.0000000000\n")
            pp.write("-72.1223600000\n")
            pp.write("1485994.1416846076\n")
            pp.write("5924228.4286862677")
            pp.close()
    return img.save(odlozisce + slika.strip(informat).strip(".") + "__TRANSPARENT" + "." + koncnica, format = format_export)

def tif_to_png(mapa, slika, odlozisce, ime_slike = ''):
    im1 = Image.open(mapa+slika)
    if ime_slike == '':
        im1.save(odlozisce + slika.strip("tif").strip(".") + ".png", format = "PNG")
    else:
        im1.save(odlozisce + ime_slike + ".png", format = "PNG")
    return 0

def napisi_text_na_sliko(mapa, slika, odlozisce,  textwidth = 200, textheight = 200, margin = 200):
    image = Image.open(mapa + slika)
    width, height = image.size
    draw = ImageDraw.Draw(image)
    text = 'Ziga'
    # textwidth, textheight = draw.textsize(text)
    # textwidth = 1000
    # textheight = 1000
    # margin = 100
    # x = width - textwidth - margin
    # y = height - textheight - margin
    x =  margin
    y = margin

    draw.text((x, y), text, font = ImageFont.truetype("arial.ttf", 50))

    # image.save('devnote.png')

    # optional parameters like optimize and quality
    # image.save(mapa + slika.strip('.tif') + '_TEXT.tif', optimize=True, quality=50)
    return image.save(mapa + slika.strip('.tif') + '_TEXT.tif')

def black_to_transparent(img):
    num_channels = img.shape[2]
    dimensions = img.shape[0:2]
    alpha_channel = (np.ones(dimensions) * 255).astype(np.uint8)
    alpha_img = np.dstack((img, alpha_channel ))
    mask = np.sum(alpha_img[:, :, 0:img.shape[2]], axis=2).clip(0,255)
    alpha_img[:,:,num_channels] = mask
    return alpha_img


def naredi_sliko_za_report(mapa, slika_pokrivanje, ime = '', datum = '', odlozisce = "G:\\Razno\\", tip = "PNG", slika_ozadje = r"G:\Geo podatki\Podlaga za reporting D96\novo\\Slika_376.tif", slika_legenda = r"G:\Pokrivanja\Slike_dodatno\Dodatki za slike\\Legenda -108 modra.tif", x = 22, y = -40, tabela= pd.DataFrame(), is_transparent = False):
    """
    1. Vzamo sliko, kjer smo prej Å¾e naredili transparenco ozadja
    2.
    3. zloÅ¾i
    """
    if ime == '':
        ime = slika_pokrivanje.strip("tif").strip(".") + "__PODLAGA.PNG"
    else:
        ime = ime + "__PODLAGA.PNG"
    im2 = Image.open(mapa + slika_pokrivanje)
    if is_transparent == False:
        img = im2.convert("RGBA")
        datas = img.getdata()
        newData = []
        for item in datas:
            if item[0] == 255 and item[1] == 255 and item[2] == 255:
                newData.append((255, 255, 255, 0))
            else:
                newData.append((0, 175, 230, 180))
        img.putdata(newData)
    else:
        img = im2
    # img.putalpha(120)
    im_ozadje = Image.open(slika_ozadje)
    im_legenda = Image.open(slika_legenda)
    img_legenda = im_legenda.convert("RGBA")
    # datas = img_legenda.getdata()
    # newData = []
    # for item in datas:
        # if item[0] == 255 and item[1] == 255 and item[2] == 255:
            # newData.append((255, 255, 255, 0))
        # else:
            # newData.append(item)
    # img_legenda.putdata(newData)
    if slika_legenda == r"G:\Pokrivanja\Slike_dodatno\Dodatki za slike\\Legenda LTE barvna shema.tif":
        img_legenda = img_legenda.resize((500,350))
    else:
        img_legenda = img_legenda.resize((500,250))
    # im_ozadje.paste(img, (13,-26), mask = img)            V primeru, da imaÅ¡ Slika_187
    im_ozadje.paste(img, (x,y), mask = img)
    # im_ozadje.paste(img_legenda, (3700,2500), mask = img_legenda)
    im_ozadje.paste(img_legenda, (1900,1250), mask = img_legenda)
    draw = ImageDraw.Draw(im_ozadje)
    teh = slika_pokrivanje.split(r"_")[0]
    if teh == 'NSA':
        teh = 'NR'
    naslov = teh + " POKRIVANJE " + datum
    draw.text((350, 50), naslov, font = ImageFont.truetype("arial.ttf", 60), fill =(0, 0, 0))
    for i in tabela.index.tolist():
        for j in tabela.columns.tolist():
            if type(tabela.loc[i,j]) != str:
                tabela.loc[i,j] = str(tabela.loc[i,j])
    stolpec = 1
    for i in tabela.index.tolist():
        draw.text((350, 100 + 35*stolpec), "    ".join(tabela.loc[i,:].tolist()), font = ImageFont.truetype("arial.ttf", 40), fill =(0, 0, 0))
        stolpec = stolpec + 1
    return im_ozadje.save(odlozisce + ime, "PNG"), im_ozadje.show()

slovar_lte = {-125:(255, 255, 255, 0),
              -115:(255, 36, 58, 180),
              -105:(255, 105, 59, 180),
              -95:(171, 181, 93, 180),
              -85:(255, 255, 74, 180),
              -75:(36, 255, 51, 180),
              -20:(100, 144, 78, 180)}


def naredi_barve_za_nivoje(mapa, slika, barvni_nivoji):
    """
    Input: map + slika mora biti .grd file ali kaj podobnega, kjer lahko mapiramo vredost na barvo.
    Barvni nivoji: dictionary
    """


