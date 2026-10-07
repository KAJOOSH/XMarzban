"""Append paired defaults and client profile examples to the isolated local deployment."""
import argparse
import json
from pathlib import Path
import requests
from scripts.init_xray_defaults import initialize
from scripts.xray_client_profiles import profiles
parser = argparse.ArgumentParser()
parser.add_argument('username')
args = parser.parse_args()
s = requests.Session()
s.verify = '/var/lib/marzban/certs/localhost.crt'
b = 'https://localhost:8000'
r=s.post(b+'/api/admin/token',data=json.loads(Path('/var/lib/marzban/local-admin.json').read_text()),timeout=30)
r.raise_for_status()
s.headers['Authorization']='Bearer '+r.json()['access_token']
def call(method,path,**kwargs):
    r=s.request(method,b+path,timeout=60,**kwargs)
    r.raise_for_status()
    return r.json()
materialized=Path('/var/lib/marzban/extended-presets.json')
try:
    initialize('/code/xray_config.json',materialized,refresh=True)
    defaults=json.loads(materialized.read_text())
    config=call('GET','/api/core/config')
    previous=json.dumps(config,sort_keys=True)
    tags={i['tag'] for i in config['inbounds']}
    additions=[i for i in defaults['inbounds'] if i['tag'] not in tags]
    for inbound in config['inbounds']:
        grpc=inbound.get('streamSettings',{}).get('grpcSettings',{})
        if grpc.get('headers')=={'User-Agent':'chrome'}:
            grpc.pop('headers')
            grpc['user_agent']='Marzban-Xray'
    owned = {i['tag']:i for i in defaults['inbounds'][65:]}
    config['inbounds'] = [owned.get(i['tag'], i) for i in config['inbounds']]
    config['inbounds'].extend(additions)
    decoy=next(i for i in defaults['inbounds'] if i['tag']=='LOCAL HTTPS')
    next(i for i in config['inbounds'] if i['tag']=='LOCAL HTTPS')['streamSettings']['tlsSettings']['certificates']=decoy['streamSettings']['tlsSettings']['certificates']
    if json.dumps(config,sort_keys=True)!=previous:
        call('PUT','/api/core/config',json=config)
finally:
    materialized.unlink(missing_ok=True)
    materialized.with_suffix('.json.backup').unlink(missing_ok=True)
inbounds=call('GET','/api/inbounds')
managed={i['tag'] for items in inbounds.values() for i in items}
hosts=call('GET','/api/hosts')
updates={}
for inbound in config['inbounds']:
    tag=inbound['tag']
    if tag not in managed: continue
    existing=[h for h in hosts[tag] if '[advanced-a]' not in h['remark'] and '[advanced-b]' not in h['remark']]
    if len(existing)==1 and existing[0]['address'] in ('localhost','{SERVER_IP}'):
        existing[0]['address']='localhost'
        existing[0]['remark']='Marz {USERNAME} ['+tag+' / base]'
    for label,stream,protocol,outbound in profiles(inbound):
        existing.append({'remark':'Marz {USERNAME} ['+tag+'] ['+label+']','address':'localhost',
            'xray_stream_settings':stream,'xray_protocol_settings':protocol,'xray_outbound_settings':outbound})
    updates[tag]=existing
call('PUT','/api/hosts',json=updates)
user=call('GET','/api/user/'+args.username)
proxies=user['proxies'] | {p:{} for p in inbounds if p not in user['proxies']}
selected=user['inbounds'].copy()
for p,items in inbounds.items(): selected[p]=list(dict.fromkeys(selected.get(p,[])+[i['tag'] for i in items]))
call('PUT','/api/user/'+args.username,json={'proxies':proxies,'inbounds':selected})
print(f'Added {len(additions)} paired inbounds and installed two client examples for {len(managed)} managed inbounds')
