@echo off
REM Script pour exécuter le scheduler en arrière-plan
REM Usage: run_scheduler.bat

echo Démarrage du scheduler en arrière-plan...
echo Le système s'exécutera automatiquement selon la configuration.
echo.

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo Erreur: Python n'est pas installé ou pas dans le PATH
    echo Veuillez installer Python 3.7+ et l'ajouter au PATH
    pause
    exit /b 1
)

REM Aller dans le répertoire du projet
cd /d "%~dp0"

REM Exécuter le scheduler en arrière-plan
echo Exécution du scheduler en mode headless (arrière-plan)...
echo Configuration: config/config.json
echo Heure d'exécution configurée dans scheduler.run_time
echo.

python src/scheduler.py --config config/config.json

echo.
echo Scheduler arrêté.
pause
