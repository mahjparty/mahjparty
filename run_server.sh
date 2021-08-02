mkdir -p games
sudo venv/bin/gunicorn --certfile /etc/letsencrypt/live/api.mahj.party/fullchain.pem --keyfile /etc/letsencrypt/live/api.mahj.party/privkey.pem -b 0.0.0.0:445 --workers=1 --timeout 60 -p /tmp/gunicorn2.pid --access-logfile logs/gunicorn-access.log --error-logfile logs/gunicorn-error.log server:app
