FROM ubuntu:latest

RUN apt-get update && apt-get install -y --no-install-recommends software-properties-common tar bzip2
RUN add-apt-repository ppa:deadsnakes/ppa -y && apt-get update && apt-get install -y --no-install-recommends python3.6 python3-setuptools && easy_install3 pip && pip3 install pybars3 pyyaml
COPY ./matiec /app/matiec

#GCC
WORKDIR /opt
ADD https://developer.arm.com/-/media/Files/downloads/gnu-rm/7-2017q4/gcc-arm-none-eabi-7-2017-q4-major-linux.tar.bz2?revision=375265d4-e9b5-41c8-bf23-56cbe927e156?product=GNU%20Arm%20Embedded%20Toolchain,64-bit,,Linux,7-2017-q4-major /opt
RUN tar xjf ./gcc-arm-none-eabi-7-2017-q4-major-linux.tar.bz2 && rm ./gcc-arm-none-eabi-7-2017-q4-major-linux.tar.bz2 && chmod -R -w /opt/gcc-arm-none-eabi-7-2017-q4-major

ENV PATH="${PATH}:/opt/gcc-arm-none-eabi-7-2017-q4-major/bin"

WORKDIR /app
ADD ./configdefs.json /app/configdefs.json
ADD ./targethardware.json /app/targethardware.json
ADD ./*.py /app/
ADD ./template/ /app/template/

RUN chmod a+x *.py

ENTRYPOINT ["python3", "./main.py", "--iec2c", "./matiec", "--source", "/src", "--target", "/files/out", "--config", "/files/.pilotfwconfig.json"]