# Build
FROM rust:1.78-slim AS build
WORKDIR /app
COPY proto ./proto
COPY control-plane ./control-plane
WORKDIR /app/control-plane
RUN apt-get update && apt-get install -y pkg-config libssl-dev && rm -rf /var/lib/apt/lists/*
RUN cargo build --release

# Runtime
FROM debian:bookworm-slim
WORKDIR /app
COPY --from=build /app/control-plane/target/release/control-plane /usr/local/bin/control-plane
ENV RUST_LOG=info
EXPOSE 50051
ENTRYPOINT ["control-plane"]
