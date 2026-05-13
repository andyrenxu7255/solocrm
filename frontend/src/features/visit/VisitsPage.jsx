import { useState, useEffect } from "react";
import { visitAPI, customerAPI } from "../../services/api";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Modal } from "../../shared/ui/Modal";
import { Input, Textarea } from "../../shared/ui/Input";
import { LeafletMap } from "../../shared/map/MapView";

export function VisitsPage() {
  const [plans, setPlans] = useState([]);
  const [records, setRecords] = useState([]);
  const [showCreatePlan, setShowCreatePlan] = useState(false);
  const [showCreateRecord, setShowCreateRecord] = useState(false);
  const [customerSearch, setCustomerSearch] = useState("");
  const [customers, setCustomers] = useState([]);
  const [planForm, setPlanForm] = useState({ customer_id: "", planned_date: "", location: "", purpose: "", notes: "" });
  const [recordForm, setRecordForm] = useState({ customer_id: "", visit_date: "", raw_notes: "" });
  const [audioFile, setAudioFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [tab, setTab] = useState("plans");

  const fetchPlans = async () => {
    try {
      const data = await visitAPI.listPlans({ page: 1, page_size: 50 });
      setPlans(data.items || []);
    } catch {}
  };

  const fetchRecords = async () => {
    try {
      const data = await visitAPI.listRecords({ page: 1, page_size: 50 });
      setRecords(data.items || []);
    } catch {}
  };

  const searchCustomers = async (q) => {
    if (q.length < 1) { setCustomers([]); return; }
    try {
      const data = await customerAPI.list({ page: 1, page_size: 10 });
      setCustomers((data.items || []).filter((c) =>
        c.name.includes(q) || c.company.includes(q)
      ));
    } catch {}
  };

  useEffect(() => { fetchPlans(); fetchRecords(); }, []);

  const createPlan = async () => {
    await visitAPI.createPlan({ ...planForm, latitude: null, longitude: null, status: "planned" });
    setShowCreatePlan(false);
    fetchPlans();
  };

  const createRecord = async () => {
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append("customer_id", recordForm.customer_id);
      fd.append("visit_date", recordForm.visit_date + ":00");
      fd.append("raw_notes", recordForm.raw_notes);
      if (audioFile) fd.append("audio", audioFile);
      await fetch("/api/visits/records", { method: "POST", body: fd });
      setShowCreateRecord(false);
      setAudioFile(null);
      fetchRecords();
    } finally {
      setUploading(false);
    }
  };

  const planMarkers = plans
    .filter((p) => p.latitude && p.longitude)
    .map((p) => ({ lat: p.latitude, lng: p.longitude, label: `${p.location} - ${p.purpose}` }));

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">拜访管理</h2>
        <div className="flex gap-2">
          <Button variant={tab === "plans" ? "primary" : "secondary"} onClick={() => setTab("plans")}>计划</Button>
          <Button variant={tab === "records" ? "primary" : "secondary"} onClick={() => setTab("records")}>记录</Button>
        </div>
      </div>

      {tab === "plans" && (
        <>
          <div className="flex justify-end mb-4">
            <Button onClick={() => setShowCreatePlan(true)}>+ 新建计划</Button>
          </div>
          {planMarkers.length > 0 && <LeafletMap markers={planMarkers} className="h-64 mb-6" />}
          <div className="space-y-3">
            {plans.length === 0 && <p className="text-gray-400">暂无拜访计划</p>}
            {plans.map((p) => (
              <Card key={p.id}>
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{p.location || "未指定地点"}</p>
                    <p className="text-sm text-gray-500">
                      {new Date(p.planned_date).toLocaleString("zh-CN")} · {p.purpose}
                    </p>
                    {p.notes && <p className="text-sm text-gray-400 mt-1">{p.notes}</p>}
                  </div>
                  <span className={`text-xs px-2 py-1 rounded-full ${p.status === "completed" ? "bg-green-100 text-green-700" : p.status === "cancelled" ? "bg-red-100 text-red-700" : "bg-blue-100 text-blue-700"}`}>
                    {p.status === "completed" ? "已完成" : p.status === "cancelled" ? "已取消" : "计划中"}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        </>
      )}

      {tab === "records" && (
        <>
          <div className="flex justify-end mb-4">
            <Button onClick={() => setShowCreateRecord(true)}>+ 新增记录</Button>
          </div>
          <div className="space-y-3">
            {records.length === 0 && <p className="text-gray-400">暂无拜访记录</p>}
            {records.map((r) => (
              <Card key={r.id}>
                <p className="font-semibold">{new Date(r.visit_date).toLocaleString("zh-CN")} 拜访</p>
                {r.summary && <p className="text-sm text-gray-600 mt-1">{r.summary.slice(0, 150)}{r.summary.length > 150 ? "..." : ""}</p>}
                {r.audio_path && <p className="text-xs text-gray-400 mt-1">含录音</p>}
                {r.transcript && <p className="text-xs text-gray-400 mt-1">已转写</p>}
              </Card>
            ))}
          </div>
        </>
      )}

      <Modal open={showCreatePlan} onClose={() => setShowCreatePlan(false)} title="新建拜访计划">
        <div className="space-y-4">
          <Input label="客户ID" value={planForm.customer_id} onChange={(e) => setPlanForm({ ...planForm, customer_id: e.target.value })} />
          <Input label="计划时间" type="datetime-local" value={planForm.planned_date} onChange={(e) => setPlanForm({ ...planForm, planned_date: e.target.value })} />
          <Input label="地点" value={planForm.location} onChange={(e) => setPlanForm({ ...planForm, location: e.target.value })} />
          <Input label="目的" value={planForm.purpose} onChange={(e) => setPlanForm({ ...planForm, purpose: e.target.value })} />
          <Textarea label="备注" value={planForm.notes} onChange={(e) => setPlanForm({ ...planForm, notes: e.target.value })} />
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowCreatePlan(false)}>取消</Button>
            <Button onClick={createPlan} disabled={!planForm.customer_id || !planForm.planned_date}>创建</Button>
          </div>
        </div>
      </Modal>

      <Modal open={showCreateRecord} onClose={() => setShowCreateRecord(false)} title="新增拜访记录">
        <div className="space-y-4">
          <Input label="客户ID" value={recordForm.customer_id} onChange={(e) => setRecordForm({ ...recordForm, customer_id: e.target.value })} />
          <Input label="拜访时间" type="datetime-local" value={recordForm.visit_date} onChange={(e) => setRecordForm({ ...recordForm, visit_date: e.target.value })} />
          <Textarea label="备注" value={recordForm.raw_notes} onChange={(e) => setRecordForm({ ...recordForm, raw_notes: e.target.value })} />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">录音文件（可选）</label>
            <input type="file" accept="audio/*" onChange={(e) => setAudioFile(e.target.files[0])} />
          </div>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setShowCreateRecord(false)}>取消</Button>
            <Button onClick={createRecord} disabled={uploading || !recordForm.customer_id}>
              {uploading ? "上传中..." : "创建"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
