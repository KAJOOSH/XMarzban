"""Smoke and persistence tests against the isolated Docker instance."""
import base64
import json
import os
import secrets
import sqlite3
import subprocess
from pathlib import Path
import bcrypt
import requests
import yaml

DATA = Path('/var/lib/marzban')
credentials = DATA / 'local-admin.json'
with sqlite3.connect(DATA / 'db.sqlite3') as db:
    row = db.execute('SELECT username FROM admins LIMIT 1').fetchone()
    if not row:
        login = {'username': 'localadmin', 'password': secrets.token_urlsafe(24)}
        db.execute('INSERT INTO admins (username,hashed_password,is_sudo,users_usage) VALUES (?,?,1,0)',
                   (login['username'], bcrypt.hashpw(login['password'].encode(), bcrypt.gensalt()).decode()))
        credentials.write_text(json.dumps(login))
        credentials.chmod(0o600)
    else:
        login = json.loads(credentials.read_text())
session = requests.Session()
session.verify = str(DATA / 'certs/localhost.crt')
base = 'https://localhost:8000'
def call(method, path, **kwargs):
    response = session.request(method, base + path, timeout=30, **kwargs)
    assert response.ok, f'{method} {path}: {response.status_code} {response.text[:300]}'
    return response
session.headers['Authorization'] = 'Bearer ' + call('POST','/api/admin/token', data=login).json()['access_token']
assert call('GET','/dashboard/').status_code == 200
bundle = next(Path('/code/app/dashboard/build/statics').glob('index.*.js'))
assert 'baseURL:"/api/"' in bundle.read_text(), 'Local dashboard must send login requests to /api/admin/token'
assert call('GET','/dashboard/statics/' + bundle.name).content == bundle.read_bytes()
core = call('GET','/api/core').json()
assert core['version'] == '26.3.27' and core['started'], core
caps = call('GET','/api/core/capabilities').json()
assert len(caps['transports']) == 7
inbounds = call('GET','/api/inbounds').json()
managed_count = sum(map(len,inbounds.values()))
assert managed_count >= 58
hosts = call('GET','/api/hosts').json()
tag = inbounds['vless'][0]['tag']
original_hosts = hosts[tag]
response = session.put(base+'/api/hosts',json={tag:[{'remark':'invalid-protocol','address':'localhost','xray_protocol_settings':{'security':'aes-128-gcm'}}]},timeout=30)
assert response.status_code == 400
assert call('GET','/api/hosts').json()[tag] == original_hosts
override = {'network':'raw','security':'none','rawSettings':{'header':{'type':'none'}}}
try:
    updated = call('PUT','/api/hosts',json={tag:[{'remark':'api-smoke','address':'localhost','xray_stream_settings':override,'xray_protocol_settings':{'encryption':'none'}}]}).json()
    assert updated[tag][0]['xray_stream_settings'] == override
    with sqlite3.connect(DATA / 'db.sqlite3') as db:
        saved = db.execute('SELECT xray_stream_settings FROM hosts WHERE xray_stream_settings IS NOT NULL').fetchall()
        assert any(json.loads(row[0]) == override for row in saved)
finally:
    call('PUT','/api/hosts',json={tag:original_hosts})
name = 'docker_smoke_' + secrets.token_hex(4)
try:
    user = call('POST','/api/user',json={'username':name,'status':'active','proxies':{p:{} for p in inbounds},'inbounds':{p:[i['tag'] for i in items] for p,items in inbounds.items()}}).json()
    original_auth = user['proxies']['hysteria']['auth']
    original_wg = user['proxies']['wireguard']['private_key']
    sub = user['subscription_url'].removeprefix(base).rstrip('/')
    negotiated = call('GET',sub,headers={'User-Agent':'v2rayN'}).json()
    expected_count = sum(len(hosts[i["tag"]]) for items in inbounds.values() for i in items)
    assert len(negotiated) == expected_count
    configs = call('GET',sub + '/v2ray-json').json()
    assert len(configs) == expected_count, len(configs)
    browser_page = call('GET',sub,headers={'Accept':'text/html','User-Agent':'Mozilla/5.0'}).text
    custom_json = os.environ.get('USE_CUSTOM_JSON_DEFAULT', '').lower() == 'true'
    assert user['use_custom_json'] == custom_json
    if custom_json:
        assert f'id="config-count">{expected_count}</span>' in browser_page
        assert browser_page.count('class="full-config"') == expected_count
        script_configs = json.loads(browser_page.split('const fullConfigs = ',1)[1].split(';\n',1)[0])
        assert len(script_configs) == expected_count
        assert sorted(c['remarks'] for c in script_configs) == sorted(c['remarks'] for c in configs)
        assert len(call('GET',sub,headers={'Accept':'*/*','User-Agent':'Mozilla/5.0'}).json()) == expected_count
    else:
        assert 'class="full-config"' not in browser_page and 'const fullConfigs' not in browser_page
        assert 'Download Xray JSON' not in browser_page
        assert f'id="link-count">{len(user["links"])}</span>' in browser_page
        raw_links = json.loads(browser_page.split('const rawLinks = ',1)[1].split(';\n',1)[0])
        assert raw_links == user['links']
        body = call('GET',sub,headers={'Accept':'*/*','User-Agent':'Mozilla/5.0'}).text
        assert base64.b64decode(body).decode().splitlines() == user['links']
    for config in configs:
        encoded = json.dumps(config)
        assert 'privateKey' not in encoded and 'keyFile' not in encoded and 'echServerKeys' not in encoded
        checked = subprocess.run(['xray','run','-test','-config','stdin:'],input=encoded,text=True,capture_output=True)
        assert checked.returncode == 0, checked.stdout + checked.stderr
    for fmt in ('clash','clash-meta','sing-box','outline','v2ray'):
        body = call('GET', sub + '/' + fmt).text
        if fmt in ('clash','clash-meta'): yaml.safe_load(body)
        elif fmt == 'v2ray': assert base64.b64decode(body).decode()
        else: json.loads(body)
    call('PUT','/api/user/'+name,json={'status':'disabled'})
    assert call('GET','/api/user/'+name).json()['status'] == 'disabled'
    call('PUT','/api/user/'+name,json={'status':'active'})
    changed = call('POST','/api/user/'+name+'/revoke_sub').json()
    assert changed['proxies']['hysteria']['auth'] != original_auth
    assert changed['proxies']['wireguard']['private_key'] != original_wg
    assert call('GET','/api/user/'+name).json()['proxies']['hysteria']['auth'] == changed['proxies']['hysteria']['auth']
finally:
    call('DELETE','/api/user/'+name)
config = call('GET','/api/core/config').json()
assert call('PUT','/api/core/config',json=config).json() == config
bad = json.loads(json.dumps(config))
bad['inbounds'][0]['settings']['accounts'] = 'invalid-object'
response = session.put(base+'/api/core/config',json=bad,timeout=30)
assert response.status_code == 400, response.status_code
assert call('GET','/api/core/config').json() == config
assert call('GET','/api/core').json()['started']
print(f'PASS: dashboard, Xray readiness, {managed_count} inbounds, host JSON database persistence, {expected_count} Xray JSON configs, six subscription formats, user create/disable/enable/revoke/delete, valid-TUN save and invalid-config preservation')
