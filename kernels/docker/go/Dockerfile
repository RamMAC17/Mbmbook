# MBM Book Go Kernel

FROM golang:1.22-bookworm

RUN go install github.com/gopherdata/gophernotes@latest || true

WORKDIR /workspace
CMD ["go", "version"]
