ARG PYTHON_VERSION=3.12

FROM node:22-alpine AS dashboard
WORKDIR /dashboard
ARG VITE_BASE_API=/api/
ENV VITE_BASE_API=$VITE_BASE_API
COPY app/dashboard/package*.json ./
RUN npm ci --ignore-scripts
COPY app/dashboard/ ./
RUN npm run build -- --outDir build --assetsDir statics --base /dashboard/ \
    && cp build/index.html build/404.html

FROM python:$PYTHON_VERSION-slim AS build
ARG XRAY_VERSION=26.3.27
ARG TARGETARCH

ENV PYTHONUNBUFFERED=1

WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl unzip gcc python3-dev libpq-dev \
    && case "$TARGETARCH" in amd64) XRAY_ARCH=64 ;; arm64) XRAY_ARCH=arm64-v8a ;; *) exit 1 ;; esac \
    && curl -fL --retry 3 "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-${XRAY_ARCH}.zip" -o /tmp/xray.zip \
    && curl -fL --retry 3 "https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-${XRAY_ARCH}.zip.dgst" -o /tmp/xray.dgst \
    && python3 -c 'import hashlib,re; expected=re.search(r"SHA2?-?256(?:SUM)?[ =:]+([a-fA-F0-9]{64})",open("/tmp/xray.dgst").read(),re.I); assert expected and hashlib.sha256(open("/tmp/xray.zip","rb").read()).hexdigest() == expected[1].lower(), "Xray checksum mismatch"' \
    && mkdir -p /usr/local/share/xray \
    && unzip /tmp/xray.zip -d /usr/local/share/xray \
    && install /usr/local/share/xray/xray /usr/local/bin/xray \
    && rm /tmp/xray.zip /tmp/xray.dgst \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt /code/
RUN python3 -m pip install --upgrade pip 'setuptools<81' \
    && pip install --no-cache-dir --upgrade -r /code/requirements.txt

FROM python:$PYTHON_VERSION-slim

ENV PYTHON_LIB_PATH=/usr/local/lib/python${PYTHON_VERSION%.*}/site-packages
WORKDIR /code

RUN apt-get update \
    && apt-get install -y --no-install-recommends iproute2 \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf $PYTHON_LIB_PATH/*

COPY --from=build $PYTHON_LIB_PATH $PYTHON_LIB_PATH
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/share/xray /usr/local/share/xray

COPY . /code
COPY --from=dashboard /dashboard/build /code/app/dashboard/build

RUN sed -i 's/\r$//' /code/marzban-cli.py \
    && ln -s /code/marzban-cli.py /usr/bin/marzban-cli \
    && chmod +x /usr/bin/marzban-cli

CMD ["bash", "-c", "alembic upgrade head && exec python main.py"]
