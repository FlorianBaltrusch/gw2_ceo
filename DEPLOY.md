# Deploying the Critical Effect Optimizer

Everything is prepared; you only fill in three concrete values wherever you
see them below:

| Placeholder       | Meaning                                        |
|-------------------|------------------------------------------------|
| `ceo.example.com` | your domain (or a subdomain of it)             |
| `/opt/gw2_ceo`    | where the repository lives on the server       |
| `deploy`          | the linux user that runs the app               |

The commands assume a Debian/Ubuntu server; adjust the package manager
otherwise.

## 1. DNS

At your domain provider, create an **A record** pointing `ceo.example.com`
to the server's public IP (add an AAAA record too if the server has IPv6).
DNS must resolve before Caddy can fetch the HTTPS certificate.

## 2. Server packages

```bash
sudo apt update
sudo apt install -y python3-venv git
# Caddy (web server with automatic HTTPS), from the official repo:
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

If the server has a firewall, open ports **80 and 443** (e.g.
`sudo ufw allow 80,443/tcp`). Port 8000 stays internal - only Caddy talks
to the app.

## 3. Install the app

```bash
sudo mkdir -p /opt/gw2_ceo && sudo chown deploy: /opt/gw2_ceo
git clone https://github.com/FlorianBaltrusch/gw2_ceo.git /opt/gw2_ceo
cd /opt/gw2_ceo
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# one-time: fetch the GW2 API caches and all images (traits, banners, icons)
PYTHONPATH=. .venv/bin/python generate_traits.py

# smoke test, then Ctrl+C
.venv/bin/gunicorn --bind 127.0.0.1:8000 gw2ceo.app:app
```

Note: deploy the branch that contains the website (merge
`feat/all-profession-traits` into `main` first, or `git clone -b <branch>`).

## 4. Run as a service

Edit the two ADJUST lines in `deploy/gw2ceo.service` (user + path), then:

```bash
sudo cp deploy/gw2ceo.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now gw2ceo
systemctl status gw2ceo        # should say "active (running)"
```

## 5. Put Caddy in front

Replace `ceo.example.com` in `deploy/Caddyfile` with your domain, then:

```bash
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Open `https://ceo.example.com` - Caddy fetches the certificate on the first
request (can take a few seconds).

## 6. Updating later

```bash
cd /opt/gw2_ceo
git pull
.venv/bin/pip install -r requirements.txt          # only when it changed
PYTHONPATH=. .venv/bin/python generate_traits.py   # after balance patches
sudo systemctl restart gw2ceo
```

## Notes

- `main.py` (Flask debug server) is for local development only - never run
  it on the server; the systemd unit uses gunicorn.
- The app keeps no secrets and needs no database; the whole state is the
  repository plus the generated `assets/` caches.
- `generate_traits.py` needs outbound internet access (GW2 API + wiki) and
  is safe to re-run any time: it only downloads what is missing and re-trims
  banners idempotently.
