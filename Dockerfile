FROM ubuntu:18.04


RUN apt-get update && apt-get install -y curl

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

RUN python3 -m pip --no-cache-dir install --upgrade \
    pip \
    setuptools

RUN ln -s $(which python3) /usr/local/bin/python

RUN apt-get install libcurl4 openssl liblzma5
RUN mkdir -p /mongodb
RUN cd /mongodb
ADD https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1804-4.4.2.tgz mongodb-linux-x86_64-ubuntu1804-4.4.2.tgz
RUN tar -zxvf mongodb-linux-x86_64-ubuntu1804-4.4.2.tgz
RUN cp mongodb-linux-x86_64-ubuntu1804-4.4.2/bin/* /usr/local/bin/
RUN cd ..

ADD ./ /code/
WORKDIR /code
RUN mkdir -p /data

RUN find . -name 'requirements.txt' -print  -exec pip install -r {} \;

ENTRYPOINT [ "python", "main.py"]
