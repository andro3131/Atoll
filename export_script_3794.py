# -*- coding: utf-8 -*-

###############################################################################################
#       KRMILJENJE EXPORTOV IZ ATOLL-A
# - Skripta naredi ascii exporte iz Atoll-a.
# - Kaj želimo exportirati krmilimo s tabelo mapa_krmilna_tabela ("D:\\Atoll_projects_planer01\\Export_coverage_krmilna_tabela.xlsx"), v stolpcu Export_da_ne. Če je vredost TRUE se coverage exportira, če je FALSE se ne (v excelici uporabi velike črke!). 
#
###############################################################################################

import subprocess
import pyodbc
import time
import os
import pandas as pd
import shutil
import re
import datetime
import pretvornik_koordinat_ascii_file 
import paramiko
import naredi_shp_za_112
import socket
import errno

nsa_correction = True # NSA - Non Stand Alone correction - pokrivanje na anchor celici
export_100 = False  # Export raster 100m
po_celicah = False  # Za export planiranega stanja ali pa iz seznama celic. Celice, ki niso delujoče. Pred tem jih je potrebno aktivirati/dodati v Atoll-u
kopiranje_na_mrezni_disk = True
preverba_velikosti_filetov_na_obeh_streznikih = False    # Atoll in karakoram 
cas_razlika_kriterij = 6*3600       # v sekundah

if export_100 == True:
    kopiranje_na_mrezni_disk = False

t0 = time.time()

odlozisce  = "G:\\Avtomatika\\Eksport\\export_zacasni.txt"
odlozisce_2  = "G:\\Avtomatika\\Eksport\\export_zacasni_2.txt"
#ukaz = "C:\\PROGRA~1\\Forsk\\Add-ins\\SIGNAL~1\\signalsexport "    SPREMENJENO ANDREJ 13.4.2026
ukaz = "C:\\PROGRA~1\\Forsk\\Add-ins\\SignalsExport\\signalsexport "
at_dok_3794 = "D:\\Atoll_projects_planer01\\Atoll_exporti_3794_3_5_1.ATL"
#mapa_ini_file = "C:\\PROGRA~1\\Forsk\\Add-ins\\SIGNAL~1\\"     SPREMENJENO ANDREJ 13.4.2026
mapa_ini_file = "C:\\PROGRA~1\\Forsk\\Add-ins\\SignalsExport\\"
mapa_shrani_arcgis = "G:\\Pokrivanja\\Arcgis\\export\\"
mapa_shrani_arcgis_3794 = "G:\\Pokrivanja\\Arcgis\\export_3794\\"
mapa_shrani_arcgis_3794 = "G:\\Pokrivanja\\Arcgis\\export_3794\\Tretjic\\"
mapa_shrani_arcgis_3794 = "G:\\Pokrivanja\\Arcgis\\export_3794\\Petic\\"
mapa_shrani_arcgis_3794 = "G:\\Pokrivanja\\Arcgis\\export_3794\\Sestic\\"

# mapa_shrani_arcgis_3794 = r"G:\Avtomatika\Eksport\Planirane_celice\Export_planirane_celice\\"

mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Drugic\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\D962\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Tretjic\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Cetrtic\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Petic\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Sestic\\"
mapa_shrani_arcgis_3794_100 = "G:\\Pokrivanja\\Arcgis\\export_3794_100m_6_best_servers\\Sestic\\NBIOT\\"

