FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --omit=dev

COPY README.md server.json ./
COPY src ./src
COPY docs ./docs
COPY examples ./examples
COPY scripts ./scripts

CMD ["node", "src/server.js"]
