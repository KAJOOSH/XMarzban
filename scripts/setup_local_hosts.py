"""Point untouched default hosts at this loopback-only Docker deployment."""
import json
from pathlib import Path
import requests
session = requests.Session()
session.verify = '/var/lib/marzban/certs/localhost.crt'
base = 'https://localhost:8000'
login = json.loads(Path('/var/lib/marzban/local-admin.json').read_text())
response = session.post(base+'/api/admin/token',data=login,timeout=20)
response.raise_for_status()
session.headers['Authorization'] = 'Bearer '+response.json()['access_token']
response = session.get(base+'/api/hosts',timeout=20)
response.raise_for_status()
updates = {}
for tag, hosts in response.json().items():
    changed = False
    for host in hosts:
        if host['address'] == '{SERVER_IP}':
            host['address'] = 'localhost'
            changed = True
    if changed: updates[tag] = hosts
response = session.put(base+'/api/hosts',json=updates,timeout=20)
response.raise_for_status()
print(f'Configured {len(updates)} untouched local host defaults')
