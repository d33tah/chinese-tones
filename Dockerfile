FROM golang as build
RUN mkdir /src
WORKDIR /src
ADD ./main.go .
ADD ./go.mod .
# http://blog.wrouesnel.com/articles/Totally%20static%20Go%20builds/
RUN CGO_ENABLED=0 GOOS=linux go build -a -ldflags '-extldflags "-static"' .
FROM scratch
COPY --from=build /src/chinese-tones /
COPY templates /templates
COPY sounds /sounds
ENTRYPOINT ["/chinese-tones"]
