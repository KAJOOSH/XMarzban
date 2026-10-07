# پشتیبانی Xray v26.3.27 در مرزبان

مبنای بررسی [تگ v26.3.27](https://github.com/XTLS/Xray-core/releases/tag/v26.3.27) و commit برابر d2758a023cd7f4174a5a5fa4ff66e487d4342ba0 است. Docker باینری رسمی همین نسخه را دریافت و SHA256 آن را کنترل می‌کند. [فهرست ۷۷ ساختار و فیلدهای JSON](xray-v26.3.27-fields.fa.md) نوع و محل تعریف هر فیلد را در سورس دارد. این فهرست JSON Schema نیست؛ قواعد اجرایی Build نیز لازم‌اند.

## پیش‌فرض‌های سرور

xray_config.json شامل ۱۲۵ ورودی است: ۱۱۸ ورودی مدیریت‌شده و ۷ ورودی ایستا. تمام گزینه‌ها هم‌زمان قابل فعال‌کردن نیستند؛ حالت‌های XHTTP، security و نوع ترنسپورت ترکیب‌های متفاوتی دارند.

| پروتکل | تنظیمات و مدیریت |
|---|---|
| VMess | clients با id، alterId، security، level و email؛ مدیریت API |
| VLESS | clients، decryption و fallbacks؛ encryption کاربر باید با decryption سرور سازگار باشد؛ reverse در شکل سادهٔ جدید خروجی |
| Trojan | clients با password، level و email و fallbacks |
| Shadowsocks | method، password، network و clients؛ مدیریت حساب فعلی برای AEAD معمولی است؛ روش‌های 2022 هنوز مدیریت جداگانه می‌خواهند |
| Hysteria | version=2 و clients با auth؛ ترنسپورت hysteria و TLS لازم است؛ افزودن/حذف حساب API دارد |
| HTTP | accounts، allowTransparent و userLevel؛ نمونهٔ RAW و TLS |
| SOCKS / Mixed | auth، accounts، udp، ip و userLevel؛ حساب ایستا |
| tunnel / dokodemo-door | address، port، network، followRedirect و userLevel؛ مقصد نمونه 127.0.0.1:18090 |
| WireGuard | secretKey، address، peers، mtu، reserved و noKernelTun؛ کلید نصب تصادفی |
| TUN | name و MTU؛ دستگاه /dev/net/tun، NET_ADMIN و routing سیستم عامل لازم است |

HTTP، SOCKS، Mixed، tunnel و TUN حساب قابل مدیریت با API کاربران مرزبان ندارند؛ کانفیگ آن‌ها در هسته نگهداری می‌شود. جزئیات همهٔ فیلدها در فهرست تنظیمات آمده است.

برای هر یک از VMess، VLESS، Trojan و Shadowsocks ۲۹ نمونه وجود دارد؛ چهارده نمونهٔ پایه عبارت‌اند از: RAW ساده/TLS/REALITY، WS با TLS، HTTPUpgrade با TLS، gRPC با TLS، mKCP، Hysteria با TLS، XHTTP packet-up، XHTTP stream-up روی H2، XHTTP stream-one روی H2 و H3، XHTTP با REALITY و gRPC با REALITY. پانزده نمونهٔ اضافه برای هر پروتکل شامل ماسک‌های mKCP، RAW با Header HTTP، XHTTP با header/cookie، TLS با ECH و REALITY با MLDSA65 است. Hysteria 2 بومی و WireGuard هرکدام یک ورودی مستقل دارند.

## تفاوت ترنسپورت‌ها

| ترنسپورت | تنظیمات و تفاوت‌ها |
|---|---|
| RAW / TCP | header نوع none یا HTTP؛ request سمت کاربر، response سمت سرور؛ acceptProxyProtocol سروری |
| WS | path، host، headers و heartbeatPeriod |
| HTTPUpgrade | path، host و headers؛ در اشتراک به WS تبدیل نمی‌شود |
| gRPC | serviceName، authority، multiMode، زمان‌بندی، پنجره و سلامت اتصال |
| mKCP | mtu، tti، ظرفیت‌ها، congestion و بافرها؛ header/seed حذف شده، ماسک در finalmask.udp |
| XHTTP | host، path، mode، extra، downloadSettings، xmux، padding، session/seq، uplink و محدودیت‌های ارسال |
| Hysteria | version=2، auth، congestion، udpHop، udpIdleTimeout و masquerade؛ TLS و ماسک Salamander در finalmask |

نام‌های tcp/raw، splithttp/xhttp، mkcp/kcp و websocket/ws یکسان‌سازی می‌شوند. http/h2/h3/quic قدیمی در این تگ حذف شده‌اند. H3 فعلی با XHTTP و ALPN تنظیم می‌شود. REALITY فقط روی RAW، XHTTP و gRPC پذیرفته می‌شود. mKCP نمونه از mkcp-aes128gcm استفاده می‌کند. Shadowsocks غیر RAW فقط network=tcp دارد تا سوکت UDP بومی با ترنسپورت UDP روی یک پورت تداخل نکند.

## تنظیمات کاربر و اشتراک

گواهی localhost، کلید TLS، REALITY، WireGuard و رمزهای مشترک هنگام نصب ساخته می‌شوند. pin گواهی TLS به اشتراک Xray می‌رود. allowInsecure در این تگ بعد از ۱ ژوئن ۲۰۲۶ حذف می‌شود؛ نمونهٔ محلی از pin استفاده می‌کند. privateKey، mldsa65Seed، کلید گواهی، echServerKeys، target و sockopt سرور به کاربر منتقل نمی‌شوند. publicKey/password، shortId، fingerprint، mldsa65Verify، echConfigList و قیود تأیید گواهی سمت کلاینت حفظ می‌شوند. downloadSettings تو در تو نیز پاک‌سازی می‌شود.

در پنجرهٔ میزبان دو کادر JSON برای xray_stream_settings و xray_protocol_settings اضافه شده‌اند و در ستون JSON پایگاه داده ذخیره می‌شوند. ترتیب اولویت: جریان استخراج‌شده از سرور، سپس host/path/SNI معمول میزبان، سپس JSON پیشرفتهٔ میزبان. اشیا بازگشتی ادغام و آرایه‌ها جایگزین می‌شوند. کادر پروتکل encryption و reverse مربوط به VLESS را می‌پذیرد؛ packetEncoding جزو تنظیمات این تگ نیست.

در XHTTP، extra جای فیلدهای پیشرفتهٔ بیرونی را می‌گیرد؛ host/path/mode از بیرون می‌آیند. downloadSettings می‌تواند آدرس، پورت، security و sockopt مستقل کلاینت داشته باشد. finalmask کامل در JSON Xray حفظ می‌شود. کانفیگ سرور قبل از ذخیره با Xray run -test و کاربران موجود اعتبارسنجی می‌شود.

| قالب | محدوده |
|---|---|
| v2ray-json | مسیر اصلی برای جزئیات کامل جریان کلاینت Xray |
| v2ray / URI | پارامترهای قابل نمایش در لینک؛ پذیرش آن‌ها به برنامهٔ واردکننده وابسته است؛ reverse و Shadowsocks پیشرفته فقط JSON |
| sing-box | RAW، WS، gRPC، HTTPUpgrade و Hysteria 2 بومی در محدودهٔ قابل تبدیل |
| clash / clash-meta | RAW، WS و gRPC؛ Meta همچنین REALITY و Hysteria 2 بومی قابل تبدیل |
| outline | Shadowsocks سادهٔ RAW بدون TLS و ماسک پیشرفته |

گزینه‌های غیرقابل تبدیل باعث حذف آن مسیر از قالب دیگر می‌شوند؛ قیود TLS بی‌صدا حذف نمی‌شوند. به همین دلیل نمونه‌های TLS محلی دارای pin در بعضی قالب‌ها دیده نمی‌شوند. پشتیبانی کامل Xray به معنی پشتیبانی تمام امکانات آن در هسته‌های دیگر نیست. API احراز هویت‌شدهٔ /api/core/capabilities فهرست فیلدها و محدودهٔ قالب‌ها را ارائه می‌کند.

## نتیجهٔ تست

۱۰ تست unittest با باینری رسمی، سرور و کلاینت جدا و سرویس echo محلی گذشت. ۱۲۵ ورودی پیش‌فرض TCP و ۹۶ مسیر UDP پشتیبانی‌شده آزمایش شدند. افزودن حساب Hysteria با API و رد احراز هویت پس از حذف، دو سناریوی اضافه‌اند. [خروجی ۱۲۷ سناریوی موفق](../scripts/xray-26327-results.json) جزئیات را دارد. UDP در Shadowsocks غیر RAW فعال نیست؛ SOCKS/Mixed و tunnel ایستا در این اجرا فقط TCP آزمایش شدند. WireGuard و عبور واقعی بسته از TUN روی TCP و UDP بررسی شدند.

تست API شامل داشبورد، آماده‌بودن هسته، ۱۱۸ ورودی مدیریت‌شده، ماندگاری JSON میزبان در SQLite، اعتبارسنجی ۳۵۴ کانفیگ اشتراک با Xray، تولید شش قالب و چرخهٔ ساخت/غیرفعال‌سازی/فعال‌سازی/ابطال/حذف کاربر و حفظ کانفیگ سالم بعد از ورودی نامعتبر است. قالب‌های دیگر تولید و parse شدند؛ اتصال با باینری sing-box، Mihomo یا برنامه‌های موبایل آزمایش نشده است. همهٔ مقدارهای ممکن و سیستم‌عامل‌ها پوشش داده نشده‌اند.

## اجرای Docker محلی

داشبورد: https://localhost:8000/dashboard/؛ گواهی محلی است. اطلاعات ورود در local-admin.json خارج از Git و در volume ذخیره شده است. پورت‌ها فقط روی loopback منتشرند: 8000، 12080–12086 و 12100–12216 روی TCP/UDP. آدرس میزبان‌های پیش‌فرض این نصب localhost است. TUN داخل کانتینر ساخته می‌شود و routing واقعی باید تنظیم شود.

دستور راه‌اندازی: rtk docker compose -p marzban-xray-local -f docker-compose.local.yml up -d --build

دستور تست API: rtk docker exec marzban-xray-local-marzban-1 python scripts/test_local_api.py

دستور ماتریس: rtk docker run --rm --cap-add NET_ADMIN --device /dev/net/tun --mount type=bind,source=D:/source/repos/Marzban,target=/code marzban-xray:26.3.27-local python -m scripts.test_xray_26327

scripts/init_xray_defaults.py placeholderها را با مقادیر نصب جایگزین می‌کند؛ راه‌اندازی معمول تنظیمات موجود را بازنویسی نمی‌کند. --refresh-presets نمونه‌ها را با backup قبلی جایگزین می‌کند. داده‌ها در volume marzban-xray-local_marzban-local-data حفظ می‌شوند. برای استقرار عمومی دامنه، گواهی معتبر، آدرس اشتراک، مقصد tunnel، routing و پورت‌ها باید برای سرور واقعی تنظیم شوند.

## اصلاح واردکردن اشتراک در v2rayN و WireGuard

اشتراک معمول برای v2rayN جدید به‌صورت JSON کامل ارسال می‌شود. مسیر صریح /v2ray-json مستقل از User-Agent همین خروجی را می‌دهد. VMess با REALITY، mKCP و XHTTP در لینک استاندارد URI ارائه می‌شود؛ قالب قدیمی Base64 VMess بعضی فیلدها را هنگام ورود به v2rayN حذف می‌کرد. ترنسپورت Hysteria برای VMess/VLESS/Trojan/SS فقط در JSON ارائه می‌شود، چون واردکنندهٔ لینک آن را به RAW تبدیل می‌کرد.

WireGuard اکنون پروتکل قابل انتخاب کاربر است و JSON Xray و URI اختصاصی WireGuard دارد. کلید هر کاربر مستقل است؛ کلید خصوصی سرور منتقل نمی‌شود. آدرس‌های تونل از شناسهٔ کاربر ساخته می‌شوند. اضافه/حذف/تغییر peerها با restart هسته و نودها اعمال می‌شود؛ این کار اتصال‌های جاری را قطع می‌کند. ابطال اشتراک کلید WireGuard را عوض می‌کند و غیرفعال/حذف شدن کاربر peer او را از سرور حذف می‌کند. محدودهٔ آدرس IPv4 فعلی برای شناسه‌های ۱ تا ۶۴۵۱۵ است.

Xray v26.3.27 شمارندهٔ ترافیک اختصاصی هر peer WireGuard را با API ارائه نمی‌کند؛ حسابداری و محدودیت حجمی مستقل WireGuard در این تغییر پیاده نشده است. غیرفعال‌سازی و ابطال کلید اعمال می‌شود. IPv4 اولویت دارد و IPv6 حالت fallback است. DNS کلاینت WireGuard ابتدا از resolver سیستم استفاده می‌کند تا قبل از تشکیل تونل، پرس‌وجوی DNS داخل خود تونل حلقه نشود.

در ویندوز، همان باینری Xray v26.3.27 نصب‌شده همراه v2rayN برای دریافت اشتراک JSON و اتصال HTTPS واقعی از طریق Docker استفاده شد. چرخهٔ WireGuard در شش مرحلهٔ ساخت، غیرفعال، فعال، ابطال کلید قبلی، کلید جدید و حذف با اتصال/رد اتصال واقعی گذشت. WireGuard در نمونهٔ Docker روی 0.0.0.0 گوش می‌دهد تا نشر پورت UDP از میزبان به آن برسد؛ نشر پورت در خود Docker همچنان محدود به loopback است. اعتبارسنجی مجدد تنظیمات، نام رابط TUN تحت مالکیت هستهٔ فعال را فقط در اجرای موقت تست جایگزین می‌کند تا با رابط جاری تداخل نکند.

تست مرحلهٔ نخست اشتراک: ۵۸ از ۵۸ کانفیگ با باینری ویندوز اعتبارسنجی شدند و ۵۸ از ۵۸ اتصال HTTPS واقعی برقرار کردند؛ [گزارش بدون کلیدها و لینک اشتراک](xray-windows-subscription-results.json). تست ذخیرهٔ کانفیگ سالم با TUN فعال نیز در تست API گذشت.

## گسترش نمونه‌های کلاینت

[راهنمای نمونه‌های کلاینت](xray-client-profiles.fa.md) اصلاح User-Agent بدون نسخه، تبدیل گزینه‌های قدیمی mKCP به finalmask، ورودی‌های جدید و پروفایل‌های پیشرفته را توضیح می‌دهد. نصب فعلی ۱۲۵ ورودی سرور، ۱۱۸ ورودی مدیریت‌شده و ۳۵۴ کانفیگ اشتراک دارد. نتایج ۵۸ کانفیگ بالا مربوط به مرحلهٔ قبلی هستند؛ گزارش جدید در xray-client-fields-results.json و xray-windows-extended-results.json ثبت می‌شود.
