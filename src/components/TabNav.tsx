'use client';

export interface Tab {
  id: string;
  label: string;
}

interface TabNavProps {
  tabs: Tab[];
  active: string;
  onChange: (id: string) => void;
}

/**
 * Pill-style tab strip used at the top of every Split-Layout right
 * panel. Mirrors the TRIBE v2 tab buttons: subtle outline pills, a
 * faint white-on-white-fill for the active tab.
 */
export function TabNav({ tabs, active, onChange }: TabNavProps) {
  return (
    <div role="tablist" className="flex flex-wrap items-center gap-3">
      {tabs.map((tab) => {
        const isActive = tab.id === active;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`rounded-full border px-5 py-2 text-sm transition-all duration-150 ${
              isActive
                ? 'border-white/40 bg-white/10 text-white'
                : 'border-white/15 bg-transparent text-white/60 hover:border-white/25 hover:text-white/80'
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
