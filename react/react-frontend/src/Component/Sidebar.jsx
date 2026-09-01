import { useState } from "react";
import {
  LayoutDashboard,
  LineChart,
  GitBranch,
  Search,
  Activity,
  Bell,
  Settings,
  LogOut,
  User,
} from "lucide-react";

export default function Sidebar({ selected, setSelected }) {
  const [collapsed, setCollapsed] = useState(false);

  const menu = [
    { name: "Dashboard", icon: LayoutDashboard },
    { name: "Chart", icon: LineChart },
    { name: "Strategy", icon: GitBranch },
    { name: "Open Interest", icon: Activity }, // 👈 NEW PAGE
    { name: "Open table", icon: Activity }, // 👈 NEW PAGE
    { name: "Search", icon: Search },
    { name: "Signals", icon: Activity },
    { name: "Advanced Advisor", icon: Activity }, // 👈 NEW PAGE
    { name: "Alerts", icon: Bell },
  ];

  return (
    <div
      className={`bg-slate-950 text-white border-r border-slate-800 h-screen flex flex-col transition-all duration-300 ${
        collapsed ? "w-20" : "w-64"
      }`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        {!collapsed && (
          <div className="text-lg font-bold tracking-wide text-blue-400">
            TradeDesk
          </div>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className="text-slate-300 hover:text-white"
        >
          {collapsed ? "→" : "←"}
        </button>
      </div>

      {/* Menu */}
      <div className="flex-1 p-2">
        {menu.map((item) => {
          const Icon = item.icon;
          const active = selected === item.name;

          return (
            <div
              key={item.name}
              onClick={() => setSelected(item.name)}
              className={`relative flex items-center gap-3 px-3 py-3 my-1 rounded-lg cursor-pointer transition-all group
                ${
                  active
                    ? "bg-slate-800 text-white"
                    : "text-slate-400 hover:bg-slate-900 hover:text-white"
                }`}
            >
              {/* Active Indicator */}
              {active && (
                <span className="absolute left-0 top-0 h-full w-1 bg-blue-500 rounded-r" />
              )}

              <Icon size={20} />

              {!collapsed && (
                <span className="text-sm font-medium">
                  {item.name}
                </span>
              )}

              {/* Tooltip on collapse */}
              {collapsed && (
                <span className="absolute left-14 bg-black text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition whitespace-nowrap">
                  {item.name}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Section */}
      <div className="border-t border-slate-800 p-3">
        {/* Settings */}
        <div className="flex items-center gap-3 p-2 text-slate-400 hover:text-white cursor-pointer">
          <Settings size={18} />
          {!collapsed && <span className="text-sm">Settings</span>}
        </div>

        {/* Profile */}
        <div className="flex items-center gap-3 p-2 mt-2">
          <User size={18} />
          {!collapsed && (
            <div className="text-xs text-slate-400">
              <div className="text-white">User</div>
              <div>Pro Trader</div>
            </div>
          )}
        </div>

        {/* Logout */}
        <div className="flex items-center gap-3 p-2 mt-2 text-red-400 hover:text-red-300 cursor-pointer">
          <LogOut size={18} />
          {!collapsed && <span className="text-sm">Logout</span>}
        </div>
      </div>
    </div>
  );
}
