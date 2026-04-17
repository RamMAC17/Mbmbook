# MBM Book R Kernel

FROM r-base:4.3.2

RUN R -e "install.packages(c('IRkernel', 'tidyverse', 'ggplot2', 'dplyr', 'caret', 'shiny'), repos='https://cran.r-project.org')"

WORKDIR /workspace
CMD ["R", "--no-save"]
