' -----------------------------------------------------------------------------------------------------------------------
' Constant definitions
Const yes				= True
Const atoInformation 	= 0		' Display Information Message icon
Const atoEQ = 0
Public Const SID_PREDICTIONS = "{DA676EF0-E300-4AFF-BBFA-EC55D3798E4F}"
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
Dim SharedOutputFolder
Dim log1

On Error Resume Next

Set objShell 		= WScript.CreateObject ("WScript.Shell")
Set objNetwork 		= WScript.CreateObject("WScript.Network")
Set objFs 			= WScript.CreateObject("Scripting.FileSystemObject")
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3912_2.ATL") 
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794.ATL")
' dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Atoll_exporti_3794_test_atoll_3_5_1.ATL")
dat = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_exporti_3794_3_5_1.ATL")

SharedOutputFolder = "G:\Atoll_dokumenti\Dokument_exporti\SharedPathlossData\"

Set log1 = objFs.OpenTextFile("G:\Avtomatika\log\Atoll_import_vbs_log.txt", 8, True)
' -----------------------------------------------------------------------------------------------------------------------
' Preveri, če je atoll vključen.  Če ni, ga vključi - ZAČETEK

Set colProcessList = GetObject("Winmgmts:").ExecQuery ("Select * from Win32_Process")

If Err.Number <> 0 Then
	log1.WriteLine Now & " – ERROR Set colProcessList " & Err.Number & ": " & Err.Description
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

' For Each objProcess in colProcessList
	' If objProcess.Name = "objAtoll.exe" Then
		' vFound = True
	' End If
' Next



Set objAtoll 	= GetObject("", "Atoll.Application")
If Err.Number <> 0 Then
	log1.WriteLine Now & " – ERROR Set objAtoll " & Err.Number & ": " & Err.Description
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

Set objDocumentAtoll = objAtoll.Documents.Open(dat)
If Err.Number <> 0 Then
	log1.WriteLine Now & " – ERROR Set objDocumentAtoll " & Err.Number & ": " & Err.Description
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

objAtoll.Visible 	= True
If Err.Number <> 0 Then
	log1.WriteLine Now & " – ERROR objAtoll.Visible " & Err.Number & ": " & Err.Description
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

log1.Close
' -----------------------------------------------------------------------------------------------------------------------
' Preveri, če je atoll vključen.  Če ni, ga vključi - KONEC

Dim strPath_novo, strPath_spremeni, strPath_brisi
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
Dim gtrans, xgtrans, utrans, sites
Dim log

' On Error Resume Next
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set log = objFSO.OpenTextFile("G:\Avtomatika\log\Atoll_import_vbs_log.txt", 8, True)

objDocumentAtoll.Refresh
If Err.Number <> 0 Then
	log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

Set cs = objDocumentAtoll.GetRecords("coordsys", True)
If cs.GetValue(1,"CODE") = 3912 Then
	strPath_novo = "G:\Avtomatika\EPSG_3912\Novo\"
	strPath_spremeni = "G:\Avtomatika\EPSG_3912\Spremeni\"
	strPath_brisi = "G:\Avtomatika\EPSG_3912\Brisi\"
Elseif cs.GetValue(1,"CODE") = 3794 Then
	strPath_novo = "G:\Avtomatika\EPSG_3794\Novo\"
	strPath_spremeni = "G:\Avtomatika\EPSG_3794\Spremeni\"
	strPath_brisi = "G:\Avtomatika\EPSG_3794\Brisi\"
Elseif cs.GetValue(1,"CODE") = 4326 Then
	strPath_novo = "G:\Avtomatika\WGS84\Novo\"
	strPath_spremeni = "G:\Avtomatika\WGS84\Spremeni\Atributi\"
	strPath_brisi = "G:\Avtomatika\WGS84\Brisi\"
End If

Set cs = Nothing


