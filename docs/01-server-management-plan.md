# MOXI Server Management Plan

本文档定义 MOXI 商业部署中的服务器管理方案。

## 1. 核心判断

正式商业部署不要依赖磁盘分区或多个 venv 实例做客户隔离。

推荐路径：

```text
客户套餐 -> 平台 license -> VPS / VM -> Docker Compose -> Hermes -> 健康回传 -> 售后运维
```

## 2. 隔离等级

| 等级 | 方式 | 适用场景 | 商业建议 |
| --- | --- | --- | --- |
| L0 | 多 venv | 开发调试 | 不售卖 |
| L1 | 同机多 Docker | 内测或低价试点 | 谨慎 |
| L2 | 单宿主机多 VM | 我方托管小客户 | 可用 |
| L3 | 每客户独立 VPS / VM | 标准私有化 | 推荐 |
| L4 | 每客户独立物理机 | 高安全企业 | 推荐 |

## 3. 服务器规格

正式套餐建议：

| 套餐 | 推荐资源 | 用途 |
| --- | --- | --- |
| Starter | 2c4g | 个人、小团队 |
| Pro | 4c8g | 标准企业使用 |
| Business | 8c16g | 多用户、多连接器 |
| Enterprise | 定制 | 专属资源和 SLA |

2c2g 只适合测试或极轻量试点，不建议作为正式主套餐。

## 4. 16c16g 服务器使用建议

内部测试：

- 可以切 7 个 2c2g VM；
- 留 2c2g 给宿主机；
- 只适合测试并发和部署流程。

商业试点：

- 建议 3 到 4 个客户；
- 每个客户 2c3g 或 2c4g；
- 宿主机至少保留 2c4g；
- 必须保留磁盘和备份空间。

正式售卖：

- 优先一个客户一个 VPS / VM；
- 企业客户独立服务器；
- 我方托管时再考虑多 VM 共宿主机。

## 5. 客户 VM 内部服务

每个客户 VM 内运行：

- Nginx；
- Hermes API；
- Hermes worker；
- PostgreSQL；
- Redis 可选；
- Obsidian Vault；
- backup job；
- health agent。

默认使用 Docker Compose。

## 6. 平台服务器登记

平台应保存：

- server_id；
- organization_id；
- license_id；
- deployment_mode；
- provider；
- region；
- hostname；
- domain；
- hermes_version；
- health_status；
- last_seen_at；
- backup_status；
- notes。

平台不保存：

- root 密码；
- SSH 私钥；
- 数据库密码；
- 模型 API Key；
- 客户业务数据。

## 7. 健康回传

Hermes 或 server agent 可以回传：

- CPU 摘要；
- 内存摘要；
- 磁盘摘要；
- Hermes 版本；
- 数据库状态；
- 备份状态；
- 最近错误数量；
- 连接器状态摘要；
- license 状态；
- 心跳时间。

健康回传只做摘要，不上传客户业务内容。

## 8. Server Agent 原则

Server Agent 默认主动连接平台，避免开放公网管理端口。

任务必须白名单化：

- check_health；
- deploy_hermes；
- restart_service；
- reload_nginx；
- backup_database；
- collect_diagnostics；
- rotate_logs；
- upgrade_agent。

禁止第一版支持任意 shell 命令。

## 9. 备份和恢复

每个客户必须支持：

- PostgreSQL 备份；
- Obsidian Vault 备份；
- `.env` 脱敏备份；
- Nginx 配置备份；
- 版本号记录；
- 恢复演练。

备份可以先本地保存，再由客户选择是否上传对象存储。

## 10. 第一阶段交付

P0 先做手动辅助：

1. 平台创建 server_id；
2. 平台生成 license；
3. 平台生成部署命令；
4. 客户或我方在 VPS / VM 执行；
5. Hermes 启动；
6. 平台看到健康心跳；
7. 客户完成验收。

这比一开始做全自动云厂商控制更稳，也更适合快速售卖试点。
