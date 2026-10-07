"""Export standalone server configurations matching every user's host profile."""
import argparse
import base64
import csv
import json
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit
from copy import deepcopy
from pathlib import Path
import requests
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

parser = argparse.ArgumentParser()
parser.add_argument('username')
parser.add_argument('directory', type=Path)
parser.add_argument('--validate', action='store_true')
args = parser.parse_args()
if args.directory.exists():
    raise SystemExit('Destination exists; choose a new directory')
root = args.directory
root.mkdir(parents=True)
session = requests.Session()
session.trust_env = False
session.verify = '/var/lib/marzban/certs/localhost.crt'
base = 'https://localhost:8000'
login = json.loads(Path('/var/lib/marzban/local-admin.json').read_text())
r = session.post(base+'/api/admin/token', data=login, timeout=30)
r.raise_for_status()
session.headers['Authorization'] = 'Bearer '+r.json()['access_token']
def get(path):
    r = session.get(base+path, timeout=30)
    r.raise_for_status()
    return r.json()
server = get('/api/core/config')
user = get('/api/user/'+args.username)
hosts = get('/api/hosts')
uri_remarks = set()
for link in user['links']:
    if link.startswith('vmess://') and '@' not in link:
        try:
            uri_remarks.add(json.loads(base64.b64decode(link[8:]))['ps'])
            continue
        except Exception:
            pass
    uri_remarks.add(unquote(urlsplit(link).fragment))
sub_url = user['subscription_url'].rstrip('/')+'/v2ray-json'
r = session.get(sub_url,timeout=30)
r.raise_for_status()
client_configs = r.json()
selected = {tag for tags in user['inbounds'].values() for tag in tags}
by_tag = {i['tag']:i for i in server['inbounds']}
with __import__('sqlite3').connect('/var/lib/marzban/db.sqlite3') as db:
    uid = db.execute('SELECT id FROM users WHERE username=?',(args.username,)).fetchone()[0]
cert_paths = {}
def localize(value):
    if isinstance(value, list): return [localize(v) for v in value]
    if not isinstance(value, dict): return value
    result = {}
    for k,v in value.items():
        if k in ('certificateFile','keyFile') and isinstance(v,str):
            source = Path(v)
            if not source.is_file(): raise RuntimeError('Missing certificate dependency')
            if v not in cert_paths:
                dest = root/'certs'/source.name
                dest.parent.mkdir(exist_ok=True)
                if dest.exists() and dest.read_bytes()!=source.read_bytes():
                    raise RuntimeError('Certificate basename collision')
                shutil.copy2(source,dest)
                cert_paths[v] = 'certs/'+dest.name
            result['certificate' if k == 'certificateFile' else 'key'] = source.read_text().strip().splitlines()
        else: result[k] = localize(v)
    return result
rows = []
for inbound in server['inbounds']:
    tag = inbound['tag']
    if tag not in selected: continue
    proto = inbound['protocol']
    account = deepcopy(user['proxies'][proto])
    primary = deepcopy(inbound)
    settings = primary.setdefault('settings',{})
    if proto == 'wireguard':
        key = X25519PrivateKey.from_private_bytes(base64.b64decode(account['private_key']))
        pub = base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()
        settings['peers'] = [{'publicKey':pub,'allowedIPs':[f'10.78.{uid//254+1}.{uid%254+1}/32',f'fd00:78::{uid+2:x}/128']}]
        settings['address'] = ['10.78.0.1/32','fd00:78::1/128']
        settings.pop('clients',None)
    else:
        stream = primary.get('streamSettings',{})
        vision = stream.get('network','raw') in ('raw','tcp') and stream.get('security') in ('tls','reality')
        if not vision: account.pop('flow',None)
        settings['clients'] = [dict(email=f'{uid}.{args.username}', **account)]
    for index, host in enumerate(hosts.get(tag,[])):
        remark = host['remark']
        match = re.search(r'/((?:advanced-[ab])|base)\]', remark)
        variant = match.group(1) if match else ('advanced-a' if 'advanced-a' in remark else 'advanced-b' if 'advanced-b' in remark else 'base' if index == 0 else f'host-{index+1}')
        client = client_configs[len(rows)]
        proxy = next(o for o in client['outbounds'] if o['tag']=='proxy')
        if proxy['protocol'] != proto: raise RuntimeError('Subscription order mismatch')
        export_format = 'URI' if client['remarks'] in uri_remarks else 'JSON'
        filename = re.sub(r'[^a-z0-9]+','-',tag.lower()).strip('-')+'--'+variant+'--'+export_format+'--DEFAULT-NOT-REQUIRED.json'
        if (root/filename).exists(): raise RuntimeError('Duplicate profile filename')
        config = {k:deepcopy(v) for k,v in server.items() if k not in ('inbounds','api','stats')}
        config['inbounds'] = [deepcopy(primary)]
        needs_decoy = primary.get('streamSettings',{}).get('security')=='reality'
        if needs_decoy:
            config['inbounds'].append(deepcopy(by_tag['LOCAL HTTPS']))
        config.setdefault('routing',{})['rules'] = [rule for rule in config.get('routing',{}).get('rules',[]) if rule.get('outboundTag')!='API']
        config = localize(config)
        (root/filename).write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n')
        rows.append({'file':filename,'protocol':proto,'server_inbound':tag,'client_profile':variant,'client_format':export_format,'USE_CUSTOM_JSON_DEFAULT_required':'no','port':primary.get('port'),'extra_inbound':'LOCAL HTTPS' if needs_decoy else ''})
