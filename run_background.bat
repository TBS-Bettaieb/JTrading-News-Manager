@echo off
REM Script pour exécuter le système de scraping en arrière-plan
REM Usage: run_background.bat

echo Démarrage du système de scraping en arrière-plan...
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

REM Exécuter le scraper en arrière-plan avec mode headless par défaut
echo Exécution du scraper en mode headless (arrière-plan)...
echo Configuration: config/config.json
echo.

python src/main.py --config config/config.json

echo.
echo Scraping terminé. Vérifiez les logs dans logs/app.log
echo.
pause
