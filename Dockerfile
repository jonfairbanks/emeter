FROM python:3-alpine

# Setup venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Run the app
WORKDIR /usr/src/app
COPY ./main.py .
CMD ["python", "main.py"]
