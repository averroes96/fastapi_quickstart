FROM python:3.12

# Create user
RUN useradd -ms /bin/sh user

ENV PYTHONPATH=/backend \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Install OS-level dependencies
RUN apt-get update && apt-get install -y curl build-essential

# Install pip & uv installer
RUN pip install --upgrade pip setuptools wheel
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /backend

# Copy code as root
COPY . /backend/

# ✅ Fix: Give user ownership of /backend so they can install stuff
RUN chown -R user:user /backend

# Drop privileges
USER user

# Install dependencies as the new user
RUN uv sync --frozen

# Run the task
CMD ["task", "run"]
