#!/usr/bin/env bash
# Envia o index.html, roda a Lambda uma vez (gera o status.json) e invalida o cache
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saida.sh

aws s3 cp site/index.html "s3://$BUCKET/index.html" \
  --content-type "text/html; charset=utf-8" --cache-control "max-age=300" --region "$REGIAO"
aws lambda invoke --function-name "$FUNCAO" --region "$REGIAO" /tmp/saida-check-urls.json >/dev/null
cat /tmp/saida-check-urls.json; echo
aws cloudfront create-invalidation --distribution-id "$DISTRIBUICAO" --paths "/*" \
  --query "Invalidation.Status" --output text
echo "Site: $SITE_URL"
