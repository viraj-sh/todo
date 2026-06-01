FROM node:24 AS builder

WORKDIR /app

COPY package*.json .

RUN npm install --verbose

COPY . .

RUN npm run build

FROM nginx:1.30-alpine 

WORKDIR /app

ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80