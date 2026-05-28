# SoloCRM Agent User Storylines

This document describes acceptance storylines for SoloCRM as an agent-first CRM. Each story is written for OpenClaw, Hermes, or a similar agent that operates SoloCRM through natural language, CLI commands, and audited HTTP actions.

The goal is not to prove that SoloCRM has a screen for every task. The goal is to prove that an agent can manage the sales, presales, contract, delivery, knowledge, graph recall, audit, and export lifecycle without direct human database work.

## Operating Rule

Agents should use this order:

1. Check `solocrm doctor --json`.
2. Check `solocrm capabilities`.
3. Write through audited actions such as `create_engagement`, `add_artifact`, `upsert_graph_fact`, and `rebuild_graph`.
4. Use `graph_recall` before broad semantic search when the user asks for old cases, reusable material, or similar customers.
5. Read `shared_nodes`, `paths`, `evidence`, and `gate` before using a recalled item.
6. Inspect `solocrm audit errors --json` after failed writes.
7. Use `solocrm export --out ...` for migration and backup.

## Automated Coverage Map

The acceptance suite lives in `backend/tests/test_user_storylines.py`. It checks that every documented `STORY-*` id remains wired to an executable test path, then validates the graph-first recall behavior, artifact reuse, audit recovery, export portability, rebuild mapping, and no-false-recall guard.

| Story ids | Automated path |
| --- | --- |
| `STORY-01`, `STORY-02`, `STORY-08` | Sales lead facts, exact industry+domain ranking, and cross-industry domain reuse |
| `STORY-03`, `STORY-06`, `STORY-07`, `STORY-14` | Proposal, contract, delivery note, and knowledge/playbook artifact recall |
| `STORY-04`, `STORY-05` | Product-led and city-led graph gates |
| `STORY-09`, `STORY-13` | Failed agent action audit recovery and multi-agent audit separation |
| `STORY-10` | Portable export context with engagements, artifacts, graph, and audit |
| `STORY-11` | Rebuild mapping from imported customers, cases, engagements, and artifacts |
| `STORY-12`, `STORY-15` | PostgreSQL-table graph recall without AGE and empty recall when facts are missing |

## Story 01: New Sales Lead From Chat

Scenario:

A founder sends a WeChat message: "帮我记录，北京电力想看数据中台方案，预算大概 50 万，下周约电话。"

Agent path:

1. Create an engagement in `sales` stage with company, owner, estimated value, and next action.
2. Upsert graph facts for `industry=能源`, `customer=北京电力`, `domain=数据中台`, and project name.
3. Confirm the action through audit.

Expected result:

- Engagement exists with stage `sales`.
- Graph contains customer, industry, domain, and project nodes.
- Audit log records `create_engagement` and `upsert_graph_fact`.

Acceptance test:

- `STORY-01-new-sales-lead`

## Story 02: Similar Case Before First Call

Scenario:

Before the first call, the user asks: "这个能源客户聊数据中台，之前有什么相似项目？"

Agent path:

1. Run graph recall with `industry=能源` and `domain=数据中台`.
2. Rank exact industry+domain matches above single-node matches.
3. Return the case or project with the explanation path.

Expected result:

- Exact same industry and domain items score higher.
- Same industry but different domain items are still visible with lower score.
- Same domain but different industry items are visible with lower score.
- Response includes `paths` and `evidence`.

Acceptance test:

- `STORY-02-similar-case-before-call`

## Story 03: Presales Material Pack

Scenario:

The user says: "给这个客户准备售前材料，先找可复用的方案、合同范本和交付说明。"

Agent path:

1. Store proposal, contract template, and delivery note as artifacts.
2. Upsert graph facts linking artifacts to customer, industry, domain, project, and product.
3. Run graph recall with artifacts enabled.

Expected result:

- Artifacts are returned as recall targets.
- Artifact paths show why the material is related.
- The agent can cite whether material matches by industry, domain, product, or customer.

Acceptance test:

- `STORY-03-presales-material-pack`

## Story 04: Product-Led Recall

Scenario:

The user says: "这个客户想上 SoloBI，找所有做过 SoloBI 的案例，不限行业。"

Agent path:

1. Upsert facts that include `product=SoloBI`.
2. Recall by product only.
3. Use the product node as the graph gate before semantic search.

Expected result:

- Returned items share the `product` node.
- Non-product semantic matches are not allowed to outrank product-linked facts.

Acceptance test:

- `STORY-04-product-led-recall`

## Story 05: City Or Regional Reuse

Scenario:

The user says: "下周去上海拜访，看看上海有哪些客户、案例和材料能顺手复用。"

Agent path:

1. Upsert graph facts with `city=上海`.
2. Recall by city.
3. Summarize customers, projects, and artifacts that share the city node.

Expected result:

- Recall works even if industry or domain is unknown.
- `located_in` paths explain the regional match.

Acceptance test:

- `STORY-05-city-regional-reuse`

