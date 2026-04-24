' -----------------------------------------------------------------------------------------------------------------------
' Constant definitions
Const yes				= True
Const atoInformation 	= 0		' Display Information Message icon
Const atoEQ = 0

' -----------------------------------------------------------------------------------------------------------------------
' Public Variables declaration used in the Script
Dim objAtoll			' Atoll Application
' Dim objDocument 		' Atoll Document
Dim objShell			' Windows Shell
Dim objNetwork 			' Windows Network
Dim objFs			' Windows File System
Dim dat, dat_nbiot				' ATL File
Dim objDocumentAtoll
Dim WshShell, colProcessList, objProcess, vFound

Dim objFSO			' Windows File System
Dim str_Path_filter_2
Dim f2, file2

On Error Resume Next

'Set WshShell = WScript.CreateObject ("WScript.Shell")
Set objNetwork 		= WScript.CreateObject("WScript.Network")
Set objFs 			= WScript.CreateObject("Scripting.FileSystemObject")
dat = objFs.GetAbsolutePathName("D:\Atoll_projects_planer01\Atoll_exporti_3794_3_5_1.ATL") 
dat_nbiot = objFs.GetAbsolutePathName("G:\Atoll_dokumenti\Dokument_exporti\Atoll_3794_v3_5_1_NBIOT.ATL") 

Set colProcessList = GetObject("Winmgmts:").ExecQuery ("Select * from Win32_Process")
For Each objProcess in colProcessList
	If objProcess.Name = "Atoll.exe" Then
		vFound = True
	End If
Next
' If vFound = True Then
	' Set objAtoll 	= GetObject("", "Atoll.Application")
	' objAtoll.Visible 	= no 
		' If objAtoll.ActiveDocument.Name = "Atoll_exporti_3794_3_5_1.ATL" Then
			' Set objDocumentAtoll = objAtoll.ActiveDocument
		' Else
			' Set objDocumentAtoll = objAtoll.Documents.Open(dat)	
		' End If
' Else

str_Path_filter_2 = "D:\Atoll_projects_planer01\Avtomatika\Eksport\export_zacasni_2.txt"
Set objFSO = CreateObject("Scripting.FileSystemObject")
Set f2 = objFSO.OpenTextFile(str_Path_filter_2,1)
file2 = f2.ReadAll
objDocumentAtoll.LogMessage file2

Set objAtoll 	= GetObject("", "Atoll.Application")
objAtoll.Visible 	= no 
If file2 = ("(([RAT_]= LTE;NB-IoT) & ([FBAND]= n20 / E-UTRA 20 (800 MHz)))") OR (file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n8 / E-UTRA 8 (900 MHz)))") OR (file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n3 / E-UTRA 3 (1800 MHz)))" ) Then
	Set objDocumentAtoll = objAtoll.Documents.Open(dat_nbiot)
	objDocumentAtoll.Refresh
Else
	Set objDocumentAtoll = objAtoll.Documents.Open(dat)
End If

'"Wait" Loop
Do While objDocumentAtoll.HasRunningTask
WScript.Sleep 1000
Loop

Dim gtrans, utrans, xgtrans, ssites
Dim xgcellsnbiot
Dim xgcellslte
Dim xgcells5gnr
Dim xgrepeaters_view
Dim i


Set ssites = objDocumentAtoll.GetRecords("sites", False)
Set gtrans = objDocumentAtoll.GetRecords("gtransmitters", False)
Set utrans = objDocumentAtoll.GetRecords("utransmitters", False)
Set xgtrans = objDocumentAtoll.GetRecords("xgtransmitters", False)
Set xgcellsnbiot = objDocumentAtoll.GetRecords("xgcellsnbiot", False)
Set xgcellslte = objDocumentAtoll.GetRecords("xgcellslte", False)
Set xgcells5gnr = objDocumentAtoll.GetRecords("xgcells5gnr", False)
' Set xgrepeaters_view = objDocumentAtoll.GetRecords("xgrepeaters_view", False)

