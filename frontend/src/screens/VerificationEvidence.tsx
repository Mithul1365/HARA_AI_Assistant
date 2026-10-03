import { useEffect, useState } from 'react';
import type { ItemContext, HaraScenario } from '@/App';

interface VerificationRecord {
  timestamp_utc: string;
  artifact_id: string;
  artifact_name: string;
  verification_method: string;
  result: string;
  linked_requirement: string;
  evidence_reference: string;
  notes: string;
}

interface Props {
  itemContext: ItemContext;
  scenario: HaraScenario | null;
  onPrevious: () => void;
  onContinue: () => void;
}

const HARA_VERIFICATION_DRAFT_KEY =
  'hara_ai_assistant_verification_draft';

export default function VerificationEvidence({
  itemContext,
  scenario,
  onPrevious,
  onContinue,
}: Props) {
  const [records, setRecords] = useState<VerificationRecord[]>([]);
  const [artifactId, setArtifactId] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.artifactId || '';
    } catch {
      return '';
    }
  });
  const [artifactName, setArtifactName] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.artifactName || '';
    } catch {
      return '';
    }
  });
  const [verificationMethod, setVerificationMethod] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.verificationMethod || '';
    } catch {
      return '';
    }
  });
  const [result, setResult] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.result || 'PASS';
    } catch {
      return 'PASS';
    }
  });
  const [linkedRequirement, setLinkedRequirement] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.linkedRequirement || '';
    } catch {
      return '';
    }
  });
  const [evidenceReference, setEvidenceReference] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.evidenceReference || '';
    } catch {
      return '';
    }
  });
  const [notes, setNotes] = useState(() => {
    try {
      const saved = JSON.parse(
        localStorage.getItem(HARA_VERIFICATION_DRAFT_KEY) || 'null'
      );
      return saved?.notes || '';
    } catch {
      return '';
    }
  });
  const [loading, setLoading] = useState(false);
  const [loadingRecords, setLoadingRecords] = useState(true);
  const [message, setMessage] = useState('');

  useEffect(() => {
    try {
      localStorage.setItem(
        HARA_VERIFICATION_DRAFT_KEY,
        JSON.stringify({
          artifactId,
          artifactName,
          verificationMethod,
          result,
          linkedRequirement,
          evidenceReference,
          notes,
        })
      );
    } catch {
      // Ignore localStorage errors.
    }
  }, [
    artifactId,
    artifactName,
    verificationMethod,
    result,
    linkedRequirement,
    evidenceReference,
    notes,
  ]);

  const loadRecords = async () => {
    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/verification/evidence'
      );

      if (!response.ok) {
        throw new Error('Failed to load verification evidence');
      }

      const data = await response.json();
      setRecords(data.records || []);
    } catch (error) {
      console.error(error);
    } finally {
      setLoadingRecords(false);
    }
  };

  useEffect(() => {
    loadRecords();
  }, []);

  const addEvidence = async () => {
    if (
      !artifactId.trim() ||
      !artifactName.trim() ||
      !verificationMethod.trim() ||
      !linkedRequirement.trim()
    ) {
      setMessage('Please fill all required fields.');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/verification/evidence',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            artifact_id: artifactId,
            artifact_name: artifactName,
            verification_method: verificationMethod,
            result,
            linked_requirement: linkedRequirement,
            evidence_reference: evidenceReference,
            notes,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Failed to save evidence');
      }

      setRecords((current) => [...current, data.record]);

      setArtifactId('');
      setArtifactName('');
      setVerificationMethod('');
      setResult('PASS');
      setLinkedRequirement('');
      setEvidenceReference('');
      setNotes('');

      localStorage.removeItem(HARA_VERIFICATION_DRAFT_KEY);
      setMessage('Verification evidence added successfully.');
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to save verification evidence.'
      );
    } finally {
      setLoading(false);
    }
  };

  const clearEvidence = async () => {
    if (!window.confirm('Clear all verification evidence records?')) {
      return;
    }

    try {
      const response = await fetch(
        'http://127.0.0.1:8000/api/verification/evidence',
        {
          method: 'DELETE',
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Failed to clear evidence');
      }

      setRecords([]);
      setMessage('Verification evidence cleared.');
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Failed to clear verification evidence.'
      );
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs font-semibold uppercase tracking-wider text-blue-700">
          Step 8
        </div>
        <h1 className="mt-1 text-2xl font-bold text-slate-900">
          Verification Evidence
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Record verification evidence and link it to the safety requirements.
        </p>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="mb-4">
          <h2 className="text-base font-semibold text-slate-900">
            Verification Context
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {itemContext.system} ? {scenario?.number || 'Selected HARA scenario'}
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Artifact ID *
            </label>
            <input
              value={artifactId}
              onChange={(e) => setArtifactId(e.target.value)}
              placeholder="e.g. TEST-001"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Artifact Name *
            </label>
            <input
              value={artifactName}
              onChange={(e) => setArtifactName(e.target.value)}
              placeholder="e.g. Gateway Integration Test"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Verification Method *
            </label>
            <input
              value={verificationMethod}
              onChange={(e) => setVerificationMethod(e.target.value)}
              placeholder="e.g. Test / Inspection / Analysis"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Result
            </label>
            <select
              value={result}
              onChange={(e) => setResult(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            >
              <option value="PASS">PASS</option>
              <option value="FAIL">FAIL</option>
              <option value="PARTIAL">PARTIAL</option>
              <option value="PENDING">PENDING</option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Linked Requirement *
            </label>
            <input
              value={linkedRequirement}
              onChange={(e) => setLinkedRequirement(e.target.value)}
              placeholder="e.g. TSR-001 / FSR-001 / SG-001"
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Evidence Reference
            </label>
            <input
              value={evidenceReference}
              onChange={(e) => setEvidenceReference(e.target.value)}
              placeholder="Document, test report, log, ticket, file reference..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>

          <div className="md:col-span-2">
            <label className="mb-1 block text-xs font-semibold text-slate-600">
              Notes
            </label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Engineering verification notes..."
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {message && (
          <div className="mt-4 rounded-lg bg-slate-50 px-4 py-3 text-sm text-slate-700">
            {message}
          </div>
        )}

        <div className="mt-5 flex flex-wrap gap-3">
          <button
            onClick={addEvidence}
            disabled={loading}
            className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:opacity-50"
          >
            {loading ? 'Saving...' : 'Add Verification Evidence'}
          </button>

          {records.length > 0 && (
            <button
              onClick={clearEvidence}
              className="rounded-lg border border-red-300 px-5 py-2.5 text-sm font-semibold text-red-700 hover:bg-red-50"
            >
              Clear Evidence
            </button>
          )}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <div>
            <h2 className="font-semibold text-slate-900">
              Verification Evidence Records
            </h2>
            <p className="text-xs text-slate-500">
              {records.length} record{records.length === 1 ? '' : 's'}
            </p>
          </div>
        </div>

        {loadingRecords ? (
          <div className="p-5 text-sm text-slate-500">
            Loading verification records...
          </div>
        ) : records.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">
            No verification evidence recorded yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Artifact</th>
                  <th className="px-4 py-3">Method</th>
                  <th className="px-4 py-3">Result</th>
                  <th className="px-4 py-3">Linked Requirement</th>
                  <th className="px-4 py-3">Evidence</th>
                  <th className="px-4 py-3">Notes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {records.map((record, index) => (
                  <tr key={`${record.timestamp_utc}-${index}`}>
                    <td className="px-4 py-4">
                      <div className="font-semibold text-slate-900">
                        {record.artifact_id}
                      </div>
                      <div className="text-xs text-slate-500">
                        {record.artifact_name}
                      </div>
                    </td>
                    <td className="px-4 py-4 text-slate-700">
                      {record.verification_method}
                    </td>
                    <td className="px-4 py-4">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-700">
                        {record.result}
                      </span>
                    </td>
                    <td className="px-4 py-4 font-medium text-slate-700">
                      {record.linked_requirement}
                    </td>
                    <td className="px-4 py-4 text-slate-600">
                      {record.evidence_reference || '?'}
                    </td>
                    <td className="max-w-xs px-4 py-4 text-slate-600">
                      {record.notes || '?'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="flex justify-between border-t border-slate-200 pt-5">
        <button
          onClick={onPrevious}
          className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
        >
          Previous
        </button>

        <button
          onClick={onContinue}
          className="rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800"
        >
          Continue to Review & Audit
        </button>
      </div>

      <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs leading-5 text-amber-800">
        Verification evidence is a traceability aid. Recorded results do not
        establish safety compliance or replace formal verification, validation,
        or authorized functional-safety review.
      </div>
    </div>
  );
}

