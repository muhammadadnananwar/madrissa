#!/bin/sh
# Writes the nginx config at container start:
#   PORT         port to listen on (Railway sets it; default 80)
#   BACKEND_URL  optional — if set (docker compose: http://api:8000), /api and /media are proxied to Django,
#                so the site can be built with VITE_API_URL=/api/site. On Railway leave it unset and build with
#                VITE_API_URL=https://<backend-domain>/api/site instead.
set -e
PROXY=""
if [ -n "$BACKEND_URL" ]; then
  PROXY="
  location /api/   { proxy_pass ${BACKEND_URL}; proxy_set_header Host \$http_host; proxy_set_header X-Forwarded-Proto \$scheme; }
  location /media/ { proxy_pass ${BACKEND_URL}; proxy_set_header Host \$http_host; }"
fi
cat > /etc/nginx/conf.d/default.conf <<CONF
server {
  listen ${PORT:-80};
  listen [::]:${PORT:-80};
  root /usr/share/nginx/html;
  client_max_body_size 40m;
${PROXY}
  location /assets/ { expires 1y; add_header Cache-Control "public, immutable"; }
  # Single-page app: every other path renders index.html
  location / { try_files \$uri /index.html; }
}
CONF
exec nginx -g 'daemon off;'
