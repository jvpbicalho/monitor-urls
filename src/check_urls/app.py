import json
import os
import time
import unicodedata
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import boto3

dynamodb = boto3.resource("dynamodb")
tabela_urls = dynamodb.Table(os.environ["TABELA_URLS"])
tabela_checagens = dynamodb.Table(os.environ["TABELA_CHECAGENS"])
s3 = boto3.client("s3")
sns = boto3.client("sns")

BUCKET_STATUS = os.environ["BUCKET_STATUS"]
TOPICO_ARN = os.environ["TOPICO_ARN"]
TIMEOUT_SEGUNDOS = 10
DIAS_HISTORICO = 7


def testar(url):
    """Faz um GET na URL e devolve ok, statusCode, ms e erro."""
    inicio = time.monotonic()
    req = urllib.request.Request(url, headers={"User-Agent": "monitor-urls-estudo/1.0"})
    resultado = {"url": url}
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
            resultado["statusCode"] = resp.status
            resultado["ok"] = 200 <= resp.status < 400
    except urllib.error.HTTPError as e:
        # O servidor respondeu, mas com 4xx ou 5xx
        resultado["statusCode"] = e.code
        resultado["ok"] = False
    except Exception as e:
        # Timeout, DNS, certificado inválido, conexão recusada...
        resultado["erro"] = type(e).__name__
        resultado["ok"] = False
    resultado["ms"] = int((time.monotonic() - inicio) * 1000)
    return resultado


def sem_acentos(texto):
    # O assunto (Subject) do SNS só aceita ASCII
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()


def alertar(item, resultado, novo_estado):
    nome = item.get("nome", item["url"])
    if novo_estado == "fora_do_ar":
        assunto = f"[Monitor] FORA DO AR: {nome}"
        detalhe = resultado.get("statusCode") or resultado.get("erro")
        corpo = f"{nome} ({item['url']}) parou de responder.\nMotivo: {detalhe}\nTempo: {resultado['ms']} ms"
    else:
        assunto = f"[Monitor] Voltou: {nome}"
        corpo = f"{nome} ({item['url']}) voltou a responder ({resultado['statusCode']}, {resultado['ms']} ms)."
    sns.publish(TopicArn=TOPICO_ARN, Subject=sem_acentos(assunto)[:100], Message=corpo)


def lambda_handler(event, context):
    itens = [i for i in tabela_urls.scan()["Items"] if i.get("ativo", True)]

    with ThreadPoolExecutor(max_workers=10) as pool:
        resultados = list(pool.map(testar, [i["url"] for i in itens]))

    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    expira_em = int(time.time()) + DIAS_HISTORICO * 24 * 3600
    status_urls = []
    alertas = 0

    for item, r in zip(itens, resultados):
        r["verificadoEm"] = agora
        r["nome"] = item.get("nome", item["url"])
        print(json.dumps(r))  # log estruturado, uma linha por URL

        tabela_checagens.put_item(Item={**r, "expiraEm": expira_em})

        # Só alerta quando o estado muda (no ar -> fora, fora -> no ar)
        novo_estado = "no_ar" if r["ok"] else "fora_do_ar"
        estado_anterior = item.get("ultimoStatus")
        if novo_estado != estado_anterior:
            tabela_urls.update_item(
                Key={"url": item["url"]},
                UpdateExpression="SET ultimoStatus = :s, mudouEm = :t",
                ExpressionAttributeValues={":s": novo_estado, ":t": agora},
            )
            # Na primeira checagem (sem estado anterior) só avisa se estiver fora
            if estado_anterior is not None or novo_estado == "fora_do_ar":
                alertar(item, r, novo_estado)
                alertas += 1

        status_urls.append(r)

    s3.put_object(
        Bucket=BUCKET_STATUS,
        Key="status.json",
        Body=json.dumps({"geradoEm": agora, "urls": status_urls}, ensure_ascii=False).encode("utf-8"),
        ContentType="application/json; charset=utf-8",
        CacheControl="max-age=60",
    )

    fora = sum(1 for r in status_urls if not r["ok"])
    return {"testadas": len(status_urls), "foraDoAr": fora, "alertas": alertas}
