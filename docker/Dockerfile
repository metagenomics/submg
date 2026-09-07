# Base Image
FROM ruby:4.0.6 AS aspera

RUN gem install aspera-cli --no-document && \
    ascli conf ascp install && \
    ascli conf ascp info

FROM eclipse-temurin:21-jre

# Set up environment
RUN apt-get update && \
    apt-get upgrade -y
RUN apt-get install -y python3 python3-pip python3-tk && \
    rm -rf /var/lib/apt/lists/*

# Install Aspera
COPY --from=aspera /root/.aspera/sdk /opt/aspera
ENV PATH="/opt/aspera:${PATH}"
RUN ascp -A

# Copy and install submg
COPY . /app
WORKDIR /app
RUN python3 -m pip install . --break-system-packages

# download webin-cli
RUN submg-cli download-webin
