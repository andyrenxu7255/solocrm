import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { customerAPI } from "../../services/api";
import { Card, CardHeader, CardTitle } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Modal } from "../../shared/ui/Modal";
import { Input, Textarea, Select } from "../../shared/ui/Input";

const INDUSTRIES = [
  { value: "", label: "全部行业" },
  { value: "电力", label: "电力" },
  { value: "金融", label: "金融" },
  { value: "制造", label: "制造" },
  { value: "医疗", label: "医疗" },
  { value: "教育", label: "教育" },
  { value: "政府", label: "政府" },
  { value: "互联网", label: "互联网" },
  { value: "能源", label: "能源" },
  { value: "交通", label: "交通" },
];

const STATUS_OPTIONS = [
  { value: "new", label: "新建" },
  { value: "contacted", label: "已联系" },
  { value: "meeting", label: "已会面" },
  { value: "negotiation", label: "谈判中" },
  { value: "won", label: "已成交" },
  { value: "lost", label: "已丢单" },
];

export function CustomerList() {
  const [customers, setCustomers] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: "", company: "", industry: "", city: "" });

  const fetchList = async () => {
    setLoading(true);
    try {
      const data = await customerAPI.list({ page, page_size: 20 });
      setCustomers(data.items || []);
      setTotal(data.total || 0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchList(); }, [page]);

  const handleCreate = async () => {
    await customerAPI.create({
      ...form,
      contact_info: {},
      tags: [],
      status: "new",
    });
    setShowCreate(false);
    setForm({ name: "", company: "", industry: "", city: "" });
    fetchList();
  };

  const statusLabel = (s) => STATUS_OPTIONS.find((o) => o.value === s)?.label || s;
  const statusColor = (s) => {
    const map = { new: "bg-gray-100 text-gray-700", contacted: "bg-blue-100 text-blue-700", meeting: "bg-yellow-100 text-yellow-700", negotiation: "bg-purple-100 text-purple-700", won: "bg-green-100 text-green-700", lost: "bg-red-100 text-red-700" };
    return map[s] || "";
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">客户列表</h2>
        <Button onClick={() => setShowCreate(true)}>+ 新增客户</Button>
      </div>

      {loading ? (
        <p className="text-gray-400">加载中...</p>
      ) : customers.length === 0 ? (
        <p className="text-gray-400">暂无客户数据</p>
      ) : (
        <div className="space-y-3">
          {customers.map((c) => (
            <Link key={c.id} to={`/customers/${c.id}`}>
              <Card className="hover:border-primary-300 transition-colors cursor-pointer">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold text-gray-900">{c.name}</p>
                    <p className="text-sm text-gray-500">
                      {c.company} {c.industry ? `· ${c.industry}` : ""} {c.city ? `· ${c.city}` : ""}
                    </p>
                    {c.tags?.length > 0 && (
                      <div className="flex gap-1 mt-1">{c.tags.map((t, i) => <span key={i} className="text-xs px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">{t}</span>)}</div>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${statusColor(c.status)}`}>{statusLabel(c.status)}</span>
                </div>
              </Card>
            </Link>
          ))}
          {total > 20 && (
            <div className="flex justify-center gap-2 mt-4">
              <Button variant="ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>上一页</Button>
              <span className="px-3 py-1 text-sm text-gray-500">第 {page} 页</span>
              <Button variant="ghost" disabled={page * 20 >= total} onClick={() => setPage(page + 1)}>下一页</Button>
            </div>
          )}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="新增客户">
        <div className="space-y-4">
          <Input label="姓名 *" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input label="公司" value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} />
          <Select label="行业" options={INDUSTRIES} value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} />
          <Input label="城市" value={form.city} onChange={(e) => setForm({ ...form, city: e.target.value })} />
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={handleCreate} disabled={!form.name}>创建</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
