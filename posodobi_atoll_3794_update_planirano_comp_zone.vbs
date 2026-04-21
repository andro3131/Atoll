' -----------------------------------------------------------------------------------------------------------------------
' Constant definitions
Const yes				= True
Const atoInformation 	= 0		' Display Information Message icon
Const atoEQ = 0



' -----------------------------------------------------------------------------------------------------------------------
' Constant definitions
Const no									= False
Const allTheTableContent 					= False
Const coverageByTx_Template 				= "{A6FB7132-FB5E-42cc-A1C1-0BEA4AF09921}"
Const coverageBySL_Template 				= "{1FF20277-9A4C-486A-B0A4-90E7E8EC72E4}"

Const coverageBySL_Template_gsm 			= "{1FF20277-9A4C-486A-B0A4-90E7E8EC72E4}"
Const coverageBySL_Template_umts 			= "{E82C3B13-240E-4DD3-A553-583ADDF57713}"
Const coverageBySL_Template_lte				= "{9C602E1C-E5E7-44CA-8E5B-878D74D07885}"

Const waitUntilTheCalculationsFinish 		= True
Const recalculateAllThePathLossMatrices 	= False
Const allTheServers							= 0
Const bestServer							= 0
Const SID_PREDICTIONS                       = "{DA676EF0-E300-4AFF-BBFA-EC55D3798E4F}"


' -----------------------------------------------------------------------------------------------------------------------
' Public Variables declaration used in the Script
Dim objAtoll			' Atoll Application
Dim objDocument 		' Atoll Document
Dim objShell			' Windows Shell
Dim objNetwork 			' Windows Network
Dim objFs			' Windows File System
Dim dat				' ATL File
Dim objDocumentAtoll
Dim WshShell, colProcessList, objProcess, vFound

On Error Resume Next

'Set objShell 		= WScript.CreateObject ("WScript.Shell")
Set objNetwork 		= WScript.CreateObject("WScript.Network")
Set objFs 			= WScript.CreateObject("Scripting.FileSystemObject")
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3912_2.ATL") 
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794.ATL")
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Atoll_exporti_3794_test_atoll_3_5_1.ATL")
dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794_3_5_1.ATL")



' -----------------------------------------------------------------------------------------------------------------------
' Preveri, če je atoll vključen.  Če ni, ga vključi - ZAČETEK

Set colProcessList = GetObject("Winmgmts:").ExecQuery ("Select * from Win32_Process")
For Each objProcess in colProcessList
	If objProcess.Name = "Atoll.exe" Then
		vFound = True
	End If
Next
' If vFound = True Then
	' Set objAtoll 	= GetObject(, "Atoll.Application")
	' If objAtoll.ActiveDocument.Name = "Atoll_exporti_3912_API" Then
			' Set objDocumentAtoll = objAtoll.ActiveDocument
		' Else
			' Set objDocumentAtoll = objAtoll.Documents.Open(dat)	
		' End If
' Else
	' Set objAtoll 	= GetObject("", "Atoll.Application")
	' Set objDocumentAtoll = objAtoll.Documents.Open(dat)
' End If

Set objAtoll 	= GetObject("", "Atoll.Application")
Set objDocumentAtoll = objAtoll.Documents.Open(dat)

objAtoll.Visible 	= no


' -----------------------------------------------------------------------------------------------------------------------
' Preveri, če je atoll vključen.  Če ni, ga vključi - KONEC

Dim strPath_novo, strPath_spremeni, strPath_brisi, str_Path_filter
Dim objFSO
Dim objFolder_novo, objFolder_spremeni, objFolder_brisi
Dim objFile
Dim datoteka
Dim f, file
Dim tabela_brisi, tabela_novo, tabela_spremeni
Dim iRow
Dim cs
Dim m
Dim ime
Dim sites
Dim f1, file1, f2, file2, f3, file3, f4, file4
Dim gtrans, utrans, xgtrans
Dim xgcellsnbiot
Dim xgcellslte
Dim i
Dim transmitters
Dim predictions
Dim coverageByTransmitter	' A coverage by transmitter
Dim coverageBySignalLevel	' A coverage by Signal Level
Dim prediction1				' A prediction within the Prediction's Folder
Dim prediction2				' A prediction within the Prediction's Folder
Dim objProjection

' On Error Resume Next

objDocumentAtoll.Refresh
If Err.Number <> 0 Then
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

Set cs = objDocumentAtoll.GetRecords("coordsys", True)

strPath_novo = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Novo\"
strPath_spremeni = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Spremeni\"
strPath_brisi = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Brisi\"
str_Path_filter1 = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_sites.txt"
str_Path_filter2 = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_trans.txt"
str_Path_filter3 = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\trans_teh.txt"
str_Path_filter4 = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\zone.txt"
odlozisce = "G:\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Export_planirane_celice\"


