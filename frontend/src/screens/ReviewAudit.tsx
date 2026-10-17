import { useEffect, useState } from 'react';
import { ClipboardCheck, History, ShieldCheck, UserCheck, Download } from 'lucide-react';
import type { ItemContext, HaraScenario } from '@/App';

interface ReviewAuditProps {
  itemContext: ItemContext | null;
  scenario: HaraScenario | null;
  asilResult: any;
  safetyGoal: any;
  fsrResults: any[];
  tsrResults: any[];
  onPrevious: () => void;
  onComplete: () => void;
  onNewWorkflow: () => void;
}

interface ReviewRecord {
  timestamp_utc?: string;
  artifact_type?: string;
  artifact_id?: string;
  decision?: string;
  reviewer_name?: string;
  comment?: string;
}

interface AuditRecord {
  timestamp_utc?: string;
  event?: string;
  details?: string;
  "HARA ID"?: string;
  ASIL?: string;
  "Safety Goal ID"?: string;
  "FSR ID"?: string;
  "TSR IDs"?: string;
}

export default function ReviewAudit({
  itemContext,
  scenario,
  asilResult,
  safetyGoal,
  fsrResults,
  tsrResults,
  onPrevious,
  onComplete,
  onNewWorkflow,
}: ReviewAuditProps) {
  const [decision, setDecision] = useState('PENDING REVIEW');
  const [reviewerName, setReviewerName] = useState('');
  const [comment, setComment] = useState('');
  const [latestReview, setLatestReview] = useState<ReviewRecord | null>(null);
  const [auditHistory, setAuditHistory] = useState<AuditRecord[]>([]);
  const [reviewNote, setReviewNote] = useState('');
  const [auditNote, setAuditNote] = useState('');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const loadStatus = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/review-audit/status');
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Unable to load review status.');
      }

      setDecision(data.review_status || 'PENDING REVIEW');
      setLatestReview(data.latest_review || null);
      setAuditHistory(data.audit_history || []);
      setReviewNote(data.review_note || '');
      setAuditNote(data.audit_note || '');

      if (data.latest_review?.reviewer_name) {
        setReviewerName(data.latest_review.reviewer_name);
      }
      if (data.latest_review?.comment) {
        setComment(data.latest_review.comment);
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to load review status.');
    }
  };

  useEffect(() => {
    loadStatus();
  }, []);

  const saveDecision = async () => {
    if (!reviewerName.trim()) {
      setMessage('Reviewer name is required.');
      return;
    }

    setSaving(true);
    setMessage('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/review-audit/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          artifact_type: 'HARA Workflow',
          artifact_id: 'HARA-001',
          decision,
          reviewer_name: reviewerName,
          comment,
          // Persist the current workflow traceability with the review record.
          asil: asilValue,
          safety_goal_id: safetyGoalId,
          fsr_id: fsrId,
          tsr_ids: tsrIds,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Unable to save review decision.');
      }

      setMessage('Review decision saved successfully.');
      await loadStatus();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to save review decision.');
    } finally {
      setSaving(false);
    }
  };

  const clearReviewAudit = async () => {
    if (!window.confirm('Clear all Review & Audit data for this workflow?')) {
      return;
    }

    setSaving(true);
    setMessage('');

    try {
      const response = await fetch('http://127.0.0.1:8000/api/review-audit/clear', {
        method: 'DELETE',
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.detail || 'Unable to clear Review & Audit data.');
      }

      setDecision('PENDING REVIEW');
      setReviewerName('');
      setComment('');
      setLatestReview(null);
      setAuditHistory([]);
      setMessage('Review & Audit data cleared successfully.');
    } catch (error) {
      setMessage(
        error instanceof Error
          ? error.message
          : 'Unable to clear Review & Audit data.'
      );
    } finally {
      setSaving(false);
    }
  };

  const systemItem =
    itemContext?.systemItem?.trim() ||
    (fsrResults?.[0]?.system as string | undefined)?.trim() ||
    (safetyGoal?.system as string | undefined)?.trim() ||
    'Not defined';

  const asilValue =
    asilResult?.candidate_asil ||
    asilResult?.asil ||
    '';

  const safetyGoalId =
    safetyGoal?.id ||
    safetyGoal?.safety_goal_id ||
    '';

  const fsrId =
    fsrResults?.[0]?.id ||
    fsrResults?.[0]?.fsr_id ||
    '';

  const tsrIds = (tsrResults || [])
    .map((item) => item?.id || item?.tsr_id)
    .filter(Boolean);

  const completeWorkflow = async () => {
    setSaving(true);
    setMessage('');

    try {
      await fetch('http://127.0.0.1:8000/api/review-audit/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event: 'Workflow Completed',
          details:
            'HARA workflow completed through Review & Audit after recording the engineering review decision.',
          hara_id: 'HARA-001',
          asil: asilValue,
          safety_goal_id: safetyGoalId,
          fsr_id: fsrId,
          tsr_ids: tsrIds,
        }),
      });

      setMessage('HARA workflow completed and audit event recorded.');
      await loadStatus();
      onComplete();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'Unable to complete workflow.');
    } finally {
      setSaving(false);
    }
  };

  const downloadProjectReport = async () => {
    const reportWindow = window.open('', '_blank');

    if (!reportWindow) {
      setMessage('Please allow pop-ups to generate the PDF report.');
      return;
    }

    const escapeHtml = (value: unknown): string =>
      String(value ?? 'Not available').replace(/[&<>"']/g, (character) => {
        const entities: Record<string, string> = {
          '&': '&amp;',
          '<': '&lt;',
          '>': '&gt;',
          '"': '&quot;',
          "'": '&#39;',
        };
        return entities[character];
      });

    const labelOf = (key: string) =>
      key.replace(/([a-z0-9])([A-Z])/g, '$1 $2')
        .replace(/[_-]+/g, ' ')
        .replace(/\b\w/g, (letter) => letter.toUpperCase());

    const renderValue = (value: any): string => {
      if (value === null || value === undefined || value === '') {
        return '<span class="muted">Not available</span>';
      }

      if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
      }

      if (Array.isArray(value)) {
        if (!value.length) return '<span class="muted">No records available</span>';

        if (value.every((item) => item === null || typeof item !== 'object')) {
          return '<ul>' + value.map((item) =>
            '<li>' + escapeHtml(item) + '</li>'
          ).join('') + '</ul>';
        }

        return '<div class="record-list">' + value.map((item, index) =>
          '<article class="record"><h3>Record ' + (index + 1) +
          '</h3>' + renderValue(item) + '</article>'
        ).join('') + '</div>';
      }

      if (typeof value === 'object') {
        const entries = Object.entries(value).filter(([key]) =>
          !['__typename'].includes(key)
        );

        if (!entries.length) return '<span class="muted">Not available</span>';

        return '<table class="details"><tbody>' + entries.map(([key, item]) =>
          '<tr><th>' + escapeHtml(labelOf(key)) + '</th><td>' +
          renderValue(item) + '</td></tr>'
        ).join('') + '</tbody></table>';
      }

      return escapeHtml(value);
    };

    const section = (title: string, value: unknown) =>
      '<section><h2>' + escapeHtml(title) + '</h2>' +
      renderValue(value) + '</section>';

    const renderRequirements = (items: any[], type: string) => {
      if (!items?.length) {
        return '<p class="muted">No ' + escapeHtml(type) +
          ' records are available in the current workflow.</p>';
      }

      const hiddenKeys = ['__typename'];
      return '<div class="requirement-list">' + items.map((item, index) => {
        if (!item || typeof item !== 'object') {
          return '<article class="record"><h3>' + escapeHtml(type + ' ' + (index + 1)) +
            '</h3><p>' + renderValue(item) + '</p></article>';
        }
        const entries = Object.entries(item).filter(([key, value]) =>
          !hiddenKeys.includes(key) && value !== undefined && value !== null && value !== ''
        );
        const idEntry = entries.find(([key]) => /^(id|fsr_id|tsr_id|requirement_id)$/i.test(key));
        const title = idEntry ? String(idEntry[1]) : type + ' ' + (index + 1);
        const rows = entries.filter(([key]) => !idEntry || key !== idEntry[0]);
        return '<article class="requirement-card"><h3>' + escapeHtml(title) +
          '</h3><table class="details"><tbody>' + rows.map(([key, value]) =>
            '<tr><th>' + escapeHtml(labelOf(key)) + '</th><td>' + renderValue(value) + '</td></tr>'
          ).join('') + '</tbody></table></article>';
      }).join('') + '</div>';
    };

    let evidenceRecords: any[] = [];
    let evidenceError = '';

    try {
      const response = await fetch('http://127.0.0.1:8000/api/verification/evidence');
      if (!response.ok) throw new Error('Evidence API returned HTTP ' + response.status);
      const data = await response.json();
      evidenceRecords = Array.isArray(data.records) ? data.records : [];
    } catch (error) {
      evidenceError = error instanceof Error
        ? error.message
        : 'Unable to load verification evidence.';
    }

    const evidenceHtml = evidenceError
      ? '<p class="warning">Verification evidence could not be loaded: ' +
        escapeHtml(evidenceError) + '. Please check the backend and generate the report again.</p>'
      : !evidenceRecords.length
        ? '<p class="muted">No verification evidence records were found in the backend.</p>'
        : '<div class="record-list">' + evidenceRecords.map((record, index) =>
          '<article class="record"><h3>Evidence ' + (index + 1) +
          (record.artifact_id ? ' — ' + escapeHtml(record.artifact_id) : '') +
          '</h3><table class="details"><tbody>' +
          [['Artifact Name', record.artifact_name], ['Verification Method', record.verification_method],
           ['Result', record.result], ['Linked Requirement', record.linked_requirement],
           ['Evidence Reference', record.evidence_reference], ['Notes', record.notes],
           ['Recorded At (UTC)', record.timestamp_utc]]
            .map(([label, value]) => '<tr><th>' + escapeHtml(label) + '</th><td>' + renderValue(value) + '</td></tr>')
            .join('') + '</tbody></table></article>'
        ).join('') + '</div>';

    const reportHtml = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>HARA Project Report</title>
        <style>
          @page { size: A4; margin: 16mm 14mm 18mm; }
          * { box-sizing: border-box; }
          body {
            font-family: Arial, Helvetica, sans-serif;
            color: #1e293b;
            margin: 0;
            font-size: 10pt;
            line-height: 1.55;
          }
          .cover {
            padding: 28px 0 20px;
            border-bottom: 3px solid #1d4ed8;
            margin-bottom: 26px;
          }
          .eyebrow {
            color: #1d4ed8;
            font-size: 9pt;
            font-weight: bold;
            letter-spacing: 2px;
            text-transform: uppercase;
          }
          h1 { font-size: 27pt; margin: 10px 0 6px; color: #0f172a; }
          .subtitle { color: #64748b; font-size: 11pt; }
          .meta { margin-top: 18px; color: #475569; font-size: 9pt; }
          h2 {
            font-size: 15pt;
            color: #1d4ed8;
            border-bottom: 1px solid #cbd5e1;
            padding-bottom: 7px;
            margin: 26px 0 12px;
          }
          h3 { font-size: 11pt; margin: 0 0 8px; }
          section { margin: 0 0 22px; }
          table {
            width: 100%;
            border-collapse: collapse;
            margin: 8px 0 14px;
            font-size: 9pt;
            table-layout: fixed;
          }
          th {
            background: #eff6ff;
            color: #1e3a8a;
            text-align: left;
            font-weight: bold;
          }
          th, td {
            border: 1px solid #dbe3ee;
            padding: 7px;
            vertical-align: top;
            overflow-wrap: anywhere;
          }
          .details th { width: 30%; }
          .details td { background: #fff; }
          .record-list, .requirement-list { display: block; }
          .record, .requirement-card {
            border: 1px solid #dbe3ee;
            border-radius: 5px;
            padding: 10px;
            margin: 10px 0 14px;
            break-inside: avoid;
            page-break-inside: avoid;
          }
          .record h3, .requirement-card h3 {
            color: #1e3a8a;
            background: #eff6ff;
            padding: 8px 10px;
            border-radius: 3px;
            margin: 0 0 8px;
            overflow-wrap: anywhere;
          }
          .details tr { break-inside: avoid; }
          .details td { overflow-wrap: anywhere; word-break: normal; }
          .details th { overflow-wrap: anywhere; }
          ul { margin: 4px 0; padding-left: 20px; }
          .muted { color: #64748b; }
          .warning { color: #92400e; background: #fffbeb; padding: 10px; }
          .status { font-weight: bold; }
          .footer-note {
            margin-top: 28px;
            padding-top: 10px;
            border-top: 1px solid #cbd5e1;
            color: #64748b;
            font-size: 8pt;
          }
          @media print {
            body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
            h2 { break-after: avoid; }
            tr, .record { break-inside: avoid; }
            thead { display: table-header-group; }
          }
        </style>
      </head>
      <body>
        <header class="cover">
          <div class="eyebrow">Functional Safety Documentation</div>
          <h1>HARA Project Report</h1>
          <div class="subtitle">Hazard Analysis and Risk Assessment</div>
          <div class="meta">
            Workflow ID: HARA-001<br>
            Generated: ${escapeHtml(new Date().toLocaleString())}<br>
            Review Status: ${escapeHtml(decision)}
          </div>
        </header>

        ${section('1. System / Item Definition', itemContext)}
        ${section('2. HARA Scenario', scenario)}
        ${section('3. ASIL Assessment', asilResult)}
        ${section('4. Safety Goal', safetyGoal)}

        <section>
          <h2>5. Functional Safety Requirements</h2>
          ${renderRequirements(fsrResults || [], 'FSR')}
        </section>

        <section>
          <h2>6. Technical Safety Requirements</h2>
          ${renderRequirements(tsrResults || [], 'TSR')}
        </section>

        <section>
          <h2>7. Verification Evidence and Traceability</h2>
          ${evidenceHtml}
        </section>

        ${section('8. Engineering Review', {
          'Review Decision': decision,
          'Reviewer Name': reviewerName,
          'Review Comment': comment,
          'Latest Saved Review': latestReview,
          'Review Note': reviewNote,
        })}

        ${section('9. Audit History', (auditHistory || []).map((record) => ({
          ...record,
          'HARA ID': record['HARA ID'] || (record as any).hara_id || 'HARA-001',
          'Current Workflow ASIL': asilValue || 'Not available',
          'Current Workflow Safety Goal ID': safetyGoalId || 'Not available',
          'Current Workflow FSR ID': fsrId || 'Not available',
          'Current Workflow TSR IDs': tsrIds.length ? tsrIds.join(', ') : 'Not available',
        })))}

        <div class="footer-note">
          This report reflects the workflow information available when generated.
          Confirm requirements, verification results and traceability before using
          this document as formal functional safety evidence.
        </div>
      </body>
      </html>
    `;

    reportWindow.document.open();
    reportWindow.document.write(reportHtml);
    reportWindow.document.close();
    reportWindow.focus();

    reportWindow.onload = () => {
      reportWindow.print();
    };
  };
  const statusClass =
    decision === 'APPROVED'
      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
      : decision === 'CHANGES REQUESTED'
        ? 'bg-amber-50 text-amber-700 border-amber-200'
        : 'bg-blue-50 text-blue-700 border-blue-200';

  return (
    <div className="h-full overflow-y-auto bg-slate-100">
      <div className="mx-auto max-w-[1500px] px-6 py-6">
        <div className="mb-6 flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-slate-900">Review & Audit</h2>
            <p className="mt-1 text-sm text-slate-500">
              Final engineering review, decision recording and audit history.
            </p>
          </div>

          {decision !== 'PENDING REVIEW' && (
              <div className={`rounded-full border px-4 py-2 text-sm font-semibold ${statusClass}`}>
                {decision}
              </div>
            )}
        </div>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-3">
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-50 text-blue-700">
                <ClipboardCheck className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Engineering Review</h3>
                <p className="text-xs text-slate-500">HARA Workflow Â· HARA-001</p>
              </div>
            </div>

            <div className="mb-5 grid grid-cols-1 gap-4 md:grid-cols-3">
              <div className="rounded-lg bg-slate-50 p-4">
                <div className="text-xs font-medium text-slate-500">System / Item</div>
                <div className="mt-1 text-sm font-semibold text-slate-900">
                  {systemItem}
                </div>
              </div>

              <div className="rounded-lg bg-slate-50 p-4">
                <div className="text-xs font-medium text-slate-500">ASIL</div>
                <div className="mt-1 text-sm font-semibold text-slate-900">
                  {asilValue || 'Not calculated'}
                </div>
              </div>

              <div className="rounded-lg bg-slate-50 p-4">
                <div className="text-xs font-medium text-slate-500">HARA Scenario</div>
                <div className="mt-1 text-sm font-semibold text-slate-900">
                  {scenario ? `Scenario ${scenario.number}` : 'Not selected'}
                </div>
              </div>
            </div>

            <div className="mb-5 rounded-lg border border-blue-100 bg-blue-50 p-4">
              <div className="text-xs font-semibold uppercase tracking-wide text-blue-700">
                Review Note
              </div>
              <p className="mt-2 text-sm leading-6 text-slate-700">
                {reviewNote}
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">
                  Review Decision
                </span>
                <select
                  value={decision}
                  onChange={(event) => setDecision(event.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                >
                  <option value="PENDING REVIEW">PENDING REVIEW</option>
                  <option value="APPROVED">APPROVED</option>
                  <option value="CHANGES REQUESTED">CHANGES REQUESTED</option>
                </select>
              </label>

              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-slate-700">
                  Reviewer Name
                </span>
                <input
                  value={reviewerName}
                  onChange={(event) => setReviewerName(event.target.value)}
                  placeholder="Enter authorized reviewer name"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none focus:border-blue-500"
                />
              </label>
            </div>

            <label className="mt-4 block">
              <span className="mb-2 block text-sm font-semibold text-slate-700">
                Review Comment
              </span>
              <textarea
                value={comment}
                onChange={(event) => setComment(event.target.value)}
                rows={5}
                placeholder="Enter engineering review comments..."
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm outline-none focus:border-blue-500"
              />
            </label>

            <div className="mt-5 flex items-center gap-3">
              <button
                type="button"
                onClick={saveDecision}
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <UserCheck className="h-4 w-4" />
                {saving ? 'Saving...' : 'Save Review Decision'}
              </button>

              <button
                type="button"
                onClick={loadStatus}
                className="rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
              >
                Refresh
              </button>

                <button
                  type="button"
                  onClick={clearReviewAudit}
                  disabled={saving}
                  className="rounded-lg border border-red-300 bg-white px-5 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  Clear Review & Audit
                </button>
            </div>

            {message && (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700">
                {message}
              </div>
            )}
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-5 flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-100 text-slate-700">
                <History className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900">Audit History</h3>
                <p className="text-xs text-slate-500">Recorded workflow events</p>
              </div>
            </div>

            {auditHistory.length === 0 ? (
              <div className="rounded-lg border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">
                No audit events recorded yet.
              </div>
            ) : (
              <div className="space-y-3">
                {auditHistory.map((item, index) => (
                  <div key={`${item.timestamp_utc}-${index}`} className="rounded-lg border border-slate-200 p-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold text-slate-900">
                        {item.event || 'Audit Event'}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {item.timestamp_utc || ''}
                      </span>
                    </div>
                    <p className="mt-2 text-xs leading-5 text-slate-600">
                      {item.details || ''}
                    </p>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-5 rounded-lg border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-amber-800">
                <ShieldCheck className="h-4 w-4" />
                Audit Notice
              </div>
              <p className="mt-2 text-xs leading-5 text-amber-800">
                {auditNote}
              </p>
            </div>

            {latestReview && (
              <div className="mt-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
                <div className="text-xs font-semibold text-slate-500">Latest Review</div>
                <div className="mt-1 text-sm font-bold text-slate-900">
                  {latestReview.decision}
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  {latestReview.reviewer_name || 'Reviewer not specified'}
                </div>
              </div>
            )}
          </div>
        </div>          <div className="mt-6 flex items-center justify-between border-t border-slate-200 pt-5">
            <button
              type="button"
              onClick={onPrevious}
              className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            >
              Previous
            </button>

                        <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={downloadProjectReport}
                className="inline-flex items-center gap-2 rounded-lg border border-emerald-300 bg-white px-5 py-2.5 text-sm font-semibold text-emerald-700 hover:bg-emerald-50"
              >
                <Download className="h-4 w-4" />
                Download Project Report (PDF)
              </button>
<button
                type="button"
                onClick={onNewWorkflow}
                className="inline-flex items-center gap-2 rounded-lg border border-blue-300 bg-white px-5 py-2.5 text-sm font-semibold text-blue-700 hover:bg-blue-50"
              >
                New Workflow
              </button>

              <button
                type="button"
                onClick={completeWorkflow}
                disabled={saving}
                className="inline-flex items-center gap-2 rounded-lg bg-blue-700 px-6 py-2.5 text-sm font-semibold text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Complete Workflow
              </button>
            </div>
          </div>
      </div>
    </div>
  );
}
















