#!/usr/bin/env bash
# Esvazia o bucket da página de status e apaga a stack inteira (custo zero depois disso)
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saida.sh
aws s3 rm "s3://$BUCKET" --recursive --region "$REGIAO"
sam delete --stack-name "$STACK" --region "$REGIAO"
