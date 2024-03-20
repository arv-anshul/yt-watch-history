FROM python:3.11-slim

WORKDIR /app/frontend

# Install dependency for `wordcloud` module
RUN apt-get update && apt-get install -y gcc

RUN pip install -U pip uv
COPY requirements.txt /app/requirements.txt
RUN uv venv /app/.venv && uv pip install --no-cache-dir -r /app/requirements.txt

COPY . .

CMD [ "/app/.venv/bin/streamlit", "run", "README.py" ]
