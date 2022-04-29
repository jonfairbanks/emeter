FROM python:3.9-alpine

RUN pip install --upgrade pip
RUN pip install pipenv

RUN apk add --no-cache tini

RUN adduser -D python
RUN mkdir /home/python/app/ && chown -R python:python /home/python/app
WORKDIR /home/python/app

ENTRYPOINT ["/sbin/tini", "--"]

USER python

RUN pip install --user pipenv

ENV PATH="/home/python/.local/bin:${PATH}"

COPY --chown=python:python Pipfile Pipfile
RUN pipenv lock -r > requirements.txt
RUN pip install --user -r requirements.txt

COPY --chown=python:python . .

CMD ["python", "-u", "main.py"]