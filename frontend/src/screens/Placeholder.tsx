import { Card, CardContent } from '@/components/ui/Card';
import { Construction } from 'lucide-react';
import { WORKFLOW_STEPS, type StepId } from '@/types/workflow';

interface PlaceholderProps {
  stepId: StepId;
}

export default function Placeholder({ stepId }: PlaceholderProps) {
  const step = WORKFLOW_STEPS.find((s) => s.id === stepId);
  if (!step) return null;

  return (
    <div className="p-5 space-y-5">
      <div>
        <div className="text-[11px] font-semibold text-tata-600 uppercase tracking-wider">
          Step {step.index}
        </div>
        <h2 className="text-xl font-bold text-slate-800">{step.label}</h2>
      </div>
      <Card>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mb-3">
              <Construction className="w-6 h-6 text-slate-400" />
            </div>
            <h3 className="text-[15px] font-semibold text-slate-600 mb-1">
              {step.label}
            </h3>
            <p className="text-[12px] text-sval-muted max-w-md">
              This workflow step will be populated with analysis results from the AI engine once the
              preceding steps are completed. Begin with Item Definition to start the functional
              safety analysis.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
