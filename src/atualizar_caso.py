"""Regenera a ficha documental demonstrativa do item 43 com a API aberta."""
from datetime import date
from decimal import Decimal
import json
from pathlib import Path
from urllib.request import urlopen

DIRETORIO = Path(__file__).resolve().parents[1] / 'casos'
COMPRA = '16033206000542025'
ITEM = '1603320600054202500043'
ENDERECO = ('https://dadosabertos.compras.gov.br/modulo-contratacoes/'
            '2.1_consultarItensContratacoes_PNCP_14133_Id?tipo=idCompra'
            f'&codigo={COMPRA}&idCompraItem={ITEM}')


def consultar_item():
    with urlopen(ENDERECO, timeout=30) as resposta:
        registros = json.load(resposta)['resultado']
    if len(registros) != 1:
        raise ValueError('O identificador não retornou um único item para revisão.')
    item = registros[0]
    descricao = item['descricaodetalhada']
    if 'caixa com 20 comprimidos' not in descricao.lower():
        raise ValueError('A descrição da fonte mudou. Revisar a interpretação da embalagem.')
    preco = Decimal(str(item['valorUnitarioResultado']))
    return {
        'data_da_conferencia': date.today().isoformat(),
        'id_compra': COMPRA,
        'id_compra_item': ITEM,
        'unidade_compradora': 'Policlínica Militar da Praia Vermelha/RJ',
        'catmat': '267778',
        'fonte_oficial_item': ENDERECO,
        'fonte_processo': 'https://pncp.gov.br/app/editais/00394452000103/2025/20613',
        'termo_de_referencia_conferido': {
            'documento': 'Termo de Referência 36/2025',
            'url': 'https://pncp.gov.br/pncp-api/v1/orgaos/00394452000103/compras/2025/20613/arquivos/2#page=6',
            'sha256_pdf_consultado': '4e2daf4ba28485f5337d7ec550960cffd9d8f434c05d92d1af51da8a755556e9',
            'data_da_leitura_do_termo': '2026-11-09',
            'pagina': 6,
            'item': 43,
            'quantidade_solicitada': 5,
            'unidade_solicitada': 'Caixa com 20 comprimidos',
            'preco_unitario_estimado_brl': '18.36',
            'total_estimado_brl': '91.80'
        },
        'campos_da_fonte': {chave: item[chave] for chave in [
            'numeroItemCompra', 'unidadeMedida', 'descricaodetalhada',
            'quantidadeResultado', 'valorUnitarioResultado', 'valorUnitarioEstimado'
        ]},
        'preco_por_comprimido_se_a_unidade_cobrada_for_a_caixa_com_20': str(preco / 20),
        'interpretacao': (
            'O termo de referência especifica cinco caixas de 20 comprimidos. O campo '
            'estruturado da base de resultados indica comprimido. Aplicado à caixa prevista, '
            'o preço homologado equivale a R$ 0,8695 por comprimido. Para confirmar '
            'a unidade faturada, seria necessário consultar os documentos de execução. '
            'O teste histórico preserva o valor registrado na extração.'
        )
    }


if __name__ == '__main__':
    ficha = consultar_item()
    DIRETORIO.mkdir(exist_ok=True)
    destino = DIRETORIO / 'policlinica-paracetamol.json'
    destino.write_text(json.dumps(ficha, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(destino.name)

