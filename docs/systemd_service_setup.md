# CAsMan Web Production Server - systemd Service Setup

This guide will help you set up CAsMan web server as a systemd service that:
- Starts automatically on boot
- Restarts automatically on failure
- Runs in its own virtual environment
- Runs in production mode

## Prerequisites

- Linux system with systemd (Ubuntu, Debian, RHEL, CentOS, etc.)
- Root or sudo access
- CAsMan installed in a dedicated directory (e.g., `/opt/casman` or `/home/casman/CAsMan`)

## Step 1: Choose Installation Directory

Decide where CAsMan will be installed. Common options:
- `/opt/casman` (system-wide, recommended)
- `/home/casman/CAsMan` (user directory)

For this guide, we'll use `/opt/casman`.

## Step 2: Install CAsMan

```bash
# Create installation directory
sudo mkdir -p /opt/casman
sudo chown $USER:$USER /opt/casman

# Clone or copy CAsMan to the directory
cd /opt/casman
git clone <your-repo-url> .
# OR copy your existing installation:
# cp -r /path/to/CAsMan/* /opt/casman/

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install CAsMan in editable mode
pip install -e .

# Deactivate
deactivate
```

## Step 3: Create a Dedicated System User (Optional but Recommended)

Running the service as a dedicated user improves security:

```bash
# Create a system user for casman (no login shell)
sudo useradd --system --no-create-home --shell /usr/sbin/nologin casman

# Give ownership of the installation directory
sudo chown -R casman:casman /opt/casman

# If using database directory, ensure it's writable
sudo chown -R casman:casman /opt/casman/database
```

## Step 4: Create systemd Service File

Create the service file at `/etc/systemd/system/casman-web.service`:

```bash
sudo nano /etc/systemd/system/casman-web.service
```

### If running as dedicated user (recommended):

```ini
[Unit]
Description=CAsMan Web Production Server
After=network.target
Documentation=https://github.com/Coherent-All-Sky-Monitor/CAsMan

[Service]
Type=simple
User=casman
Group=casman
WorkingDirectory=/opt/casman

# Use the virtual environment's Python
Environment="PATH=/opt/casman/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"

# Run casman web in production mode
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5000

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=200
StartLimitBurst=5

# Resource limits (optional)
LimitNOFILE=4096

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=casman-web

[Install]
WantedBy=multi-user.target
```

### If running as your own user:

Replace `User=casman` and `Group=casman` with your username, and adjust the `WorkingDirectory` path.

## Step 5: Configure Service Options

You can customize the service by modifying the `ExecStart` line:

```bash
# Default (both scanner and visualization)
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5000

# Scanner only
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5000 --scanner-only

# Visualization only
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5000 --visualize-only

# Custom host and port
ExecStart=/opt/casman/.venv/bin/casman web --production --host 0.0.0.0 --port 8080
```

## Step 6: Reload systemd and Enable Service

```bash
# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable casman-web.service

# Start the service now
sudo systemctl start casman-web.service

# Check service status
sudo systemctl status casman-web.service
```

## Step 7: Verify Service is Running

```bash
# Check status
sudo systemctl status casman-web.service

# View logs (live)
sudo journalctl -u casman-web.service -f

# View recent logs
sudo journalctl -u casman-web.service -n 100

# Check if web server is responding
curl http://localhost:5000
```

## Managing the Service

### Start/Stop/Restart
```bash
# Start the service
sudo systemctl start casman-web.service

# Stop the service
sudo systemctl stop casman-web.service

# Restart the service
sudo systemctl restart casman-web.service

# Reload service configuration (after editing service file)
sudo systemctl daemon-reload
sudo systemctl restart casman-web.service
```

### View Logs
```bash
# Follow logs in real-time
sudo journalctl -u casman-web.service -f

# View logs since boot
sudo journalctl -u casman-web.service -b

# View logs from last hour
sudo journalctl -u casman-web.service --since "1 hour ago"

# View logs with priority (errors only)
sudo journalctl -u casman-web.service -p err
```

### Check Service Status
```bash
# Full status
sudo systemctl status casman-web.service

# Is it running?
sudo systemctl is-active casman-web.service

# Is it enabled for boot?
sudo systemctl is-enabled casman-web.service
```

## Advanced Configuration

### Environment Variables

If you need to set environment variables, add them to the service file:

```ini
[Service]
Environment="PATH=/opt/casman/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="CASMAN_DB_DIR=/var/lib/casman/database"
Environment="FLASK_ENV=production"
```

Or use an environment file:

```ini
[Service]
EnvironmentFile=/opt/casman/.env
```

Then create `/opt/casman/.env`:
```bash
CASMAN_DB_DIR=/var/lib/casman/database
FLASK_ENV=production
```

### Firewall Configuration

If using a firewall, open the port:

```bash
# For ufw (Ubuntu/Debian)
sudo ufw allow 5000/tcp

# For firewalld (RHEL/CentOS)
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Reverse Proxy with Nginx (Optional)

For production, you may want to use Nginx as a reverse proxy:

1. Install Nginx:
```bash
sudo apt install nginx  # Ubuntu/Debian
sudo yum install nginx  # RHEL/CentOS
```

2. Create Nginx configuration at `/etc/nginx/sites-available/casman`:

```nginx
server {
    listen 80;
    server_name your-server-name.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

3. Enable the configuration:
```bash
sudo ln -s /etc/nginx/sites-available/casman /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Running Multiple Instances

To run multiple instances (e.g., scanner on one port, visualization on another):

1. Create separate service files:
   - `/etc/systemd/system/casman-scanner.service`
   - `/etc/systemd/system/casman-visualize.service`

2. Use different ports and options for each:

**casman-scanner.service:**
```ini
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5000 --scanner-only
```

**casman-visualize.service:**
```ini
ExecStart=/opt/casman/.venv/bin/casman web --production --port 5001 --visualize-only
```

## Troubleshooting

### Service won't start
```bash
# Check detailed status
sudo systemctl status casman-web.service

# View full logs
sudo journalctl -u casman-web.service -xe

# Check if port is already in use
sudo netstat -tlnp | grep 5000

# Verify virtual environment and executable
ls -la /opt/casman/.venv/bin/casman
```

### Service keeps restarting
```bash
# View recent crash logs
sudo journalctl -u casman-web.service -n 200

# Check file permissions
ls -la /opt/casman
ls -la /opt/casman/database

# Test running manually
sudo -u casman /opt/casman/.venv/bin/casman web --production --port 5000
```

### Permission errors
```bash
# Ensure ownership is correct
sudo chown -R casman:casman /opt/casman
sudo chown -R casman:casman /opt/casman/database

# Check SELinux (if applicable)
sudo setenforce 0  # Temporarily disable to test
```

### Database errors
```bash
# Ensure database files are writable
chmod 644 /opt/casman/database/*.db
chown casman:casman /opt/casman/database/*.db

# Check database integrity
sqlite3 /opt/casman/database/parts.db "PRAGMA integrity_check;"
```

## Updating CAsMan

When updating CAsMan:

```bash
# Stop the service
sudo systemctl stop casman-web.service

# Update the code
cd /opt/casman
sudo -u casman git pull  # Or copy new files

# Update dependencies
sudo -u casman /opt/casman/.venv/bin/pip install -e .

# Restart the service
sudo systemctl start casman-web.service

# Verify it's running
sudo systemctl status casman-web.service
```

## Uninstalling

To remove the service:

```bash
# Stop and disable the service
sudo systemctl stop casman-web.service
sudo systemctl disable casman-web.service

# Remove service file
sudo rm /etc/systemd/system/casman-web.service

# Reload systemd
sudo systemctl daemon-reload

# Optionally remove installation directory
sudo rm -rf /opt/casman

# Optionally remove user
sudo userdel casman
```

## Quick Reference

```bash
# Start service
sudo systemctl start casman-web

# Stop service
sudo systemctl stop casman-web

# Restart service
sudo systemctl restart casman-web

# View status
sudo systemctl status casman-web

# View logs
sudo journalctl -u casman-web -f

# Enable on boot
sudo systemctl enable casman-web

# Disable on boot
sudo systemctl disable casman-web
```

## Security Recommendations

1. **Run as dedicated user**: Don't run as root
2. **Use firewall**: Restrict access to necessary ports
3. **Use reverse proxy**: Put Nginx in front for better security
4. **Enable HTTPS**: Use Let's Encrypt with Nginx
5. **Restrict file permissions**: `chmod 640` for sensitive files
6. **Regular backups**: Backup database files regularly
7. **Monitor logs**: Set up log rotation and monitoring
