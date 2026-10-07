"""Create a disposable profile fixture in the isolated CI API container."""
import json
from pathlib import Path
import requests

session = requests.Session()
session.trust_env = False
session.verify = '/var/lib/marzban/certs/localhost.crt'
base = 'https://localhost:8000'
login = json.loads(Path('/var/lib/marzban/local-admin.json').read_text())
r = session.post(base+'/api/admin/token', data=login, timeout=30)
r.raise_for_status()
session.headers['Authorization'] = 'Bearer '+r.json()['access_token']
r = session.get(base+'/api/inbounds', timeout=30)
r.raise_for_status()
inbounds = r.json()
r = session.post(base+'/api/user', json={
    'username': 'ci_profiles', 'status': 'active',
    'proxies': {p: {} for p in inbounds},
    'inbounds': {p: [i['tag'] for i in items] for p, items in inbounds.items()},
}, timeout=30)
r.raise_for_status()
print('Disposable CI profile user created')
