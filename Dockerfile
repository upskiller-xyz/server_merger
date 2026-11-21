# Merger image on Project Hummingbird (Red Hat hardened, distroless Python).
#
# Two stages: the -builder image (has pip and a shell) builds a venv, and the
# distroless runtime image (no shell, no package manager, runs as UID 65532)
# only receives the venv and the source. Both are pinned by index digest
# (multi-arch); Dependabot bumps them, or bump tag and digest together:
#   docker buildx imagetools inspect registry.access.redhat.com/hi/python:3.14
#
# No OS packages are installed: opencv-python-headless (no libGL/X11 needed),
# numpy and shapely ship manylinux wheels that bundle their native libraries.

FROM registry.access.redhat.com/hi/python:3.15-builder@sha256:41b08fc687e756ba1d099e14ab3595028ef4b1f649f328336cad74b318a539df AS build

# The builder image runs as 65532 too; installing into /opt needs root.
USER 0
RUN python3 -m venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
# pip is only needed to build the venv; removing it keeps it (and its CVEs)
# out of the runtime image.
RUN /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && /opt/venv/bin/pip uninstall -y pip

FROM registry.access.redhat.com/hi/python:3.15@sha256:1739a8c22a807a31cb06a266747b72a276d8e416910a920941b168681a72420b

COPY --from=build /opt/venv /opt/venv
# Copied as root-owned files, so the runtime user cannot modify them.
COPY requirements.txt /requirements.txt
COPY src/ /src/

WORKDIR /src

# PORT is read by gunicorn itself (no --bind: it binds 0.0.0.0:$PORT), so the
# platform can still override it without a shell to expand $PORT.
# Only /tmp is writable for UID 65532: SAVE_IMAGES/DEBUG image dumps go to
# /tmp/outputs unless IMAGES_OUTPUT_DIR points at a mounted writable volume.
ENV PATH=/opt/venv/bin:$PATH \
    PORT=8084 \
    PYTHONUNBUFFERED=1 \
    IMAGES_OUTPUT_DIR=/tmp/outputs

# The image default (65532), stated explicitly so a base-image change cannot
# silently make the service run as root.
USER 65532

EXPOSE 8084
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "900", "main:app"]
