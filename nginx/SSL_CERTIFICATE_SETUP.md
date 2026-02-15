# SSL 证书配置指南

## 方案 1: Let's Encrypt 免费证书（推荐）

### 安装 Certbot

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install certbot python3-certbot-nginx
```

### 获取证书

```bash
# 单域名证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 通配符证书（需要 DNS 验证）
sudo certbot --nginx -d "*.yourdomain.com" --manual --preferred-challenges dns
```

### 自动续期

Certbot 会自动设置定时任务续期证书：

```bash
# 查看定时任务
sudo systemctl list-timers | grep certbot

# 手动测试续期
sudo certbot renew --dry-run
```

### Nginx 配置更新

Certbot 会自动更新 Nginx 配置，但需要手动重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 方案 2: 商业证书

### 购买证书

推荐提供商：
- DigiCert
- GlobalSign
- Comodo
- Let's Encrypt Enterprise

### 安装证书

将证书文件上传到服务器：

```bash
# 创建证书目录
sudo mkdir -p /etc/nginx/ssl

# 上传证书文件
# cert.pem - 证书文件
# key.pem - 私钥文件
# chain.pem - 中间证书（如有）
```

### 配置 Nginx

更新 nginx.conf 中的证书路径：

```nginx
ssl_certificate /etc/nginx/ssl/cert.pem;
ssl_certificate_key /etc/nginx/ssl/key.pem;
```

## 方案 3: 自签名证书（仅测试）

### 生成自签名证书

```bash
# 创建证书目录
mkdir -p /etc/nginx/ssl

# 生成私钥
openssl genrsa -out /etc/nginx/ssl/key.pem 2048

# 生成证书
openssl req -new -x509 -key /etc/nginx/ssl/key.pem -out /etc/nginx/ssl/cert.pem -days 365 \
    -subj "/C=CN/ST=State/L=City/O=Organization/CN=yourdomain.com"
```

## 证书验证

### 检查证书

```bash
# 检查证书信息
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# 检查证书有效期
openssl x509 -in /etc/nginx/ssl/cert.pem -noout -dates

# 测试 SSL 连接
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
```

### 在线测试

使用以下工具测试 SSL 配置：

- SSL Labs: https://www.ssllabs.com/ssltest/
- Qualys SSL Labs: https://www.ssllabs.com/ssltest/
- Let's Debug: https://letsdebug.net/

## 安全配置

### 推荐的 SSL 配置

```nginx
# 使用强加密套件
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;

# 启用 HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# 启用 OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
```

### 禁用不安全的协议和加密

```nginx
# 只使用 TLS 1.2 和 1.3
ssl_protocols TLSv1.2 TLSv1.3;

# 禁用弱加密
ssl_ciphers HIGH:!aNULL:!MD5:!3DES;
```

## 证书管理

### 定期检查

```bash
# 创建检查脚本
cat > /usr/local/bin/check-ssl.sh << 'EOF'
#!/bin/bash
EXPIRY_DAYS=30
CERT_FILE="/etc/nginx/ssl/cert.pem"

if [ -f "$CERT_FILE" ]; then
    EXPIRY_DATE=$(openssl x509 -in "$CERT_FILE" -noout -dates | grep notAfter | cut -d= -f2)
    EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
    CURRENT_EPOCH=$(date +%s)
    DAYS_LEFT=$(( ($EXPIRY_EPOCH - $CURRENT_EPOCH) / 86400 ))

    if [ $DAYS_LEFT -lt $EXPIRY_DAYS ]; then
        echo "警告：证书将在 $DAYS_LEFT 天后过期！"
        # 发送告警邮件或通知
    fi
fi
EOF

chmod +x /usr/local/bin/check-ssl.sh

# 添加到定时任务（每天检查）
echo "0 8 * * * /usr/local/bin/check-ssl.sh" | sudo tee -a /etc/crontab
```

### 自动续期

Let's Encrypt 证书会自动续期，但需要确保：

```bash
# 测试续期
sudo certbot renew --dry-run

# 如果测试成功，启用自动续期
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

## 故障排除

### 常见问题

1. **证书路径错误**
   ```bash
   # 检查证书文件是否存在
   ls -la /etc/nginx/ssl/
   
   # 检查文件权限
   sudo chmod 644 /etc/nginx/ssl/cert.pem
   sudo chmod 600 /etc/nginx/ssl/key.pem
   ```

2. **Nginx 配置错误**
   ```bash
   # 测试配置
   sudo nginx -t
   
   # 查看错误日志
   sudo tail -f /var/log/nginx/error.log
   ```

3. **证书链不完整**
   ```bash
   # 合并证书和中间证书
   cat cert.pem chain.pem > fullchain.pem
   ```

4. **端口被占用**
   ```bash
   # 检查 443 端口
   sudo netstat -tlnp | grep :443
   
   # 检查防火墙
   sudo ufw status
   sudo firewall-cmd --list-all
   ```

## 监控和告警

### SSL 证书监控

```bash
# 使用 Nagios/Icinga 监控证书
# 使用 Prometheus + Alertmanager 监控证书
# 使用 Uptime Robot 监控 HTTPS 可用性
```

### 告警配置

在 Alertmanager 中配置证书过期告警：

```yaml
groups:
  - name: ssl_certificates
    rules:
      - alert: SSLCertificateExpiringSoon
        expr: ssl_cert_days_remaining < 30
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate for {{ $labels.instance }} will expire in {{ $value }} days"
```

## 参考资料

- [Let's Encrypt 文档](https://letsencrypt.org/docs/)
- [Nginx SSL 配置](http://nginx.org/en/docs/http/configuring_https_servers/)
- [Mozilla SSL 配置生成器](https://ssl-config.mozilla.org/)
- [OWASP TLS 配置](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet)
