# MBM Book Rust Kernel

FROM rust:1.77-bookworm

# Install evcxr (Rust Jupyter kernel / REPL)
RUN cargo install evcxr_repl || true

WORKDIR /workspace
CMD ["bash"]
