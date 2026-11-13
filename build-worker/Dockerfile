FROM node:20-alpine
ENV PYTHONDONTWRITEBYTECODE=1 npm_config_audit=false npm_config_fund=false npm_config_cache=/tmp/npm-cache
WORKDIR /service
COPY requirements.txt .
RUN apk add --no-cache python3 py3-pip && pip install --no-cache-dir --break-system-packages -r requirements.txt
COPY app.py .
RUN mkdir -p /data/previews && chmod 700 /data/previews
EXPOSE 8001
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
