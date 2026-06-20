import React, { useState, useEffect, useRef } from "react";
import {
  AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import {
  LayoutGrid, Package, ShoppingCart, Truck, BarChart3, TrendingUp,
  Settings, Search, Bell, Moon, Sun, ChevronDown, ArrowUpRight, ArrowDownRight,
  Sparkles, X, Send, ChevronRight,
  MoreHorizontal, ArrowRight,
} from "lucide-react";

/* ----------------------------------------------------------------------- */
/* DESIGN TOKENS — exact palette from brief                                */
/* ----------------------------------------------------------------------- */

const C = {
  bg: "#0F1117",
  sidebar: "#171923",
  card: "#1E2230",
  primary: "#7C3AED",
  accent: "#A855F7",
  success: "#22C55E",
  warning: "#F59E0B",
  danger: "#EF4444",
  text: "#F8FAFC",
  textSecondary: "#94A3B8",
  border: "rgba(255,255,255,0.08)",
};

/* ----------------------------------------------------------------------- */
/* SAMPLE DATA                                                              */
/* ----------------------------------------------------------------------- */

const salesTrend = [
  { day: "Mon", revenue: 82000, orders: 412 },
  { day: "Tue", revenue: 91000, orders: 448 },
  { day: "Wed", revenue: 78000, orders: 390 },
  { day: "Thu", revenue: 104000, orders: 501 },
  { day: "Fri", revenue: 118000, orders: 562 },
  { day: "Sat", revenue: 142000, orders: 640 },
  { day: "Sun", revenue: 129000, orders: 598 },
];

const categoryData = [
  { name: "Dairy", value: 28, color: "#7C3AED" },
  { name: "Snacks", value: 22, color: "#A855F7" },
  { name: "Beverages", value: 18, color: "#C084FC" },
  { name: "Staples", value: 16, color: "#E9D5FF" },
  { name: "Household", value: 16, color: "#4C1D95" },
];

const topProducts = [
  { name: "Amul Milk 500ml", units: 4280 },
  { name: "Lay's Classic 52g", units: 3940 },
  { name: "Tata Salt 1kg", units: 3510 },
  { name: "Maggi Noodles", units: 3120 },
  { name: "Coca-Cola 750ml", units: 2870 },
];

const inventoryItems = [
  { name: "Amul Toned Milk 500ml", category: "Dairy", stock: 412, reorder: 100, supplier: "FreshFarm Distributors", status: "in-stock", price: 28 },
  { name: "Lay's Classic Salted 52g", category: "Snacks", stock: 38, reorder: 80, supplier: "SnackWorld Traders", status: "low-stock", price: 20 },
  { name: "Tata Salt 1kg", category: "Staples", stock: 0, reorder: 40, supplier: "Daily Needs Wholesale", status: "out-of-stock", price: 25 },
  { name: "Mother Dairy Curd 400g", category: "Dairy", stock: 286, reorder: 60, supplier: "FreshFarm Distributors", status: "in-stock", price: 45 },
  { name: "Maggi Noodles (4-pack)", category: "Snacks", stock: 52, reorder: 90, supplier: "SnackWorld Traders", status: "low-stock", price: 56 },
  { name: "Surf Excel 1kg", category: "Household", stock: 198, reorder: 40, supplier: "HomeEssentials Ltd.", status: "in-stock", price: 135 },
];

const transactions = [
  { product: "Amul Toned Milk 500ml", category: "Dairy", qty: 24, revenue: 672, status: "completed" },
  { product: "Lay's Classic Salted 52g", category: "Snacks", qty: 60, revenue: 1200, status: "completed" },
  { product: "Tata Salt 1kg", category: "Staples", qty: 12, revenue: 300, status: "pending" },
  { product: "Maggi Noodles (4-pack)", category: "Snacks", qty: 8, revenue: 448, status: "completed" },
  { product: "Coca-Cola 750ml", category: "Beverages", qty: 30, revenue: 1200, status: "failed" },
];

const heatmapCategories = ["Dairy", "Snacks", "Beverages", "Staples", "Household"];
const heatmapDays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const heatmapData = heatmapCategories.map(() =>
  heatmapDays.map(() => Math.floor(Math.random() * 80) + 15)
);

/* ----------------------------------------------------------------------- */
/* PRIMITIVES                                                              */
/* ----------------------------------------------------------------------- */

function StatusBadge({ status }) {
  const config = {
    "in-stock": { label: "In stock", color: C.success, bg: "rgba(34,197,94,0.12)" },
    "low-stock": { label: "Low stock", color: C.warning, bg: "rgba(245,158,11,0.12)" },
    "out-of-stock": { label: "Out of stock", color: C.danger, bg: "rgba(239,68,68,0.12)" },
    completed: { label: "Completed", color: C.success, bg: "rgba(34,197,94,0.12)" },
    pending: { label: "Pending", color: C.warning, bg: "rgba(245,158,11,0.12)" },
    failed: { label: "Failed", color: C.danger, bg: "rgba(239,68,68,0.12)" },
  }[status];

  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
      style={{ color: config.color, backgroundColor: config.bg }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: config.color }} />
      {config.label}
    </span>
  );
}

