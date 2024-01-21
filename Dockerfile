FROM python:alpine3.19

RUN apk add --no-cache lirc
RUN sed -i 's/devinput/default/' /usr/etc/lirc/lirc_options.conf

COPY entrypoint.sh /

ENTRYPOINT ["/entrypoint.sh"]
