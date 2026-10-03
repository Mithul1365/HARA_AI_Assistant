import { useState } from 'react';

import type {
  ItemContext,
  HaraScenario,
} from '@/App';

interface AsilResult {
  asil: string;
  rationale: string;
}

interface SafetyGoalResult {
  id?: string;
  safety_goal: string;
  candidate_asil: string;
  hazard: string;
  hazardous_event: string;
  malfunction: string;
  system?: string;
  function?: string;
}

interface SafetyGoalsProps {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  asilResult: AsilResult | null;
  initialResult?: SafetyGoalResult | null;
  onPrevious: () => void;
  onGenerated: (result: SafetyGoalResult) => void;
  onContinue: () => void;
}

function SafetyGoals({
  itemContext,
  scenario,
  asilResult,
  initialResult = null,
  onPrevious,
  onGenerated,
  onContinue,
}: SafetyGoalsProps) {

  const [result, setResult] =
    useState<SafetyGoalResult | null>(initialResult);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState('');

  const generateSafetyGoal = async () => {

    if (!scenario) {
      setError('HARA scenario is not available.');
      return;
    }

    if (!asilResult?.asil) {
      setError('Please complete ASIL Assessment first.');
      return;
    }

    setLoading(true);
    setError('');

    try {

      const response = await fetch(
        'http://127.0.0.1:8000/api/safety-goal/generate',
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
            candidate_asil: asilResult.asil,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `Safety Goal API failed with status ${response.status}`
        );
      }

      const data = await response.json();

      if (!data.success || !data.safety_goal) {
        throw new Error(
          data.message || 'Safety Goal generation failed.'
        );
      }

      setResult(data.safety_goal);
      onGenerated(data.safety_goal);

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to generate Safety Goal.'
      );

    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full bg-slate-50 p-6 lg:p-8">

      <div className="mx-auto max-w-6xl">

        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">
            4. Safety Goals
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Generate a candidate Safety Goal from the selected HARA
            scenario and Candidate ASIL.
          </p>
        </div>

        <div className="mb-6 rounded-xl border border-blue-200 bg-blue-50 p-5">

          <div className="text-sm font-semibold text-blue-900">
            Safety Goal Traceability Context
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">

            <div className="rounded-lg bg-white p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                System / Item
              </div>

              <div className="mt-1 text-sm font-medium text-slate-800">
                {itemContext.systemItem}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Candidate ASIL
              </div>

              <div className="mt-1 text-lg font-bold text-blue-700">
                {asilResult?.asil || 'Not calculated'}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4 md:col-span-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Malfunction
              </div>

              <div className="mt-1 text-sm text-slate-800">
                {scenario?.malfunction || 'Not available'}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4 md:col-span-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Hazard
              </div>

              <div className="mt-1 text-sm text-slate-800">
                {scenario?.hazard || 'Not available'}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4 md:col-span-2">
              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Hazardous Event
              </div>

              <div className="mt-1 text-sm text-slate-800">
                {scenario?.event || 'Not available'}
              </div>
            </div>

          </div>
        </div>

        {!result && (
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

            <h2 className="text-lg font-semibold text-slate-900">
              Generate Candidate Safety Goal
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              The existing HARA Safety Goal engine will generate the
              candidate from the current engineering context.
            </p>

            <button
              type="button"
              onClick={generateSafetyGoal}
              disabled={loading || !scenario || !asilResult}
              className="mt-6 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading
                ? 'Generating Safety Goal...'
                : 'Generate Safety Goal'}
            </button>

            {error && (
              <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

          </div>
        )}

        {result && (
          <div className="space-y-5">

            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <div className="text-sm font-semibold text-green-800">
                Candidate Safety Goal generated successfully
              </div>
            </div>

            <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900">
                  {result.id || 'SG-001'} — Candidate Safety Goal
                </h2>

                <span className="rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-700">
                  ASIL {result.candidate_asil}
                </span>
              </div>

              <div className="mt-5 rounded-lg border border-blue-100 bg-blue-50 p-5">

                <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                  Safety Goal
                </div>

                <p className="mt-2 text-base leading-7 text-slate-900">
                  {result.safety_goal}
                </p>

              </div>

              <div className="mt-5 grid gap-4 md:grid-cols-2">

                <div className="rounded-lg bg-slate-50 p-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Hazard
                  </div>

                  <div className="mt-1 text-sm text-slate-800">
                    {result.hazard}
                  </div>
                </div>

                <div className="rounded-lg bg-slate-50 p-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Hazardous Event
                  </div>

                  <div className="mt-1 text-sm text-slate-800">
                    {result.hazardous_event}
                  </div>
                </div>

              </div>

              <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-800">
                Candidate Safety Goal is AI-assisted decision support.
                Final acceptance must be performed by an authorized
                functional-safety engineer.
              </div>

            </div>

            <div className="flex items-center justify-between border-t border-slate-200 pt-5">

              <button
                type="button"
                onClick={onPrevious}
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                ← Previous
              </button>

              <button
                type="button"
                onClick={onContinue}
                className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
              >
                Continue to FSR →
              </button>

            </div>

          </div>
        )}

      </div>

    </div>
  );
}

export default SafetyGoals;
