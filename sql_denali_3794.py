# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 09:54:06 2020

@author: kavklerz
"""

import pyodbc 

conn_denali = pyodbc.connect('Driver={SQL Server};'
                      'Server=BPW-DENALI;'
                      'Database=SQLBazne;'
                      'UID=beribaze;'
                      'PWD=beribaze')

sites_denali = """select lokbb.ImeBSC as NAME, cast(round(lokbb.GKe,0) as int) as LONGITUDE, cast(round(lokbb.GKn,0) as int) as LATITUDE from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
union
select lokrr.ImeBSC as NAME, cast(round(lokrr.GKe,0) as int) as LONGITUDE, cast(round(lokrr.GKn,0) as int)  as LATITUDE from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
"""

sites_denali_za_upravicenost_bazne_postaje = """select ImeBSC, GKe, GKn from SQLBazne.dbo.Lokacija"""

antene_denali = """select ant_vh.PbpAntenaVhodID, 
ant_vh.AntenaID,
div.Ime as div,
ant_vh.ET,
tip_ant_vh.BeamHeight,
tip_ant_vh.BeamWidth,
tip_ant_vh.ETdo,
tip_ant_vh.ETod,
tip_ant_vh.Fdo,
tip_ant_vh.Fod,
tip_ant_vh.Gain,
tip_ant_vh.InputNo,
tip_ant_vh.Oznaka,
ant_tip.Ime,
ant_tip.Kot,
ant_tip.Dobitek
from 
SQLBazne.dbo.PbpAntenaVhod ant_vh 
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join Diversity div on ant_vh.DiversityID = div.DiversityID
"""

tipi_an_denali = """select  tip_ant_vh.PbpTipAntenaVhodID,
tip_ant_vh.TipAnteneID,
tip_ant_vh.DiversityID,
tip_ant_vh.InputNo,
tip_ant_vh.ETdo,
tip_ant_vh.ETod,
tip_ant_vh.Fod,
tip_ant_vh.Fdo,
tip_ant_vh.BeamWidth,
tip_ant_vh.BeamHeight,
tip_ant_vh.Gain,
UPPER(tip_ant_vh.Oznaka),
ant_tip.Ime
from SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID"""

sistem = """SELECT [SistemID]
      ,[GenSistemID]
	  ,[Ime]
	  ,case when GenSistemID = 2 THEN 'GSM'
	  when GenSistemID = 4 THEN 'UMTS'
	  when GenSistemID = 11 THEN 'LTE'
	  when GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when ime = '5G 2600/2700' then 2600
		   when ime ='5G 3500' then 3500
		   when ime ='5G 700' then 700
		   when ime ='GSM 1800' then 1800
		   when	ime ='GSM 900' then 900
		   when ime ='LTE 1800' then 1800
		   when ime ='LTE 2100' then 2100
		   when ime ='LTE 2600' then 2600
		   when	ime ='LTE 2600 TDD' then 2600
			when ime ='LTE 3500' then 3500
			when ime ='LTE 3500 TDD' then 3500
			when ime ='LTE 700' then 700
			when ime ='LTE 800' then 800
			when ime ='LTE 900' then 900
			when ime ='UMTS' then 2100
			when ime ='UMTS 900' then 900
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as fband,
		case when CHARINDEX('TDD', ime) != 0 then 'TDD' else 'FDD' end as duplex
  FROM [SQLBazne].[dbo].[Sistem]
  where Radio =1 and GenSistemID in (2,4,11,12)
  order by ime"""
  
celice_ena = """
select distinct
	lokbb.ImeBSC,
	celica.ime as celica,
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='5G 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900'
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
			end as fband,    
		case when CHARINDEX('TDD', sis.ime) != 0 then 'TDD' else 'FDD' end as duplex,
	case 
	when sis.Ime like 'LTE%' then va.ecgi
	else va.CI end								as CID,
	case when ant.azimut is null then cast(ant.Azimut_P as int)
    else cast(ant.azimut as int) end as azimut,
	case when ant.nagib is null then ant.Nagib_P
    else ant.nagib end as nagib,
	ant_vh.ET, 
    case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as Visina,
	TipAntene, 
	ant.antenaid,
	oddajnaMoc, 
	case when sis.Ime like 'LTE%' 
	then (cableLoss + 0.0)/10 
	else null end								as cable_loss,
	case 
	when tant.Ime = 'Zunanja' then 'Outdoor'
	when tant.Ime = 'Notranja' then 'Indoor'
	else 'Tunnel' end							as Type,
    tip_ant_vh.oznaka,
    tip_ant_vh.ETdo,
    tip_ant_vh.ETod,
    va.UARFCN

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.AntenaID = ant_vh.AntenaID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join atoll.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
where rru.LokacijaID = kabin.LokacijaID and Celica.Delujoca = 1
order by celica.ime"""

celice = """with tab1 as (
select distinct
	lokbb.ImeBSC,
	celica.ime as celica,
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 700' then 700
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
	       when sis.ime = 'NR 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='NR 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
           when sis.ime ='NR 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900' 
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
			when sis.ime ='NR 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='NR 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='NR 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
			when sis.ime ='NR 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            
			end as fband,    
		case when CHARINDEX('TDD', sis.ime) != 0 then 'TDD' else 'FDD' end as duplex,
	/*case 
	when sis.Ime like 'LTE%' then va.ecgi
	else va.CI end								as CID,*/
    0 as CID,
	case when ant.azimut is null then ant.Azimut_P
    else cast(ant.azimut as int) end as azimut,
	case when ant.nagib is null then ant.Nagib_P
    else ant.nagib end as nagib,
	case when ant_vh.ET is null then ant_vh.ET_p
    else ant_vh.ET end as ET,
    case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as Visina,
	--va.TipAntene, 
    ant_tip.Ime as TipAntene, 
	convert(varchar, ant.AntenaID) as AntenaID,
    ant_tip.dobitek,
	oddajnaMoc, 
	case when sis.Ime like 'LTE%' 
	then (cableLoss + 0.0)/10 
	else null end								as cable_loss,
	case 
	when tant.Ime = 'Zunanja' then 'Outdoor'
	when tant.Ime = 'Notranja' then 'Indoor'
	else 'Tunnel' end							as Type,
    tip_ant_vh.oznaka,
    tip_ant_vh.ETdo,
    tip_ant_vh.ETod,
    --va.UARFCN,
    0.0 as UARFCN,
	rru.LokacijaID as rru_lokacija,
	kabin.LokacijaID as bbu_lokacija_id,
    lokrr.ImeBSC as rru_ime,
    cast(round(lokrr.GKe,0) as int) as lokrr_zsirina,
    cast(round(lokrr.GKn,0) as int) as lokrr_zvisina,
	lokbb.ImeBSC as bb_ime,
    case when ((cast(round(ant.GKe,0) as int) is null) or (ant.GKe = 0))  then cast(round(lokrr.GKe,0) as int)
	else cast(round(ant.GKe,0) as int) end as ZSirina,
	case when ((cast(round(ant.GKn,0) as int) is null) or (ant.GKn = 0)) then cast(round(lokrr.GKn,0) as int)
	else cast(round(ant.GKn,0) as int) end as ZVisina,
    lokbb.Ime as IIme

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
left join atoll_prod.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
)
select tab1.*,
case when tehn like 'GSM%' or tehn like 'UMTS%' then concat(celica, '_', (ROW_NUMBER() over (PARTITION BY celica ORDER BY AntenaID)))
	else concat(celica, '_', AntenaID)	end	as name_rru_location_antena,
	concat(celica, '_', (ROW_NUMBER() over (PARTITION BY celica ORDER BY AntenaID))) as atoll_name,
	count(celica) OVER (PARTITION BY celica) as stevilo,
	ROW_NUMBER() over (PARTITION BY celica ORDER BY AntenaID) as zap_st ,
	round(oddajnaMoc - 10 * log(count(celica) OVER (PARTITION BY celica), 10),1) as power_split
