# Dados e critérios da triagem

O piloto busca resultados de compras que merecem leitura do processo original. A fila combina três sinais verificáveis e preserva uma ligação com a consulta oficial de cada compra. As 12 apresentações configuradas cobrem oito códigos CATMAT de cinco famílias. A lista pode crescer sem alterar o método.

## Fonte, recorte e unidade de análise

O módulo Pesquisa de Preços do Compras.gov.br publica valores homologados de compras registradas no sistema. Foram consultadas as páginas do endpoint `modulo-pesquisa-preco/1_consultarMaterial` com `tipo=codigoItemCatalogo`, o código do material e `tamanhoPagina=500`. Em 9 de novembro de 2026, por volta das 03h12 de Brasília, o extrator recebeu 10.420 observações em 26 páginas. O manifesto especifica a URL e o SHA-256 da resposta original de cada página. A projeção congelada retém as 4.777 observações com data de resultado em 2024 ou 2025. [Documentação da API](https://dadosabertos.compras.gov.br/swagger-ui/index.html) · [Pesquisa de Preços](https://www.gov.br/compras/pt-br/sistemas/conheca-o-compras/pesquisa-de-precos)

O portal oficial prevê reutilização e redistribuição dos dados abertos. Os arquivos distribuídos contêm os campos utilizados na análise, uma chave derivada para o fornecedor e um trecho do objeto da compra. O nome e a inscrição do fornecedor ficam fora da projeção. O processamento mascara e-mails, números com formato de CPF/CNPJ e telefones reconhecidos. As respostas originais são processadas em memória em uma nova coleta. Os hashes também permitem conferir a versão recebida na origem. [Portal de Dados Abertos](https://www.gov.br/compras/pt-br/cidadao/portal-de-dados-abertos) · [Decreto nº 9.903/2019](https://planalto.gov.br/ccivil_03/_ato2019-2022/2019/decreto/d9903.htm)

Cada linha identifica um resultado para a combinação de código CATMAT, item de compra e fornecedor homologado. Uma compra pode conter vários itens. A seleção dos materiais foi intencional, por diversidade de famílias, especificação verificável e disponibilidade nos dois anos. O alcance se limita aos códigos e às compras registrados no sistema. Os preços são nominais, em reais por unidade de fornecimento cadastrada. As três esferas estão representadas. A UF identifica a unidade compradora.

| Família | CATMAT | Material e apresentações configuradas |
| --- | --- | --- |
| Expediente | 461889 | Papel A4 branco de 75 g/m². Embalagens de 100 ou 500 folhas, tratadas separadamente. |
| Expediente | 462546 | Caneta esferográfica azul. Unidade, caixa de 12 ou caixa de 50. |
| Saúde | 267778 | Paracetamol 500 mg. Comprimido. |
| Saúde | 267203 | Dipirona sódica 500 mg. Comprimido. |
| Tecnologia | 451819 | Teclado multimídia USB com fio. Unidade. |
| Tecnologia | 462261 | Mouse USB com fio. Unidade. O CATMAT descreve sensor com esfera. |
| Copa | 232589 | Garrafa térmica plástica de 1 litro. Unidade. |
| Limpeza | 299605 | Água sanitária com 2 a 2,5% de cloro ativo. Frasco de 1 litro e garrafa de 5 litros, separadamente. |

## Seleção e cobertura

Cada apresentação habilitada é uma combinação exata das siglas de fornecimento e de medida e da capacidade declarada. Para `UN` e `COMPR`, o padrão da fonte contém capacidade zero e sigla de medida nula. A lista aceita esse padrão somente quando a própria unidade de fornecimento identifica a peça ou o comprimido. Os registros com embalagem incompleta, divergente ou externa à configuração seguem para as pendências. Por exemplo, um frasco registrado no código de comprimido não recebe a referência do comprimido.

O processamento verifica a chave do resultado e exige preço e quantidade positivos. Nas 4.777 linhas dos dois anos houve zero chaves incompletas ou repetidas e zero registros de preço ou quantidade não positivos. O código prevê um status específico se uma atualização trouxer esses problemas. A versão distribuída também conserva os preços extremos do cadastro.

| Indicador | 2024 | 2025 |
| --- | ---: | ---: |
| Resultados dos oito códigos | 2.351 | 2.426 |
| Apresentação habilitada e valores válidos | 2.062 | 2.151 |
| Resultados nas apresentações com suporte histórico mínimo | 2.057 | 2.146 |
| Apresentação fora da configuração | 289 | 275 |
| Resultados sem suporte histórico suficiente | 5 | 5 |

A caixa de 12 canetas tinha apenas cinco observações em 2024. Ficou separada das 11 apresentações com pelo menos 20 observações de treino. O universo de 2025 inclui 1.867 compras, 1.270 unidades compradoras, 1.060 chaves distintas de fornecedor e 27 UFs. Os resultados distribuem-se pelas esferas federal (960), municipal (789) e estadual (677).

## Regras e ordem de revisão

| Regra | Teste operacional | Evidência gravada |
| --- | --- | --- |
| R1 · Preço superior ao histórico | Dentro do CATMAT e da apresentação, comparar o preço observado com Q3 + 1,5 × (Q3 − Q1) dos preços de 2024. A regra exige que o preço ultrapasse estritamente essa cerca e que existam pelo menos 20 observações do ano anterior. | Preço observado, cerca histórica, apresentação e tamanho do histórico. |
| R2 · Possível precificação por lote | Exigir quantidade exatamente igual a 1 e ocorrência de expressão textual selecionada no objeto oficial, como “lote único”, “grupo único”, “em lotes”, “por lote” ou “dois lotes”. A expressão regular aplicada é visível no script. | Expressão encontrada e trecho do objeto. O edital permite averiguar a composição. |
| R3 · Recorrência em 30 dias | Encontrar outro ID de compra com a mesma unidade compradora, CATMAT e fornecedor homologado. A data de resultado anterior deve estar de 1 até 30 dias antes. Para empates na mesma data anterior, o processamento seleciona uma das compras testemunhas de forma determinística. | Data e identificador da compra anterior. |

R3 percorre os resultados em ordem cronológica. Processa o dia completo antes de incorporá-lo ao histórico. Observações do próprio dia e itens da mesma compra não acionam o sinal. A janela inclui o fim de 2024 para as observações de janeiro de 2025. Apresentações diversas do mesmo material podem sustentar R3, cujo foco é o contexto da aquisição. R2 e R3 também ficam registrados nas pendências, sem promover um item de apresentação incerta à fila comparável.

**Alta** reúne duas ou mais regras, **Média** corresponde a R1 isolada e **Contextual** a R2 ou R3 isoladas. Dentro da prioridade, a ordem usa mais sinais e depois a maior diferença total positiva frente à referência de volume. Em empate usa presença de R1, data, CATMAT, identificador do item e chave do fornecedor. A diferença exibida mantém seu sinal. A ordenação considera zero quando a diferença é negativa.

O preço usado para estimar a diferença é a mediana histórica da apresentação e da faixa de volume. Ele é uma estimativa diferente da cerca estatística que aciona R1. No cálculo, diferença unitária = observado − referência. Diferença percentual = 100 × diferença unitária ÷ referência. Diferença total = quantidade × diferença unitária. Frete, condições de entrega, especificação no edital, inflação e alocação de preço a lotes podem explicar diferenças. O exame documental pode confirmar que a contratação é compatível.

## Modelo, teste e capacidade operacional

O treino usa resultados de 2024, do mesmo CATMAT e da mesma apresentação. Para cada uma das 11 apresentações com suporte suficiente, o algoritmo calcula os quantis de 1/3 e 2/3 da quantidade usando interpolação linear na posição (n − 1) × p. Os limites integram a faixa inferior. A previsão é a mediana de preços na faixa. Se houver menos de dez registros nessa faixa, aplica-se a mediana global da própria apresentação. O baseline usa apenas essa última mediana. Os preços do teste e os sinais da fila ficam fora do ajuste.

O modelo congelado em 2024 foi testado em 2.146 resultados de 2025, incluindo os extremos. Todos os casos comparáveis puderam ser avaliados. Nenhuma compra do treino habilitado reapareceu no teste comparável. Das estimativas, 44 usaram a mediana geral da apresentação por falta de suporte na faixa. A avaliação é retrospectiva com a versão da fonte obtida em 2026, que pode conter revisões posteriores à data do resultado.

| Métrica de 2025 | Mediana por CATMAT e apresentação | Modelo com volume |
| --- | ---: | ---: |
| Erro absoluto médio por unidade declarada | R$ 94,54 | R$ 94,41 |
| Mediana do erro absoluto | R$ 0,6025 | R$ 0,50 |
| Mediana do erro percentual absoluto | 18,38% | 17,93% |

O ganho de 0,14% em MAE é pequeno. Para mouse USB, o MAE cresceu de R$ 118,97 para R$ 119,14. Para garrafa térmica, o MAE cresceu de R$ 4,40 para R$ 4,46. Como as unidades e os níveis de preço variam entre produtos, a análise por material e os erros percentuais complementam o MAE agregado. Um resultado de paracetamol com preço de R$ 134.275,00 para quantidade 1 representou 66,28% da soma dos erros absolutos do modelo. A classificação depende da leitura do processo.

A fila de 2025 contém 274 resultados em 235 compras, com sete altas, 246 médias e 21 contextuais. Há 253 ocorrências de R1, quatro de R2 e 24 de R3 na fila. Dois ou mais sinais podem apontar o mesmo resultado. Três outras observações com R3 permaneceram nas pendências de apresentação. Uma equipe que consiga revisar **20 resultados** cobriria 19 compras, quatro códigos e as sete prioridades altas. Essa simulação mede capacidade de revisão. O conjunto não contém rótulos de irregularidade para estimar precisão, revocação ou economia.

Para o cenário de 1º de janeiro de 2026, o mesmo procedimento é recalibrado sobre 2025. Em um pedido de 30 teclados (451819), a referência é R$ 25,52 por unidade e R$ 765,60 para a quantidade informada. Trata-se de uma simulação retrospectiva. Os dados de resultados de 2026 ficam fora do cálculo.

## Caso para revisão

Na posição 5, um órgão de SP registrou resultado em 13 de janeiro de 2025 para 1.600 frascos de água sanitária de 1 L. O preço unitário de R$ 3,80 ficou acima da cerca histórica de R$ 3,49. A referência de preço por volume foi R$ 1,89. A diferença calculada é R$ 1,91 por frasco e R$ 3.056,00 no total. A mesma UASG registrou resultado para o mesmo CATMAT e fornecedor em outra compra em 10 de janeiro. Para revisar, consultar o item `9264950590130202400019`, conferir embalagem e condições de entrega e comparar os processos envolvidos. [Consulta oficial da compra](https://dadosabertos.compras.gov.br/modulo-pesquisa-preco/1_consultarMaterial?tipo=codigoItemCatalogo&codigo=299605&idCompra=92649505901302024)

## Dicionário e arquivos

| Arquivo | Conteúdo |
| --- | --- |
| `config/materiais.json` | Códigos e apresentações parametrizados e limites de suporte e da janela de recorrência. |
| `dados/fonte/manifesto.json` e `*.json.gz` | Uma entrada para cada página da API, com contagens, URL e hashes. Cada arquivo distribuído contém apenas a projeção de 2024 e 2025. |
| `dados/treino_2024.csv` | Universo de 2024 com status inicial. Para replicar os modelos, selecionar status “Elegível” e exigir o suporte configurado dentro da apresentação. |
| `dados/triagem_2025.csv` | Universo de 2025 com status, referência, sinais e prioridade. |
| `dados/fila_2025.csv` e `dados/pendencias_2025.csv` | Fila ordenada de revisão e tabela de problemas de apresentação/suporte. |
| `dados/resultados.json` | Indicadores, métricas agregadas e por material, parâmetros das safras de 2024 e 2025 e cenário simulado. |
| `dados/hashes.json` | Somas SHA-256 dos quatro CSVs e do JSON de resultados. |

Os CSVs usam UTF-8 com BOM, separador de ponto e vírgula, vírgula decimal e datas ISO. Ao importar, mantenha **identificadores como texto**, inclusive `codigo_uasg`, `id_compra_item` e `id_compra`. Planilhas podem perder dígitos ao tratar esses códigos como números.

| Campos | Interpretação |
| --- | --- |
| `id_compra_item`, `fornecedor`, `id_compra`, `catmat` | Identificadores do item, fornecedor pseudonimizado, compra e material de catálogo. |
| `data_resultado`, `uf`, `esfera`, `codigo_uasg`, `uasg`, `orgao` | Referência temporal e localização administrativa da unidade compradora. |
| `material`, `familia`, `apresentacao`, `quantidade`, `preco_unitario` | Rótulos do catálogo e do estudo, apresentação declarada, unidades dessa apresentação e R$ por unidade. Apresentações fora da configuração exibem a tripla original. |
| `objeto_compra`, `expressao_lote`, `url_fonte` | Trecho do objeto, expressão que pode sustentar R2 e endereço da API filtrado por CATMAT e ID da compra. Havendo mais de um item, conferir o identificador do item. |
| `status`, `n_historico`, `faixa_volume`, `fallback_volume` | Condição de comparabilidade, número de observações da coorte em 2024, faixa de quantidade e uso da mediana geral por suporte insuficiente na faixa. |
| `referencia`, `baseline`, `limite_superior` | Estimativa com volume, mediana de toda a apresentação e cerca superior para R1, em R$ por unidade. |
| `desvio_unitario`, `desvio_pct`, `diferenca_total` | Diferença assinada de preço em reais, relativa à referência em porcentagem e multiplicada pela quantidade. |
| `erro_modelo`, `erro_baseline`, `valida_teste` | Distâncias absolutas em reais por unidade e indicador de elegibilidade para as métricas. |
| `r1_preco`, `r2_lote`, `r3_recorrencia`, `data_anterior`, `compra_anterior` | Indicadores binários dos sinais e evidência temporal de recorrência. |
| `motivos`, `prioridade`, `posicao` | Combinação de regras, prioridade operacional e ordem na fila de 2025. A posição fica vazia fora da fila. |

## Reproduzir, verificar e ampliar

Com Python 3.10 ou superior, execute a partir desta pasta. O extrator e o verificador usam a biblioteca padrão.

```powershell
python src/triagem.py
python src/verificar_dados.py
```

A reprodução offline recalcula a análise, checa os arquivos congelados e produz os mesmos cinco hashes. A auditoria independente também verifica a exclusividade da chave, os sinais, as janelas temporais, os cálculos de diferença e os erros do teste. Uma segunda coleta real reproduziu os quatro CSVs do piloto em 9 de novembro de 2026.

Para consultar a fonte novamente, use uma pasta vazia. A cópia original do projeto permanece como referência para a análise de 2024–2025.

```powershell
python src/triagem.py --online --saida ../triagem_atualizada
```

Para ampliar a cobertura material, duplique `config/materiais.json`, acrescente o CATMAT confirmado e as apresentações aceitas. Cada apresentação tem quatro valores em ordem, sigla de fornecimento, capacidade, sigla de medida e rótulo legível. Faça a coleta com o novo arquivo e verifique o tamanho do histórico e as pendências. Os períodos 2024/2025 e o cenário de 2026 estão explícitos no script. Uma mudança de período requer atualizar os cortes temporais e repetir a avaliação.

```powershell
python src/triagem.py --online --config config/materiais_ampliados.json --saida ../triagem_ampliada
```
