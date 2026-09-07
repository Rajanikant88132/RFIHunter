# ── Build stage ─────────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

ARG REACT_APP_API_URL=http://localhost:4000/api
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Install deps in a separate layer so Docker cache is reused when only src changes
COPY package.json ./
RUN npm install --prefer-offline 2>/dev/null || npm install

COPY public/ ./public/
COPY src/    ./src/

RUN npm run build

# ── Production stage ─────────────────────────────────────────────────
FROM nginx:alpine

COPY --from=build /app/build /usr/share/nginx/html

# SPA routing — rewrite unknown paths to index.html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
