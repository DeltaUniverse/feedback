FROM python:3.11-alpine AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev

WORKDIR /app

COPY requirements.txt ./
RUN python -m venv /install \
    && /install/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-alpine

WORKDIR /app
ENV PATH="/install/bin:$PATH"

COPY --from=build /install /install

RUN adduser -D appuser \
    && chown -R appuser:appuser /app

COPY --chown=appuser:appuser . .

USER appuser

CMD ["python", "main.py"]