from tab1"""

gsm_cells = """SELECT * FROM [attributdb].[dbo].[oss_bcch]"""

#gsm_cells = """SELECT   
#       [NW]
#      ,[MSC]
#      ,[BSC]
#      ,[CELL]
#     ,[ncc]
#      ,[bcc]
#     ,[mcc]
#     ,[mnc]
#     ,[lac]
#     ,[rac]
#     ,[ci]
#     ,[bcchno]
#     ,[ch_group_0]
#  FROM [attributdb].[dbo].[oss_bcch]"""

umts_cells = """SELECT * FROM [attributdb].[dbo].[UMTS_Cell]"""

lte_cells = """SELECT * FROM [attributdb].[dbo].[LTE_Cell]"""

petg_cells = """SELECT * FROM [attributdb].[dbo].[NRcelice-v]"""

mw_small_cell = """select distinct celica.ime as celica
from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join atoll_prod.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
where tant.Ime = 'Notranja'
"""

celice_nove_bp = """with tab1 as (
select distinct
	lokbb.ImeBSC,
	celica.ime as celica,
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
	       when sis.ime = 'NR 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='NR 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
           when sis.ime ='NR 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900' 
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
			when sis.ime ='NR 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='NR 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='NR 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
			when sis.ime ='NR 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
			end as fband,    
		case when CHARINDEX('TDD', sis.ime) != 0 then 'TDD' else 'FDD' end as duplex,
	--case 
	--when sis.Ime like 'LTE%' then va.ecgi
	--else va.CI end								as CID,
	case when ant.azimut is null then ant.Azimut_P
    else cast(ant.azimut as int) end as azimut,
	case when ant.nagib is null then ant.Nagib_P
    else ant.nagib end as nagib,
	case when ant_vh.ET is null then ant_vh.ET_p
    else ant_vh.ET end as ET,
    case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as Visina,
	ant_tip.Ime as TipAntene,
	--va.TipAntene, 
	REPLACE(rru_tip.Ime, '+','/' ) as rru_tip,
	convert(varchar, ant.AntenaID) as AntenaID,
    ant_tip.dobitek,
	--oddajnaMoc, 
	--case when sis.Ime like 'LTE%' 
	--then (cableLoss + 0.0)/10 
	--else null end								as cable_loss,
	case 
	when tant.Ime = 'Zunanja' then 'Outdoor'
	when tant.Ime = 'Notranja' then 'Indoor'
	else 'Tunnel' end							as Type,
    tip_ant_vh.oznaka,
    tip_ant_vh.ETdo,
    tip_ant_vh.ETod,
    --va.UARFCN,
	rru.LokacijaID as rru_lokacija,
	kabin.LokacijaID as bbu_lokacija_id,
    lokrr.ImeBSC as rru_ime,
    cast(round(lokrr.GKe,0) as int) as lokrr_zsirina,
    cast(round(lokrr.GKn,0) as int) as lokrr_zvisina,
	lokbb.ImeBSC as bb_ime,
    case when cast(round(ant.GKe,0) as int) is null then cast(round(lokrr.GKe,0) as int)
	else cast(round(ant.GKe,0) as int) end as ZSirina,
	case when cast(round(ant.GKn,0) as int) is null then cast(round(lokrr.GKn,0) as int)
	else cast(round(ant.GKn,0) as int) end as ZVisina

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpRUunitTip rru_tip on rru_tip.PbpRUunitTipID = rru.PbpRUunitTipID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
--left join atoll_prod.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
)
select
tab1.ImeBSC as BSC, 
tab1.TipAntene as "Antena NOVA"	,
tab1.azimut as Azimut,
tab1.nagib as MDT,
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port1",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port2",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port3",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port4",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port5",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT Port6",
CONCAT(tab1.oznaka, '=', tab1.ET) as "EDT 5G",
tab1.rru_tip as RU,
tab1.celica as Cell, 
'' as "RRU port",
tab1.Ime as "Tehnol",
case 
	when tab1.tehn = 'GSM' then ''
	when tab1.tehn = 'LTE' then SUBSTRING(tab1.celica, PATINDEX('%[0-9]%', tab1.celica), 2)
	when tab1.tehn = '5G' then CONCAT(SUBSTRING(tab1.celica, PATINDEX('%[0-9]%', tab1.celica), 2), 'NR')
	end as konc,
case 
	when Ime = 'GSM 1800' then 4
	else 0 end as dod,
tab1.ETdo,
tab1.ETod
from tab1
"""

