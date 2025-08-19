FROM python:3.9-slim as builder

WORKDIR /app

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/libs -r requirements.txt

FROM seleniarm/standalone-chromium

ENV PYTHONPATH=/app/libs
ENV PATH="/app/libs/bin:${PATH}"

WORKDIR /app

COPY --from=builder /app/libs /app/libs

COPY . .

EXPOSE 5001

CMD ["python", "app.py"]
