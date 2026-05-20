import { Routes, Route } from "react-router-dom";
import { AppShell } from "./shared/layout/AppShell";
import { CaseList } from "./features/case/CaseList";
import { CustomerList } from "./features/customer/CustomerList";
import { CustomerDetail } from "./features/customer/CustomerDetail";
import { SearchPage } from "./features/search/SearchPage";
import { VisitsPage as VisitsPageContent } from "./features/visit/VisitsPage";
import { TodoList } from "./features/todo/TodoList";
import { BusinessPage } from "./features/business/BusinessPage";

function HomePage() {
  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold text-gray-900">欢迎回来</h2>
      <p className="mt-1 text-gray-500">今天有哪些客户需要跟进？</p>
      <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard label="待跟进客户" value="0" color="blue" />
        <StatCard label="本月拜访" value="0" color="orange" />
        <StatCard label="待办事项" value="0" color="green" />
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  const colors = { blue: "bg-blue-50 text-blue-700", orange: "bg-orange-50 text-orange-700", green: "bg-green-50 text-green-700" };
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
      <p className="text-sm text-gray-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${colors[color] || ""}`}>{value}</p>
    </div>
  );
}

function CasesPage() { return <CaseList />; }
function CustomersPage() { return <CustomerList />; }
function CustomerDetailPage() { return <CustomerDetail />; }
function VisitsRoute() { return <VisitsPageContent />; }
function TodosPage() { return <TodoList />; }
function BusinessRoute() { return <BusinessPage />; }

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<HomePage />} />
        <Route path="cases" element={<CasesPage />} />
        <Route path="customers" element={<CustomersPage />} />
        <Route path="customers/:id" element={<CustomerDetailPage />} />
        <Route path="visits" element={<VisitsRoute />} />
        <Route path="todos" element={<TodosPage />} />
        <Route path="search" element={<SearchPage />} />
        <Route path="business" element={<BusinessRoute />} />
      </Route>
    </Routes>
  );
}
