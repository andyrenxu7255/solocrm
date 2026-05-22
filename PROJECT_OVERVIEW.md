# SoloCRM 项目总览

**给 AI 开发工具的完整设计文档** - 新的权威设计请优先参考 [docs/agent-first-redesign.md](docs/agent-first-redesign.md)。

## 📋 项目定位

**SoloCRM** = 面向超级个体和小型公司的 agent-first 本地 CRM

- 销售、售前、交付统一建模
- 人类通过 agent 维护 CRM
- 合同、知识、方案、交付材料都可迁移导出
- 数据默认留在自己的 PostgreSQL
- 支持 OpenClaw / Hermes 风格的对话入口
- 提供 `solocrm` CLI 作为 agent 的稳定命令层

## 🎯 核心设计原则

1. **Agent-first** - 系统优先服务 agent 调用
2. **本地优先** - 不依赖云端表格作为主存储
3. **可迁移** - 业务过程与材料可以整体导出
4. **开箱即用** - 默认配置就能跑，不用复杂设置
5. **易于扩展** - 清晰分层，模块化设计，好改好维护

## 🏗️ 架构概览

### 业务架构（三段式）

| 阶段 | 功能 | 核心能力 |
|------|------|----------|
| 销售 | 线索、客户、案例、商机 | 结构化录入、相似案例、开场白 |
| 售前 | 方案、合同、知识、评审 | 文档沉淀、材料复用、风险跟踪 |
| 交付 | 项目执行、会议纪要、行动项 | 过程追踪、交付记录、可导出上下文 |

### 应用架构（分层）

```
前端 (React + Vite)
  ↓
API 网关 (FastAPI)
  ↓
业务逻辑层 (Services)
  ↓
数据访问层 (Repositories)
  ↓
数据库 (PostgreSQL + pgvector)
```

### 数据架构（核心表）

1. `success_cases` - 成功案例
2. `customers` - 潜在客户
3. `visit_plans` - 拜访计划
4. `visit_records` - 拜访记录
5. `todos` - 待办事项
6. `user_product_config` - 用户产品配置
7. `engagements` - 业务过程
8. `business_artifacts` - 合同/知识/交付材料
9. `agent_action_logs` - agent 操作审计

**导出策略**：结构化 JSON 导出整套业务上下文，方便备份、迁移、agent 读取

### 技术架构

| 层级 | 选型 | 理由 |
|------|------|------|
| 前端 | React + Vite + TailwindCSS | 生态成熟，开发快 |
| 地图 | Leaflet | 开源轻量，够用 |
| 后端 | Python + FastAPI | AI 生态好，开发快 |
| 数据库 | PostgreSQL 16 + pgvector | 结构化 + 向量一个库，运维简单 |
| 部署 | Docker Compose | 一键启动，用户友好 |
| AI | OpenAI 兼容 API | 用户自己控制 Key，不绑定厂商 |
| Agent 接口 | REST command API | `/agent/actions` + `/business/export` |
| Agent CLI | Python console script | `solocrm doctor` / `solocrm engagement` / `solocrm audit` / `solocrm export` |
| Agent 审计 | API + CLI | `/agent/audit` + 失败动作留痕 |

## 📂 目录结构

```
solocrm/
├── README.md                    # 项目首页（给用户看）
├── PROJECT_OVERVIEW.md          # 项目总览（给 AI 开发看）
├── ROADMAP.md                   # 迭代路线
├── CONTRIBUTING.md              # 贡献指南
├── OPENCLAW_INSTALL.md          # OpenClaw 部署指南
├── docs/agent-deployment-guide.md # agent 部署与 CLI 接入
├── docs/agent-api-examples.md    # API 样例
├── AGENTS.md                    # agent 入口规则
├── .env.example                 # 环境变量模板
├── docker-compose.yml           # Docker 编排
├── deploy.sh                    # 一键部署脚本
├── openclaw-command.json        # OpenClaw 命令配置
├── pyproject.toml               # CLI 安装入口
├── solocrm_cli/                 # agent CLI
├── skills/solocrm/              # 供 agent 读取的技能
│
├── backend/                     # 后端服务
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # FastAPI 入口
│       ├── config.py            # 配置管理
│       ├── models/              # Pydantic 请求/响应模型
│       ├── services/            # 业务逻辑层
│       ├── repositories/        # 数据访问层
│       ├── schemas/             # SQLAlchemy ORM 模型
│       ├── prompts/             # AI 提示词模板（用户可改）
│       └── utils/               # 工具函数
│
├── frontend/                    # 前端服务
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── components/          # 通用组件
│       ├── pages/               # 页面
│       ├── services/            # API 调用封装
│       └── store/               # 状态管理
│
├── data/                        # 数据目录
│   └── audio/                   # 音频文件存储
│
└── design-system/               # UI/UX 设计系统
    └── solocrm/
        ├── MASTER.md            # 全局设计规则
        └── pages/               # 页面级覆盖规则
```

