"""Extract the tagged Go JSON field inventory; not a JSON Schema validator."""
import argparse
import json
import re
from pathlib import Path

FILES = ("xray.go", "dokodemo.go", "http.go", "socks.go", "shadowsocks.go",
         "vmess.go", "vless.go", "trojan.go", "wireguard.go", "hysteria.go",
         "tun.go", "transport_internet.go", "transport_authenticators.go", "grpc.go")


def extract(source):
    objects = {}
    for filename in FILES:
        text = (source / "infra/conf" / filename).read_text()
        for match in re.finditer(r"type\s+(\w+)\s+struct\s*\{(.*?)\n\}", text, re.S):
            fields = []
            for field in re.finditer(r'^\s*(\w+)\s+(.+?)\s+`json:"([^"\n]+)"`', match[2], re.M):
                key = field[3].split(",")[0]
                if key:
                    fields.append({"json": key, "go_type": field[2].strip()})
            if fields:
                objects[match[1]] = {"source": "infra/conf/" + filename,
                                     "line": text.count("\n", 0, match.start()) + 1,
                                     "fields": fields}
    return {"version": "v26.3.27", "commit": "d2758a023cd7f4174a5a5fa4ff66e487d4342ba0",
            "kind": "source-field-inventory", "objects": objects}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("app/xray/schema_v26_3_27.json"))
    args = parser.parse_args()
    args.output.write_text(json.dumps(extract(args.source), indent=2) + "\n")
