# MBM Book Node.js Kernel (JavaScript + TypeScript)

FROM node:20-bookworm-slim

RUN npm install -g \
    tsx typescript ts-node \
    @types/node \
    lodash mathjs d3 \
    express axios \
    sharp jimp

WORKDIR /workspace
CMD ["node"]
