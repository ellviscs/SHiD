FROM python:3.14
WORKDIR /usr/local/discordbot

LABEL authors="EllvisCS"

COPY requirement.txt ./
RUN pip install -r requirement.txt

COPY *.py ./
COPY cogs ./cogs

RUN useradd discordbot
USER discordbot

CMD ["python", "main.py"]