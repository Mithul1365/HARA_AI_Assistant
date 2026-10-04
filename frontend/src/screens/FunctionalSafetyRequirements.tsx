import { useState } from 'react';

import type {
  ItemContext,
  HaraScenario,
} from '@/App';

import AiRequirementRecommendation
  from '@/components/AiRequirementRecommendation';

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

interface FSRResult {
  id: string;
  requirement: string;
  rationale: string;
  candidate_asil: string;
  review_status: string;
  hazard: string;
  hazardous_event: string;
  system: string;
  function: string;
  malfunction: string;
  safety_goal: string;
}

interface FunctionalSafetyRequirementsProps {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  asilResult: AsilResult | null;
  safetyGoal: SafetyGoalResult | null;
  initialResults?: FSRResult[];
  onPrevious: () => void;
  onGenerated: (results: FSRResult[]) => void;
  onContinue: () => void;
}

function FunctionalSafetyRequirements({
  itemContext,
  scenario,
  asilResult,
  safetyGoal,
  initialResults = [],
  onPrevious,
  onGenerated,
  onContinue,
}: FunctionalSafetyRequirementsProps) {

  const [results, setResults] =
    useState<FSRResult[]>(initialResults);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState('');

  /*
   * ------------------------------------------------------------
   * Update ONE FSR requirement
   *
   * IMPORTANT:
   * We preserve every existing FSR field.
   * Only "requirement" is changed.
   *
   * This keeps:
   * - FSR ID
   * - ASIL
   * - rationale
   * - hazard
   * - hazardous event
   * - malfunction
   * - safety goal
   * - traceability
   * intact for downstream TSR / Quality / Traceability.
   * ------------------------------------------------------------
   */
  const updateRequirement = (
    fsrId: string,
    requirement: string
  ) => {
    const updated = results.map((item) =>
      item.id === fsrId
        ? {
            ...item,
            requirement,
          }
        : item
    );

    setResults(updated);
    onGenerated(updated);
  };

  /*
   * ------------------------------------------------------------
   * Generate FSRs from the existing backend engine
   *
   * DO NOT change this API flow.
   * TSR depends on the generated FSR structure.
   * ------------------------------------------------------------
   */
  const generateFSRs = async () => {

    if (!scenario) {
      setError(
        'HARA scenario is not available.'
      );
      return;
    }

    if (!asilResult?.asil) {
      setError(
        'ASIL Assessment is not available.'
      );
      return;
    }

    if (!safetyGoal?.safety_goal) {
      setError(
        'Please generate the Safety Goal first.'
      );
      return;
    }

    setLoading(true);
    setError('');

    try {

      const response = await fetch(
        'http://127.0.0.1:8000/api/fsr/generate',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            system:
              itemContext.systemItem,

            function:
              itemContext.intendedFunction,

            malfunction:
              scenario.malfunction,

            hazard:
              scenario.hazard,

            hazardous_event:
              scenario.event,

            safety_goal:
              safetyGoal.safety_goal,

            candidate_asil:
              asilResult.asil,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(
          `FSR API failed with status ${response.status}`
        );
      }

      const data =
        await response.json();

      if (
        !data.success ||
        !Array.isArray(data.fsr_results)
      ) {
        throw new Error(
          data.message ||
          'FSR generation failed.'
        );
      }

      setResults(
        data.fsr_results
      );

      onGenerated(
        data.fsr_results
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : 'Unable to generate FSRs.'
      );

    } finally {

      setLoading(false);

    }
  };

  return (
    <div className="min-h-full bg-slate-50 p-6 lg:p-8">

      <div className="mx-auto max-w-6xl">

        {/* =====================================================
            HEADER
        ====================================================== */}

        <div className="mb-6">

          <h1 className="text-2xl font-bold text-slate-900">
            5. Functional Safety Requirements
          </h1>

          <p className="mt-1 text-sm text-slate-500">
            Generate candidate Functional Safety Requirements
            from the Safety Goal and HARA context.
          </p>

        </div>

        {/* =====================================================
            TRACEABILITY CONTEXT
        ====================================================== */}

        <div className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">

          <div className="mb-4">

            <h2 className="text-sm font-bold text-slate-900">
              FSR Traceability Context
            </h2>

            <p className="mt-1 text-xs text-slate-500">
              The following engineering context is used to
              generate and refine the Functional Safety Requirements.
            </p>

          </div>

          <div className="grid gap-4 md:grid-cols-2">

            <div>
              <p className="text-xs font-semibold text-slate-500">
                System
              </p>

              <p className="mt-1 text-sm text-slate-800">
                {itemContext.systemItem}
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500">
                Function
              </p>

              <p className="mt-1 text-sm text-slate-800">
                {itemContext.intendedFunction}
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500">
                Malfunction
              </p>

              <p className="mt-1 text-sm text-slate-800">
                {scenario?.malfunction || '-'}
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500">
                Hazard
              </p>

              <p className="mt-1 text-sm text-slate-800">
                {scenario?.hazard || '-'}
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500">
                Hazardous Event
              </p>

              <p className="mt-1 text-sm text-slate-800">
                {scenario?.event || '-'}
              </p>
            </div>

            <div>
              <p className="text-xs font-semibold text-slate-500">
                Candidate ASIL
              </p>

              <p className="mt-1 text-sm font-bold text-indigo-700">
                {asilResult?.asil || '-'}
              </p>
            </div>

          </div>

          <div className="mt-4">

            <p className="text-xs font-semibold text-slate-500">
              Safety Goal
            </p>

            <p className="mt-1 text-sm leading-6 text-slate-800">
              {safetyGoal?.safety_goal || '-'}
            </p>

          </div>

        </div>

        {/* =====================================================
            GENERATE BUTTON
        ====================================================== */}

        <div className="mb-6">

          <button
            type="button"
            onClick={generateFSRs}
            disabled={loading}
            className="rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {loading
              ? 'Generating Functional Safety Requirements...'
              : 'Generate Functional Safety Requirements'}
          </button>

        </div>

        {/* =====================================================
            ERROR
        ====================================================== */}

        {error && (
          <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* =====================================================
            GENERATED FSR RESULTS
        ====================================================== */}

        {results.length > 0 && (

          <div className="space-y-5">

            <div className="flex items-center justify-between">

              <div>

                <h2 className="text-lg font-bold text-slate-900">
                  Generated Functional Safety Requirements
                </h2>

                <p className="mt-1 text-sm text-slate-500">
                  {results.length} candidate Functional Safety
                  Requirement(s) generated.
                </p>

              </div>

              <div className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                {results.length} FSR
                {results.length !== 1 ? 's' : ''}
              </div>

            </div>

            {/* =================================================
                FSR CARDS
            ================================================== */}

            {results.map((fsr) => (

              <div
                key={fsr.id}
                className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm"
              >

                {/* ---------------------------------------------
                    FSR HEADER
                ---------------------------------------------- */}

                <div className="flex flex-wrap items-start justify-between gap-3">

                  <div>

                    <h3 className="text-lg font-bold text-slate-900">
                      {fsr.id}
                    </h3>

                    <p className="mt-1 text-xs text-slate-500">
                      Functional Safety Requirement
                    </p>

                  </div>

                  <div className="flex flex-wrap gap-2">

                    <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
                      ASIL {fsr.candidate_asil}
                    </span>

                    <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">
                      {fsr.review_status}
                    </span>

                  </div>

                </div>

                {/* ---------------------------------------------
                    REQUIREMENT — CONTROLLED FIELD
                ---------------------------------------------- */}

                <div className="mt-5">

                  <div className="flex items-center justify-between gap-3">

                    <label
                      htmlFor={`fsr-requirement-${fsr.id}`}
                      className="text-sm font-bold text-slate-900"
                    >
                      Functional Safety Requirement
                    </label>

                    <span className="text-[11px] font-medium text-slate-400">
                      Editable
                    </span>

                  </div>

                  <textarea
                    id={`fsr-requirement-${fsr.id}`}
                    value={fsr.requirement}
                    onChange={(event) => {
                      updateRequirement(
                        fsr.id,
                        event.target.value
                      );
                    }}
                    rows={4}
                    className="mt-2 w-full resize-y rounded-lg border border-slate-300 bg-white p-4 text-sm leading-6 text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  />

                  <p className="mt-2 text-[11px] text-slate-500">
                    Manual edits are also synchronized with the
                    application workflow and downstream TSR generation.
                  </p>

                </div>

                {/* ---------------------------------------------
                    RATIONALE
                ---------------------------------------------- */}

                <div className="mt-5 rounded-lg bg-slate-50 p-4">

                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Rationale
                  </p>

                  <p className="mt-2 text-sm leading-6 text-slate-700">
                    {fsr.rationale}
                  </p>

                </div>

                {/* ---------------------------------------------
                    SOURCE HAZARD
                ---------------------------------------------- */}

                <div className="mt-4 grid gap-4 md:grid-cols-3">

                  <div>

                    <p className="text-xs font-semibold text-slate-500">
                      ASIL
                    </p>

                    <p className="mt-1 text-sm font-semibold text-slate-900">
                      {fsr.candidate_asil}
                    </p>

                  </div>

                  <div>

                    <p className="text-xs font-semibold text-slate-500">
                      Review Status
                    </p>

                    <p className="mt-1 text-sm text-slate-900">
                      {fsr.review_status}
                    </p>

                  </div>

                  <div>

                    <p className="text-xs font-semibold text-slate-500">
                      Source Hazard
                    </p>

                    <p className="mt-1 text-sm text-slate-900">
                      {fsr.hazard}
                    </p>

                  </div>

                </div>

                {/* ---------------------------------------------
                    TRACEABILITY
                ---------------------------------------------- */}

                <details className="mt-5 rounded-lg border border-slate-200">

                  <summary className="cursor-pointer px-4 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50">
                    🔗 Traceability Details
                  </summary>

                  <div className="grid gap-4 border-t border-slate-200 p-4 md:grid-cols-2">

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        System
                      </p>

                      <p className="mt-1 text-sm text-slate-800">
                        {fsr.system}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        Function
                      </p>

                      <p className="mt-1 text-sm text-slate-800">
                        {fsr.function}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        Malfunction
                      </p>

                      <p className="mt-1 text-sm text-slate-800">
                        {fsr.malfunction}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        Hazard
                      </p>

                      <p className="mt-1 text-sm text-slate-800">
                        {fsr.hazard}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        Hazardous Event
                      </p>

                      <p className="mt-1 text-sm text-slate-800">
                        {fsr.hazardous_event}
                      </p>

                    </div>

                    <div>

                      <p className="text-xs font-semibold text-slate-500">
                        Candidate ASIL
                      </p>

                      <p className="mt-1 text-sm font-semibold text-indigo-700">
                        {fsr.candidate_asil}
                      </p>

                    </div>

                    <div className="md:col-span-2">

                      <p className="text-xs font-semibold text-slate-500">
                        Linked Safety Goal
                      </p>

                      <p className="mt-1 text-sm leading-6 text-slate-800">
                        {fsr.safety_goal}
                      </p>

                    </div>

                  </div>

                </details>

                {/* ---------------------------------------------
                    AI RECOMMENDATION
                ---------------------------------------------- */}

                <AiRequirementRecommendation
                  type="FSR"

                  context={{
                    system:
                      fsr.system || '',

                    function:
                      fsr.function || '',

                    malfunction:
                      fsr.malfunction || '',

                    hazard:
                      fsr.hazard || '',

                    hazardous_event:
                      fsr.hazardous_event || '',

                    safety_goal:
                      fsr.safety_goal || '',

                    candidate_asil:
                      fsr.candidate_asil || '',

                    source_requirement:
                      fsr.requirement || '',

                    source_rationale:
                      fsr.rationale || '',
                  }}

                  onUse={(value) => {
                    updateRequirement(
                      fsr.id,
                      value
                    );
                  }}
                />

              </div>

            ))}

            {/* =================================================
                ENGINEERING REVIEW NOTICE
            ================================================== */}

            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">

              <p className="text-sm font-semibold text-amber-900">
                Engineering Review Required
              </p>

              <p className="mt-1 text-xs leading-5 text-amber-800">
                These FSRs are AI-assisted candidate drafts.
                They must be reviewed, refined and approved by
                an authorized functional-safety engineer before
                being used as official safety requirements.
              </p>

            </div>

          </div>

        )}

        {/* =====================================================
            EMPTY STATE
        ====================================================== */}

        {results.length === 0 && !loading && (

          <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center">

            <h2 className="text-lg font-semibold text-slate-800">
              No Functional Safety Requirements yet
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Generate the candidate FSRs from the approved
              Safety Goal and HARA context.
            </p>

          </div>

        )}

        {/* =====================================================
            NAVIGATION
        ====================================================== */}

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3">

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
            disabled={results.length === 0}
            className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-50"
          >
            Continue to TSR →
          </button>

        </div>

      </div>

    </div>
  );
}

export default FunctionalSafetyRequirements;