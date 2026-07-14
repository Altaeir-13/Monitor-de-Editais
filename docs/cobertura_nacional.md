# Cobertura nacional

Data de referência desta versão: **14 de julho de 2026**.

Este documento define o contrato auditável do catálogo nacional. “Nacional”
descreve o inventário de instituições no escopo; não significa que todas já
tenham uma fonte verificada, uma captura validada ou monitoramento ativo.

O inventário institucional possui alcance nacional. A cobertura operacional das fontes permanece em validação progressiva.

## Totais reconciliados

Os totais abaixo descrevem o estado do catálogo versionado, não o resultado de
um crawler nacional:

| Métrica | Total |
|---|---:|
| Registros públicos no Censo 2024 | 317 |
| Registros censitários elegíveis | 315 |
| Instituições posteriores ao Censo | 3 |
| Inventário auditável completo | 320 |
| Alvo operacional elegível | 318 |
| Fontes no inventário completo | 303 |
| Fontes associadas às instituições elegíveis | 302 |
| Fontes associadas às instituições excluídas | 1 |
| Instituições elegíveis com ao menos uma fonte | 263 |
| Instituições elegíveis sem fonte | 55 |
| Instituições elegíveis em `verified` | 93 |
| Instituições elegíveis em `partial` | 165 |
| Instituições elegíveis em `manual_review` | 29 |
| Instituições elegíveis em `source_not_found` | 31 |
| Instituições elegíveis com captura validada | 0 |
| Instituições elegíveis em monitoramento ativo | 0 |

Os quatro status de cobertura por instituição (`verified`, `partial`,
`manual_review` e `source_not_found`) somam o alvo de 318. Eles não contam
URLs: uma instituição pode ter mais de uma fonte e uma instituição em revisão
manual pode já ter uma URL candidata. Por isso 263 instituições com fonte
correspondem a 302 fontes elegíveis.

### Distribuição regional

| Região | Inventário | Alvo elegível | Instituições com fonte | Fontes elegíveis |
|---|---:|---:|---:|---:|
| Centro-Oeste | 29 | 29 | 27 | 27 |
| Nordeste | 67 | 67 | 46 | 85 |
| Norte | 24 | 24 | 24 | 24 |
| Sudeste | 166 | 166 | 134 | 134 |
| Sul | 34 | 32 | 32 | 32 |
| **Brasil** | **320** | **318** | **263** | **302** |

O Sul possui 34 registros no inventário, mas somente 32 no alvo: a Universidade
do Contestado (código 441) permanece em revisão manual de escopo sem fonte, e o
antigo Centro Universitário de União da Vitória (código 649) permanece excluído
como inativo. A UNIUV conserva uma única fonte histórica inativa,
`inep-649-uniuv-editais-arquivo`. Essa fonte explica a diferença entre as 303
fontes do inventário e as 302 fontes elegíveis.

## Cinco estágios de cobertura

As métricas operacionais usam como denominador as instituições elegíveis no
filtro consultado; o inventário auditável preserva também as duas excluídas.

1. **Inventário nacional:** a instituição foi identificada em fonte oficial,
   normalizada e registrada no catálogo versionado.
2. **Fonte mapeada:** existe pelo menos uma URL oficial de editais ou conteúdo
   equivalente no manifesto regional.
3. **Fonte verificada:** a URL foi acessada, permaneceu em domínio oficial e a
   estrutura esperada foi observada.
4. **Captura validada:** um spider extraiu pelo menos um item válido em ensaio
   controlado ou fixture local representativa.
5. **Monitoramento ativo:** a fonte foi habilitada por decisão operacional e
   possui execução bem-sucedida recente.

O README, a API e a interface não devem reduzir esses cinco estágios a uma
única alegação de operação integral em todo o país.

## Fonte canônica e proveniência

A linha de base é o [Censo da Educação Superior 2024 do
Inep](https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior),
arquivo `microdados_censo_da_educacao_superior_2024.zip`. O gerador seleciona
somente o membro de cadastro de IES e aplica exatamente:

```text
NU_ANO_CENSO = 2024
TP_REDE = 1
```

O inventário bruto contém 317 registros. O membro usado é
`microdados_censo_da_educacao_superior_2024/dados/MICRODADOS_ED_SUP_IES_2024.CSV`.
Seus hashes conferidos são:

