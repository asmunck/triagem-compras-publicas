# Revisão documental da fila de compras

**Pergunta de avaliação.** Ao examinar um resultado de compra, um revisor consegue apontar um fato documental que justifique uma providência adicional? Uma providência pode ser obter a proposta discriminada, confirmar uma apresentação comercial ou reconciliar datas entre sistemas. O desfecho mede a utilidade da triagem para essa tarefa. A apuração de irregularidade exige outra investigação.

## O que já foi conferido

A [conferência documental de 9 de novembro de 2026](revisao_documental.csv) compara quatro resultados de compras com os respectivos editais e registros oficiais. A planilha indica a página ou o item que sustenta cada observação.

| Exemplo | O que os documentos esclarecem |
| --- | --- |
| Paracetamol, fila 215 | O campo estruturado informa comprimido. O termo especifica cinco caixas de 20. É preciso distinguir as unidades antes de interpretar o preço. |
| Água sanitária, fila 5 | Os resultados de 10 e 13 de janeiro de 2025 dizem respeito a entregas previstas em Campinas e Sorocaba, com volumes diferentes. O sinal de recorrência exige esse contexto. |
| Papel A4, fila 1 | O valor estimado registrado no item eletrônico corresponde ao lote de materiais. A planilha do termo especifica as 350 resmas e seu preço estimado individual. |
| Dipirona, controle sem sinal | Quantidade, apresentação e preço coincidem. A data do resultado difere entre a pesquisa de preços e o registro do item da contratação no PNCP, atravessando a virada de 2024 para 2025. |

Esses exemplos ilustram verificações executadas; as fichas de avaliação humana abaixo estão em branco. As quatro consultas direcionadas não estimam uma taxa de acerto. O teste da previsão de preços, já executado no notebook, tem outro alvo e outra métrica.

## Amostra pronta para avaliação humana

A unidade avaliada é o **resultado de item para um fornecedor**. Um mesmo processo pode ter mais de um resultado. Se forem divulgadas taxas, o denominador deve manter essa unidade.

| Estrato na base de 2025 | Universo | Fichas selecionadas |
| --- | ---: | ---: |
| Prioridade alta | 7 | 7 |
| Prioridade média | 246 | 7 |
| Prioridade contextual | 21 | 7 |
| Comparável sem sinal | 1.872 | 7 |
| **Total comparável** | **2.146** | **28** |

Cada estrato é ordenado pelo SHA-256 da semente fixa, do identificador de item e da chave pseudonimizada do fornecedor. Os sete primeiros compõem a amostra. Os 280 resultados pendentes ficam em uma lista de saneamento à parte: 275 por apresentação fora do recorte e cinco por histórico insuficiente. Eles não receberam a mesma avaliação de comparabilidade dos outros 2.146.

O coordenador guarda o [plano por estrato e a planilha de consenso](plano_amostral.csv). Cada revisor recebe sua própria cópia das [28 fichas sem prioridade visível](fichas_revisao.csv), em ordem misturada. Para uma leitura independente, cada um deve examinar as fontes antes de ver a fila, os exemplos resolvidos ou a resposta do outro. Ao importar os CSVs no Excel ou LibreOffice, escolha o delimitador ponto e vírgula e o tipo **Texto** para `id_compra_item`. O identificador tem 22 dígitos e sua conversão para número pode alterar os dígitos finais.

## Como preencher uma ficha

1. **Verifique a identidade.** Abra as fontes de preço e do item. Confira identificador, órgão, código de catálogo, unidade e quantidade. Quando houver vários resultados para o mesmo item, confira o fornecedor no processo e a chave pseudonimizada correspondente. O [dicionário dos dados](../README_DADOS.md) descreve a construção da chave.
2. **Leia o documento original.** Use o número de controle PNCP da contratação para acessar o [portal](https://pncp.gov.br/app/editais). No edital ou termo procure o número do item, o CATMAT e a unidade solicitada. Para estimativas versus preços homologados, distinga as duas colunas. Para lotes, identifique os subitens e procure a proposta discriminada. Para compras próximas, confronte as duas datas de resultado, os destinos, volumes e condições de entrega. Registre a URL e a página, tabela ou campo que sustenta a conclusão.
3. **Decida e justifique.** Preencha `revisor_codigo`, data, campos confirmados, fato observado, documento, desfecho, providência ou limite e os minutos gastos. Use um dos valores exatos abaixo.

| Desfecho | Critério operacional |
| --- | --- |
| **Encaminhar** | Há uma divergência ou questão específica sustentada por evidência e uma ação adicional identificável. Descreva qual informação faz falta e como ela ajudaria a decidir. Um preço alto, isoladamente, não basta. |
| **Encerrar** | A documentação examinada esclarece a questão ou sustenta a comparabilidade, e o revisor não identifica providência adicional para a pergunta avaliada. Cite o fundamento. |
| **Inconclusivo** | Um documento essencial está inacessível, o registro não pôde ser identificado sem ambiguidade ou as fontes não permitem uma decisão fundamentada. Identifique a lacuna. |

4. **Concilie as leituras.** Dois revisores preenchem suas cópias independentemente. O coordenador junta as respostas pela coluna `ficha`, registra os desacordos e preserva as versões originais. Havendo divergência, ambos confrontam as fontes, anotam o fundamento no plano e registram o consenso. Se não houver consenso documentado, o desfecho final será **Inconclusivo**. Fichas ainda não examinadas permanecem vazias e são contadas separadamente.

## Como interpretar a avaliação

Primeiro divulgue, por estrato, as quantidades de **Encaminhar**, **Encerrar**, **Inconclusivo** e **sem leitura**, junto com a concordância anterior à conciliação (decisões idênticas divididas pelas fichas com duas leituras). Com um só revisor é possível relatar uma leitura exploratória, identificando a ausência de avaliação independente.

Com as duas leituras de todas as fichas, a proporção de encaminhamentos entre casos conclusivos de um estrato é `encaminhar / (encaminhar + encerrar)`. Se esse denominador for zero, informe “sem estimativa”. Relate os inconclusivos separadamente. Para estimar a utilidade na fila completa, considere somente os três estratos sinalizados e dê a cada ficha peso `N/n` conforme a tabela. Some os pesos dos encaminhamentos e divida pela soma dos pesos dos casos conclusivos. Um quociente simples sobre as 21 fichas super-representaria a prioridade alta.

Mostre também limites de sensibilidade considerando os inconclusivos da fila: peso dos encaminhamentos dividido por 274 como limite inferior e peso dos encaminhamentos mais inconclusivos dividido por 274 como superior. São cenários de classificação dos inconclusivos, e não intervalos de confiança. Os sete controles sem sinal fornecem um comparador exploratório em separado. Com sete fichas por estrato, apresente as contagens junto às taxas e evite generalizar ganhos de precisão ou de tempo. O tempo de revisão e a taxa de encaminhamento útil podem orientar estudos maiores. A precisão na detecção de fraude e a economia financeira permanecem fora do que esse desenho mede.

## Reprodução

Os arquivos de seleção acompanham a base congelada em `dados/triagem_2025.csv`. Para reproduzi-los a partir da raiz do projeto, use `python src/gerar_amostra_revisao.py --saida amostra_temporaria` e compare com as fichas em `casos/`. O programa preserva planilhas já preenchidas e solicita outro diretório se encontrar arquivos com os mesmos nomes.
