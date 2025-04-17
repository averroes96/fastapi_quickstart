FROM python:3.12

# Create a user and set environment variables
RUN useradd -ms /bin/sh user

ENV PYTHONPATH=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install OS-level dependencies
RUN apt-get update && apt-get install -y curl build-essential

# Install pip & uv installer as root
RUN pip install --upgrade pip setuptools wheel
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /backend

# Copy code
COPY . /backend/

# 🔻 Drop privileges before installing Python deps
USER user

# ✅ Install Python dependencies as non-root user
RUN uv sync --frozen

# Run the default task
CMD ["task", "run"]
