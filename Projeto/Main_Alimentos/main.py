import os
import re
import time
import importlib
import functions  # Arquivo com as funções de instalação e chamada da API
from pathlib import Path

base_dir = Path(__file__).parent

def req(proposta):
    return f"""
    Você é um analista especializado em licitações públicas e alimentos.
    
    AAnalise o conteúdo de {proposta} e determine se a licitação representa uma oportunidade na área de alimentação e nutrição, com foco em:
    
    - hortifruti
    - frutas
    - legumes
    - verduras
    - alimentos perecíveis
    - merenda escolar
    -  gêneros alimentícios
    - produtos agropecuários

    Regras importantes:

    1. Se a licitação não for de computação, apenas retorne "Proposta X não é computação" onde X é o número do contrato

    2. Use principalmente:
    - "objetoCompra"
    - "informacaoComplementar"
    - contexto semântico

    3. Diferencie:
    - Compra direta de alimentos
    - Serviços de alimentação ou nutrição
    - Itens não relacionados a alimentos

    4. Seja conservador: só marque como alimentação se houver evidência clara ou plausível.

    5. Caso a licitação não seja da área, retorne como "Proposta X não é alimentação" e siga para a próxima.

    6. Para a saída, formate exatamente como abaixo, sem alterar a estrutura, mesmo que algum campo seja null ou vazio:
    Razão social: razão social da empresa contratante,
    É alimentação: true/false,
    Número do contrato: usando o campo Sequencial Compra,
    Tipo principal: hortifruti | frutas | legumes | verduras | pereciveis | merenda_escolar | alimentos | nao_aplicavel,
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
                sequencial = proposta.get("sequencialCompra", "-")
                prompt = req(proposta)
                try:
                    resposta = client.generate(
                        model=modelo,
                        prompt=prompt,
                        options={
                            "temperature": 0.1,
                            "repeat_penalty": 1.1,
                            "num_predict": 256,
                        },
                    )
                except functions.ollama.ResponseError as e:
                    if "token repeat limit reached" not in str(e).lower():
                        print(f"Erro ao gerar proposta {sequencial}: {e}")
                        continue

                    print(
                        f"Repetição excessiva ao gerar proposta {sequencial}; "
                        "tentando novamente com limite menor."
                    )
                    try:
                        resposta = client.generate(
                            model=modelo,
                            prompt=prompt,
                            options={
                                "temperature": 0.1,
                                "repeat_penalty": 1.2,
                                "num_predict": 160,
                            },
                        )
                    except functions.ollama.ResponseError as retry_error:
                        print(
                            f"Erro ao gerar proposta {sequencial} após nova tentativa: "
                            f"{retry_error}"
                        )
                        continue

                if re.search("É alimentação: true", resposta.response, re.IGNORECASE):
                    modo = "w" if primeiro else "a"
                    with open(caminho_saida_ollama_teste, modo, encoding="utf-8") as file:
                        file.write(resposta.response + "\n" + "\n")
                        print(f"\nResposta salva em: {caminho_saida_ollama_teste}")
                        primeiro = False
        except (OSError, ValueError) as e:
            print(f"Erro ao ler os dados ou salvar a resposta: {e}")
        spinner.ok("✓ Concluído")
