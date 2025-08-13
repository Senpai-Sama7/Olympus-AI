FROM node:20-slim
WORKDIR /app
COPY workflows/ingest/package.json workflows/ingest/tsconfig.json ./
RUN npm install
COPY workflows/ingest/src ./src
EXPOSE 7233
CMD ["npm", "run", "start"]