function AnimatedNumber({ value, prefix = "", suffix = "", decimals = 0 }) {
  const [display, setDisplay] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const duration = 900;
          const start = performance.now();
          const step = (now) => {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setDisplay(value * eased);
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) obs.observe(ref.current);
    return () => obs.disconnect();
  }, [value]);

  return (
    <span ref={ref}>
      {prefix}
      {display.toLocaleString("en-IN", { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}
      {suffix}
    </span>
  );
}

function KpiCard({ label, value, prefix, suffix, decimals, trend, trendUp, accentColor, big = false }) {
  const [hover, setHover] = useState(false);

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="relative overflow-hidden rounded-2xl transition-all duration-300 cursor-default"
      style={{
        backgroundColor: C.card,
        border: `1px solid ${C.border}`,
        padding: big ? "22px 22px 20px" : "18px 20px",
        boxShadow: hover ? "0 16px 32px -14px rgba(0,0,0,0.5)" : "0 2px 10px -4px rgba(0,0,0,0.25)",
        transform: hover ? "translateY(-2px)" : "translateY(0)",
      }}
    >
      <div
        className="absolute -right-6 -top-6 w-28 h-28 rounded-full transition-opacity duration-500 pointer-events-none"
        style={{
          opacity: hover ? 0.5 : 0.22,
          background: `radial-gradient(circle, ${accentColor}, transparent 70%)`,
          filter: "blur(18px)",
        }}
      />
      <p
        className="relative text-[13px] mb-2"
        style={{ color: C.textSecondary, letterSpacing: "0.01em" }}
      >
        {label}
      </p>
      <div className="relative flex items-end justify-between gap-3">
        <p
          className={big ? "text-[34px] font-semibold tracking-tight leading-none" : "text-[26px] font-semibold tracking-tight leading-none"}
          style={{ color: C.text }}
        >
          <AnimatedNumber value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
        </p>
        <span
          className="flex items-center gap-0.5 text-xs font-medium pb-1"
          style={{ color: trendUp ? C.success : C.danger }}
        >
          {trendUp ? <ArrowUpRight size={13} /> : <ArrowDownRight size={13} />}
          {trend}
        </span>
      </div>
    </div>
  );
}

