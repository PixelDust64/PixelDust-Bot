#!/bin/bash

# entra no diretório do projeto (ajuste se necessário)
cd /mnt/256/TelgramBot || exit 1

# ativa o ambiente virtual
source venv/bin/activate

# roda o bot
python bot.py