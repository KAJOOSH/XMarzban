"""Check real Windows WireGuard connections through local Docker user lifecycle."""
import argparse
import json
import secrets
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('--core',required=True)
parser.add_argument('--certificate',required=True)
args = parser.parse_args()
context = ssl.create_default_context(cafile=args.certificate)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPSHandler(context=context))
base = 'https://localhost:8000'
login = json.loads(Path('local-admin.json').read_text())
from urllib.parse import urlencode
request = urllib.request.Request(base+'/api/admin/token',data=urlencode(login).encode(),headers={'Content-Type':'application/x-www-form-urlencoded'})
with opener.open(request,timeout=30) as response: token = json.load(response)['access_token']
def call(method,path,payload=None):
    request = urllib.request.Request(base+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,
                                    headers={'Authorization':'Bearer '+token,'Content-Type':'application/json','User-Agent':'v2rayN/7.22.6'})
    with opener.open(request,timeout=30) as response: return json.load(response)
name = 'wg_test_'+secrets.token_hex(4)
root = Path('output/xray')
results = []
def connect(label,path,reject=False):
    report = root / ('wg-'+label+'.json')
    command = [sys.executable,'scripts/test_windows_subscription.py','unused','--core',args.core,'--certificate',args.certificate,
               '--configuration',str(path),'--report',str(report)]
    if reject: command += ['--expect-rejection']
    checked = subprocess.run(command,timeout=40,capture_output=True,text=True)
    print(label+': '+('PASS' if checked.returncode == 0 else 'FAIL'),flush=True)
    assert checked.returncode == 0, checked.stdout + checked.stderr
    results.append({'stage':label,'passed':True,'expected_rejection':reject})
try:
    user = call('POST','/api/user',{'username':name,'status':'active','proxies':{'wireguard':{}},'inbounds':{'wireguard':['LOCAL WIREGUARD']}})
    sub = user['subscription_url'].removeprefix(base)
    original = root / 'wg-original-private-custom.json'
    original.write_text(json.dumps(call('GET',sub)),encoding='utf-8')
    connect('created',original)
    call('PUT','/api/user/'+name,{'status':'disabled'})
    connect('disabled',original,reject=True)
    call('PUT','/api/user/'+name,{'status':'active'})
    connect('reactivated',original)
    user = call('POST','/api/user/'+name+'/revoke_sub',{})
    connect('revoked-old-key',original,reject=True)
    sub = user['subscription_url'].removeprefix(base)
    current = root / 'wg-current-private-custom.json'
    current.write_text(json.dumps(call('GET',sub)),encoding='utf-8')
    connect('new-key',current)
    call('DELETE','/api/user/'+name)
    connect('deleted',current,reject=True)
finally:
    try: call('DELETE','/api/user/'+name)
    except Exception: pass
    for path in (root/'wg-original-private-custom.json',root/'wg-current-private-custom.json'):
        path.unlink(missing_ok=True)
    (root/'wireguard-lifecycle-results.json').write_text(json.dumps(results,indent=2))
