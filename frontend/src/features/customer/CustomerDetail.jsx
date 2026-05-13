import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { customerAPI, aiAPI, caseAPI } from "../../services/api";
import { Card, CardHeader, CardTitle } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Input, Textarea, Select } from "../../shared/ui/Input";

const STATUS_OPTIONS = [
  { value: "new", label: "新建" },
  { value: "contacted", label: "已联系" },
  { value: "meeting", label: "已会面" },
  { value: "negotiation", label: "谈判中" },
  { value: "won", label: "已成交" },
  { value: "lost", label: "已丢单" },
];

const INDUSTRIES = [
  { value: "", label: "-" },
  { value: "电力", label: "电力" }, { value: "金融", label: "金融" },
  { value: "制造", label: "制造" }, { value: "医疗", label: "医疗" },
  { value: "教育", label: "教育" }, { value: "政府", label: "政府" },
  { value: "互联网", label: "互联网" }, { value: "能源", label: "能源" },
  { value: "交通", label: "交通" },
];

export function CustomerDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [loading, setLoading] = useState(true);
  const [meddicLoading, setMeddicLoading] = useState(false);
  const [openingLoading, setOpeningLoading] = useState(false);
  const [opening, setOpening] = useState(null);
  const [intelLoading, setIntelLoading] = useState(false);
  const [intel, setIntel] = useState(null);
  const [cases, setCases] = useState([]);

  const fetchCustomer = async () => {
    try {
      const c = await customerAPI.get(id);
      setCustomer(c);
      setForm(c);
    } catch {} finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomer();
    caseAPI.list({ page: 1, page_size: 50 }).then((d) => setCases(d.items || [])).catch(() => {});
  }, [id]);

  const handleSave = async () => {
    const updated = await customerAPI.update(id, form);
    setCustomer(updated);
    setEditing(false);
  };

  const handleDelete = async () => {
    if (!confirm("确定删除？")) return;
    await customerAPI.remove(id);
    navigate("/customers");
  };

  const handleMeddic = async () => {
    setMeddicLoading(true);
    try {
      const updated = await aiAPI.meddic({ customer_id: id });
      setCustomer(updated);
    } catch (e) {
      alert("MEDDIC 复盘失败: " + e.message);
    } finally {
      setMeddicLoading(false);
    }
  };

  const handleOpening = async () => {
    setOpeningLoading(true);
    try {
      const matchedCase = cases.find((c) => c.industry === customer.industry);
      const result = await aiAPI.opening({ customer_id: id, case_id: matchedCase?.id || null });
      setOpening(result.content);
    } catch (e) {
      alert("生成失败: " + e.message);
    } finally {
      setOpeningLoading(false);
    }
  };

  const handleIntel = async () => {
    setIntelLoading(true);
    try {
      const result = await aiAPI.intel({ customer_id: id });
      setIntel(result);
    } catch (e) {
      alert("情报获取失败: " + e.message);
    } finally {
      setIntelLoading(false);
    }
  };

  const dimLabels = {
    metrics: "M - 指标", economic_buyer: "E - 经济决策者",
    decision_criteria: "D - 决策标准", decision_process: "D - 决策流程",
    pain_points: "I - 痛点", champion: "C - 支持者",
  };

  if (loading) return <div className="p-8 text-gray-400">加载中...</div>;
  if (!customer) return <div className="p-8 text-red-500">客户不存在</div>;

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <Button variant="ghost" onClick={() => navigate("/customers")}>&larr; 返回</Button>
        <div className="flex gap-2">
          {editing ? (
            <>
              <Button variant="ghost" onClick={() => setEditing(false)}>取消</Button>
              <Button onClick={handleSave}>保存</Button>
            </>
          ) : (
            <>
              <Button variant="secondary" onClick={() => setEditing(true)}>编辑</Button>
              <Button variant="primary" onClick={handleMeddic} disabled={meddicLoading}>
                {meddicLoading ? "评估中..." : "MEDDIC复盘"}
              </Button>
              <Button onClick={handleOpening} disabled={openingLoading}>
                {openingLoading ? "生成中..." : "开场白"}
              </Button>
              <Button variant="secondary" onClick={handleIntel} disabled={intelLoading}>
                {intelLoading ? "搜集中..." : "客户情报"}
              </Button>
              <Button variant="danger" onClick={handleDelete}>删除</Button>
            </>
          )}
        </div>
      </div>

      {opening && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-xl">
          <p className="text-xs text-blue-500 mb-1 font-medium">AI 生成开场白</p>
          <pre className="text-sm text-blue-800 whitespace-pre-wrap font-sans">{opening}</pre>
        </div>
      )}

      {intel && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl">
          <p className="text-xs text-green-600 mb-1 font-medium">客户情报</p>
          <p className="text-sm text-green-800 mb-2">{intel.summary}</p>
          {intel.results?.length > 0 && (
            <div className="space-y-1">
              {intel.results.map((r, i) => (
                <a key={i} href={r.url} target="_blank" rel="noopener noreferrer" className="block text-xs text-green-700 hover:underline">
                  {i + 1}. {r.title}
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {editing ? (
        <div className="space-y-4 max-w-lg">
          <Input label="姓名" value={form.name || ""} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="公司" value={form.company || ""} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          <Input label="职位" value={form.title || ""} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Select label="行业" options={INDUSTRIES} value={form.industry || ""} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
          <Input label="城市" value={form.city || ""} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          <Select label="状态" options={STATUS_OPTIONS} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} />
          <Textarea label="备注" value={form.notes || ""} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={6} />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader><CardTitle>基本信息</CardTitle></CardHeader>
            <dl className="space-y-2 text-sm">
              <InfoRow label="姓名" value={customer.name} />
              <InfoRow label="公司" value={customer.company} />
              <InfoRow label="职位" value={customer.title} />
              <InfoRow label="行业" value={customer.industry} />
              <InfoRow label="城市" value={customer.city} />
              <InfoRow label="状态" value={STATUS_OPTIONS.find((o) => o.value === customer.status)?.label} />
            </dl>
          </Card>
          <Card>
            <CardHeader><CardTitle>备注</CardTitle></CardHeader>
            <p className="text-sm text-gray-600 whitespace-pre-wrap">{customer.notes || "无"}</p>
          </Card>
          {customer.meddic_json ? (
            <Card className="md:col-span-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>MEDDIC 健康评估</CardTitle>
                  <span className={`text-lg font-bold ${customer.meddic_json.health_score >= 70 ? "text-green-600" : customer.meddic_json.health_score >= 40 ? "text-yellow-600" : "text-red-600"}`}>
                    {customer.meddic_json.health_score}/100
                  </span>
                </div>
              </CardHeader>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                {Object.entries(customer.meddic_json).filter(([k]) => dimLabels[k]).map(([dim, data]) => (
                  <div key={dim} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-700">{dimLabels[dim]}</span>
                      <span className="text-xs font-bold text-gray-900">{data.score ?? "-"}/10</span>
                    </div>
                    {data.notes && <p className="text-xs text-gray-500">{data.notes}</p>}
                  </div>
                ))}
              </div>
              {customer.meddic_json.gaps?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-red-600 mb-1">待补维度</p>
                  {customer.meddic_json.gaps.map((g, i) => (
                    <span key={i} className="inline-block text-xs px-2 py-0.5 bg-red-50 text-red-700 rounded mr-1 mb-1">{g}</span>
                  ))}
                </div>
              )}
            </Card>
          ) : (
            <Card className="md:col-span-2">
              <p className="text-sm text-gray-400">尚未进行 MEDDIC 评估，点击上方"MEDDIC复盘"按钮开始</p>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return <div className="flex"><dt className="w-20 text-gray-400">{label}</dt><dd className="text-gray-900">{value || "-"}</dd></div>;
}