function RevenueHeroCard() {
  const max = Math.max(...salesTrend.map((d) => d.revenue));
  const min = Math.min(...salesTrend.map((d) => d.revenue));
  const pts = salesTrend.map((d, i) => {
    const x = (i / (salesTrend.length - 1)) * 100;
    const y = 36 - ((d.revenue - min) / (max - min || 1)) * 32;
    return `${x},${y}`;
  });
  const path = "M" + pts.join(" L");
  const areaPath = `${path} L100,36 L0,36 Z`;

  return (
    <div
      className="relative overflow-hidden rounded-2xl flex flex-col justify-between"
      style={{
        background: `linear-gradient(155deg, #1E2230 0%, #221B36 100%)`,
        border: `1px solid rgba(168,85,247,0.18)`,
        padding: "22px 24px 18px",
      }}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[13px] mb-2" style={{ color: C.textSecondary }}>Revenue this week</p>
          <p className="text-[34px] font-semibold tracking-tight leading-none" style={{ color: C.text }}>
            <AnimatedNumber value={1.24} prefix="₹" suffix="M" decimals={2} />
          </p>
        </div>
        <span
          className="flex items-center gap-0.5 text-xs font-medium mt-1"
          style={{ color: C.success }}
        >
          <ArrowUpRight size={13} />
          11.3% vs last week
        </span>
      </div>

      <svg viewBox="0 0 100 36" preserveAspectRatio="none" className="w-full h-12 mt-3" style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id="heroFade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.accent} stopOpacity="0.35" />
            <stop offset="100%" stopColor={C.accent} stopOpacity="0" />
          </linearGradient>
        </defs>
        <path d={areaPath} fill="url(#heroFade)" stroke="none" />
        <path d={path} fill="none" stroke={C.accent} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
      </svg>
      <div className="flex justify-between text-[11px] mt-1" style={{ color: C.textSecondary }}>
        {salesTrend.map((d) => <span key={d.day}>{d.day}</span>)}
      </div>
    </div>
  );
}

function NavItem({ icon: Icon, label, active, onClick }) {
  const [hover, setHover] = useState(false);
  return (
    <button
      onClick={onClick}
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative"
      style={{
        backgroundColor: active ? "rgba(124,58,237,0.14)" : hover ? "rgba(255,255,255,0.04)" : "transparent",
        color: active ? C.accent : hover ? C.text : C.textSecondary,
      }}
    >
      {active && (
        <span
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 rounded-full"
          style={{ backgroundColor: C.accent }}
        />
      )}
      <Icon size={18} strokeWidth={2} />
      <span>{label}</span>
    </button>
  );
}

function SectionHeader({ title, subtitle, action }) {
  return (
    <div className="flex items-center justify-between mb-5">
      <div>
        <h3 className="text-base font-semibold" style={{ color: C.text }}>{title}</h3>
        {subtitle && <p className="text-sm mt-0.5" style={{ color: C.textSecondary }}>{subtitle}</p>}
      </div>
      {action}
    </div>
  );
}

function Card({ children, className = "", padding = "p-6" }) {
  return (
    <div
      className={`rounded-2xl ${padding} ${className}`}
      style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}
    >
      {children}
    </div>
  );
}

/* ----------------------------------------------------------------------- */
/* CHARTS                                                                  */
/* ----------------------------------------------------------------------- */

function CustomTooltip({ active, payload, label, currency }) {
  if (!active || !payload?.length) return null;
  return (
    <div
      className="rounded-xl px-3 py-2 text-xs"
      style={{ backgroundColor: "#252A3B", border: `1px solid ${C.border}`, boxShadow: "0 8px 24px rgba(0,0,0,0.4)" }}
    >
      <p style={{ color: C.textSecondary }} className="mb-1">{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: C.text }} className="font-medium">
          {currency ? `₹${p.value.toLocaleString("en-IN")}` : p.value.toLocaleString("en-IN")}
        </p>
      ))}
    </div>
  );
}

function SalesTrendChart() {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={salesTrend} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={C.primary} stopOpacity={0.35} />
            <stop offset="100%" stopColor={C.primary} stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
        <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{ fill: C.textSecondary, fontSize: 12 }} />
        <YAxis axisLine={false} tickLine={false} tick={{ fill: C.textSecondary, fontSize: 12 }}
               tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
        <Tooltip content={<CustomTooltip currency />} />
        <Area type="monotone" dataKey="revenue" stroke={C.accent} strokeWidth={2.5}
              fill="url(#revGrad)" dot={{ r: 0 }} activeDot={{ r: 5, fill: C.accent, stroke: C.bg, strokeWidth: 2 }} />
      </AreaChart>
    </ResponsiveContainer>
  );
}

