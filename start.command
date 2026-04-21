#!/bin/bash

cd "$(dirname "$0")" || exit 1

"./AdvancedSerialReader/bin/python" "./main.py"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "Errore durante l'esecuzione (codice $EXIT_CODE)"
    read -p "Premi Invio per chiudere..."
fi

exit $EXIT_CODE