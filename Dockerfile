FROM homebrew/brew:latest

RUN brew update

RUN brew tap caffix/amass
RUN brew install amass

RUN brew install python@3.7
RUN brew unlink python@3.7
RUN brew link --force python@3.7

RUN pip3 install shodan
RUN pip3 install luigi

RUN brew install pipenv

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --system --deploy
#  --ignore-pipfile

ENV PYTHONPATH "${PYTHONPATH}:$(pwd)"

ENV TARGET tesla

COPY . /app
WORKDIR /app

USER root

CMD pipenv run luigi --local-scheduler --module recon.shodan ShodanQuery --target-file ${TARGET} && cat results.${TARGET}.json


# Docker build command: docker build -t pipeline .
# Docker run command: docker run -e TARGET=www.example.com pipeline
