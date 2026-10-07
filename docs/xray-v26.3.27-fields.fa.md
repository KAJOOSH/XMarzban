# فهرست تنظیمات Xray v26.3.27

این فهرست از سورس همان تگ استخراج شده است؛ نوع Go و محل تعریف هر فیلد را نشان می‌دهد. این فایل JSON Schema یا تضمین معتبر بودن تمام ترکیب‌های فیلدها نیست. قواعد Build و اعتبارسنجی اجرایی Xray نیز باید رعایت شوند.

Commit: `d2758a023cd7f4174a5a5fa4ff66e487d4342ba0`

## SniffingConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L58)

| فیلد JSON | نوع در سورس |
|---|---|
| `enabled` | `bool` |
| `destOverride` | `*StringList` |
| `domainsExcluded` | `*StringList` |
| `metadataOnly` | `bool` |
| `routeOnly` | `bool` |

## MuxConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L102)

| فیلد JSON | نوع در سورس |
|---|---|
| `enabled` | `bool` |
| `concurrency` | `int16` |
| `xudpConcurrency` | `int16` |
| `xudpProxyUDP443` | `string` |

## InboundDetourConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L126)

| فیلد JSON | نوع در سورس |
|---|---|
| `protocol` | `string` |
| `port` | `*PortList` |
| `listen` | `*Address` |
| `settings` | `*json.RawMessage` |
| `tag` | `string` |
| `streamSettings` | `*StreamConfig` |
| `sniffing` | `*SniffingConfig` |

## OutboundDetourConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L213)

| فیلد JSON | نوع در سورس |
|---|---|
| `protocol` | `string` |
| `sendThrough` | `*string` |
| `tag` | `string` |
| `settings` | `*json.RawMessage` |
| `streamSettings` | `*StreamConfig` |
| `proxySettings` | `*ProxyConfig` |
| `mux` | `*MuxConfig` |
| `targetStrategy` | `string` |

## Config

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L346)

| فیلد JSON | نوع در سورس |
|---|---|
| `transport` | `map[string]json.RawMessage` |
| `log` | `*LogConfig` |
| `routing` | `*RouterConfig` |
| `dns` | `*DNSConfig` |
| `inbounds` | `[]InboundDetourConfig` |
| `outbounds` | `[]OutboundDetourConfig` |
| `policy` | `*PolicyConfig` |
| `api` | `*APIConfig` |
| `metrics` | `*MetricsConfig` |
| `stats` | `*StatsConfig` |
| `reverse` | `*ReverseConfig` |
| `fakeDns` | `*FakeDNSConfig` |
| `observatory` | `*ObservatoryConfig` |
| `burstObservatory` | `*BurstObservatoryConfig` |
| `version` | `*VersionConfig` |

## SimpleRule

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/xray.go#L680)

| فیلد JSON | نوع در سورس |
|---|---|
| `ruleTag` | `string` |
| `domain` | `*StringList` |
| `domains` | `*StringList` |

## DokodemoConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/dokodemo.go#L10)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `portMap` | `map[string]string` |
| `network` | `*NetworkList` |
| `followRedirect` | `bool` |
| `userLevel` | `uint32` |

## HTTPAccount

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/http.go#L13)

| فیلد JSON | نوع در سورس |
|---|---|
| `user` | `string` |
| `pass` | `string` |

## HTTPServerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/http.go#L25)

| فیلد JSON | نوع در سورس |
|---|---|
| `accounts` | `[]*HTTPAccount` |
| `allowTransparent` | `bool` |
| `userLevel` | `uint32` |

## HTTPRemoteConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/http.go#L47)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `users` | `[]json.RawMessage` |

## HTTPClientConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/http.go#L53)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `uint32` |
| `email` | `string` |
| `user` | `string` |
| `pass` | `string` |
| `servers` | `[]*HTTPRemoteConfig` |
| `headers` | `map[string]string` |

## SocksAccount

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/socks.go#L13)

| فیلد JSON | نوع در سورس |
|---|---|
| `user` | `string` |
| `pass` | `string` |

## SocksServerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/socks.go#L30)

| فیلد JSON | نوع در سورس |
|---|---|
| `auth` | `string` |
| `accounts` | `[]*SocksAccount` |
| `udp` | `bool` |
| `ip` | `*Address` |
| `userLevel` | `uint32` |

## SocksRemoteConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/socks.go#L66)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `users` | `[]json.RawMessage` |

## SocksClientConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/socks.go#L72)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `uint32` |
| `email` | `string` |
| `user` | `string` |
| `pass` | `string` |
| `servers` | `[]*SocksRemoteConfig` |

## ShadowsocksUserConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/shadowsocks.go#L33)

| فیلد JSON | نوع در سورس |
|---|---|
| `method` | `string` |
| `password` | `string` |
| `level` | `byte` |
| `email` | `string` |
| `address` | `*Address` |
| `port` | `uint16` |

## ShadowsocksServerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/shadowsocks.go#L42)

| فیلد JSON | نوع در سورس |
|---|---|
| `method` | `string` |
| `password` | `string` |
| `level` | `byte` |
| `email` | `string` |
| `clients` | `[]*ShadowsocksUserConfig` |
| `network` | `*NetworkList` |

## ShadowsocksServerTarget

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/shadowsocks.go#L161)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `byte` |
| `email` | `string` |
| `method` | `string` |
| `password` | `string` |
| `uot` | `bool` |
| `uotVersion` | `int` |

## ShadowsocksClientConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/shadowsocks.go#L172)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `byte` |
| `email` | `string` |
| `method` | `string` |
| `password` | `string` |
| `uot` | `bool` |
| `uotVersion` | `int` |
| `servers` | `[]*ShadowsocksServerTarget` |

## VMessAccount

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vmess.go#L17)

| فیلد JSON | نوع در سورس |
|---|---|
| `id` | `string` |
| `security` | `string` |
| `experiments` | `string` |

## VMessDefaultConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vmess.go#L49)

| فیلد JSON | نوع در سورس |
|---|---|
| `level` | `byte` |

## VMessInboundConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vmess.go#L60)

| فیلد JSON | نوع در سورس |
|---|---|
| `clients` | `[]json.RawMessage` |
| `default` | `*VMessDefaultConfig` |

## VMessOutboundTarget

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vmess.go#L99)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `users` | `[]json.RawMessage` |

## VMessOutboundConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vmess.go#L105)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `uint32` |
| `email` | `string` |
| `id` | `string` |
| `security` | `string` |
| `experiments` | `string` |
| `vnext` | `[]*VMessOutboundTarget` |

## VLessInboundFallback

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vless.go#L23)

| فیلد JSON | نوع در سورس |
|---|---|
| `name` | `string` |
| `alpn` | `string` |
| `path` | `string` |
| `type` | `string` |
| `dest` | `json.RawMessage` |
| `xver` | `uint64` |

## VLessInboundConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vless.go#L32)

| فیلد JSON | نوع در سورس |
|---|---|
| `clients` | `[]json.RawMessage` |
| `decryption` | `string` |
| `fallbacks` | `[]*VLessInboundFallback` |
| `flow` | `string` |
| `testseed` | `[]uint32` |

## VLessReverseConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vless.go#L205)

| فیلد JSON | نوع در سورس |
|---|---|
| `tag` | `string` |
| `sniffing` | `*SniffingConfig` |

## VLessOutboundVnext

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vless.go#L227)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `users` | `[]json.RawMessage` |

## VLessOutboundConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/vless.go#L233)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `uint32` |
| `email` | `string` |
| `id` | `string` |
| `flow` | `string` |
| `seed` | `string` |
| `encryption` | `string` |
| `reverse` | `*VLessReverseConfig` |
| `testpre` | `uint32` |
| `testseed` | `[]uint32` |
| `vnext` | `[]*VLessOutboundVnext` |

## TrojanServerTarget

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/trojan.go#L20)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `byte` |
| `email` | `string` |
| `password` | `string` |
| `flow` | `string` |

## TrojanClientConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/trojan.go#L30)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `level` | `byte` |
| `email` | `string` |
| `password` | `string` |
| `flow` | `string` |
| `servers` | `[]*TrojanServerTarget` |

## TrojanInboundFallback

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/trojan.go#L95)

| فیلد JSON | نوع در سورس |
|---|---|
| `name` | `string` |
| `alpn` | `string` |
| `path` | `string` |
| `type` | `string` |
| `dest` | `json.RawMessage` |
| `xver` | `uint64` |

## TrojanUserConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/trojan.go#L105)

| فیلد JSON | نوع در سورس |
|---|---|
| `password` | `string` |
| `level` | `byte` |
| `email` | `string` |
| `flow` | `string` |

## TrojanServerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/trojan.go#L113)

| فیلد JSON | نوع در سورس |
|---|---|
| `clients` | `[]*TrojanUserConfig` |
| `fallbacks` | `[]*TrojanInboundFallback` |

## WireGuardPeerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/wireguard.go#L13)

| فیلد JSON | نوع در سورس |
|---|---|
| `publicKey` | `string` |
| `preSharedKey` | `string` |
| `endpoint` | `string` |
| `keepAlive` | `uint32` |
| `allowedIPs` | `[]string` |

## WireGuardConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/wireguard.go#L51)

| فیلد JSON | نوع در سورس |
|---|---|
| `noKernelTun` | `bool` |
| `secretKey` | `string` |
| `address` | `[]string` |
| `peers` | `[]*WireGuardPeerConfig` |
| `mtu` | `int32` |
| `workers` | `int32` |
| `reserved` | `[]byte` |
| `domainStrategy` | `string` |

## HysteriaClientConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/hysteria.go#L12)

| فیلد JSON | نوع در سورس |
|---|---|
| `version` | `int32` |
| `address` | `*Address` |
| `port` | `uint16` |

## HysteriaUserConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/hysteria.go#L33)

| فیلد JSON | نوع در سورس |
|---|---|
| `auth` | `string` |
| `level` | `uint32` |
| `email` | `string` |

## HysteriaServerConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/hysteria.go#L39)

| فیلد JSON | نوع در سورس |
|---|---|
| `version` | `int32` |
| `clients` | `[]*HysteriaUserConfig` |

## TunConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/tun.go#L8)

| فیلد JSON | نوع در سورس |
|---|---|
| `name` | `string` |
| `MTU` | `uint32` |
| `userLevel` | `uint32` |

## KCPConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L55)

| فیلد JSON | نوع در سورس |
|---|---|
| `mtu` | `*uint32` |
| `tti` | `*uint32` |
| `uplinkCapacity` | `*uint32` |
| `downlinkCapacity` | `*uint32` |
| `congestion` | `*bool` |
| `readBufferSize` | `*uint32` |
| `writeBufferSize` | `*uint32` |
| `header` | `json.RawMessage` |
| `seed` | `*string` |

## TCPConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L117)

| فیلد JSON | نوع در سورس |
|---|---|
| `header` | `json.RawMessage` |
| `acceptProxyProtocol` | `bool` |

## WebSocketConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L142)

| فیلد JSON | نوع در سورس |
|---|---|
| `host` | `string` |
| `path` | `string` |
| `headers` | `map[string]string` |
| `acceptProxyProtocol` | `bool` |
| `heartbeatPeriod` | `uint32` |

## HttpUpgradeConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L184)

| فیلد JSON | نوع در سورس |
|---|---|
| `host` | `string` |
| `path` | `string` |
| `headers` | `map[string]string` |
| `acceptProxyProtocol` | `bool` |

## SplitHTTPConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L220)

