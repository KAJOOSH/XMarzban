"""Verify each persisted client option survives HTTP subscription serialization."""
import json
from pathlib import Path
import requests
from scripts.xray_client_profiles import profiles
s=requests.Session()
s.verify='/var/lib/marzban/certs/localhost.crt'
b='https://localhost:8000'
r=s.post(b+'/api/admin/token',data=json.loads(Path('/var/lib/marzban/local-admin.json').read_text()),timeout=30)
r.raise_for_status()
s.headers['Authorization']='Bearer '+r.json()['access_token']
def get(path,ua=None):
    r=s.get(b+path,headers={'User-Agent':ua or 'profile-verification'},timeout=30)
    r.raise_for_status()
    return r.json()
import argparse
p=argparse.ArgumentParser()
p.add_argument('username')
a=p.parse_args()
user=get('/api/user/'+a.username)
sub=user['subscription_url'].removeprefix(b)
configs=get(sub+'/v2ray-json')
for ua in ('v2rayN','v2rayN/7.22.6','V2rayN','v2rayN/6.40'):
    assert len(get(sub,ua))==len(configs), ua
configuration=get('/api/core/config')
hosts=get('/api/hosts')
checks=[]
def subset(expected,actual,path,paths):
    if isinstance(expected,dict):
        assert isinstance(actual,dict), path
        for key,value in expected.items():
            assert key in actual, path+'.'+key
            subset(value,actual[key],path+'.'+key,paths)
    else:
        assert expected==actual, path
        paths.append(path)
for inbound in configuration['inbounds']:
    tag=inbound['tag']
    if tag not in hosts: continue
    for label,stream,protocol,outbound in profiles(inbound):
        suffix='['+tag+'] ['+label+']'
        matches=[c for c in configs if c['remarks'].endswith(suffix)]
        assert len(matches)==1, suffix
        saved=[h for h in hosts[tag] if h['remark'].endswith(suffix)]
        assert len(saved)==1, suffix
        assert saved[0]['xray_outbound_settings']==outbound
        assert saved[0]['xray_protocol_settings']==protocol
        assert saved[0]['xray_stream_settings']==stream
        actual=matches[0]['outbounds'][0]
        paths=[]
        if stream:
            stream=json.loads(json.dumps(stream))
            if 'extra' in stream.get('xhttpSettings',{}):
                extra=stream['xhttpSettings'].pop('extra')
                stream['xhttpSettings'].update(extra)
            subset(stream,actual['streamSettings'],'streamSettings',paths)
        settings=actual['settings']
        if 'vnext' in settings: settings=settings['vnext'][0]['users'][0]
        elif 'servers' in settings: settings=settings['servers'][0]
        subset(protocol,settings,'protocolSettings',paths)
        subset(outbound,actual,'outbound',paths)
        checks.append({'inbound':tag,'profile':label,'verified_fields':paths})
# Check inherited fields independently of the projection implementation.
for inbound in configuration['inbounds']:
    tag=inbound['tag']
    if tag not in hosts or inbound['protocol']=='wireguard': continue
    server=inbound.get('streamSettings',{})
    entries=[c for c in configs if ('['+tag+'] [') in c['remarks'] or ('['+tag+' / base]') in c['remarks']]
    assert len(entries)==3, tag
    for entry in entries:
        actual=entry['outbounds'][0]['streamSettings']
        paths=[]
        if server.get('finalmask',{}).get('udp'):
            subset({'udp':server['finalmask']['udp']},actual['finalmask'],'streamSettings.finalmask',paths)
        for field in ('pinnedPeerCertSha256','echConfigList','echForceQuery'):
            if field in server.get('tlsSettings',{}):
                subset({field:server['tlsSettings'][field]},actual['tlsSettings'],'streamSettings.tlsSettings',paths)
        for field in ('publicKey','mldsa65Verify'):
            if field in server.get('realitySettings',{}):
                subset({field:server['realitySettings'][field]},actual['realitySettings'],'streamSettings.realitySettings',paths)
        if server.get('network')=='xhttp':
            fields=('host','path','mode','sessionPlacement','sessionKey','seqPlacement','seqKey',
                    'uplinkHTTPMethod','uplinkDataPlacement','uplinkDataKey','uplinkChunkSize',
                    'xPaddingObfsMode','xPaddingKey','xPaddingHeader','xPaddingPlacement','xPaddingMethod')
            inherited={f:server['xhttpSettings'][f] for f in fields if f in server['xhttpSettings']}
            subset(inherited,actual['xhttpSettings'],'streamSettings.xhttpSettings',paths)
        if paths: checks.append({'inbound':tag,'profile':'inherited','verified_fields':paths})
report={'total_configs':len(configs),'profiles_checked':sum(c['profile']!='inherited' for c in checks),
        'inherited_checks':sum(c['profile']=='inherited' for c in checks),
        'leaf_value_assertions':sum(len(c['verified_fields']) for c in checks),
        'unique_field_paths':sorted({p for c in checks for p in c['verified_fields']}),'checks':checks}
Path('/code/docs/xray-client-fields-results.json').write_text(json.dumps(report,indent=2))
print(f"PASS: {len(configs)} JSON entries, {report['profiles_checked']} explicit profiles and {report['inherited_checks']} inherited checks, {report['leaf_value_assertions']} exact field-value assertions; four User-Agent variants")
