# Base Image
FROM eclipse-temurin:23.0.2_7-jre

# Set up environment
RUN apt-get update && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip python3-tk git && \
    rm -rf /var/lib/apt/lists/*

# Clone and install submg
RUN git clone https://github.com/ttubb/submg /app
WORKDIR /app
RUN python3 -m pip install . --break-system-packages

# download webin-cli
RUN submg-cli download-webin
