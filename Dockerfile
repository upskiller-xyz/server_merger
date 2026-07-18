
FROM python:3.12

# Use .dockerignore to exclude unnecessary files (e.g. .git, tests, docs, assets, etc.)

# Copy only requirements.txt and main files to root
COPY requirements.txt ./

# Copy only necessary source files to /src
COPY src/ /src/

WORKDIR /src

RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev

# Upgrade build tooling & purge old bundled/cached wheels the base image ships
# (fixes pip / setuptools / wheel CVEs; ensurepip stashes vulnerable .whl files
# that scanners still flag even after an upgrade)
RUN pip install --no-cache-dir --upgrade "pip>=25.3" "setuptools>=78.1.1" "wheel>=0.46.1" \
    && { \
        find / -type d -name "_bundled" -path "*ensurepip*" -exec rm -rf {} + 2>/dev/null || true; \
        find / -type f -name "*.whl" -delete 2>/dev/null || true; \
        rm -rf /root/.cache/pip; \
    }

RUN pip install --no-cache-dir -r /requirements.txt

RUN chmod 444 main.py
RUN chmod 444 /requirements.txt

ENV PORT 8084

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 900 main:app


# Run the application
# CMD ["python", "main.py"]