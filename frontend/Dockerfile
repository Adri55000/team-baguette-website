# Base commune : installation des dépendances
FROM node:24-bookworm-slim AS base

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
FROM nginx:stable-alpine AS production

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
