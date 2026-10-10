FROM python:3.14
WORKDIR /usr/local/discordbot

LABEL authors="EllvisCS"

COPY requirement.txt ./
RUN pip install -r requirement.txt

COPY *.py ./
COPY cogs/music.py ./cogs/music.py

RUN useradd discordbot
USER discordbot

CMD ["python", "-u", "main.py"]