micro_in_pico_query = """with tab1 as (
select distinct
	lokbb.ImeBSC,
	celica.ime as celica,
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
	       when sis.ime = 'NR 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='NR 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
           when sis.ime ='NR 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900' 
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
			when sis.ime ='NR 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='NR 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='NR 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
			when sis.ime ='NR 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
			end as fband,    
		case when CHARINDEX('TDD', sis.ime) != 0 then 'TDD' else 'FDD' end as duplex,
	case 
	when sis.Ime like 'LTE%' then va.ecgi
	else va.CI end								as CID,
	case when ant.azimut is null then ant.Azimut_P
    else cast(ant.azimut as int) end as azimut,
	case when ant.nagib is null then ant.Nagib_P
    else ant.nagib end as nagib,
	case when ant_vh.ET is null then ant_vh.ET_p
    else ant_vh.ET end as ET,
    case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as Visina,
	va.TipAntene, 
	convert(varchar, ant.AntenaID) as AntenaID,
    ant_tip.dobitek,
	oddajnaMoc, 
	case when sis.Ime like 'LTE%' 
	then (cableLoss + 0.0)/10 
	else null end								as cable_loss,
	case 
	when tant.Ime = 'Zunanja' then 'Outdoor'
	when tant.Ime = 'Notranja' then 'Indoor'
	else 'Tunnel' end							as Type,
    tip_ant_vh.oznaka,
    tip_ant_vh.ETdo,
    tip_ant_vh.ETod,
    va.UARFCN,
	rru.LokacijaID as rru_lokacija,
	kabin.LokacijaID as bbu_lokacija_id,
    lokrr.ImeBSC as rru_ime,
    cast(round(lokrr.GKe,0) as int) as lokrr_zsirina,
    cast(round(lokrr.GKn,0) as int) as lokrr_zvisina,
	lokbb.ImeBSC as bb_ime,
    case when cast(round(ant.GKe,0) as int) is null then cast(round(lokrr.GKe,0) as int)
	else cast(round(ant.GKe,0) as int) end as ZSirina,
	case when cast(round(ant.GKn,0) as int) is null then cast(round(lokrr.GKn,0) as int)
	else cast(round(ant.GKn,0) as int) end as ZVisina,
    lokbb.Ime as IIme,
	bb_tip.Ime as ime_bb,
	/*substring(bb_tip.Ime,1,charindex(' ',bb_tip.Ime)) as bb_type,*/
	case when substring(bb_tip.Ime,1,charindex(' ',bb_tip.Ime)) = 'MicroCell ' then 'Micro'
	when substring(bb_tip.Ime,1,charindex(' ',bb_tip.Ime)) = 'PicoCell ' then 'Pico'
	else substring(bb_tip.Ime,1,charindex(' ',bb_tip.Ime)) end as bb_type
from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpBBunitTip bb_tip on bb_tip.PbpBBunitTipID = bb.PbpBBunitTipID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join atoll_prod.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
where celica.Delujoca = 1
)
select tab1.bb_type, tab1.tehn,  count(*) as stevilo
from tab1
where Delujoca = 1 and ime_bb like '%Micro%' or ime_bb like '%Pico%'
group by tab1.bb_type, tab1.tehn"""


