FROM python:3.12-alpine AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine AS runner

WORKDIR /app

COPY --from=builder /install /usr/local

ENV PYTHONPATH=/usr/local/lib/python3.11/site-packages
ENV MONGO_URL=
ENV MONGO_DB=

COPY /app .

CMD ["fastapi", "run", "main.py", "--port", "80"]

EXPOSE 80
