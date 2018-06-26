FROM alpine:3.7

ARG TNL_VERSION

RUN apk add --no-cache python3

RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    rm -rf .cache get-pip.py

RUN test -n "${TNL_VERSION}"
RUN pip install tcpnetlock==${TNL_VERSION} && \
    rm -rf .cache

EXPOSE 7654

CMD ["tcpnetlock_server", "--info", "--listen", "0.0.0.0", "--port", "7654"]
