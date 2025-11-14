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


def salvar_txt(fichas: list[str], caminho_saida: str):
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for ficha in fichas:
            f.write(ficha + "\n\n")
    print(f"\nFichas salvas em: {caminho_saida}")


# ------------------ EXECUÇÃO ------------------

if __name__ == "__main__":

    base_dir = Path(__file__).parent

    arquivo_json = base_dir / "dados_contratacoes.json"
    arquivo_saida = base_dir / "fichas_propostas.txt"

    with open(arquivo_json, "r", encoding="utf-8") as f:
        dados = json.load(f)

    itens = dados.get("data", [])
    if not itens:
        print("Nenhuma proposta encontrada no JSON.")
        exit()

    fichas_txt = []
    for i, item in enumerate(itens):
        ficha = parse_proposta(item)
        fichas_txt.append(imprimir_ficha(ficha, indice=i))

    salvar_txt(fichas_txt, arquivo_saida)
    print(f"{len(fichas_txt)} propostas processadas com sucesso.")