| فیلد JSON | نوع در سورس |
|---|---|
| `host` | `string` |
| `path` | `string` |
| `mode` | `string` |
| `headers` | `map[string]string` |
| `xPaddingBytes` | `Int32Range` |
| `xPaddingObfsMode` | `bool` |
| `xPaddingKey` | `string` |
| `xPaddingHeader` | `string` |
| `xPaddingPlacement` | `string` |
| `xPaddingMethod` | `string` |
| `uplinkHTTPMethod` | `string` |
| `sessionPlacement` | `string` |
| `sessionKey` | `string` |
| `seqPlacement` | `string` |
| `seqKey` | `string` |
| `uplinkDataPlacement` | `string` |
| `uplinkDataKey` | `string` |
| `uplinkChunkSize` | `Int32Range` |
| `noGRPCHeader` | `bool` |
| `noSSEHeader` | `bool` |
| `scMaxEachPostBytes` | `Int32Range` |
| `scMinPostsIntervalMs` | `Int32Range` |
| `scMaxBufferedPosts` | `int64` |
| `scStreamUpServerSecs` | `Int32Range` |
| `serverMaxHeaderBytes` | `int32` |
| `xmux` | `XmuxConfig` |
| `downloadSettings` | `*StreamConfig` |
| `extra` | `json.RawMessage` |

## XmuxConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L251)

| فیلد JSON | نوع در سورس |
|---|---|
| `maxConcurrency` | `Int32Range` |
| `maxConnections` | `Int32Range` |
| `cMaxReuseTimes` | `Int32Range` |
| `hMaxRequestTimes` | `Int32Range` |
| `hMaxReusableSecs` | `Int32Range` |
| `hKeepAlivePeriod` | `int64` |

## UdpHop

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L503)

| فیلد JSON | نوع در سورس |
|---|---|
| `ports` | `json.RawMessage` |
| `interval` | `*Int32Range` |

## Masquerade

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L508)

| فیلد JSON | نوع در سورس |
|---|---|
| `type` | `string` |
| `dir` | `string` |
| `url` | `string` |
| `rewriteHost` | `bool` |
| `insecure` | `bool` |
| `content` | `string` |
| `headers` | `map[string]string` |
| `statusCode` | `int32` |

## HysteriaConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L522)

| فیلد JSON | نوع در سورس |
|---|---|
| `version` | `int32` |
| `auth` | `string` |
| `congestion` | `*string` |
| `up` | `*Bandwidth` |
| `down` | `*Bandwidth` |
| `udphop` | `*UdpHop` |
| `udpIdleTimeout` | `int64` |
| `masquerade` | `Masquerade` |

## TLSCertConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L578)

| فیلد JSON | نوع در سورس |
|---|---|
| `certificateFile` | `string` |
| `certificate` | `[]string` |
| `keyFile` | `string` |
| `key` | `[]string` |
| `usage` | `string` |
| `ocspStapling` | `uint64` |
| `oneTimeLoading` | `bool` |
| `buildChain` | `bool` |

## QuicParamsConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L630)

| فیلد JSON | نوع در سورس |
|---|---|
| `congestion` | `string` |
| `debug` | `bool` |
| `brutalUp` | `Bandwidth` |
| `brutalDown` | `Bandwidth` |
| `udpHop` | `UdpHop` |
| `initStreamReceiveWindow` | `uint64` |
| `maxStreamReceiveWindow` | `uint64` |
| `initConnectionReceiveWindow` | `uint64` |
| `maxConnectionReceiveWindow` | `uint64` |
| `maxIdleTimeout` | `int64` |
| `keepAlivePeriod` | `int64` |
| `disablePathMTUDiscovery` | `bool` |
| `maxIncomingStreams` | `int64` |

## TLSConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L646)

| فیلد JSON | نوع در سورس |
|---|---|
| `allowInsecure` | `bool` |
| `certificates` | `[]*TLSCertConfig` |
| `serverName` | `string` |
| `alpn` | `*StringList` |
| `enableSessionResumption` | `bool` |
| `disableSystemRoot` | `bool` |
| `minVersion` | `string` |
| `maxVersion` | `string` |
| `cipherSuites` | `string` |
| `fingerprint` | `string` |
| `rejectUnknownSni` | `bool` |
| `curvePreferences` | `*StringList` |
| `masterKeyLog` | `string` |
| `pinnedPeerCertSha256` | `string` |
| `verifyPeerCertByName` | `string` |
| `verifyPeerCertInNames` | `[]string` |
| `echServerKeys` | `string` |
| `echConfigList` | `string` |
| `echForceQuery` | `string` |
| `echSockopt` | `*SocketConfig` |

## REALITYConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L780)

| فیلد JSON | نوع در سورس |
|---|---|
| `masterKeyLog` | `string` |
| `show` | `bool` |
| `target` | `json.RawMessage` |
| `dest` | `json.RawMessage` |
| `type` | `string` |
| `xver` | `uint64` |
| `serverNames` | `[]string` |
| `privateKey` | `string` |
| `minClientVer` | `string` |
| `maxClientVer` | `string` |
| `maxTimeDiff` | `uint64` |
| `shortIds` | `[]string` |
| `mldsa65Seed` | `string` |
| `limitFallbackUpload` | `LimitFallback` |
| `limitFallbackDownload` | `LimitFallback` |
| `fingerprint` | `string` |
| `serverName` | `string` |
| `password` | `string` |
| `publicKey` | `string` |
| `shortId` | `string` |
| `mldsa65Verify` | `string` |
| `spiderX` | `string` |

## CustomSockoptConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1026)

| فیلد JSON | نوع در سورس |
|---|---|
| `system` | `string` |
| `network` | `string` |
| `level` | `string` |
| `opt` | `string` |
| `value` | `string` |
| `type` | `string` |

## HappyEyeballsConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1035)

| فیلد JSON | نوع در سورس |
|---|---|
| `prioritizeIPv6` | `bool` |
| `tryDelayMs` | `uint64` |
| `interleave` | `uint32` |
| `maxConcurrentTry` | `uint32` |

## SocketConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1059)

| فیلد JSON | نوع در سورس |
|---|---|
| `mark` | `int32` |
| `tcpFastOpen` | `interface{}` |
| `tproxy` | `string` |
| `acceptProxyProtocol` | `bool` |
| `domainStrategy` | `string` |
| `dialerProxy` | `string` |
| `tcpKeepAliveInterval` | `int32` |
| `tcpKeepAliveIdle` | `int32` |
| `tcpCongestion` | `string` |
| `tcpWindowClamp` | `int32` |
| `tcpMaxSeg` | `int32` |
| `penetrate` | `bool` |
| `tcpUserTimeout` | `int32` |
| `v6only` | `bool` |
| `interface` | `string` |
| `tcpMptcp` | `bool` |
| `customSockopt` | `[]*CustomSockoptConfig` |
| `addressPortStrategy` | `string` |
| `happyEyeballs` | `*HappyEyeballsConfig` |
| `trustedXForwardedFor` | `[]string` |

## TCPItem

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1262)

| فیلد JSON | نوع در سورس |
|---|---|
| `delay` | `Int32Range` |
| `rand` | `int32` |
| `randRange` | `*Int32Range` |
| `type` | `string` |
| `packet` | `json.RawMessage` |

## HeaderCustomTCP

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1270)

| فیلد JSON | نوع در سورس |
|---|---|
| `clients` | `[][]TCPItem` |
| `servers` | `[][]TCPItem` |
| `errors` | `[][]TCPItem` |

## FragmentMask

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1383)

| فیلد JSON | نوع در سورس |
|---|---|
| `packets` | `string` |
| `length` | `Int32Range` |
| `delay` | `Int32Range` |
| `maxSplit` | `Int32Range` |

## NoiseItem

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1427)

| فیلد JSON | نوع در سورس |
|---|---|
| `rand` | `Int32Range` |
| `randRange` | `*Int32Range` |
| `type` | `string` |
| `packet` | `json.RawMessage` |
| `delay` | `Int32Range` |

## NoiseMask

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1435)

| فیلد JSON | نوع در سورس |
|---|---|
| `reset` | `Int32Range` |
| `noise` | `[]NoiseItem` |

## UDPItem

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1477)

| فیلد JSON | نوع در سورس |
|---|---|
| `rand` | `int32` |
| `randRange` | `*Int32Range` |
| `type` | `string` |
| `packet` | `json.RawMessage` |

