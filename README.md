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

## Versão SAM

Tudo acima em um `template.yaml`. O agendamento fica na própria Lambda (evento `ScheduleV2`), sem retries.

No CloudShell (us-east-2), um comando por vez:

```bash
git clone https://github.com/jvpbicalho/monitor-urls.git && cd monitor-urls
sam build
sam deploy --parameter-overrides EmailAlerta=seu-email@exemplo.com
```

Depois do deploy:

1. Confirme a assinatura no e-mail "AWS Notification - Subscription Confirmation".
2. Cadastre as URLs: `scripts/adicionar-url.sh https://www.wikipedia.org Wikipedia`
3. Publique a página: `scripts/publicar-site.sh` (envia o `index.html`, roda a Lambda uma vez e invalida o cache). O endereço aparece no fim.

Para apagar tudo e zerar o custo: `scripts/destruir.sh`.
