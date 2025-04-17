FROM python:3.12

RUN useradd -ms /bin/sh user

ENV PYTHONPATH=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

RUN apt-get update && apt-get install -y curl build-essential

RUN pip install --upgrade pip setuptools wheel

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /backend

# Copy the full source code (including libs/core)
COPY . /backend/

# Now uv can resolve local path dependencies
RUN uv sync --frozen

# Drop privileges after deps installed
USER user

CMD ["task", "run"]