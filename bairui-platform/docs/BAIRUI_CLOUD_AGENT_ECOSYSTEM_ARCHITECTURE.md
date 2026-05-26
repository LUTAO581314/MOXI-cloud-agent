# 百瑞云代理生态架构文档

## 1. 总体定位

百瑞云代理是一个面向个人、团队和企业的云端智能体托管与本地协作平台。平台不是单一网站，而是由官网、用户控制台、管理员端、桌面软件、本地代理、云端调度器和可插拔运行时共同组成的完整生态。

核心原则：

- 云端负责账号、套餐、任务调度、模型推理、记忆、审计和策略判断。
- 本地代理负责接触私有代码、大文件、终端和本地工具。
- 网站和桌面软件共同承担用户工作台职能。
- Hermes 作为可插拔运行时之一，等生态稳定后再做具体适配。
- 用户数据按助理、工作区、文件、记忆和日志隔离。

## 2. 产品形态

### 2.1 网站端

职责：

- 官网展示、助理市场、套餐说明。
- 注册、登录、邮箱验证码登录。
- 助理配置、开通申请、用户控制台。
- 文件、记忆、任务、日志查看。
- 管理员审批、套餐、用户和审计管理。

适合场景：

- 用户初次了解和开通。
- 轻量任务管理。
- 管理员运营。
- 浏览器端查看状态和结果。

### 2.2 桌面软件端

职责：

- 包含网站的大部分用户端职能。
- 登录百瑞账号。
- 绑定本机设备。
- 选择本地项目目录。
- 管理本地代理权限。
- 展示实时任务、日志、补丁和确认请求。
- 允许用户控制高风险动作。

适合场景：

- 代码开发。
- 本地大文件处理。
- 私密项目协作。
- 长时间后台运行。

推荐技术：

- 第一版可用 Tauri 或 Electron。
- 如果优先快，可以先做 CLI，再包桌面壳。
- UI 可以复用网站设计系统。

### 2.3 本地代理端

职责：

- 读取授权目录。
- 搜索本地代码。
- 运行测试、构建、脚本。
- 应用补丁。
- 调用 Git。
- 屏蔽 `.env`、密钥、大文件和未授权路径。
- 把摘要、diff、日志和执行结果回传云端。

边界：

- 默认不上传整个代码库。
- 默认不上传密钥和隐私文件。
- 高风险命令需要用户确认。
- 所有本地动作写入审计日志。

### 2.4 云端大脑端

职责：

- 用户、套餐、订阅、配额。
- 助理配置和审批。
- 任务队列和调度。
- 模型调用。
- 文件和记忆索引。
- 设备绑定和工作区绑定。
- 日志与审计。
- Runtime Provider 选择。

当前技术底座：

- Django + Django REST Framework。
- SQLite 本地开发，生产建议 PostgreSQL。
- 后续加入 Redis、Celery、Channels。
- 静态 SPA 前端，后续可迁移 React/Vue。

## 3. 三种工作模式

### 3.1 云端资料模式

用户上传资料到云端，助理在云端处理。

适合：

- PDF 分析。
- 财报、论文、报告。
- 知识库资料。
- 用户明确允许上传的小文件。

数据流：

```text
用户上传文件
  -> AssistantStorage/files
  -> 任务队列
  -> 云端模型/工具处理
  -> 结果、记忆、日志回写
```

优点：

- 用户使用成本低。
- 浏览器即可完成。
- 适合文档类产品化。

风险：

- 大文件成本高。
- 涉及隐私文件时需要明确授权。

### 3.2 Git 云端工作区模式

用户授权 GitHub、Gitee 或自建 Git 仓库，云端拉取代码到隔离工作区处理。

适合：

- 团队 CI 式开发。
- 开源项目。
- 中小型私有仓库。
- 用户愿意授权仓库访问的场景。

数据流：

```text
用户授权 Git
  -> 云端创建隔离 workspace
  -> 拉取仓库
  -> Agent 读写代码
  -> 运行测试/生成 diff
  -> 提交 PR 或补丁
```

优点：

- 不依赖用户电脑在线。
- 适合自动化和团队协作。
- 方便接 CI/CD。

风险：

- 云端会接触代码。
- 需要严格密钥、token 和仓库权限管理。

### 3.3 本地代理模式

代码和大文件留在用户电脑，本地代理执行，云端负责大脑和调度。

适合：

- 私密代码库。
- 大型项目。
- 大文件、数据集、本地工具链。
- 用户不希望上传源码的开发任务。

数据流：

