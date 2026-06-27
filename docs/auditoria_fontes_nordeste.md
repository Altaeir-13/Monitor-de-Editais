# Auditoria de fontes do Nordeste

Gerado em: 2026-06-27 16:22:13 UTC
Banco usado: `sqlite:///C:/Users/Altair/Documents/Editais/backend/audit_northeast_initial.db`

## Escopo

Instituicoes auditadas: UFPI, UFMA, UFC, UFRN, UFPE, UFBA, IFPI, IFCE, IFRN, UEMA, UESPI, UEPB, UNEB, UPE, IFBA
Catalogo carregado: 44 instituicoes, 83 fontes.
Fontes testadas neste relatorio: 27

## Seed

Primeira execucao: `{"institutions_created": 44, "institutions_updated": 0, "sources_created": 83, "sources_updated": 0}`
Segunda execucao: `{"institutions_created": 0, "institutions_updated": 44, "sources_created": 0, "sources_updated": 83}`
Idempotencia: ok, sem novas instituicoes/fontes na segunda execucao.

## Resumo do crawler

Primeira execucao: `{"sources_checked": 27, "items_found": 1534, "new_items": 1256, "failed_sources": 1}`
Segunda execucao (duplicidade): `{"sources_checked": 27, "items_found": 1534, "new_items": 0, "failed_sources": 1}`
Instituicoes com pelo menos 1 edital salvo: 14 (IFBA, IFCE, IFPI, IFRN, UEMA, UEPB, UESPI, UFBA, UFC, UFMA, UFPI, UFRN, UNEB, UPE)
Editais ativos recuperados para o escopo: 1256
Fontes funcionais: 20
Fontes funcionais parciais: 4
Fontes falhas/sem captura util: 3

Tipos encontrados: bolsa=71, concurso=118, convocacao=39, edital=529, homologacao=34, licitacao=4, pregao=5, processo_seletivo=300, resultado=125, retificacao=31

## Amostras de editais salvos

- `retificacao` UPE - Retificação do Resultado dos Recursos da Autodeclaração do Processo de Heteroidentificação (Candidatos Remanejáveis) - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202602231601_-_RETIFICACAO_DO_RESULTADO_DOS_RECURSOS_DA_AUTODECLARACAO_DO_PROCESSO_DE_HETEROIDENTIFICACAO_-_Candidatos_Remanejaveis.pdf
- `resultado` UPE - Resultado Final da Autodeclaração do Processo de Heteroidentificação(Candidatos Remanejáveis) - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202602221317_-_Resultado_Final_da_Autodeclaracao_do_Processo_de_Heteroidentificacao_-_Candidatos_Remanejaveis.pdf
- `resultado` UPE - Resultado dos Recursos da Autodeclaração do Processo de Heteroidentificação(Candidatos Remanejáveis) - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202602221316_-_Resultado_dos_Recursos_da_Autodeclaracao_do_Processo_de_Heteroidentificacao_-_Candidatos_Remanejaveis.pdf
- `resultado` UPE - Resultado Preliminar dos Candidatos Remanejáveis da Autodeclaração do Processo de Heteroidentificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202602121120_-_RESULTADO_PRELIMINAR_ETAPA_DE_HETEROIDENTIFICACAO-CANDIDATOS_REMANEJAVEIS_SSA3.pdf
- `resultado` UPE - Resultado Final da Autodeclaração do Processo de Heteroidentificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202601281623_-_Resultado_Final_da_Autodeclaracao_do_Processo_de_Heteroidentificacao.pdf
- `resultado` UPE - Resultado do Recurso da Autodeclaração do Processo de Heteroidentificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202601281155_-_Resultado_do_Recurso_da_Autodeclaracao_do_Processo_de_Heteroidentificacao.pdf
- `resultado` UPE - Resultado Preliminar da Autodeclaração do Processo de Heteroidentificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202601241346_-_SSA3_2026-RESULTADO_PRELIMINAR_CLASSIFICADOS_HETEROIDENTIFICACAO.pdf
- `edital` UPE - Errata do Edital de Procedimento de Heteroidentificação e Verificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202601151846_-_ERRATA_DO_EDITAL_DE_PROCEDIMENTO_DE_HETEROIDENTIFICACAO_SSA3.pdf
- `edital` UPE - Edital de Procedimento de Heteroidentificação e Verificação - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202601121932_-_SSA_3_2026_-_EDITAL_N_1_-_PROCEDIMENTO_DE_HETEROIDENTIFICACAO_E_VERIFICACAO.pdf
- `resultado` UPE - Resultado Final das Solicitações de Regime Especial - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202508051620_-_Resultado_Final_-_Solicitacao_de_Regime_Especial_SSA_3_2026.pdf
- `resultado` UPE - Resultado das Solicitações de Regime Especial - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202507291404_-_Resultado_-_Solicitacao_de_Regime_Especial_SSA_3_2026.pdf
- `resultado` UPE - Resultado dos Recursos das Solicitações de Isenção - NIS - https://processodeingresso.upe.pe.gov.br/arquivos/ssa3_2026/202507081602_-_RESULTADO_NIS_SSA3_RECURSO.pdf

