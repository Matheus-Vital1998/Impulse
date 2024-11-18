# Usar uma imagem base do Python slim
FROM python:3.10-slim

# Configurar o diretório de trabalho
WORKDIR /app

# Copiar o arquivo requirements.txt para o container
COPY requirements.txt .

# Atualizar pip e instalar as dependências do projeto
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copiar todo o código da aplicação para o container
COPY . .

# Expor a porta do servidor Flask
EXPOSE 5000

# Comando para rodar a aplicação
CMD ["python", "main.py"]