## 🎨 UI/UX 设计规范

设计系统已持久化到 `design-system/solocrm/MASTER.md`，核心要点：

- **风格**: 扁平化设计 (Flat Design)，干净现代
- **字体**: Plus Jakarta Sans（标题 + 正文统一）
- **色彩**: 专业蓝色系 (#2563EB 主色) + 橙色 CTA (#F97316)
- **交互**: 所有可点击元素 ≥ 44×44px，动画 150-300ms
- **响应式**: 移动优先，支持 375px → 1440px
- **无障碍**: 文本对比度 ≥ 4.5:1，支持键盘导航

**AI 开发必读**：所有 UI 实现必须遵循设计系统规则，不得随意发挥。

## 🔧 开发规范

### 代码风格

- Python: 遵循 PEP 8，使用 black 格式化
- JavaScript: 遵循 ESLint + Prettier
- 命名：见名知意，不用奇怪缩写
- 注释：关键逻辑必须有注释

### 依赖方向

上层依赖下层，下层不依赖上层：
```
前端 → API → Service → Repository → DB
```

### API 规范

所有 API 返回统一格式：
```json
{
  "code": 0,
  "data": { ... },
  "message": "success"
}
```

- `code: 0` 成功，`code: 1` 失败
- 错误必须有清晰的 `message`

### 提示词管理

所有 AI 提示词放在 `backend/app/prompts/` 目录，纯文本 Markdown 文件：

- `case_extraction.md` - 从对话提取案例结构化
- `visit_summary.md` - 拜访总结提取
- `meddic_review.md` - MEDDIC 复盘
- `generate_opening.md` - 生成开场话术

**用户可以自己修改这些文件来自定义 AI 行为，不用改代码。**

### 配置管理

- 所有敏感配置通过环境变量注入
- 提供 `.env.example` 模板
- 用户复制成 `.env` 后填写自己的值

## 🚀 部署流程

### 一键部署（推荐）

用户在 OpenClaw 里说：
```
/deploy solocrm
```

自动完成：
1. 克隆代码
2. 引导填写 API Key
3. 生成随机密码
4. 启动 Docker 服务
5. 健康检查
6. 返回访问地址

### Agent CLI

```bash
python -m pip install -e .
solocrm doctor --json
solocrm capabilities
solocrm audit summary --json
solocrm export --out ./solocrm-export.json
```

### 手动部署

```bash
 git clone https://github.com/andyrenxu7255/solocrm.git
cd solocrm
cp .env.example .env
# 编辑 .env 填写 API Key
docker-compose up -d
```

访问 `http://localhost:3000`

## 📖 核心用户故事（端到端）

1. 用户通过 agent 创建一个销售机会。
2. agent 推进它从销售到售前，再到交付。
3. 关键合同范本和知识被沉淀为可迁移材料。
4. 需要备份时，系统导出整套业务上下文。

## ✅ 验收标准

开发完成后，必须验证以下场景：

- [ ] agent 能创建和更新 engagement
- [ ] agent 能新增业务材料
- [ ] agent 成功和失败写入都能形成审计日志
- [ ] agent 能用 `solocrm audit` 查询失败原因
- [ ] `/business/export` 能导出整套上下文
- [ ] 无 AI Key 时 CRUD 仍可工作
- [ ] Docker Compose 一键启动成功
- [ ] OpenClaw / Hermes 风格 agent 可直接调用
- [ ] `solocrm` CLI 可在安装后直接使用

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

详见 `CONTRIBUTING.md`

## 📄 许可证

MIT License
