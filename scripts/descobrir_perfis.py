#!/usr/bin/env python3
"""Descobre os perfis por trás dos posts que viralizaram nos temas e cadastra os melhores como referência.

A busca principal do radar é por perfis do nicho (não por hashtag). As hashtags servem como porta de
entrada: elas trazem posts virais, este script descobre quem postou (pela página pública de incorporação
do post, a mesma que os sites usam para mostrar posts), confere o perfil na API oficial (Business Discovery)
e acrescenta os melhores de cada subtema em config/temas.json -> profiles.

Uso: IG_TOKEN=... python3 scripts/descobrir_perfis.py
"""
import json, os, re, ssl, sys, time, urllib.parse, urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CFG_FILE = ROOT / "config/temas.json"
POR_SUBTEMA = 8          # perfis novos no máximo por subtema, por rodada
MIN_SEGUIDORES = 3000
VER = "v26.0"
TOKEN = os.environ.get("IG_TOKEN", "").strip()

_ctx = ssl.create_default_context()
for ca in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
    if ca and os.path.exists(ca):
        _ctx = ssl.create_default_context(cafile=ca)
        break


def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, context=_ctx, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def autor(link):
    m = re.search(r"/(p|reel|tv)/([^/?#]+)", link or "")
    if not m:
        return None
    try:
        html = get(f"https://www.instagram.com/p/{m.group(2)}/embed/", {"User-Agent": "Mozilla/5.0 (radar-viral)"})
    except Exception:
        return None
    u = re.search(r'class="UsernameText">([^<]+)<', html) or re.search(r'"username":"([^"]+)"', html)
    return u.group(1).strip() if u else None


def conferir(ig, user):
    q = urllib.parse.urlencode({"fields": f"business_discovery.username({user}){{username,followers_count,media_count}}", "access_token": TOKEN})
    for tentativa in range(3):
        try:
            return json.loads(get(f"https://graph.facebook.com/{VER}/{ig}?{q}"))["business_discovery"]
        except urllib.error.HTTPError as e:
            body = json.loads(e.read() or b"{}").get("error", {})
            if "resource limits" in str(body.get("message", "")) or body.get("code") in (4, 17, 32, 613):
                time.sleep(90)
                continue
            return None
        except Exception:
            return None
    return None


def main():
    if not TOKEN:
        sys.exit("IG_TOKEN não está definido.")
    coletas = sorted((ROOT / "dados").glob("coleta-*.json")) or [p for p in [ROOT / "radar/coleta.json"] if p.exists()]
    if not coletas:
        sys.exit("Nenhuma coleta em dados/. Rode scripts/coletar.py antes.")
    d = json.loads(coletas[-1].read_text(encoding="utf-8"))
    posts = d.get("todos") or d.get("posts")
    if not posts:
        vistos = {}
        for t in d["temas"]:
            for p in t["posts"]:
                vistos.setdefault(p["link"], {**p, "temas": []})["temas"].append(t["id"])
        posts = list(vistos.values())
    cfg = json.loads(CFG_FILE.read_text(encoding="utf-8"))
    ja = {p["username"].lower() for p in cfg.get("profiles", [])} | {u.lower() for u in cfg.get("perfisRecusados", [])}
    me = json.loads(get(f"https://graph.facebook.com/{VER}/me/accounts?" + urllib.parse.urlencode({"fields": "instagram_business_account", "access_token": TOKEN})))
    ig = next(p["instagram_business_account"]["id"] for p in me["data"] if p.get("instagram_business_account"))

    por_autor = defaultdict(lambda: {"posts": 0, "temas": Counter(), "eng": 0})
    for i, p in enumerate(sorted(posts, key=lambda p: -(p.get("nota") or 0))[:400]):
        u = autor(p.get("link"))
        time.sleep(1)
        if not u:
            continue
        a = por_autor[u]
        a["posts"] += 1
        a["eng"] += (p.get("curtidas") or 0) + 2 * (p.get("comentarios") or 0)
        for t in p.get("temas", []):
            a["temas"][t] += 1
    print(f"{len(por_autor)} autores encontrados", file=sys.stderr)

    novos = defaultdict(list)
    for u, a in sorted(por_autor.items(), key=lambda kv: (-kv[1]["posts"], -kv[1]["eng"])):
        if u.lower() in ja or not a["temas"]:
            continue
        tema = a["temas"].most_common(1)[0][0]
        if len(novos[tema]) >= POR_SUBTEMA:
            continue
        info = conferir(ig, u)
        time.sleep(15)   # respeita o limite de consultas por hora
        if not info or (info.get("followers_count") or 0) < MIN_SEGUIDORES:
            continue
        novos[tema].append({"username": info["username"], "theme": tema, "origem": "descoberto", "seguidores": info.get("followers_count")})
        ja.add(u.lower())
    add = [p for lst in novos.values() for p in lst]
    cfg["profiles"] = cfg.get("profiles", []) + add
    CFG_FILE.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(add)} perfis novos cadastrados:")
    for t, lst in novos.items():
        print(f"  {t}: " + ", ".join(f"@{p['username']} ({p['seguidores']})" for p in lst))


if __name__ == "__main__":
    main()
