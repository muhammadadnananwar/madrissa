FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN DJANGO_SECRET_KEY=build DJANGO_DEBUG=false python manage.py collectstatic --noinput \
    && chmod +x start.sh && mkdir -p /app/media
EXPOSE 8000
CMD ["./start.sh"]
