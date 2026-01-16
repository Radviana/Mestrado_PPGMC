import json
import time
import requests
from pathlib import Path
from datetime import datetime

def formatar_data(d):
    "Formata datas ISO em dd/mm/yyyy ou dd/mm/yyyy hh:mm:ss."
    if not d:
        return "-"
    try:
        return datetime.fromisoformat(d.replace("Z", "")).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return d  # retorna o original se falhar

def parse_contrato(data: dict) -> dict:
    return {
        "Órgão Contratante": data.get("orgaoEntidade", {}).get("razaoSocial", "-"),
        "CNPJ do Órgão": data.get("orgaoEntidade", {}).get("cnpj", "-"),
        "UF": data.get("unidadeOrgao", {}).get("ufSigla", "-"),
        "Município": data.get("unidadeOrgao", {}).get("municipioNome", "-"),

        "Fornecedor": data.get("nomeRazaoSocialFornecedor", "-"),
        "CNPJ do Fornecedor": data.get("niFornecedor", "-"),
        "País": data.get("codigoPaisFornecedor", "-"),

        "Número do Contrato": data.get("numeroContratoEmpenho", "-"),
        "Ano": data.get("anoContrato", "-"),
        "Tipo de Contrato": data.get("tipoContrato", {}).get("nome", "-"),
        "Processo": data.get("processo", "-"),
        "Categoria do Processo": data.get("categoriaProcesso", {}).get("nome", "-"),

        "Objeto": data.get("objetoContrato", "-"),
        "Valor Inicial (R$)": data.get("valorInicial", "-"),
        "Valor Global (R$)": data.get("valorGlobal", "-"),
        "Número de Parcelas": data.get("numeroParcelas", "-"),

        "Data de Assinatura": formatar_data(data.get("dataAssinatura")),
        "Vigência Início": formatar_data(data.get("dataVigenciaInicio")),
        "Vigência Fim": formatar_data(data.get("dataVigenciaFim")),
        "Publicação no PNCP": formatar_data(data.get("dataPublicacaoPncp")),
        "Última Atualização": formatar_data(data.get("dataAtualizacao")),

        "Usuário Responsável": data.get("usuarioNome", "-")
    }

def imprimir_ficha(ficha: dict, indice=None):
    linhas = []
    linhas.append("-" * 60)
    if indice is not None:
        linhas.append(f"Contrato nº {indice + 1}")
        linhas.append("-" * 60)
    for chave, valor in ficha.items():
        linhas.append(f"{chave}: {valor}")
    #linhas.append("-" * 60)
    linhas.append("\n")
    return "\n".join(linhas)

def ler_json(caminho_arquivo: str):
    "Lê um arquivo JSON e retorna seu conteúdo (dict ou list)."
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados

def encontrar_contratos(obj):
    contratos = []

    if isinstance(obj, dict):
        if "objetoContrato" in obj and "orgaoEntidade" in obj:
            contratos.append(obj)
        else:
            for v in obj.values():
                contratos.extend(encontrar_contratos(v))

    elif isinstance(obj, list):
        for item in obj:
            contratos.extend(encontrar_contratos(item))

    return contratos

def salvar_txt(fichas: list[str], caminho_saida: str):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for ficha in fichas:
            f.write(ficha + "\n\n")
    print(f"\nFichas salvas em: {caminho_saida}")


BASE_URL = 'https://pncp.gov.br/api/consulta/v1/contratos'

base_dir = Path(__file__).parent

# Pega o dia atual
hoje = datetime.now()

# Formata para YYYYMMDD
hoje_string = hoje.strftime("%Y%m%d")

'''parametros_consulta = {
    'dataInicial': hoje_string, #Formato AAAAMMDD
    'dataFinal': hoje_string,   #Formato AAAAMMDD
    'pagina': 1
}'''
parametros_consulta = {
    'dataInicial': 20250801, #Formato AAAAMMDD
    'dataFinal': 20250831,   #Formato AAAAMMDD
    'pagina': 1
}

headers = {'accept': '*/*'}
NOME_ARQUIVO = base_dir / f"dados_contratos {parametros_consulta['dataInicial']}_{parametros_consulta['dataFinal']}.json"

all_data = []
current_page = parametros_consulta['pagina']
total_pages = None

try:
    while True:
        print(f"Solicitando página {current_page}...")
        parametros_consulta['pagina'] = current_page
        response = requests.get(BASE_URL, params=parametros_consulta, headers=headers)

        if response.status_code != 200:
            print(f"Erro na requisição da página {current_page}: {response.status_code}")
            print(response.text)
            break

        payload = response.json()

        # Ajuste conforme estrutura da API: aqui os itens estão em 'data'
        page_items = payload.get('data', [])
        all_data.extend(page_items)

        # Pegar metadados de paginação (quando disponíveis)
        if total_pages is None:
            total_pages = payload.get('totalPaginas')

        numero_pagina = payload.get('numeroPagina', current_page)
        paginas_restantes = payload.get('paginasRestantes', None)

        print(f"Recebidos {len(page_items)} itens. página {numero_pagina}/{total_pages} - restantes: {paginas_restantes}")

        # Condições de parada:
        #  - se não veio item algum
        #  - se numero_pagina >= total_pages (quando total_pages informado)
        #  - se paginasRestantes == 0 (quando informado)
        if not page_items:
            print("Nenhum item retornado nesta página; finalizando.")
            break
        if total_pages is not None and numero_pagina >= total_pages:
            print("Última página atingida.")
            break
        if paginas_restantes is not None and paginas_restantes == 0:
            print("Não há mais páginas restantes.")
            break

        # Avança para a próxima página
        current_page = numero_pagina + 1

        # Pequena pausa para evitar sobrecarregar a API
        time.sleep(0.2)

    # Salvar resultados agregados
    resultado = {
        "data": all_data,
        "totalRegistros": len(all_data),
        "totalPaginas": total_pages,
        "numeroPagina": 1,
        "paginasRestantes": 0,
        "empty": len(all_data) == 0
    }
    with open(NOME_ARQUIVO, 'w', encoding='utf-8') as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    print(f"Dados agregados salvos em {NOME_ARQUIVO} (total {len(all_data)} registros).")

except requests.exceptions.RequestException as e:
    print(f"Erro de conexão: {e}")
except json.JSONDecodeError:
    print("Resposta não é JSON válido.")
    print(response.text)
except IOError as e:
    print(f"Erro ao escrever arquivo: {e}")

if __name__ == "__main__":
    arquivo_json = base_dir / f"dados_contratos {parametros_consulta['dataInicial']}_{parametros_consulta['dataFinal']}.json"        # nome do arquivo de entrada
    arquivo_saida = base_dir / f"fichas_contratos {parametros_consulta['dataInicial']}_{parametros_consulta['dataFinal']}.txt"       # nome do arquivo de saída

    try:
        dados = ler_json(arquivo_json)
        contratos = encontrar_contratos(dados)

        if not contratos:
            print("Nenhum contrato encontrado no JSON. Verifique a estrutura do arquivo.")
        else:
            fichas_txt = []
            for i, contrato in enumerate(contratos):
                ficha = parse_contrato(contrato)
                texto = imprimir_ficha(ficha, indice=i)
                fichas_txt.append(texto)

            salvar_txt(fichas_txt, arquivo_saida)
            print(f"\n{len(contratos)} contrato(s) processado(s) com sucesso.\n")

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")