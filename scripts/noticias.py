#!/usr/bin/env python3
"""Busca notícias dos últimos dias para cada subtema de config/temas.json (Google Notícias).

Não precisa de chave. Uso: python3 scripts/noticias.py
Saída: noticias/noticias.json (lido pela aba "Notícias e react" do sistema).
"""
import json, os, ssl, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config/temas.json").read_text(encoding="utf-8"))
DIAS = 7
POR_TEMA = 10

_ctx = ssl.create_default_context()
for ca in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
    if ca and os.path.exists(ca):
        _ctx = ssl.create_default_context(cafile=ca)
        break


def consulta(tema):
    # nome do subtema + expressões de 2 ou mais palavras (palavras soltas como "plástica" trazem notícia errada)
    termos = [tema["name"]] + [k for k in tema["keywords"] if " " in k and len(k) > 8][:6]
    vistos, partes = set(), []
    for t in termos:
        k = t.lower()
        if k in vistos:
            continue
        vistos.add(k)
        partes.append(f'"{t}"')
    return " OR ".join(partes) + f" when:{DIAS}d"


def buscar(q):
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": q, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"})
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (radar-viral)"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, context=_ctx, timeout=30) as r:
                return ET.fromstring(r.read())
        except Exception:
            if tentativa == 2:
                raise
            time.sleep(3)


def main():
    saida = {"geradoEm": datetime.now(timezone.utc).isoformat(timespec="seconds"), "temas": {}}
    for t in CFG["themes"]:
        try:
            root = buscar(consulta(t))
            if not root.findall(".//item"):
                time.sleep(3)
                root = buscar(consulta(t))
        except Exception as e:
            print(f"{t['name']}: erro {e}")
            saida["temas"][t["id"]] = []
            continue
        itens = []
        for it in root.findall(".//item"):
            titulo = (it.findtext("title") or "").strip()
            fonte = (it.findtext("source") or "").strip()
            if fonte and titulo.endswith(" - " + fonte):
                titulo = titulo[: -len(" - " + fonte)]
            try:
                data = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc).isoformat(timespec="seconds")
            except Exception:
                data = None
            itens.append({"titulo": titulo, "fonte": fonte, "link": it.findtext("link"), "data": data})
        itens.sort(key=lambda x: x["data"] or "", reverse=True)
        saida["temas"][t["id"]] = itens[:POR_TEMA]
        print(f"{t['name']}: {len(itens)} notícias")
        time.sleep(1)
    out = ROOT / "noticias/noticias.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(saida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
