# Radar Viral

Painel pessoal da Samyra (@samyra__duarte) que mostra posts em alta no Instagram nos temas dela e entrega pautas semanais.

- `index.html`: o sistema inteiro (página única, publicada no GitHub Pages em https://samyrabduarte-code.github.io/radar-viral/). A chave de acesso fica no navegador dela; nunca coloque chave no repositório.
- `config/temas.json`: temas, hashtags, palavras-chave e perfis usados pela coleta automática.
- `config/hashtag_ids.json`: cache dos IDs de hashtag (o Instagram permite 30 hashtags novas por semana; não apague).
- `scripts/coletar.py`: busca os posts em alta e grava `dados/coleta-AAAA-MM-DD.json`. Lê a chave da variável de ambiente `IG_TOKEN`.
- `pautas/`: edições semanais de pautas, lidas pela aba **Pautas** do sistema.
- `scripts/noticias.py`: busca notícias da semana de cada subtema (Google Notícias, sem chave) e grava `noticias/noticias.json` (aba **Notícias e react**).
- `formatos/formatos.json`: biblioteca de formatos validados (aba **Formatos**). `formatos/exemplos.json`: posts reais que usam cada formato, revisados um a um.
- `scripts/exemplos.py`: acha **candidatos** a exemplo por padrões de texto e grava `dados/candidatos-formatos.json`. Erra bastante; serve só como ponto de partida.

Escreva tudo em português do Brasil. Commits vão direto na branch `main` (é o que o GitHub Pages publica).

## Rotina semanal de pautas (toda quinta-feira)

1. Rode `python3 scripts/coletar.py`. Se falhar porque `IG_TOKEN` falta ou a chave expirou, **não invente dados**: crie a edição só com o campo `avisos` explicando o problema e o que a Samyra precisa fazer (gerar nova chave de 60 dias e atualizar `IG_TOKEN` no ambiente do Claude), publique e pare.
2. Rode `python3 scripts/noticias.py` (atualiza as notícias de todos os subtemas).
3. Leia o arquivo `dados/coleta-*.json` mais recente.
4. Para **cada subtema** que tiver posts, crie **3 pautas** (menos se o tema tiver poucos posts bons). Cada pauta se inspira em um post de referência real da coleta, preferindo notas altas e posts recentes.
5. Escreva também a **análise de por que viralizou** (campo `analise`, formato abaixo): um resumo da semana e, para cada tema com posts, 2 a 4 padrões observados (assunto, palavra, gancho, emoção, formato, CTA) e os 2 posts mais fortes explicados em linguagem simples. Baseie-se só nos posts e números da coleta.
6. Grave `pautas/AAAA-MM-DD.json` (data de hoje) no formato abaixo e acrescente a edição **no início** de `pautas/index.json`.
7. **Exemplos reais dos formatos.** Rode `python3 scripts/exemplos.py` e leia também a lista `todos` da coleta. Para cada formato de `formatos/formatos.json`, procure posts que **de fato** usam aquela fórmula (leia a legenda; na dúvida, não coloque) e acrescente em `formatos/exemplos.json` com os campos `link, formato, visualizacoes, curtidas, comentarios, nota, temas, trecho, achadoEm`. Máximo de 6 por formato: fique com os de maior nota e mais recentes. Dê atenção especial a posts de **lançamento** (vagas abertas, turma nova, carrinho, últimas vagas, prova social, contagem regressiva) e de **captação** (comente uma palavra, material gratuito, aula gratuita, lista VIP, teste) e coloque nos formatos com objetivo Lançamento ou Captação. Nunca use posts partidários, de sorteio ou golpe. Se aparecer uma fórmula nova que se repete em vários virais, crie o formato em `formatos/formatos.json` seguindo o mesmo padrão (id, nome, formato, objetivos, quandoUsar, estrutura, comoAplicar, modelo, exemplos).
8. Faça commit (`Pautas da semana AAAA-MM-DD`) e push para `main`, incluindo `noticias/`, `formatos/` e `config/hashtag_ids.json`. Não faça commit da pasta `dados/` (está no .gitignore).

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
