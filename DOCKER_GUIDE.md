# Docker Setup for PokeBot - 24/7 Running

## What is Docker?
Container = isolated mini-computer with Python + bot. Easy to move between your PC, server, cloud, etc.

---

## Step 1: Install Docker

**Windows/Mac:**
- Download [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Install & restart computer

**Linux (Ubuntu):**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Logout & login
```

Check install:
```bash
docker --version
```

---

## Step 2: Your PokeBot Folder Structure

```
PokeBot/
├── smartbot.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── logs/  (created automatically)
```

---

## Step 3: Build Docker Image

In PokeBot folder:
```bash
docker build -t pokebot .
```

Wait for it to finish (downloads Python, installs dependencies)

Check image created:
```bash
docker images
```

You should see `pokebot` in list

---

## Step 4: Run Bot Locally (Test First!)

**Option A: Using docker-compose (EASIER):**
```bash
cd PokeBot
docker-compose up -d
```

Check if running:
```bash
docker-compose logs -f
```

Stop:
```bash
docker-compose down
```

**Option B: Using docker run (More manual):**
```bash
docker run -d --name pokebot pokebot
```

Check logs:
```bash
docker logs -f pokebot
```

Stop:
```bash
docker stop pokebot
docker rm pokebot
```

---

## Step 5: Deploy to Cloud (Railway)

### A. Push to GitHub

1. **Create GitHub repo** (github.com/new)
   - Name: `PokeBot`
   - Make it **Private** (keep bot credentials safe!)

2. **In PokeBot folder:**
```bash
git init
git add .
git commit -m "Initial PokeBot commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/PokeBot.git
git push -u origin main
```

### B. Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your **PokeBot** repo
6. Railway auto-detects Docker (sees Dockerfile)
7. Click "Deploy"
8. Wait ~2 min, bot runs 24/7 on Railway servers! ✅

Check logs in Railway dashboard:
- Deployments tab → click latest → View Logs

---

## Step 6: Common Commands

```bash
# Build image
docker build -t pokebot .

# Run container
docker run -d --name pokebot pokebot

# View running containers
docker ps

# View logs (realtime)
docker logs -f pokebot

# Stop container
docker stop pokebot

# Remove container
docker rm pokebot

# View image size
docker images pokebot

# Remove image
docker rmi pokebot
```

---

## Troubleshooting

**Bot not connecting to Showdown:**
```bash
docker logs pokebot
```
Check for errors in logs. Common issues:
- Wrong `BOT_USERNAME` or `BOT_PASSWORD` in smartbot.py
- Username already taken on Showdown

**Container keeps restarting:**
```bash
docker logs pokebot
```
See what error caused crash. Fix in smartbot.py, rebuild:
```bash
docker build -t pokebot .
docker-compose up -d
```

**High CPU/Memory:**
- Reduce `max_concurrent_battles` in smartbot.py
- Reduce `LADDER_GAMES` 
- Rebuild image & restart

**Want to update bot code:**
1. Edit smartbot.py
2. Rebuild: `docker build -t pokebot .`
3. Restart: `docker-compose down && docker-compose up -d`

---

## Benefits of Docker

✅ Same code runs on your PC, server, Railway, anywhere  
✅ No "works on my machine" problems  
✅ Easy to backup (just zip the folder)  
✅ Easy to move to different hosting  
✅ Can run multiple bots at once  
✅ Isolates bot from your system  

---

## File Changes Needed

**smartbot.py:**
- Update `BOT_USERNAME` and `BOT_PASSWORD` with real credentials

**requirements.txt:**
- Already has `poke-env` and `aiohttp` ✅

**Dockerfile:**
- Already configured ✅

**docker-compose.yml:**
- Already configured ✅

---

## Quick Start Checklist

- [ ] Install Docker
- [ ] Have smartbot.py, requirements.txt, Dockerfile, docker-compose.yml in PokeBot folder
- [ ] Run `docker build -t pokebot .`
- [ ] Test locally: `docker-compose up -d` then `docker logs -f`
- [ ] Push to GitHub
- [ ] Deploy on Railway
- [ ] Bot runs 24/7! 🎉

---

## Which Hosting is Best?

**Local (your PC):**
- Free ✅
- Dies when PC off ❌

**Railway:**
- Free tier (limited hours, ~$5/mo for unlimited)
- Super easy deployment
- Great for testing
- Recommended for beginners ✅

**DigitalOcean:**
- $6/month
- Full control
- More power
- Recommended if Railway not enough

**AWS:**
- Free 1st year
- Complex setup
- Overkill for bot

---

## Done! 🤖

Your bot is now:
- Containerized (Docker)
- Easy to deploy (Railway)
- Running 24/7
- Easy to update
- Easy to backup

Questions? Check Docker logs! 📋