```text
MD5     dbe25e67857aa68b12beaeffa194f53f
SHA-256 aaa37fb9433d005686616bb9e48c5d7083526fdcc171973e787eed35a2ee349d
```

O manifesto MD5 oficial chama o mesmo conteúdo de
`MICRODADOS_CADASTRO_IES_2024.csv`; o gerador documenta essa divergência de
nome e exige igualdade byte a byte do hash.

O Censo registra a situação no ano de referência, mas não substitui a
confirmação jurídica atual. Por isso existe uma camada pequena e explícita de
revisão pós-Censo:

- código 649, antigo UNIUV: excluído do alvo operacional como inativo após a
  incorporação pela Unespar;
- código 441, Universidade do Contestado: mantido no inventário bruto, mas
  excluído do alvo automático para revisão de escopo, pois a classificação
  especial do Censo e a natureza jurídica exigem tratamento conservador;
- `LAW-15367-IFSPB`: Instituto Federal do Sertão Paraibano, criado pela Lei
  15.367/2026, ainda sem portal próprio confirmado;
- `LAW-15418-UNIND`: Universidade Federal Indígena, criada pela Lei
  15.418/2026, ainda em implantação;
- `LAW-15457-UFESPORTE`: Universidade Federal do Esporte, criada pela Lei
  15.457/2026, ainda em implantação.

As três criações posteriores ao Censo ficam incluídas no alvo com situação
`included_pending_activation`, sem inventar código Inep e sem ativar fonte.
Assim, o alvo operacional desta versão é 315 registros elegíveis do Censo mais
3 criações legais posteriores: **318 instituições**.

