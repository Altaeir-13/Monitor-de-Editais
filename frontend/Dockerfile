# Estágio de Build (Builder)
FROM node:22-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Passa VITE_API_URL como relativo para utilizar o proxy reverso do Nginx
ENV VITE_API_URL=/api
RUN npm run build

# Estágio de Execução (Runner)
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
