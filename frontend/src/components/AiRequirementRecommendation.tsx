import { useState } from "react";

interface AiRequirementRecommendationProps {
  type: "FSR" | "TSR";
  context: {
    system?: string;
    function?: string;
    malfunction?: string;
    hazard?: string;
    hazardous_event?: string;
    safety_goal?: string;
    candidate_asil?: string;
    source_requirement?: string;
    source_rationale?: string;
  };
  onUse: (recommendation: string) => void;
}

interface RecommendationResponse {
  recommendation: string;
  rationale: string;
  confidence: number;
  verification_focus: string;
  review_required: boolean;
}

function toText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function toConfidence(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) {
    return value > 1 ? value / 100 : value;
  }

  if (typeof value === "string") {
    const normalized = value.trim().toUpperCase();
    if (normalized === "HIGH") return 0.9;
    if (normalized === "MEDIUM") return 0.7;
    if (normalized === "LOW") return 0.4;

    const parsed = Number(normalized);
    if (Number.isFinite(parsed)) {
      return parsed > 1 ? parsed / 100 : parsed;
    }
  }

  return 0;
}

function normalizeResponse(value: unknown): RecommendationResponse | null {
  if (!value || typeof value !== "object") {
    return null;
  }

  const root = value as Record<string, unknown>;

  // The API currently returns:
  // { success: true, recommendation: { recommendation: "...", ... } }
  // Also support a direct recommendation object for compatibility.
  const source =
    root.recommendation && typeof root.recommendation === "object"
      ? (root.recommendation as Record<string, unknown>)
      : root;

  const recommendation = toText(source.recommendation).trim();

  if (!recommendation) {
    return null;
  }

  return {
    recommendation,
    rationale: toText(source.rationale),
    confidence: toConfidence(source.confidence),
    verification_focus: toText(source.verification_focus),
    review_required:
      typeof source.review_required === "boolean"
        ? source.review_required
        : true,
  };
}

export default function AiRequirementRecommendation({
  type,
  context,
  onUse,
}: AiRequirementRecommendationProps) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<RecommendationResponse | null>(null);
  const [applied, setApplied] = useState(false);
  const [error, setError] = useState("");

  const generateRecommendation = async () => {
    setLoading(true);
    setError("");
    setApplied(false);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/api/ai/requirement-recommend",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            requirement_type: type,
            ...context,
          }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const raw: unknown = await response.json();
      const normalized = normalizeResponse(raw);

      if (!normalized) {
        throw new Error("AI response did not contain a valid recommendation.");
      }

      setData(normalized);
    } catch (err) {
      console.error("AI recommendation error:", err);
      setData(null);
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate AI recommendation."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleUseRecommendation = () => {
    const recommendation = data?.recommendation.trim();

    if (!recommendation) {
      return;
    }

    // IMPORTANT: only the requirement string is sent to FSR/TSR.
    onUse(recommendation);
    setApplied(true);
  };

  return (
    <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h4 className="text-sm font-bold text-indigo-900">
            AI {type} Recommendation
          </h4>
          <p className="text-xs text-indigo-700">
            AI-generated engineering recommendation for review.
          </p>
        </div>

        <button
          type="button"
          onClick={generateRecommendation}
          disabled={loading}
          className="rounded-lg bg-indigo-600 px-4 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Generating..." : "Generate Recommendation"}
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded-lg border border-red-200 bg-red-50 p-3 text-xs text-red-700">
          {error}
        </div>
      )}

      {data && (
        <div className="space-y-3">
          <div className="rounded-lg border border-indigo-200 bg-white p-3">
            <div className="mb-1 text-xs font-semibold text-gray-500">
              AI Recommendation
            </div>
            <p className="text-sm leading-6 text-gray-900">
              {data.recommendation}
            </p>
          </div>

          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <div className="mb-1 text-xs font-semibold text-gray-500">
              Rationale
            </div>
            <p className="text-sm leading-6 text-gray-700">
              {data.rationale}
            </p>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-white p-3">
              <div className="text-xs font-semibold text-gray-500">
                Confidence
              </div>
              <div className="mt-1 text-sm font-bold text-gray-900">
                {Math.round(data.confidence * 100)}%
              </div>
            </div>

            <div className="rounded-lg bg-white p-3 md:col-span-2">
              <div className="text-xs font-semibold text-gray-500">
                Verification Focus
              </div>
              <div className="mt-1 text-sm text-gray-700">
                {data.verification_focus}
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-amber-200 bg-amber-50 p-3">
            <div className="text-xs text-amber-800">
              Final engineering review is required before acceptance.
            </div>
            <button
              type="button"
              onClick={handleUseRecommendation}
              className="rounded-lg border border-indigo-300 bg-white px-4 py-2 text-xs font-semibold text-indigo-700 hover:bg-indigo-100"
            >
              {applied ? "✓ Applied" : "Use AI Recommendation"}
            </button>
          </div>

          {applied && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-3 text-xs font-semibold text-green-700">
              ✓ AI recommendation applied to the requirement.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
