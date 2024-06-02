FROM python:3.12.3
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000

ENV DATA_PATH=/data

VOLUME /data
VOLUME /config

CMD ["python", "main.py"]
