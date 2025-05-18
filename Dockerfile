FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt


RUN python -c "from transformers import pipeline; pipeline('text2text-generation', model='prithivida/grammar_error_correcter_v1')"

COPY . .


EXPOSE 5000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --timeout 300 --workers 1 
