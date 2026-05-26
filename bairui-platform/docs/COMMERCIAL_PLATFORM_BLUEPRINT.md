# 百瑞云助理商用网站平台设计

## 1. 产品定位

百瑞云助理是一个专业个人云助理托管平台。用户不需要购买服务器、安装智能体、配置模型、维护运行环境，只需要选择或配置自己的云助理，平台负责部署、模型接入、工具权限、记忆、文件空间、日志和持续运行。

核心价值：

- 把复杂 Agent 部署变成可购买、可审批、可运营的服务。
- 给每个用户和每个助理提供独立 `workspace`、`memory`、`logs`。
- 支持学习、生活、研究、工作、创作等个人场景。
- 后续扩展为多子 Agent 编排、定时任务、文件处理、代码沙箱和企业团队节点。

## 2. 商用版本范围

### 必须具备

- 官网首页与产品介绍。
- 助理市场与场景模板。
- 配置向导。
- 用户注册、登录、账户中心。
- 用户控制台。
- 助理详情页。
- 开通申请与审批流。
- 管理员后台。
- 套餐与权益管理。
- 运行状态展示。
- 基础日志与审计。
- Hermes/Agent 内部运行层接入边界。

### 第一版暂缓

- 真实在线支付，可先用内测资格、人工收款或兑换码。
- 大规模文件对象存储，可先本地 volume，后续接 S3/R2。
- 多租户企业组织结构，可先个人账户，后续加 Team/Org。
- 复杂 Agent 编排 UI，可先保留能力开关与管理员审批。

## 3. 站点信息架构

### 公开站点

```text
/
  产品首页
/market
  助理市场
/pricing
  套餐与内测名额
/security
  安全与隐私
/status
  平台运行状态
/login
  登录
/register
  注册
```

### 用户端

```text
/app
  用户控制台总览
/app/assistants
  我的助理
/app/assistants/new
  新建云助理
/app/assistants/:id
  助理详情
/app/assistants/:id/chat
  会话入口
/app/assistants/:id/tasks
  任务
/app/assistants/:id/memory
  记忆
/app/assistants/:id/files
  文件
/app/assistants/:id/logs
  日志
/app/billing
  套餐与用量
/app/settings
  账户设置
```

### 管理员端

```text
/admin
  Django Admin
/admin/assistants
  助理管理
/admin/provision-requests
  开通审批
/admin/users
  用户管理
/admin/plans
  套餐管理
/admin/usage
  用量与配额
/admin/audit
  审计日志
/hermes
  Hermes 内部控制台，继续保护
```

## 4. 用户工作流

### 新用户开通

1. 用户进入官网。
2. 浏览助理市场或点击开始配置。
3. 注册或登录。
4. 填写助理名称、场景、目标、语气。
5. 选择模型和工具能力。
6. 确认记忆与隐私策略。
7. 提交开通申请。
8. 后台生成 `ProvisionRequest`。
9. 管理员审批。
10. Worker 创建 workspace、memory、logs。
11. 助理进入 `active` 状态。

### 日常使用

1. 用户进入 `/app`。
2. 查看助理状态和任务。
3. 发起会话、上传文件或创建任务。
4. 平台记录任务、日志、记忆摘要。
5. 用户可关闭工具、删除记忆或暂停助理。

### 高权限能力

代码执行、定时任务、多子 Agent、外部集成等能力默认进入审批。用户可申请，管理员确认风险后启用。

## 5. 管理员工作流

### 审批开通申请

1. 管理员进入 `/admin/provision-requests`。
2. 查看用户、套餐、助理目标、工具权限。
3. 调整模型、权限和配额。
4. 批准或拒绝。
5. 批准后触发异步开通任务。

### 运营管理

- 查看活跃用户、活跃助理、任务量。
- 调整套餐和权益。
- 查看错误日志。
- 暂停异常助理。
- 管理内测名额和邀请。

## 6. 权限模型

角色：

- `anonymous`：只能访问公开站点。
- `user`：管理自己的助理、任务、文件、记忆。
- `staff`：审批申请、查看运营后台。
- `admin`：管理系统配置、套餐、Hermes 入口和高权限能力。

原则：

- 用户只能访问自己的数据。
- 普通用户不能访问 API Key、环境变量、Hermes 系统日志。
- 高权限工具必须显式审批。
- 所有审批和关键操作进入审计日志。

