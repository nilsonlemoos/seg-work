FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads
EXPOSE 5000
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "app.py"]
