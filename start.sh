nginx
cd /app
su -c "uvicorn app:app --host 127.0.0.1 --port 8000 --workers 1 --proxy-headers" -s /bin/bash