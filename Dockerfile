
# Base image pinned by digest (reproducible, tamper-evident); Dependabot bumps it.
FROM python:3.12@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7

# Use .dockerignore to exclude unnecessary files (e.g. .git, tests, docs, assets, etc.)

# Copy only requirements.txt and main files to root
COPY requirements.txt ./

# Copy only necessary source files to /src
COPY src/ /src/

WORKDIR /src

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev

# Pinned build-tooling versions keep the image reproducible; override with
# --build-arg if a newer patched release is needed. These pins clear the
# pip / setuptools / wheel CVE scan findings (setuptools 83 also vendors the
# patched jaraco.context 6.1 + wheel 0.46.3 under setuptools/_vendor/).
ARG PIP_VERSION=26.1.2
ARG SETUPTOOLS_VERSION=83.0.0
ARG WHEEL_VERSION=0.47.0
# Upgrade build tooling, then purge the vulnerable bundled .whl the base image
# ships: the scoped find deletes the ensurepip _bundled wheels (old pip/
# setuptools/wheel that scanners flag), plus the pip cache. Scoped to
# /usr/local/lib on purpose (no full-filesystem scan). The block ends in
# `true`, so this best-effort cleanup never fails the build; the pip upgrade
# stays &&-gated so a failed upgrade still does.
RUN pip install --no-cache-dir --upgrade "pip==${PIP_VERSION}" "setuptools==${SETUPTOOLS_VERSION}" "wheel==${WHEEL_VERSION}" \
    && { \
        find /usr/local/lib -type d -name "_bundled" -path "*ensurepip*" -exec rm -rf {} + 2>/dev/null; \
        rm -rf /root/.cache/pip; \
        true; \
    }

RUN pip install --no-cache-dir -r /requirements.txt

RUN chmod 444 main.py
RUN chmod 444 /requirements.txt

# Unprivileged runtime user (no shell, no home). SAVE_IMAGES/DEBUG image dumps
# need a writable volume mounted at IMAGES_OUTPUT_DIR when enabled.
RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app
USER app

ENV PORT 8084

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 900 main:app


# Run the application
# CMD ["python", "main.py"]