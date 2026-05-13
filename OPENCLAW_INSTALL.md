# OpenClaw 一键部署指南

SoloCRM 原生支持 OpenClaw 部署，可以一键在你的服务器安装完成，直接通过 IM 聊天使用。

## 🚀 一键安装

在你的 OpenClaw 对话中直接发送这条命令：

```
/openclaw clone https://github.com/你的用户名/solocrm
```

OpenClaw 会自动：

1. 克隆代码到你的服务器
2. 提示你输入 AI API Key
3. 自动配置环境变量
4. 启动 Docker Compose 服务
5. 配置完成后直接可以在 IM 中使用

## 💬 使用方式

安装完成后，你直接在 OpenClaw IM 对话中就能使用 SoloCRM，和你平时聊天一样：

```
你：帮我录入一个新的成功案例，我上个月刚做成北京电力的数据中台项目

SoloCRM：请问这个项目是在哪个行业？什么细分领域？
...
```

全程对话交互，不用打开浏览器也能用。

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

## 🎯 优势

通过 OpenClaw 使用 SoloCRM：

- ✅ 不用记命令，一键搞定
- ✅ 直接在 IM 聊天里用，随时随地打开手机就能用
- ✅ 数据还在你自己服务器，安全可控
- ✅ 和你日常工作流无缝整合
