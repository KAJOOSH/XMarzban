"""Enable a separately keyed WireGuard proxy on an existing local user."""
import argparse
import json
from pathlib import Path
import requests
parser = argparse.ArgumentParser()
parser.add_argument('username')
args = parser.parse_args()
session = requests.Session()
session.verify = '/var/lib/marzban/certs/localhost.crt'
base = 'https://localhost:8000'
login = json.loads(Path('/var/lib/marzban/local-admin.json').read_text())
response = session.post(base+'/api/admin/token',data=login,timeout=30)
response.raise_for_status()
session.headers['Authorization'] = 'Bearer '+response.json()['access_token']
response = session.get(base+'/api/user/'+args.username,timeout=30)
response.raise_for_status()
user = response.json()
if 'wireguard' not in user['proxies']:
    proxies = user['proxies'] | {'wireguard':{}}
    inbounds = user['inbounds'] | {'wireguard':['LOCAL WIREGUARD']}
    response = session.put(base+'/api/user/'+args.username,json={'proxies':proxies,'inbounds':inbounds},timeout=30)
    response.raise_for_status()
print('WireGuard enabled with an independent client key')