query_bevc = """select distinct
	celica.ime as celica,
    bb.ime as managed_element,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN 'NR'
	  end as tehnologija,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 700' then 700
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as band,  
	crcel.DatumVkljucitve,

    cast(round(lokrr.GKx,0) as int) as GKx,
    cast(round(lokrr.GKy,0) as int) as GKy,
    lokrr.ZVisina Latitude,
	lokrr.ZSirina Longitude,
    cast(round(lokrr.GKe,2) as float) as GKe,
    cast(round(lokrr.GKn,2) as float) as GKn,
    ant_tip.Ime as TipAntene,
    bb_tip.Ime,
	lokbb.ImeBSC as BSC_BB,
	lokrr.ImeBSC as BSC_RU

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpBBunitTip bb_tip on bb.PbpBBunitTipID = bb_tip.PbpBBunitTipID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
where celica.Delujoca = 1 and lokrr.Aktivna = 1"""

celice_pwas = """
select distinct
	lokrr.ImeBSC,
	celica.ime as celica,
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 700' then 700
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
	       when sis.ime = 'NR 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='NR 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
           when sis.ime ='NR 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900' 
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
			when sis.ime ='NR 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='NR 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='NR 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
			when sis.ime ='NR 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
			end as fband,    
		case when CHARINDEX('TDD', sis.ime) != 0 then 'TDD' else 'FDD' end as duplex,
	case when ant.azimut is null then ant.Azimut_P
    else cast(ant.azimut as int) end as azimut,
	case when ant.nagib is null then ant.Nagib_P
    else ant.nagib end as nagib,
	case when ant_vh.ET is null then ant_vh.ET_p
    else ant_vh.ET end as ET,
    case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as Visina,
	convert(varchar, ant.AntenaID) as AntenaID,
    ant_tip.dobitek,
	case 
	when tant.Ime = 'Zunanja' then 'Outdoor'
	when tant.Ime = 'Notranja' then 'Indoor'
	else 'Tunnel' end							as Type,
    tip_ant_vh.oznaka,
    tip_ant_vh.ETdo,
    tip_ant_vh.ETod,
	rru.LokacijaID as rru_lokacija,
	kabin.LokacijaID as bbu_lokacija_id,
    lokrr.ImeBSC as rru_ime,
    cast(round(lokrr.GKe,0) as int) as ZSirina,
    cast(round(lokrr.GKn,0) as int) as ZVisina,
	lokbb.ImeBSC as bb_ime,

    lokbb.Ime as IIme,
	ant_tip.Kot as beamwidth,
	lokbb.Posta as posta

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID"""


