# SoloCRM Graph Memory Design

SoloCRM needs graph memory because sales recall is not only semantic similarity.

Example:

- Industry A, Customer A, Domain A project
- Industry A, Customer B, Domain B project
- Industry B, Customer C, Domain A project

A new Customer D may match by industry, by domain, by project pattern, or by reusable material. Vector search can find similar wording, but it cannot reliably prove which fact path made an old case relevant. Graph memory stores those facts explicitly.

## Story Line

1. Agent records a customer, case, engagement, contract template, proposal, meeting note, or delivery note.
2. SoloCRM extracts or receives facts: industry, customer, domain, project, product, city, and source record.
3. Facts become graph nodes and edges.
4. When a new customer appears, the agent calls graph recall with known facts.
5. Graph recall gates candidate cases and artifacts by explicit shared nodes before ranking.
6. The response includes the old material plus explainable paths such as:
   - `case -> in_industry -> 能源`
   - `case -> serves_domain -> 数据中台`
   - `artifact -> serves_domain -> 数据中台`
7. The agent can safely tell the user why the old case or material was recalled.

## Database Strategy

Apache AGE feasibility note:

- Apache AGE is a PostgreSQL graph extension for graph database workloads.
- It supports openCypher-style graph queries inside PostgreSQL.
- The Apache AGE site announces PostgreSQL 16 compatibility, and the official downloads page includes a PostgreSQL 16 release, so it is a realistic optional path for SoloCRM's PostgreSQL 16 deployment.

pgvector feasibility note:

- pgvector remains the right component for vector similarity search.
- It does not replace graph facts because semantic similarity alone cannot prove industry/customer/domain relationships.

Default storage:

- PostgreSQL tables `graph_nodes` and `graph_edges`
- pgvector remains available for semantic ranking
- graph recall works without any extra database extension
- graph indexes cover node identity, source records, relation type, and both edge directions
- graph edge identity uses PostgreSQL `UNIQUE NULLS NOT DISTINCT`, so repeated manual or agent facts without a source id remain idempotent

Optional enhancement:

- Apache AGE can be enabled with `ENABLE_APACHE_AGE=true` after installing the AGE extension into PostgreSQL.
- AGE is useful for deeper openCypher traversals, long path analytics, and graph-native exploration.
- The core product does not depend on AGE being installed, so standard Docker Compose deployment still works.

This design favors a complete user story first: graph facts are persisted today, explainable recall works today, and AGE remains a forward-compatible acceleration/analytics layer.

## Core Ontology

Node types:

- `industry`
- `customer`
- `domain`
- `project`
- `case`
- `artifact`
- `product`
- `city`

Relation types:

- `in_industry`
- `serves_domain`
- `has_project`
- `uses_product`
- `located_in`
- `has_case`
- `supports_artifact`
- `similar_to`
- `references`

Every edge keeps:

- source type and source id
- confidence
- weight
- evidence text
- original fact payload

## Agent Actions

Graph actions are available through `/agent/actions` and audited in `agent_action_logs`:

- `upsert_graph_fact`
- `graph_recall`
- `rebuild_graph`

CLI equivalents:

```bash
solocrm graph fact --payload-json '{"industry":"能源","customer":"北京电力","domain":"数据中台","project":"数据治理项目"}'
solocrm graph recall --industry 能源 --domain 数据中台 --json
solocrm graph rebuild --json
```

## Recall Contract

Request:

```json
{
  "industry": "能源",
  "domain": "数据中台",
  "query": "找可复用案例和材料",
  "include_artifacts": true,
  "limit": 10
}
```

Response includes:

- `query_nodes`: graph nodes that matched the query facts
- `items`: cases, engagements, and artifacts gated by graph facts
- `shared_nodes`: exact shared industry/domain/customer/project nodes
- `paths`: explainable source-to-fact paths with evidence and confidence
- `gate`: graph gate metadata

## Operational Rule

Agents should prefer this order for serious recall:

1. `solocrm graph rebuild --json` after bulk imports or migrations.
2. `solocrm graph recall ... --json` for sales or presales preparation.
3. Use vector or text search only after graph recall has defined a candidate set.

This prevents an impressive but wrong semantic match from outranking an explicitly related old case.
