FROM docker-mirrors.alauda.cn/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ARG APT_MIRROR=mirrors.tuna.tsinghua.edu.cn
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

WORKDIR /app

RUN if [ "$APT_MIRROR" != "deb.debian.org" ]; then \
    sed -i "s|deb.debian.org|$APT_MIRROR|g" /etc/apt/sources.list.d/debian.sources; \
  fi \
  && apt-get update -o Acquire::Retries=5 -o Acquire::http::Timeout=20 \
  && apt-get install -y --no-install-recommends build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt -i "$PIP_INDEX_URL" --trusted-host "$PIP_TRUSTED_HOST"

COPY . .
RUN chmod +x /app/scripts/bootstrap-backend.sh

EXPOSE 8000
