#!/usr/bin/env bash
# Uso: source scripts/saida.sh  -> exporta as saídas da stack como variáveis
STACK=${STACK:-monitor-urls}
REGIAO=${REGIAO:-us-east-2}
saida() {
  aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGIAO" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}
SITE_URL=$(saida SiteUrl)
DISTRIBUICAO=$(saida DistributionId)
BUCKET=$(saida StatusBucketName)
TABELA_URLS=$(saida UrlsTableName)
FUNCAO=$(saida CheckUrlsFunctionName)
export STACK REGIAO SITE_URL DISTRIBUICAO BUCKET TABELA_URLS FUNCAO
