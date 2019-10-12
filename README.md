uvicorn main:app --reload --port 8888


brew install nginx
/usr/local/etc/nginx/nginx.conf

sudo brew services restart nginx


# issues

```
future: <Task finished coro=<client_ws_wazo() done, defined at ./main.py:125> exception=ConnectionClosedError('code = 4003 (private use), reason = authentication expired')>
```

Because refresh_token is not managed
