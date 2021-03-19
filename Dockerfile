FROM python:3-slim-buster AS builder

# Installing nodejs, npm and gulp
RUN apt-get update \
 && apt-get install -yq --no-install-recommends nodejs npm \
 && npm install --global gulp-cli

# Build app
COPY . /app/monitorrent
WORKDIR /app/monitorrent
RUN npm install \
 && gulp dist

# Runtime image
FROM python:3-slim-buster

WORKDIR /var/www/monitorrent
COPY --from=builder /app/monitorrent .

RUN pip install --no-cache-dir -r /var/www/monitorrent/requirements.txt

EXPOSE 6687

CMD ["python3", "server.py"]