#!/bin/bash

# Script pour exécuter le système de scraping en arrière-plan
# Usage: ./run_background.sh

echo "Démarrage du système de scraping en arrière-plan..."
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python3 n'est pas installé"
    echo "Veuillez installer Python 3.7+"
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

# Exécuter le scraper en arrière-plan avec mode headless par défaut
echo "Exécution du scraper en mode headless (arrière-plan)..."
echo "Configuration: config/config.json"
echo

python3 src/main.py --config config/config.json

echo
echo "Scraping terminé. Vérifiez les logs dans logs/app.log"
