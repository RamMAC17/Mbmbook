# MBM Book Julia Kernel

FROM julia:1.10

RUN julia -e 'using Pkg; Pkg.add(["IJulia", "Plots", "DataFrames", "CSV", "Flux", "DifferentialEquations"])'

WORKDIR /workspace
CMD ["julia"]
