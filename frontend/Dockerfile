# Base commune : installation des dépendances
FROM node:24-bookworm-slim@sha256:c86ecead9e55a5210ac1727de38a4ca840bf03dcaf34dc9749addbf383b1920c AS base

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .


# Développement : serveur Vite avec hot reload
FROM base AS development

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]


# Compilation pour la production
FROM base AS build

RUN npm run build


# Production : serveur HTTP léger
FROM nginx:stable-alpine@sha256:0e52bd054126cdc040b1276c0af347aeb02a41b9cfe305d6094767ac30e97949 AS production


COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
