# MOXI Cloud Agent

## Bairui Cloud Agent Platform

This repository now also contains the first commercial platform prototype under `bairui-platform/`.

The platform currently includes:

- Django + DRF backend
- user/password login and SMTP email-code login
- assistant creation and provision approval flow
- plan, subscription, quota, storage, files, memory, tasks, and logs models
- local device pairing code API
- WebSocket device heartbeat endpoint
- local Python CLI agent prototype
- local read-only workspace authorization and safe file-tree indexing

Quick start:

```powershell
cd bairui-platform
copy .env.example .env
docker compose up --build
```

Local development:

```powershell
cd bairui-platform
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python manage.py test assistants
.\.venv\Scripts\python -m unittest bairui_agent.tests
```

See `bairui-platform/README.md` and `bairui-platform/docs/` for the current Bairui Cloud Agent architecture and development plan.

---
# MOXI Server Agent

MOXI Server Agent 是 MOXI 生态的服务器管理代理方案。目标不是魔改 Linux 内核，而是在稳定的 Ubuntu / Debian / OpenCloudOS 基础上，做一个“开机即接入主控”的服务器镜像和 Agent。

这样新服务器创建后，Agent 自动启动并注册到 MOXI 主控后台，后续可以统一完成部署、监控、日志、备份、安全巡检和服务更新。

## 核心定位

- 自建服务器统一管理
- MOXI / WarmStudy / Hermes 等服务的一键部署与运维
- 自定义云镜像预装 Agent
- 主控后台集中查看服务器状态
- 为未来“托管部署服务”打基础，而不是直接做高风险裸服务器出租

## 推荐路线

1. 安装脚本：新服务器执行一条命令，自动安装 Docker、Nginx、安全组件和 Agent。
2. cloud-init：购买云服务器时填入初始化脚本，开机自动接入。
3. 自定义镜像：把安装好 Agent 的系统保存成镜像，以后直接基于镜像开机器。
4. 主控平台：在 MOXI 管理端或独立运维后台管理所有服务器。

## Agent 能力

- 服务器状态：CPU、内存、磁盘、网络、负载。
- 服务管理：Docker 容器、Compose 项目、Nginx、systemd 服务。
- 部署任务：拉取 GitHub 代码、构建镜像、滚动重启、健康检查。
- 安全巡检：SSH 配置、防火墙、Fail2ban、异常登录、危险端口。
- 日志与报警：容器日志、系统日志、异常事件、资源阈值报警。
- 备份任务：数据库、配置文件、上传目录、定时快照。

## 设计原则

- 不在仓库保存密钥、服务器 IP、私钥、数据库密码。
- Agent 不开放公网管理端口，默认主动连接主控。
- 每台服务器使用独立 token，泄露后可单独吊销。
- 指令白名单化，避免主控变成任意远程命令执行入口。
- 所有关键操作要写审计日志。
- 代理管理员不能接触底层服务器权限。

## 文档

- [架构设计](docs/architecture.md)
- [安全边界](docs/security.md)
- [实施路线图](docs/roadmap.md)

## 当前状态

这是第一版方案仓库，先记录架构、边界和实施步骤。后续再逐步加入 Agent 程序、主控 API、安装脚本和镜像构建流程。

