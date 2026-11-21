# Public website: static React build served by nginx.
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
# Baked into the build (Railway passes service variables as build args)
ARG VITE_API_URL=/api/site
ARG VITE_PORTAL_URL=http://localhost:4322
ENV VITE_API_URL=$VITE_API_URL VITE_PORTAL_URL=$VITE_PORTAL_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.sh /nginx.sh
COPY --from=build /app/dist /usr/share/nginx/html
ENV PORT=80
EXPOSE 80
CMD ["/nginx.sh"]
