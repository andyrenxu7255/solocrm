import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "首页", end: true },
  { to: "/todos", label: "待办" },
  { to: "/customers", label: "客户" },
  { to: "/cases", label: "案例" },
  { to: "/visits", label: "拜访" },
  { to: "/search", label: "搜索" },
];

export function AppShell() {
  return (
    <div className="flex h-screen bg-gray-50">
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-5 py-4 border-b border-gray-100">
          <h1 className="text-lg font-bold text-primary-600">SoloCRM</h1>
          <p className="text-xs text-gray-400 mt-0.5">极简销售 CRM</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? "bg-primary-50 text-primary-700"
                    : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="px-5 py-3 border-t border-gray-100">
          <p className="text-xs text-gray-400">v0.1.0</p>
        </div>
      </aside>
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
