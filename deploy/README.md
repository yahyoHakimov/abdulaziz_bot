# Deployment

The bot runs on a DigitalOcean droplet under `/opt/abdulaziz_bot` as a systemd
service. The two reminder jobs run as **systemd timers** (replacing the old
hand-edited crontab, which was not version-controlled).

## One-time server setup

```bash
# 1. Create a dedicated unprivileged user and hand it the app dir
sudo useradd --system --home /opt/abdulaziz_bot --shell /usr/sbin/nologin barber
sudo chown -R barber:barber /opt/abdulaziz_bot

# 2. Install unit files
sudo cp /opt/abdulaziz_bot/deploy/barber-bot.service     /etc/systemd/system/
sudo cp /opt/abdulaziz_bot/deploy/barber-remind.service  /etc/systemd/system/
sudo cp /opt/abdulaziz_bot/deploy/barber-remind.timer    /etc/systemd/system/
sudo cp /opt/abdulaziz_bot/deploy/barber-confirm.service /etc/systemd/system/
sudo cp /opt/abdulaziz_bot/deploy/barber-confirm.timer   /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Enable the long-running bot and the two timers
sudo systemctl enable --now barber-bot.service
sudo systemctl enable --now barber-remind.timer barber-confirm.timer

# 4. Remove the old crontab entries (now superseded by the timers)
sudo crontab -e   # delete the remind.py / confirm.py lines
```

## Verifying

```bash
systemctl status barber-bot
systemctl list-timers 'barber-*'      # next run times for both jobs
systemctl start barber-remind.service # fire a reminder run manually
journalctl -u barber-bot -n 50        # recent bot logs
```

## Timer schedule

- `barber-remind.timer`  → 03:00 UTC (08:00 Asia/Tashkent) — morning reminders
- `barber-confirm.timer` → 18:00 UTC (23:00 Asia/Tashkent) — evening confirmations

`Persistent=true` means a job missed while the droplet was down runs at next boot.

> The CI deploy (`.github/workflows/deploy.yml`) `git pull`s and restarts
> `barber-bot`. After changing any unit file, re-run steps 2–3 above on the
> server; the deploy workflow does not reinstall unit files automatically.
