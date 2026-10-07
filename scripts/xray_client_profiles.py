"""Server-compatible client examples for each managed Xray inbound."""
from copy import deepcopy
from app.xray.transport import client_stream

def profiles(inbound):
    protocol = inbound['protocol']
    stream = inbound.get('streamSettings', {})
    network = stream.get('network', 'raw')
    security = stream.get('security', 'none')
    for variant in ('advanced-a', 'advanced-b'):
        second = variant.endswith('b')
        transport = {'sockopt': {'domainStrategy': 'UseIPv4', 'tcpFastOpen': False,
                                'tcpKeepAliveIdle': 30 if second else 60, 'tcpKeepAliveInterval': 10,
                                'happyEyeballs': {'prioritizeIPv6': False, 'tryDelayMs': 100, 'interleave': 1, 'maxConcurrentTry': 2}}}
        options = {}
        outbound = {'targetStrategy': 'AsIs', 'mux': {'enabled': False, 'concurrency': 4,
                                                    'xudpConcurrency': 8, 'xudpProxyUDP443': 'allow'}}
        if protocol == 'wireguard':
            transport = None
            options = {'mtu': 1280 if second else 1380, 'workers': 2 if second else 1,
                       'reserved': [0, 0, 0], 'noKernelTun': True, 'domainStrategy': 'ForceIPv4'}
        else:
            if security == 'tls':
                transport['tlsSettings'] = {'fingerprint': 'firefox' if second else 'chrome',
                    'minVersion': '1.2' if second else '1.3', 'maxVersion': '1.3',
                    'enableSessionResumption': not second, 'disableSystemRoot': True,
                    'verifyPeerCertByName': 'localhost', 'curvePreferences': ['X25519', 'CurveP256']}
                if second:
                    transport['tlsSettings']['cipherSuites'] = 'TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256'
            elif security == 'reality':
                transport['realitySettings'] = {'fingerprint': 'firefox' if second else 'chrome',
                                               'spiderX': '/client-b' if second else '/client-a'}
            if network in ('ws', 'httpupgrade'):
                transport[network+'Settings'] = {'headers': {'User-Agent': 'Marzban-Xray-'+variant, 'X-Client-Profile': variant}}
                if network == 'ws': transport['wsSettings']['heartbeatPeriod'] = 10 if second else 20
            elif network == 'grpc':
                transport['grpcSettings'] = {'multiMode': second, 'idle_timeout': 30, 'health_check_timeout': 10,
                    'permit_without_stream': second, 'initial_windows_size': 131072 if second else 65536,
                    'user_agent': 'Marzban-Xray-'+variant}
            elif network == 'kcp':
                transport['kcpSettings'] = {'mtu': 1280 if second else 1350, 'tti': 10 if second else 20,
                    'uplinkCapacity': 20, 'downlinkCapacity': 50, 'congestion': second, 'readBufferSize': 4, 'writeBufferSize': 4}
            elif network == 'xhttp':
                extra = {'headers': {'User-Agent': 'Marzban-Xray-'+variant, 'X-Client-Profile': variant},
                    'xPaddingBytes': '128-256' if second else '256-512',
                    'noGRPCHeader': second, 'noSSEHeader': second,
                    'scMaxEachPostBytes': '32768-65536', 'scMinPostsIntervalMs': '10-20',
                    'xmux': {'maxConcurrency': '2-4', 'maxConnections': 0, 'cMaxReuseTimes': '4-8',
                             'hMaxRequestTimes': '20-40', 'hMaxReusableSecs': '60-120', 'hKeepAlivePeriod': 10}}
                inherited = client_stream(stream)['xhttpSettings']
                inherited.update(extra)
                if second and inherited.get('mode') != 'stream-one':
                    download = client_stream(stream)
                    download.update(address='localhost', port=inbound['port'])
                    download['sockopt'] = deepcopy(transport['sockopt'])
                    if security == 'reality':
                        download['realitySettings'].update(serverName='localhost', fingerprint='firefox',
                            shortId=stream['realitySettings']['shortIds'][0])
                    inherited['downloadSettings'] = download
                if second:
                    transport['xhttpSettings'] = {key: inherited.pop(key) for key in ('host', 'path', 'mode') if key in inherited}
                    transport['xhttpSettings']['extra'] = inherited
                else: transport['xhttpSettings'] = inherited
            elif network == 'hysteria':
                transport['finalmask'] = {'quicParams': {'congestion': 'brutal' if second else 'bbr',
                    'brutalUp': '50mbps', 'brutalDown': '100mbps', 'debug': False,
                    'initStreamReceiveWindow': 1048576, 'maxStreamReceiveWindow': 2097152,
                    'initConnectionReceiveWindow': 2097152, 'maxConnectionReceiveWindow': 4194304,
                    'maxIdleTimeout': 30, 'keepAlivePeriod': 10, 'disablePathMTUDiscovery': second, 'maxIncomingStreams': 128}}
            if protocol == 'vmess': options = {'security': 'chacha20-poly1305' if second else 'aes-128-gcm', 'level': 0, 'email': variant}
            elif protocol == 'vless': options = {'encryption': 'none', 'level': 0, 'email': variant}
            elif protocol == 'trojan': options = {'level': 0, 'email': variant}
            elif protocol == 'shadowsocks': options = {'level': 0, 'email': variant, 'uot': second}
            if second and protocol in ('vmess', 'vless', 'trojan', 'shadowsocks') and network in ('raw', 'ws', 'httpupgrade', 'kcp'):
                outbound['mux']['enabled'] = True
        yield variant, transport, options, outbound
