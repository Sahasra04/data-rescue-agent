FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

ENV GOOGLE_GENAI_USE_ENTERPRISE=1
ENV GOOGLE_CLOUD_PROJECT=project-55baabff-7a22-41ac-91e
ENV GOOGLE_CLOUD_LOCATION=us

EXPOSE 8080
CMD ["python", "app.py"]