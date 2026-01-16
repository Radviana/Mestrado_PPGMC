import json
from pathlib import Path
from datetime import datetime


def formatar_data(d):
    if not d:
        return "-"
    try:
        return datetime.fromisoformat(d.replace("Z", "")).strftime("%d/%m/%Y %H:%M:%S")
    except Exception:
        return d


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
    linhas.append("=" * 70)
    if indice is not None:
        linhas.append(f"PROPOSTA Nº {indice + 1}")
        linhas.append("=" * 70)

    for chave, valor in ficha.items():
        linhas.append(f"{chave}: {valor}")

    linhas.append("\n")
    return "\n".join(linhas)


def salvar_txt(fichas: list[str], caminho_saida: str):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for ficha in fichas:
            f.write(ficha + "\n\n")
    print(f"\nFichas salvas em: {caminho_saida}")


# ------------------ EXECUÇÃO ------------------

if __name__ == "__main__":

    base_dir = Path(__file__).parent

    # Encontrar todos os arquivos JSON que começam com "dados_contratos"
    arquivos_json = sorted(base_dir.glob("dados_contratos*.json"))
    
    if not arquivos_json:
        print("Nenhum arquivo 'dados_contratos*.json' encontrado na pasta.")
        exit()

    print(f"Encontrados {len(arquivos_json)} arquivo(s) para processar:")
    for arquivo in arquivos_json:
        print(f"  - {arquivo.name}")

    total_fichas = 0

    # Processar cada arquivo JSON
    for arquivo_json in arquivos_json:
        print(f"\nProcessando: {arquivo_json.name}")
        
        try:
            with open(arquivo_json, "r", encoding="utf-8") as f:
                dados = json.load(f)

            itens = dados.get("data", [])
            if not itens:
                print(f"  Nenhuma proposta encontrada em {arquivo_json.name}.")
                continue

            fichas_txt = []
            for i, item in enumerate(itens):
                ficha = parse_contrato(item)
                fichas_txt.append(imprimir_ficha(ficha, indice=i))

            # Gerar nome do arquivo de saída a partir do arquivo de entrada
            nome_saida = arquivo_json.name.replace("dados_contratos", "fichas_propostas").replace(".json", ".txt")
            arquivo_saida = base_dir / nome_saida
            
            salvar_txt(fichas_txt, str(arquivo_saida))
            total_fichas += len(fichas_txt)
            print(f"  {len(fichas_txt)} propostas processadas.")

        except Exception as e:
            print(f"  Erro ao processar {arquivo_json.name}: {e}")
            continue

    if total_fichas > 0:
        print(f"\n{total_fichas} propostas processadas com sucesso em total.")
    else:
        print("\nNenhuma proposta foi processada.")
