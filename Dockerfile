# Usar uma imagem base do Python
FROM python:3.10-slim

# Definir o diretório de trabalho
WORKDIR /app

# Copiar o arquivo requirements.txt e instalar as dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código da aplicação
COPY . .

# Expor a porta usada pelo Flask (padrão: 5000)
EXPOSE 5000

# Configurar o comando de execução do Flask
CMD ["python", "main.py"]
