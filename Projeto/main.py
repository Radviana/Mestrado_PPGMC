import os
import re
import time
import importlib
import functions  # Arquivo com as funções de instalação e chamada da API
from pathlib import Path

base_dir = Path(__file__).parent

def req(proposta):
    return f"""
    Você é um analista especializado em licitações públicas e tecnologia da informação.

    Analise o conteúdo de {proposta} e determine se a licitação representa uma oportunidade na área de computação, com foco em:

    - computadores
    - notebooks
    - servidores
    - supercomputadores
    - infraestrutura de TI

    Regras importantes:

    1. Se a licitação não for de computação, apenas retorne "Proposta X não é computação" onde X é o número do contrato

    2. Use principalmente:
    - "objetoCompra"
    - "informacaoComplementar"
    - contexto semântico

    3. Diferencie:
    - Compra direta de equipamentos
    - Serviços relacionados à TI
    - Itens não relacionados

    4. Seja conservador: só marque como computação se houver evidência clara ou plausível.

    5. Caso a licitação não seja da área, retorne como "Proposta X não é computação" e siga para a próxima.

    6. Para a saída, formate exatamente como abaixo, sem alterar a estrutura, mesmo que algum campo seja null ou vazio:
    Razão social: razão social da empresa contratante,
    É computação: true/false,
    Número do contrato: usando o campo Sequencial Compra,
    Tipo principal: computadores | notebooks | servidores | supercomputadores | infraestrutura_ti | nao_aplicavel,
    Subtipo: descrição mais específica ou null,
    Indicadores encontrados: "palavra1", "palavra2",
    Risco de ser falso positivo: baixo | medio | alto,
    Justificativa: "explicação técnica baseada nos dados"
    """


if __name__ == "__main__":
    #dados = functions.api_get()  # Chama a função para obter os dados da API
    caminho_dados = base_dir / f"dados_contratacoes - {functions.hoje_string_arq}.json" # Define o caminho para o arquivo de dados da API
    caminho_saida_ollama_teste = base_dir / f"resposta_ollama_teste_{functions.hoje_string_arq}.txt" # Define o caminho de saída para o arquivo de resposta
    
    # Modelo a ser utilizado
    modelo = "gemma3"
    # Certifica que o modelo esteja disponível
    functions.subprocess.run(
        ["ollama", "pull", f"{modelo}"], check=True
    )
    # Inicializa o client Ollama
    client = functions.ollama.Client()
    
    
    with functions.yaspin.yaspin(
        functions.Spinners.material,
        text="Analisando os dados...",
        color="green",
        timer=1,
        side="right",
    ) as spinner:
        try:
            primeiro = True
            for proposta in functions.json_para_ollama(caminho_dados):
                resposta = client.generate(model=modelo, prompt=req(proposta))
                if(re.search("É computação: true", resposta.response, re.IGNORECASE)):
                    modo = "w" if primeiro else "a"
                    with open(caminho_saida_ollama_teste, modo, encoding="utf-8") as file:
                        file.write(resposta.response + "\n" + "\n")
                        print(f"\nResposta salva em: {caminho_saida_ollama_teste}")
                        primeiro = False
        except Exception as e:
            print(f"Erro ao gerar ou salvar a resposta: {e}")
        spinner.ok("✓ Concluído")