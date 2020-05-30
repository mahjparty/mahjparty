mkdir -p games
sudo /usr/local/bin/gunicorn --certfile /etc/letsencrypt/live/api.mahj.party/fullchain.pem --keyfile /etc/letsencrypt/live/api.mahj.party/privkey.pem -b 0.0.0.0:443 --workers=1 --timeout 60 -p /tmp/gunicorn.pid --access-logfile logs/gunicorn-access.log --error-logfile logs/gunicorn-error.log server:app