```text
用户在网站/桌面软件提交任务
  -> 云端调度器判断需要本地代理
  -> 本地代理接收任务
  -> 本地读取、搜索、测试、修改
  -> 回传摘要、diff、日志、确认请求
  -> 云端展示状态和结果
```

优点：

- 私有代码不离开本机。
- 可以使用用户本地工具链。
- 适合商业化代码助理。

风险：

- 需要安装软件。
- 需要设备在线。
- 本地权限和确认机制必须设计清楚。

## 4. 通信与协议

### 4.1 HTTP API

用途：

- 登录、注册、套餐。
- 助理配置。
- 文件上传。
- 任务创建。
- 管理员审批。

特点：

- 简单稳定。
- 适合请求/响应。
- 不适合实时双向任务流。

### 4.2 WebSocket

用途：

- 本地代理在线状态。
- 云端下发任务。
- 实时日志回传。
- 任务进度更新。
- 用户确认请求。

特点：

- 第一阶段最适合。
- 浏览器和桌面软件都容易接。
- Django 可通过 Channels 支持。

### 4.3 gRPC

用途：

- 后期桌面软件和本地代理高频双向流。
- 企业版私有部署。
- 多语言 SDK。
- 强类型协议。

特点：

- 性能高，协议严格。
- 浏览器不如 WebSocket 直接。
- 不建议第一阶段就强依赖。

### 4.4 内部消息队列

用途：

- 云端异步任务。
- 重试、超时、后台执行。
- 定时任务。

建议：

- Redis + Celery 作为第一阶段内部任务队列。
- 后续可评估 NATS、RabbitMQ 或 Kafka。

## 5. 标准消息协议

无论 WebSocket 还是 gRPC，都应共享统一语义：

```text
device.connect
device.heartbeat
device.status_changed

workspace.bound
workspace.indexed
workspace.policy_updated

task.assigned
task.accepted
task.progress
task.completed
task.failed

tool.call
tool.result
tool.error

log.append
confirm.required
confirm.resolved

patch.proposed
patch.applied
patch.rejected
```

第一版可以 JSON over WebSocket；协议稳定后再引入 protobuf/gRPC。

## 6. 数据模型规划

已具备：

- `Assistant`
- `AssistantToolProfile`
- `ProvisionRequest`
- `RuntimeBinding`
- `AssistantStorage`
- `AssistantFile`
- `MemoryItem`
- `AssistantTask`
- `AssistantLog`
- `Plan`
- `Subscription`
- `UsageMeter`
- `AuditEvent`
- `EmailLoginCode`

需要新增：

- `DeviceBinding`：用户设备绑定。
- `LocalAgent`：本地代理实例。
- `WorkspaceBinding`：本地目录、Git 工作区、云端资料空间绑定。
- `JobSession`：一次任务执行会话。
- `ToolCall`：工具调用记录。
- `PatchRecord`：补丁提案和应用记录。
- `ConfirmationRequest`：高风险动作确认。
- `RuntimeProvider`：Hermes、Local Agent、Git Workspace、Document Workspace 等运行时声明。

## 7. 安全策略

默认策略：

- 用户只能访问自己的助理、文件、记忆、任务和日志。
- 本地代理只能访问用户授权目录。
- 默认屏蔽 `.env`、私钥、token、证书、浏览器 Cookie、系统目录。
- 默认不上传完整代码库。
- 命令执行、删除文件、提交 Git、联网访问等高风险动作需要策略或用户确认。
- 所有关键动作写入 `AuditEvent`。

敏感文件规则：

```text
.env
.env.*
*.pem
*.key
id_rsa
id_ed25519
*.p12
*.pfx
node_modules/
.git/
dist/
build/
target/
*.sqlite
*.db
```

## 8. Runtime Provider 抽象

任务不直接绑定 Hermes，而是进入 Runtime Provider：

```text
Task
  -> Scheduler
  -> RuntimeProvider
      -> Document Workspace
      -> Git Cloud Workspace
      -> Local Agent
      -> Hermes
      -> External Model Provider
```

这样 Hermes 可以晚些接入，也可以和其他运行时并存。

## 9. 当前实现状态

已完成：

- Django 后端骨架。
- 邮箱验证码登录。
- 助理配置和开通申请。
- 管理员审批。
- 套餐、订阅、用量基础模型。
- 存储空间分配。
- 文件上传和配额。
- 长期记忆 API 和前端。
- 任务队列 API 和前端。
- 静态 SPA 控制台。

待完成：

- 日志 API 真实化。
- 设备绑定。
- 本地代理协议。
- 桌面软件/CLI。
- Git 云端工作区。
- Runtime Provider 抽象。
- Hermes 适配。
- 生产部署和安全强化。
