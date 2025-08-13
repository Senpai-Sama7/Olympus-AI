FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

WORKDIR /app

COPY pyproject.toml /app/
RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn[standard]==0.30.0 pydantic==2.7.0

COPY app /app/app

EXPOSE 8083

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083"]
