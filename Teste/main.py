import os
import time
import importlib
import functions # Arquivo com as funções de instalação e chamada da API
from pathlib import Path

# Verifica e instala os pacotes necessários listados em requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as file:
    requirements = file.readlines()

for req in requirements:
    req = req.strip()
    try:
        importlib.import_module(req)
        print(f"O módulo {req} já está instalado.")
    except ImportError:
        functions.instalar_pacote(req)

base_dir = Path(__file__).parent

# dados = base_dir / "fichas_propostas - 04032026.txt"
# dados_convertidos = txt_para_ollama(dados)

dados = base_dir / "dados_contratacoes - 04032026.json"
dados_convertidos = functions.json_para_ollama(dados)

# Inicializa o client Ollama
client = functions.ollama.Client()
modelo = "gemma3"  # Modelo a ser utilizado, certifique-se de que o modelo esteja disponível no Ollama
requisicao = f"Analise o arquivo json de {dados_convertidos} e com base no campo 'ufNome', retorne apenas as licitações do estado da Bahia."  # Prompt utilizado para o modelo

caminho_saida_ollama = base_dir / "resposta_ollama.txt"


if __name__ == "__main__":
    print("Main iniciado.")

    # dados = functions.api_get()  # Chama a função para obter os dados da API
    # functions.save_resposta(client, modelo, requisicao, caminho_saida_ollama)
    # functions.stream_resposta(client, modelo, requisicao)
    # os.system("pause")