Set objFolder_novo = objFSO.GetFolder(strPath_novo)
Set objFolder_spremeni = objFSO.GetFolder(strPath_spremeni)
Set objFolder_brisi = objFSO.GetFolder(strPath_brisi)
Set m = objFSO.OpenTextFile("G:\Avtomatika\Eksport\fajl.txt", 1)

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
Set utrans = objDocumentAtoll.GetRecords("utransmitters", False)
Set xgtrans = objDocumentAtoll.GetRecords("xgtransmitters", False)
sites.Filter = ""
gtrans.Filter = ""
utrans.Filter = ""
xgtrans.Filter = ""

' Set gtrans = Nothing
' Set xgtrans = Nothing
' Set utrans = Nothing
objAtoll.LogMessage "*** Število tabel po mapah***"
objAtoll.LogMessage "Brisanje " & objFolder_brisi.Files.Count
objAtoll.LogMessage "Spremeni " & objFolder_spremeni.Files.Count
objAtoll.LogMessage "Novo " & objFolder_novo.Files.Count
objAtoll.LogMessage "*********************"


' Brisi

If objFolder_brisi.Files.Count > 0 Then
	For Each objFile In objFolder_brisi.Files
		objAtoll.LogMessage InStr(objFile.Name, "__NE_BRISI__")
		If InStr(objFile.Name, "__NE_BRISI__") = 0 Then
			ime = objFile.Name
			' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' If Err.Number <> 0 Then
			  ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' WScript.Echo "Error in set tabela_brisi: " & Err.Description
			  ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' Err.Clear
			' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' ' End If
			objAtoll.LogMessage ime
			objAtoll.LogMessage objFile
			tabela = split(split(objFile.Name, "_")(1),".")(0)
			objAtoll.LogMessage "Ime  tabele brisi: " & tabela
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
				objAtoll.LogMessage "Izbrisana vrednost " & split(file, vbCrLf)(i) & " v tabeli " & tabela
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
		log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
		Err.Clear
	End If
	'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
	objDocumentAtoll.Refresh
	If Err.Number <> 0 Then
		log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
		Err.Clear
	End If
	'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
End If


'Spremeni

If objFolder_spremeni.Files.Count > 0 Then
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
						log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
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
									log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
								  ' WScript.Echo "tabela_spremeni.SetValue " & Err.Description
								  Err.Clear
								End If
								objDocumentAtoll.LogMessage "Sprememenjena vrednost atributa " & atribut & " parametra " &  Split(Split(file, vbCrLf)(i), ";")(0) & " na vrednost " & Split(Split(file, vbCrLf)(i), ";")(j)
							End If
						Next
					tabela_spremeni.Update
					If Err.Number <> 0 Then
						log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
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
End If

'Novo

If objFolder_novo.Files.Count > 0 Then
	For Each objFile In objFolder_novo.Files
		ime = objFile.Name
		'objAtoll.LogMessage ime
		'objAtoll.LogMessage objFile
		tabela = split(split(objFile.Name, "_")(1),".")(0)
		' objAtoll.LogMessage "Ime tabele dodamo: " & tabela
		' f = objFSO.OpenTextFile(objFile,1)
		Set f = objFSO.OpenTextFile(objFile,1)
		file = f.ReadAll
		f.Close
		Set f = Nothing
		vr = Vrstice(file)
		st = Stolpci(file)
		'objAtoll.LogMessage vr
		'objAtoll.LogMessage st
		If vr > 0 then 
			Set tabela_novo = objDocumentAtoll.GetRecords(tabela, True)
			For i=1 To Vrstice(file)-1
				tabela_novo.AddNew
				For j=0 To Stolpci(file)
					tabela_novo.SetValue split(split(file, vbCrLf)(0),";")(j) , split(split(file, vbCrLf)(i),";")(j)
					If Err.Number <> 0 Then
						log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
						Err.Clear
					End If
					' If Err Then
						' objAtoll.LogMessage Err.Description
					'Else
						'objAtoll.LogMessage "Uspeh, Bravo!!!"
					' End If
				Next
			tabela_novo.Update
			If Err.Number <> 0 Then
				WScript.Echo "tabela_novo.Update : " & Err.Description
				log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
				Err.Clear
			End If
			objAtoll.LogMessage "Dodana vrstica " & split(file, vbCrLf)(i) & " v tabeli " & tabela
			Next
			' objAtoll.LogMessage "Stevilo dodanih elementov: " & Vrstice(file)-1
			'objAtoll.LogMessage MyFunction(10)
		End If
		Set tabela_novo = Nothing
		ime  = ""
		file = ""
	Next
	Set objFile = Nothing
