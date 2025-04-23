FROM python:3.12-slim

ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV TZ=Europe/Moscow

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app
WORKDIR app

RUN uv sync --frozen --no-cache

ENTRYPOINT ["tail"]
CMD ["-f","/dev/null"]
