import { useState } from 'react';

interface Props {
  type: 'FSR' | 'TSR';
  context: Record<string, string>;
  onUse?: (value: string) => void;
}

export default function AiRequirementRecommendation({
  type,
  context,
  onUse,
}: Props) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const askAI = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/ai/requirement-recommend',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            requirement_type: type,
            ...context,
          }),
        }
      );

      const result = await response.json();

      if (!response.ok || !result.success) {
        throw new Error(
          result.detail ||
            'AI recommendation failed.'
        );
      }

      setData(result.recommendation);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'AI recommendation failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-5 rounded-xl border border-indigo-200 bg-indigo-50 p-5">

      <div className="flex flex-wrap items-center justify-between gap-3">

        <div>
          <div className="text-sm font-bold text-indigo-900">
            AI Engineering Recommendation
          </div>

          <div className="mt-1 text-xs text-indigo-700">
            Qwen3-assisted {type} refinement.
            The existing {type} engine remains unchanged.
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
            : `Ask AI for ${type}`}
        </button>

      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {data && (
        <div className="mt-4 space-y-3">

          <div className="rounded-lg bg-white p-4">

            <div className="flex items-center justify-between gap-3">

              <div className="text-xs font-semibold uppercase tracking-wide text-indigo-700">
                AI Recommended {type}
              </div>

              <span className="rounded-full bg-indigo-100 px-2.5 py-1 text-xs font-semibold text-indigo-700">
                AI Confidence: {data.confidence}
              </span>

            </div>

            <p className="mt-2 text-sm leading-6 text-slate-900">
              {data.recommendation}
            </p>

          </div>

          <div className="rounded-lg bg-white p-4">

            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Why AI recommends this
            </div>

            <p className="mt-2 text-sm leading-6 text-slate-700">
              {data.rationale}
            </p>

          </div>

          <div className="rounded-lg bg-white p-4">

            <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Verification Focus
            </div>

            <p className="mt-2 text-sm text-slate-700">
              {data.verification_focus}
            </p>

          </div>

          {onUse && (
            <button
              type="button"
              onClick={() =>
                onUse(data.recommendation)
              }
              className="rounded-lg border border-indigo-300 bg-white px-4 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
            >
              Use AI Recommendation
            </button>
          )}

          <p className="text-[11px] text-amber-700">
            AI output is candidate decision support.
            Engineer review and approval are required before official use.
          </p>

        </div>
      )}

    </div>
  );
}