if len(rows)!=354: raise RuntimeError(f'Expected 354 profiles, got {len(rows)}')
with (root/'index.csv').open('w',newline='',encoding='utf-8-sig') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
(root/'README.md').write_text('''# کانفیگ‌های مستقل سمت سرور

۳۵۴ فایل JSON متناظر با ۳۵۴ نمونهٔ اشتراک کاربر؛ شامل ۱۱۸ ورودی سرور با سه پروفایل کلاینت برای هر ورودی.
نام فایل از نام ورودی، پروتکل، ترنسپورت، امنیت یا ماسک و نام پروفایل ساخته شده است. جدول index.csv ارتباط هر فایل را مشخص می‌کند.
برچسب URI یعنی نمونه در خروجی لینک خام فعلی وجود دارد؛ پشتیبانی وارد کردن فیلدهای آن به نسخهٔ کلاینت بستگی دارد. برچسب JSON یعنی نمونه برای حفظ تنظیمات کامل به خروجی JSON نیاز دارد. DEFAULT-NOT-REQUIRED در تمام نام‌ها یعنی فعال کردن USE_CUSTOM_JSON_DEFAULT برای این نمونه الزامی نیست؛ مسیر صریح /v2ray-json یا تشخیص v2rayN خروجی JSON را بدون آن ارائه می‌دهد. این گزینه تنها پیش‌فرض پاسخ لینک عمومی را تغییر می‌دهد.
تفاوت advanced-a و advanced-b در تنظیمات کلاینت است؛ بنابراین سه فایل متناظر با یک ورودی، عمداً کانفیگ سرور یکسان دارند. تنظیمات کلاینت به جای تنظیمات سرور قرار داده نشده‌اند.
فایل‌ها حساب همین کاربر و کلیدهای سرور فعلی را دارند؛ گواهی و کلید TLS داخل فایل‌ها قرار گرفته‌اند تا فایل‌ها به مسیر نصب Xray وابسته نباشند. نسخهٔ جداگانهٔ آن‌ها نیز در certs موجود است.

برای اجرا، ابتدا وارد این پوشه شوید و فقط یکی از فایل‌ها را اجرا کنید:

    xray run -config vless-raw--base.json

پورت‌ها با Docker فعال مشترک‌اند؛ اجرای هم‌زمان روی همان میزبان باعث تداخل پورت می‌شود. این خروجی تنظیمات سیستم فعال را تغییر نمی‌دهد.
نمونه‌های REALITY علاوه بر ورودی اصلی، ورودی LOCAL HTTPS را برای مقصد محلی REALITY همراه دارند. گواهی و کلید لازم در certs موجود است.
این فایل‌ها به نصب محلی و آدرس localhost مربوط‌اند؛ برای استقرار روی سرور دیگر، دامنه، آدرس، گواهی و مقصد REALITY باید با آن محیط هماهنگ شوند.
WireGuard در فضای کاربر اجرا می‌شود و peer همین کاربر را دارد. گواهی‌های خصوصی و کلیدهای موجود در پوشه را عمومی منتشر نکنید.
''',encoding='utf-8')
if args.validate:
    for row in rows:
        result = subprocess.run(['/usr/local/bin/xray','run','-test','-config',row['file']],cwd=root,text=True,capture_output=True)
        if result.returncode:
            raise RuntimeError(row['file']+': '+result.stdout+result.stderr)
    (root/'validation.txt').write_text('Xray v26.3.27: 354/354 standalone server configuration checks passed. No listeners started.\n')
print(f'Exported {len(rows)} server files for {len(selected)} inbounds; validation={args.validate}')
