FROM python:3.11-slim

WORKDIR /app/backend

RUN pip install -U pip uv
COPY requirements.txt /app/requirements.txt
RUN uv venv /app/.venv && uv pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD [ "/app/.venv/bin/gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app:app", "-b", "0.0.0.0:8001" ]
