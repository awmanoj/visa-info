FROM python:3.12-slim

WORKDIR /app

COPY index.html india_visa_requirements.json visa_unlock_mapping.json ./

EXPOSE 8000

CMD ["python", "-m", "http.server", "8000"]