atoll_txt_to_grd  = """select distinct
        lokbb.ImeBSC,
        celica.ime as celica,
        celica.CelicaID, 
        convert(varchar, ant.AntenaID) as AntenaID,
		cast(celica.ime as varchar) + '~' +  cast(celica.CelicaID as varchar) + '~' + convert(varchar, ant.AntenaID)  rbs,
        celica.Delujoca,
        concat('RBS-',substring(celica.Ime,1, LEN(celica.ime)-1)) celica_rbs,
        sis.Ime,
        ant.ZSirina,
		concat(cast(ant.ZSirina as int), '°') as stopinje_sir,
		concat(cast(60 * (ant.ZSirina - cast(ant.ZSirina as int)) as int),'''') as minut_sir,
		concat(round(60*(60 * (ant.ZSirina - cast(ant.ZSirina as int)) - cast(60 * (ant.ZSirina - cast(ant.ZSirina as int)) as int)),2),'"') as sek_sir ,
		concat(concat(cast(ant.ZSirina as int), '°'),
		concat(cast(60 * (ant.ZSirina - cast(ant.ZSirina as int)) as int),''''),
		concat(round(60*(60 * (ant.ZSirina - cast(ant.ZSirina as int)) - cast(60 * (ant.ZSirina - cast(ant.ZSirina as int)) as int)),2),'**'), 'E') lon,
        ant.ZVisina,
		concat(cast(ant.ZVisina as int), '°') as stopinje_vis,
		concat(cast(60 * (ant.ZVisina - cast(ant.ZVisina as int)) as int),'''') as minut_vis,
		concat(round(60*(60 * (ant.ZVisina - cast(ant.ZVisina as int)) - cast(60 * (ant.ZVisina - cast(ant.ZVisina as int)) as int)),2),'"') as sek_vis,
		concat(concat(cast(ant.ZVisina as int), '°'),
		concat(cast(60 * (ant.ZVisina - cast(ant.ZVisina as int)) as int),''''),
		concat(round(60*(60 * (ant.ZVisina - cast(ant.ZVisina as int)) - cast(60 * (ant.ZVisina - cast(ant.ZVisina as int)) as int)),2),'**'), 'N') as lat,
        ant.GKn, ant.GKe

    from SQLBazne.dbo.PbpBBRUCelica crcel
    inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
    inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
    inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
    inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
    inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
    inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
    inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
    inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
    inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
    inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
    --inner join atoll_prod.dbo.vATOLL_Cell va on va.antenaID = ant.AntenaID and celica.Ime = va.Celica_Ime
    inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
    inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
    where ant.GKn < ant.GKe
    order by celica.ime"""

