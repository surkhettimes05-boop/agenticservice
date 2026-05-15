FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
COPY custom_agents/agentic_it_firm/requirements.txt custom_agents/agentic_it_firm/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV PORT=8000
CMD ["sh", "-c", "uvicorn dashboard.app:app --host 0.0.0.0 --port ${PORT}"]
