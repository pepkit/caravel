FROM python:3.6.8
MAINTAINER "michal@virginia.edu"

RUN apt-get update -y
RUN apt-get install -y python-pip python-dev build-essential
COPY . /app
RUN pip install -U pip
# install caravel deps
RUN pip install -r /app/caravel/requirements/requirements-all.txt
# install peppy dev
RUN pip install https://github.com/pepkit/peppy/archive/dev.zip
# install looper dev
RUN pip install https://github.com/pepkit/looper/archive/dev.zip

# Install samtools and pypier, used in the example pipeline
RUN pip install piper
WORKDIR /home/src/
RUN wget https://github.com/samtools/samtools/releases/download/1.7/samtools-1.7.tar.bz2 && \
    tar xf samtools-1.7.tar.bz2 && \
    cd /home/src/samtools-1.7 && \
    ./configure && \
    make && \
    make install && \
    ln -s /home/src/samtools-1.7/samtools /usr/bin/
# install caravel
WORKDIR /app
RUN pip install .

# then run with caravel --demo, like:
# docker build -t caravel_demo .
# docker run -p 5000:5000 caravel_demo caravel --demo