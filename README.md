# Monitor de URLs

Projeto 2 do estudo de AWS: um monitor no estilo UptimeRobot, sem API e sem ação do usuário.

```
EventBridge Scheduler (a cada 5 min)
        │
        ▼
Lambda Check-Urls ──► DynamoDB (urls + checagens com TTL de 7 dias)
        │
        ├──► S3 status.json ──► CloudFront ──► página de status
        └──► SNS ──► e-mail quando um site cai ou volta

CloudWatch: logs da Lambda + alarmes "erros" e "parado"
```

## Versão manual (console)

Feita passo a passo no console em us-east-2. Os arquivos usados estão em [`manual/`](manual/):

- `check_urls.py`: código da Lambda (Python 3.13, arm64, timeout 30 s)
- `politica-check-urls.json`: política em linha da role da Lambda
- `site/index.html` e `site/status.json`: página de status e um exemplo de dados

Decisões:

- Só alerta quando o estado muda (no ar → fora, fora → no ar), usando `ultimoStatus` na tabela de URLs.
- Site fora do ar **não** é erro da Lambda. O alarme de erros mede a saúde do monitor, não dos sites.
- O alarme "parado" trata dados ausentes como ruins: se ninguém chama a Lambda, a métrica some.
- `status.json` é gravado com `Cache-Control: max-age=60` para o CloudFront não segurar versão velha.
