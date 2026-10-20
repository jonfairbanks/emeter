FROM python:3.13-alpine AS dependencies

RUN apk add --no-cache build-base cargo libffi-dev openssl-dev pkgconf
RUN pip install --no-cache-dir pipenv

WORKDIR /build
COPY Pipfile* .
RUN pipenv requirements > requirements.txt \
    && pip install --no-cache-dir --ignore-installed --prefix=/install -r requirements.txt

FROM python:3.13-alpine

RUN apk add --no-cache tini libffi libgcc openssl \
    && adduser -D python

COPY --from=dependencies /install /usr/local
WORKDIR /home/python/app
COPY --chown=python:python . .

USER python
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["python", "-u", "main.py"]
