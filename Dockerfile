FROM python:3.12-alpine

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN apt-get install libgomp1
RUN --mount=type=cache,target=/root/.cache/pip pip install --upgrade -r /code/requirements.txt

COPY ./model.pkl .
COPY ./app /code/app
COPY ./version.txt .

CMD ["fastapi", "run", "app/main.py", "--port", "5000"]

# If running behind a proxy like Nginx or Traefik add --proxy-headers
# CMD ["fastapi", "run", "app/main.py", "--port", "80", "--proxy-headers"]