import { useEffect, useMemo, useState } from "react";
import { agentAPI, businessAPI } from "../../services/api";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Input, Textarea, Select } from "../../shared/ui/Input";

const STAGES = [
  { value: "sales", label: "销售" },
  { value: "presales", label: "售前" },
  { value: "contract", label: "合同" },
  { value: "delivery", label: "交付" },
  { value: "renewal", label: "续约" },
  { value: "closed", label: "关闭" },
];

const ARTIFACT_TYPES = [
  { value: "contract_template", label: "合同范本" },
  { value: "knowledge", label: "知识" },
  { value: "proposal", label: "方案" },
  { value: "delivery_note", label: "交付笔记" },
  { value: "meeting_note", label: "会议纪要" },
  { value: "playbook", label: "打法" },
];

export function BusinessPage() {
  const [summary, setSummary] = useState(null);
  const [engagements, setEngagements] = useState([]);
  const [artifacts, setArtifacts] = useState([]);
  const [capabilities, setCapabilities] = useState(null);
  const [actionResult, setActionResult] = useState(null);
  const [exportResult, setExportResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const [engagementForm, setEngagementForm] = useState({
    name: "",
    company: "",
    stage: "sales",
    status: "active",
    owner: "",
    value: "",
    priority: 3,
  });

  const [artifactForm, setArtifactForm] = useState({
    artifact_type: "knowledge",
    title: "",
    content: "",
    summary: "",
    source: "manual",
    version: "1",
  });

  const loadAll = async () => {
    setLoading(true);
    try {
      const [summaryData, engagementsData, artifactsData, capabilityData] =
        await Promise.all([
          businessAPI.summary(),
          businessAPI.engagements.list({ page: 1, page_size: 50 }),
          businessAPI.artifacts.list({ page: 1, page_size: 50 }),
          agentAPI.capabilities(),
        ]);
      setSummary(summaryData);
      setEngagements(engagementsData.items || []);
      setArtifacts(artifactsData.items || []);
      setCapabilities(capabilityData);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAll();
  }, []);

  const stageCounts = useMemo(() => {
    const map = Object.fromEntries(STAGES.map((stage) => [stage.value, 0]));
    for (const item of engagements) {
      map[item.stage] = (map[item.stage] || 0) + 1;
    }
    return map;
  }, [engagements]);

  const createEngagement = async () => {
    await businessAPI.engagements.create({
      ...engagementForm,
      value: engagementForm.value ? Number(engagementForm.value) : null,
      tags: [],
    });
    setEngagementForm({
      name: "",
      company: "",
      stage: "sales",
      status: "active",
      owner: "",
      value: "",
      priority: 3,
    });
    await loadAll();
  };

  const createArtifact = async () => {
    await businessAPI.artifacts.create({
      ...artifactForm,
      tags: [],
    });
    setArtifactForm({
      artifact_type: "knowledge",
      title: "",
      content: "",
      summary: "",
      source: "manual",
      version: "1",
    });
    await loadAll();
  };

  const runAgent = async (action, payload) => {
    const result = await agentAPI.runAction({
      agent_name: "ui",
      action,
      payload,
    });
    setActionResult(result);
    await loadAll();
  };

  const loadExport = async () => {
    const result = await businessAPI.export();
    setExportResult(result);
  };

  return (
    <div className="p-8 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">业务内核</h2>
          <p className="text-sm text-gray-500">销售、售前、交付统一在同一个结构里流转</p>
        </div>
        <Button onClick={loadAll}>刷新</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Metric label="活动过程" value={summary?.active_engagements ?? 0} />
        <Metric label="开放风险" value={summary?.open_risks ?? 0} />
        <Metric label="材料数量" value={artifacts.length} />
        <Metric label="Agent 动作" value={capabilities?.actions ? Object.keys(capabilities.actions || {}).length : 0} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">新建业务过程</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input label="名称" value={engagementForm.name} onChange={(e) => setEngagementForm({ ...engagementForm, name: e.target.value })} />
            <Input label="公司" value={engagementForm.company} onChange={(e) => setEngagementForm({ ...engagementForm, company: e.target.value })} />
            <Select label="阶段" options={STAGES} value={engagementForm.stage} onChange={(e) => setEngagementForm({ ...engagementForm, stage: e.target.value })} />
            <Input label="负责人" value={engagementForm.owner} onChange={(e) => setEngagementForm({ ...engagementForm, owner: e.target.value })} />
            <Input label="金额" type="number" value={engagementForm.value} onChange={(e) => setEngagementForm({ ...engagementForm, value: e.target.value })} />
            <Input label="优先级" type="number" value={engagementForm.priority} onChange={(e) => setEngagementForm({ ...engagementForm, priority: e.target.value })} />
          </div>
          <div className="mt-4 flex justify-end">
            <Button onClick={createEngagement} disabled={!engagementForm.name}>创建过程</Button>
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">沉淀可迁移材料</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Select label="类型" options={ARTIFACT_TYPES} value={artifactForm.artifact_type} onChange={(e) => setArtifactForm({ ...artifactForm, artifact_type: e.target.value })} />
            <Input label="标题" value={artifactForm.title} onChange={(e) => setArtifactForm({ ...artifactForm, title: e.target.value })} />
          </div>
          <Textarea label="内容" className="mt-4" value={artifactForm.content} onChange={(e) => setArtifactForm({ ...artifactForm, content: e.target.value })} rows={4} />
          <Textarea label="摘要" className="mt-4" value={artifactForm.summary} onChange={(e) => setArtifactForm({ ...artifactForm, summary: e.target.value })} rows={3} />
          <div className="mt-4 flex justify-end">
            <Button onClick={createArtifact} disabled={!artifactForm.title}>保存材料</Button>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">阶段分布</h3>
          <div className="space-y-3">
            {STAGES.map((stage) => (
              <div key={stage.value} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{stage.label}</span>
                <span className="text-sm font-medium text-gray-900">{stageCounts[stage.value] || 0}</span>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Agent 控制</h3>
          <div className="space-y-3">
            <Button variant="secondary" className="w-full" onClick={loadExport}>
              导出上下文
            </Button>
            <Button variant="secondary" className="w-full" onClick={() => runAgent("get_pipeline_summary", {})}>
              取业务摘要
            </Button>
            <Button variant="secondary" className="w-full" onClick={() => runAgent("create_engagement", { name: "演示项目", company: "未命名公司", stage: "sales" })}>
              快速建一个过程
            </Button>
            <Button variant="secondary" className="w-full" onClick={() => runAgent("add_artifact", { artifact_type: "knowledge", title: "演示知识", content: "placeholder" })}>
              快速存一条材料
            </Button>
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">Agent 返回</h3>
          <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words bg-gray-50 p-3 rounded-lg min-h-40">
            {actionResult ? JSON.stringify(actionResult.result, null, 2) : "还没有动作"}
          </pre>
        </Card>
      </div>

      <Card>
        <h3 className="font-semibold text-gray-900 mb-4">导出结果</h3>
        <pre className="text-xs text-gray-600 whitespace-pre-wrap break-words bg-gray-50 p-3 rounded-lg min-h-32">
          {exportResult ? JSON.stringify(exportResult, null, 2) : "还没有导出"}
        </pre>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">业务过程</h3>
          <div className="space-y-3">
            {loading && <p className="text-sm text-gray-400">加载中...</p>}
            {!loading && engagements.length === 0 && <p className="text-sm text-gray-400">暂无业务过程</p>}
            {engagements.map((item) => (
              <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">{item.name}</p>
                    <p className="text-sm text-gray-500">{item.company} · {item.stage} · {item.status}</p>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => runAgent("advance_stage", { engagement_id: item.id, stage: item.stage === "sales" ? "presales" : "delivery" })}>
                    推进
                  </Button>
                </div>
                {item.next_actions?.length > 0 && (
                  <div className="mt-2 text-xs text-gray-500">
                    下一步: {item.next_actions.slice(0, 2).map((a) => a.title || a.action || "action").join(" / ")}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h3 className="font-semibold text-gray-900 mb-4">可迁移材料</h3>
          <div className="space-y-3">
            {artifacts.length === 0 && <p className="text-sm text-gray-400">暂无材料</p>}
            {artifacts.map((item) => (
              <div key={item.id} className="rounded-lg border border-gray-200 p-4">
                <p className="font-medium text-gray-900">{item.title}</p>
                <p className="text-sm text-gray-500">{item.artifact_type} · {item.version}</p>
                {item.summary && <p className="text-sm text-gray-600 mt-1">{item.summary}</p>}
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <Card>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-gray-900">{value}</p>
    </Card>
  );
}
