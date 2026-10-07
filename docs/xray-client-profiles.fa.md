# نمونه‌های کلاینت Xray v26.3.27

علت نمایش ۴۲ کانفیگ در لینک قبلی، تشخیص User-Agent بدون شمارهٔ نسخه بود: v2rayN خروجی URI می‌گرفت، ولی v2rayN/7.22.6 خروجی کامل JSON. تشخیص اکنون نام بدون نسخه و حروف متفاوت را هم می‌پذیرد. نسخه‌های شناخته‌شدهٔ قدیمی‌تر از 6.40 همچنان قالب قدیمی می‌گیرند. مسیر /v2ray-json مستقل از User-Agent است.

در نصب محلی، ۱۲۵ ورودی سرور وجود دارد: ۱۱۸ ورودی قابل مدیریت کاربر و ۷ ورودی زیرساختی. برای هر ورودی قابل مدیریت، یک نمونهٔ پایه و دو نمونهٔ advanced-a و advanced-b در میزبان‌ها تعریف شده است؛ اشتراک کاربر شامل ۳۵۴ کانفیگ است. VMess، VLESS، Trojan و Shadowsocks هرکدام ۸۷ کانفیگ دارند؛ Hysteria 2 و WireGuard هرکدام ۳ کانفیگ. اسم هر کانفیگ، tag کامل ورودی و نام پروفایل را نشان می‌دهد.

صفحهٔ مرورگر و دکمهٔ «Copy configs» از USE_CUSTOM_JSON_DEFAULT پیروی می‌کنند: در حالت خاموش فقط لینک‌های URI موجود نمایش داده و کپی می‌شوند؛ نمونه‌های اختصاصی JSON نمایش داده نمی‌شوند. در حالت روشن تمام کانفیگ‌های JSON نمایش داده و کپی می‌شوند. نصب محلی اکنون این گزینه را خاموش دارد. مسیر صریح /v2ray-json و تشخیص اختصاصی v2rayN همچنان مستقل از نمایش صفحه هستند.

## گزینه‌های تصویر mKCP

فیلد kcpSettings.header و seed در این نسخه حذف شده‌اند. معادل‌های پشتیبانی‌شده در finalmask.udp هستند:

| فهرست قدیمی کلاینت | ماسک Xray فعلی |
|---|---|
| srtp | header-srtp |
| utp | header-utp |
| wechat-video | header-wechat |
| dtls | header-dtls |
| wireguard | header-wireguard |
| dns | header-dns |

این‌ها ماسک ترنسپورت mKCP هستند؛ header-wireguard به معنی پروتکل مستقل WireGuard نیست. نمونه‌های mkcp-original، mkcp-aes128gcm، header-custom، salamander و noise نیز تعریف شده‌اند. زنجیرهٔ ماسک سمت سرور و کلاینت تطبیق دارد. تنظیمات JSON سفارشی در فرم قدیمی Header کلاینت بازتاب کامل ندارد؛ برای مشاهده باید JSON کانفیگ سفارشی یا فایل اجرای هسته را باز کرد. تغییر دادن dropdown قدیمی به یک Header حذف‌شده، کانفیگ جدید را خراب می‌کند.

## تنظیمات نمونه‌ها

| قسمت | نمونه‌های موجود |
|---|---|
| VMess | auto، aes-128-gcm و chacha20-poly1305؛ level و email |
| VLESS | encryption=none؛ level و email؛ هویت کاربر حفظ می‌شود |
| Trojan | level و email؛ رمز حساب مستقل |
| Shadowsocks | level، email و UOT خاموش/روشن؛ روش رمزگذاری حساب حفظ می‌شود |
| WireGuard | MTU 1280/1380/1420، workers، reserved، noKernelTun و domainStrategy |
| RAW | header=none و HTTP با request/response منطبق |
| WS | headers، User-Agent، heartbeatPeriod |
| HTTPUpgrade | headers و User-Agent |
| gRPC | multiMode، authority، serviceName، idle/health timeout، permit_without_stream، initial_windows_size و user_agent |
| mKCP | mtu، tti، ظرفیت‌ها، congestion، بافرها و ماسک‌ها |
| XHTTP | packet-up/stream-up/stream-one، H2/H3، path/header/cookie برای session/seq/data، padding، headers، xmux، extra و downloadSettings مستقل |
| TLS | SNI، ALPN، fingerprint، min/max version، session resumption، disableSystemRoot، pin، verifyPeerCertByName، curvePreferences، cipherSuites و ECH |
| REALITY | publicKey، shortId، fingerprint، spiderX و mldsa65Verify |
| QUIC/Hysteria | bbr/brutal، سرعت‌ها، پنجره‌های جریان/اتصال، idle timeout، keepalive، PMTU discovery و maxIncomingStreams |
| Outbound | Mux فعال/غیرفعال، concurrency، xudpConcurrency، xudpProxyUDP443 و targetStrategy |
| Socket | domainStrategy، tcpFastOpen، TCP keepalive و happyEyeballs |

