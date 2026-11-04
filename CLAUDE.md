# Radar Viral

Painel pessoal da Samyra (@samyra__duarte) que mostra posts em alta no Instagram nos temas dela e entrega pautas semanais.

- `index.html`: o sistema inteiro (página única, publicada no GitHub Pages em https://samyrabduarte-code.github.io/radar-viral/). A chave de acesso fica no navegador dela; nunca coloque chave no repositório.
- `config/temas.json`: temas, hashtags, palavras-chave e perfis usados pela coleta automática.
- `config/hashtag_ids.json`: cache dos IDs de hashtag (o Instagram permite 30 hashtags novas por semana; não apague).
- `scripts/coletar.py`: busca os posts em alta, **primeiro pelos perfis de referência** (a busca principal, parecida com SEO: quem fala do tema) e depois pelas hashtags (complemento). Grava `radar/coleta.json` (público, lido pelo site) e `dados/coleta-AAAA-MM-DD.json`. Lê a chave de `IG_TOKEN`; `RADAR_PAUSA` (segundos entre consultas) evita estourar o limite de ~200 consultas por hora.
- `.github/workflows/radar.yml`: **coleta automática todo dia às 4h07** no GitHub (notícias + posts + às segundas, perfis novos). A chave fica no segredo `IG_TOKEN` do repositório no GitHub.
- `scripts/descobrir_perfis.py`: descobre quem postou os virais e cadastra os melhores perfis de cada subtema em `config/temas.json` (`profiles`). Perfis recusados ficam em `perfisRecusados` e não voltam.
- `pautas/`: edições semanais de pautas, lidas pela aba **Pautas** do sistema.
- `scripts/noticias.py`: busca notícias da semana de cada subtema (Google Notícias, sem chave) e grava `noticias/noticias.json` (aba **Notícias e react**).
- `formatos/formatos.json`: biblioteca de formatos validados (aba **Formatos**). `formatos/exemplos.json`: posts reais que usam cada formato, revisados um a um.
- `scripts/exemplos.py`: acha **candidatos** a exemplo por padrões de texto e grava `dados/candidatos-formatos.json`. Erra bastante; serve só como ponto de partida.

Escreva tudo em português do Brasil. Commits vão direto na branch `main` (é o que o GitHub Pages publica).

## Rotina semanal de pautas (toda quinta-feira)

1. Use os dados da coleta automática: `radar/coleta.json` (campo `posts`; cada post tem `temas`, `fontes`, números, `legenda` e `link`). Se o `geradoEm` tiver mais de 2 dias, a coleta diária falhou: se houver `IG_TOKEN` neste ambiente, rode `python3 scripts/coletar.py`; se não, **não invente dados**, crie a edição só com `avisos` explicando que a coleta automática parou e que a Samyra precisa conferir o segredo `IG_TOKEN` no GitHub (Settings → Secrets and variables → Actions) ou gerar uma nova chave de 60 dias, publique e pare.
2. As notícias (`noticias/noticias.json`) são atualizadas todo dia pelo GitHub; se estiverem com mais de 2 dias, rode `python3 scripts/noticias.py`.
3. Leia `radar/coleta.json` e a lista de subtemas em `config/temas.json`.
4. Para **cada subtema** que tiver posts, crie **3 pautas** (menos se o tema tiver poucos posts bons). Cada pauta se inspira em um post de referência real da coleta, preferindo notas altas e posts recentes.
5. Escreva também a **análise de por que viralizou** (campo `analise`, formato abaixo): um resumo da semana e, para cada tema com posts, 2 a 4 padrões observados (assunto, palavra, gancho, emoção, formato, CTA) e os 2 posts mais fortes explicados em linguagem simples. Baseie-se só nos posts e números da coleta.
6. Grave `pautas/AAAA-MM-DD.json` (data de hoje) no formato abaixo e acrescente a edição **no início** de `pautas/index.json`.
7. **Exemplos reais dos formatos.** Rode `python3 scripts/exemplos.py` e leia também a lista `todos` da coleta. Para cada formato de `formatos/formatos.json`, procure posts que **de fato** usam aquela fórmula (leia a legenda; na dúvida, não coloque) e acrescente em `formatos/exemplos.json` com os campos `link, formato, visualizacoes, curtidas, comentarios, nota, temas, trecho, achadoEm`. **Só some, nunca apague:** mantenha todos os exemplos que já existem e acrescente os novos (sem repetir o mesmo link). Ordene cada lista do mais forte para o mais fraco (nota, depois curtidas + comentários). Dê atenção especial a posts de **lançamento** (vagas abertas, turma nova, carrinho, últimas vagas, prova social, contagem regressiva) e de **captação** (comente uma palavra, material gratuito, aula gratuita, lista VIP, teste) e coloque nos formatos com objetivo Lançamento ou Captação. Nunca use posts partidários, de sorteio ou golpe. Também nunca remova nem reescreva formatos que já existem em `formatos/formatos.json`; a biblioteca só cresce. Se aparecer uma fórmula nova que se repete em vários virais, crie o formato em `formatos/formatos.json` seguindo o mesmo padrão (id, nome, formato, etapas, objetivos, quandoUsar, estrutura, comoAplicar, modelo, exemplos).
8. **Conferência visual dos exemplos.** Vários formatos dependem do visual (meme, print de tweet, print de WhatsApp, cartoon, fundo branco, preguiçoso em vídeo). Antes de salvar um exemplo novo, abra o post: monte uma página HTML com o embed do Instagram (`<blockquote class="instagram-media" data-instgrm-permalink="LINK">` + `https://www.instagram.com/embed.js`), tire um print com o Playwright (já instalado) e olhe a imagem. Se o visual não bater com o formato, mude de formato ou descarte.
9. **Pesquisa semanal de formatos novos, por etapa do funil.** Toda semana, pesquise e acrescente **pelo menos 3 formatos novos** em `formatos/formatos.json`: pelo menos 1 de **Topo** (atrair gente nova), 1 de **Meio** (confiança e autoridade) e 1 de **Fundo** (vendas: lançamento, oferta, objeção, prova, pós-venda). Fontes: os posts virais da coleta (fórmulas que se repetem), os perfis de referência e pesquisa na web sobre formatos de conteúdo e vendas no Instagram que estão funcionando no Brasil. Cada formato precisa de `etapas` (lista com "Topo", "Meio" e/ou "Fundo"), além dos outros campos, e de preferência já com exemplos reais conferidos. Não repita formatos que já existem com outro nome.
10. Faça commit (`Pautas da semana AAAA-MM-DD`) e push para `main`, incluindo `noticias/`, `formatos/` e `config/hashtag_ids.json`. Não faça commit da pasta `dados/` (está no .gitignore).

### Como escrever as pautas

- **Modelagem, não cópia.** A Samyra quer replicar o que viraliza: mantenha a **fórmula** do post de referência (tipo de gancho, estrutura, ritmo, virada, tamanho e tom) o mais próxima possível, mas escreva o texto com palavras, exemplos e números diferentes. Nunca reproduza frases do original nem troque só algumas palavras: isso é cópia, pode gerar denúncia e queda de alcance.
- `estrutura` descreve o esqueleto do post de referência, passo a passo (ex.: "frase de julgamento entre aspas → concordância irônica → lista do que custa → arremate irônico").
- `textoPronto` é o post **pronto para publicar**, seguindo a mesma estrutura: para Foto, o texto da arte; para Carrossel, o texto de cada slide ("Slide 1: ..."); para Reels, o roteiro falado por cena. Use quebras de linha (\n).
- `ideia` é a **ideia de replicação**: como produzir (visual, legenda, CTA) e o que adaptar ao perfil dela.
- `porQueFunciona` explica o mecanismo que fez o post de referência performar (dor, polêmica, identificação, utilidade, salvar para depois etc.).
- Temas de saúde mental: linguagem responsável, sem prometer cura, sem diagnóstico pelo post, sem estigmatizar; quando fizer sentido, oriente procurar avaliação profissional.
- Temas de finanças e tributação: não prometa resultado financeiro; números e regras precisam ser verificáveis ou apresentados como exemplo.
- Ignore posts de referência que sejam golpe, sorteio ou conteúdo sem relação real com o tema.
- **Política e economia** é um subtema desejado (impostos, juros, decisões do governo e do Congresso que mexem no bolso). Explique o impacto prático para o público, com fatos verificáveis, sem tomar partido nem atacar políticos; ignore posts de campanha eleitoral ou de ataque pessoal.

### Formato de `pautas/AAAA-MM-DD.json`

```json
{
  "edicao": "2026-11-06",
  "geradoEm": "2026-11-06T09:47:00Z",
  "postsAnalisados": 812,
  "avisos": [],
  "temas": [
    {
      "id": "tdah",
      "nome": "TDAH",
      "painel": "Saúde mental e neuro",
      "pautas": [
        {
          "titulo": "Frase curta que resume a pauta",
          "formato": "Carrossel",
          "gancho": "Primeira frase/tela do post",
          "estrutura": "Esqueleto do post de referência, passo a passo",
          "textoPronto": "Post pronto para publicar, mesma fórmula, texto novo",
          "ideia": "Ideia de replicação: como produzir, legenda e CTA",
          "porQueFunciona": "Por que o post de referência performou",
          "referencia": { "link": "https://www.instagram.com/p/...", "formato": "Reels", "curtidas": 9025, "comentarios": 896, "nota": 93, "resumo": "Do que o post de referência fala, em uma frase" }
        }
      ]
    }
  ]
}
```

`formato` é `Reels`, `Carrossel` ou `Foto`. Copie os campos `avisos` da coleta para a edição.

O campo `analise` fica no mesmo arquivo, ao lado de `temas`, e aparece na aba **Por que viraliza**:

```json
"analise": {
  "resumo": "2 ou 3 frases sobre o que mais viralizou na semana",
  "temas": [
    {
      "id": "tdah",
      "nome": "TDAH",
      "padroes": ["Padrão observado nos virais deste tema"],
      "destaques": [
        { "link": "https://www.instagram.com/p/...", "formato": "Carrossel", "curtidas": 9025, "comentarios": 896, "nota": 93,
          "porQueViralizou": "Explicação simples: assunto, gancho, emoção, palavra ou CTA que fez o post performar",
          "gatilhos": ["identificação", "lista prática"] }
      ]
    }
  ]
}
```

### Formato de `pautas/index.json`

```json
{ "edicoes": [ { "arquivo": "2026-11-06.json", "edicao": "2026-11-06", "total": 33 } ] }
```
