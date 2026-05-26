# 百瑞云代理开发计划与任务追踪

## 1. 目标

建设完整百瑞云代理生态：

- 网站端：官网、用户控制台、管理员端。
- 云端平台：用户、套餐、助理、文件、记忆、任务、日志、审计。
- 桌面软件：用户本地工作台。
- 本地代理：私有代码和大文件本地执行。
- Git 云端工作区：授权仓库的云端开发模式。
- Runtime Provider：Hermes、本地代理、Git 工作区、文档工作区等可插拔运行时。

## 2. 当前阶段

当前处于 **Phase 1.5：平台核心能力成型**。

已完成：

- Django + DRF 后端。
- 静态 SPA 前端。
- 用户名密码登录。
- SMTP 邮箱验证码登录。
- 套餐、订阅、用量模型。
- 助理配置、提交开通申请、管理员审批。
- 审批后分配 `workspace/files/memory/logs`。
- 文件上传、配额检查、文件列表。
- 长期记忆 API、JSONL 同步、前端记忆页。
- 任务队列 API、任务额度检查、前端任务页。

## 3. 阶段计划

### Phase 0：基础平台

状态：已完成。

任务：

- [x] Django 项目。
- [x] DRF API。
- [x] 前端静态 SPA。
- [x] 基础模型。
- [x] Django Admin。
- [x] Docker 部署草案。

验收：

- 后端能启动。
- 前端能展示。
- `/portal-api/health/` 正常。

### Phase 1：可运营 MVP

状态：基本完成。

任务：

- [x] 注册、登录、登出、当前用户。
- [x] 邮箱验证码登录。
- [x] 助理创建。
- [x] 工具能力配置。
- [x] 开通申请。
- [x] 管理员审批。
- [x] 审批后分配存储空间。
- [x] 套餐和订阅模型。
- [x] 前端配置流接后端。
- [x] 前端控制台读取真实助理。

剩余：

- [x] 日志 API 真实化。
- [ ] 管理员操作入口优化。
- [ ] 邀请码兑换。
- [ ] 用户套餐页真实化。

验收：

- 新用户能创建助理并提交开通申请。
- 管理员能批准。
- 用户能看到真实状态。

### Phase 2：云端资料模式

状态：进行中。

任务：

- [x] AssistantStorage。
- [x] AssistantFile。
- [x] 文件上传 API。
- [x] 文件列表前端。
- [x] MemoryItem API。
- [x] 记忆前端。
- [x] AssistantTask API。
- [x] 任务前端。
- [x] 日志 API。
- [ ] 文件删除和配额回收。
- [ ] 记忆删除和导出。
- [ ] 文档解析任务。
- [ ] 文档摘要结果页。

验收：

- 用户能上传资料。
- 用户能写入/查看记忆。
- 用户能创建任务。
- 任务和日志能关联展示。

### Phase 3：本地代理生态

状态：未开始。

任务：

- [ ] 设计本地代理协议。
- [x] 新增 `DeviceBinding`。
- [x] 新增 `LocalAgent`。
- [x] 新增 `WorkspaceBinding`。
- [ ] 新增 `JobSession`。
- [ ] 新增 `ToolCall`。
- [ ] 新增 `PatchRecord`。
- [ ] 新增 `ConfirmationRequest`。
- [x] 后端设备配对码 API。
- [x] WebSocket 设备连接。
- [x] 本地 CLI 原型。
- [x] 本地目录授权。
- [x] 文件树索引。
- [x] 敏感文件屏蔽规则。
- [ ] 工具调用协议。
- [ ] 命令执行确认机制。

验收：

- 用户能在网页生成配对码。
- 本地代理能输入配对码绑定设备。
- 云端能看到设备在线。
- 用户能绑定一个本地项目目录。
- 云端能下发一个只读搜索任务。
- 本地代理能回传结果摘要。

### Phase 4：Git 云端工作区

状态：未开始。

任务：

- [ ] Git Provider 设计。
- [ ] GitHub/Gitee 授权。
- [ ] 仓库绑定模型。
- [ ] 云端隔离 workspace。
- [ ] 仓库拉取。
- [ ] 分支创建。
- [ ] 运行测试。
- [ ] diff 生成。
- [ ] PR/补丁输出。

验收：

- 用户能绑定一个测试仓库。
- 平台能创建隔离工作区。
- 助理能生成 diff。
- 用户能查看和确认变更。

### Phase 5：Runtime Provider 抽象

状态：未开始。

任务：

- [ ] 新增 `RuntimeProvider` 概念。
- [ ] 任务调度器。
- [ ] 文档工作区 Provider。
- [ ] 本地代理 Provider。
- [ ] Git 工作区 Provider。
- [ ] Hermes Provider。
- [ ] 运行时健康检查。
- [ ] Provider fallback 策略。

验收：

- 一个任务能被调度到不同 Provider。
- 用户能看到任务采用的运行模式。
- Provider 错误能回写日志。

### Phase 6：桌面软件

状态：未开始。

任务：

- [ ] 技术选型：Tauri、Electron 或 CLI-first。
- [ ] 登录与设备绑定。
- [ ] 本地项目选择。
- [ ] 权限设置页。
- [ ] 实时任务页。
- [ ] 日志页。
- [ ] 补丁确认页。
- [ ] 自动更新策略。

验收：

- 用户能安装并登录。
- 用户能绑定项目。
- 用户能看到云端任务。
- 用户能确认或拒绝本地高风险操作。

### Phase 7：商业化与安全

状态：未开始。

任务：

- [ ] 支付或人工订阅流程。
- [ ] 套餐升级。
- [ ] 用量统计。
- [ ] 邀请码。
- [ ] 管理员 2FA。
- [ ] 审计日志覆盖。
- [ ] 备份和恢复。
- [ ] 隐私删除流程。
- [ ] 安全策略文档。

验收：

- 管理员能运营内测用户。
- 用户能看到权益和用量。
- 越权访问被测试覆盖。
- 关键操作可追溯。

## 4. 当前优先级

P0：

- 设备绑定模型设计。
- 本地代理协议文档。
- 前端日志页后续升级为 WebSocket 实时流。

P1：

- 文件删除和配额回收。
- 记忆删除。
- 邀请码兑换。
- 套餐页真实用量。

P2：

- Git 云端工作区。
- 桌面软件原型。
- Hermes Provider。

## 5. 任务追踪规则

每次继续开发时：

1. 先读取本文件。
2. 对照当前代码确认状态，不只相信文档。
3. 更新已完成项。
4. 把新增任务放到对应 Phase。
5. 每次完成后运行相关测试。
6. 最终回复说明：
   - 本轮完成。
   - 修改文件。
   - 验证结果。
   - 下一步建议。

## 6. 验证命令

后端测试：

```powershell
cd "C:\Users\34206\OneDrive\ドキュメント\cloud agent\bairui-platform"
.\.venv\Scripts\python manage.py test assistants
```

迁移：

```powershell
.\.venv\Scripts\python manage.py makemigrations
.\.venv\Scripts\python manage.py migrate
```

前端语法：

```powershell
node --check "C:\Users\34206\Downloads\stitch_\stitch_\app.js"
```

本地服务：

```powershell
.\.venv\Scripts\python manage.py runserver 127.0.0.1:8081
python -m http.server 5177 --bind 127.0.0.1
```

## 7. 关键路径

```text
日志 API
  -> 设备绑定
  -> WebSocket 在线状态
  -> 本地代理 CLI
  -> 本地工作区绑定
  -> 只读工具调用
  -> 补丁/命令确认
  -> Git 云端工作区
  -> Runtime Provider
  -> Hermes 适配
```
