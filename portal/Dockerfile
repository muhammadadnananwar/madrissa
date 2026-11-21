FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Baked into the build (Railway passes service variables as build args)
ARG PUBLIC_API_URL
ARG PUBLIC_WEBSITE_URL
RUN npm run build

FROM node:22-alpine
WORKDIR /app
ENV HOST=0.0.0.0 PORT=4322
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
EXPOSE 4322
CMD ["node", "./dist/server/entry.mjs"]
