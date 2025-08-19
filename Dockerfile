FROM python:3.9-slim as builder

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/libs -r requirements.txt


FROM seleniarm/standalone-chromium

USER root
RUN apt-get update && \
    apt-get install -y python3 python3-pip --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
USER seluser

ENV PYTHONPATH=/app/libs


WORKDIR /app

COPY --from=builder /app/libs /app/libs

USER root
COPY . .

RUN chown -R seluser:seluser /app
USER seluser


EXPOSE 5001

CMD ["python3", "app.py"]