Set objFso 			= WScript.CreateObject("Scripting.FileSystemObject")
Set objProjection 	= objDocumentAtoll.CoordSystemProjection
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objFolder_novo = objFSO.GetFolder(strPath_novo)
Set objFolder_spremeni = objFSO.GetFolder(strPath_spremeni)
Set objFolder_brisi = objFSO.GetFolder(strPath_brisi)
Set f1 = objFSO.OpenTextFile(str_Path_filter1,1)
Set f2 = objFSO.OpenTextFile(str_Path_filter2,1)
Set f3 = objFSO.OpenTextFile(str_Path_filter3,1)
Set f4 = objFSO.OpenTextFile(str_Path_filter4,1)
file1 = f1.ReadAll
file2 = f2.ReadAll
file3 = f3.ReadAll
file4 = f4.ReadAll

Public Function Vrstice(datoteka)
	Dim i
	Dim vrst
	vrst = 0
	For i = 1 to len(datoteka)
		If Mid(datoteka,i,1) = vbLf Then
			vrst = vrst+1
		End If
	Next
	Vrstice = vrst
End Function

Public Function Stolpci(datoteka)
	Dim i
	Dim stolp
	stolp = 0
	For i = 1 to len(datoteka)
		If Mid(datoteka,i,1) = ";" Then
			stolp = stolp+1
		End If
	Next
	Stolpci = stolp/Vrstice(datoteka)
End Function

' Pobriši potencialne filtre

Set sites = objDocumentAtoll.GetRecords("sites", False)
Set gtrans = objDocumentAtoll.GetRecords("gtransmitters", False)
Set xgtrans = objDocumentAtoll.GetRecords("xgtransmitters", False)
Set xgcellsnbiot = objDocumentAtoll.GetRecords("xgcellsnbiot", False)
Set xgcellslte = objDocumentAtoll.GetRecords("xgcellslte", False)
sites.Filter = file1
gtrans.Filter = file2
xgtrans.Filter = file2



' Brisi

For Each objFile In objFolder_brisi.Files
	If InStr(objFile.Name, "__NE_BRISI__") = 0 Then
		ime = objFile.Name
		' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' If Err.Number <> 0 Then
		  ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' WScript.Echo "Error in set tabela_brisi: " & Err.Description
		  ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' Err.Clear
		' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' End If
		'Atoll.LogMessage ime
		'Atoll.LogMessage objFile
		tabela = split(split(objFile.Name, "_")(1),".")(0)
		Atoll.LogMessage "Ime  tabele brisi: " & tabela
		Set f = objFSO.OpenTextFile(objFile,1)
		file = f.ReadAll
		f.Close
		Set f = Nothing
		vr = Vrstice(file)
		'st = Stolpci(file)
		If vr > 0 then 
			Set tabela_brisi = objDocumentAtoll.GetRecords(tabela, True)
			atribut = split(file, vbCrLf)(0)
			For i=1 To Vrstice(file)-1
				transmitter_name = split(file, vbCrLf)(i)
				iRow = tabela_brisi.Find(1, atribut, atoEQ, transmitter_name)
				If iRow <> -1 Then
					tabela_brisi.Delete iRow
				End If
			Atoll.LogMessage "Izbrisana vrednost " & split(file, vbCrLf)(i) & " v tabeli " & tabela
			Next
			Set tabela_brisi = Nothing
		End If
		ime  = ""
		file = ""
		vr = ""
	End If
Next
Set objFile = Nothing
objDocumentAtoll.Archive
If Err.Number <> 0 Then
	Err.Clear
End If
'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
objDocumentAtoll.Refresh
If Err.Number <> 0 Then
	Err.Clear
End If
'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop

'Spremeni

