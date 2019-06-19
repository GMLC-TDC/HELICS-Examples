FROM ubuntu:18.04 as builder

RUN apt update && apt install -y \
  libboost-dev \
  libboost-test-dev \
  libzmq3-dev python3-dev \
  build-essential swig cmake git

WORKDIR /root/develop

RUN git clone --single-branch -b v2.1.0 https://github.com/GMLC-TDC/HELICS.git helics

WORKDIR /root/develop/helics/build

RUN cmake \
  -DBUILD_PYTHON_INTERFACE=ON \
  -DBUILD_CXX_SHARED_LIB=ON \
  -DPYTHON_INCLUDE_DIR=/usr/include/python3.6/ \
  -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.6m.so \
  -DCMAKE_INSTALL_PREFIX=/helics \
  ..
RUN make -j8 install

FROM ubuntu:18.04

RUN apt update && apt install -y --no-install-recommends \
  libboost-test1.65.1 libzmq5 \
  iproute2 net-tools

COPY --from=builder /helics /usr/local/

ENV PYTHONPATH /usr/local/python

# Python must be installed after the PYTHONPATH is set above for it to
# recognize and import libhelicsSharedLib.so.
RUN apt install -y --no-install-recommends python3-dev \
  && rm -rf /var/lib/apt/lists/*

CMD ["python3", "-c", "import helics; print(helics.helicsGetVersion())"]
