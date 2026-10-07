import json
import re
from enum import Enum
from typing import Optional, Union
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.system import random_password
from xray_api.types.account import (
    ShadowsocksAccount,
    HysteriaAccount,
    ShadowsocksMethods,
    TrojanAccount,
    VLESSAccount,
    VMessAccount,
    XTLSFlows,
)

FRAGMENT_PATTERN = re.compile(r'^((\d{1,4}-\d{1,4})|(\d{1,4})),((\d{1,3}-\d{1,3})|(\d{1,3})),(tlshello|\d|\d\-\d)$')

NOISE_PATTERN = re.compile(
    r'^(rand:(\d{1,4}-\d{1,4}|\d{1,4})|str:.+|hex:.+|base64:.+)(,(\d{1,4}-\d{1,4}|\d{1,4}))?(&(rand:(\d{1,4}-\d{1,4}|\d{1,4})|str:.+|hex:.+|base64:.+)(,(\d{1,4}-\d{1,4}|\d{1,4}))?)*$')


class ProxyTypes(str, Enum):
    # proxy_type = protocol

    VMess = "vmess"
    VLESS = "vless"
    Trojan = "trojan"
    Shadowsocks = "shadowsocks"
    Hysteria = "hysteria"
    WireGuard = "wireguard"

    @property
    def account_model(self):
        if self == self.VMess:
            return VMessAccount
        if self == self.VLESS:
            return VLESSAccount
        if self == self.Trojan:
            return TrojanAccount
        if self == self.Shadowsocks:
            return ShadowsocksAccount
        if self == self.Hysteria:
            return HysteriaAccount

    @property
    def settings_model(self):
        if self == self.VMess:
            return VMessSettings
        if self == self.VLESS:
            return VLESSSettings
        if self == self.Trojan:
            return TrojanSettings
        if self == self.Shadowsocks:
            return ShadowsocksSettings
        if self == self.Hysteria:
            return HysteriaSettings
        if self == self.WireGuard:
            return WireGuardSettings


class ProxySettings(BaseModel, use_enum_values=True):
    @classmethod
    def from_dict(cls, proxy_type: ProxyTypes, _dict: dict):
        return ProxyTypes(proxy_type).settings_model.model_validate(_dict)

    def dict(self, *, no_obj=False, **kwargs):
        if no_obj:
            return json.loads(self.json())
        return super().dict(**kwargs)


class VMessSettings(ProxySettings):
    id: UUID = Field(default_factory=uuid4)

    def revoke(self):
        self.id = uuid4()


class VLESSSettings(ProxySettings):
    id: UUID = Field(default_factory=uuid4)
    flow: XTLSFlows = XTLSFlows.NONE

    def revoke(self):
        self.id = uuid4()


class TrojanSettings(ProxySettings):
    password: str = Field(default_factory=random_password)
    flow: XTLSFlows = XTLSFlows.NONE

    def revoke(self):
        self.password = random_password()


class HysteriaSettings(ProxySettings):
    auth: str = Field(default_factory=random_password, min_length=1)

    def revoke(self):
        self.auth = random_password()


def generate_wireguard_private_key():
    from app.xray.wireguard import private_key
    return private_key()


class WireGuardSettings(ProxySettings):
    private_key: str = Field(default_factory=generate_wireguard_private_key)

    @field_validator("private_key")
    @classmethod
    def validate_key(cls, value):
        from app.xray.wireguard import public_key
        try:
            public_key(value)
        except Exception as exc:
            raise ValueError("WireGuard private_key must be a base64 encoded 32-byte X25519 key") from exc
        return value

    def revoke(self):
        from app.xray.wireguard import private_key
        self.private_key = private_key()


class ShadowsocksSettings(ProxySettings):
    password: str = Field(default_factory=random_password)
    method: ShadowsocksMethods = ShadowsocksMethods.CHACHA20_POLY1305

    def revoke(self):
        self.password = random_password()


class ProxyHostSecurity(str, Enum):
    inbound_default = "inbound_default"
    none = "none"
    tls = "tls"