End If


gtrans.Filter = "([ACTIVE]=True)"
utrans.Filter = "([TX_ID]=AAAAAAAAAAAAA)"
xgtrans.Filter = "([ACTIVE]=True)"




' Za nočno kalkulacijo postavimo v prvat pathloss folder naš sharan folder. Po izračunu pathloss-ov vrnemo stanje v prvotno. Priporočilo Forsk-a

Dim item1
Dim sharedPathLossFolder
Dim privat 
Dim networksTable

Set item1 = objDocumentAtoll.GetRootFolder(0).Item(SID_PREDICTIONS)
privat = item1.GetProperty("PrivateStorage")
Set networksTable = objDocumentAtoll.GetRecords("Networks", True)
For i = 1 to networksTable.columnCount
  If (networksTable.GetValue (0,i) = "SHARED_RESULTS_FOLDER") Then
	 sharedPathLossFolder = networksTable.GetValue(1, i)
	 networksTable.Edit(i)
	 networksTable.SetValue "SHARED_RESULTS_FOLDER", ""
	 networksTable.Update

  End If
Next
item1.SetProperty "PrivateStorage", sharedPathLossFolder




' objDocumentAtoll.LogMessage "Update podatkov koncan!"
objDocumentAtoll.RunPathloss TRUE, FALSE
If Err.Number <> 0 Then
	log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
  ' WScript.Echo "Archive konec dokumenta " & Err.Description
  Err.Clear
End If
'"Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
If Err.Number <> 0 Then
	log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
  ' WScript.Echo "Do While objDocumentAtoll.HasRunningTask Archieve " & Err.Description
  Err.Clear
End If



For i = 1 to networksTable.columnCount
  If (networksTable.GetValue (0,i) = "SHARED_RESULTS_FOLDER") Then
	 networksTable.Edit(i)
	 networksTable.SetValue "SHARED_RESULTS_FOLDER", sharedPathLossFolder
	 networksTable.Update
  End If
Next
item1.SetProperty "PrivateStorage", privat


Set item1 = Nothing
Set sharedPathLossFolder = Nothing
Set privat  = Nothing
Set networksTable = Nothing



objDocumentAtoll.Archive
' objDocumentAtoll.LogMessage AtoArchiveStatus
If Err.Number <> 0 Then
  ' WScript.Echo "objDocumentAtoll.RunPathloss konec dokumenta " & Err.Description
  Err.Clear
End If
' ' "Wait" Loop
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
If Err.Number <> 0 Then
  ' WScript.Echo "objDocumentAtoll.RunPathloss konec dokumenta " & Err.Description
  Err.Clear
End If



Set gtrans = Nothing
Set xgtrans = Nothing
Set utrans = Nothing
Set objFSO = Nothing
Set sites = Nothing




objDocumentAtoll.Close 1
If Err.Number <> 0 Then
	log.WriteLine Now & " – ERROR " & Err.Number & ": " & Err.Description
	WScript.Echo "objDocumentAtoll.Quit konec dokumenta " & Err.Description
	Err.Clear
End If
log.Close
Set objDocumentAtoll = Nothing
m = Nothing
objAtoll.Quit
Set objAtoll = Nothing
'objShell.Run "taskkill /F /IM atoll.exe", 0, True
