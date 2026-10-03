import { useState } from 'react';
import AiRequirementRecommendation from "../components/AiRequirementRecommendation";
import type {
  ItemContext,
  HaraScenario,
  AsilResult,
  SafetyGoalResult,
  FSRResult,
} from '@/App';

interface TSRResult {
  id: string;
  requirement: string;
  rationale: string;
  candidate_asil: string;
  review_status: string;
  system: string;
  function: string;
  malfunction: string;
  hazard: string;
  hazardous_event: string;
  safety_goal: string;
  fsr: string;
}

interface TechnicalSafetyRequirementsProps {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  asilResult: AsilResult | null;
  safetyGoal: SafetyGoalResult | null;
  fsrResults: FSRResult[];
  initialResults: TSRResult[];
  onPrevious: () => void;
  onGenerated: (results: TSRResult[]) => void;
  onContinue: () => void;
}

export default function TechnicalSafetyRequirements({
  itemContext,
  scenario,
  asilResult,
  safetyGoal,
  fsrResults,
  initialResults,
  onPrevious,
  onGenerated,
  onContinue,
}: TechnicalSafetyRequirementsProps) {

  const [results, setResults] = useState<TSRResult[]>(initialResults || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const generateTSRs = async () => {

    setError('');

    if (!scenario) {
      setError('Please select a HARA scenario first.');
      return;
    }

    if (!asilResult) {
      setError('ASIL assessment is required before generating TSRs.');
      return;
    }

    if (!safetyGoal) {
      setError('Safety Goal is required before generating TSRs.');
      return;
    }

    if (!fsrResults || fsrResults.length === 0) {
      setError('Please generate Functional Safety Requirements first.');
      return;
    }

    setLoading(true);

    try {

      const generated: TSRResult[] = [];

      for (const fsr of fsrResults) {

        const response = await fetch(
          'http://127.0.0.1:8000/api/tsr/generate',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              system: itemContext.systemItem,
              function: itemContext.intendedFunction,
              malfunction: scenario.malfunction,
              hazard: scenario.hazard,
              hazardous_event: scenario.event,
              safety_goal: safetyGoal.safety_goal,
              fsr: fsr.requirement,
              candidate_asil: asilResult.asil,
            }),
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail ||
            'Technical Safety Requirement generation failed.'
          );
        }

        if (Array.isArray(data.tsr_results)) {
          generated.push(...data.tsr_results);
        }
      }

      setResults(generated);
      onGenerated(generated);

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : 'Technical Safety Requirement generation failed.'
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div className="min-h-full bg-slate-100 p-6">

      <div className="mx-auto max-w-7xl space-y-6">

        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            Technical Safety Requirements
          </h1>

          <p className="mt-1 text-sm text-slate-600">
            Derive technical implementation requirements from the approved
            Functional Safety Requirements.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              System
            </p>

            <p className="mt-2 text-sm font-semibold text-slate-900">
              {itemContext.systemItem || 'Not available'}
            </p>

          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Candidate ASIL
            </p>

            <p className="mt-2 text-2xl font-bold text-blue-700">
              {asilResult?.asil || '—'}
            </p>

          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              FSR Count
            </p>

            <p className="mt-2 text-2xl font-bold text-slate-900">
              {fsrResults.length}
            </p>

          </div>

        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="flex items-center justify-between gap-4">

            <div>

              <h2 className="text-lg font-semibold text-slate-900">
                FSR → TSR Derivation
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                Existing TSR engineering rules are used to derive candidate
                technical safety requirements.
              </p>

            </div>

            <button
              onClick={generateTSRs}
              disabled={loading}
              className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? 'Generating TSRs...' : 'Generate TSRs'}
            </button>

          </div>

          {error && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

        </div>

        {results.length > 0 && (

          <div className="space-y-4">

            <div className="flex items-center justify-between">

              <div>
                <h2 className="text-lg font-semibold text-slate-900">
                  Generated Technical Safety Requirements
                </h2>

                <p className="text-sm text-slate-500">
                  {results.length} candidate TSR
                  {results.length === 1 ? '' : 's'} generated.
                </p>
              </div>

              <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                Pending Review
              </span>

            </div>

            {results.map((tsr, index) => (

              <div
                key={`${tsr.id}-${index}`}
                className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              >

                <div className="flex items-start justify-between gap-4">

                  <div>

                    <span className="inline-flex rounded-md bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">
                      {tsr.id}
                    </span>

                    <h3 className="mt-3 text-base font-semibold text-slate-900">
                      Technical Safety Requirement
                    </h3>

                  </div>

                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-600">
                    ASIL {tsr.candidate_asil}
                  </span>

                </div>

                <div className="mt-5 rounded-lg bg-slate-50 p-4">

                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Requirement
                  </p>

                  <p className="mt-2 text-sm leading-6 text-slate-900">
                    {tsr.requirement}
                  </p>

                </div>

                <div className="mt-4">

                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Engineering Rationale
                  </p>

                  <p className="mt-2 text-sm leading-6 text-slate-600">
                    {tsr.rationale}
                  </p>

                </div>

                <div className="mt-5 grid grid-cols-1 gap-4 md:grid-cols-2">

                  <div>
                    <p className="text-xs font-semibold text-slate-500">
                      Linked FSR
                    </p>

                    <p className="mt-1 text-sm text-slate-800">
                      {tsr.fsr}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs font-semibold text-slate-500">
                      Safety Goal
                    </p>

                    <p className="mt-1 text-sm text-slate-800">
                      {tsr.safety_goal}
                    </p>
                  </div>

                  <AiRequirementRecommendation
                    type="TSR"
                    context={{
                      system: tsr.system,
                      function: tsr.function,
                      malfunction: tsr.malfunction,
                      hazard: tsr.hazard,
                      hazardous_event: tsr.hazardous_event,
                      safety_goal: tsr.safety_goal,
                      candidate_asil: tsr.candidate_asil,
                      source_requirement: tsr.requirement,
                      source_rationale: tsr.rationale,
                    }}
                    onUse={(value) => {
                      const updated = results.map((item) =>
                        item.id === tsr.id
                          ? {
                              ...item,
                              requirement: value,
                            }
                          : item
                      );

                      setResults(updated);
                      onGenerated(updated);
                    }}
                  />

                </div>

              </div>

            ))}

          </div>

        )}

        <div className="flex items-center justify-between border-t border-slate-200 pt-5">

          <button
            onClick={onPrevious}
            className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          >
            ← Previous
          </button>

          <button
            onClick={onContinue}
            disabled={results.length === 0}
            className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Continue to Traceability Matrix →
          </button>

        </div>

      </div>

    </div>
  );
}
