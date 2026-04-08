# Stage 1: Base image with apt packages
FROM ghcr.io/linuxserver/baseimage-kasmvnc:debianbookworm AS base

ENV TITLE=MetaTrader
ENV WINEARCH=win64
ENV WINEPREFIX=/config/.wine
ENV DISPLAY=:0
ENV DEBIAN_FRONTEND=noninteractive

# Ensure the directory exists with correct permissions
RUN mkdir -p /config/.wine /etc/apt/keyrings && \
    chown -R abc:abc /config/.wine && \
    chmod -R 755 /config/.wine

# Install required packages and WineHQ from the current Debian release.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        dos2unix \
        gnupg \
        netcat-openbsd \
        python3-pip \
        python3-pyxdg \
        wget \
    && wget -qO- https://dl.winehq.org/wine-builds/winehq.key | gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key \
    && echo 'deb [signed-by=/etc/apt/keyrings/winehq-archive.key] https://dl.winehq.org/wine-builds/debian/ bookworm main' > /etc/apt/sources.list.d/winehq.list \
    && dpkg --add-architecture i386 \
    && apt-get update \
    && apt-get install -y --install-recommends winehq-staging \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Final image
FROM base

# Copy the scripts directory and convert start.sh to Unix format
COPY app /app
COPY scripts /scripts
RUN dos2unix /scripts/*.sh && \
    chmod +x /scripts/*.sh

COPY /root /
RUN touch /var/log/mt5_setup.log && \
    chown abc:abc /var/log/mt5_setup.log && \
    chmod 644 /var/log/mt5_setup.log

EXPOSE 3000 5000 5001 8001 18812
VOLUME /config
