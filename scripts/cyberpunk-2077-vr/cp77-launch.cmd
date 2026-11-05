@echo off
rem ============================================================================
rem  Cyberpunk 2077 launch wrapper (added 2026-11-04 for CyberpunkVRPort)
rem
rem  Flat by default. With -vr on the command line (the "Cyberpunk 2077 (VR)"
rem  Steam shortcut runs: steam.exe -applaunch 1091500 -vr) it starts the VR plugin.
rem
rem  Lives in <Cyberpunk 2077>\_vr\ and finds the game root from there.
rem  Steam launch option on Cyberpunk 2077 (app 1091500):
rem    "<Cyberpunk 2077>\_vr\cp77-launch.cmd" %command%
rem
rem  What it does, in order:
rem   1. copies red4ext-config.flat.ini or red4ext-config.vr.ini over red4ext\config.ini
rem      (flat = RED4ext skips the cyberpunkvrport plugin, everything else unchanged)
rem   2. swaps in this mode's own settings file (profiles\UserSettings.<mode>.json), so the
rem      VR preset the plugin merges on its first start never touches the flat settings
rem   3. VR only: starts SteamVR if vrserver.exe is not running and waits for it
rem   4. runs bin\x64\Cyberpunk2077.exe directly (no REDlauncher) and waits for it
rem   5. saves UserSettings.json back into profiles\UserSettings.<mode>.json
rem  -dryrun: log the arguments and stop before step 3 (for checking what Steam passes).
rem
rem  Undo: clear the launch option and delete the "Cyberpunk 2077 (VR)" shortcut; the game
rem  then runs with whatever red4ext\config.ini last said (flat if "ignored = cyberpunkvrport").
rem  Log: _vr\cp77-launch.log
rem ============================================================================
setlocal EnableExtensions
set "VRDIR=%~dp0"
if "%VRDIR:~-1%"=="\" set "VRDIR=%VRDIR:~0,-1%"
for %%i in ("%VRDIR%\..") do set "ROOT=%%~fi"
set "PROF=%VRDIR%\profiles"
set "CFG=%ROOT%\red4ext\config.ini"
set "USDIR=%LOCALAPPDATA%\CD Projekt Red\Cyberpunk 2077"
set "US=%USDIR%\UserSettings.json"
set "LOG=%VRDIR%\cp77-launch.log"
set "FIND=%SystemRoot%\System32\find.exe"
set "MODE=flat"
set "DRY=0"
for %%a in (%*) do (
    if /i "%%~a"=="-vr" set "MODE=vr"
    if /i "%%~a"=="-dryrun" set "DRY=1"
)
if not exist "%PROF%" mkdir "%PROF%"
echo [%date% %time%] start mode=%MODE% dryrun=%DRY% root=%ROOT% args=%*>>"%LOG%"

rem ---- 1. RED4ext: plugin on (vr) or ignored (flat) ---------------------------------------
if not exist "%VRDIR%\red4ext-config.%MODE%.ini" (
    echo [%date% %time%] WARNING missing %VRDIR%\red4ext-config.%MODE%.ini, config.ini left alone>>"%LOG%"
) else (
    copy /y "%VRDIR%\red4ext-config.%MODE%.ini" "%CFG%" >nul
    if errorlevel 1 echo [%date% %time%] WARNING could not write %CFG%>>"%LOG%"
)

rem ---- 2. settings profile -----------------------------------------------------------------
if not exist "%USDIR%" mkdir "%USDIR%"
set "LAST="
if exist "%PROF%\last-mode.txt" set /p LAST=<"%PROF%\last-mode.txt"
if exist "%PROF%\UserSettings.%MODE%.json" goto :restore
if not exist "%US%" goto :profiledone
if "%LAST%"=="" goto :profiledone
if "%LAST%"=="%MODE%" goto :profiledone
rem the current file belongs to the other mode (already saved as its profile): set it aside
move /y "%US%" "%PROF%\UserSettings.%LAST%.json.setaside" >nul
echo [%date% %time%] no %MODE% profile yet; set aside the %LAST% settings so %MODE% starts fresh>>"%LOG%"
goto :profiledone
:restore
copy /y "%PROF%\UserSettings.%MODE%.json" "%US%" >nul
echo [%date% %time%] restored %MODE% profile>>"%LOG%"
:profiledone

if "%DRY%"=="1" (
    echo [%date% %time%] dry run, stopping here>>"%LOG%"
    exit /b 0
)

rem ---- 3. VR: make sure SteamVR is up before the game asks OpenXR for a session -----------
if not "%MODE%"=="vr" goto :launch
tasklist /fi "imagename eq vrserver.exe" 2>nul | "%FIND%" /i "vrserver.exe" >nul
if not errorlevel 1 goto :launch
echo [%date% %time%] starting SteamVR>>"%LOG%"
start "" "steam://run/250820"
set /a N=0
:waitvr
ping -n 3 127.0.0.1 >nul
tasklist /fi "imagename eq vrserver.exe" 2>nul | "%FIND%" /i "vrserver.exe" >nul
if not errorlevel 1 goto :vrup
set /a N+=1
if %N% lss 20 goto :waitvr
echo [%date% %time%] WARNING SteamVR did not start within 40 s, launching anyway>>"%LOG%"
goto :launch
:vrup
ping -n 6 127.0.0.1 >nul
echo [%date% %time%] SteamVR is running>>"%LOG%"

rem ---- 4. run the game and wait ------------------------------------------------------------
:launch
echo [%date% %time%] launching Cyberpunk2077.exe>>"%LOG%"
pushd "%ROOT%\bin\x64"
start "" /wait "%ROOT%\bin\x64\Cyberpunk2077.exe"
set "RC=%ERRORLEVEL%"
popd
echo [%date% %time%] game exited rc=%RC%>>"%LOG%"

rem ---- 5. keep this mode's settings --------------------------------------------------------
if exist "%US%" (
    copy /y "%US%" "%PROF%\UserSettings.%MODE%.json" >nul
    >"%PROF%\last-mode.txt" echo %MODE%
    echo [%date% %time%] saved %MODE% profile>>"%LOG%"
)
exit /b %RC%
