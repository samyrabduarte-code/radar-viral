#!/usr/bin/env python3
"""Encontra posts reais que usam cada formato validado, a partir da coleta mais recente.

Uso: python3 scripts/exemplos.py
Lê dados/coleta-*.json (a mais recente) e grava CANDIDATOS em dados/candidatos-formatos.json.
Os candidatos são achados por padrões de texto e erram bastante: revise um a um e copie
só os que realmente usam a fórmula para formatos/exemplos.json (ver CLAUDE.md).
"""
import json, re, unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POR_FORMATO = 6


def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s or "")) if unicodedata.category(c) != "Mn").lower()


# Cada regra olha a legenda (normalizada) e, às vezes, só a primeira linha e o tipo do post.
# "first" = primeira frase da legenda; "cap" = legenda inteira; "fmt" = Reels/Carrossel/Foto.
R = lambda p: re.compile(p)
REGRAS = {
    "lista-sinais": lambda f, c, fmt: bool(R(r"^\W*\d{1,2}\s+(sinais|erros|coisas|motivos|dicas|formas|maneiras|habitos|frases|atitudes|comportamentos|sintomas|tipos|segredos|licoes|beneficios)\b").search(f)),
    "passo-a-passo": lambda f, c, fmt: "passo a passo" in c or bool(R(r"^\W*como (fazer|montar|criar|conseguir|organizar|sair|limpar|aumentar|negociar|calcular|declarar)\b").search(f)),
    "checklist": lambda f, c, fmt: bool(R(r"\b(checklist|check-list|o que levar|lista do que|confira se)\b").search(c)),
    "mito-verdade": lambda f, c, fmt: bool(R(r"\b(mito ou verdade|mitos e verdades|mito x verdade|mito:|e mito)\b").search(c)),
    "verdade-mentira": lambda f, c, fmt: fmt == "Reels" and bool(R(r"\b(verdade ou mentira|verdade ou mito)\b").search(c)),
    "troque-isso": lambda f, c, fmt: bool(R(r"\b(troque|pare de dizer|em vez de dizer|ao inves de dizer|substitua)\b").search(f)),
    "glossario": lambda f, c, fmt: bool(R(r"\b(o que (e|significa)|voce sabe o que (e|significa)|significado de)\b").search(f)),
    "ironia-julgamento": lambda f, c, fmt: bool(R(r"^\W*[\"“].{5,80}(ne|ne\?)[\"”]?").search(f)) and bool(R(r"\b(realmente|claro|com certeza|sim!)\b").search(c)),
    "se-voce": lambda f, c, fmt: bool(R(r"^\W*se voce\b").search(f)),
    "carta-aberta": lambda f, c, fmt: bool(R(r"^\W*(para|pra) (voce|vc|a mae|a mulher|quem)\b").search(f)) or bool(R(r"^\W*querid[ao]s?\b").search(f)),
    "pergunta-polemica": lambda f, c, fmt: bool(R(r"\b(voce concorda|concorda\?|concordam\?|discorda|polemica|opiniao impopular)\b").search(c)),
    "comente-palavra": lambda f, c, fmt: bool(R(r"\b(comenta|comente)\s+[\"“']?[a-z0-9]{2,15}[\"”']?\s+(que|e|aqui|para|pra)\b").search(c)),
    "qual-voce-e": lambda f, c, fmt: bool(R(r"\b(qual (tipo|desses|dessas|deles|delas|voce e)|qual e o seu|com qual voce se identifica)\b").search(c)),
    "pov": lambda f, c, fmt: bool(R(r"^\W*pov\b").search(f)),
    "3-coisas": lambda f, c, fmt: bool(R(r"^\W*(3|tres) (coisas|erros|dicas|habitos|perguntas)\b").search(f)),
    "historia-virada": lambda f, c, fmt: len(R(r"\b(eu|minha|meu|comigo)\b").findall(c)) >= 6 and bool(R(r"\b(ate que|foi quando|hoje eu|descobri)\b").search(c)),
    "caixinha": lambda f, c, fmt: bool(R(r"\b(caixinha|me perguntaram|pergunta que recebi|perguntaram na)\b").search(c)),
    "respondendo-direct": lambda f, c, fmt: bool(R(r"\b(recebi (essa|uma|esta) mensagem|me mandaram no direct|chegou no (meu )?direct|mensagem que recebi)\b").search(c)),
    "react": lambda f, c, fmt: fmt == "Reels" and bool(R(r"\b(reagindo|react|vi esse video|viralizou|esse video)\b").search(c)),
    "pergunta-resposta": lambda f, c, fmt: fmt == "Reels" and f.strip().endswith("?") and len(f) < 140,
    "dado-surpreendente": lambda f, c, fmt: bool(R(r"(\d+([.,]\d+)?\s?%|\d+ em cada \d+|segundo (uma |o |a )?(pesquisa|estudo|dados|levantamento|ibge|oms))").search(f)),
    "antes-depois": lambda f, c, fmt: bool(R(r"\b(antes e depois|antes x depois|antes vs depois)\b").search(c)),
    "objecao": lambda f, c, fmt: bool(R(r"[\"“](e caro|nao tenho tempo|nao e pra mim|nao e para mim|vou pensar|depois eu vejo)").search(c)),
    "nota-repudio": lambda f, c, fmt: "nota de repudio" in c,
    "anuncio-misterio": lambda f, c, fmt: bool(R(r"\b(vem ai|em breve|novidade chegando|esta chegando|aguardem|contagem regressiva)\b").search(f)),
    "abertura-carrinho": lambda f, c, fmt: bool(R(r"\b(vagas abertas|inscricoes abertas|carrinho aberto|abrimos as (vagas|inscricoes)|nova turma|turma nova|matriculas abertas|agenda aberta)\b").search(c)),
    "prova-social": lambda f, c, fmt: bool(R(r"\b(resultado d[ao]s? (minha |meu |nossa |nosso )?(aluna|aluno|cliente|mentorad)|depoimento|olha o que (ela|ele) disse|case de sucesso)\b").search(c)),
    "contagem-regressiva": lambda f, c, fmt: bool(R(r"\b(ultimas vagas|ultimas horas|acaba hoje|encerra hoje|faltam \d+ (dias|horas|vagas)|ultimo dia|ultima chance)\b").search(c)),
    "oferta-comparativa": lambda f, c, fmt: bool(R(r"\b(voce recebe|tudo isso por|bonus exclusivo|bonus:|de r\$ ?\d+ por)\b").search(c)),
    "convite-aula": lambda f, c, fmt: bool(R(r"\b(aula gratuita|aula ao vivo|masterclass|workshop|webinar|imersao gratuita|evento gratuito|live (gratuita|amanha|hoje))\b").search(c)),
    "lista-vip": lambda f, c, fmt: bool(R(r"\b(lista vip|lista de espera|grupo vip|grupo exclusivo)\b").search(c)),
    "isca-material": lambda f, c, fmt: bool(R(r"\b(e-?book|guia gratuito|material gratuito|checklist gratuito|planilha gratuita|baixe (gratis|agora|o)|link na bio)\b").search(c)),
    "quiz-diagnostico": lambda f, c, fmt: bool(R(r"\b(descubra (se|qual|o seu|a sua|seu|sua)|faca o teste|teste:|quiz)\b").search(c)),
    "bastidores": lambda f, c, fmt: fmt == "Reels" and bool(R(r"\b(um dia (na vida|comigo)|bastidores|rotina de (uma|um))\b").search(c)),
    "preguicoso": lambda f, c, fmt: fmt == "Reels" and len(c) < 220,
    "estatico": lambda f, c, fmt: fmt == "Foto" and 40 < len(c) < 900,
    "carrossel-fundo-branco": lambda f, c, fmt: fmt == "Carrossel" and len(c) > 700 and not R(r"\b(vagas|inscric|link na bio)\b").search(c),
}


