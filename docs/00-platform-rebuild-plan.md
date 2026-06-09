# MOXI Cloud Agent Platform Rebuild Plan

本文档定义 `MOXI-cloud-agent` 的重建方案。

当前定位：

- `hermes-` 是客户侧 Agent OS 产品内核。
- `MOXI-cloud-agent` 是官网、客户平台、商业授权、部署向导、服务器管理和售后平台。
- 现有 `bairui-platform/` 是旧原型，可复用思路和局部代码，但不是最终边界。

## 1. 为什么要重建

现有仓库已经有 Django 原型，包含账号、套餐、订阅、设备配对、本地 Agent 和 WebSocket 心跳。

这些能力有价值，但旧项目存在三个问题：

- 品牌还是 Bairui，不是 MOXI 商业平台；
- 业务定位偏云助理托管，不是 Hermes 私有化交付平台；
- Hermes 在旧文档中只是可插拔运行时之一，不符合当前“Hermes 是客户侧产品内核”的决策。

所以建议重建，而不是继续在旧定位上追加功能。

## 2. 新平台要解决的问题

新平台必须解决：

1. 客户为什么买；
2. 客户如何注册和购买；
3. 客户如何获得 license；
4. 客户如何部署 Hermes；
5. 我方如何知道客户服务器是否健康；
6. 客户如何提交工单；
7. 我方如何管理版本、续费和售后；
8. 托管客户如何由我们统一运维。

## 3. 平台边界

平台负责：

- 官网；
- 客户注册；
- 组织；
- 套餐；
- 订单；
- license；
- 部署向导；
- 服务器登记；
- 健康摘要；
- 版本发布；
- 工单；
- 诊断包；
- 管理员后台。

平台不负责：

- Hermes 内部 Agent 逻辑；
- 客户业务聊天内容；
- 客户 Obsidian 正文；
- 客户模型 API Key；
- 客户连接器 token；
- 任意远程 shell。

## 4. 推荐技术路线

建议新平台采用：

- Next.js；
- TypeScript；
- PostgreSQL；
- Prisma 或 Drizzle；
- Tailwind CSS；
- shadcn/ui；
- Auth.js 或自研 session；
- Docker Compose；
- GitHub Actions；
- Playwright。

可选路线：

- 如果想最快复用旧代码，可以保留 Django 后端作为 API 层；
- 但官网、客户控制台、部署向导、管理后台仍建议使用 Next.js；
- Django 原型中的模型和接口可以迁移为新平台的参考。

## 5. 首批功能

P0：

- 官网；
- 登录注册；
- 组织；
- 套餐；
- license 生成；
- 部署向导；
- 服务器登记；
- 管理员后台；
- 平台审计日志。

P1：

- 订单；
- 支付；
- 工单；
- 文档站；
- 版本发布；
- 健康回传；
- 诊断包上传。

P2：

- 自动开通；
- 自动创建 VM；
- 自动部署；
- 自动升级；
- 托管版；
- 渠道商。

## 6. 数据模型

平台侧最小数据模型：

- users；
- organizations；
- organization_members；
- plans；
- subscriptions；
- orders；
- licenses；
- license_features；
- customer_servers；
- server_heartbeats；
- deployments；
- releases；
- support_tickets；
- ticket_messages；
- diagnostic_uploads；
- audit_logs。

## 7. License 流程

1. 客户购买套餐；
2. 平台生成 license；
3. license 绑定组织、套餐、能力、到期时间；
4. 客户下载 license；
5. 客户部署 Hermes 时导入 license；
6. Hermes 本地验证；
7. Hermes 周期性上报健康摘要；
8. 平台显示授权和服务器状态。

license 不应包含客户密钥、模型 API Key、连接器 token 或业务数据。

## 8. 部署向导

部署向导应收集：

- 部署模式：本地、VPS、VM、托管；
- 操作系统；
- 是否已有域名；
- 是否需要 HTTPS；
- license；
- server_id；
- Hermes 版本；
- PostgreSQL 密码生成；
- Obsidian Vault 路径；
- 模型供应商选择。

输出：

- `.env` 模板；
- Docker Compose 命令；
- Nginx 参考配置；
- DNS 指引；
- 健康检查 URL；
- 验收清单。

## 9. 和 Hermes 的接口

平台给 Hermes：

- license；
- server_id；
- release 信息；
- 部署配置模板；
- 文档链接。

Hermes 给平台：

- server_id；
- version；
- health_status；
- backup_status；
- connector_status_summary；
- error_count_24h；
- last_seen_at。

默认不上传：

- 聊天内容；
- Obsidian 正文；
- 客户文件；
- API Key；
- token。

## 10. 重建步骤

建议执行：

1. 打 tag 备份当前 `main`；
2. 保留现有代码一段时间作为 `legacy`；
3. 新建 Next.js 平台骨架；
4. 建立数据库 schema；
5. 实现组织、套餐、license；
6. 实现服务器登记；
7. 实现部署向导；
8. 实现管理员后台；
9. 再迁移旧 Django 原型中有价值的配对和心跳逻辑。

如果确认无人依赖旧历史，可以使用 orphan 分支重建；否则建议普通提交重建，保留历史更稳。
