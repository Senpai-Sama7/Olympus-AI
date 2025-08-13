# Enterprise Application Deployment Guide

## 🚀 Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- Domain name configured
- SSL certificates (Let's Encrypt recommended)
- MongoDB backup strategy
- Monitoring solution (optional)

### Environment Configuration

1. **Create production environment file**:

```bash
cp .env.example .env.production
```

2. **Update critical production values**:

```env
NODE_ENV=production
JWT_SECRET=<generate-secure-64-char-random-string>
MONGODB_URI=mongodb://username:password@mongodb:27017/enterprise-app?authSource=admin
FRONTEND_URL=https://yourdomain.com
```

### Security Checklist

- [x] Change default MongoDB credentials
- [x] Generate secure JWT secret
- [x] Enable HTTPS/SSL
- [x] Configure firewall rules
- [x] Set up rate limiting
- [x] Enable CORS for specific domains
- [x] Implement backup strategy
- [x] Set up monitoring and alerts
- [x] Configure log rotation
- [x] Enable security headers

### Docker Production Setup

1. **Build images**:

```bash
docker-compose -f docker-compose.yml build --no-cache
```

2. **Start services**:

```bash
docker-compose -f docker-compose.yml up -d
```

3. **Check logs**:

```bash
docker-compose logs -f
```

### MongoDB Security

1. **Create admin user**:

```javascript
use admin
db.createUser({
  user: "admin",
  pwd: "secure-password",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})
```

2. **Create application user**:

```javascript
use enterprise-app
db.createUser({
  user: "appuser",
  pwd: "secure-password",
  roles: [ { role: "readWrite", db: "enterprise-app" } ]
})
```

### SSL/HTTPS Configuration

1. **Using Let's Encrypt with nginx**:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://client:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://server:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Backup Strategy

1. **Automated MongoDB backups**:

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
docker exec mongodb mongodump --out /backup/$DATE
docker cp mongodb:/backup/$DATE ./backups/
find ./backups -type d -mtime +7 -exec rm -rf {} \;
```

2. **Schedule with cron**:

```cron
0 2 * * * /path/to/backup.sh
```

### Monitoring

1. **Health check endpoints**:

- Server: `https://yourdomain.com/api/health`
- Database: Monitor MongoDB metrics

2. **Recommended monitoring tools**:

- Prometheus + Grafana
- New Relic
- Datadog
- Sentry for error tracking

### Performance Optimization

1. **Enable Redis caching**:

```env
REDIS_URL=redis://redis:6379
```

2. **CDN for static assets**:

- CloudFlare
- AWS CloudFront
- Fastly

3. **Database indexes** (already configured):

- User.email (unique)
- Product.name + Product.category (compound)
- Product.owner

### Scaling Strategies

1. **Horizontal scaling**:

```yaml
# docker-compose.scale.yml
services:
  server:
    deploy:
      replicas: 3
```

2. **Load balancing**:

- nginx upstream configuration
- HAProxy
- AWS ELB/ALB

### Troubleshooting

1. **Check container status**:

```bash
docker-compose ps
```

2. **View logs**:

```bash
docker-compose logs -f server
docker-compose logs -f client
docker-compose logs -f mongodb
```

3. **Access container shell**:

```bash
docker exec -it server sh
```

4. **Common issues**:

- Port conflicts: Change exposed ports in docker-compose.yml
- Memory issues: Increase Docker memory allocation
- Connection refused: Check firewall and security groups

### Maintenance

1. **Update dependencies**:

```bash
cd server && npm update
cd ../client && npm update
```

2. **Database migrations**:

```bash
docker exec -it server npm run migrate
```

3. **Clear cache**:

```bash
docker exec -it server npm run cache:clear
```

## 🔒 Security Best Practices

1. **Regular updates**: Keep all dependencies updated
2. **Audit logs**: Monitor access and error logs
3. **Penetration testing**: Regular security audits
4. **Incident response**: Have a plan ready
5. **Data encryption**: Encrypt sensitive data at rest
6. **API rate limiting**: Prevent abuse
7. **Input validation**: Never trust user input
8. **OWASP compliance**: Follow security guidelines

## 📊 Performance Monitoring

Key metrics to track:

- Response time (< 200ms target)
- Error rate (< 1% target)
- Database query time
- Cache hit rate
- CPU and memory usage
- Active user sessions

## 🎯 Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL certificates installed
- [ ] Database backups scheduled
- [ ] Monitoring configured
- [ ] Security headers enabled
- [ ] Rate limiting configured
- [ ] Error tracking setup
- [ ] Load testing completed
- [ ] Rollback plan documented
- [ ] Team access configured
