import { useState } from 'react';

import type {
  ItemContext,
  HaraScenario,
} from '@/App';

interface Props {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  onApply: (values: {
    severity: string;
    exposure: string;
    controllability: string;
  }) => void;
}

export default function AiAsilRecommendation({
  itemContext,
  scenario,
  onApply,
}: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const askAI = async () => {
    if (!scenario) {
      setError('Select a HARA scenario first.');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/ai/asil-recommend',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            system: itemContext.systemItem,
            function: itemContext.intendedFunction,
            operational_scenario:
              itemContext.operationalScenario,
            operating_conditions:
              itemContext.operatingConditions,
            malfunction: scenario.malfunction,
            hazard: scenario.hazard,
            hazardous_event: scenario.event,
          }),
        }
      );

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(
          result.detail ||
            'AI ASIL recommendation failed.'
        );
      }

      setData(result.recommendation);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'AI ASIL recommendation failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mb-6 rounded-xl border border-indigo-200 bg-indigo-50 p-5">

      <div className="flex flex-wrap items-center justify-between gap-3">

        <div>
          <div className="text-sm font-bold text-indigo-900">
            AI Recommended Assessment
          </div>

          <div className="mt-1 text-xs text-indigo-700">
            Qwen3 analyzes the selected HARA context and
            suggests Severity, Exposure and Controllability.
          </div>
        </div>

        <button
          type="button"
          onClick={askAI}
          disabled={loading}
          className="rounded-lg bg-indigo-700 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-800 disabled:opacity-50"
        >
          {loading
            ? 'Analyzing...'
            : 'Ask AI for Recommendation'}
        </button>

      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {data && (
        <div className="mt-4 space-y-3">

          <div className="grid gap-3 md:grid-cols-3">

            <div className="rounded-lg bg-white p-4">
              <div className="text-xs text-slate-500">
                Severity
              </div>
              <div className="mt-1 text-xl font-bold text-indigo-700">
                {data.severity}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4">
              <div className="text-xs text-slate-500">
                Exposure
              </div>
              <div className="mt-1 text-xl font-bold text-indigo-700">
                {data.exposure}
              </div>
            </div>

            <div className="rounded-lg bg-white p-4">
              <div className="text-xs text-slate-500">
                Controllability
              </div>
              <div className="mt-1 text-xl font-bold text-indigo-700">
                {data.controllability}
              </div>
            </div>

          </div>

          <div className="rounded-lg bg-white p-4">

            <div className="flex justify-between gap-3">

              <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Why AI recommends this
              </div>

              <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-700">
                AI Confidence: {data.confidence}
              </span>

            </div>

            <p className="mt-2 text-sm leading-6 text-slate-700">
              {data.rationale}
            </p>

          </div>

          <button
            type="button"
            onClick={() => onApply(data)}
            className="rounded-lg border border-indigo-300 bg-white px-4 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
          >
            Use AI Recommendation
          </button>

          <p className="text-[11px] text-amber-700">
            AI output is decision support only. Final S/E/C
            selection and ASIL classification require engineering review.
          </p>

        </div>
      )}

    </div>
  );
}