# mapa_shrani_bpw_neimage = r"\\bpw-neimage\data2\TS\PREDIKCIJE\cov_atoll\atoll_ascii_d96\\"       # Mrežni disk, od koder se napaja baza POSTGRES, ki je vir za T-GIS
# mapa_shrani_bpw_neimage_d48 = r"\\bpw-neimage\data2\TS\PREDIKCIJE\cov_atoll\atoll_ascii\\"       # Mrežni disk za D48 predikcije
# mapa_shrani_bpw_neimage = r"W:\var\atoll_d96\\"       # Mrežni disk, od koder se napaja baza POSTGRES, ki je vir za T-GIS - NE DELA z WINDOWS TASK SCHEDULERJEM!
# mapa_shrani_bpw_neimage_d48 = r"W:\var\atoll_d48\\"      # Mrežni disk za D48 predikcije  - NE DELA z WINDOWS TASK SCHEDULERJEM!
mapa_shrani_bpw_neimage = "/home/raplatimport/atoll/var/atoll_d96/"
mapa_shrani_bpw_neimage_d48 = "/home/raplatimport/atoll/var/atoll_d48/"
mapa_shrani_marjan = "G:\\Pokrivanja\\Marjan\\"
mapa_shrani_tomaz = "G:\\Pokrivanja\\Tomaz\\EPSG_3912\\Export\\"
mapa_krmilna_tabela = "D:\\Atoll_projects_planer01\\Export_coverage_krmilna_tabela.xlsx"
transfer_log = "G:\\Pokrivanja\\log\\transfer_log.txt"
transfer_log_temp = "G:\\Pokrivanja\\log\\transfer_log_temp.txt"
planirano_stanje = "G:\\Avtomatika\\Eksport\\planirane_celice_tabela.txt"
celice_seznam = r"G:\Avtomatika\Eksport\Planirane_celice\\imena_lokacij_p2.csv"
nr700_original = r"G:\Pokrivanja\Arcgis\export_3794\Sestic\NR__700_original\\"
# celice_seznam = r"G:\Avtomatika\Eksport\Planirane_celice\\imena_lokacij_p3.csv"


