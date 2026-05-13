# SoloCRM 项目总览

**给 AI 开发工具的完整设计文档** - 所有设计决策、架构规范、开发指南都在这里。

## 📋 项目定位

**SoloCRM** = 面向超级个体（单人销售/独立顾问）的极简 CRM 系统

- **只解决 8 件事**，不做企业级复杂功能
- **全程对话交互**，AI 缺什么问什么，不用填表单
- **深度嵌入 MEDDIC 方法论**，自动复盘推荐动作
- **一键部署**，Docker Compose 一条命令启动
- **OpenClaw 原生集成**，可直接通过 IM 聊天使用
- **开源免费**，MIT 协议，用户数据完全自控

## 🎯 核心设计原则

1. **简洁第一** - 每个模块只解决一个核心问题
2. **AI 原生** - 所有结构化提取、复盘、推荐都由 AI 完成
3. **用户掌控** - 数据存在用户自己的数据库，用用户自己的 AI API Key
4. **开箱即用** - 默认配置就能跑，不用复杂设置
5. **易于扩展** - 清晰分层，模块化设计，好改好维护

## 🏗️ 架构概览

### 业务架构（8 大模块）

| 模块 | 功能 | 核心能力 |
|------|------|----------|
| 1. 找客户 | 相似客户拓客 | 基于成功案例，向量检索 + 结构化过滤，自动生成开场白 |
| 2. 规划拜访 | 拜访计划编排 | 就近推荐顺路客户，定时提醒 |
| 3. 拜访准备 | 客户情报收集 | 自动搜新闻/招投标/领导发言，AI 匹配需求切入点 |
| 4. 现场记录 | 音频转文字 | 录音上传，Whisper 转文字，区分发言人 |
| 5. 事后总结 | 结构化沉淀 | AI 提取人物关系、关键要点，更新知识图谱 |
| 6. MEDDIC 复盘 | 方法论嵌入 | 逐项检查 MEDDIC 覆盖，给出健康评分和动作推荐 |
| 7. 规划行程 | 下一步计划 | 把关键动作排入日程，优先级对齐甲方节点 |
| 8. 浏览界面 | 多视图切换 | 待办 (默认)/地图/时间线/阶段看板 |

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

### 数据架构（6 张核心表）

1. `success_cases` - 成功案例（含向量字段）
2. `customers` - 潜在客户（含向量字段）
3. `visit_plans` - 拜访计划
4. `visit_records` - 拜访记录总结
5. `todos` - 待办事项
6. `user_product_config` - 用户产品配置（含向量字段）

**召回策略**：先结构化过滤（城市/行业）→ 再向量相似度排序 → 混合召回

### 技术架构

| 层级 | 选型 | 理由 |
|------|------|------|
| 前端 | React + Vite + TailwindCSS | 生态成熟，开发快 |
| 地图 | Leaflet | 开源轻量，够用 |
| 后端 | Python + FastAPI | AI 生态好，开发快 |
| 数据库 | PostgreSQL 16 + pgvector | 结构化 + 向量一个库，运维简单 |
| 部署 | Docker Compose | 一键启动，用户友好 |
| AI | OpenAI 兼容 API | 用户自己控制 Key，不绑定厂商 |

## 📂 目录结构

```
solocrm/
├── README.md                    # 项目首页（给用户看）
├── PROJECT_OVERVIEW.md          # 项目总览（给 AI 开发看）
├── ROADMAP.md                   # 迭代路线
├── CONTRIBUTING.md              # 贡献指南
├── OPENCLAW_INSTALL.md          # OpenClaw 部署指南
├── .env.example                 # 环境变量模板
├── docker-compose.yml           # Docker 编排
├── deploy.sh                    # 一键部署脚本
├── openclaw-command.json        # OpenClaw 命令配置
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

### 手动部署

```bash
git clone https://github.com/renxu-solo/solocrm.git
cd solocrm
cp .env.example .env
# 编辑 .env 填写 API Key
docker-compose up -d
```

访问 `http://localhost:3000`

## 📖 核心用户故事（端到端）

详见 `memory/2026-03-23.md` 中的完整用户故事。

简版：
1. 用户录入成功案例（对话式）
2. AI 帮忙找相似客户
3. 规划拜访，顺路推荐
4. 拜访前自动准备情报
5. 现场录音转文字
6. AI 自动总结复盘
7. 推荐下一步动作
8. 排入日程，优先级对齐甲方节点

## ✅ 验收标准

开发完成后，必须验证以下场景：

- [ ] 用户可以对话式录入案例，AI 主动提问补全信息
- [ ] 基于案例能找到相似客户，排序合理
- [ ] 拜访计划可以语音创建，自动提取结构化
- [ ] 就近推荐能工作，减少通勤
- [ ] 音频上传能转文字，区分发言人
- [ ] AI 总结能提取人物关系和关键要点
- [ ] MEDDIC 复盘能给出健康评分和动作推荐
- [ ] 待办列表按甲方节点倒推优先级排序
- [ ] 四视图切换正常（待办/地图/时间线/阶段看板）
- [ ] Docker Compose 一键启动成功
- [ ] OpenClaw IM 可以直接对话使用

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

详见 `CONTRIBUTING.md`

## 📄 许可证

MIT License