indoor_celice = """select distinct
	lokbb.ImeBSC as bb_lokacija,
	lokrr.ImeBSC as rr_lokacija,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	
    ant_tip.Ime as TipAntene, 
	convert(varchar, ant.AntenaID) as AntenaID,
	case when bb_tip.Ime like '%icro%'  then 'Micro'
    when bb_tip.Ime like  '%ico%' then 'Pico'
	else 'Indoor' end as celicnost,
	case when ant_tip.Ime like '%span%'  then 'Airspan'
	when ant_tip.Ime like '%uawei%' then 'Huawei'
	else 'Ericsson' end as vendor


from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpBBunitTip bb_tip on bb_tip.PbpBBunitTipID = bb.PbpBBunitTipID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpRUunitTip rru_tip on rru_tip.PbpRUunitTipID= rru.PbpRUunitTipID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
where tant.Ime = 'Notranja' and celica.Delujoca = 1 
"""

das_celice = """
with tab1 as (
select lok.LokacijaID, lok.ImeBSC as rr_lokacija, ant_tip.Ime as TipAntene,  ind_ant.Stevilo as Stevilo 
from SQLBazne.dbo.PIndoorLokacija lok_ind
inner join SQLBazne.dbo.Lokacija lok on lok.LokacijaID = lok_ind.LokacijaID

inner join SQLBazne.dbo.PIndoorAntena ind_ant on ind_ant.LokacijaID = lok_ind.LokacijaID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = ind_ant.TipAnteneID
where lok.ImeBSC is not null
),
tab2 as (select lok_ind.LokacijaID,  
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	end as tehn from SQLBazne.dbo.PIndoorLokacija lok_ind
inner join SQLBazne.dbo.PIndoorParametri ind_par on ind_par.LokacijaID = lok_ind.LokacijaID
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = ind_par.SistemID
where sis.GenSistemID != 4)
select  tab1.rr_lokacija, tab1.TipAntene, tab1.Stevilo, tab2.tehn from tab1
inner join tab2 on tab1.LokacijaID = tab2.LokacijaID
"""

