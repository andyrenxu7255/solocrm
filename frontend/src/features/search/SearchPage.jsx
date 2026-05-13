import { useState } from "react";
import { searchAPI } from "../../services/api";
import { Card } from "../../shared/ui/Card";
import { Button } from "../../shared/ui/Button";
import { Input, Select, Textarea } from "../../shared/ui/Input";
import { Link } from "react-router-dom";

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

export function SearchPage() {
  const [query, setQuery] = useState("");
  const [industry, setIndustry] = useState("");
  const [city, setCity] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    setSearched(true);
    try {
      const data = await searchAPI.customers({
        query: query || undefined,
        industry: industry || undefined,
        city: city || undefined,
        limit: 30,
      });
      setResults(data || []);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-xl font-semibold mb-6">找客户</h2>

      <Card className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <Textarea
            placeholder="描述理想客户特征，或用成功案例描述让AI帮你匹配..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            rows={3}
            className="md:col-span-3"
          />
          <div className="space-y-2">
            <Select label="行业" options={INDUSTRIES} value={industry} onChange={(e) => setIndustry(e.target.value)} />
            <Input placeholder="城市" value={city} onChange={(e) => setCity(e.target.value)} />
            <Button onClick={handleSearch} disabled={loading} className="w-full">
              {loading ? "搜索中..." : "搜索"}
            </Button>
          </div>
        </div>
      </Card>

      {searched && (
        <div>
          <p className="text-sm text-gray-400 mb-3">
            {loading ? "搜索中..." : `找到 ${results.length} 个结果`}
          </p>
          <div className="space-y-3">
            {results.map((c) => (
              <Link key={c.id} to={`/customers/${c.id}`}>
                <Card className="hover:border-primary-300 transition-colors cursor-pointer">
                  <p className="font-semibold text-gray-900">{c.name}</p>
                  <p className="text-sm text-gray-500">
                    {c.company} · {c.industry} · {c.city} · {c.title}
                  </p>
                  {c.tags?.length > 0 && (
                    <div className="flex gap-1 mt-1">
                      {c.tags.map((t, i) => <span key={i} className="text-xs px-1.5 py-0.5 bg-gray-100 rounded text-gray-500">{t}</span>)}
                    </div>
                  )}
                </Card>
              </Link>
            ))}
            {!loading && results.length === 0 && (
              <p className="text-gray-400">未找到匹配客户，试试更换条件或先用"案例录入"补充案例库</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
