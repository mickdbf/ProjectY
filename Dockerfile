FROM ubuntu:latest
LABEL authors="mickd"

ENTRYPOINT ["top", "-b"]