' Set xgrepeaters_view = objDocumentAtoll.GetRecords("xgrepeaters_view", False)
If (InStr(file2,"GSM") > 0) Then

	ssites.Filter = ""
	gtrans.Filter = file2
	utrans.Filter = "([TX_ID] = XXXXXXXX)"
	xgtrans.Filter = "([TX_ID] = XXXXXXXX)"
	xgcellsnbiot.Filter = ""
	xgcellslte.Filter = ""
	xgcells5gnr.Filter = ""
	xgrepeaters_view.Filter = ""
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
Else
	ssites.Filter = ""
	gtrans.Filter = "([TX_ID] = XXXXXXXX)"
	utrans.Filter = "([TX_ID] = XXXXXXXX)"
	xgtrans.Filter = file2
	xgcellsnbiot.Filter = ""
	xgcellslte.Filter = ""
	xgcells5gnr.Filter = ""
	xgrepeaters_view.Filter = ""
	Do While objDocumentAtoll.HasRunningTask
	WScript.Sleep 1000
	Loop
End If

' Set xgrepeaters_view = objDocumentAtoll.GetRecords("xgrepeaters_view", False)
' If file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n20 / E-UTRA 20 (800 MHz)))"  Then
	' ' xgcellsnbiot.Filter = ""
	' ' xgcellslte.Filter = "([TX_ID] = XXXXXXXX)"
	' ' xgtrans.Filter = "([FBAND]= n20 / E-UTRA 20 (800 MHz))"
	' For i = 1 To xgtrans.RowCount
		' xgtrans.Edit i
		' 'xgtrans.setvalue "PROPAG_MODEL", "Aster L6201 4 drugic"
		' 'xgtrans.setvalue "PROPAG_MODEL2", "Aster L6201 4 drugic"
		' xgtrans.setvalue "PROPAG_MODEL", "Aster L6201 4 drugic prilagojen 3794"
		' If Len(xgtrans.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgtrans.setvalue "PROPAG_MODEL2", "Aster L6201 4 drugic prilagojen 3794"
		' End If
		' xgtrans.Update
	' Next
	' For i = 1 To xgrepeaters_view.RowCount
		' xgrepeaters_view.Edit i
		' xgrepeaters_view.setvalue "PROPAG_MODEL", "Aster L6201 4 drugic prilagojen 3794"
		' If Len(xgrepeaters_view.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgrepeaters_view.setvalue "PROPAG_MODEL2", "Aster L6201 4 drugic prilagojen 3794"
		' End If
		' xgrepeaters_view.Update
	' Next
	' objDocumentAtoll.RunPathloss FALSE, FALSE
	' If Err.Number <> 0 Then
	  ' ' WScript.Echo "Archieve konec dokumenta " & Err.Description
	  ' Err.Clear
	' End If
	' '"Wait" Loop
	' Do While objDocumentAtoll.HasRunningTask
	' WScript.Sleep 1000
	' Loop
' End If

' If file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n8 / E-UTRA 8 (900 MHz)))" Then
	' ' xgcellsnbiot.Filter = ""
	' ' xgcellslte.Filter = "([TX_ID] = XXXXXXXX)"
	' ' xgtrans.Filter = "([FBAND] = n8 / E-UTRA 8 (900 MHz))"
	' For i = 1 to xgtrans.RowCount
		' xgtrans.Edit i
		' 'xgtrans.SetValue "PROPAG_MODEL", "Aster G900 iter 4 drugic"
		' 'xgtrans.SetValue "PROPAG_MODEL2", "Aster G900 iter 4 drugic"
		' xgtrans.SetValue "PROPAG_MODEL", "Aster G900 iter 4 drugic prilagojen 3794"
		' If Len(xgtrans.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgtrans.setvalue "PROPAG_MODEL2", "Aster G900 iter 4 drugic prilagojen 3794"
		' End If
		' xgtrans.Update
	' Next
	' For i = 1 To xgrepeaters_view.RowCount
		' xgrepeaters_view.Edit i
		' xgrepeaters_view.setvalue "PROPAG_MODEL", "Aster G900 iter 4 drugic prilagojen 3794"
		' If Len(xgrepeaters_view.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgrepeaters_view.setvalue "PROPAG_MODEL2", "Aster G900 iter 4 drugic prilagojen 3794"
		' End If
		' xgrepeaters_view.Update
	' Next
	' objDocumentAtoll.RunPathloss FALSE, FALSE
	' If Err.Number <> 0 Then
	  ' ' WScript.Echo "Archieve konec dokumenta " & Err.Description
	  ' Err.Clear
	' End If
	' '"Wait" Loop
	' Do While objDocumentAtoll.HasRunningTask
	' WScript.Sleep 1000
	' Loop
