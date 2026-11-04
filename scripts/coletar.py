#!/usr/bin/env python3
"""Coleta os posts em alta do Instagram para os temas de config/temas.json.

Usa a mesma lógica do radar (index.html): top_media + recent_media por hashtag,
perfis de referência via business_discovery, filtro de português, classificação
por palavra-chave e nota viral de 0 a 100.

Uso:  IG_TOKEN=... python3 scripts/coletar.py
Saída: dados/coleta-AAAA-MM-DD.json
"""
import json, os, re, ssl, sys, time, unicodedata, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

VER = "v26.0"
ROOT = Path(__file__).resolve().parent.parent
CFG = json.loads((ROOT / "config/temas.json").read_text(encoding="utf-8"))
IDS_FILE = ROOT / "config/hashtag_ids.json"
TAG_FIELDS = "id,caption,media_type,like_count,comments_count,timestamp,permalink,media_url"
BD_FIELDS = "id,caption,media_type,like_count,comments_count,view_count,timestamp,permalink,media_url,thumbnail_url"
BD_FIELDS_MIN = "id,caption,media_type,like_count,comments_count,view_count,timestamp,permalink"
# Pausa entre consultas (segundos). O Instagram aceita cerca de 200 consultas por hora;
# na coleta automática diária (GitHub) usamos RADAR_PAUSA=15 para nunca estourar.
PAUSA = float(os.environ.get("RADAR_PAUSA", "0"))
POSTS_POR_TEMA = 15
DIAS = 30

TOKEN = os.environ.get("IG_TOKEN", "").strip()
if not TOKEN:
    sys.exit("IG_TOKEN não está definido. Adicione a chave nas configurações do ambiente do Claude.")

_ctx = ssl.create_default_context()
for ca in (os.environ.get("SSL_CERT_FILE"), "/root/.ccr/ca-bundle.crt"):
    if ca and os.path.exists(ca):
        _ctx = ssl.create_default_context(cafile=ca)
        break


class ApiError(Exception):
    def __init__(self, err):
        super().__init__(err.get("message", "erro desconhecido"))
        self.code = err.get("code")


def api(path, **params):
    params["access_token"] = TOKEN
    url = f"https://graph.facebook.com/{VER}/{path}?{urllib.parse.urlencode(params)}"
    if PAUSA:
        time.sleep(PAUSA)
    for tentativa in range(5):
        try:
            with urllib.request.urlopen(url, context=_ctx, timeout=40) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = json.loads(e.read() or b"{}")
            if "error" in body:
                err = body["error"]
                limite = err.get("code") in (4, 17, 32, 613) or "resource limits" in str(err.get("message", ""))
                if limite and tentativa < 4:
                    espera = 600 if PAUSA else 120
                    print(f"limite de consultas do Instagram; esperando {espera // 60} minutos...", file=sys.stderr)
                    time.sleep(espera)
                    continue
                raise ApiError(err)
            if tentativa == 4:
                raise
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            if tentativa == 4:
                raise
        time.sleep(2 * (tentativa + 1))


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").lower()


def clean_tag(t):
    return re.sub(r"[^a-z0-9_]", "", norm(t).lstrip("#"))


PT = re.compile(r"\b(não|você|vocês|voce|nao|também|então|muito|isso|está|são|uma|pra|filho|criança)\b")
ES = re.compile(r"\b(y|pero|muy|tiene|usted|niño|niños|hace|hacer|eres|soy|ella|cuando|porque|los|las|del)\b")
EN = re.compile(r"\b(the|and|you|your|with|this|that|is|are|my|for)\b")


def is_pt(caption):
    c = f" {str(caption or '').lower()} "
    if len(c.strip()) < 3:
        return True
    pt = len(re.findall(r"[ãõç]", c)) + 2 * len(PT.findall(c))
    es = 2 * len(re.findall(r"[ñ¿¡]", c)) + 2 * len(ES.findall(c))
    en = 2 * len(EN.findall(c))
    return pt >= es and pt >= en


_kw = {}


def kw_match(kw, text):
    if kw not in _kw:
        _kw[kw] = re.compile(r"(^|[^a-z0-9])#?" + re.escape(norm(kw)) + r"([^a-z0-9]|$)")
    return _kw[kw].search(text) is not None


def to_post(m, source):
    ts = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").timestamp()
    return {
        "id": m["id"], "legenda": m.get("caption") or "", "tipo": m.get("media_type", "IMAGE"),
        "curtidas": m.get("like_count"), "comentarios": m.get("comments_count") or 0, "visualizacoes": m.get("view_count"),
        "ts": ts, "link": m.get("permalink", ""), "fontes": [source],
        "thumb": m.get("thumbnail_url") or (m.get("media_url") if m.get("media_type") != "VIDEO" else None),
    }


