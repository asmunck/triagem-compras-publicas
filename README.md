# Triagem de compras públicas

Quais compras merecem ser abertas primeiro por uma equipe de controle? O painel compara 2.426 resultados de 2025 com o histórico de 2024 para oito materiais do Compras.gov.br. Ao abrir uma ocorrência, é possível ver o preço declarado, a apresentação do material, o motivo da seleção e o processo de origem.

[Abrir painel](https://asmunck.github.io/triagem-compras-publicas/) · [Executar no Colab](https://colab.research.google.com/github/asmunck/triagem-compras-publicas/blob/main/analise_compras.ipynb) · [Consultar o código](https://github.com/asmunck/triagem-compras-publicas)

## Abrir o painel

Para consultar o painel offline, extraia o ZIP do projeto e abra `index.html` em um navegador. O arquivo também funciona sozinho, sem servidor ou conexão. As consultas à API oficial exigem internet.

1. Em **Fila de revisão**, combine família, material, UF, esfera e busca no objeto ou órgão. Abra uma linha para consultar a compra, a unidade, os sinais, o preço de referência e a origem. O CSV exporta toda a fila filtrada na ordenação escolhida.
2. Use **Abrir caso de paracetamol** para consultar o item 1603320600054202500043. A fonte informa a unidade “Comprimido” e descreve uma caixa com 20 comprimidos. A ficha distingue a comparação estatística da verificação documental.
3. Em **Cobertura**, veja quantos resultados têm referência e quantos dependem de identificação da apresentação ou de histórico adicional.
4. Em **Validação e previsão**, compare o modelo por faixa com a mediana de cada apresentação. Escolha um material e uma quantidade para simular um lote com todo o histórico de 2025. O cenário inicial usa 30 teclados USB.

Quando um item acumula sinais, ele sobe na fila. Na compra de água sanitária da posição 5, por exemplo, duas aquisições próximas envolviam destinos e quantidades diferentes. A ficha permite conferir ambas antes de interpretar a recorrência.

## Conferência dos alertas

Quatro exemplos documentam o que os autos esclarecem sobre preços, unidades e compras recorrentes. No caso do paracetamol, a página 6 do termo de referência especifica cinco caixas de 20 comprimidos. [Casos e evidências](casos/revisao_documental.csv) · [Termo de referência, item 43](https://pncp.gov.br/pncp-api/v1/orgaos/00394452000103/compras/2025/20613/arquivos/2#page=6)

Para avaliar se os sinais ajudam a selecionar processos, o protocolo define como examinar uma amostra de 28 resultados e documentar cada decisão. As fichas de julgamento humano estão em branco. O MAE apresentado no notebook mede o erro de previsão de preço. [Protocolo de revisão](casos/PROTOCOLO.md) · [Fichas da amostra](casos/fichas_revisao.csv)

## Executar no Google Colab

Abra o [notebook no Google Colab](https://colab.research.google.com/github/asmunck/triagem-compras-publicas/blob/main/analise_compras.ipynb) e selecione **Ambiente de execução → Executar tudo**. A primeira célula busca a [versão dos dados usada no relatório](https://github.com/asmunck/triagem-compras-publicas/tree/1fb584581cb6945bf9f6f398979ca74cc7237588) e o painel correspondente. Se o serviço estiver indisponível, a célula oferece a opção de carregar o ZIP do projeto.

As três vistas em Python, as tabelas e o cenário ficam salvos no notebook. Altere os campos da seção **Filtros** e reexecute as células seguintes para outro recorte. Na última célula, o painel HTML oferece filtros e fichas interativas.

## Reproduzir localmente

A partir da pasta do projeto, execute os comandos abaixo com Python 3.10 ou superior. O ETL e a geração do HTML usam a biblioteca padrão. O notebook usa Jupyter, pandas, NumPy e Matplotlib.

```text
python src/triagem.py
python src/gerar_painel.py
jupyter nbconvert --to notebook --execute --inplace analise_compras.ipynb
```

O pipeline lê o material congelado em `dados/fonte` e gera os produtos analíticos. Os limites de suporte e as apresentações estão em `config/materiais.json`. As figuras das três vistas estão em `figuras`. [Documentação oficial do Compras.gov.br](https://dadosabertos.compras.gov.br/swagger-ui/index.html)
