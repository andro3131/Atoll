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


Set objAtoll 	= GetObject("", "Atoll.Application")
Set objDocumentAtoll = objAtoll.Documents.Open(dat)

objAtoll.Visible 	= yes


' objDocumentAtoll.Refresh   ' ZAKOMENTIRANO - povleci kolega's G:\ poti iz SQL archive nazaj v dokument


If Err.Number <> 0 Then
  WScript.Echo "objDocumentAtoll.Refresh cisto na zacetku: " & Err.Description
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

