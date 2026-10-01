# <b>SHiD</b>
## Self Hosted Discord Bot
This bot can play music, set honeypot and simple chatbot

## How to Run
Simply make a docker compose file like ``docker-compose.yml`` like this: <br>
````
services:
  discordbot:
    image: ellviscs/discordbot:v0.1.0-alpha.1
    container_name: discordbot
    network_mode: "host"
    env_file:
      - .env
    restart: unless-stopped
    depends_on:
      lavalink:
        condition: service_started

  lavalink:
    container_name: lavalink
    image: ghcr.io/lavalink-devs/lavalink:4-alpine
    restart: unless-stopped
    volumes:
      - ./application.yml:/opt/Lavalink/application.yml
      - ./plugins/:/opt/Lavalink/plugins/
    network_mode: "host"
    ports:
      # if the network mode is host, i suggest to only bind localhost
      - "127.0.0.1:2333:2333" 
````

make sure to make ``.env`` file. The example is in ``.env.example`` 
