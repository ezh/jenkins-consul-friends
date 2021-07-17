# builder
FROM golang:1.16-alpine AS builder

COPY go/jenkins-consul-friends /src

WORKDIR /src/cmd

RUN CGO_ENABLED=0 GOOS=linux go build -o /jenkins-consul-friends .

FROM scratch

USER 4357

WORKDIR /

COPY --from=builder /jenkins-consul-friends /

CMD ["/jenkins-consul-friends"]