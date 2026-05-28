# SoloCRM - Agent-First CRM

> 面向超级个体和小型公司，给 agent 使用的本地 CRM。销售、售前、交付、合同和知识都保存在你自己的数据库里。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

1. **销售、售前、交付统一建模**
2. **agent 统一操作入口**
3. **合同范本和知识可持久化迁移**
4. **本地 PostgreSQL 存储**
5. **行业/客户/领域/项目图记忆**
6. **agent 操作审计和失败追溯**
7. **导出整体业务上下文**

## 🎯 设计哲学

- **Agent-first** - 人类通过自然语言让 agent 操作 CRM
- **本地优先** - 不依赖飞书多维表格这类云表格作为主存储
- **图记忆优先** - 重要销售召回先用事实图门控，再做语义补充
- **可迁移** - 合同、知识、交付资产都能整体导出
- **用户掌控** - 数据存在你自己的数据库里
- **一键部署** - Docker Compose 启动

## 🚀 快速部署

### 方式一：OpenClaw 一键部署（推荐）

如果你已经安装了 OpenClaw，直接在对话中执行：

```
/deploy solocrm
```

按照提示填写你的 AI API Key，完成后一键启动，直接通过 IM 使用。

详见 [OPENCLAW_INSTALL.md](./OPENCLAW_INSTALL.md)

### 方式二：手动 Docker Compose 部署

1. 克隆代码：
```bash
git clone https://github.com/andyrenxu7255/solocrm.git
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

### 方式三：安装 agent CLI

如果你要让 OpenClaw、Hermes 或其他本地 agent 直接调用 SoloCRM，先安装 CLI：

```bash
python -m pip install -e .
solocrm doctor --json
```

常用命令：

```bash
solocrm capabilities
solocrm engagement list
solocrm graph recall --industry 能源 --domain 数据中台 --json
solocrm graph recall --customer 北京电力 --max-hops 2 --json
solocrm audit summary --json
solocrm audit errors --json
solocrm db info
solocrm export --out ./solocrm-export.json
```

## 📖 使用指南

### 核心流程

1. 创建一个业务过程，标记它处于销售、售前还是交付。
2. 让 agent 维护客户、行动项、风险和推进阶段。
3. 把行业、客户、领域、项目、案例和材料沉淀成图关系。
4. 面向新客户准备时，先用图召回共同点和老材料。
5. 常规召回默认 1 跳；相似案例分析才使用 `--max-hops 2`，且只能通过行业、领域、产品、城市这些白名单事实桥接。
6. 如果写入失败，agent 先查看审计错误再修正重试。
7. 需要迁移时，直接导出整套业务上下文。

## 🏗️ 技术架构

- **前端**: React + Vite + TailwindCSS + Leaflet
- **后端**: Python + FastAPI
- **数据库**: PostgreSQL + pgvector + 可选 Apache AGE
- **AI**: OpenAI 兼容 API
- **Agent 协议**: `/agent/capabilities` 和 `/agent/actions`
- **图记忆**: `/graph/facts` / `/graph/recall` / `solocrm graph`
- **Agent 审计**: `/agent/audit` 和 `solocrm audit`
- **Agent CLI**: `solocrm doctor` / `solocrm engagement` / `solocrm audit` / `solocrm export`
- **部署**: Docker Compose
- **前端构建**: Vite 7，需要 Node.js 20.19+ 或 22.12+

## 🗺️ 路线图

见 [ROADMAP.md](./ROADMAP.md)

## 🧭 用户故事线

见 [docs/user-storylines.md](./docs/user-storylines.md)。该文档覆盖 15 条 agent 操作路径，包括销售线索、售前材料、产品召回、区域复用、合同模板、交付交接、审计恢复、迁移备份和无 AGE 部署。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)

## 📄 许可证

MIT License - 见 [LICENSE](./LICENSE)

## 💖 致谢

 Inspired by the open source community and the idea that sales tools should be simple and personal.
