import { useState } from 'react';

import type {
  ItemContext,
  HaraScenario,
  AsilResult,
  SafetyGoalResult,
  FSRResult,
} from '@/App';

interface TraceabilityMatrixProps {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  asilResult: AsilResult | null;
  safetyGoal: SafetyGoalResult | null;
  fsrResults: FSRResult[];
  tsrResults: any[];
  onPrevious: () => void;
  onContinue: () => void;
}

interface TraceabilityRow {
  [key: string]: unknown;
}

export default function TraceabilityMatrix({
  itemContext,
  scenario,
  asilResult,
  safetyGoal,
  fsrResults,
  tsrResults,
  onPrevious,
  onContinue,
}: TraceabilityMatrixProps) {

  const [rows, setRows] = useState<TraceabilityRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [generated, setGenerated] = useState(false);

  const buildMatrix = async () => {
    setError('');

    if (!scenario) {
      setError('Please select a HARA scenario first.');
      return;
    }

    if (!asilResult?.asil) {
      setError('ASIL Assessment is required.');
      return;
    }

    if (!safetyGoal?.safety_goal) {
      setError('Safety Goal is required.');
      return;
    }

    if (!fsrResults || fsrResults.length === 0) {
      setError('Functional Safety Requirements are required.');
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/traceability/build',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            hara_candidate: {
              number: scenario.number,
              malfunction: scenario.malfunction,
              hazard: scenario.hazard,
              hazardous_event: scenario.event,
              rationale: scenario.rationale,
              system: itemContext.systemItem,
              function: itemContext.intendedFunction,
            },
            candidate_asil: asilResult.asil,
            safety_goal: {
              ...safetyGoal,
              candidate_asil: asilResult.asil,
              system: itemContext.systemItem,
              function: itemContext.intendedFunction,
              malfunction: scenario.malfunction,
              hazard: scenario.hazard,
              hazardous_event: scenario.event,
            },
            fsr_results: fsrResults,
            tsr_results: tsrResults || [],
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
          `Traceability API failed with status ${response.status}`
        );
      }

      if (!data.success || !Array.isArray(data.traceability_rows)) {
        throw new Error(
          data.message ||
          'Traceability matrix generation failed.'
        );
      }

      setRows(data.traceability_rows);
      setGenerated(true);

    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Traceability generation failed.'
      );
    } finally {
      setLoading(false);
    }
  };

  const formatValue = (value: unknown) => {
    if (
      value === null ||
      value === undefined ||
      value === ''
    ) {
      return '—';
    }

    if (typeof value === 'object') {
      return JSON.stringify(value);
    }

    return String(value);
  };

  return (
    <div className="space-y-6">

      <div>
        <div className="text-sm font-semibold text-blue-600">
          STEP 7
        </div>

        <h1 className="text-2xl font-bold text-slate-900">
          Traceability Matrix
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          End-to-end traceability from HARA through ASIL,
          Safety Goal, FSR and TSR.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

        <div className="grid grid-cols-4 gap-4">

          <div className="rounded-lg bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">
              HARA
            </div>
            <div className="mt-1 font-semibold text-slate-900">
              {scenario ? `HARA-${String(scenario.number).padStart(3, '0')}` : '—'}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">
              CANDIDATE ASIL
            </div>
            <div className="mt-1 font-semibold text-blue-700">
              {asilResult?.asil || '—'}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">
              SAFETY GOAL
            </div>
            <div className="mt-1 font-semibold text-slate-900">
              {safetyGoal?.id || '—'}
            </div>
          </div>

          <div className="rounded-lg bg-slate-50 p-4">
            <div className="text-xs font-semibold text-slate-500">
              TSR LINKS
            </div>
            <div className="mt-1 font-semibold text-slate-900">
              {tsrResults?.length || 0}
            </div>
          </div>

        </div>

        <div className="mt-6 rounded-lg border border-blue-100 bg-blue-50 p-5">

          <div className="text-xs font-semibold uppercase tracking-wide text-blue-600">
            Selected Safety Chain
          </div>

          <div className="mt-3 space-y-2 text-sm text-slate-800">

            <div>
              <span className="font-semibold">{scenario ? `HARA-${String(scenario.number).padStart(3, '0')}:` : '—'}</span>{' '}
              {scenario?.malfunction}
            </div>

            <div className="text-slate-400 text-center my-1">↓</div>

            <div>
              <span className="font-semibold">
                ASIL {asilResult?.asil}
              </span>
            </div>

            <div className="text-slate-400 text-center my-1">↓</div>

            <div>
              <span className="font-semibold">
                {safetyGoal?.id || '—'}:
              </span>{' '}
              {safetyGoal?.safety_goal}
            </div>

            <div className="text-slate-400 text-center my-1">↓</div>

            <div>
              <span className="font-semibold">
                Functional Safety Requirements:
              </span>{' '}
              {fsrResults.length}
            </div>

            <div className="text-slate-400 text-center my-1">↓</div>

            <div>
              <span className="font-semibold">
                Technical Safety Requirements:
              </span>{' '}
              {tsrResults.length}
            </div>

          </div>

        </div>

        {!generated && (
          <div className="mt-6 flex justify-center">
            <button
              onClick={buildMatrix}
              disabled={loading}
              className="rounded-lg bg-blue-700 px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading
                ? 'Building Traceability Matrix...'
                : 'Build Traceability Matrix'}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

      </div>

      {generated && (
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">

          <div className="mb-5 flex items-center justify-between">

            <div>
              <h2 className="text-lg font-bold text-slate-900">
                Traceability Links
              </h2>

              <p className="text-sm text-slate-500">
                {rows.length} traceability row(s) generated from
                the existing engineering traceability engine.
              </p>
            </div>

            <div className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
              Generated
            </div>

          </div>

          {rows.length === 0 ? (

            <div className="rounded-lg bg-slate-50 p-6 text-center text-sm text-slate-500">
              No traceability rows were returned.
            </div>

          ) : (

            <div className="overflow-x-auto rounded-lg border border-slate-200">

              <table className="min-w-full text-left text-sm">

                <thead className="bg-slate-50">

                  <tr>
                    {Object.keys(rows[0]).map((key) => (
                      <th
                        key={key}
                        className="whitespace-nowrap border-b border-slate-200 px-4 py-3 font-semibold text-slate-700"
                      >
                        {key.replace(/_/g, ' ')}
                      </th>
                    ))}
                  </tr>

                </thead>

                <tbody>

                  {rows.map((row, index) => (
                    <tr
                      key={index}
                      className="border-b border-slate-100 last:border-b-0"
                    >

                      {Object.keys(rows[0]).map((key) => (
                        <td
                          key={key}
                          className="max-w-md px-4 py-4 align-top text-slate-700"
                        >
                          {formatValue(row[key])}
                        </td>
                      ))}

                    </tr>
                  ))}

                </tbody>

              </table>

            </div>

          )}

        </div>
      )}

      <div className="flex items-center justify-between">

        <button
          onClick={onPrevious}
          className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Previous
        </button>

        <button
          onClick={onContinue}
          disabled={!generated}
          className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Continue to Verification Evidence
        </button>

      </div>

    </div>
  );
}




