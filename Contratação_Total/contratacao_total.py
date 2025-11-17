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


def parse_proposta(data: dict) -> dict:
    return {
        "CNPJ do Órgão": data.get("orgaoEntidade", {}).get("cnpj", "-"),
        "Órgão (Razão Social)": data.get("orgaoEntidade", {}).get("razaoSocial", "-"),
        "UF": data.get("unidadeOrgao", {}).get("ufSigla", "-"),
        "Município": data.get("unidadeOrgao", {}).get("municipioNome", "-"),
        "Unidade": data.get("unidadeOrgao", {}).get("nomeUnidade", "-"),
        "Ano da Compra": data.get("anoCompra", "-"),
        "Número da Compra": data.get("numeroCompra", "-"),
        "Sequencial Compra": data.get("sequencialCompra", "-"),
        "Número Controle PNCP": data.get("numeroControlePNCP", "-"),
        "Modalidade": data.get("modalidadeNome", "-"),
        "Modalidade ID": data.get("modalidadeId", "-"),
        "Modo de Disputa": data.get("modoDisputaNome", "-"),
        "Modo de Disputa ID": data.get("modoDisputaId", "-"),
        "Tipo Instrumento Convocatório": data.get(
            "tipoInstrumentoConvocatorioNome", "-"
        ),
        "Tipo Instrumento Cod.": data.get("tipoInstrumentoConvocatorioCodigo", "-"),
        "Objeto": data.get("objetoCompra", "-"),
        "Informação Complementar": data.get("informacaoComplementar", "-"),
        "Valor Total Estimado (R$)": data.get("valorTotalEstimado", "-"),
        "Valor Total Homologado (R$)": data.get("valorTotalHomologado", "-"),
        "Processo": data.get("processo", "-"),
        "Situação ID": data.get("situacaoCompraId", "-"),
        "Situação Nome": data.get("situacaoCompraNome", "-"),
        "Data Abertura Proposta": formatar_data(data.get("dataAberturaProposta")),
        "Data Encerramento": formatar_data(data.get("dataEncerramentoProposta")),
        "Data Publicação PNCP": formatar_data(data.get("dataPublicacaoPncp")),
        "Data Atualização": formatar_data(data.get("dataAtualizacao")),
        "Data Atualização Global": formatar_data(data.get("dataAtualizacaoGlobal")),
        "Data Inclusão": formatar_data(data.get("dataInclusao")),
        "Amparo Legal": data.get("amparoLegal", {}).get("nome", "-"),
        "Descrição Amparo Legal": data.get("amparoLegal", {}).get("descricao", "-"),
        "Link Sistema Origem": data.get("linkSistemaOrigem", "-"),
        "Link Processo Eletrônico": data.get("linkProcessoEletronico", "-"),
        "Usuário Responsável": data.get("usuarioNome", "-"),
        "SRP (Sistema de Registro de Preços)": data.get("srp", "-"),
    }


def imprimir_ficha(ficha: dict, indice=None):
    linhas = []
    linhas.append("=" * 70)
    if indice is not None:
        linhas.append(f"PROPOSTA Nº {indice + 1}")
        linhas.append("=" * 70)

    for chave, valor in ficha.items():
        linhas.append(f"{chave}: {valor}")

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


def encontrar_propostas(obj):
    if isinstance(obj, dict):
        data = obj.get("data")
        if isinstance(data, list):
            return data

    return []


def salvar_txt(fichas: list[str], caminho_saida: str):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for ficha in fichas:
            f.write(ficha + "\n\n")
    print(f"\nFichas salvas em: {caminho_saida}")


BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"

base_dir = Path(__file__).parent

parametros_consulta = {
    'dataFinal': 20251231,      #Formato AAAAMMDD
    'pagina': 1,                #Página inicial
    'tamanhoPagina': 50         #Número de registros por página (Máx: 50)
}

headers = {"accept": "*/*"}
NOME_ARQUIVO = base_dir / "dados_contratacoes.json"

all_data = []
current_page = parametros_consulta["pagina"]
total_pages = None

try:
    while True:
        print(f"Solicitando página {current_page}...")
        parametros_consulta["pagina"] = current_page
        response = requests.get(BASE_URL, params=parametros_consulta, headers=headers)

        if response.status_code != 200:
            print(
                f"Erro na requisição da página {current_page}: {response.status_code}"
            )
            print(response.text)
            break

        payload = response.json()

        # Ajuste conforme estrutura da API: aqui os itens estão em 'data'
        page_items = payload.get("data", [])
        all_data.extend(page_items)

        # Pegar metadados de paginação (quando disponíveis)
        if total_pages is None:
            total_pages = payload.get("totalPaginas")

        numero_pagina = payload.get("numeroPagina", current_page)
        paginas_restantes = payload.get("paginasRestantes", None)

        print(
            f"Recebidos {len(page_items)} itens. página {numero_pagina}/{total_pages} - restantes: {paginas_restantes}"
        )

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
        "empty": len(all_data) == 0,
    }
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=4, ensure_ascii=False)

    print(
        f"Dados agregados salvos em {NOME_ARQUIVO} (total {len(all_data)} registros)."
    )

except requests.exceptions.RequestException as e:
    print(f"Erro de conexão: {e}")
except json.JSONDecodeError:
    print("Resposta não é JSON válido.")
    print(response.text)
except IOError as e:
    print(f"Erro ao escrever arquivo: {e}")

if __name__ == "__main__":
    arquivo_json = base_dir / "dados_contratacoes.json"  # nome do arquivo de entrada
    arquivo_saida = base_dir / "fichas_propostas.txt"  # nome do arquivo de saída

    try:
        dados = ler_json(arquivo_json)
        propostas = encontrar_propostas(dados)

        if not propostas:
            print("Nenhuma proposta encontrada no JSON.")
        else:
            fichas_txt = []
            for i, prop in enumerate(propostas):
                ficha = parse_proposta(prop)
                texto = imprimir_ficha(ficha, indice=i)
                fichas_txt.append(texto)

            salvar_txt(fichas_txt, arquivo_saida)
            print(f"\n{len(propostas)} proposta(s) processada(s) com sucesso.\n")

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
