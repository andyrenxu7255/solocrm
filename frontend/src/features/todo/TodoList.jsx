import { useState, useEffect } from "react";
import { todoAPI, customerAPI } from "../../services/api";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Modal } from "../../shared/ui/Modal";
import { Input, Textarea, Select } from "../../shared/ui/Input";

const STATUS_OPTIONS = [
  { value: "pending", label: "待办" },
  { value: "in_progress", label: "进行中" },
  { value: "done", label: "已完成" },
];

const STATUS_COLORS = {
  pending: "border-l-gray-300",
  in_progress: "border-l-blue-400",
  done: "border-l-green-400",
};

const MEDDIC_DIMS = [
  { value: "", label: "全部维度" },
  { value: "metrics", label: "M - 指标" },
  { value: "economic_buyer", label: "E - 经济决策者" },
  { value: "decision_criteria", label: "D - 决策标准" },
  { value: "decision_process", label: "D - 决策流程" },
  { value: "pain_points", label: "I - 痛点" },
  { value: "champion", label: "C - 支持者" },
];

export function TodoList() {
  const [todos, setTodos] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [view, setView] = useState("kanban");
  const [filter, setFilter] = useState("");
  const [form, setForm] = useState({
    title: "", description: "", priority: 0, due_date: "",
    status: "pending", customer_id: "", meddic_dim: "",
  });

  const fetchTodos = async () => {
    setLoading(true);
    try {
      const data = await todoAPI.list({ page: 1, page_size: 200 });
      setTodos(data.items || []);
    } finally {
      setLoading(false);
    }
  };

  const fetchCustomers = async () => {
    try {
      const data = await customerAPI.list({ page: 1, page_size: 200 });
      setCustomers(data.items || []);
    } catch {}
  };

  useEffect(() => { fetchTodos(); fetchCustomers(); }, []);

  const createTodo = async () => {
    await todoAPI.create({
      ...form,
      priority: parseInt(form.priority) || 0,
      due_date: form.due_date || null,
      customer_id: form.customer_id || null,
      source: "manual",
    });
    setShowCreate(false);
    setForm({ title: "", description: "", priority: 0, due_date: "", status: "pending", customer_id: "", meddic_dim: "" });
    fetchTodos();
  };

  const toggleStatus = async (todo) => {
    const next = todo.status === "done" ? "pending" : todo.status === "pending" ? "in_progress" : "done";
    await todoAPI.update(todo.id, { status: next });
    fetchTodos();
  };

  const deleteTodo = async (id) => {
    await todoAPI.remove(id);
    fetchTodos();
  };

  const filtered = filter
    ? todos.filter((t) => t.meddic_dim === filter || (!filter && true))
    : todos;

  const kanbanColumns = ["pending", "in_progress", "done"];
  const getCustomerName = (cid) => customers.find((c) => c.id === cid)?.name || "";

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">待办事项</h2>
        <div className="flex gap-2">
          <Select options={MEDDIC_DIMS} value={filter} onChange={(e) => setFilter(e.target.value)} className="w-40" />
          <Button variant={view === "kanban" ? "primary" : "secondary"} onClick={() => setView("kanban")}>看板</Button>
          <Button variant={view === "list" ? "primary" : "secondary"} onClick={() => setView("list")}>列表</Button>
          <Button onClick={() => setShowCreate(true)}>+ 新建</Button>
        </div>
      </div>

      {view === "kanban" ? (
        <div className="grid grid-cols-3 gap-4">
          {kanbanColumns.map((col) => (
            <div key={col} className="bg-gray-50 rounded-xl p-4">
              <h3 className="text-sm font-semibold text-gray-500 mb-3 uppercase">
                {STATUS_OPTIONS.find((o) => o.value === col)?.label}
                <span className="ml-2 text-xs font-normal">{filtered.filter((t) => t.status === col).length}</span>
              </h3>
              <div className="space-y-2">
                {filtered.filter((t) => t.status === col).sort((a, b) => b.priority - a.priority).map((t) => (
                  <Card key={t.id} className="p-4 cursor-pointer hover:shadow-md transition-shadow">
                    <p className="text-sm font-medium text-gray-900">{t.title}</p>
                    {t.description && <p className="text-xs text-gray-500 mt-1">{t.description.slice(0, 80)}</p>}
                    <div className="flex flex-wrap gap-1 mt-2">
                      {t.meddic_dim && <span className="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded">{t.meddic_dim}</span>}
                      {t.customer_id && <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">{getCustomerName(t.customer_id)}</span>}
                      {t.due_date && <span className="text-xs text-gray-400">截止: {t.due_date}</span>}
                    </div>
                    <div className="flex gap-1 mt-2">
                      {col !== "done" && <Button variant="ghost" size="sm" onClick={() => toggleStatus(t)}>→</Button>}
                      <Button variant="danger" size="sm" onClick={() => deleteTodo(t.id)}>×</Button>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {loading && <p className="text-gray-400">加载中...</p>}
          {!loading && filtered.length === 0 && <p className="text-gray-400">暂无待办事项</p>}
          {filtered.map((t) => (
            <Card key={t.id} className={`border-l-4 ${STATUS_COLORS[t.status] || "border-l-gray-300"}`}>
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  <input type="checkbox" checked={t.status === "done"} onChange={() => toggleStatus(t)}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
                  <div>
                    <p className={`font-medium ${t.status === "done" ? "text-gray-400 line-through" : "text-gray-900"}`}>{t.title}</p>
                    {t.description && <p className="text-sm text-gray-500 mt-0.5">{t.description}</p>}
                    <div className="flex gap-2 mt-1">
                      {t.meddic_dim && <span className="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-700 rounded">{t.meddic_dim}</span>}
                      {t.customer_id && <span className="text-xs px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded">{getCustomerName(t.customer_id)}</span>}
                      {t.due_date && <span className="text-xs text-gray-400">截止: {t.due_date}</span>}
                      <span className="text-xs text-gray-400">P{t.priority}</span>
                    </div>
                  </div>
                </div>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => toggleStatus(t)}>
                    {t.status === "done" ? "重开" : t.status === "pending" ? "开始" : "完成"}
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => deleteTodo(t.id)}>删</Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal open={showCreate} onClose={() => setShowCreate(false)} title="新建待办">
        <div className="space-y-4">
          <Input label="标题 *" value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} />
          <Textarea label="描述" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={3} />
          <div className="grid grid-cols-2 gap-4">
            <Input label="优先级" type="number" value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} />
            <Select label="MEDDIC维度" options={MEDDIC_DIMS} value={form.meddic_dim} onChange={(e) => setForm({ ...form, meddic_dim: e.target.value })} />
          </div>
          <Input label="截止日期" type="date" value={form.due_date} onChange={(e) => setForm({ ...form, due_date: e.target.value })} />
          <Select label="状态" options={STATUS_OPTIONS} value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} />
          <Select label="关联客户" options={[{ value: "", label: "-" }, ...customers.map((c) => ({ value: c.id, label: `${c.name} (${c.company})` }))]}
            value={form.customer_id} onChange={(e) => setForm({ ...form, customer_id: e.target.value })} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowCreate(false)}>取消</Button>
            <Button onClick={createTodo} disabled={!form.title}>创建</Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
