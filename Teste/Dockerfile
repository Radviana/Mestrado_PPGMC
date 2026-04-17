# Imagem oficial do Python como base
FROM python:3.13

ADD main.py .
ADD functions.py .
ADD requirements.txt .

# Instalar dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para rodar a aplicação
CMD ["python", "main.py"]