## HeaderCustomUDP

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1484)

| فیلد JSON | نوع در سورس |
|---|---|
| `client` | `[]UDPItem` |
| `server` | `[]UDPItem` |

## Dns

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1547)

| فیلد JSON | نوع در سورس |
|---|---|
| `domain` | `string` |

## Aes128Gcm

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1598)

| فیلد JSON | نوع در سورس |
|---|---|
| `password` | `string` |

## Salamander

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1608)

| فیلد JSON | نوع در سورس |
|---|---|
| `password` | `string` |

## Sudoku

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1618)

| فیلد JSON | نوع در سورس |
|---|---|
| `password` | `string` |
| `ascii` | `string` |
| `customTable` | `string` |
| `custom_table` | `string` |
| `customTables` | `[]string` |
| `custom_tables` | `[]string` |
| `paddingMin` | `uint32` |
| `padding_min` | `uint32` |
| `paddingMax` | `uint32` |
| `padding_max` | `uint32` |

## Xdns

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1662)

| فیلد JSON | نوع در سورس |
|---|---|
| `domain` | `string` |

## Xicmp

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1676)

| فیلد JSON | نوع در سورس |
|---|---|
| `listenIp` | `string` |
| `id` | `uint16` |

## Mask

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1694)

| فیلد JSON | نوع در سورس |
|---|---|
| `type` | `string` |
| `settings` | `*json.RawMessage` |

## FinalMask

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1720)

| فیلد JSON | نوع در سورس |
|---|---|
| `tcp` | `[]Mask` |
| `udp` | `[]Mask` |
| `quicParams` | `*QuicParamsConfig` |

## StreamConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1726)

| فیلد JSON | نوع در سورس |
|---|---|
| `address` | `*Address` |
| `port` | `uint16` |
| `network` | `*TransportProtocol` |
| `security` | `string` |
| `finalmask` | `*FinalMask` |
| `tlsSettings` | `*TLSConfig` |
| `realitySettings` | `*REALITYConfig` |
| `rawSettings` | `*TCPConfig` |
| `tcpSettings` | `*TCPConfig` |
| `xhttpSettings` | `*SplitHTTPConfig` |
| `splithttpSettings` | `*SplitHTTPConfig` |
| `kcpSettings` | `*KCPConfig` |
| `grpcSettings` | `*GRPCConfig` |
| `wsSettings` | `*WebSocketConfig` |
| `httpupgradeSettings` | `*HttpUpgradeConfig` |
| `hysteriaSettings` | `*HysteriaConfig` |
| `sockopt` | `*SocketConfig` |

## ProxyConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_internet.go#L1990)

| فیلد JSON | نوع در سورس |
|---|---|
| `tag` | `string` |
| `transportLayer` | `bool` |

## AuthenticatorRequest

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_authenticators.go#L19)

| فیلد JSON | نوع در سورس |
|---|---|
| `version` | `string` |
| `method` | `string` |
| `path` | `StringList` |
| `headers` | `map[string]*StringList` |

## AuthenticatorResponse

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_authenticators.go#L120)

| فیلد JSON | نوع در سورس |
|---|---|
| `version` | `string` |
| `status` | `string` |
| `reason` | `string` |
| `headers` | `map[string]*StringList` |

## Authenticator

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/transport_authenticators.go#L188)

| فیلد JSON | نوع در سورس |
|---|---|
| `request` | `AuthenticatorRequest` |
| `response` | `AuthenticatorResponse` |

## GRPCConfig

[تعریف در سورس](https://github.com/XTLS/Xray-core/blob/v26.3.27/infra/conf/grpc.go#L8)

| فیلد JSON | نوع در سورس |
|---|---|
| `authority` | `string` |
| `serviceName` | `string` |
| `multiMode` | `bool` |
| `idle_timeout` | `int32` |
| `health_check_timeout` | `int32` |
| `permit_without_stream` | `bool` |
| `initial_windows_size` | `int32` |
| `user_agent` | `string` |
