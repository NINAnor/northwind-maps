FROM registry.opensuse.org/opensuse/leap:latest as base
RUN --mount=type=cache,target=/var/cache/zypper \
    zypper install --no-recommends -y python311 gdal proj
WORKDIR /app
ENV PYTHONPATH=/app/.venv/lib
ENV PATH=$PATH:/app/.venv/bin

FROM base as pdm
RUN --mount=type=cache,target=/var/cache/zypper \
    zypper install --no-recommends -y python311-pip git
RUN python3.11 -m pip install pdm
COPY ./pyproject.toml ./pdm.lock .
RUN --mount=type=cache,target=/var/cache/zypper \
    zypper install --no-recommends -y gdal-devel gcc gcc-c++ python311-devel
RUN pdm install --prod
RUN pdm add gdal==$(rpm -q --queryformat='%{VERSION}' gdal)

FROM pdm
COPY src src
ENTRYPOINT ["python", "src/main.py"]
