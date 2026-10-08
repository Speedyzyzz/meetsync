import { LucideIcon } from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  subtext?: string;
  icon: LucideIcon;
  badge?: string;
  badgeColor?: string;
}

export function StatCard({
  title,
  value,
  subtext,
  icon: Icon,
  badge,
  badgeColor = "text-sky-400 bg-sky-500/10 border-sky-500/20",
}: StatCardProps) {
  return (
    <div className="glass-card p-5 rounded-2xl relative overflow-hidden group">
      <div className="absolute top-0 right-0 -mr-6 -mt-6 w-24 h-24 bg-sky-500/5 rounded-full blur-2xl group-hover:bg-sky-500/10 transition-colors" />
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </p>
          <p className="mt-2 text-3xl font-bold tracking-tight text-white">
            {value}
          </p>
          {subtext && (
            <p className="mt-1 text-xs text-slate-400">{subtext}</p>
          )}
        </div>
        <div className="p-2.5 rounded-xl bg-slate-800/80 border border-slate-700/60 text-sky-400">
          <Icon className="w-5 h-5" />
        </div>
      </div>
      {badge && (
        <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center">
          <span
            className={`text-[11px] font-medium px-2 py-0.5 rounded-full border ${badgeColor}`}
          >
            {badge}
          </span>
        </div>
      )}
    </div>
  );
}