For Each objFile In objFolder_spremeni.Files
	ime = objFile.Name
	tabela = split(split(objFile.Name, "_")(1),".")(0)
	'atribut = split(split(objFile.Name, "__")(1),".")(0)
	Set f = objFSO.OpenTextFile(objFile,1)
	file = f.ReadAll
	f.Close
	Set f = Nothing
	If Err.Number <> 0 Then
	  ' WScript.Echo "file = f.ReadAll Spremeni : " & Err.Description
	  Err.Clear
	End If
	' objDocumentAtoll.LogMessage file
	pkey = Split(Split(file, vbCrLf)(0), ";")(0)
	' objDocumentAtoll.LogMessage pkey
	Set tabela_spremeni = objDocumentAtoll.GetRecords(tabela, True)	
	' objDocumentAtoll.LogMessage Vrstice(file)
	' objDocumentAtoll.LogMessage Stolpci(file)
	If Vrstice(file) > 1 Then
	    If Stolpci(file) => 1 Then
			For i = 1 to Vrstice(file)-1
				iRow = 0
				iRow = tabela_spremeni.Find(iRow, pkey, atoEQ, Split(Split(file, vbCrLf)(i), ";")(0))
				If Err.Number <> 0 Then
				  ' WScript.Echo "tabela_spremeni.Find : " & Err.Description
				  Err.Clear
				End If
				If iRow <> -1 Then
				tabela_spremeni.Edit iRow
				If Err.Number <> 0 Then
				  ' WScript.Echo "tabela_spremeni.Edit iRow : " & Err.Description
				  Err.Clear
				End If
					For j = 1 to Stolpci(file)
						If (Split(Split(file, vbCrLf)(i), ";")(j) <> "") Then
						    atribut = Split(Split(file, vbCrLf)(0), ";")(j)
							' If Err.Number <> 0 Then
							  ' WScript.Echo "atribut = Split(Split(file, vbCrLf)(0), ";")(j) : " & Err.Description
							  ' Err.Clear
							' End If
							tabela_spremeni.SetValue atribut, Split(Split(file, vbCrLf)(i), ";")(j)
							If Err.Number <> 0 Then
							  ' WScript.Echo "tabela_spremeni.SetValue " & Err.Description
							  Err.Clear
							End If
							objDocumentAtoll.LogMessage "Sprememenjena vrednost atributa " & atribut & " parametra " &  Split(Split(file, vbCrLf)(i), ";")(0) & " na vrednost " & Split(Split(file, vbCrLf)(i), ";")(j)
						End If
					Next
				tabela_spremeni.Update
				If Err.Number <> 0 Then
				  WScript.Echo "tabela_spremeni.Update " & Err.Description
				  Err.Clear
				End If
				End If
			Next
		End If
	End If
	Set tabela_spremeni = Nothing
	ime = ""
	file = ""
Next

'Novo

For Each objFile In objFolder_novo.Files
	ime = objFile.Name
	'Atoll.LogMessage ime
	'Atoll.LogMessage objFile
	tabela = split(split(objFile.Name, "_")(1),".")(0)
	' Atoll.LogMessage "Ime tabele dodamo: " & tabela
	' f = objFSO.OpenTextFile(objFile,1)
	Set f = objFSO.OpenTextFile(objFile,1)
	file = f.ReadAll
	f.Close
	Set f = Nothing
	vr = Vrstice(file)
	st = Stolpci(file)
	'Atoll.LogMessage vr
	'Atoll.LogMessage st
	If vr > 0 then 
		Set tabela_novo = objDocumentAtoll.GetRecords(tabela, True)
		For i=1 To Vrstice(file)-1
			tabela_novo.AddNew
			For j=0 To Stolpci(file)
				tabela_novo.SetValue split(split(file, vbCrLf)(0),";")(j) , split(split(file, vbCrLf)(i),";")(j)
				If Err.Number <> 0 Then
				  Err.Clear
				End If
				' If Err Then
					' Atoll.LogMessage Err.Description
				'Else
					'Atoll.LogMessage "Uspeh, Bravo!!!"
				' End If
			Next
		tabela_novo.Update
		If Err.Number <> 0 Then
		  WScript.Echo "tabela_novo.Update : " & Err.Description
		  Err.Clear
		End If
		Atoll.LogMessage "Dodana vrstica " & split(file, vbCrLf)(i) & " v tabeli " & tabela
		Next
		' Atoll.LogMessage "Stevilo dodanih elementov: " & Vrstice(file)-1
		'Atoll.LogMessage MyFunction(10)
	End If
	Set tabela_novo = Nothing
	ime  = ""
	file = ""
Next
Set objFile = Nothing



' objDocumentAtoll.LogMessage "Update podatkov koncan!"
objDocumentAtoll.RunPathloss TRUE, FALSE
If Err.Number <> 0 Then
  ' WScript.Echo "Archive konec dokumenta " & Err.Description
  Err.Clear
End If
'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
If Err.Number <> 0 Then
  ' WScript.Echo "Do While objDocumentAtoll.HasRunningTask Archieve " & Err.Description
  Err.Clear
End If



objDocumentAtoll.Close 1
If Err.Number <> 0 Then
  WScript.Echo "objDocumentAtoll.Quit konec dokumenta " & Err.Description
  Err.Clear
End If
Set objDocumentAtoll = Nothing
objAtoll.Quit
Set objAtoll = Nothing

