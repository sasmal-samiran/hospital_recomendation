# ==============================================================================
# Frontend Service Dockerfile - Nginx Alpine
# ==============================================================================
FROM nginx:alpine

# Clean out default Nginx HTML content
RUN rm -rf /usr/share/nginx/html/*

# Copy custom Nginx configuration with reverse proxy support
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static frontend application assets
COPY index.html /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

# Expose Nginx HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/ || exit 1

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
