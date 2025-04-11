FROM python:3.10

COPY / /bot/

WORKDIR /bot

RUN apt-get update && apt-get upgrade -y \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/opt/venv

RUN python3 -m venv $VIRTUAL_ENV

ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN pip install -U pip

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
