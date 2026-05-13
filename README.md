# SoloCRM - 超级个体销售的极简CRM

> 面向超级个体（单人销售/独立顾问）的极简CRM，深度嵌入MEDDIC方法论，AI全程辅助，一键部署。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ 特性

SoloCRM 只解决超级个体销售最关心的**8件事**，极致简洁：

1. 🎯 **找客户** - 基于成功案例，AI帮你找同行业/同地域相似潜在客户，自动生成开场白
2. 📅 **规划拜访** - 就近推荐顺路客户，减少通勤，定时提醒
3. 📑 **拜访准备** - AI自动搜客户新闻/招投标/领导发言，找到需求切入点
4. 🎙️ **现场记录** - 音频直传转文字，自动区分发言人，轻量不打扰
5. 📝 **事后总结** - AI自动梳理人物关系和关键要点，结构化沉淀
6. 🧠 **MEDDIC复盘** - 每次拜访自动做MEDDIC健康体检，推荐下一步动作
7. 🚀 **规划行程** - 先保证关键动作不遗漏，再优化时间，优先级对齐甲方节点
8. 👀 **多视图浏览** - 待办/地图/时间线/阶段看板，默认展示甲方视角优先级待办

## 🎯 设计哲学

- **超级个体第一** - 不做企业级协作，只服务单人销售
- **极致简洁** - 全程对话交互，AI缺什么问什么，不用填复杂表单
- **AI原生** - 所有结构化提取、复盘、推荐都由AI完成
- **用户掌控** - 数据全存在你自己的数据库，用你自己的AI API Key，没有订阅，没有锁定
- **一键部署** - Docker Compose 一条命令启动，开箱即用

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

1. **录入成功案例** - 对着AI说你刚做成的项目，AI会一步步问你缺的信息，自动结构化保存
2. **找相似客户** - 基于案例让AI帮你找同行业相似潜在客户
3. **规划拜访** - 语音说"明天上午10点去XX见张总"，AI自动生成计划，顺路推荐附近客户
4. **拜访准备** - 出发前AI自动帮你收集客户情报，找到切入点
5. **现场录音** - 手机录音上传，自动转文字区分发言人
6. **总结复盘** - AI自动总结，做MEDDIC复盘，推荐下一步
7. **规划行程** - 把关键动作排入日程，优先级自动对齐甲方节点
8. **日常浏览** - 打开默认就是待办列表，按优先级排序

## 🏗️ 技术架构

- **前端**: React + Vite + TailwindCSS + Leaflet（地图）
- **后端**: Python + FastAPI
- **数据库**: PostgreSQL + pgvector（向量检索）
- **AI**: 对接用户提供的 OpenAI 兼容 API
- **部署**: Docker Compose 一键启动

## 🗺️ 路线图

见 [ROADMAP.md](./ROADMAP.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

详见 [CONTRIBUTING.md](./CONTRIBUTING.md)

## 📄 许可证

MIT License - 见 [LICENSE](./LICENSE)

## 💖 致谢

 Inspired by the open source community and the idea that sales tools should be simple and personal.
