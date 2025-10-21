#!/bin/bash

# Script pour exécuter le scheduler en arrière-plan
# Usage: ./run_scheduler.sh

echo "Démarrage du scheduler en arrière-plan..."
echo "Le système s'exécutera automatiquement selon la configuration."
echo

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "Erreur: Python3 n'est pas installé"
    echo "Veuillez installer Python 3.7+"
    exit 1
fi

# Aller dans le répertoire du projet
cd "$(dirname "$0")"

# Exécuter le scheduler en arrière-plan
echo "Exécution du scheduler en mode headless (arrière-plan)..."
echo "Configuration: config/config.json"
echo "Heure d'exécution configurée dans scheduler.run_time"
echo

python3 src/scheduler.py --config config/config.json

echo
echo "Scheduler arrêté."