def main():
    coletas = sorted((ROOT / "dados").glob("coleta-*.json")) or [p for p in [ROOT / "radar/coleta.json"] if p.exists()]
    if not coletas:
        raise SystemExit("Nenhuma coleta em dados/. Rode scripts/coletar.py antes.")
    d = json.loads(coletas[-1].read_text(encoding="utf-8"))
    nomes = {t["id"]: t["nome"] for t in d.get("temas", [])}
    posts = d.get("todos") or d.get("posts")
    if not posts:  # coletas antigas: junta as listas por tema
        vistos = {}
        for t in d["temas"]:
            for p in t["posts"]:
                q = vistos.setdefault(p["link"], {**p, "temas": []})
                q["temas"].append(t["id"])
        posts = list(vistos.values())

    out_file = ROOT / "dados/candidatos-formatos.json"
    atual = {"formatos": {}}
    hoje = datetime.now(timezone.utc).date().isoformat()
    novos = 0
    for fid, regra in REGRAS.items():
        achados = []
        for p in posts:
            leg = p.get("legenda") or ""
            first = norm(re.split(r"(?<=[.!?])\s|\n", leg.strip(), maxsplit=1)[0])[:200]
            if p.get("link") and regra(first, norm(leg), p.get("formato")):
                achados.append({
                    "link": p["link"], "formato": p.get("formato"), "visualizacoes": p.get("visualizacoes"),
                    "curtidas": p.get("curtidas"), "comentarios": p.get("comentarios"), "nota": p.get("nota"),
                    "temas": [nomes.get(t, t) for t in p.get("temas", [])][:3],
                    "trecho": leg[:280] + ("…" if len(leg) > 280 else ""), "achadoEm": hoje,
                })
        lista = {e["link"]: e for e in atual["formatos"].get(fid, [])}
        for e in achados:
            if e["link"] not in lista:
                novos += 1
            lista[e["link"]] = e
        melhores = sorted(lista.values(), key=lambda e: (-(e.get("nota") or 0), -((e.get("curtidas") or 0) + 2 * (e.get("comentarios") or 0))))
        atual["formatos"][fid] = melhores[:POR_FORMATO]
    atual["geradoEm"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    out_file.write_text(json.dumps(atual, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    com = sum(1 for v in atual["formatos"].values() if v)
    print(f"dados/candidatos-formatos.json: {com} formatos com candidatos, {novos} candidatos")
    for fid, v in atual["formatos"].items():
        print(f"  {fid}: {len(v)}")


if __name__ == "__main__":
    main()