## 7. 套餐设计

### Starter

- 1 个个人助理。
- 基础模型。
- 基础 workspace。
- 基础浏览器检索。
- 无长期记忆或轻量记忆。

### Pro

- 多个个人助理。
- 长期记忆。
- 文件空间。
- 更多任务额度。
- 高级模型可选。

### Research

- 研究资料库。
- 长文档解析。
- 引用整理。
- 更高上下文和任务额度。

### Team

- 多成员。
- 多子 Agent。
- 团队共享资料。
- 管理员控制台。
- 高级审计。

## 8. 核心数据域

现有第一版模型：

- `Assistant`
- `AssistantToolProfile`
- `ProvisionRequest`
- `AssistantTask`
- `AssistantLog`
- `MemoryItem`

商用扩展模型：

- `Plan`
- `Subscription`
- `UsageMeter`
- `AssistantStorage`
- `Workspace`
- `FileObject`
- `Conversation`
- `Message`
- `AuditEvent`
- `InvitationCode`
- `ToolApproval`
- `RuntimeBinding`

## 9. API 分区

公开 API：

```text
GET /portal-api/health/
GET /portal-api/public/status/
GET /portal-api/public/plans/
```

用户 API：

```text
GET    /portal-api/me/
GET    /portal-api/assistants/
POST   /portal-api/assistants/
GET    /portal-api/assistants/:id/
PATCH  /portal-api/assistants/:id/
POST   /portal-api/provision-requests/
GET    /portal-api/provision-requests/
GET    /portal-api/tasks/
GET    /portal-api/logs/
GET    /portal-api/memory/
```

管理员 API 可先依赖 Django Admin，后续再做专属运营 API。

## 10. 运行架构

```text
Browser
  |
Caddy
  |-- static site
  |-- /portal-api/ -> Django
  |-- /admin/ -> Django Admin
  |-- /hermes/ -> Hermes, protected

Django
  |
PostgreSQL
Redis
Celery Worker
  |
Hermes / Agent runtime
  |
workspace / memory / logs
```

## 10.1 套餐磁盘空间与目录隔离

平台按用户当前套餐为每个助理分配存储配额。审批开通成功后，系统生成 `AssistantStorage`，并把助理数据拆成固定分区：

```text
/srv/bairui/workspaces/
  user-<user_id>/
    assistant-<assistant_id>/
      workspace/
      files/
      memory/
      logs/
```

分区用途：

- `workspace/`：助理运行时工作目录。
- `files/`：用户上传文件与助理生成文件。
- `memory/`：长期记忆、摘要、向量索引或后续 RAG 资料。
- `logs/`：用户可见运行日志与任务日志。

配额来源：

- `Plan.storage_limit_mb`
- `AssistantStorage.quota_mb`
- `AssistantStorage.used_mb`
- `AssistantStorage.available_mb`

后续文件上传、记忆写入和任务日志写入都必须先检查 `AssistantStorage`，不能直接写裸路径。

当前实现：

- 开通审批成功时创建 `AssistantStorage` 并创建实际目录。
- `POST /portal-api/assistants/:id/upload_file/` 写入 `files/` 分区。
- `GET /portal-api/assistants/:id/files/` 返回用户自己的文件元数据。
- 上传会按 MB 计入 `AssistantStorage.used_mb`，超出套餐配额时拒绝。

## 11. 安全与合规边界

- 登录态使用 HttpOnly session cookie 或后续 JWT + refresh cookie。
- 管理员后台必须强密码，后续启用 2FA。
- Caddy 保留 `/hermes/` Basic Auth 或升级到 VPN/SSO。
- API Key 和环境变量只存在服务器 private/env，不入库、不进前端。
- 文件上传需要大小限制、类型限制和病毒扫描预留。
- 日志不记录密钥、完整用户敏感输入或支付信息。
- 用户可请求删除记忆和文件。

## 12. 商用上线验收

第一阶段可上线标准：

- 用户能注册登录。
- 用户能创建助理草稿。
- 用户能提交开通申请。
- 管理员能审批。
- 审批后助理状态变为运行中。
- 用户能在控制台看到真实数据。
- 公开状态页可用。
- 管理员后台可查看用户、助理、日志。
- 所有核心数据进入 PostgreSQL。
- 静态前端不再依赖纯模拟状态。