def percentis(posts, key):
    vals = sorted(p[key] for p in posts)
    n = len(vals)
    out = {}
    for p in posts:
        lo = 0
        hi = n
        while lo < hi:
            mid = (lo + hi) // 2
            if vals[mid] < p[key]:
                lo = mid + 1
            else:
                hi = mid
        out[p["id"]] = 1 if n == 1 else lo / (n - 1)
    return out


def main():
    avisos = []
    themes = CFG["themes"]
    theme_by_id = {t["id"]: t for t in themes}
    panel_name = {p["id"]: p["name"] for p in CFG["panels"]}

    # conta
    contas = api("me/accounts", fields="name,instagram_business_account{id,username}")
    page = next((p for p in contas.get("data", []) if p.get("instagram_business_account")), None)
    if not page:
        sys.exit("Nenhuma conta profissional do Instagram encontrada para esta chave.")
    ig = page["instagram_business_account"]["id"]
    user = page["instagram_business_account"]["username"]

    # validade da chave
    try:
        d = api("debug_token", input_token=TOKEN).get("data", {})
        exp = d.get("expires_at") or 0
        if exp:
            dias = (exp - time.time()) / 86400
            if dias < 14:
                avisos.append(f"A chave de acesso do Instagram expira em {max(0, round(dias))} dias. Gere uma nova de 60 dias e atualize o segredo IG_TOKEN no GitHub e no radar.")
        if "instagram_manage_insights" not in d.get("scopes", []) and CFG.get("profiles"):
            avisos.append("A chave não tem instagram_manage_insights; os perfis de referência foram pulados.")
    except ApiError:
        pass

    ids = json.loads(IDS_FILE.read_text()) if IDS_FILE.exists() else {}
    posts = {}

    def add(p):
        old = posts.get(p["id"])
        if old:
            old["fontes"] += p["fontes"]
            if p.get("visualizacoes") is not None:
                old["visualizacoes"] = p["visualizacoes"]
            if p.get("mult") is not None:
                old["mult"] = max(old.get("mult") or 0, p["mult"])
        else:
            posts[p["id"]] = p

    # 1) perfis de referência: a busca principal (funciona como o SEO: quem fala do tema)
    for pr in CFG.get("profiles", []):
        u = str(pr.get("username", "")).strip().lstrip("@")
        if not u:
            continue
        try:
            try:
                r = api(ig, fields=f"business_discovery.username({u}){{username,followers_count,media.limit(20){{{BD_FIELDS}}}}}")
            except ApiError as e1:
                if e1.code != 100 and "reduce the amount" not in str(e1):
                    raise
                r = api(ig, fields=f"business_discovery.username({u}){{username,followers_count,media.limit(12){{{BD_FIELDS_MIN}}}}}")
            bd = r["business_discovery"]
            lst = [to_post(m, {"tipo": "perfil", "perfil": bd["username"], "tema": pr.get("theme") or None}) for m in bd.get("media", {}).get("data", [])]
            engs = sorted((p["curtidas"] or 0) + 2 * p["comentarios"] for p in lst)
            med = engs[len(engs) // 2] if engs else 0
            for p in lst:
                p["mult"] = ((p["curtidas"] or 0) + 2 * p["comentarios"]) / max(med, 1)
                add(p)
        except ApiError as e:
            if e.code == 190:
                sys.exit("A chave de acesso expirou. Gere uma nova de 60 dias e atualize o segredo IG_TOKEN no GitHub.")
            avisos.append(f"@{u}: {e}")
        print(f"@{u} ok", file=sys.stderr)

    # 2) hashtags: porta de entrada para descobrir perfis novos (complemento)
    vistos = set()
    for t in themes:
        for h in t["hashtags"]:
            tag = clean_tag(h)
            if not tag or tag in vistos:
                continue
            vistos.add(tag)
            try:
                if tag not in ids:
                    r = api("ig_hashtag_search", user_id=ig, q=tag)
                    if not r.get("data"):
                        avisos.append(f"#{tag} não existe no Instagram.")
                        continue
                    ids[tag] = r["data"][0]["id"]
                    IDS_FILE.write_text(json.dumps(ids, indent=2, ensure_ascii=False) + "\n")
                src = {"tipo": "hashtag", "tag": tag, "tema": t["id"]}
                try:
                    top = api(f"{ids[tag]}/top_media", user_id=ig, fields=TAG_FIELDS, limit=30)
                except ApiError as e1:
                    if "reduce the amount" not in str(e1):
                        raise
                    top = api(f"{ids[tag]}/top_media", user_id=ig, fields=TAG_FIELDS, limit=12)
                for m in top.get("data", []):
                    add(to_post(m, src))
                try:
                    rec = api(f"{ids[tag]}/recent_media", user_id=ig, fields=TAG_FIELDS, limit=25)
                    for m in rec.get("data", []):
                        p = to_post(m, src)
                        if (p["curtidas"] or 0) + 2 * p["comentarios"] >= 15:
                            add(p)
                except ApiError:
                    pass
            except ApiError as e:
                if e.code == 190:
                    sys.exit("A chave de acesso expirou. Gere uma nova de 60 dias e atualize o segredo IG_TOKEN no GitHub.")
                avisos.append(f"#{tag}: {e}")
            print(f"#{tag} ok", file=sys.stderr)

    # classificação, idioma e nota
    now = time.time()
    todos = []
    for p in posts.values():
        if not is_pt(p["legenda"]) or now - p["ts"] > DIAS * 86400:
            continue
        temas = {f["tema"] for f in p["fontes"] if f.get("tema")}
        cap = norm(p["legenda"])
        for t in themes:
            if any(kw_match(k, cap) for k in t["keywords"]) or any(f"#{clean_tag(h)}" in cap for h in t["hashtags"]):
                temas.add(t["id"])
        p["temas"] = [x for x in temas if x in theme_by_id]
        p["eng"] = (p["curtidas"] or 0) + 2 * p["comentarios"]
        p["horas"] = max(1, (now - p["ts"]) / 3600)
        p["vel"] = p["eng"] / (p["horas"] + 3)
        todos.append(p)
    tagp = [p for p in todos if any(f["tipo"] == "hashtag" for f in p["fontes"])]
    profp = [p for p in todos if p.get("mult") is not None]
    pv, pe, pm = percentis(tagp, "vel"), percentis(tagp, "eng"), percentis(profp, "mult")
    for p in todos:
        s = .55 * pv[p["id"]] + .45 * pe[p["id"]] if p["id"] in pv else 0
        s = max(s, pm.get(p["id"], 0))
        if (p.get("mult") or 0) >= 5:
            s = max(s, .97)
        p["nota"] = round(s * 100)

    saida = {"geradoEm": datetime.now(timezone.utc).isoformat(timespec="seconds"), "conta": user,
             "postsAnalisados": len(todos), "avisos": avisos, "temas": []}
    for t in themes:
        doTema = sorted((p for p in todos if t["id"] in p["temas"]), key=lambda p: (-p["nota"], -p["vel"]))[:POSTS_POR_TEMA]
        saida["temas"].append({
            "id": t["id"], "nome": t["name"], "painel": panel_name.get(t["panel"], t["panel"]),
            "posts": [{
                "nota": p["nota"], "formato": {"VIDEO": "Reels", "CAROUSEL_ALBUM": "Carrossel", "IMAGE": "Foto"}.get(p["tipo"], p["tipo"]),
                "visualizacoes": p.get("visualizacoes"), "curtidas": p["curtidas"], "comentarios": p["comentarios"], "interacoesPorHora": round(p["vel"], 1),
                "publicadoHaDias": round(p["horas"] / 24, 1), "link": p["link"],
                "origem": next((f"@{f['perfil']} ({p['mult']:.1f}x a média)" for f in p["fontes"] if f["tipo"] == "perfil"), f"#{p['fontes'][0].get('tag')}"),
                "legenda": re.sub(r"\s+", " ", p["legenda"]).strip()[:900],
            } for p in doTema],
        })
    def resumo(p):
        return {"nota": p["nota"], "formato": {"VIDEO": "Reels", "CAROUSEL_ALBUM": "Carrossel", "IMAGE": "Foto"}.get(p["tipo"], p["tipo"]),
                "visualizacoes": p.get("visualizacoes"), "curtidas": p["curtidas"], "comentarios": p["comentarios"],
                "interacoesPorHora": round(p["vel"], 1), "publicadoHaDias": round(p["horas"] / 24, 1), "link": p["link"],
                "temas": p["temas"], "legenda": re.sub(r"\s+", " ", p["legenda"]).strip()[:1200],
                "ts": datetime.fromtimestamp(p["ts"], timezone.utc).isoformat(timespec="seconds"), "thumb": p.get("thumb"),
                "tipo": p["tipo"], "mult": round(p["mult"], 2) if p.get("mult") is not None else None,
                "fontes": [{"tipo": f["tipo"], "tag": f.get("tag"), "perfil": f.get("perfil"), "tema": f.get("tema")} for f in p["fontes"]][:4]}
    saida["todos"] = [resumo(p) for p in sorted(todos, key=lambda p: -p["nota"])[:800]]
    publico = ROOT / "radar/coleta.json"   # lido pelo site: abre com os dados prontos
    publico.parent.mkdir(exist_ok=True)
    publico.write_text(json.dumps({"geradoEm": saida["geradoEm"], "conta": user, "postsAnalisados": len(todos), "avisos": avisos, "posts": saida["todos"]}, ensure_ascii=False) + "\n", encoding="utf-8")
    out = ROOT / f"dados/coleta-{datetime.now().strftime('%Y-%m-%d')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(saida, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out.relative_to(ROOT)}: {len(todos)} posts, {len(avisos)} avisos")


if __name__ == "__main__":
    main()
