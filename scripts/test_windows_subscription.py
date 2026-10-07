"""Validate and connect every Xray JSON entry using the installed Windows core."""
import argparse
import copy
import json
import re
import socket
import ssl
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('url')
parser.add_argument('--debug', action='store_true')
parser.add_argument('--protocol')
parser.add_argument('--match')
parser.add_argument('--attempts',type=int,default=1,choices=range(1,4))
parser.add_argument('--timeout',type=float,default=8)
parser.add_argument('--configuration')
parser.add_argument('--expect-rejection', action='store_true')
parser.add_argument('--core', required=True)
parser.add_argument('--certificate', required=True)
parser.add_argument('--report', default='output/xray/windows-subscription-results.json')
args = parser.parse_args()
context = ssl.create_default_context(cafile=args.certificate)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), urllib.request.HTTPSHandler(context=context))
if args.configuration:
    entries = json.loads(Path(args.configuration).read_text(encoding='utf-8'))
else:
    request = urllib.request.Request(args.url, headers={'User-Agent':'v2rayN/7.22.6'})
    with opener.open(request, timeout=20) as response:
        entries = json.load(response)
if args.protocol:
    entries = [entry for entry in entries if entry['outbounds'][0]['protocol'] == args.protocol]
if args.match:
    entries = [entry for entry in entries if re.search(args.match,entry.get('remarks',''))]
assert isinstance(entries, list) and entries
results = []
def read_exact(conn, length):
    value = b''
    while len(value) < length:
        chunk = conn.recv(length-len(value))
        if not chunk: raise OSError('Unexpected end of stream')
        value += chunk
    return value
with tempfile.TemporaryDirectory(prefix='marzban-windows-client-') as directory:
    root = Path(directory)
    for index, entry in enumerate(entries):
        config = copy.deepcopy(entry)
        config['log'] = {'loglevel':'debug' if args.debug else 'warning'}
        config['inbounds'] = [{'listen':'127.0.0.1','port':19091,'protocol':'socks','settings':{'auth':'noauth','udp':True}}]
        path = root / 'client.json'
        path.write_text(json.dumps(config), encoding='utf-8')
        record = {'index':index+1,'remark':entry.get('remarks'),'protocol':entry['outbounds'][0]['protocol'],
                  'network':entry['outbounds'][0].get('streamSettings',{}).get('network'),'validation':False,'connection':False}
        checked = subprocess.run([args.core,'run','-test','-c',str(path)],capture_output=True,text=True,encoding='utf-8',timeout=20)
        if checked.returncode:
            record['error'] = (checked.stdout+checked.stderr)[-1000:]
        else:
            record['validation'] = True
            record['attempt_errors'] = []
            for attempt in range(args.attempts):
                record['attempts'] = attempt+1
                with open(root/'client.log','w+',encoding='utf-8') as log:
                    process = subprocess.Popen([args.core,'run','-c',str(path)],stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
                    started = time.monotonic()
                    try:
                        while True:
                            if process.poll() is not None: raise OSError('Core exited')
                            try:
                                conn = socket.create_connection(('127.0.0.1',19091),timeout=.2)
                                break
                            except OSError:
                                if time.monotonic()-started > 5: raise
                                time.sleep(.05)
                        with conn:
                            conn.settimeout(args.timeout)
                            conn.sendall(b'\x05\x01\x00')
                            assert read_exact(conn,2) == b'\x05\x00'
                            target = b'www.google.com'
                            conn.sendall(b'\x05\x01\x00\x03'+bytes([len(target)])+target+(443).to_bytes(2,'big'))
                            head = read_exact(conn,4)
                            assert head[1] == 0, f'SOCKS reply {head[1]}'
                            length = 4 if head[3] == 1 else 16 if head[3] == 4 else read_exact(conn,1)[0]
                            read_exact(conn,length+2)
                            with ssl.create_default_context().wrap_socket(conn,server_hostname='www.google.com') as secure:
                                secure.sendall(b'HEAD /generate_204 HTTP/1.1\r\nHost: www.google.com\r\nConnection: close\r\n\r\n')
                                status = secure.recv(4096).split(b'\r\n')[0].decode('ascii')
                                assert status.startswith('HTTP/'), status
                                record.update(connection=True,response=status,seconds=round(time.monotonic()-started,3))
                    except Exception as exc:
                        record['error'] = str(exc)
                        log.flush()
                        log.seek(0)
                        record['diagnostic_log'] = log.read()[-5000:]
                    finally:
                        process.terminate()
                        process.wait(timeout=5)
                if record['connection']:
                    record.pop('error',None)
                    record.pop('diagnostic_log',None)
                    break
                record['attempt_errors'].append(record.get('error','Unknown failure'))
                if args.expect_rejection: break
        results.append(record)
        print(f'{index+1}/{len(entries)} {record["protocol"]}/{record["network"]}: '+('PASS' if record['connection'] else 'FAIL '+record.get('error','')),flush=True)
        Path(args.report).write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(f'Validated {sum(r["validation"] for r in results)}/{len(results)}; connected {sum(r["connection"] for r in results)}/{len(results)}',flush=True)
passed = all(r['validation'] and not r['connection'] for r in results) if args.expect_rejection else all(r['connection'] for r in results)
raise SystemExit(0 if passed else 1)
