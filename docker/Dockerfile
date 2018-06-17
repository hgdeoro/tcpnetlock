FROM alpine:3.7

RUN apk add --no-cache python3

RUN wget https://bootstrap.pypa.io/get-pip.py -O get-pip.py && \
    python3 get-pip.py && \
    pip install tcpnetlock && \
    rm -rf .cache get-pip.py

EXPOSE 7654

CMD ["tcpnetlock_server", "--listen", "0.0.0.0", "--port", "7654"]
