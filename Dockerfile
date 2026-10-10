# Stay on the Python minor version used by this project's CI.
ARG PYTHON_IMAGE=python:3.13-slim-trixie
FROM ${PYTHON_IMAGE} AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Qt's desktop (xcb) and offscreen platform dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-dejavu-core \
    libdbus-1-3 \
    libegl1 \
    libfontconfig1 \
    libfreetype6 \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 sudoku \
    && mkdir /data && chown sudoku:sudoku /data

WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/

FROM base AS test
RUN python -m pip install --no-cache-dir '.[dev]'
COPY tests/ ./tests/
ENV QT_QPA_PLATFORM=offscreen
USER sudoku
CMD ["python", "-m", "pytest", "-q", "-p", "no:cacheprovider"]

# The default target is the desktop application without development tools.
FROM base AS runtime
RUN python -m pip install --no-cache-dir .
WORKDIR /data
USER sudoku
CMD ["sudoku-inator"]
