# MBM Book C/C++ Kernel

FROM gcc:13-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    cmake make gdb valgrind \
    libboost-all-dev libopencv-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace
CMD ["bash"]
