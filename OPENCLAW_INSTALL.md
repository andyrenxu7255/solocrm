# OpenClaw 一键部署指南

SoloCRM 原生支持 OpenClaw 部署，可以一键在你的服务器安装完成，直接通过 IM 聊天使用。

## 🚀 一键安装

在你的 OpenClaw 对话中直接发送这条命令：

```
/deploy solocrm
```

OpenClaw 会自动：

1. 克隆代码到你的服务器
2. 提示你输入 AI API Key
3. 自动配置环境变量
4. 启动 Docker Compose 服务
5. 配置完成后直接可以在 IM 中使用

如果你的 OpenClaw 节点能直接执行本地命令，建议再安装 SoloCRM CLI：

```bash
cd ${OPENCLAW_WORKSPACE}/solocrm
python -m pip install -e .
solocrm doctor --json
solocrm audit summary --json
```

## 💬 使用方式

安装完成后，你直接在 OpenClaw IM 对话中就能使用 SoloCRM，和你平时聊天一样：

```
你：帮我录入一个新的成功案例，我上个月刚做成北京电力的数据中台项目

SoloCRM：请问这个项目是在哪个行业？什么细分领域？
...
```

全程对话交互，不用打开浏览器也能用。

如果你想让 agent 更稳定地调用结构化能力，建议优先使用：

- `solocrm doctor --json`
- `solocrm capabilities`
- `solocrm graph recall --industry 能源 --domain 数据中台 --json`
- `solocrm engagement create`
- `solocrm artifact create`
- `solocrm audit errors --json`
- `solocrm export --out ...`

建议把 `skills/solocrm/SKILL.md` 加入 OpenClaw 的技能目录，并把 `AGENTS.md` 中的关键规则加入工作区 instructions。这样 agent 会优先走 CLI/API，不会直接改数据库，也会在失败时先查审计。

## ⚙️ 配置说明

OpenClaw 会自动处理：

- 数据库初始化
- 向量扩展启用
- 端口映射
- 服务重启

如果你需要修改配置，可以直接编辑项目目录下的 `.env` 文件，然后执行：

```
docker-compose up -d --force-recreate
```

## 📂 项目位置

默认安装在你的 OpenClaw 工作区下：

```
${OPENCLAW_WORKSPACE}/solocrm/
```

## 🛟 故障排查

### 服务没启动？

```bash
cd solocrm
docker-compose logs
```

查看日志定位问题。

### 数据库连接失败？

检查 `POSTGRES_PASSWORD` 在 `.env` 中是否正确。

### AI API 调用失败？

检查 `OPENAI_API_KEY` 和 `OPENAI_API_BASE` 是否正确配置。

### agent 写入失败？

```bash
solocrm audit errors --json
```

先查看最新失败动作的 `message` 和审计记录，再修正 payload 重试。

### 要找老案例共同点？

```bash
solocrm graph recall --industry 能源 --domain 数据中台 --json
```

优先使用返回里的 `shared_nodes` 和 `paths`，再决定是否补充语义搜索。

## 🎯 优势

通过 OpenClaw 使用 SoloCRM：

- ✅ 不用记命令，一键搞定
- ✅ 直接在 IM 聊天里用，随时随地打开手机就能用
- ✅ 数据还在你自己服务器，安全可控
- ✅ 和你日常工作流无缝整合
- ✅ 还能通过 `solocrm` CLI 做审计友好的结构化调用
