FROM python:3.11

WORKDIR /usr/agent

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY data/ ./data/

WORKDIR /usr/agent/src

CMD ["python", "main.py"]