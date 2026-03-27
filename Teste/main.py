import os
import time
import importlib
import functions  # Arquivo com as funções de instalação e chamada da API
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

dados = functions.api_get()  # Chama a função para obter os dados da API

# dados = base_dir / "fichas_propostas - 04032026.txt"
# dados_convertidos = txt_para_ollama(dados)

dados = base_dir / f"dados_contratacoes - {functions.hoje_string_arq}.json"
dados_convertidos = functions.json_para_ollama(dados)

# Inicializa o client Ollama
functions.subprocess.run(["ollama", "pull", "gemma3"], check=True)  # Certifique-se de que o modelo esteja disponível
client = functions.ollama.Client()
modelo = "gemma3"  # Modelo a ser utilizado, certifique-se de que o modelo esteja disponível no Ollama

req1 = f"""
Você receberá o JSON {dados_convertidos} de uma licitação pública.

Sua tarefa é classificar se a licitação está relacionada à área de COMPUTAÇÃO, com foco específico em:

- computadores
- notebooks
- supercomputadores
- servidores
- equipamentos de informática

Critérios:
- Considere principalmente o campo "objetoCompra"
- Considere também "informacaoComplementar" se existir
- Ignore áreas como saúde, obras, serviços gerais, etc.

Responda APENAS no formato JSON:

{{
  "eh_computacao": true/false,
  "categoria_detectada": "computadores | notebooks | servidores | supercomputadores | nenhum",
  "justificativa": "explicação curta baseada no objetoCompra"
}}
"""

req2 = f"""
Analise a licitação do JSON {dados_convertidos} considerando tanto correspondência EXPLÍCITA quanto IMPLÍCITA com a área de computação.

Considere como relevantes:
- Aquisição de computadores, notebooks, servidores, supercomputadores
- Equipamentos de TI
- Infraestrutura computacional
- Termos genéricos que indiquem tecnologia (ex: "equipamentos de informática", "infraestrutura tecnológica")

NÃO considerar:
- Serviços médicos
- Obras
- Alimentação
- Transporte
- Serviços administrativos sem relação com TI

Sua tarefa:

1. Identificar se a licitação pertence à área de computação
2. Detectar o tipo de equipamento (se houver)
3. Avaliar o nível de certeza

Responda no formato JSON:

{{
  "eh_computacao": true/false,
  "tipo": "computador | notebook | servidor | supercomputador | ti_generico | nenhum",
  "nivel_confianca": "alto | medio | baixo",
  "trecho_relevante": "trecho do objetoCompra que justifica",
  "justificativa": "explicação objetiva"
}}
"""

req3 = f"""
Você é um analista especializado em licitações públicas e tecnologia da informação.

Analise o JSON {dados_convertidos} e determine se a licitação representa uma oportunidade na área de computação, com foco em:

- computadores
- notebooks
- servidores
- supercomputadores
- infraestrutura de TI

Regras importantes:

1. Use principalmente:
   - "objetoCompra"
   - "informacaoComplementar"
   - contexto semântico

2. Diferencie:
   - Compra direta de equipamentos
   - Serviços relacionados à TI
   - Itens não relacionados

3. Seja conservador: só marque como computação se houver evidência clara ou plausível.

Saída obrigatória:

{{
  "contrato_numero": número do contrato na ordem do json,
  "eh_computacao": true/false,
  "tipo_principal": "computadores | notebooks | servidores | supercomputadores | infraestrutura_ti | nao_aplicavel",
  "subtipo": "descrição mais específica ou null",
  "indicadores_encontrados": ["palavra1", "palavra2"],
  "risco_falso_positivo": "baixo | medio | alto",
  "justificativa": "explicação técnica baseada nos dados"
}}

"""


caminho_saida_ollama_req1 = base_dir / "resposta_ollama_req1.txt"
caminho_saida_ollama_req2 = base_dir / "resposta_ollama_req2.txt"
caminho_saida_ollama_req3 = base_dir / "resposta_ollama_req3.txt"


if __name__ == "__main__":
    functions.save_resposta(client, modelo, req1, caminho_saida_ollama_req1)
    functions.save_resposta(client, modelo, req2, caminho_saida_ollama_req2)
    functions.save_resposta(client, modelo, req3, caminho_saida_ollama_req3)
    os.system("pause")
