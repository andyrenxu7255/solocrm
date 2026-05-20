# SoloCRM - Agent-First CRM

> 面向超级个体和小型公司，给 agent 使用的本地 CRM。销售、售前、交付、合同和知识都保存在你自己的数据库里。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

1. **销售、售前、交付统一建模**
2. **agent 统一操作入口**
3. **合同范本和知识可持久化迁移**
4. **本地 PostgreSQL 存储**
5. **导出整体业务上下文**

## 🎯 设计哲学

- **Agent-first** - 人类通过自然语言让 agent 操作 CRM
- **本地优先** - 不依赖飞书多维表格这类云表格作为主存储
- **可迁移** - 合同、知识、交付资产都能整体导出
- **用户掌控** - 数据存在你自己的数据库里
- **一键部署** - Docker Compose 启动

## 🚀 快速部署

### 方式一：OpenClaw 一键部署（推荐）

如果你已经安装了 OpenClaw，直接在对话中执行：

```
/openclaw deploy https://github.com/你的用户名/solocrm
```

按照提示填写你的 AI API Key，完成后一键启动，直接通过 IM 使用。

详见 [OPENCLAW_INSTALL.md](./OPENCLAW_INSTALL.md)

### 方式二：手动 Docker Compose 部署

1. 克隆代码：
```bash
git clone https://github.com/你的用户名/solocrm.git
cd solocrm
```

2. 复制环境变量模板：
```bash
cp .env.example .env
```

3. 编辑 `.env`，填入你的 AI API Key：
```env
# 大模型 API Key（OpenAI / 通义千问 / 文心一言，支持任何OpenAI兼容格式）
OPENAI_API_KEY=your-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# 嵌入模型名称
EMBEDDING_MODEL=text-embedding-3-small

# 数据库密码
POSTGRES_PASSWORD=your-db-password
```

4. 启动：
```bash
docker-compose up -d
```

5. 打开浏览器访问 `http://localhost:3000` 即可使用。

## 📖 使用指南

### 核心流程

1. 创建一个业务过程，标记它处于销售、售前还是交付。
2. 让 agent 维护客户、行动项、风险和推进阶段。
3. 把合同范本、知识、方案和交付材料沉淀到可导出的对象里。
4. 需要迁移时，直接导出整套业务上下文。

## 🏗️ 技术架构

- **前端**: React + Vite + TailwindCSS + Leaflet
- **后端**: Python + FastAPI
- **数据库**: PostgreSQL + pgvector
- **AI**: OpenAI 兼容 API
- **Agent 协议**: `/agent/capabilities` 和 `/agent/actions`
- **部署**: Docker Compose

## 🗺️ 路线图

见 [ROADMAP.md](./ROADMAP.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)

## 📄 许可证

MIT License - 见 [LICENSE](./LICENSE)

## 💖 致谢

 Inspired by the open source community and the idea that sales tools should be simple and personal.
