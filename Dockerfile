FROM python:3.11-slim

# Instala dependências essenciais
RUN apt-get update && apt-get install -y cron supervisor

# Define diretório de trabalho
WORKDIR /app

# Copia arquivos necessários
COPY requirements.txt coletor.py web.py ./

ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Instala dependências do Python
RUN pip install --no-cache-dir -r requirements.txt

# Adiciona cron para rodar das 7h às 18h
RUN echo "0 7 * * * root /usr/local/bin/python /app/coletor.py" >> /etc/crontab
RUN echo "0 18 * * * root pkill -f coletor.py" >> /etc/crontab

# Expõe a porta do Flask
EXPOSE 5000

CMD ["/usr/local/bin/python", "/app/coletor.py"]
CMD ["/usr/local/bin/python", "/app/web.py"]
