# Base Image
FROM openjdk:slim

# Set up environment
RUN apt-get update && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip git && \
    rm -rf /var/lib/apt/lists/*
RUN python3 -m pip install --upgrade pip wheel

# Clone and install submg
RUN git clone https://github.com/ttubb/submg /app
WORKDIR /app
RUN python3 -m pip install .

# download webin-cli
RUN submg-cli download_webin