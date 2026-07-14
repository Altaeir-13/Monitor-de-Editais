# Auditoria controlada de fontes nacionais

- Gerado em: `2026-07-14T14:45:02.656699Z`
- Páginas selecionadas: **5** (limite: 5)
- Regiões representadas: Centro-Oeste, Nordeste, Norte, Sudeste, Sul
- Spiders representados: generic, govbr, pagination, sigaa, wordpress
- Escopo: somente a página HTML inicial e o `robots.txt`; nenhum documento ou link listado foi aberto.
- Rede: execução sequencial, no máximo duas conexões simultâneas por host, intervalo mínimo de 1 segundo, timeout e dois retries.

## Resultado

- `manual_review`: 1
- `partial`: 2
- `verified`: 2

## Evidências por fonte

| Região | UF | Instituição | Fonte | Spider | Status | HTTP | Título | Evidência |
|---|---|---|---|---|---|---:|---|---|
| Norte | AM | UNIVERSIDADE FEDERAL DO AMAZONAS | inep-4-ufam-compec | generic | verified | 200 | Página inicial | HTML, título, termos de editais e elementos esperados confirmados; compatibilidade do spider é provável, sem executar coleta |
| Nordeste | SE | UNIVERSIDADE FEDERAL DE SERGIPE | inep-3-processos-seletivos-sigaa-ufs-cea9a10ed2 | sigaa | manual_review |  |  | robots.txt não permite esta URL para o agente da auditoria |
| Centro-Oeste | GO | UNIVERSIDADE ESTADUAL DE GOIÁS | inep-47-ueg-editais | pagination | partial | 200 | ::.Universidade Estadual de Goiás.:: | HTML acessível, mas faltam: elementos esperados para spider pagination |
| Sudeste | SP | CENTRO UNIVERSITÁRIO DAS FACULDADES ASSOCIADAS DE ENSINO - FAE | inep-217-editais-unifae | wordpress | verified | 200 | Editais - UNIFAE SÃO JOÃO DA BOA VISTA | HTML, título, termos de editais e elementos esperados confirmados; compatibilidade do spider é provável, sem executar coleta |
| Sul | PR | UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ | inep-588-utfpr-vestibular | govbr | partial | 200 | Vestibular | HTML acessível, mas faltam: elementos esperados para spider govbr |

## Pendências explícitas

- `inep-3-processos-seletivos-sigaa-ufs-cea9a10ed2` (UNIVERSIDADE FEDERAL DE SERGIPE): `manual_review` — robots_disallowed.
- `inep-47-ueg-editais` (UNIVERSIDADE ESTADUAL DE GOIÁS): `partial` — structure_partial.
- `inep-588-utfpr-vestibular` (UNIVERSIDADE TECNOLÓGICA FEDERAL DO PARANÁ): `partial` — structure_partial.

## Interpretação

`verified` nesta auditoria confirma DNS, HTTP, HTML, título, termos e elementos estruturais prováveis. Não equivale a captura validada nem a monitoramento ativo. `partial`, `manual_review`, `unsupported` e indisponibilidades permanecem pendentes, sem tentativa de evasão.
