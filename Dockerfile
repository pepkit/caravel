FROM python:3.6.8
MAINTAINER "michal@virginia.edu"

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /app
RUN pip install -U pip
# install pypiper, used in the example pipeline
RUN pip install piper
# install R, used in the demo pipeline
RUN apt-get --assume-yes install r-base r-base-dev
# install caravel
WORKDIR /app
RUN pip install .

ENV PATH="${PATH}:/usr/bin/Rscript"
CMD ["/bin/bash"]
# then run with caravel --demo, like:
# docker build -t caravel_demo .
# docker run -p 5000:5000 caravel_demo caravel --demo