گزینه‌های سه بخش مستقل میزبان در JSON ذخیره می‌شوند: xray_stream_settings، xray_protocol_settings و xray_outbound_settings. فیلدهای ناسازگار با پروتکل قبل از ذخیره رد می‌شوند. گزینه‌های جدید Outbound و پروتکل که در قالب‌های دیگر قابل نمایش نیستند، فقط در اشتراک JSON منتشر می‌شوند تا بی‌صدا حذف نشوند.

## کنترل صحت

scripts/test_client_profiles.py مقدار فیلدهای ذخیره‌شده را با پاسخ واقعی HTTP مقایسه می‌کند، از جمله false، اعداد، رشته‌ها، اشیای تودرتو، extra، downloadSettings، ماسک‌ها و کلیدهای عمومی. scripts/test_windows_subscription.py هر کانفیگ همین لینک را با باینری Xray ویندوز اعتبارسنجی می‌کند و از SOCKS به HTTPS واقعی وصل می‌شود. scripts/test_xray_26327.py ورودی‌های سرور را با TCP و مسیرهای UDP پشتیبانی‌شده به echo محلی آزمایش می‌کند.

این مجموعه، نمونه‌های متنوع و مشخص است؛ تمام ترکیب‌های ممکن مقادیر را پوشش نمی‌دهد. تنظیمات سروری مانند acceptProxyProtocol، کلید خصوصی، masquerade و serverMaxHeaderBytes نباید به کلاینت منتقل شوند. تنظیمات وابسته به محیط مانند interface، mark، tproxy، UDP hopping چندپورت و reverse به توپولوژی مخصوص نیاز دارند و با افزودن یک فیلد تصادفی به لینک تست معنادار نمی‌شوند. VLESS Encryption با decryption=none سرور فعلی قابل جایگزینی نیست. فهرست کامل فیلدهای این تگ در xray-v26.3.27-fields.fa.md موجود است؛ وجود یک فیلد در فهرست سورس، به معنی قابل استفاده بودن آن نیست: allowInsecure و verifyPeerCertInNames نیز در این نسخه حذف یا بی‌اثر شده‌اند.

## نتیجهٔ اجرای نهایی

۳۵۴ از ۳۵۴ کانفیگ با Xray v26.3.27 ویندوز اعتبارسنجی و از طریق سرور Docker به HTTPS واقعی متصل شدند. ۳۵۳ اتصال در تلاش اول و یک اتصال در تلاش دوم موفق شد؛ زمان انتظار ۱۵ ثانیه و حداکثر دو تلاش بود. [گزارش اتصال](xray-windows-extended-results.json) خطای تلاش نخست را نیز نگه می‌دارد. [گزارش فیلدها](xray-client-fields-results.json) ۲۳۶ پروفایل صریح، ۳۲۷ کنترل فیلدهای ارث‌رسیده، ۱۵۰ مسیر فیلد متفاوت و ۹۷۰۵ تطبیق دقیق مقدار را ثبت کرده است. آزمون‌های API و ماتریس ۱۰ تست نیز گذشتند؛ ماتریس شامل ۱۲۵ ورودی پیش‌فرض و ۹۶ مسیر UDP است.

برای تکرار تست ویندوز: rtk proxy python scripts/test_windows_subscription.py SUB_URL --core C:/v2rayN-windows-64/bin/xray/xray.exe --certificate output/xray/localhost.crt --timeout 15 --attempts 2
