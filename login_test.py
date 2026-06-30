import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

url = 'http://localhost:5000/api/login'
data = json.dumps({'correo': 'admin@rentstyle.com', 'Contrasena': 'admin123'}).encode('utf-8')
req = Request(url, data=data, headers={'Content-Type': 'application/json'})

print('REQUEST', url)
try:
    with urlopen(req, timeout=10) as resp:
        print('STATUS', resp.status)
        print(resp.read().decode('utf-8'))
except HTTPError as e:
    print('STATUS', e.code)
    print(e.read().decode('utf-8'))
except URLError as e:
    print('URL ERROR', e)