## Verificacao de duplicidade

Novos itens na segunda execucao: 0
A segunda execucao nao criou novos registros no escopo; nao houve duplicidade indevida detectada.

## Filtros por tipo

| notice_type | Registros no escopo | Amostra via listagem publica | Exemplos |
| --- | ---: | ---: | --- |
| `edital` | 529 | 5 | Errata do Edital de Procedimento de Heteroidentificação e Verificação; Edital de Procedimento de Heteroidentificação e Verificação; Errata 2 do Edital de Matrícula e Remanejamentos |
| `concurso` | 118 | 5 | Concursos UPE; UPE lança edital de vídeos sobre sustentabilidade para transformar metas da Agenda 2030 em soluções locais; UPE, Ministério Público do Trabalho e IAUPE firmam par... |
| `processo_seletivo` | 300 | 5 | Publicação no Diário Oficial de Pernambuco - Aviso de Alteração da Data de Realização de Provas da Seleção Pública para Ingresso nas Esco...; RESOLUÇÃO CONSUN Nº 014/2026 - Regu... |
| `licitacao` | 4 | 4 | Licitações, Contratos e Fornecedores; Governo de Pernambuco e UPE anunciam investimentos iniciais de 11,4 milhões para a requalificação do Hospital Universitário Oswaldo Cruz; U... |
| `pregao` | 5 | 5 | Aviso de licitação do Pregão Eletrônico Nº 013/2022; Errata ao aviso de licitação &#8211; PREGÃO ELETRÔNICO Nº 013/2022; PREGÃO ELETRÔNICO Nº. 014/2022 – FUESPI |
| `resultado` | 125 | 5 | Resultado Final da Autodeclaração do Processo de Heteroidentificação(Candidatos Remanejáveis); Resultado dos Recursos da Autodeclaração do Processo de Heteroidentificação(Candid... |
| `retificacao` | 31 | 5 | Retificação do Resultado dos Recursos da Autodeclaração do Processo de Heteroidentificação (Candidatos Remanejáveis); Comunicado Sobre a Prorrogação das Inscrições SSA3; Comunic... |
| `homologacao` | 34 | 5 | Cláudia Gusmão, primeira mulher indicada como general no Brasil, tem formação na UPE; UPE lança edital de Inovação Pedagógica 2026; UPE divulga edital de Apoio à Vivência de Com... |
| `convocacao` | 39 | 5 | UPE abre inscrições para palestrantes voluntários em ações de qualidade de vida no trabalho; UPE divulga edital PROGRAD nº 12/2026 – Seleção de Estudantes à Mobilidade Acadêmica... |
| `bolsa` | 71 | 5 | UPE representa universidades estaduais em fórum nacional de pró-reitores em Brasília; UPE abre edital de Auxílio Deslocamento para estudantes de graduação; UPE inicia turmas do... |

## Fontes auditadas

### IFBA - Portal IFBA - descoberta

- Instituicao: Instituto Federal da Bahia (IFBA)
- Fonte: Portal IFBA - descoberta
- URL: https://portal.ifba.edu.br/
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://portal.ifba.edu.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (188051 bytes, 235 links)
- Itens encontrados: 2
- Novos itens salvos: 2
- Editais validos: 2
- Links de amostra que abriram: 2/2
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `edital` 1 Edital Simplificado Unificado 2026.2 - https://portal.ifba.edu.br/banner/banner-home/edital-simplificado-unificado-2026.2/view
  - `concurso` Abertas inscrições de concurso para escolha de logotipo das Cipeas a partir de amanhã, 19 - https://portal.ifba.edu.br/noticias/2026/abertas-inscricoes-de-concurso-para-escolha-de-logotipo-das-cipeas-a-partir-de-amanha-19

### IFCE - Processos seletivos IFCE

- Instituicao: Instituto Federal do Ceara (IFCE)
- Fonte: Processos seletivos IFCE
- URL: https://portal.ifce.edu.br/processos-seletivos/buscar/
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://portal.ifce.edu.br/processos-seletivos/buscar/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (83353 bytes, 205 links)
- Itens encontrados: 51
- Novos itens salvos: 51
- Editais validos: 51
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Bolsas para Estudantes - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=1
  - `concurso` Concursos culturais - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=8
  - `concurso` Empreenda no IFCE - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=6

### IFCE - Trabalhe no IFCE

- Instituicao: Instituto Federal do Ceara (IFCE)
- Fonte: Trabalhe no IFCE
- URL: https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=3
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=3`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (77939 bytes, 196 links)
- Itens encontrados: 50
- Novos itens salvos: 41
- Editais validos: 50
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Bolsas para Estudantes - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=1
  - `concurso` Concursos culturais - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=8
  - `concurso` Empreenda no IFCE - https://portal.ifce.edu.br/processos-seletivos/buscar/?tipo=6

### IFPI - Chamadas publicas IFPI

- Instituicao: Instituto Federal do Piaui (IFPI)
- Fonte: Chamadas publicas IFPI
- URL: https://www.ifpi.edu.br/chamadas-publicas
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.ifpi.edu.br/chamadas-publicas`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (95138 bytes, 107 links)
- Itens encontrados: 12
- Novos itens salvos: 12
- Editais validos: 12
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Concursos Públicos - https://www.ifpi.edu.br/processos-seletivos/concursos
  - `concurso` Exame Classificatório - http://selecao.ifpi.edu.br
  - `concurso` Seletivos - https://www.ifpi.edu.br/processos-seletivos/concursos-e-seletivos

### IFPI - Concursos IFPI

- Instituicao: Instituto Federal do Piaui (IFPI)
- Fonte: Concursos IFPI
- URL: https://www.ifpi.edu.br/processos-seletivos/concursos
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.ifpi.edu.br/processos-seletivos/concursos`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (95187 bytes, 105 links)
- Itens encontrados: 8
- Novos itens salvos: 2
- Editais validos: 8
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Concursos Públicos - https://www.ifpi.edu.br/processos-seletivos/concursos
  - `concurso` Exame Classificatório - http://selecao.ifpi.edu.br
  - `concurso` Seletivos - https://www.ifpi.edu.br/processos-seletivos/concursos-e-seletivos

### IFPI - Seletivos IFPI

- Instituicao: Instituto Federal do Piaui (IFPI)
- Fonte: Seletivos IFPI
- URL: https://www.ifpi.edu.br/processos-seletivos/concursos-e-seletivos
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.ifpi.edu.br/processos-seletivos/concursos-e-seletivos`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (95207 bytes, 102 links)
- Itens encontrados: 7
- Novos itens salvos: 1
- Editais validos: 7
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Concursos Públicos - https://www.ifpi.edu.br/processos-seletivos/concursos
  - `concurso` Exame Classificatório - http://selecao.ifpi.edu.br
  - `concurso` Seletivos - https://www.ifpi.edu.br/processos-seletivos/concursos-e-seletivos

### IFRN - Processos seletivos IFRN

- Instituicao: Instituto Federal do Rio Grande do Norte (IFRN)
- Fonte: Processos seletivos IFRN
- URL: https://processoseletivo.ifrn.edu.br/
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://processoseletivo.ifrn.edu.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (284203 bytes, 1152 links)
- Itens encontrados: 573
- Novos itens salvos: 573
- Editais validos: 573
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `edital` EDITAL Nº 36/2026-PROPI/IFRN – Especialização em Educação Ambiental e Geografia do Semiárido - CONVÊNIO INCRA - https://processoseletivo.ifrn.edu.br/edital/visualizar/651/
  - `edital` EDITAL Nº 32/2026-PROEN/IFRN Cursos Proeja Fic na Forma Integrada ao Ensino Médio - https://processoseletivo.ifrn.edu.br/edital/visualizar/648/
  - `edital` EDITAL Nº 30/2026-PROEN/IFRN - Rede de Certificadores - IFRN (exclusivo servidores efetivos do IFRN) - https://processoseletivo.ifrn.edu.br/edital/visualizar/646/

### UEMA - Editais UEMA

- Instituicao: Universidade Estadual do Maranhao (UEMA)
- Fonte: Editais UEMA
- URL: https://www.uema.br/category/editais
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.uema.br/category/editais/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (69839 bytes, 154 links)
- Itens encontrados: 13
- Novos itens salvos: 13
- Editais validos: 13
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` PAES - https://sigconcursos.uema.br/
  - `resultado` EDITAL N.º 222/2026-SUCONS/UEMA RESULTADO DO EDITAL N.º... - https://www.uema.br/2026/06/edital-n-o-222-2026-sucons-uema-resultado-do-edital-n-o-177-2026-sucons-uema-de-processo-seletivo-simplificado-destinado-a-contratacao-de-professor-substituto-da-uema/
  - `processo_seletivo` RELAÇÃO PRELIMINAR DE CANDIDATOS ISENTOS POR CADÚNICO OU... - https://www.uema.br/2026/06/relacao-preliminar-de-candidatos-isentos-por-cadunico-ou-por-serem-servidores-da-uema-ou-seusdependentes-no-processo-seletivo-simplificado-ead-uema-2026-2-edital-n-o-214-2026-gr-uema/

### UEMA - SIGConcursos UEMA

- Instituicao: Universidade Estadual do Maranhao (UEMA)
- Fonte: SIGConcursos UEMA
- URL: https://sigconcursos.uema.br/
- Tipo configurado: `TABLE_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://sigconcursos.uema.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (48622 bytes, 3 links)
- Itens encontrados: 2
- Novos itens salvos: 2
- Editais validos: 2
- Links de amostra que abriram: 2/2
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Concursos e Seletivos ENTRAR - https://sigconcursos.uema.br/HOME
  - `concurso` ENTRAR - https://sigconcursos.uema.br/login

### UEPB - Editais UEPB

- Instituicao: Universidade Estadual da Paraiba (UEPB)
- Fonte: Editais UEPB
- URL: https://uepb.edu.br/editais/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://uepb.edu.br/editais/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (133399 bytes, 255 links)
- Itens encontrados: 122
- Novos itens salvos: 122
- Editais validos: 122
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `convocacao` Nova convocação: divulgada 7ª Chamada da Lista Geral de Espera do Sistema de Seleção Unificada 2026 - https://uepb.edu.br/nova-convocacao-divulgada-7a-chamada-da-lista-geral-de-espera-do-sistema-de-selecao-unificada-2026/
  - `processo_seletivo` Pró-reitoria de Graduação divulga Chamada Regular do Processo Seletivo do Sistema de Seleção Unificada+ 2026 - https://uepb.edu.br/pro-reitoria-de-graduacao-divulga-chamada-regular-do-processo-seletivo-do-sistema-de-selecao-unificada-2026-2/
  - `processo_seletivo` Universidade Estadual da Paraíba faz seleção de preceptores, orientadores, tutores e estudantes para Programa Pet Saúde: Clima - https://uepb.edu.br/universidade-estadual-da-paraiba-faz-selecao-de-preceptores-orientadores-tutores-e-estudantes-para-programa-pet-saude-clima/

### UEPB - Professor substituto UEPB

- Instituicao: Universidade Estadual da Paraiba (UEPB)
- Fonte: Professor substituto UEPB
- URL: https://uepb.edu.br/editais/selecao-professor-substituto/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://uepb.edu.br/editais/selecao-professor-substituto/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (162405 bytes, 299 links)
- Itens encontrados: 156
- Novos itens salvos: 33
- Editais validos: 156
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `convocacao` Nova convocação: divulgada 7ª Chamada da Lista Geral de Espera do Sistema de Seleção Unificada 2026 - https://uepb.edu.br/nova-convocacao-divulgada-7a-chamada-da-lista-geral-de-espera-do-sistema-de-selecao-unificada-2026/
  - `processo_seletivo` Pró-reitoria de Graduação divulga Chamada Regular do Processo Seletivo do Sistema de Seleção Unificada+ 2026 - https://uepb.edu.br/pro-reitoria-de-graduacao-divulga-chamada-regular-do-processo-seletivo-do-sistema-de-selecao-unificada-2026-2/
  - `processo_seletivo` Universidade Estadual da Paraíba faz seleção de preceptores, orientadores, tutores e estudantes para Programa Pet Saúde: Clima - https://uepb.edu.br/universidade-estadual-da-paraiba-faz-selecao-de-preceptores-orientadores-tutores-e-estudantes-para-programa-pet-saude-clima/

### UESPI - Editais UESPI

- Instituicao: Universidade Estadual do Piaui (UESPI)
- Fonte: Editais UESPI
- URL: https://uespi.br/editais/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://uespi.br/editais/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (221741 bytes, 249 links)
- Itens encontrados: 127
- Novos itens salvos: 127
- Editais validos: 127
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `processo_seletivo` Editais UESPI PET SAÚDE CLIMA: Seleção para orientadores bolsistas, tutores, estudantes e voluntários - https://uespi.br/editais-uespi-pet-saude-clima-selecao-para-orientadores-bolsistas-tutores-estudantes-e-voluntarios/
  - `convocacao` Edital PREX/DAEC/SEE Nº 06/2026: Convocação para Estágio Não Obrigatório no NUFPERPI em Teresina-PI - https://uespi.br/edital-prex-daec-see-no-06-2026-convocacao-para-estagio-nao-obrigatorio-no-nufperpi-em-teresina-pi/
  - `resultado` Edital PREX/DAEC/SEE Nº63/2025: Resultado preeliminar de estágio para lotação na DTIC em Teresina - https://uespi.br/edital-prex-daec-see-no63-2025-resultado-preeliminar-para-estagio-para-lotacao-na-dtic-em-teresina/

### UFBA - Portal de concursos UFBA

- Instituicao: Universidade Federal da Bahia (UFBA)
- Fonte: Portal de concursos UFBA
- URL: https://concursos.ufba.br/
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://concursos.ufba.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (32290 bytes, 29 links)
- Itens encontrados: 6
- Novos itens salvos: 6
- Editais validos: 6
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Portal de Concursos da UFBA - https://concursos.ufba.br/
  - `edital` Visitantes - https://prppg.ufba.br/editais-e-chamadas
  - `concurso` Editais Anteriores - https://concursos.ufba.br/concursos-anteriores-docentes

### UFC - Editais e concursos UFC

- Instituicao: Universidade Federal do Ceara (UFC)
- Fonte: Editais e concursos UFC
- URL: https://www.ufc.br/editais-e-concursos/graduacao
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional_parcial`
- Pagina abre: True (HTTP 200, final `https://www.ufc.br/editais-e-concursos/graduacao`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (20838 bytes, 66 links)
- Itens encontrados: 9
- Novos itens salvos: 9
- Editais validos: 9
- Links de amostra que abriram: 2/3
- Problemas: -
- Acao tomada: Mantida parcialmente; requer revisao fina de fonte/spider.
- Observacao:
  - `concurso` Editais e Concursos - https://www.ufc.br/editais-e-concursos/graduacao
  - `concurso` Graduação - https://www.ufc.br/editais-e-concursos/graduacao?tmpl=component&print=1
  - `resultado` → Editais divulgados pela Pró-Reitoria de Graduação - http://www.prograd.ufc.br/editais-e-resultados

### UFC - Noticias e editais de concursos e selecoes UFC

- Instituicao: Universidade Federal do Ceara (UFC)
- Fonte: Noticias e editais de concursos e selecoes UFC
- URL: https://www.ufc.br/noticias/noticias-e-editais-de-concursos-e-selecoes
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.ufc.br/noticias/noticias-e-editais-de-concursos-e-selecoes`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (35597 bytes, 108 links)
- Itens encontrados: 52
- Novos itens salvos: 50
- Editais validos: 52
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `resultado` Programa Mais Ciência na Escola UFC divulga resultado de seleção de professores e abre segunda chamada de edital - https://www.ufc.br/noticias/noticias-e-editais-de-concursos-e-selecoes/20344-programa-mais-ciencia-na-escola-ufc-divulga-resultado-de-selecao-de-professores-e-abre-segunda-chamada-de-edital
  - `concurso` UFC e Fundação Cetrede divulgam edital de processo seletivo para Centros de Acesso a Direitos e Inclusão Social em Fortaleza - https://www.ufc.br/noticias/noticias-e-editais-de-concursos-e-selecoes/20340-ufc-e-fundacao-cetrede-divulgam-edital-de-processo-seletivo-para-centros-de-acesso-a-direitos-e-inclusao-social-em-fortaleza
  - `concurso` Lançado edital para turma de 2026.2 no Mestrado e Doutorado em Engenharia de Teleinformática - https://www.ufc.br/noticias/noticias-e-editais-de-concursos-e-selecoes/20332-lancado-edital-para-turma-de-2026-2-no-mestrado-e-doutorado-em-engenharia-de-teleinformatica

### UFMA - Editais UFMA

- Instituicao: Universidade Federal do Maranhao (UFMA)
- Fonte: Editais UFMA
- URL: https://portalpadrao.ufma.br/site/editais
- Tipo configurado: `GOVBR`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://portalpadrao.ufma.br/site/editais`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (49410 bytes, 128 links)
- Itens encontrados: 2
- Novos itens salvos: 2
- Editais validos: 2
- Links de amostra que abriram: 2/2
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Docentes - https://portais.ufma.br/PortalProReitoria/progep/concursos_docentes/
  - `concurso` Técnico-administrativos, Colégio Universitário, Alunos EAD, Residência Médica, etc - http://www.concursos.ufma.br/

### UFPE - Oportunidades UFPE

- Instituicao: Universidade Federal de Pernambuco (UFPE)
- Fonte: Oportunidades UFPE
- URL: https://www.ufpe.br/oportunidades
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `url_invalida`
- Pagina abre: False (HTTP 404, final `https://www.ufpe.br/oportunidades`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: False (146 bytes, 0 links)
- Itens encontrados: 0
- Novos itens salvos: 0
- Editais validos: 0
- Links de amostra que abriram: 0/0
- Problemas: 404 Client Error: Not Found for url: https://www.ufpe.br/oportunidades
- Acao tomada: Requer substituicao por URL oficial funcional.
- Observacao:
  - Sem amostra valida capturada.

### UFPE - Site oficial UFPE - descoberta

- Instituicao: Universidade Federal de Pernambuco (UFPE)
- Fonte: Site oficial UFPE - descoberta
- URL: https://www.ufpe.br/
- Tipo configurado: `HTML_STATIC`
- Spider usado: `GenericNoticeSpider`
- Status: `exige_javascript`
- Pagina abre: True (HTTP 200, final `https://www.ufpe.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: False (1296 bytes, 0 links)
- Itens encontrados: 0
- Novos itens salvos: 0
- Editais validos: 0
- Links de amostra que abriram: 0/0
- Problemas: -
- Acao tomada: Requer alternativa oficial sem JavaScript ou spider com renderizacao.
- Observacao:
  - Sem amostra valida capturada.

### UFPI - Concursos UFPI

- Instituicao: Universidade Federal do Piaui (UFPI)
- Fonte: Concursos UFPI
- URL: http://www.ufpi.br/concursos
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://ufpi.br/concursos`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (53820 bytes, 100 links)
- Itens encontrados: 14
- Novos itens salvos: 14
- Editais validos: 14
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Página Inicial - Concursos - http://www.ufpi.br/concursos
  - `concurso` Outros - http://www.ufpi.br/concursos-outros
  - `processo_seletivo` CPCE-Bom Jesus: Seleção Professor Substituto, Ed. 09/2026-CPCE- Clínica de Animais Selvagens, Manejo de Fauna, Epidemiologia e áreas afins - http://www.ufpi.br/ultimas-noticias-professor-substituto/67661-cpce-bom-jesus-selecao-professor-substituto-ed-09-2026-cpce-clinica-de-animais-selvagens-manejo-de-fauna-epidemiologia-e-areas-afins

### UFPI - Editais UFPI

- Instituicao: Universidade Federal do Piaui (UFPI)
- Fonte: Editais UFPI
- URL: https://ufpi.br/editais
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://ufpi.br/editais`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (32548 bytes, 109 links)
- Itens encontrados: 1
- Novos itens salvos: 1
- Editais validos: 1
- Links de amostra que abriram: 1/1
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `edital` Editais de Assuntos Estudantis e Comunitários (PRAEC) - http://ufpi.br/edital-praec

### UFRN - Concursos UFRN

- Instituicao: Universidade Federal do Rio Grande do Norte (UFRN)
- Fonte: Concursos UFRN
- URL: https://www.ufrn.br/institucional/concursos
- Tipo configurado: `HTML_STATIC`
- Spider usado: `GenericNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://www.ufrn.br/institucional/concursos`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (25770 bytes, 112 links)
- Itens encontrados: 4
- Novos itens salvos: 4
- Editais validos: 4
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `concurso` Docentes - https://progesp.ufrn.br/secao/concursos
  - `concurso` Técnicos Administrativos - http://www.comperve.ufrn.br/conteudo/concursos/concursos.php
  - `processo_seletivo` Seleções de Pós-Graduação - https://sigaa.ufrn.br/sigaa/public/processo_seletivo/lista.jsf?aba=p-processo&nivel=S

### UFRN - Processos seletivos SIGAA UFRN

- Instituicao: Universidade Federal do Rio Grande do Norte (UFRN)
- Fonte: Processos seletivos SIGAA UFRN
- URL: https://sigaa.ufrn.br/sigaa/public/processo_seletivo/lista.jsf?aba=p-processo&nivel=S
- Tipo configurado: `TABLE_HTML`
- Spider usado: `PaginatedNoticeSpider`
- Status: `exige_spider_especifico`
- Pagina abre: True (HTTP 200, final `https://sigaa.ufrn.br/sigaa/public/servicos_digitais/processo_seletivo/area_do_candidato/login.jsf?servico=inscricao-processo-seletivo-stricto-sensu&redirect=/public/servicos_digitais/processo_seletivo/lista.jsf?nivel=S`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (6135 bytes, 3 links)
- Itens encontrados: 0
- Novos itens salvos: 0
- Editais validos: 0
- Links de amostra que abriram: 0/0
- Problemas: -
- Acao tomada: Requer spider especifico ou seletor dedicado.
- Observacao:
  - Sem amostra valida capturada.

### UNEB - Editais UNEB

- Instituicao: Universidade do Estado da Bahia (UNEB)
- Fonte: Editais UNEB
- URL: https://portal.uneb.br/category/editais/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional_parcial`
- Pagina abre: False (HTTP 404, final `https://portal.uneb.br/category/editais/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: False (293866 bytes, 177 links)
- Itens encontrados: 76
- Novos itens salvos: 76
- Editais validos: 76
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida parcialmente; requer revisao fina de fonte/spider.
- Observacao:
  - `resultado` SiSU+ 2026: UNEB divulga resultado e orienta candidatos sobre próximas etapas para ingresso - https://portal.uneb.br/2026/06/27/sisu-2026-uneb-divulga-resultado-e-orienta-candidatos-sobre-proximas-etapas-para-ingresso/
  - `bolsa` UNEB vai abrir inscrições para cursos de idiomas e seleção para bolsas de estudo: 22/06 (Salvador) - https://portal.uneb.br/2026/06/16/uneb-vai-abrir-inscricoes-para-cursos-de-idiomas-e-selecao-para-bolsas-de-estudo-22-06-salvador/
  - `processo_seletivo` UNEB abre seleção (aluno regular) do Mestrado em Letras (Teixeira de Freitas) - https://portal.uneb.br/2026/06/16/uneb-abre-selecao-aluno-regular-do-mestrado-em-letras/

### UNEB - Portal UNEB - descoberta

- Instituicao: Universidade do Estado da Bahia (UNEB)
- Fonte: Portal UNEB - descoberta
- URL: https://portal.uneb.br/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://portal.uneb.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (599582 bytes, 424 links)
- Itens encontrados: 78
- Novos itens salvos: 2
- Editais validos: 78
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `resultado` SiSU+ 2026: UNEB divulga resultado e orienta candidatos sobre próximas etapas para ingresso - https://portal.uneb.br/2026/06/27/sisu-2026-uneb-divulga-resultado-e-orienta-candidatos-sobre-proximas-etapas-para-ingresso/
  - `bolsa` UNEB vai abrir inscrições para cursos de idiomas e seleção para bolsas de estudo: 22/06 (Salvador) - https://portal.uneb.br/2026/06/16/uneb-vai-abrir-inscricoes-para-cursos-de-idiomas-e-selecao-para-bolsas-de-estudo-22-06-salvador/
  - `processo_seletivo` UNEB abre seleção (aluno regular) do Mestrado em Letras (Teixeira de Freitas) - https://portal.uneb.br/2026/06/16/uneb-abre-selecao-aluno-regular-do-mestrado-em-letras/

### UPE - Concursos UPE

- Instituicao: Universidade de Pernambuco (UPE)
- Fonte: Concursos UPE
- URL: https://upe.br/editais/concursos/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional_parcial`
- Pagina abre: True (HTTP 200, final `https://upe.br/editais/concursos/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (275886 bytes, 239 links)
- Itens encontrados: 57
- Novos itens salvos: 57
- Editais validos: 29
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida parcialmente; requer revisao fina de fonte/spider.
- Observacao:
  - `resultado` Escola de Aplicação do Recife (EAR/UPE) lidera ranking nacional do ENEM entre as instituições públicas de Pernambuco - https://upe.br/ear-upe-enem/
  - `resultado` UPE é credenciada para integrar o Laboratório InovaSUS Digital do Ministério da Saúde - https://upe.br/upe-inovasus/
  - `resultado` CNPq lança Chamada Universal 2026 com R$ 300 milhões para financiamento de pesquisas - https://upe.br/cnpq-financiamento/

### UPE - Editais UPE

- Instituicao: Universidade de Pernambuco (UPE)
- Fonte: Editais UPE
- URL: https://upe.br/editais/
- Tipo configurado: `WORDPRESS`
- Spider usado: `WordPressNoticeSpider`
- Status: `funcional_parcial`
- Pagina abre: True (HTTP 200, final `https://upe.br/editais/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (281786 bytes, 246 links)
- Itens encontrados: 58
- Novos itens salvos: 2
- Editais validos: 30
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida parcialmente; requer revisao fina de fonte/spider.
- Observacao:
  - `resultado` Escola de Aplicação do Recife (EAR/UPE) lidera ranking nacional do ENEM entre as instituições públicas de Pernambuco - https://upe.br/ear-upe-enem/
  - `resultado` UPE é credenciada para integrar o Laboratório InovaSUS Digital do Ministério da Saúde - https://upe.br/upe-inovasus/
  - `resultado` CNPq lança Chamada Universal 2026 com R$ 300 milhões para financiamento de pesquisas - https://upe.br/cnpq-financiamento/

### UPE - Processo de ingresso UPE

- Instituicao: Universidade de Pernambuco (UPE)
- Fonte: Processo de ingresso UPE
- URL: https://processodeingresso.upe.pe.gov.br/
- Tipo configurado: `PAGINATED_HTML`
- Spider usado: `GovBrNoticeSpider`
- Status: `funcional`
- Pagina abre: True (HTTP 200, final `https://processodeingresso.upe.pe.gov.br/`)
- Fallback curl por TLS/OpenSSL: False
- HTML util: True (122593 bytes, 267 links)
- Itens encontrados: 54
- Novos itens salvos: 54
- Editais validos: 54
- Links de amostra que abriram: 3/3
- Problemas: -
- Acao tomada: Mantida; crawler recuperou editais validos.
- Observacao:
  - `processo_seletivo` Diretoria de Processos Seletivos Acadêmicos Processo de Ingresso 2026 Clique aqui e Acompanhe - https://processodeingresso.upe.pe.gov.br/arquivos/aplicacao_2027/202606111653_-_COMUNICADO_ACERCA_DA_ALTERACAO_DA_DATA_DA_PROVA_-_ESCOLAS_DE_APLICACAO_DA_UPE_2027.pdf
  - `processo_seletivo` Aviso do Edital - https://processodeingresso.upe.pe.gov.br/arquivos/aplicacao_2027/202605081743_-_AVISO_DO_EDITAL_-_DOE.pdf
  - `processo_seletivo` RESOLUÇÃO CONSUN Nº 014/2026 - Regulamenta a reserva de vagas para estudantes com deficiência no Processo Seletivo para as Escolas de Aplicação da Universidade de Pernambuco - UPE - https://sispub.upe.br/download/e6a6fda25c0d02db41701f1faadff895.pdf

## Limitacoes e proximos passos

- Fontes com `exige_spider_especifico` devem ser analisadas no HTML para seletor dedicado ou fonte oficial alternativa.
- Fontes com `url_invalida` ou `bloqueio_acesso` precisam de confirmacao manual antes de troca no catalogo.
- A validacao de links abre somente amostras por fonte para evitar baixar grandes PDFs em massa.
- Algumas fontes exigiram fallback via `curl` por falha de cadeia TLS no OpenSSL/requests; `curl` foi usado com verificacao TLS padrao, sem `--insecure`.
- Para expandir a auditoria, rode o script com `--all`.

## Reproducao

```bash
cd backend
python scripts/audit_northeast_sources.py
python scripts/audit_northeast_sources.py --all
```
