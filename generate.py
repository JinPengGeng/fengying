#!/usr/bin/env python3
"""
生成 Clash/mihomo 订阅 YAML
从 proxifly/free-proxy-list 拉取免费 HTTP/SOCKS5 代理并转换为 Clash YAML 格式
"""
import json
import sys
import urllib.request
import os

# 配置
CONFIG = {
    "source_url": os.environ.get(
        "SOURCE_URL",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.json",
    ),
    "max_proxies": int(os.environ.get("MAX_PROXIES", "300")),
    "filter_anonymity": os.environ.get("FILTER_ANONYMITY", ""),  # elite / anonymous / transparent
    "filter_country": os.environ.get("FILTER_COUNTRY", ""),      # 2-letter ISO code
    "include_socks4": os.environ.get("INCLUDE_SOCKS4", "false").lower() == "true",
    "out_file": os.environ.get("OUT_FILE", "clash.yaml"),
    "group_type": os.environ.get("GROUP_TYPE", "url-test"),  # url-test / fallback / select
    "health_check_url": os.environ.get(
        "HEALTH_CHECK_URL",
        "https://www.gstatic.com/generate_204",
    ),
}


def fetch_proxies(url: str) -> list:
    """从 proxifly JSON URL 拉取代理列表"""
    print(f"[+] 拉取代理列表: {url}", file=sys.stderr)
    resp = urllib.request.urlopen(url, timeout=15)
    data = json.loads(resp.read().decode())
    print(f"[+] 总计: {len(data)} 个", file=sys.stderr)
    return data


def filter_proxies(proxies: list) -> list:
    """筛选可用的代理 (HTTP/SOCKS5, 可选匿名性/国家)"""
    supported = ("http", "socks5")
    if CONFIG["include_socks4"]:
        supported = supported + ("socks4",)

    filtered = [p for p in proxies if p["protocol"] in supported]
    print(f"[+] 协议筛选后: {len(filtered)} 个 (排除 socks4)" if not CONFIG["include_socks4"] else f"[+] 协议筛选后: {len(filtered)} 个", file=sys.stderr)

    if CONFIG["filter_anonymity"]:
        filtered = [p for p in filtered if p.get("anonymity", "") == CONFIG["filter_anonymity"]]
        print(f"[+] 匿名性 ({CONFIG['filter_anonymity']}) 筛选后: {len(filtered)} 个", file=sys.stderr)

    if CONFIG["filter_country"]:
        filtered = [p for p in filtered if p.get("geolocation", {}).get("country", "") == CONFIG["filter_country"]]
        print(f"[+] 国家 ({CONFIG['filter_country']}) 筛选后: {len(filtered)} 个", file=sys.stderr)

    # 去重 (按 ip:port)
    seen = set()
    deduped = []
    for p in filtered:
        key = f"{p['ip']}:{p['port']}"
        if key not in seen:
            seen.add(key)
            deduped.append(p)
    print(f"[+] 去重后: {len(deduped)} 个", file=sys.stderr)

    return deduped[:CONFIG["max_proxies"]]


def generate_clash_yaml(proxies: list) -> str:
    """将代理列表转换为 Clash/mihomo YAML 配置"""
    # 构造 proxies 部分
    clash_proxies = []
    for i, p in enumerate(proxies):
        name = f"px-{i+1:04d}"
        node = {
            "name": name,
            "type": p["protocol"],
            "server": p["ip"],
            "port": p["port"],
        }
        clash_proxies.append(node)

    # proxy-group
    proxy_group = {
        "name": "PROXY",
        "type": CONFIG["group_type"],
        "proxies": [n["name"] for n in clash_proxies],
        "url": CONFIG["health_check_url"],
        "interval": 300,
    }

    if CONFIG["group_type"] == "fallback":
        proxy_group["url"] = CONFIG["health_check_url"]

    # 序列化为 YAML（手动构造，避免 pyyaml 依赖）
    lines = [
        "# Clash/mihomo 免费代理订阅",
        "# 来源: proxifly/free-proxy-list",
        f"# 生成时间: __GENERATED__",
        f"# 节点数: {len(clash_proxies)}",
        "",
        "proxies:",
    ]

    for n in clash_proxies:
        lines.append(f"  - name: {n['name']}")
        lines.append(f"    type: {n['type']}")
        lines.append(f"    server: {n['server']}")
        lines.append(f"    port: {n['port']}")

    lines.extend([
        "",
        "proxy-groups:",
        f"  - name: {proxy_group['name']}",
        f"    type: {proxy_group['type']}",
        "    proxies:",
    ])

    for pname in proxy_group["proxies"]:
        lines.append(f"      - {pname}")

    lines.extend([
        f"    url: {proxy_group['url']}",
        f"    interval: {proxy_group['interval']}",
        "",
        "rules:",
        "  - MATCH,PROXY",
        "",
    ])

    return "\n".join(lines)


def main():
    try:
        proxies = fetch_proxies(CONFIG["source_url"])
        filtered = filter_proxies(proxies)

        if not filtered:
            print("[!] 没有可用的代理，跳过文件生成", file=sys.stderr)
            sys.exit(0)

        yaml_content = generate_clash_yaml(filtered)

        # 写入当前时间
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        yaml_content = yaml_content.replace("__GENERATED__", now)

        with open(CONFIG["out_file"], "w", encoding="utf-8") as f:
            f.write(yaml_content)

        print(f"[+] 已写入 {CONFIG['out_file']}: {len(filtered)} 节点, {len(yaml_content)} 字节", file=sys.stderr)
        print(f"[+] 订阅 URL 复制到 Clash/mihomo 使用", file=sys.stderr)

    except Exception as e:
        print(f"[!] 错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
