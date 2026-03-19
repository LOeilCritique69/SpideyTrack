@echo off
title Marveldle — Spider-Man Tracker
color 0A

echo.
echo  ╔══════════════════════════════════════╗
echo  ║     MARVELDLE · Spider-Man Tracker   ║
echo  ╚══════════════════════════════════════╝
echo.

:: Se déplacer dans le dossier du projet
cd /d "d:\projet_webs\MarvelDleSpidey\"
if %errorlevel% neq 0 (
    echo  [ERREUR] Dossier projet introuvable.
    pause
    exit /b 1
)

:: Vérifier que Python est accessible
"C:\Program Files\Python314\python.exe" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERREUR] Python introuvable.
    pause
    exit /b 1
)

:: Vérifier que le script existe
if not exist "tweet.py" (
    echo  [ERREUR] tweet.py introuvable dans le dossier.
    pause
    exit /b 1
)

echo  Lancement du script...
echo  ----------------------------------------
echo.

:: Exécuter le script
"C:\Program Files\Python314\python.exe" tweet.py

echo.
echo  ----------------------------------------
if %errorlevel% neq 0 (
    echo  [ERREUR] Le script s'est termine avec une erreur ^(code %errorlevel%^).
    pause
) else (
    echo  [OK] Script termine avec succes.
    timeout /t 5 /nobreak >nul
)