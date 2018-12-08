# Pull base image
FROM python:3.6

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create and set work directory
RUN mkdir /code
WORKDIR /code

# Install Unzip
RUN apt-get update
RUN apt-get install unzip

# Install dependencies
RUN pip3 install pipenv
COPY ./Pipfile /code/Pipfile
RUN pipenv install --deploy --system --skip-lock --dev

# Copy project
COPY . /code/

RUN export PYTHONPATH=.

CMD scripts/send_email_update.sh