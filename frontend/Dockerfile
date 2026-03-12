FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./

# --legacy-peer-deps bypasses the eslint peer conflict (dev deps only, safe for build)
RUN npm ci --legacy-peer-deps

COPY . .
RUN npm run build


FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=builder /app/dist /usr/share/nginx/html
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]