def glava(fr):
    # with open(f, "r") as fo:
        # fr = fo.readlines()
        # fo.close()
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
    """
    with open(atoll_txt_export_file_path, "r") as fo:
        fo_read = fo.readlines()
        fo_read_str = [i.strip("\n") for i in fo_read]
        fo.close()
    gl = glava(fo_read_str)
    body = fo_read_str[11:len(fo_read_str)]
    body_df = pd.DataFrame(body)
    body_df = body_df[0].str.split(r"\t|;", expand = True)
    body_df[0] = body_df[0].str.replace(".","")
    body_df[1] = body_df[1].str.replace(".","")
    return gl, body_df
    




# # # # # # # # # ini_nbiot = "SignalsExport_epsg3912_nbiot_Arcgis.txt"

# # # # # # # # # #########################################################################################
# # # # # # # # # # 
# # # # # # # # # # Obstoječe celice
# # # # # # # # # # 
# # # # # # # # # #########################################################################################

def main():

    krm_tab_df = pd.read_excel(mapa_krmilna_tabela)
    nr700_da_ne = krm_tab_df.loc[(krm_tab_df['ime_fajla'] == 'NR_700'), 'Export_da_ne'].item()
    krm_tab_df["tehn_check"] =  krm_tab_df["tehn"].notna()
    krm_tab_df = krm_tab_df[krm_tab_df["Export_da_ne"] == True]
    krm_tab_df['fajl'] = krm_tab_df['ime_fajla']+"_1_w.txt"
    print(krm_tab_df)


    for i in krm_tab_df.index:
        print(i)
        t_a = time.time() 
        file_odpri = open(odlozisce_2,"w")
        file_odpri.write('')
        file_odpri.close()
        if krm_tab_df.loc[i,"tehn_check"] == True:
            if po_celicah == True:
                celice_df = pd.read_csv(celice_seznam)
                celice_list = celice_df['cell1'].tolist()
                for j in celice_list:
                    sez_zac = krm_tab_df.loc[i, "tehn"].split("|")
                    if len(sez_zac) > 1:
                        file_odpri_2 = open(odlozisce_2,"a")
                        file_odpri_2.write("(" + sez_zac[0][0:len(sez_zac[0])-2] + " & ([TX_ID] = " + j + ")) | " + sez_zac[1][0:len(sez_zac[1])-1] + " & ([TX_ID] = " + j + "))) | ")
                        file_odpri_2.close()
               

                        print("(" + sez_zac[0][0:len(sez_zac[0])-2] + " & ([TX_ID] = " + j + ")) | " + sez_zac[1][0:len(sez_zac[1])-1] + " & ([TX_ID] = " + j + "))) | ")
                       
                    else:
                        file_odpri_2 = open(odlozisce_2,"a")
                        file_odpri_2.write("(" + sez_zac[0][0:len(sez_zac[0])] + " & ([TX_ID] = " + j + ")) | ")
                        file_odpri_2.close()
                        print("(" + sez_zac[0][0:len(sez_zac[0])] + " & ([TX_ID] = " + j + ")) | ")
                
                file_odpri_2 = open(odlozisce_2,"r+")
                f_read = file_odpri_2.readlines()
                file_odpri_2.close()
                f_read = f_read[0][0:len(f_read[0])-2]
                file_odpri_2 = open(odlozisce_2, 'w')
                file_odpri_2.writelines(f_read)
                file_odpri_2.close()
                
            else:
                file_odpri_2 = open(odlozisce_2,"w")
                file_odpri_2.write(krm_tab_df.loc[i, "tehn"])
                file_odpri_2.close()
                krm_tab_df.loc[i, "tehn"]
        if export_100 == True:
            ini_file = krm_tab_df.loc[i,"ini_file_3794_100_slovar"]
            at_dok_3794 = krm_tab_df.loc[i,'atoll_dokument']
            odlozisce_pokrivanja = mapa_shrani_arcgis_3794_100
        else:
            ini_file = krm_tab_df.loc[i,"ini_file_3794_slovar"]
            # odlozisce_pokrivanja = mapa_shrani_arcgis_3794
            at_dok_3794 = krm_tab_df.loc[i,'atoll_dokument']
            odlozisce_pokrivanja = krm_tab_df.loc[i,'mapa_shrani']
            mapa_shrani_bpw_neimage = krm_tab_df.loc[i,'mapa_shrani_bpw_neimage']
            
        # ini_file = krm_tab_df.loc[i,"ini_file_3794_slovar"]
        print(ini_file)
        folder = krm_tab_df.loc[i, "folder_slovar"]
        # ini_file_tomaz = krm_tab_df.loc[i,  "ini_file_tomaz_slovar"]
        ime = krm_tab_df.loc[i,  "ime_fajla"]
        t_c = time.time()
        print(ime)
        print(krm_tab_df.loc[i,"tehn"])
        print(at_dok_3794)
        print(odlozisce_pokrivanja)
        print(mapa_shrani_bpw_neimage)
        # at_dok_3794 = "D:\\Atoll_projects_planer01\\Atoll_exporti_3794_3_5_1.ATL"
        subprocess.run("C:\\Users\\planer02\\Skripte\\VBasic\\skripta_filter_atoll_iz_aplikacije_3794.vbs", shell =True)        # Nastavitev filtra
        t_d = time.time()
        print(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt")
        subprocess.run(ukaz + " " + at_dok_3794 + " " + mapa_ini_file + ini_file + " " + odlozisce_pokrivanja + ime + ".txt")   # Izračun predikcije
        t_b = time.time()
        print("Cas izvajanja izračuna tehnologije {} je {} minut. Cas izvajanja filtra je {} s".format(ime, (t_b - t_a)/60, t_d - t_c))
        print("\n")

    ########################################################################
    # Preimenuj filete (Export iz Atoll-a se zaključi z "_[GSM]", "_[LTE]"..., mi želimo "_w"). 
    # V primeru, da fajl "_w" že obstaja, ga prepišemo, drugače ga pustimo.
    # 
    #
    ########################################################################
    if krm_tab_df.shape[0] > 0:
        if len(os.listdir(odlozisce_pokrivanja)) > 0:
            for i in os.listdir(odlozisce_pokrivanja):
                if ((i.find("[") > 0) & ((i.find(".txt") > 0) | (i.find(".TXT") > 0))):
                    if os.path.isfile(odlozisce_pokrivanja + i.split("[")[0] + "1_w.txt"):
                        os.remove(odlozisce_pokrivanja + i.split("[")[0] + "1_w.txt")
                        os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + i.split("[")[0] + "1_w.txt")
                    else: 
                        os.rename(odlozisce_pokrivanja + i, odlozisce_pokrivanja + i.split("[")[0] + "1_w.txt")
                else:
                    pass
             
    #######################################
    # NR 700 coverage naredimo na LTE 1800
    # Izrišemo samo best server 1800 layerja (vzamemo vseh 6 layerejev in nato uparimo z 700 pokrivanjem, kjer nastavimo max moč na NR 700 na -110 dbm. )
    #######################################

    if ((nsa_correction == True) & (nr700_da_ne == True)):
        try:
            shutil.copy2(odlozisce_pokrivanja + 'NR_700_1_w.txt', nr700_original + 'NR_700_1_w.txt')
        except:
            pass
        naredi_shp_za_112.naredi_nsa_700()
     
    #######################################
    # Sprememba imen NBIOT celic
    # Atoll-ov export da ven imena transmitterjev. Potrebujemo pa imena celic. 
    # Primer: PZUSTE18A -> PZUSTE18IOTA
    #######################################

    seznam_stolpcev_celic = [2,4,6,8,10,12]
    if odlozisce_pokrivanja == r"G:\Pokrivanja\Arcgis\NBIOT\NBIOT\NBIOT_3794\\":
        for i in os.listdir(odlozisce_pokrivanja):
            if ((i.find("NBIOT") >= 0) & ((i.find(".txt") > 0) | (i.find(".TXT") > 0))):
                with open(odlozisce_pokrivanja + i, "r") as dd:
                    ddr = dd.readlines()
                    dd.close()
                ddr1 = ddr[0:11]
                for j in ddr[11:]:
                    ddr1.append(re.sub(r"([A-Z]+[01][89])([A-Z])", r"\1IOT\2", j))
                del ddr
                with open(odlozisce_pokrivanja + i.split(".")[0] + "_2.txt", "w") as ww:
                    ww.write("".join(ddr1))
                    ww.close()
            
            
            
                # nbiot_df = beri_atoll_txt_export(odlozisce_pokrivanja + i)
                # shape = nbiot_df[1].shape
                # stolpci = [i for i in range(shape[1]) if i in seznam_stolpcev_celic]
                # print("Zacetek menjava {}.".format(str(i)))
                # for j in stolpci:
                    # nbiot_df[1].iloc[:,j] = nbiot_df[1].iloc[:,j].str[:-1] + "IOT" + nbiot_df[1].iloc[:,j].str[-1]
                    # print(j)
                    # print(nbiot_df[1].iloc[:,j])
                # print("Konec menjava {}.".format(str(i)))
                # with open (odlozisce_pokrivanja + i, 'w') as aa:
                    # aa.write(nbiot_df[0]['type'] + '\n')
                    # aa.write(nbiot_df[0]['timestamp']+ '\n')
                    # aa.write('resolution\t' + str(nbiot_df[0]['resolution']) + '\n')
                    # aa.write('xmin\t' + str(nbiot_df[0]['xmin'])+ '\n')
                    # aa.write('xmax\t' + str(nbiot_df[0]['xmax'])+ '\n')
                    # aa.write('ymin\t' + str(nbiot_df[0]['ymin'])+ '\n')
                    # aa.write('ymax\t' + str(nbiot_df[0]['ymax'])+ '\n')
                    # aa.write('x_num_pixels\t' + str(nbiot_df[0]['x_num_pixels']) + '\n')
                    # aa.write('y_num_pixels\t' + str(nbiot_df[0]['y_num_pixels']) + '\n')
                    # aa.write('\n\n')
                    # aa.close()
                # nbiot_df[1].to_csv(odlozisce_pokrivanja + str(i), mode = 'a', sep = ";", index = False, header = None)
                # print("{} konec!".format(str(i)))
            # else:
                # pass
    else:
        pass

    #######################################
    #
    #   Pretvori v D48
    #
    #######################################    
    
    if krm_tab_df.shape[0] > 0:
        for i in krm_tab_df['fajl'].tolist():
            if i.find('IOT') < 0:
                pretvornik_koordinat_ascii_file.pretvori_ascii_d96_v_d48_2(odlozisce_pokrivanja, i, raster = 25)
    #######################################
    # Prenos na mrežni disk
    #   1. Preveri, če obstaja fajl v obeh mapah. Če ne obstaja v mapi mapa_shrani_bpw_neimage, ga prenese iz mape mapa_shrani_arcgis_3794 v mapo mapa_shrani_bpw_neimage.
    #   2. Preveri, če sta datuma v mapah mapa_shrani_bpw_neimage in mapa_shrani_arcgis_3794. Če je datum v mapi na strežniku mapa_shrani_bpw_neimage manjši, kopiraj, drugače pusti.  
    #    
    #######################################   
     
    if kopiranje_na_mrezni_disk == True:
        if krm_tab_df.shape[0] > 0:
            ssh_client =paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname='karakoram.ts.telekom.si',username='root',password='just4me')
            ftp_client=ssh_client.open_sftp()
            mmm = open(transfer_log, "a")
            # 1. prenos v D96
            for i in krm_tab_df['fajl'].tolist():
                try:
                    # shutil.copyfile(odlozisce_pokrivanja + i, mapa_shrani_bpw_neimage + i)
                    ftp_client.put(odlozisce_pokrivanja + i, mapa_shrani_bpw_neimage + i)
                    mmm.write("\n" + time.asctime() + "\t" + i + " prenešen!")
                    print(i + " uspešno prenešen!")
                
                except:
                    mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    print(i + " ni uspešno prenešen!")                    
                # except paramiko.AuthenticationException as e:
                    # print("AUTHENTICATION FAILED")
                    # print(f"Error: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
                    
                # except paramiko.SSHException as e:
                    # print("SSH ERROR")
                    # print(f"Error: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
                    
                # except FileNotFoundError as e:
                    # print("LOCAL FILE NOT FOUND")
                    # print(f"Errno: {e.errno} ({errno.errorcode.get(e.errno)})")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except PermissionError as e:
                    # print("PERMISSION DENIED")
                    # print(f"Errno: {e.errno} ({errno.errorcode.get(e.errno)})")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except IOError as e:
                    # # Covers SFTP transfer errors
                    # print("I/O ERROR DURING SFTP TRANSFER")
                    # print(f"Errno: {e.errno}")
                    # print(f"Error Code: {errno.errorcode.get(e.errno, 'UNKNOWN')}")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except socket.timeout:
                    # print("CONNECTION TIMED OUT")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except Exception as e:
                    # print("UNEXPECTED ERROR")
                    # print(type(e).__name__, e)
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
            try:
                ftp_client.close()
            except Exception:
                pass
            ssh_client.close()
            print("Connection closed.")           
                        
                        
            ssh_client =paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(hostname='karakoram.ts.telekom.si',username='root',password='just4me')
            ftp_client=ssh_client.open_sftp()

            # 2. prenos v D48
            for i in krm_tab_df['fajl'].tolist():
                try:
                    # shutil.copyfile(odlozisce_pokrivanja + "D48\\" + i, mapa_shrani_bpw_neimage_d48 + i)
                    ftp_client.put(odlozisce_pokrivanja + "\\D48\\" + i, mapa_shrani_bpw_neimage_d48 + i)
                    mmm.write("\n" + time.asctime() + "\t" + i + " prenešen!")
                    print(i + " uspešno pretvorjen v D48 in prenešen!")
                except:
                    mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    print(i + " ni uspešno prenešen!")      
                    
                # except paramiko.AuthenticationException as e:
                    # print("AUTHENTICATION FAILED")
                    # print(f"Error: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
                    
                # except paramiko.SSHException as e:
                    # print("SSH ERROR")
                    # print(f"Error: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
                    
                # except FileNotFoundError as e:
                    # print("LOCAL FILE NOT FOUND")
                    # print(f"Errno: {e.errno} ({errno.errorcode.get(e.errno)})")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except PermissionError as e:
                    # print("PERMISSION DENIED")
                    # print(f"Errno: {e.errno} ({errno.errorcode.get(e.errno)})")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except IOError as e:
                    # # Covers SFTP transfer errors
                    # print("I/O ERROR DURING SFTP TRANSFER")
                    # print(f"Errno: {e.errno}")
                    # print(f"Error Code: {errno.errorcode.get(e.errno, 'UNKNOWN')}")
                    # print(f"Message: {e}")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except socket.timeout:
                    # print("CONNECTION TIMED OUT")
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")                        

                # except Exception as e:
                    # print("UNEXPECTED ERROR")
                    # print(type(e).__name__, e)
                    # mmm.write("\n" + time.asctime() + "\t" + i + " prenos neuspešen")
                    # print(i + " ni uspešno prenešen!")
            try:
                ftp_client.close()
            except Exception:
                pass
            ssh_client.close()
            print("Connection closed.")   
            mmm.close()
                      
    if preverba_velikosti_filetov_na_obeh_streznikih == True:        
        # Dodatna preverba velikosti filetov na obeh strežnikih
        
        ssh_client =paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(hostname='karakoram.ts.telekom.si',username='root',password='just4me')
        ftp_client=ssh_client.open_sftp()
        for i in os.listdir(odlozisce_pokrivanja):
            if i.find(".txt") > 0:
                fajl_atoll_st_size = os.stat(odlozisce_pokrivanja + "\\" +i).st_size
                fajl_atoll_st_mtime  = os.stat(odlozisce_pokrivanja + "\\" + i).st_mtime
                try:
                    fajl_karak_st_size = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_size
                    fajl_karak_st_mtime = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_mtime
                except:
                    fajl_karak_st_size = 0
                    fajl_karak_st_mtime = 0
                cas_razlika = abs(fajl_atoll_st_mtime - fajl_karak_st_mtime)
                print(i)
                # print(cas_razlika)
                # print(((fajl_atoll_st_size != fajl_karak_st_size) | (fajl_atoll_st_mtime != fajl_karak_st_mtime)))
                # print((fajl_atoll_st_size == fajl_karak_st_size))
                # print(((fajl_atoll_st_size != fajl_karak_st_size) | (cas_razlika > cas_razlika_kriterij)))
                if (fajl_atoll_st_size != fajl_karak_st_size):       # ((fajl_atoll_st_size != fajl_karak_st_size) | (cas_razlika > cas_razlika_kriterij))
                    try:
                        # shutil.copyfile(odlozisce_pokrivanja + i, mapa_shrani_bpw_neimage + i)
                        ftp_client.put(odlozisce_pokrivanja + i, mapa_shrani_bpw_neimage + i)
                        print(i + " uspešno prenešen v drugo!")
                    except:
                        print(i + " ni uspešno prenešen v drugo!")
                    fajl_atoll_st_size = os.stat(odlozisce_pokrivanja + "\\" +i).st_size
                    fajl_atoll_st_mtime  = os.stat(odlozisce_pokrivanja + "\\" +i).st_mtime
                    fajl_karak_st_size = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_size
                    fajl_karak_st_mtime = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_mtime
                    print(((fajl_atoll_st_size != fajl_karak_st_size) | (cas_razlika > cas_razlika_kriterij)))
        # D48
        try:
            for i in os.listdir(odlozisce_pokrivanja + "\\D48"):
                if ((i.find(".txt") > 0) & (i.find("IOT") < 0)):
                    fajl_atoll_st_size = os.stat(odlozisce_pokrivanja + "\\D48\\" +i).st_size
                    fajl_atoll_st_mtime  = os.stat(odlozisce_pokrivanja + "\\D48\\" + i).st_mtime
                    try:
                        fajl_karak_st_size = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_size
                        fajl_karak_st_mtime = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_mtime
                    except:
                        fajl_karak_st_size = 0
                        fajl_karak_st_mtime = 0
                    cas_razlika = abs(fajl_atoll_st_mtime - fajl_karak_st_mtime)
                    # print(i)
                    # print(cas_razlika)
                    # print(((fajl_atoll_st_size != fajl_karak_st_size) | (fajl_atoll_st_mtime != fajl_karak_st_mtime)))
                    # print((fajl_atoll_st_size == fajl_karak_st_size))
                    # print(((fajl_atoll_st_size != fajl_karak_st_size) | (cas_razlika > cas_razlika_kriterij)))
                    if (fajl_atoll_st_size != fajl_karak_st_size):       # ((fajl_atoll_st_size != fajl_karak_st_size) | (cas_razlika > cas_razlika_kriterij))
                        try:
                            # shutil.copyfile(odlozisce_pokrivanja + i, mapa_shrani_bpw_neimage + i)
                            ftp_client.put(odlozisce_pokrivanja + "\\D48\\" + i, mapa_shrani_bpw_neimage_d48 + i)
                            print(i + " uspešno prenešen v drugo!")
                        except:
                            print(i + " ni uspešno prenešen v drugo!")
                        fajl_atoll_st_size = os.stat(odlozisce_pokrivanja + "\\" +i).st_size
                        fajl_atoll_st_mtime  = os.stat(odlozisce_pokrivanja + "\\" +i).st_mtime
                        fajl_karak_st_size = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_size
                        fajl_karak_st_mtime = ftp_client.stat(mapa_shrani_bpw_neimage + i).st_mtime
        except:
            pass
            
        ftp_client.close()
        ssh_client.close()
            
if __name__ == '__main__':
    main()
            
    
    