function CategoryDonut() {
  const [activeIdx, setActiveIdx] = useState(null);
  return (
    <div className="flex items-center gap-6">
      <ResponsiveContainer width="55%" height={220}>
        <PieChart>
          <Pie
            data={categoryData}
            dataKey="value"
            nameKey="name"
            innerRadius={62}
            outerRadius={88}
            paddingAngle={3}
            stroke="none"
            onMouseEnter={(_, i) => setActiveIdx(i)}
            onMouseLeave={() => setActiveIdx(null)}
          >
            {categoryData.map((entry, i) => (
              <Cell
                key={i}
                fill={entry.color}
                style={{
                  filter: activeIdx === i ? "brightness(1.25)" : "brightness(1)",
                  transition: "filter 0.2s",
                  cursor: "pointer",
                }}
              />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="flex-1 space-y-2.5">
        {categoryData.map((c, i) => (
          <div key={i} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: c.color }} />
              <span style={{ color: activeIdx === i ? C.text : C.textSecondary }}>{c.name}</span>
            </div>
            <span className="font-medium" style={{ color: C.text }}>{c.value}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopProductsChart() {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={topProducts} layout="vertical" margin={{ top: 0, right: 20, left: 0, bottom: 0 }}>
        <XAxis type="number" hide />
        <YAxis
          type="category"
          dataKey="name"
          axisLine={false}
          tickLine={false}
          width={140}
          tick={{ fill: C.textSecondary, fontSize: 12 }}
        />
        <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
        <Bar dataKey="units" radius={[0, 8, 8, 0]} barSize={16}>
          {topProducts.map((_, i) => (
            <Cell key={i} fill={i === 0 ? C.accent : C.primary} fillOpacity={1 - i * 0.13} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

function InventoryHeatmap() {
  const max = Math.max(...heatmapData.flat());
  return (
    <div>
      <div className="grid mb-2" style={{ gridTemplateColumns: "90px repeat(7, 1fr)", gap: "6px" }}>
        <div />
        {heatmapDays.map((d) => (
          <div key={d} className="text-center text-xs" style={{ color: C.textSecondary }}>{d}</div>
        ))}
      </div>
      {heatmapCategories.map((cat, ri) => (
        <div key={cat} className="grid mb-1.5" style={{ gridTemplateColumns: "90px repeat(7, 1fr)", gap: "6px" }}>
          <div className="text-xs flex items-center" style={{ color: C.textSecondary }}>{cat}</div>
          {heatmapDays.map((_, ci) => {
            const val = heatmapData[ri][ci];
            const intensity = val / max;
            return (
              <div
                key={ci}
                title={`${cat} · ${heatmapDays[ci]}: ${val} units`}
                className="aspect-square rounded-lg transition-transform duration-150 hover:scale-110 cursor-pointer"
                style={{
                  backgroundColor: `rgba(124,58,237,${0.12 + intensity * 0.75})`,
                  border: `1px solid ${C.border}`,
                }}
              />
            );
          })}
        </div>
      ))}
      <div className="flex items-center gap-2 mt-4 justify-end">
        <span className="text-xs" style={{ color: C.textSecondary }}>Less</span>
        {[0.15, 0.35, 0.55, 0.75, 0.95].map((o, i) => (
          <span key={i} className="w-3 h-3 rounded" style={{ backgroundColor: `rgba(124,58,237,${o})` }} />
        ))}
        <span className="text-xs" style={{ color: C.textSecondary }}>More</span>
      </div>
    </div>
  );
}

/* ----------------------------------------------------------------------- */
/* AI ASSISTANT — docked panel, Linear-command-K inspired                  */
/* ----------------------------------------------------------------------- */

const assistantSuggestions = [
  "Which products are running low?",
  "What should I reorder?",
  "Which products sell fastest?",
];

const assistantAnswers = {
  "Which products are running low?":
    "3 products are below their reorder threshold: Lay's Classic Salted 52g (38 left), Maggi Noodles 4-pack (52 left), and Tata Salt 1kg (out of stock). Want me to draft a reorder list?",
  "What should I reorder?":
    "Based on a 7-day demand forecast, I'd prioritize Tata Salt 1kg (out of stock, ~280 units/week demand) and Lay's Classic Salted 52g (~310 units/week). Reordering both today covers roughly 3 weeks of runway.",
  "Which products sell fastest?":
    "Amul Toned Milk 500ml leads at 4,280 units this month, followed by Lay's Classic Salted 52g and Tata Salt 1kg. Dairy and Snacks are your two fastest-moving categories.",
};

function AIAssistant() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Hi, I'm your inventory copilot. Ask me anything about stock, reorders, or sales." },
  ]);
  const [input, setInput] = useState("");

  const send = (text) => {
    if (!text.trim()) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setTimeout(() => {
      const answer = assistantAnswers[text] || "I can help with stock levels, reorder suggestions, and sales velocity — try one of the questions below.";
      setMessages((m) => [...m, { role: "assistant", text: answer }]);
    }, 500);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end">
      {open && (
        <div
          className="mb-3 w-80 rounded-2xl overflow-hidden flex flex-col"
          style={{
            backgroundColor: "#181B27",
            border: `1px solid ${C.border}`,
            boxShadow: "0 24px 60px -12px rgba(0,0,0,0.6), 0 0 0 1px rgba(124,58,237,0.1)",
            maxHeight: "480px",
            animation: "aiSlideUp 0.25s ease-out",
          }}
        >
          <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
            <div className="flex items-center gap-2">
              <div
                className="w-7 h-7 rounded-full flex items-center justify-center"
                style={{ background: `linear-gradient(135deg, ${C.primary}, ${C.accent})` }}
              >
                <Sparkles size={14} color="white" />
              </div>
              <span className="text-sm font-medium" style={{ color: C.text }}>Inventory copilot</span>
            </div>
            <button onClick={() => setOpen(false)} className="opacity-60 hover:opacity-100 transition-opacity">
              <X size={16} style={{ color: C.textSecondary }} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ maxHeight: "280px" }}>
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  className="rounded-xl px-3 py-2 text-sm leading-relaxed max-w-[85%]"
                  style={{
                    backgroundColor: m.role === "user" ? C.primary : "#252A3B",
                    color: m.role === "user" ? "white" : C.text,
                  }}
                >
                  {m.text}
                </div>
              </div>
            ))}
          </div>

          <div className="px-4 pb-2 flex flex-wrap gap-1.5">
            {assistantSuggestions.map((q) => (
              <button
                key={q}
                onClick={() => send(q)}
                className="text-xs px-2.5 py-1.5 rounded-lg transition-colors"
                style={{ backgroundColor: "rgba(124,58,237,0.1)", color: C.accent, border: `1px solid rgba(124,58,237,0.2)` }}
              >
                {q}
              </button>
            ))}
          </div>

          <div className="px-3 pb-3 pt-1 flex items-center gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send(input)}
              placeholder="Ask about your inventory..."
              className="flex-1 bg-transparent text-sm px-3 py-2 rounded-xl outline-none"
              style={{ backgroundColor: "#0F1117", color: C.text, border: `1px solid ${C.border}` }}
            />
            <button
              onClick={() => send(input)}
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-transform hover:scale-105"
              style={{ backgroundColor: C.primary }}
            >
              <Send size={15} color="white" />
            </button>
          </div>
        </div>
      )}

      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 pl-4 pr-5 py-3 rounded-full transition-all duration-300 hover:scale-105"
        style={{
          background: `linear-gradient(135deg, ${C.primary}, ${C.accent})`,
          boxShadow: "0 12px 32px -8px rgba(124,58,237,0.5)",
        }}
      >
        <Sparkles size={16} color="white" />
        <span className="text-sm font-medium text-white">{open ? "Close" : "Ask copilot"}</span>
      </button>
    </div>
  );
}

/* ----------------------------------------------------------------------- */
/* PAGES                                                                   */
/* ----------------------------------------------------------------------- */

function DashboardPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="grid grid-cols-1 lg:grid-cols-[1.3fr_1fr] gap-4">
        <RevenueHeroCard />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <KpiCard label="Total products" value={12847} trend="4.2%" trendUp accentColor={C.primary} />
          <KpiCard label="Inventory value" value={8.2} prefix="₹" suffix="M" decimals={1} trend="2.8%" trendUp accentColor={C.accent} />
          <KpiCard label="Low stock items" value={24} trend="6 new" trendUp={false} accentColor={C.warning} />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Card className="lg:col-span-2">
          <SectionHeader
            title="Sales trend"
            subtitle="Revenue across the last 7 days"
            action={
              <button className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg"
                      style={{ color: C.textSecondary, border: `1px solid ${C.border}` }}>
                This week <ChevronDown size={13} />
              </button>
            }
          />
          <SalesTrendChart />
        </Card>

        <Card>
          <SectionHeader title="Category distribution" subtitle="Share of total stock" />
          <CategoryDonut />
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <Card className="lg:col-span-1">
          <SectionHeader title="Top selling products" subtitle="By units this month" />
          <TopProductsChart />
        </Card>

        <Card className="lg:col-span-2">
          <SectionHeader title="Inventory heatmap" subtitle="Sales density by category and day" />
          <InventoryHeatmap />
        </Card>
      </div>

      <Card padding="p-0">
        <div className="p-6 pb-0">
          <SectionHeader
            title="Recent transactions"
            subtitle="Latest sales activity"
            action={
              <button className="flex items-center gap-1 text-sm font-medium" style={{ color: C.accent }}>
                View all <ChevronRight size={14} />
              </button>
            }
          />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr style={{ borderTop: `1px solid ${C.border}`, borderBottom: `1px solid ${C.border}` }}>
                {["Product", "Category", "Quantity", "Revenue", "Status"].map((h) => (
                  <th key={h} className="text-left px-6 py-3 font-medium text-xs uppercase tracking-wide"
                      style={{ color: C.textSecondary }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {transactions.map((t, i) => (
                <tr key={i} className="transition-colors hover:bg-white/[0.02]"
                    style={{ borderBottom: i < transactions.length - 1 ? `1px solid ${C.border}` : "none" }}>
                  <td className="px-6 py-4 font-medium" style={{ color: C.text }}>{t.product}</td>
                  <td className="px-6 py-4" style={{ color: C.textSecondary }}>{t.category}</td>
                  <td className="px-6 py-4" style={{ color: C.textSecondary }}>{t.qty}</td>
                  <td className="px-6 py-4 font-medium" style={{ color: C.text }}>₹{t.revenue.toLocaleString("en-IN")}</td>
                  <td className="px-6 py-4"><StatusBadge status={t.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}

function InventoryPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold" style={{ color: C.text }}>Inventory</h2>
          <p className="text-sm mt-0.5" style={{ color: C.textSecondary }}>{inventoryItems.length} products across 5 categories</p>
        </div>
        <button
          className="px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-colors hover:bg-[#6D28D9]"
          style={{ backgroundColor: C.primary }}
        >
          + Add product
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {inventoryItems.map((item, i) => (
          <InventoryCard key={i} item={item} />
        ))}
      </div>
    </div>
  );
}

function InventoryCard({ item }) {
  const [hover, setHover] = useState(false);
  const stockPct = Math.min(100, (item.stock / (item.reorder * 2)) * 100);
  const barColor = item.status === "in-stock" ? C.success : item.status === "low-stock" ? C.warning : C.danger;

  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="relative transition-all duration-300"
      style={{
        backgroundColor: C.card,
        border: `1px solid ${hover ? "rgba(124,58,237,0.3)" : C.border}`,
        borderLeft: `3px solid ${barColor}`,
        borderTopLeftRadius: "4px",
        borderBottomLeftRadius: "4px",
        borderTopRightRadius: "16px",
        borderBottomRightRadius: "16px",
        transform: hover ? "translateY(-2px)" : "translateY(0)",
        boxShadow: hover ? "0 16px 32px -12px rgba(0,0,0,0.4)" : "none",
        padding: "18px 18px 16px 19px",
      }}
    >
      <div className="flex items-start justify-between mb-3 gap-3">
        <div className="min-w-0">
          <h4 className="font-medium text-sm mb-0.5 truncate" style={{ color: C.text }}>{item.name}</h4>
          <p className="text-xs" style={{ color: C.textSecondary }}>{item.category} · ₹{item.price}</p>
        </div>
        <button className="opacity-40 hover:opacity-100 transition-opacity flex-shrink-0 mt-0.5">
          <MoreHorizontal size={16} style={{ color: C.textSecondary }} />
        </button>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between text-xs mb-1.5">
          <span style={{ color: C.textSecondary }}>Stock level</span>
          <span className="font-medium" style={{ color: C.text }}>{item.stock} units</span>
        </div>
        <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "rgba(255,255,255,0.06)" }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${stockPct}%`, backgroundColor: barColor }}
          />
        </div>
      </div>

      <div className="flex items-center justify-between pt-3" style={{ borderTop: `1px solid ${C.border}` }}>
        <span className="text-xs" style={{ color: C.textSecondary }}>{item.supplier}</span>
        <StatusBadge status={item.status} />
      </div>
    </div>
  );
}

function AnalyticsPage() {
  return (
    <div className="space-y-6 animate-fadeIn">
      <div>
        <h2 className="text-lg font-semibold" style={{ color: C.text }}>Analytics</h2>
        <p className="text-sm mt-0.5" style={{ color: C.textSecondary }}>Revenue, sales, and performance insights</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <Card>
          <SectionHeader title="Revenue trends" subtitle="Last 7 days" />
          <SalesTrendChart />
        </Card>
        <Card>
          <SectionHeader title="Category comparison" subtitle="Revenue share by category" />
          <CategoryDonut />
        </Card>
      </div>

      <Card>
        <SectionHeader title="Product performance matrix" subtitle="Units sold vs. revenue contribution" />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {topProducts.map((p, i) => (
            <div key={i} className="rounded-xl p-4" style={{ backgroundColor: "#252A3B" }}>
              <p className="text-xs mb-2 truncate" style={{ color: C.textSecondary }}>{p.name}</p>
              <p className="text-xl font-semibold" style={{ color: C.text }}>{p.units.toLocaleString()}</p>
              <p className="text-xs mt-1" style={{ color: C.success }}>units sold</p>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

/* ----------------------------------------------------------------------- */
/* SHELL: sidebar + header                                                  */
/* ----------------------------------------------------------------------- */

const navItems = [
  { key: "dashboard", icon: LayoutGrid, label: "Dashboard" },
  { key: "inventory", icon: Package, label: "Inventory" },
  { key: "orders", icon: ShoppingCart, label: "Orders" },
  { key: "suppliers", icon: Truck, label: "Suppliers" },
  { key: "analytics", icon: BarChart3, label: "Analytics" },
  { key: "forecasting", icon: TrendingUp, label: "Forecasting" },
  { key: "settings", icon: Settings, label: "Settings" },
];

export default function InventoryDashboard() {
  const [activePage, setActivePage] = useState("dashboard");
  const [darkMode, setDarkMode] = useState(true);

  return (
    <div
      className="min-h-screen w-full flex transition-all duration-300"
      style={{
        backgroundColor: C.bg,
        fontFamily: "Inter, system-ui, sans-serif",
        filter: darkMode ? "none" : "brightness(1.15) contrast(0.95)",
      }}
    >
      <style>{`
        @keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes aiSlideUp { from { opacity: 0; transform: translateY(12px) scale(0.98); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .animate-fadeIn { animation: fadeIn 0.4s ease-out; }
        * { scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.1) transparent; }
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 8px; }
      `}</style>

      {/* SIDEBAR */}
      <aside
        className="w-64 flex-shrink-0 flex flex-col px-4 py-5 sticky top-0 h-screen"
        style={{ backgroundColor: C.sidebar, borderRight: `1px solid ${C.border}` }}
      >
        <div className="flex items-center gap-2.5 px-2 mb-8">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: C.primary }}
          >
            <Package size={16} color="white" />
          </div>
          <span className="font-semibold text-[15px]" style={{ color: C.text }}>InventoryOS</span>
        </div>

        <nav className="flex-1 space-y-1">
          {navItems.map((item) => (
            <NavItem
              key={item.key}
              icon={item.icon}
              label={item.label}
              active={activePage === item.key}
              onClick={() => setActivePage(item.key)}
            />
          ))}
        </nav>

        <div
          className="flex items-center gap-3 px-2 py-3 rounded-xl mt-2"
          style={{ backgroundColor: "rgba(255,255,255,0.03)" }}
        >
          <div className="relative">
            <div
              className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold text-white"
              style={{ background: `linear-gradient(135deg, ${C.primary}, ${C.accent})` }}
            >
              A
            </div>
            <span
              className="absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: C.success, border: `2px solid ${C.sidebar}` }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate" style={{ color: C.text }}>Ayush Sharma</p>
            <p className="text-xs truncate" style={{ color: C.textSecondary }}>Store admin</p>
          </div>
        </div>
      </aside>

      {/* MAIN */}
      <div className="flex-1 min-w-0 flex flex-col">
        {/* HEADER */}
        <header
          className="flex items-center justify-between px-8 py-4 sticky top-0 z-30 backdrop-blur-md"
          style={{ backgroundColor: "rgba(15,17,23,0.85)", borderBottom: `1px solid ${C.border}` }}
        >
          <div className="relative w-full max-w-md">
            <Search size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2" style={{ color: C.textSecondary }} />
            <input
              placeholder="Search products, orders, suppliers..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm outline-none transition-colors"
              style={{ backgroundColor: C.card, border: `1px solid ${C.border}`, color: C.text }}
            />
          </div>

          <div className="flex items-center gap-3 ml-6">
            <button
              className="relative w-9 h-9 rounded-xl flex items-center justify-center transition-colors hover:bg-white/[0.04]"
              style={{ border: `1px solid ${C.border}` }}
            >
              <Bell size={16} style={{ color: C.textSecondary }} />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full" style={{ backgroundColor: C.danger }} />
            </button>
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="w-9 h-9 rounded-xl flex items-center justify-center transition-colors hover:bg-white/[0.04]"
              style={{ border: `1px solid ${C.border}` }}
            >
              {darkMode ? <Moon size={16} style={{ color: C.textSecondary }} /> : <Sun size={16} style={{ color: C.textSecondary }} />}
            </button>
            <button className="flex items-center gap-2 pl-1 pr-2 py-1 rounded-xl transition-colors hover:bg-white/[0.04]">
              <div
                className="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold text-white"
                style={{ backgroundColor: C.primary }}
              >
                A
              </div>
              <ChevronDown size={14} style={{ color: C.textSecondary }} />
            </button>
          </div>
        </header>

        {/* CONTENT */}
        <main className="flex-1 px-8 py-7 overflow-y-auto">
          {activePage === "dashboard" && (
            <>
              <div className="mb-7">
                <h1 className="text-2xl font-semibold tracking-tight" style={{ color: C.text }}>
                  Good evening, Ayush <span style={{ filter: "saturate(1.2)" }}>👋</span>
                </h1>
                <p className="text-sm mt-1.5" style={{ color: C.textSecondary }}>
                  Manage your inventory efficiently.
                </p>
              </div>
              <DashboardPage />
            </>
          )}
          {activePage === "inventory" && <InventoryPage />}
          {activePage === "analytics" && <AnalyticsPage />}
          {!["dashboard", "inventory", "analytics"].includes(activePage) && (
            <div className="flex flex-col items-center justify-center h-[60vh] text-center">
              <div
                className="w-12 h-12 rounded-2xl flex items-center justify-center mb-4"
                style={{ backgroundColor: C.card, border: `1px solid ${C.border}` }}
              >
                {React.createElement(navItems.find((n) => n.key === activePage)?.icon || ArrowRight, {
                  size: 18,
                  style: { color: C.textSecondary },
                })}
              </div>
              <p className="font-medium" style={{ color: C.text }}>
                {navItems.find((n) => n.key === activePage)?.label} isn't wired up yet
              </p>
              <p className="text-sm mt-1 max-w-xs" style={{ color: C.textSecondary }}>
                Ask for it by name and it'll get the same treatment as Dashboard and Inventory.
              </p>
            </div>
          )}
        </main>
      </div>

      <AIAssistant />
    </div>
  );
}
