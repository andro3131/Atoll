# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 08:57:26 2020

@author: kavklerz
"""
import funkcije_at
import prilagodi_3794
import sql_atoll_3794
import os

odlozisce_dnevnik = "G:\\Avtomatika\\EPSG_3794\\dnevnik.xlsx"
odlozisce_dnevnik = "G:\\Avtomatika\\EPSG_3794\\Dnevnik\\"
odlozisce_novo = "G:\\Avtomatika\\EPSG_3794\\Novo\\"
odlozisce_spremeni = "G:\\Avtomatika\\EPSG_3794\\Spremeni\\"
odlozisce_spremeni_atributi = "G:\\Avtomatika\\EPSG_3794\\Spremeni\\Atributi\\"
odlozisce_brisi_drugo = "G:\\Avtomatika\\EPSG_3794\\Brisi_drugo\\"
odlozisce_brisi = "G:\\Avtomatika\\EPSG_3794\\Brisi\\"
odlozisce_sosede_dodaj = "G:\\Avtomatika\\EPSG_3794\\Sosede\\Dodaj\\"
odlozisce_sosede_brisi = "G:\\Avtomatika\\EPSG_3794\\Sosede\\Brisi\\"
tabela_upravljaj = "G:\\Avtomatika\\Eksport\\Podatki_krmilna_tabela.xlsx"

novo = True
spremeni = True
brisi = True
dnevnik = False
sprememba = []

brisanje_krirerij = 100

def vrni_vars(seznam1, seznam2, modul):
    sl = {}
    for i in range(len(seznam1)):
        sl[seznam1[i]] = vars(modul)[seznam2[i]]
    return sl

def vrni_seznam(slovar):
    sl  ={}
    for i in slovar.keys():
        if type(slovar[i]) == str:
            sl[i] = slovar[i].split(",")
        else:
            sl[i] = ["nekaj"]
    return sl            

def main():
    
    krm_tab = funkcije_at.pd.read_excel(tabela_upravljaj)
    # krm_tab = krm_tab[krm_tab['posodobi'] == True]
    krm_tab_brisi = krm_tab[(krm_tab['posodobi'] == True)&(krm_tab['brisi'] == True)]
    krm_tab_novo = krm_tab[(krm_tab['posodobi'] == True)&(krm_tab['novo'] == True)]
    krm_tab_spremeni = krm_tab[(krm_tab['posodobi'] == True)&(krm_tab['spremeni'] == True)]

    # atoll_tabele = dict(zip(krm_tab['zap_st'].tolist(), krm_tab['atoll_tabele'].tolist()))
    atoll_tabele_brisi = dict(zip(krm_tab_brisi['zap_st'].tolist(), krm_tab_brisi['atoll_tabele'].tolist()))
    atoll_tabele_novo = dict(zip(krm_tab_novo['zap_st'].tolist(), krm_tab_novo['atoll_tabele'].tolist()))
    atoll_tabele_spremeni = dict(zip(krm_tab_spremeni['zap_st'].tolist(), krm_tab_spremeni['atoll_tabele'].tolist()))

    # prilagodi_3794_tabele = vrni_vars(krm_tab['zap_st'].tolist(), krm_tab['prilagodi_3794_tabele'].tolist())
    prilagodi_3794_tabele_brisi = vrni_vars(krm_tab_brisi['zap_st'].tolist(), krm_tab_brisi['prilagodi_3794_tabele'].tolist(), prilagodi_3794)
    prilagodi_3794_tabele_novo = vrni_vars(krm_tab_novo['zap_st'].tolist(), krm_tab_novo['prilagodi_3794_tabele'].tolist(), prilagodi_3794)
    prilagodi_3794_tabele_spremeni = vrni_vars(krm_tab_spremeni['zap_st'].tolist(), krm_tab_spremeni['prilagodi_3794_tabele'].tolist(), prilagodi_3794)

    # sql_atoll_3794_tabele = vrni_vars(krm_tab['zap_st'].tolist(), krm_tab['sql_atoll_3794_tabele'].tolist())
    sql_atoll_3794_tabele_brisi = vrni_vars(krm_tab_brisi['zap_st'].tolist(), krm_tab_brisi['sql_atoll_3794_tabele'].tolist(), prilagodi_3794)
    sql_atoll_3794_tabele_novo = vrni_vars(krm_tab_novo['zap_st'].tolist(), krm_tab_novo['sql_atoll_3794_tabele'].tolist(), prilagodi_3794)
    sql_atoll_3794_tabele_spremeni = vrni_vars(krm_tab_spremeni['zap_st'].tolist(), krm_tab_spremeni['sql_atoll_3794_tabele'].tolist(), prilagodi_3794)

    odstr_stolp = dict(zip(krm_tab['zap_st'].tolist(), krm_tab['odstr_stolpci'].tolist()))
    odstr_stolpci = vrni_seznam(odstr_stolp)

    # pkey = dict(zip(krm_tab['zap_st'].tolist(), krm_tab['pkey'].tolist()))
    pkey_novo = dict(zip(krm_tab_novo['zap_st'].tolist(), krm_tab_novo['pkey'].tolist()))
    pkey_spremeni = dict(zip(krm_tab_spremeni['zap_st'].tolist(), krm_tab_spremeni['pkey'].tolist()))

    ########################################################
    # Beri krmilno tabelo - KONEC
    ########################################################


    if len(os.listdir(odlozisce_novo)) > 0:   
        for i in os.listdir(odlozisce_novo):
            os.remove(odlozisce_novo+i)
        else:
            pass 

    if len(os.listdir(odlozisce_spremeni_atributi)) > 0:   
        for i in os.listdir(odlozisce_spremeni_atributi):
            os.remove(odlozisce_spremeni_atributi+i)
        else:
            pass

    if len(os.listdir(odlozisce_spremeni)) > 0:   
        for i in os.listdir(odlozisce_spremeni):
            if i.find('.csv') > 0:
                os.remove(odlozisce_spremeni+i)
            else:
                pass

    if len(os.listdir(odlozisce_brisi)) > 0:   
        for i in os.listdir(odlozisce_brisi):
            os.remove(odlozisce_brisi+i)
        else:
            pass
            
    if len(os.listdir(odlozisce_sosede_dodaj)) > 0:   
        for i in os.listdir(odlozisce_sosede_dodaj):
            os.remove(odlozisce_sosede_dodaj+i)
        else:
            pass

    if len(os.listdir(odlozisce_sosede_brisi)) > 0:   
        for i in os.listdir(odlozisce_sosede_brisi):
            os.remove(odlozisce_sosede_brisi+i)
        else:
            pass

    if len(os.listdir(odlozisce_brisi_drugo)) > 0:   
        for i in os.listdir(odlozisce_brisi_drugo):
            os.remove(odlozisce_brisi_drugo+i)
        else:
            pass

    #############################################################################
    # Kreacija tabel csv
    #############################################################################

    for i in atoll_tabele_novo:
        if novo == True:
            # if funkcije_at.razlika_ustvari(prilagodi_3794_tabele[i], sql_atoll_3794_tabele[i], pkey[i]).shape[0] > 0:
                # funkcije_at.razlika_ustvari(prilagodi_3794_tabele[i], sql_atoll_3794_tabele[i], pkey[i]).to_csv(odlozisce_novo + (str(i) + '_' + atoll_tabele[i] + '.csv'), index=False, sep = ';', decimal = ',')
        
            i_novo = funkcije_at.razlika_ustvari(prilagodi_3794_tabele_novo[i], sql_atoll_3794_tabele_novo[i], pkey_novo[i])
            i_stolpec_novo = i_novo.columns.to_list()
            
            if len(odstr_stolpci[i]) > 0:
                for j in odstr_stolpci[i]:
                    if j in i_stolpec_novo:
                        i_stolpec_novo.remove(j)
            tab_den = prilagodi_3794_tabele_novo[i]
            tab_den = tab_den[i_stolpec_novo]
            tab_ato = sql_atoll_3794_tabele_novo[i]
            tab_ato = tab_ato[i_stolpec_novo]
            
            i_novo_odstr = funkcije_at.razlika_ustvari(tab_den, tab_ato, pkey_novo[i])
            if i_novo_odstr.shape[0] > 0:
                if atoll_tabele_novo[i].find("neigh") > 0:
                    i_novo_odstr.to_csv(odlozisce_sosede_dodaj + (str(i) + '_' + atoll_tabele_novo[i] + '.csv'), index=False, sep = ';', decimal = ',')
                else:
                    i_novo_odstr.to_csv(odlozisce_novo + (str(i) + '_' + atoll_tabele_novo[i] + '.csv'), index=False, sep = ';', decimal = ',')
                sprememba.append(str(atoll_tabele_novo[i]))
            
            print(atoll_tabele_novo[i])
            
    for i in atoll_tabele_spremeni:           
        if spremeni == True:
            i_spremeni =  funkcije_at.razlika_spremeni(prilagodi_3794_tabele_spremeni[i], sql_atoll_3794_tabele_spremeni[i])
            i_stolpec = i_spremeni.columns.to_list()

            if len(odstr_stolpci[i]) > 0:
                for j in odstr_stolpci[i]:
                    if j in i_stolpec:
                        i_stolpec.remove(j)
            tab_den = prilagodi_3794_tabele_spremeni[i]
            tab_den = tab_den[i_stolpec]
            tab_ato = sql_atoll_3794_tabele_spremeni[i]
            tab_ato = tab_ato[i_stolpec]
            if i_spremeni.shape[0] > 0:
                zac = funkcije_at.razlika_spremeni(tab_den, tab_ato, datum = False)
                zac_prvi = zac[zac.columns[0]]
                zac_ost = zac[zac.columns[1:]].dropna(how = 'all')
                zac_filter = zac_ost.join(zac_prvi)
                zac_filter = zac_filter[zac_filter.columns[::-1]]
                if zac_filter.shape[0] > 0:
                    zac_filter.to_csv(odlozisce_spremeni + (str(i) + '_' + atoll_tabele_spremeni[i] + '.csv'), index=False, sep = ';', decimal = ',')
                    sprememba.append(str(atoll_tabele_spremeni[i]))
            for stolpec in i_stolpec:
                funkcije_at.razlika_stolpec(i_spremeni, (str(i) + '_' + atoll_tabele_spremeni[i]), stolpec, pkey_spremeni[i],  odlozisce_spremeni_atributi)

    for i in atoll_tabele_brisi:
        if brisi == True:
            if 	funkcije_at.razlika_brisi(prilagodi_3794_tabele_brisi[i], sql_atoll_3794_tabele_brisi[i]).shape[0] > 0:
                if atoll_tabele_brisi[i].find("neigh") > 0:
                    funkcije_at.razlika_brisi(prilagodi_3794_tabele_brisi[i], sql_atoll_3794_tabele_brisi[i]).to_csv(odlozisce_sosede_brisi + (str(i) + '_' + atoll_tabele_brisi[i] + '.csv'), index=False, sep = ';', decimal = ',')
                else:
                    funkcije_at.razlika_brisi(prilagodi_3794_tabele_brisi[i], sql_atoll_3794_tabele_brisi[i]).to_csv(odlozisce_brisi + (str(i) + '_' + atoll_tabele_brisi[i] + '.csv'), index=False, sep = ';', decimal = ',')
                sprememba.append(str(atoll_tabele_brisi[i]))
        
    spr = list(set(sprememba))  
    for i in os.listdir(odlozisce_spremeni_atributi):
        os.rename(odlozisce_spremeni_atributi+i,odlozisce_spremeni_atributi+i+'.csv')

    # =============================================================================	
    # xgsecondaryantennas - trenutno se ne posodablja
    # =============================================================================

    xg = False
    if xg == True:
        try: 
            tab1 = funkcije_at.razlika_spremeni(prilagodi_3794.xgtransmitters, prilagodi_3794.xgtransmitters_atoll)
            if 'AZIMUT' in tab1.columns.tolist():
                tab1 = tab1[['TX_ID',  'AZIMUT']]
                izbor = tab1.dropna(how = 'all', subset = ['AZIMUT'])
            elif 'ANTENNA_NAME' in tab1.columns.tolist():
                tab1 = tab1[['TX_ID',  'ANTENNA_NAME']]
                izbor = tab1.dropna(how = 'all', subset = ['ANTENNA_NAME'])
            # elif ('SHAREDMAST' in tab1.columns.tolist()) & ('ANTENNA_NAME' in tab1.columns.tolist()):
                # tab1 = tab1[['TX_ID',  'AZIMUT', 'ANTENNA_NAME']]
                # izbor = tab1.dropna(how = 'all', subset = ['AZIMUT','ANTENNA_NAME'])
            else:
                izbor = funkcije_at.pd.DataFrame()
            izbor_df = izbor.to_frame()
            izbor_df.to_csv(odlozisce_brisi_drugo + ('xgsecondaryantennas' + '.csv'), index=False, sep = ';', decimal = ',')
            izb_sk = izbor_df.merge(prilagodi_3794.xgsecondaryantennas, how = 'inner', left_on = izbor_df['TX_ID'], right_on = prilagodi_3794.xgsecondaryantennas['TX_ID'])
            izb_sk = izb_sk[['TX_ID_y', 'ANTENNA', 'AZIMUT', 'TILT','PERCENT_POWER']].rename(columns = {'TX_ID_y':'TX_ID'})

            xgsec_novo = funkcije_at.razlika_ustvari(prilagodi_3794.xgsecondaryantennas, funkcije_at.df(sql_atoll_3794.xgsecondaryantennas_atoll, sql_atoll_3794.conn_atoll), 'TX_ID')
            if xgsec_novo.shape[0] > 0:
                xg_skup = funkcije_at.pd.concat([izb_sk,xgsec_novo])
            else:
                xg_skup = izb_sk
            xg_skup.to_csv(odlozisce_novo + ('35' + '_' + 'xgsecondaryantennas' + '.csv'), index=False, sep = ';', decimal = ',')
        except:
            KeyError
    else:
        pass

    # =============================================================================	
    # - Tukaj preverimo število elementov po tabelah za brisanje. Če število elementov za brisanje preseže brisanje_krirerij, se tabelo preimenuje s predpono "__NE_BRISI__" v mapi odlozisce_brisi in se tako brisanje ne izvede. To naredimo,
    #       da se izognemo morebitnemu brisanju zaradi izpada podatkov, če je slučanjno izpad na kakšnem viru za Atoll. 
    # 
    # =============================================================================
    for i in os.listdir(odlozisce_brisi):
        t = funkcije_at.pd.read_csv(odlozisce_brisi + i, sep = ";")
        if t.shape[0] >= brisanje_krirerij:
            # t.to_csv(odlozisce_brisi + "__NE_BRISI__" + i, index = False)
            os.rename(odlozisce_brisi + i, odlozisce_brisi + "__NE_BRISI__" + i)
        else:
            pass

if __name__ == '__main__':
    main()