akos_podatki = """with tab1 as (
select distinct
	celica.ime as ID,
	lokrr.ImeBSC as IDLokacije,
	lokrr.Ime as "Ime Lokacije",
	lokrr.Posta as "Postna stevilka",
	lokrr.ZSirina as ZD,
	lokrr.ZVisina as ZS,
    tip_ant_vh.gain as GAIN,
	case when ant.azimut is null then ant.Azimut_P
    else cast(ant.azimut as int) end as "Smer antene",
	case when ant.nagib is null then ant.Nagib_P
	else ant.nagib end as nagib,
	case when ant_vh.ET is null then ant_vh.ET_p
    else ant_vh.ET end as ET,
	case when ant.Visina is null and ant.Visina_P = 0 then 1
	when ant.Visina is null then ant.Visina_P
	when ant.Visina = 0 then 1
    else ant.Visina end as "h-ant",
	tip_ant_vh.BeamWidth as "H_sirina",
	tip_ant_vh.BeamHeight as "V_sirina",
	ant_tip.Ime as "Oznaka antene",
	ant.Indoor ,

	
	celica.Delujoca,
	sis.Ime,
	case when sis.GenSistemID = 2 THEN 'GSM'
	  when sis.GenSistemID = 4 THEN 'UMTS'
	  when sis.GenSistemID = 11 THEN 'LTE'
	  when sis.GenSistemID = 12 THEN '5G'
	  end as tehn,
	  case when sis.ime = '5G 2600/2700' then 2600
	       when sis.ime = 'NR 2600/2700' then 2600
		   when sis.ime ='5G 3500' then 3500
		   when sis.ime ='NR 3500' then 3500
		   when sis.ime ='5G 700' then 700
           when sis.ime ='NR 700' then 700
		   when sis.ime ='GSM 1800' then 1800
		   when	sis.ime ='GSM 900' then 900
		   when sis.ime ='LTE 1800' then 1800
		   when sis.ime ='LTE 2100' then 2100
		   when sis.ime ='LTE 2600' then 2600
		   when	sis.ime ='LTE 2600 TDD' then 2600
			when sis.ime ='LTE 3500' then 3500
			when sis.ime ='LTE 3500 TDD' then 3500
			when sis.ime ='LTE 700' then 700
			when sis.ime ='LTE 800' then 800
			when sis.ime ='LTE 900' then 900
			when sis.ime ='UMTS' then 2100
			when sis.ime ='UMTS 900' then 900
			when sis.ime ='NR 700' then 700
			when sis.ime ='NR 800' then 800
			when sis.ime ='NR 900' then 900
			when sis.ime ='NR 1800' then 1800
			when sis.ime ='NR 2100' then 2100
            when sis.ime ='NR 1500' then 1500
            when sis.ime ='5G 1500' then 1500
			end as frekvenca,
    case when sis.ime = '5G 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
	       when sis.ime = 'NR 2600/2700' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when sis.ime ='5G 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='NR 3500' then 'n78 (3300 MHz)'
		   when sis.ime ='5G 700' then 'n28 / E-UTRA 28 (700 MHz)'
           when sis.ime ='NR 700' then 'n28 / E-UTRA 28 (700 MHz)'
		   when sis.ime ='GSM 1800' then 'GSM 1800'
		   when	sis.ime ='GSM 900' then 'GSM 900' 
		   when sis.ime ='LTE 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
		   when sis.ime ='LTE 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
		   when sis.ime ='LTE 2600' then 'n7 / E-UTRA 7 (2600 MHz)'
		   when	sis.ime ='LTE 2600 TDD' then 'n38 / E-UTRA 38'
			when sis.ime ='LTE 3500' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 3500 TDD' then 'n42 / E-UTRA 42'
			when sis.ime ='LTE 700' then 'n28 / E-UTRA 28 (700 MHz)'
			when sis.ime ='LTE 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='LTE 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='UMTS' then 'UTRA Band I'
			when sis.ime ='UMTS 900' then 'UTRA Band VIII'
			when sis.ime ='NR 800' then 'n20 / E-UTRA 20 (800 MHz)'
			when sis.ime ='NR 900' then 'n8 / E-UTRA 8 (900 MHz)'
			when sis.ime ='NR 1800' then 'n3 / E-UTRA 3 (1800 MHz)'
			when sis.ime ='NR 2100' then 'n1 / E-UTRA 1 (2100 MHz)'
            when sis.ime ='NR 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            when sis.ime ='5G 1500' then 'n75 / E-UTRA 75 (1500 MHz)'
            
			end as fband
		

from SQLBazne.dbo.PbpBBRUCelica crcel
inner join SQLBazne.dbo.PbpBBunitList bb on bb.PbpBBunitListID = crcel.PbpBBunitListID
inner join SQLBazne.dbo.PbpKabinetList kabin on kabin.PbpKabinetListID = bb.PbpKabinetListID
inner join SQLBazne.dbo.PbpRUunitList rru on rru.PbpRUunitListID = crcel.PbpRUunitListID
inner join SQLBazne.dbo.PbpAntenaVhod ant_vh on ant_vh.PbpAntenaVhodID = crcel.PbpAntenaVhodID
inner join SQLBazne.dbo.PbpTipAntenaVhod tip_ant_vh on tip_ant_vh.PbpTipAntenaVhodID = ant_vh.PbpTipAntenaVhodID
inner join SQLBazne.dbo.TipAntene ant_tip on ant_tip.TipAnteneID = tip_ant_vh.TipAnteneID
inner join SQLBazne.dbo.Lokacija lokbb on lokbb.LokacijaID = kabin.LokacijaID
inner join SQLBazne.dbo.Lokacija lokrr on lokrr.LokacijaID = rru.LokacijaID
inner join SQLBazne.dbo.Celica celica on celica.CelicaID = crcel.CelicaID
inner join SQLBazne.dbo.Antena ant on ant.AntenaID = ant_vh.AntenaID
inner join SQLBazne.dbo.Sistem sis on sis.SistemID = celica.SistemID
inner join SQLBazne.dbo.TipIzvedbeAntene tant on tant.TipIzvedbeAnteneID = ant.Indoor
)
select distinct tab1.*, nagib + ET as "Naklon antene"
from tab1"""

