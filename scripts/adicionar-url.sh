#!/usr/bin/env bash
# Uso: scripts/adicionar-url.sh https://exemplo.com "Nome do site"
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saida.sh
URL=$1
NOME=${2:-$1}
aws dynamodb put-item --table-name "$TABELA_URLS" --region "$REGIAO" --item "$(cat <<JSON
{"url": {"S": "$URL"}, "nome": {"S": "$NOME"}, "ativo": {"BOOL": true}}
JSON
)"
echo "Adicionada: $NOME ($URL)"
