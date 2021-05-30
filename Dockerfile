FROM node:10-buster-slim AS builder

# # Installing nodejs, npm and gulp
# RUN echo "deb http://deb.debian.org/debian buster-backports main" > /etc/apt/sources.list.d/buster-backports.list \
#  && apt-get update \
#  && apt-get install -yq --no-install-recommends nodejs npm \
#  && npm install --global gulp-cli

RUN npm install -g npm@7.14.0 \
 && npm install --global gulp-cli

WORKDIR /app/monitorrent

# Install packages
COPY package.json /app/monitorrent
RUN npm install

# Build app
COPY . /app/monitorrent
RUN gulp dist


# Runtime image
FROM python:3-slim-buster

WORKDIR /var/www/monitorrent

# Install packages
COPY requirements.txt /var/www/monitorrent/
RUN pip install --no-cache-dir -r /var/www/monitorrent/requirements.txt

# Install runtime files
COPY --from=builder /app/monitorrent .

EXPOSE 6687

CMD ["python3", "server.py"]