## Story 06: Contract Template During Negotiation

Scenario:

The user says: "对方法务要标准合同和数据安全条款，帮我存一版并以后能找回。"

Agent path:

1. Add a `contract_template` artifact.
2. Link the artifact to domain and product graph facts.
3. Later recall by domain or product.

Expected result:

- Contract template persists as a business artifact.
- Graph recall can return it with `supports_artifact` or artifact-domain paths.
- Export includes the artifact and graph facts.

Acceptance test:

- `STORY-06-contract-template-negotiation`

## Story 07: Delivery Handoff Memory

Scenario:

After winning, the user says: "转交付了，把风险、上线计划和客户特殊要求记下来。"

Agent path:

1. Advance the engagement to `delivery`.
2. Update delivery JSON, next actions, and risks.
3. Add delivery notes as artifacts.
4. Upsert graph facts so future recalls can find the delivery experience.

Expected result:

- Engagement stage becomes `delivery`.
- Delivery note is persisted.
- Graph recall can retrieve the delivery note by customer, industry, domain, or project.

Acceptance test:

- `STORY-07-delivery-handoff-memory`

## Story 08: Cross-Industry Domain Reuse

Scenario:

A finance customer asks about data middle platform. The old best case is in energy. The user asks: "虽然行业不同，领域相同的案例有哪些？"

Agent path:

1. Recall by `domain=数据中台`.
2. Keep cross-industry results, but explain that the shared node is domain only.
3. Avoid claiming industry similarity.

Expected result:

- Energy and finance projects can both be recalled through the domain node.
- `shared_nodes` contains domain, not an invented industry match.

Acceptance test:

- `STORY-08-cross-industry-domain-reuse`

## Story 09: Audit Recovery After Bad Command

Scenario:

The agent sends an invalid action or bad stage during a chat workflow.

Agent path:

1. The failed action is written to audit with `status=error`.
2. Agent reads recent audit errors.
3. Agent corrects the payload and retries once.

Expected result:

- Failure is visible through audit.
- The user does not need database access to debug the agent.

Acceptance test:

- `STORY-09-audit-recovery`

## Story 10: Migration And Backup

Scenario:

The user says: "我要从本机迁到服务器，先导出完整上下文。"

Agent path:

1. Run export.
2. Verify exported format version.
3. Confirm that engagements, artifacts, graph nodes, graph edges, and audit logs are present.

Expected result:

- Export format is `solocrm-agent-context-v2`.
- Graph memory and audit trail are portable.

Acceptance test:

- `STORY-10-migration-backup`

## Story 11: Bulk Import Rebuild

Scenario:

The user imports old customers, old cases, and old artifacts. The agent needs to build graph memory from existing rows.

Agent path:

1. Run `rebuild_graph`.
2. Derive facts from customers, success cases, engagements, and artifacts.
3. Recall against the rebuilt graph.

Expected result:

- Rebuild creates graph nodes and edges without manual re-entry.
- Recall works after import.

Acceptance test:

- `STORY-11-bulk-import-rebuild`

## Story 12: Lightweight Deployment Without AGE

Scenario:

A small company deploys with default Docker Compose and does not install Apache AGE.

Agent path:

1. Start PostgreSQL with pgvector image.
2. Keep `ENABLE_APACHE_AGE=false`.
3. Use graph facts and graph recall normally.

Expected result:

- Core graph recall works without AGE.
- AGE remains optional for advanced graph analytics.

Acceptance test:

- `STORY-12-lightweight-without-age`

## Story 13: Multi-Agent Channel Operation

Scenario:

OpenClaw receives a Feishu message while Hermes receives a WeChat message. Both operate the same CRM through the CLI.

Agent path:

1. Each agent sets `SOLOCRM_AGENT_NAME`.
2. Both write through `/agent/actions`.
3. Audit can filter by agent name.

Expected result:

- Same database is shared.
- Agent-specific audit history remains distinguishable.

Acceptance test:

- `STORY-13-multi-agent-channel-operation`

## Story 14: Knowledge Management For Reusable Playbooks

Scenario:

The user says: "把能源行业数据治理开场白和异议处理沉淀成知识，下次同类客户直接找。"

Agent path:

1. Add a `playbook` or `knowledge` artifact.
2. Link it to industry, domain, and product graph facts.
3. Recall by industry/domain before a new conversation.

Expected result:

- Knowledge is stored as portable artifact content.
- Graph recall returns the playbook through explicit fact paths.

Acceptance test:

- `STORY-14-knowledge-playbook-reuse`

## Story 15: No False Recall When Facts Are Missing

Scenario:

The user asks about a new and unknown industry/domain combination.

Agent path:

1. Run graph recall with unknown facts.
2. Do not invent related cases.
3. Tell the user that graph memory has no matched facts and optionally suggest recording new facts.

Expected result:

- Recall returns no items.
- Gate reason explains `no query nodes matched`.

Acceptance test:

- `STORY-15-no-false-recall`
