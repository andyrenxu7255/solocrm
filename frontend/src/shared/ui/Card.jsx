export function Card({ children, className = "", padding = true }) {
  return (
    <div
      className={`bg-white rounded-xl border border-gray-200 shadow-sm ${padding ? "p-6" : ""} ${className}`}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, className = "" }) {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  );
}

export function CardTitle({ children, className = "" }) {
  return (
    <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>
      {children}
    </h3>
  );
}
