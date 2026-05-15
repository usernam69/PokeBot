# Keep PokeBot Running 24/7 on Cloud Server

## Option A: DigitalOcean Droplet (Recommended - $6/month)

### 1. Create Droplet
- Go to [digitalocean.com](https://digitalocean.com)
- Click "Create" → "Droplet"
- Choose: Ubuntu 24.04 LTS, Basic ($6/month), smallest tier
- Add SSH key (easier than password)
- Create droplet, wait 1-2 min

### 2. SSH Into Server
```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Install Python & Dependencies
```bash
apt update
apt install -y python3 python3-pip git
pip install poke-env aiohttp
```

### 4. Clone Your PokeBot
```bash
cd /root
git clone https://github.com/YOUR_USERNAME/PokeBot.git
cd PokeBot
```

OR if no git repo:
```bash
mkdir /root/PokeBot
cd /root/PokeBot
# Upload smartbot.py via sftp or nano
```

### 5. Run Bot in Background (with logging)
```bash
nohup python3 smartbot.py > bot.log 2>&1 &
```

Check if running:
```bash
ps aux | grep smartbot
tail bot.log
```

### 6. Auto-Restart if Bot Crashes (systemd)

Create service file:
```bash
cat > /etc/systemd/system/pokebot.service << EOF
[Unit]
Description=Pokemon Showdown Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/PokeBot
ExecStart=/usr/bin/python3 /root/PokeBot/smartbot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

Enable it:
```bash
systemctl enable pokebot
systemctl start pokebot
systemctl status pokebot
```

Check logs:
```bash
journalctl -u pokebot -f
```

---

## Option B: Docker (Better for Moving Hosts)

### 1. Create Dockerfile in PokeBot folder

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY smartbot.py .

CMD ["python", "smartbot.py"]
```

### 2. Create requirements.txt
```
poke-env>=1.0.0
aiohttp>=3.8.0
```

### 3. Build & Run Locally First
```bash
docker build -t pokebot .
docker run -d --name pokebot pokebot
docker logs -f pokebot
```

### 4. Deploy to Docker Host (Railway, etc)
- Push to GitHub
- Connect to Railway/Heroku/etc
- They auto-build & run 24/7

---

## Option C: Railway (Free-ish, ~$5 if you use it)

### 1. Push code to GitHub
```bash
cd ~/PokeBot
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/PokeBot.git
git push -u origin main
```

### 2. Go to [railway.app](https://railway.app)
- Sign in with GitHub
- New Project → Deploy from GitHub repo
- Select PokeBot repo
- Railway auto-detects Python
- Add `requirements.txt` (see above)
- Deploy!

Bot runs 24/7 on Railway servers

---

## Option D: Keep Local PC as Server (Bad Idea But Possible)

If you MUST use your PC:

### Windows:
```bash
# Run in background using Task Scheduler
# Create scheduled task to run smartbot.py at startup
# Or use: pythonw.exe smartbot.py (no console window)
```

### Mac/Linux:
```bash
# Add to crontab
crontab -e

# Add line:
@reboot /usr/bin/python3 /path/to/PokeBot/smartbot.py
```

⚠️ **Problem:** PC crashes/power loss = bot dead. Not reliable.

---

## Quick Comparison

| Option | Cost | Setup Time | Reliability |
|--------|------|-----------|-------------|
| DigitalOcean | $6/mo | 15 min | ⭐⭐⭐⭐⭐ |
| Railway | $0-5/mo | 10 min | ⭐⭐⭐⭐ |
| AWS Free | $0 (1 year) | 20 min | ⭐⭐⭐⭐⭐ |
| Local PC | $0 | 5 min | ⭐ (unreliable) |

---

## File Structure
```
PokeBot/
├── smartbot.py
├── requirements.txt
├── Dockerfile (if using Docker)
└── bot.log (created on server)
```

---

## Troubleshooting

**Bot not connecting:**
- Check username/password in smartbot.py
- Check internet on server: `ping google.com`
- Check logs: `journalctl -u pokebot -f`

**Bot running but not battling:**
- Check Showdown is not blocking IP
- Try different bot username
- Check bot permissions on Showdown

**High CPU/Memory:**
- Reduce `max_concurrent_battles` in code
- Limit `LADDER_GAMES` to smaller number

---

## Next Steps

1. Choose hosting (DigitalOcean recommended)
2. Deploy bot
3. `ssh` into server & run it
4. Monitor with `tail bot.log`
5. Sleep peacefully while bot climbs ladder 24/7! 🤖
