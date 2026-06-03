# Proxifly Clash Subscription

利用 proxifly/free-proxy-list 的免费 HTTP/SOCKS5 代理自动生成 Clash/mihomo 订阅配置。

## 如何使用

### 直接使用生成的订阅链接

将以下 URL 添加到 Clash Verge / FlClash / mihomo 的订阅管理器：

```
https://raw.githubusercontent.com/JinPengGeng/fengying/main/clash.yaml
```

### 手动生成

```bash
python3 generate.py
```

输出 `clash.yaml`，可直接导入 Clash 客户端。

## 环境变量配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MAX_PROXIES` | `300` | 最大节点数 |
| `FILTER_ANONYMITY` | (空) | 筛选匿名级别: `elite` / `anonymous` / `transparent` |
| `FILTER_COUNTRY` | (空) | 筛选国家代码: `US`, `JP`, `SG` 等 |
| `INCLUDE_SOCKS4` | `false` | 是否包含 SOCKS4 代理 |
| `GROUP_TYPE` | `url-test` | 策略组类型: `url-test` / `fallback` / `select` |
| `HEALTH_CHECK_URL` | gstatic/generate_204 | 健康检查 URL |
| `SOURCE_URL` | proxifly master all/data.json | 代理源 URL |

## GitHub Actions 自动更新

每 30 分钟自动拉取最新代理并推送到本仓库，生成的 `clash.yaml` 可直接作为 Clash 订阅链接。

## 许可证

GPL-3.0
