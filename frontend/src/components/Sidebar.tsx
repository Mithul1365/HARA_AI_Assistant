import { WORKFLOW_STEPS, type StepId } from '@/types/workflow';

interface SidebarProps {
  activeStep: StepId;
  completedSteps: Set<StepId>;
  onStepClick: (step: StepId) => void;
}

export default function Sidebar({
  activeStep,
  completedSteps,
  onStepClick,
}: SidebarProps) {
  return (
    <aside className="w-60 bg-white border-r border-sval-border flex flex-col shrink-0 z-20">
      {/* Workflow header */}
      <div className="px-4 py-3 border-b border-sval-border bg-sval-bg">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-sval-muted">
          Workflow
        </div>
      </div>

      {/* Steps */}
      <nav className="flex-1 overflow-y-auto py-2">
        {WORKFLOW_STEPS.map((step) => {
          const isActive = step.id === activeStep;
          const isCompleted = completedSteps.has(step.id);
          const Icon = step.icon;

          return (
            <button
              key={step.id}
              onClick={() => onStepClick(step.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-left text-[13px] font-medium border-l-[3px] transition-colors duration-100 ${
                isActive
                  ? 'bg-tata-50 text-tata-700 border-tata-600'
                  : 'text-slate-600 border-transparent hover:bg-slate-50 hover:text-slate-800'
              }`}
            >
              <Icon
                className={`w-4 h-4 shrink-0 ${
                  isActive ? 'text-tata-600' : 'text-slate-400'
                }`}
              />

              <span className="truncate">{step.label}</span>

              {/* Completed tick */}
              {isCompleted && (
                <span className="ml-auto text-emerald-600 font-bold text-sm">
                  ✓
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer status */}
      <div className="px-4 py-3 border-t border-sval-border bg-sval-bg">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-500" />
          <span className="text-[10px] text-sval-muted font-medium">
            AI Engine Connected
          </span>
        </div>
      </div>
    </aside>
  );
}