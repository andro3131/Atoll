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
dat = objFs.GetAbsolutePathName("D:\Atoll_projects_planer01\Atoll_exporti_3794_3_5_1.ATL")



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
Dim f1, file1, f2, file2, f3, file3, f4, file4, f5, file5
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

' objDocumentAtoll.Refresh
If Err.Number <> 0 Then
  ' WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
  Err.Clear
End If

Set cs = objDocumentAtoll.GetRecords("coordsys", True)

strPath_novo = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Novo\"
strPath_spremeni = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Spremeni\"
strPath_brisi = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Brisi\"
str_Path_filter1 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_sites.txt"
str_Path_filter2 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\filter_trans.txt"
str_Path_filter3 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\trans_teh.txt"
str_Path_filter4 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\zone.txt"
str_Path_filter5 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\trans_teh_filter.txt"
odlozisce = "D:\Atoll_projects_planer01\Avtomatika\Eksport\Planirane_celice\Update_planirane_celice\Export_planirane_celice\"


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
Set f5 = objFSO.OpenTextFile(str_Path_filter5,1)
file1 = f1.ReadAll
file2 = f2.ReadAll 
file3 = f3.ReadAll
file4 = f4.ReadAll
file5 = f5.ReadAll

objAtoll.LogMessage "test"
objAtoll.LogMessage file5

Set sites = objDocumentAtoll.GetRecords("sites", False)
Set gtrans = objDocumentAtoll.GetRecords("gtransmitters", False)
Set xgtrans = objDocumentAtoll.GetRecords("xgtransmitters", False)
Set utrans = objDocumentAtoll.GetRecords("utransmitters", False)

sites.Filter = file4
xgtrans.Filter = ""
gtrans.Filter = ""
utrans.Filter = "([TX_ID]= IIIII)"
' xgtrans.Filter = file5
' gtrans.Filter = file5
' objAtoll.LogMessage "test1"

If InStr(file5,"[RAT_]") > 0 Then
	xgtrans.Filter = file5
	gtrans.Filter = "([TX_ID]= IIIII)"
ElseIf InStr(file5,"GSM") > 0 Then
	xgtrans.Filter = "([TX_ID]= IIIII)"
	gtrans.Filter = file5
End If

' If file5 = "([RAT_]= LTE) | ([RAT_]= LTE;NB-IoT)" Then
	' xgtrans.Filter = file5
	' gtrans.Filter = "([TX_ID]= IIIII)"
' ElseIf  file5 = "([RAT_]= LTE;NB-IoT)"  Then
	' xgtrans.Filter = file5
	' gtrans.Filter = "([TX_ID]= IIIII)"
' ElseIf file5 = "([RAT_]= 5G NR)" Then
	' xgtrans.Filter = file5
	' gtrans.Filter = "([TX_ID]= IIIII)"
' ElseIf file5 ="([RAT_]= LTE)" Then
	' xgtrans.Filter = file5
	' gtrans.Filter = "([TX_ID]= IIIII)"
' ElseIf file5 = "([FBAND]= GSM 1800) | ([FBAND]= GSM 900)" Then
	' xgtrans.Filter = "([TX_ID]= IIIII)"
	' gtrans.Filter = file5
' End If

' objDocumentAtoll.Refresh   ' ZAKOMENTIRANO - povleci kolega's G:\ poti iz SQL archive nazaj v dokument
objDocumentAtoll.Close 1
If Err.Number <> 0 Then
  WScript.Echo "objDocumentAtoll.Quit konec dokumenta " & Err.Description
  Err.Clear
End If
Set objDocumentAtoll = Nothing
objAtoll.Quit
Set objAtoll = Nothing