ProxyHostALPN = Enum(
    "ProxyHostALPN",
    {
        "none": "",
        "h3": "h3",
        "h2": "h2",
        "http/1.1": "http/1.1",
        "h3,h2,http/1.1": "h3,h2,http/1.1",
        "h3,h2": "h3,h2",
        "h2,http/1.1": "h2,http/1.1",
    },
)


ProxyHostFingerprint = Enum(
    "ProxyHostFingerprint",
    {
        "none": "",
        "chrome": "chrome",
        "firefox": "firefox",
        "safari": "safari",
        "ios": "ios",
        "android": "android",
        "edge": "edge",
        "360": "360",
        "qq": "qq",
        "random": "random",
        "randomized": "randomized",
    },
)


class FormatVariables(dict):
    def __missing__(self, key):
        return key.join("{}")


class ProxyHost(BaseModel):
    remark: str
    address: str
    port: Optional[int] = Field(None, nullable=True)
    sni: Optional[str] = Field(None, nullable=True)
    host: Optional[str] = Field(None, nullable=True)
    path: Optional[str] = Field(None, nullable=True)
    security: ProxyHostSecurity = ProxyHostSecurity.inbound_default
    alpn: ProxyHostALPN = ProxyHostALPN.none
    fingerprint: ProxyHostFingerprint = ProxyHostFingerprint.none
    allowinsecure: Union[bool, None] = None
    is_disabled: Union[bool, None] = None
    mux_enable: Union[bool, None] = None
    fragment_setting: Optional[str] = Field(None, nullable=True)
    noise_setting: Optional[str] = Field(None, nullable=True)
    random_user_agent: Union[bool, None] = None
    use_sni_as_host: Union[bool, None] = None
    xray_stream_settings: Optional[dict] = None
    xray_protocol_settings: Optional[dict] = None
    xray_outbound_settings: Optional[dict] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("xray_stream_settings")
    @classmethod
    def validate_client_stream(cls, value):
        if value is not None:
            from app.xray.transport import validate_client_override
            validate_client_override(value)
        return value

    @field_validator("xray_protocol_settings")
    @classmethod
    def validate_protocol_settings(cls, value):
        if value and set(value) - {"encryption", "reverse", "seed", "testpre", "testseed", "security", "experiments", "level", "email", "uot", "mtu", "workers", "reserved", "noKernelTun", "domainStrategy"}:
            raise ValueError("Unsupported or credential-bearing client protocol field")
        return value

    @field_validator("xray_outbound_settings")
    @classmethod
    def validate_outbound_settings(cls, value):
        if value and set(value) - {"mux", "targetStrategy", "sendThrough"}:
            raise ValueError("Client outbound settings support mux, targetStrategy and sendThrough")
        if value and "mux" in value and (not isinstance(value["mux"], dict) or set(value["mux"]) - {"enabled", "concurrency", "xudpConcurrency", "xudpProxyUDP443"}):
            raise ValueError("Invalid client mux settings")
        return value

    @field_validator("remark", mode="after")
    def validate_remark(cls, v):
        try:
            v.format_map(FormatVariables())
        except ValueError as exc:
            raise ValueError("Invalid formatting variables")

        return v

    @field_validator("address", mode="after")
    def validate_address(cls, v):
        try:
            v.format_map(FormatVariables())
        except ValueError as exc:
            raise ValueError("Invalid formatting variables")

        return v

    @field_validator("fragment_setting", check_fields=False)
    @classmethod
    def validate_fragment(cls, v):
        if v and not FRAGMENT_PATTERN.match(v):
            raise ValueError(
                "Fragment setting must be like this: length,interval,packet (10-100,100-200,tlshello)."
            )
        return v

    @field_validator("noise_setting", check_fields=False)
    @classmethod
    def validate_noise(cls, v):
        if v:
            if not NOISE_PATTERN.match(v):
                raise ValueError(
                    "Noise setting must be like this: packet,delay (rand:10-20,100-200)."
                )
            if len(v) > 2000:
                raise ValueError(
                    "Noise can't be longer that 2000 character"
                )
        return v


class ProxyInbound(BaseModel):
    tag: str
    protocol: ProxyTypes
    network: str
    tls: str
    port: Union[int, str]
