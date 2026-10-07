import atexit
import base64
import os
import json
import secrets
import re
import subprocess
import threading
import time
from collections import deque
from contextlib import contextmanager

from app import logger
from app.xray.config import XRayConfig
from config import DEBUG


class XRayCore:
    def __init__(self,
                 executable_path: str = "/usr/bin/xray",
                 assets_path: str = "/usr/share/xray"):
        self.executable_path = executable_path
        self.assets_path = assets_path

        self.version = self.get_version()
        self.process = None
        self._tun_names = set()
        self.restarting = False

        self._logs_buffer = deque(maxlen=100)
        self._temp_log_buffers = {}
        self._on_start_funcs = []
        self._on_stop_funcs = []
        self._env = {
            "XRAY_LOCATION_ASSET": assets_path
        }

        atexit.register(lambda: self.stop() if self.started else None)

    def get_version(self):
        cmd = [self.executable_path, "version"]
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf-8')
        m = re.match(r'^Xray (\d+\.\d+\.\d+)', output)
        if m:
            return m.groups()[0]

    def get_x25519(self, private_key: str = None):
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
        key = (X25519PrivateKey.from_private_bytes(base64.urlsafe_b64decode(private_key + "=" * (-len(private_key) % 4)))
               if private_key else X25519PrivateKey.generate())
        return {"private_key": base64.urlsafe_b64encode(key.private_bytes_raw()).decode().rstrip("="),
                "public_key": base64.urlsafe_b64encode(key.public_key().public_bytes_raw()).decode().rstrip("=")}

    def __capture_process_logs(self):
        process = self.process
        def capture_and_debug_log():
            while process:
                output = process.stdout.readline()
                if output:
                    output = output.strip()
                    self._logs_buffer.append(output)
                    for buf in list(self._temp_log_buffers.values()):
                        buf.append(output)
                    logger.debug(output)

                elif process.poll() is not None:
                    break

        def capture_only():
            while process:
                output = process.stdout.readline()
                if output:
                    output = output.strip()
                    self._logs_buffer.append(output)
                    for buf in list(self._temp_log_buffers.values()):
                        buf.append(output)

                elif process.poll() is not None:
                    break

        if DEBUG:
            threading.Thread(target=capture_and_debug_log).start()
        else:
            threading.Thread(target=capture_only).start()

    @contextmanager
    def get_logs(self):
        buf = deque(self._logs_buffer, maxlen=100)
        buf_id = id(buf)
        try:
            self._temp_log_buffers[buf_id] = buf
            yield buf
        finally:
            del self._temp_log_buffers[buf_id]
            del buf

    @property
    def started(self):
        if not self.process:
            return False

        if self.process.poll() is None:
            return True

        return False

    def validate(self, config: XRayConfig):
        payload = json.loads(config.to_json())
        # Xray -test opens TUN devices; the running core already owns its name.
        aliases = {}
        for inbound in payload.get("inbounds", []):
            name = inbound.get("settings", {}).get("name")
            if (inbound.get("protocol") == "tun" and self.started
                    and isinstance(name, str) and name in self._tun_names):
                aliases.setdefault(name, "mbcheck" + secrets.token_hex(3))
                inbound["settings"]["name"] = aliases[name]
        result = subprocess.run([self.executable_path, "run", "-test", "-config", "stdin:"],
                                input=json.dumps(payload), capture_output=True, text=True,
                                env={**os.environ, **self._env}, timeout=30)
        if result.returncode:
            raise ValueError((result.stdout + result.stderr).strip())

    def start(self, config: XRayConfig):
        if self.started is True:
            raise RuntimeError("Xray is started already")

        if config.get('log', {}).get('logLevel') in ('none', 'error'):
            config['log']['logLevel'] = 'warning'

        cmd = [
            self.executable_path,
            "run",
            '-config',
            'stdin:'
        ]
        self.process = subprocess.Popen(
            cmd,
            env={**os.environ, **self._env},
            stdin=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdout=subprocess.PIPE,
            universal_newlines=True
        )
        self.process.stdin.write(config.to_json())
        self.process.stdin.flush()
        self.process.stdin.close()
        self.__capture_process_logs()
        from xray_api import XRay
        api = XRay(config.api_host, config.api_port)
        deadline = time.monotonic() + 15
        while True:
            try:
                api.get_sys_stats(timeout=1)
                break
            except Exception as exc:
                if not self.started or time.monotonic() >= deadline:
                    self.stop()
                    raise RuntimeError("Xray failed to become ready: " + "\n".join(self._logs_buffer)) from exc
                time.sleep(.1)
        self._tun_names = {i.get("settings", {}).get("name")
                           for i in config.get("inbounds", []) if i.get("protocol") == "tun"}
        logger.warning(f"Xray core {self.version} started")

        # execute on start functions
        for func in self._on_start_funcs:
            threading.Thread(target=func).start()

    def stop(self):
        if not self.started:
            return

        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        self.process = None
        logger.warning("Xray core stopped")

        # execute on stop functions
        for func in self._on_stop_funcs:
            threading.Thread(target=func).start()

    def restart(self, config: XRayConfig):
        if self.restarting is True:
            return

        try:
            self.restarting = True
            logger.warning("Restarting Xray core...")
            self.stop()
            self.start(config)
        finally:
            self.restarting = False

    def on_start(self, func: callable):
        self._on_start_funcs.append(func)
        return func

    def on_stop(self, func: callable):
        self._on_stop_funcs.append(func)
        return func
