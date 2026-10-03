import {
  Home,
  FileText,
  GitBranch,
  ShieldCheck,
  Target,
  ListChecks,
  Cpu,
  Grid3x3,
  ClipboardCheck,
  ScrollText,
  type LucideIcon,
} from 'lucide-react';

export type StepId =
  | 'home'
  | 'item-definition'
  | 'hara-analysis'
  | 'asil-assessment'
  | 'safety-goals'
  | 'functional-safety-requirements'
  | 'technical-safety-requirements'
  | 'traceability-matrix'
  | 'verification-evidence'
  | 'review-audit';

export interface WorkflowStep {
  id: StepId;
  label: string;
  index: number; // 0 = Home (no number shown), 1..9 numbered
  icon: LucideIcon;
}

export const WORKFLOW_STEPS: WorkflowStep[] = [
  { id: 'home', label: 'Home', index: 0, icon: Home },
  { id: 'item-definition', label: 'Item Definition', index: 1, icon: FileText },
  { id: 'hara-analysis', label: 'HARA Analysis', index: 2, icon: GitBranch },
  { id: 'asil-assessment', label: 'ASIL Assessment', index: 3, icon: ShieldCheck },
  { id: 'safety-goals', label: 'Safety Goals', index: 4, icon: Target },
  { id: 'functional-safety-requirements', label: 'Functional Safety Requirements', index: 5, icon: ListChecks },
  { id: 'technical-safety-requirements', label: 'Technical Safety Requirements', index: 6, icon: Cpu },
  { id: 'traceability-matrix', label: 'Traceability Matrix', index: 7, icon: Grid3x3 },
  { id: 'verification-evidence', label: 'Verification Evidence', index: 8, icon: ClipboardCheck },
  { id: 'review-audit', label: 'Review & Audit', index: 9, icon: ScrollText },
];
