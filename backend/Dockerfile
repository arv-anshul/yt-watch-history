FROM python:3.11-slim

WORKDIR /backend

RUN pip install -U pip
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "-b", "0.0.0.0:8001" ]