' End If

' If file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n3 / E-UTRA 3 (1800 MHz)))" Then
	' ' xgcellsnbiot.Filter = ""
	' ' xgcellslte.Filter = "([TX_ID] = XXXXXXXX)"
	' ' xgtrans.Filter = "([FBAND]= n3 / E-UTRA 3 (1800 MHz))"
	' For i = 1 to xgtrans.RowCount
		' xgtrans.Edit i
		' 'xgtrans.SetValue "PROPAG_MODEL", "Aster L1657 iter 4_0 drugic"
		' 'xgtrans.SetValue "PROPAG_MODEL2", "Aster L1657 iter 4_0 drugic"
		' xgtrans.SetValue "PROPAG_MODEL", "Aster L1657 iter 4_0 drugic prilagojen 3794"
		' If Len(xgtrans.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgtrans.setvalue "PROPAG_MODEL2", "Aster L1657 iter 4_0 drugic prilagojen 3794"
		' End If
		' xgtrans.Update
	' Next
	' For i = 1 To xgrepeaters_view.RowCount
		' xgrepeaters_view.Edit i
		' xgrepeaters_view.setvalue "PROPAG_MODEL", "Aster L1657 iter 4_0 drugic prilagojen 3794"
		' If Len(xgrepeaters_view.GetValue(i, "PROPAG_MODEL2")) > 0 Then
			' xgrepeaters_view.setvalue "PROPAG_MODEL2", "Aster L1657 iter 4_0 drugic prilagojen 3794"
		' End If
		' xgrepeaters_view.Update
	' Next
	' objDocumentAtoll.RunPathloss FALSE, FALSE
	' If Err.Number <> 0 Then
	  ' ' WScript.Echo "Archieve konec dokumenta " & Err.Description
	  ' Err.Clear
	' End If
	' '"Wait" Loop
	' Do While objDocumentAtoll.HasRunningTask
	' WScript.Sleep 1000
	' Loop
' End If

If file2 = ("(([RAT_]= LTE;NB-IoT) & ([FBAND]= n20 / E-UTRA 20 (800 MHz)))") OR (file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n8 / E-UTRA 8 (900 MHz)))") OR (file2 = "(([RAT_]= LTE;NB-IoT) & ([FBAND]= n3 / E-UTRA 3 (1800 MHz)))" ) Then
	xgcellsnbiot.Filter = ""
	xgcellslte.Filter = "([TX_ID] = XXXXXXXX)"
Else
	xgcellsnbiot.Filter = "([TX_ID] = XXXXXXXX)"
	xgcellslte.Filter = ""
End If

Do While objDocumentAtoll.HasRunningTask
WScript.Sleep 1000
Loop

Set gtrans = Nothing
Set xgtrans = Nothing
Set utrans = Nothing
Set xgcellsnbiot = Nothing
Set xgcellslte = Nothing
Set xgcells5gnr = Nothing
Set xgrepeaters_view = Nothing
Set objFSO = Nothing
Set objFs  = Nothing
Set f2 = Nothing
Set objNetwork 	 = Nothing
Set colProcessList = Nothing

' objDocumentAtoll.Save
objDocumentAtoll.Close 1
Set objDocumentAtoll = Nothing
objAtoll.Quit
Set objAtoll = Nothing
' If vFound = False Then
	' objAtoll.Quit
	' Set objAtoll = Nothing
' End If
