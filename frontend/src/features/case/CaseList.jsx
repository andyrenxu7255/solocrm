import { useState } from "react";
import { caseAPI } from "../../services/api";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Textarea } from "../../shared/ui/Input";

export function CaseList() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversation, setConversation] = useState("");
  const [extracting, setExtracting] = useState(false);
  const [result, setResult] = useState(null);

  const fetchList = async () => {
    setLoading(true);
    try {
      const data = await caseAPI.list({ page: 1, page_size: 50 });
      setCases(data.items || []);
    } finally {
      setLoading(false);
    }
  };

  const handleExtract = async () => {
    setExtracting(true);
    setResult(null);
    try {
      const data = await caseAPI.extract({ content: conversation });
      setResult(data);
      setConversation("");
      await fetchList();
    } catch (e) {
      setResult({ error: e.message });
    } finally {
      setExtracting(false);
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-xl font-semibold mb-6">成功案例</h2>

      <Card className="mb-6">
        <h3 className="font-medium text-gray-700 mb-3">AI 对话录入案例</h3>
        <Textarea
          placeholder="描述你最近做成功的一个项目，比如：我上个月帮杭州电力做了个数据中台项目，合同大概200万..."
          value={conversation}
          onChange={(e) => setConversation(e.target.value)}
          rows={4}
        />
        <div className="mt-3 flex items-center gap-3">
          <Button onClick={handleExtract} disabled={extracting || conversation.trim().length < 10}>
            {extracting ? "AI 分析中..." : "提取并保存"}
          </Button>
          {!loading && (
            <Button variant="ghost" onClick={fetchList}>
              刷新列表
            </Button>
          )}
        </div>
        {result && !result.error && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-800">
            案例已录入：{result.title} ({result.company_name})
          </div>
        )}
        {result?.error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
            提取失败：{result.error}
          </div>
        )}
      </Card>

      <div className="space-y-3">
        {loading && <p className="text-gray-400">加载中...</p>}
        {!loading && cases.length === 0 && <p className="text-gray-400">暂无案例数据，用上方 AI 对话录入第一个</p>}
        {cases.map((c) => (
          <Card key={c.id}>
            <div className="flex items-start justify-between">
              <div>
                <p className="font-semibold text-gray-900">{c.title}</p>
                <p className="text-sm text-gray-500">
                  {c.company_name} · {c.industry} · {c.city} · 方案: {c.product}
                </p>
                {c.summary && <p className="text-sm text-gray-600 mt-1 line-clamp-2">{c.summary}</p>}
                {c.key_points?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {c.key_points.map((kp, i) => (
                      <span key={i} className="text-xs px-2 py-0.5 bg-blue-50 text-blue-700 rounded-full">
                        {kp.key}: {kp.value}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {c.deal_size != null && (
                <span className="text-sm font-medium text-green-700 whitespace-nowrap">¥{c.deal_size.toLocaleString()}</span>
              )}
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
