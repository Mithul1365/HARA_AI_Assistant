import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { WORKFLOW_STEPS, type StepId } from '@/types/workflow';
import {
  GitBranch,
  ShieldCheck,
  Target,
  ListChecks,
  Cpu,
  Grid3x3,
  ClipboardCheck,
  ScrollText,
  FileText,
  ArrowRight,
} from 'lucide-react';

interface HomeProps {
  onStepClick: (step: StepId) => void;
  documentsUploaded: number;
  haraScenarioCount: number;
  activeAsil: string;
}

export default function Home({
  onStepClick,
  documentsUploaded,
  haraScenarioCount,
  activeAsil,
}: HomeProps) {
  const steps = WORKFLOW_STEPS.filter((s) => s.id !== 'home');

  const iconMap: Record<string, typeof GitBranch> = {
    'item-definition': FileText,
    'hara-analysis': GitBranch,
    'asil-assessment': ShieldCheck,
    'safety-goals': Target,
    'functional-safety-requirements': ListChecks,
    'technical-safety-requirements': Cpu,
    'traceability-matrix': Grid3x3,
    'verification-evidence': ClipboardCheck,
    'review-audit': ScrollText,
  };

  return (
    <div className="p-5 space-y-5">
      {/* Welcome header */}
      <div className="bg-tata-darker rounded-lg px-5 py-5">
        <h2 className="text-white text-lg font-bold">HARA AI Assistant</h2>
        <p className="text-tata-300 text-[13px] mt-0.5">
          AI-powered Automotive Functional Safety Analysis — ISO 26262 Compliance Workflow
        </p>
      </div>

      {/* Overview cards */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Workflow Steps" value="9" />
        <StatCard
               label="Documents Uploaded"
               value={String(documentsUploaded)}
          />

        <StatCard
              label="HARA Scenarios"
              value={String(haraScenarioCount)}
            />

         <StatCard
              label="Active ASIL"
              value={activeAsil}
             />
      </div>

      {/* Workflow grid */}
      <Card>
        <CardHeader>
          <CardTitle>Functional Safety Workflow</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-3">
            {steps.map((step) => {
              const Icon = iconMap[step.id] || FileText;
              return (
                <button
                  key={step.id}
                  onClick={() => onStepClick(step.id)}
                  className="flex items-start gap-3 p-3.5 border border-slate-200 rounded hover:border-tata-400 hover:bg-tata-50/50 transition-colors text-left group"
                >
                  <div className="w-9 h-9 rounded bg-tata-50 flex items-center justify-center shrink-0">
                    <Icon className="w-4.5 h-4.5 text-tata-600" />
                  </div>
                  <div className="min-w-0">
                    <div className="text-[10px] font-semibold text-sval-muted uppercase tracking-wider">
                      Step {step.index}
                    </div>
                    <div className="text-[13px] font-semibold text-slate-700 group-hover:text-tata-700">
                      {step.label}
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-slate-300 group-hover:text-tata-500 ml-auto shrink-0 mt-1" />
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <div className="px-3.5 py-3">
        <div className="text-[10px] font-semibold uppercase tracking-wider text-sval-muted mb-1">
          {label}
        </div>
        <div className="text-xl font-bold text-slate-800">{value}</div>
      </div>
    </Card>
  );
}
