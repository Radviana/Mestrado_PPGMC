import sys
import json
import time
import ollama
import yaspin
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from yaspin.spinners import Spinners


base_dir = Path(__file__).parent

# Pega o dia atual
hoje = datetime.now()

# Formata para YYYYMMDD
hoje_string = hoje.strftime("%Y%m%d")

# Formata para DDMMYYYY
hoje_string_arq = hoje.strftime("%d%m%Y")


def acessar_api(parametros_consulta):
    all_data = []
    total_pages = None
    headers = {"accept": "*/*"}
    current_page = parametros_consulta["pagina"]
    BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratacoes/proposta"
    NOME_ARQUIVO = base_dir / f"dados_contratacoes - {hoje_string_arq}.json"

    try:
        while True:
            print(f"Solicitando página {current_page}...")
            parametros_consulta["pagina"] = current_page
            response = requests.get(
                BASE_URL, params=parametros_consulta, headers=headers
            )

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
            if not page_items:
                print("\nNenhum item retornado nesta página; finalizando.")
                break
            #  - se numero_pagina >= total_pages (quando total_pages informado)
            if total_pages is not None and numero_pagina >= total_pages:
                print("\nÚltima página atingida.")
                break
            #  - se paginasRestantes == 0 (quando informado)
            if paginas_restantes is not None and paginas_restantes == 0:
                print("\nNão há mais páginas restantes.")
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
            f"\nDados agregados salvos em {NOME_ARQUIVO} (total {len(all_data)} registros)."
        )

    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão: {e}")
    except json.JSONDecodeError:
        print("Resposta não é JSON válido.")
        print(response.text)
    except IOError as e:
        print(f"Erro ao escrever arquivo: {e}")


def api_get():

    parametros_consulta = {
        "dataFinal": hoje_string,  # Formato AAAAMMDD
        "pagina": 1,  # Página inicial
        "tamanhoPagina": 50,  # Número de registros por página (Máx: 50)
    }
    arquivo_json = (
        base_dir / f"dados_contratacoes - {hoje_string_arq}.json"
    )  # nome do arquivo de entrada
    arquivo_saida = (
        base_dir / f"fichas_propostas - {hoje_string_arq}.txt"
    )  # nome do arquivo de saída

    try:
        acessar_api(parametros_consulta)

        dados = ler_json(arquivo_json)
        propostas = encontrar_propostas(dados)

        if not propostas:
            print("Nenhuma proposta encontrada no JSON.")
        else:
            fichas_txt = []
            for i, prop in enumerate(propostas):
                ficha = parser_propostas(prop)
                texto = imprimir_ficha(ficha, indice=i)
                fichas_txt.append(texto)

            salvar_txt(fichas_txt, arquivo_saida)
            print(f"\n{len(propostas)} proposta(s) processada(s) com sucesso.\n")

    except Exception as e:
        print(f"Erro ao processar o arquivo: {e}")
    return arquivo_saida  # Retorna o caminho do arquivo de saída para uso posterior


def encontrar_propostas(obj):
    # Encontra a lista de propostas no objeto JSON.
    if isinstance(obj, dict):
        data = obj.get("data")
        if isinstance(data, list):
            return data
    return []


def formatar_data(d):
    # Formata datas ISO em dd/mm/yyyy ou dd/mm/yyyy hh:mm:ss.
    if not d:
        return "-"  # Retorna hífen se vazio
    try:
        return datetime.fromisoformat(d.replace("Z", "")).strftime(
            "%d/%m/%Y %H:%M:%S"
        )  # Retorna formato com hora
    except ValueError:
        try:
            return datetime.strptime(d, "%Y-%m-%d").strftime(
                "%d/%m/%Y"
            )  # Retorna formato só data
        except Exception:
            return d  # Retorna o original se falhar


def imprimir_ficha(ficha: dict, indice=None):
    # Formata em texto a ficha da proposta.
    linhas = []
    linhas.append("=" * 70)
    if indice is not None:
        linhas.append(f"PROPOSTA Nº {indice + 1}")
        linhas.append("=" * 70)

    for chave, valor in ficha.items():
        linhas.append(f"{chave}: {valor}")

    linhas.append("\n")
    return "\n".join(linhas)


def instalar_pacote(package_name):
    print(f"Tentando instalar {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        # print(f"{package_name} instalado com sucesso.")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao instalar {package_name}: {e}")


def ler_json(caminho_arquivo: str):
    # Lê um arquivo JSON e retorna seu conteúdo (dict ou list).
    caminho = Path(caminho_arquivo)
    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho_arquivo}")

    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return dados


def parser_propostas(data: dict) -> dict:
    # Dicionário que extrai e formata os campos relevantes de uma proposta.
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


def salvar_txt(fichas: list[str], caminho_saida: str):
    # Salva as fichas formatadas em "imprimir_ficha" em um arquivo de texto.
    with open(caminho_saida, "w", encoding="utf-8") as f:
        for ficha in fichas:
            f.write(ficha + "\n\n")
    print(f"\nFichas salvas em: {caminho_saida}")


def txt_para_ollama(arquivo):
    with open(arquivo, "r", encoding="utf-8") as file:
        dados = file.read()
    return dados


def json_para_ollama(arquivo):
    with open(arquivo, "r", encoding="utf-8") as file:
        dados = json.load(file)
    return dados


def stream_resposta(
    client, modelo, requisicao
):  # Exibe a resposta do modelo em tempo real enquanto é gerada
    # Utiliza tqdm para criar um indicador de progresso
    try:
        from tqdm import tqdm
    except ImportError:
        print("O módulo 'tqdm' não está instalado.  Instale-o com: pip install tqdm")
        tqdm = None  # Define tqdm como None para evitar erros

    # Envia o prompt para o modelo e obtém a resposta
    print("Enviando prompt para o gemma3...")

    if tqdm:
        with tqdm(desc="Gerando resposta", total=100) as pbar:
            for i in range(
                100
            ):  # Simula o processo, substituindo pela chamada real da API
                time.sleep(0.05)  # Simula o tempo de resposta
                pbar.update(1)
            print("\n")
            for chunk in client.generate(model=modelo, prompt=requisicao, stream=True):
                print(chunk["response"], end="", flush=True)
    else:
        print("tqdm não está instalado.  Aguarde a resposta...")
        for chunk in client.generate(model=modelo, prompt=requisicao, stream=True):
            print(chunk["response"], end="", flush=True)


def save_resposta(
    client, modelo, requisicao, caminho_saida
):  # Salva a resposta do modelo em um arquivo de texto
    with yaspin.yaspin(
        Spinners.material,
        text="Analisando os dados...",
        color="green",
        timer=1,
        side="right",
    ) as spinner:
        try:
            resposta_modelo = client.generate(model=modelo, prompt=requisicao)
            resposta = resposta_modelo["response"]
            with open(caminho_saida, "w", encoding="utf-8") as file:
                file.write(resposta)
                print(f"\nResposta salva em: {caminho_saida}")
        except Exception as e:
            print(f"Erro ao gerar ou salvar a resposta: {e}")
        spinner.ok("✓ Concluído")