A [legislação do Censo e a relação de não
respondentes](https://www.gov.br/inep/pt-br/centrais-de-conteudo/legislacao/censo-da-educacao-superior)
formam uma trilha de conferência, não uma lista para inclusão automática.
Instituições ausentes do arquivo canônico só entram por sobreposição oficial,
documentada e revisável.

## Arquivos e regeneração

- `backend/scripts/update_inep_catalog.py`: download seletivo por intervalos,
  validação de ZIP e hashes, extração e normalização;
- `backend/app/catalog/institutions_2024.json`: inventário normalizado e
  determinístico;
- `backend/app/catalog/post_census_2024.json`: sobreposição jurídica posterior;
- `backend/app/catalog/sources/*.json`: um manifesto para cada região;
- `backend/scripts/build_northeast_manifest.py`: converte o seed Nordeste
  legado para o contrato nacional;
- `backend/app/catalog/loader.py`: valida e consolida os arquivos sem rede.

O ZIP bruto não deve ser versionado. Para regenerar a partir da fonte oficial:

```powershell
Set-Location .\backend
.\venv\Scripts\python.exe .\scripts\update_inep_catalog.py
.\venv\Scripts\python.exe .\scripts\build_northeast_manifest.py
.\venv\Scripts\python.exe .\tests\test_national_catalog.py
.\venv\Scripts\python.exe .\tests\test_source_manifests.py
.\venv\Scripts\python.exe .\tests\test_catalog_eligibility.py
Get-FileHash .\app\catalog\institutions_2024.json -Algorithm SHA256
Get-FileHash .\app\catalog\post_census_2024.json -Algorithm SHA256
Get-ChildItem .\app\catalog\sources\*.json | Get-FileHash -Algorithm SHA256
```

O primeiro comando lê apenas os intervalos do ZIP necessários ao membro de IES,
impõe limites de tamanho, valida CRC e hashes e troca o arquivo de saída de
forma atômica. O hash SHA-256 do membro canônico deve continuar igual a
`aaa37fb9433d005686616bb9e48c5d7083526fdcc171973e787eed35a2ee349d`. Também
aceita `--csv <caminho>` para reprodução offline a partir
de um membro já extraído. Não mantenha o arquivo bruto dentro do repositório.

## Campos do inventário

Cada instituição possui:

- `official_code`, com código Inep ou identificador `LAW-*` explicitamente
  qualificado;
- nome e sigla oficiais, além da origem da sigla de fallback;
- região, UF, município-sede e código de município;
- categoria administrativa e organização acadêmica, com código e rótulo;
- situação censitária, situação atual e elegibilidade;
- URL institucional quando confirmada;
- URL e data de referência da proveniência;
- situação da descoberta de fontes e observações.

Siglas ausentes no Censo não são deixadas vazias: recebem `IES-<código>` e o
campo `initials_origin=generated_fallback`. Isso evita colisões sem apresentar a
sigla gerada como oficial.

Cada fonte regional registra:

- identificador estável, instituição, URL normalizada e nome;
- tipo de conteúdo e spider recomendado;
- `verified`, `partial`, `source_not_found`, `temporarily_unavailable`,
  `manual_review`, `unsupported` ou `inactive`;
- data, HTTP, URL final, redirects, título e evidência quando aplicáveis;
- prioridade de 1 a 3, categorias de edital e observações;
- data/evidência de captura e URLs substituídas.

Instituições sem URL permanecem no manifesto com `sources=[]`; elas não somem
dos totais nem das pendências.

## Escopo

Incluem-se instituições públicas de educação superior classificadas na rede
pública do Censo, incluindo universidades federais, estaduais e municipais,
institutos federais, CEFETs, centros universitários, faculdades públicas e
instituições públicas equivalentes. Instituições militares só entram quando
presentes na linha de base ou confirmadas por ato oficial e com conteúdo
relevante ao produto.

Excluem-se instituições privadas, comunitárias ou confessionais privadas,
instituições extintas/incorporadas e registros sem confirmação oficial. Uma
incerteza jurídica recebe `manual_review`; não é resolvida por Wikipédia, blog,
agregador ou mecanismo de busca.

## Descoberta e verificação de fontes

O mecanismo de busca pode localizar candidatos, mas a evidência final deve ser
o domínio oficial da instituição ou do ente público responsável. A ordem de
preferência é: página específica de editais, processos seletivos, chamadas,
bolsas, pesquisa, extensão, pós-graduação, graduação e assistência estudantil;
notícias gerais são fallback. Licitações só são mapeadas quando fizerem parte
do escopo do produto.

Na descoberta em massa não se abrem documentos nem se executa o crawler
nacional. A auditoria controlada:

- usa no máximo duas conexões simultâneas por host e intervalo mínimo de um
  segundo;
- envia User-Agent identificável, timeout e no máximo duas novas tentativas;
- consulta `robots.txt`, limita redirects e lê no máximo 1 MB da página HTML;
- recusa endereços não públicos, credenciais em URL e arquivos/documentos;
- não contorna CAPTCHA, autenticação, Cloudflare ou outro controle de acesso;
- marca bloqueios como `manual_review` ou `unsupported`.

O script de auditoria escolhe uma amostra determinística que cobre todas as
regiões e todos os spiders presentes. A ativação operacional continua sendo um
gate manual.

## Classificação dos spiders

Use o factory atual antes de propor implementação nova:

- `generic`: HTML estático sem padrão mais específico;
- `wordpress`: listas e posts WordPress;
- `govbr`: portais Gov.br/Plone;
- `sigaa`: páginas públicas SIGAA/JSF;
- `pagination`: tabelas, portais de processo e listas paginadas.

Um spider novo só deve existir depois de confirmar a inadequação dos atuais,
agrupar fontes com a mesma estrutura, estimar o benefício e criar fixtures
locais. Não se cria um spider por universidade.

## Seed nacional

O serviço nacional carrega o catálogo consolidado e só persiste instituições
cujo `eligibility_status` começa com `included`. Ele consolida por código
oficial e só usa sigla + UF como fallback legado quando a correspondência é
única. É possível selecionar uma região ou todas.

O endpoint `POST /api/admin/seed-national` é exposto pelo contrato público sob
Nginx; diretamente no FastAPI, sem `API_ROOT_PATH=/api`, a rota equivalente
não inclui o prefixo `/api`. O endpoint legado
`POST /api/admin/seed-northeast` permanece como wrapper do mesmo serviço com
filtro Nordeste, preservando integrações existentes. Ambos exigem autenticação
administrativa.

Regras de atualização:

- um único commit de banco ao final e rollback integral em erro;
- instituições excluídas permanecem auditáveis no arquivo e não são inseridas;
- campos canônicos e de proveniência podem ser atualizados;
- `name`, `initials`, logo, ativação e site manual não vazio são preservados;
- fontes são consolidadas por identificador, URL normalizada e `replaces`;
- frequência, execução, erro e ativação operacionais são preservados;
- fontes novas sempre começam inativas;
- o resultado separa instituições e fontes criadas, atualizadas e ignoradas,
  além de pendências e itens em revisão manual.

## API e painel

O contrato administrativo implementado é protegido pela mesma autenticação de
administrador usada nas demais rotas:

- `GET /api/admin/coverage`: resumo dos estágios e totais reconciliados;
- `GET /api/admin/coverage/regions`: distribuição regional;
- `GET /api/admin/coverage/institutions`: lista auditável e filtrável;
- `POST /api/admin/seed-national`: seed nacional idempotente, opcionalmente por
  região.

Os filtros disponíveis incluem região, UF, categoria administrativa, organização
acadêmica, elegibilidade, cobertura, verificação, ativação da instituição e da
fonte, presença ou ausência de fonte e revisão manual. O painel sempre
exibir separadamente inventário, fonte mapeada, fonte verificada, captura
validada e monitoramento ativo. Enquanto não houver evidência registrada, os
dois últimos totais nacionais permanecem em zero.

## Auditoria amostral de 14/07/2026

A execução controlada consultou cinco landing pages: uma por região e uma para
cada família de spider (generic, sigaa, pagination, wordpress e govbr). A
seleção incluiu fontes previamente classificadas como verified e partial,
respeitou robots.txt, usou timeout de 8 segundos, User-Agent identificável e
não abriu documentos, autenticou ou contornou bloqueios.

O resultado da amostra foi:

- 2 fontes verified: UFAM (generic) e UNIFAE (wordpress);
- 2 fontes partial: UEG (pagination) e UTFPR (govbr), com HTML acessível, mas
  sem todos os elementos estruturais esperados;
- 1 fonte manual_review: UFS (sigaa), interrompida porque robots.txt recusou o
  agente da auditoria.

Os relatórios completos estão em
[auditoria_fontes_nacional.md](auditoria_fontes_nacional.md) e
[auditoria_fontes_nacional.json](auditoria_fontes_nacional.json). O resultado
não altera automaticamente manifestos, não ativa fontes, não valida captura e
não sustenta inferência sobre toda a operação nacional.

## Atualização e manutenção

Revalide URLs pelo menos trimestralmente e sempre que um host começar a falhar.
A cada novo Censo, baixe ou forneça offline o membro oficial de IES, confira os
hashes publicados, atualize o ano e os filtros no gerador, regenere o JSON
determinístico e reconcilie os cinco manifestos regionais. Atos posteriores
permanecem em overlay até aparecerem no arquivo do Inep; quando isso ocorrer,
migre-os para a linha de base sem perder a trilha de proveniência. Revise o
diff, os totais, as exclusões, os checksums e os testes antes de aceitar a nova
geração.

Para adicionar uma instituição:

1. confirme a fonte oficial e a elegibilidade;
2. prefira a regeneração do Censo; use overlay somente para mudança posterior;
3. registre código/origem, data e situação;
4. adicione ou atualize a entrada no manifesto regional;
5. execute os testes de catálogo e seed.

Para adicionar uma fonte:

1. confirme a URL no domínio oficial;
2. normalize a URL e atribua um `catalog_source_id` estável;
3. classifique conteúdo, spider, status, evidência, prioridade e categorias;
4. mantenha `is_active=false` até captura validada e decisão operacional;
5. execute os testes de manifesto e a auditoria amostrada.

Para adicionar um spider:

1. documente por que os spiders existentes não servem e quantas fontes se
   beneficiam;
2. implemente o padrão reutilizável no factory;
3. acrescente fixture HTML local e testes sem rede;
4. faça uma captura controlada e registre evidência;
5. só então altere a recomendação das fontes compatíveis.

## Limitações desta versão

- o Censo 2024 não traz URL institucional nem prova de situação jurídica atual;
- várias fontes são compartilhadas por mantenedoras estaduais e precisam de
  confirmação por instituição;
- `partial` significa fonte oficial candidata, não estrutura completamente
  confirmada;
- cadastro, captura e monitoramento são métricas distintas;
- instituições posteriores ao Censo ainda não possuem código Inep;
- a auditoria controlada não substitui observação de execuções no ambiente
  operacional.

O relatório nacional gerado lista os números atuais e cada instituição ainda
pendente, com seu motivo, sem esconder falhas em totais agregados.
