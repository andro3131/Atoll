# -*- coding: utf-8 -*-
###############################################################################
#       ARHIV SPREMEMB V ATOLLU
#   Skripta na podlagi sprememb, ki se zapišejo v mape G:\Avtomatika\EPSG_3794\ podmape  Brisi, Novo in Spremeni, piše v text fajle, kaj so dnevne spremmeb v Atollu. 
#   
#
###############################################################################
import datetime
import time
import os

def main():
    folder = r'G:\Avtomatika\EPSG_3794'
    mape = ['Brisi','Novo','Spremeni']
    mapa_arhiv = 'Arhiv sprememb'
    leto = str(datetime.datetime.now().year)
    mesec = time.asctime().split(" ")[1]
    # Preverimo če obstaja mapa leto in če ne, jo ustvarimo
    if len(os.listdir(folder + "\\"+ mapa_arhiv)) == 0:
        os.mkdir(folder + "\\"+ mapa_arhiv + "\\" + leto)
    else:
        if leto in os.listdir(folder + "\\"+ mapa_arhiv):
            pass
        else:
            os.mkdir(folder + "\\"+ mapa_arhiv + "\\" + leto)
    # Preverimo če obstaja datoteka mesec in če ne, jo ustvarimo
    if (mesec+".txt") not in  os.listdir(folder + "\\"+ mapa_arhiv + "\\" + leto):
        m = open(folder + "\\"+ mapa_arhiv + "\\" + leto + "\\" + mesec + ".txt", "w")
    else:
        m = open(folder + "\\"+ mapa_arhiv + "\\" + leto + "\\" + mesec + ".txt", "a")

    for i in mape:
        if len(os.listdir(folder + "\\"+ i)) > 0:
            for j in os.listdir((folder + "\\"+ i + "\\")):
                if (j.find('.csv') > 0) & (j.find('NE_BRISI') < 0):
                    t = open(folder + "\\"+ i + "\\" + j, "r")
                    t_read = t.readlines()
                    print
                    for k in t_read:
                        m.write(time.asctime() + "\t" + i + "\t" + j.split("_")[1].split('.csv')[0] + "\t" + k )
                    t.close()
    m.write("\n")
    m.close()
                
if __name__ == '__main__':
    main()