; ==============================================================================
; NSIS Installer Script for Local AI Development Environment
; ==============================================================================
;
; This script creates a Windows installer for the Local AI Development Environment
; Desktop GUI Application using NSIS (Nullsoft Scriptable Install System).
;
; Requirements implemented:
; - 8.7: Create installer with desktop shortcut and Start menu entry
; - 7.5: Set application icon for shortcuts
;
; Prerequisites:
; - NSIS 3.0 or later (https://nsis.sourceforge.io/)
; - PyInstaller-built executable in dist/LocalAIDev/
;
; Usage:
;   makensis build/installers/windows.nsi
;
; Output:
;   dist/LocalAIDev-Setup.exe
;
; ==============================================================================

; ==============================================================================
; Includes
; ==============================================================================

!include "MUI2.nsh"              ; Modern UI
!include "LogicLib.nsh"           ; Logic library
!include "x64.nsh"                ; 64-bit detection

; ==============================================================================
; General Configuration
; ==============================================================================

; Application information
!define PRODUCT_NAME "Local AI Development Environment"
!define PRODUCT_SHORT_NAME "LocalAIDev"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "Local AI Dev Team"
!define PRODUCT_WEB_SITE "https://github.com/yourusername/local-ai-dev"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\${PRODUCT_SHORT_NAME}.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"

; Installer properties
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "..\..\dist\${PRODUCT_SHORT_NAME}-Setup.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; Compression
SetCompressor /SOLID lzma
SetCompressorDictSize 32

; Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "..\..\src\web\assets\icon.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis3-metro.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\nsis3-metro.bmp"

; Installer pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\..\LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

; Finish page with options
!define MUI_FINISHPAGE_RUN "$INSTDIR\${PRODUCT_SHORT_NAME}.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${PRODUCT_NAME}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Create Desktop Shortcut"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION CreateDesktopShortcut
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language
!insertmacro MUI_LANGUAGE "English"

; ==============================================================================
; Version Information
; ==============================================================================

VIProductVersion "1.0.0.0"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey "LegalCopyright" "Copyright © 2024 ${PRODUCT_PUBLISHER}"
VIAddVersionKey "FileDescription" "${PRODUCT_NAME} Installer"
VIAddVersionKey "FileVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"

; ==============================================================================
; Installer Sections
; ==============================================================================

Section "MainSection" SEC01
  SetOutPath "$INSTDIR"
  SetOverwrite try
  
  ; Copy all files from PyInstaller dist folder
  File /r "..\..\dist\${PRODUCT_SHORT_NAME}\*.*"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Write registry keys for application paths
  WriteRegStr HKLM "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe"
  
  ; Write uninstall information
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
  
  ; Estimate installation size (in KB)
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\${PRODUCT_NAME}"
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe" "" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe" 0
  CreateShortCut "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  
  ; Add to PATH (optional - for CLI access)
  ; Uncomment if you want the application accessible from command line
  ; EnVar::AddValue "PATH" "$INSTDIR"
  
SectionEnd

; ==============================================================================
; Functions
; ==============================================================================

Function CreateDesktopShortcut
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe" "" "$INSTDIR\${PRODUCT_SHORT_NAME}.exe" 0
FunctionEnd

Function .onInit
  ; Check if already installed
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" done
  
  ; Prompt to uninstall previous version
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${PRODUCT_NAME} is already installed.$\n$\nClick 'OK' to remove the previous version or 'Cancel' to cancel this installation." \
    IDOK uninst
  Abort
  
uninst:
  ; Run the uninstaller
  ClearErrors
  ExecWait '$R0 _?=$INSTDIR'
  
  ; Check if uninstaller succeeded
  IfErrors no_remove_uninstaller
    ; Remove uninstaller executable
    Delete $R0
    RMDir "$INSTDIR"
  no_remove_uninstaller:
  
done:
FunctionEnd

; ==============================================================================
; Uninstaller Section
; ==============================================================================

Section Uninstall
  ; Stop application if running
  !include "FileFunc.nsh"
  ${GetProcessInfo} "${PRODUCT_SHORT_NAME}.exe" $R0
  ${If} $R0 != 0
    MessageBox MB_OK|MB_ICONINFORMATION "Please close ${PRODUCT_NAME} before uninstalling."
    Abort
  ${EndIf}
  
  ; Remove Start Menu shortcuts
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\${PRODUCT_NAME}\Uninstall.lnk"
  RMDir "$SMPROGRAMS\${PRODUCT_NAME}"
  
  ; Remove Desktop shortcut
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  
  ; Remove application files
  RMDir /r "$INSTDIR"
  
  ; Remove registry keys
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  
  ; Remove from PATH if it was added
  ; EnVar::DeleteValue "PATH" "$INSTDIR"
  
  ; Remove user data (optional - prompt user)
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to remove user data and settings?" IDNO skip_userdata
    RMDir /r "$APPDATA\${PRODUCT_NAME}"
    RMDir /r "$LOCALAPPDATA\${PRODUCT_NAME}"
  skip_userdata:
  
  SetAutoClose true
SectionEnd

; ==============================================================================
; Uninstaller Functions
; ==============================================================================

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer."
FunctionEnd

; ==============================================================================
; Helper Functions - Process Detection
; ==============================================================================

!macro GetProcessInfo PROCESS_NAME RESULT
  nsExec::ExecToStack 'tasklist /FI "IMAGENAME eq ${PROCESS_NAME}" /NH'
  Pop $0  ; Exit code
  Pop $1  ; Output
  
  ${If} $0 == 0
    StrCpy ${RESULT} 1  ; Process found
  ${Else}
    StrCpy ${RESULT} 0  ; Process not found
  ${EndIf}
!macroend

!define GetProcessInfo "!insertmacro GetProcessInfo"

; ==============================================================================
; Size Calculation Helper
; ==============================================================================

!macro GetSize ROOT PATTERN SIZE_KB SIZE_MB SIZE_GB
  Push "${ROOT}"
  Push "${PATTERN}"
  Call GetSize
  Pop ${SIZE_KB}
  Pop ${SIZE_MB}
  Pop ${SIZE_GB}
!macroend

!define GetSize "!insertmacro GetSize"

Function GetSize
  Exch $0  ; Pattern
  Exch
  Exch $1  ; Root
  Push $2  ; Size in KB
  Push $3  ; Temp
  Push $4  ; Temp
  
  StrCpy $2 0
  
  ${If} ${FileExists} "$1\*.*"
    FindFirst $3 $4 "$1\*.*"
    loop:
      StrCmp $4 "" done
      StrCmp $4 "." next
      StrCmp $4 ".." next
      
      ${If} ${FileExists} "$1\$4\*.*"
        ; Directory - recurse (not implemented for simplicity)
        ; Skip subdirectories to avoid complexity
      ${Else}
        ; File - estimate size (simplified)
        IntOp $2 $2 + 1
      ${EndIf}
      
    next:
      FindNext $3 $4
      Goto loop
    done:
      FindClose $3
  ${EndIf}
  
  Pop $4
  Pop $3
  Exch $2  ; KB
  Exch
  Pop $1
  Exch
  Pop $0
FunctionEnd

; ==============================================================================
; Build Instructions
; ==============================================================================

/*

BUILD INSTRUCTIONS:

1. Install NSIS:
   Download from https://nsis.sourceforge.io/Download
   Install NSIS 3.0 or later

2. Ensure PyInstaller build is complete:
   - Run: pyinstaller build/pyinstaller/local-ai-dev.spec
   - Verify: dist/LocalAIDev/ directory exists with all files

3. Ensure icon file exists:
   - File: src/web/assets/icon.ico
   - Should contain multiple sizes (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)

4. Build the installer:
   cd c:\Users\acer\Local dev ai
   makensis build/installers/windows.nsi

5. Test the installer:
   - Run: dist/LocalAIDev-Setup.exe
   - Verify: Desktop shortcut created (if selected)
   - Verify: Start menu entry created
   - Verify: Application launches correctly
   - Verify: Uninstaller works correctly

OUTPUT:
   dist/LocalAIDev-Setup.exe (~80-120MB compressed)

CUSTOMIZATION:

To customize the installer:
- Change PRODUCT_WEB_SITE to your actual website
- Add a LICENSE file in the project root
- Customize installer graphics (replace MUI_HEADERIMAGE_BITMAP, etc.)
- Add file associations if needed
- Add registry keys for application settings

CODE SIGNING (Recommended for production):

To sign the installer with a code signing certificate:
1. Obtain a code signing certificate
2. After building the installer, sign it:
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist/LocalAIDev-Setup.exe

TROUBLESHOOTING:

- Error: "Can't open file": Check that PyInstaller build completed successfully
- Error: "Icon not found": Verify icon.ico exists at src/web/assets/icon.ico
- Installer size too large: Check PyInstaller output size, optimize excludes
- Application won't launch: Test the PyInstaller build directly before creating installer

*/

