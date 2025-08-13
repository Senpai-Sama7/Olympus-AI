FROM python:3.11-slim
WORKDIR /app
COPY services/retrieval/pyproject.toml ./pyproject.toml
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -e .
COPY services/retrieval/app ./app
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081"]
