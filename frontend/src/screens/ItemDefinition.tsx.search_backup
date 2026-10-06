import { useRef, useState } from 'react';
import type {
  DocumentData,
  ItemContext,
} from '@/App';

import {
  UploadCloud,
  FileText,
  CheckCircle2,
  X,
  Loader2,
} from 'lucide-react';

import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from '@/components/ui/Card';

interface ItemDefinitionProps {
  initialDocumentData?: DocumentData | null;
  initialItemContext?: ItemContext;
  onContinue?: (
    document: DocumentData,
    context: ItemContext
  ) => void;
}

const API_BASE_URL =
  'http://127.0.0.1:8000';

const EMPTY_CONTEXT: ItemContext = {
  systemItem: '',
  intendedFunction: '',
  operationalScenario: '',
  operatingConditions: '',
};

export default function ItemDefinition({
  initialDocumentData = null,
  initialItemContext = EMPTY_CONTEXT,
  onContinue,
}: ItemDefinitionProps) {

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const [files, setFiles] =
    useState<File[]>([]);

  const [dragActive, setDragActive] =
    useState(false);

  const [systemItem, setSystemItem] =
    useState(
      initialItemContext.systemItem
    );

  const [intendedFunction, setIntendedFunction] =
    useState(
      initialItemContext.intendedFunction
    );

  const [operationalScenario, setOperationalScenario] =
    useState(
      initialItemContext.operationalScenario
    );

  const [operatingConditions, setOperatingConditions] =
    useState(
      initialItemContext.operatingConditions
    );

  const [processedDocument, setProcessedDocument] =
    useState<DocumentData | null>(
      initialDocumentData
    );

  const [uploading, setUploading] =
    useState(false);

  const [uploadMessage, setUploadMessage] =
    useState(
      initialDocumentData
        ? `Previously processed: ${initialDocumentData.documentName}`
        : ''
    );

  const [uploadError, setUploadError] =
    useState('');

  const addFiles = (
    selectedFiles: FileList | File[]
  ) => {

    const validFiles =
      Array.from(selectedFiles).filter(
        (file) =>
          file.name
            .toLowerCase()
            .endsWith('.pdf')
      );

    setFiles((previous) => {

      const existingNames =
        new Set(
          previous.map(
            (file) => file.name
          )
        );

      return [
        ...previous,
        ...validFiles.filter(
          (file) =>
            !existingNames.has(
              file.name
            )
        ),
      ];
    });

    setProcessedDocument(null);
    setUploadError('');
    setUploadMessage('');
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {

    if (event.target.files) {
      addFiles(
        event.target.files
      );
    }
  };

  const handleDrop = (
    event: React.DragEvent<HTMLDivElement>
  ) => {

    event.preventDefault();

    setDragActive(false);

    if (event.dataTransfer.files) {
      addFiles(
        event.dataTransfer.files
      );
    }
  };

  const removeFile = (
    fileName: string
  ) => {

    setFiles((previous) =>
      previous.filter(
        (file) =>
          file.name !== fileName
      )
    );

    setUploadMessage('');
    setUploadError('');
  };

  const handleContinue = async () => {

    if (!systemItem.trim()) {
      alert(
        'Please enter the System / Item.'
      );
      return;
    }

    if (!intendedFunction.trim()) {
      alert(
        'Please enter the Intended Function.'
      );
      return;
    }

    const context: ItemContext = {
      systemItem:
        systemItem.trim(),

      intendedFunction:
        intendedFunction.trim(),

      operationalScenario:
        operationalScenario.trim(),

      operatingConditions:
        operatingConditions.trim(),
    };

    /*
     * IMPORTANT:
     *
     * If user comes back from Step 2/3,
     * use the already processed document.
     * Do NOT force another PDF upload.
     */
    if (
      files.length === 0 &&
      processedDocument
    ) {

      onContinue?.(
        processedDocument,
        context
      );

      return;
    }

    if (files.length === 0) {

      alert(
        'Please upload an engineering PDF.'
      );

      return;
    }

    const pdfFile = files[0];

    setUploading(true);
    setUploadMessage('');
    setUploadError('');

    try {

      const formData =
        new FormData();

      formData.append(
        'file',
        pdfFile
      );

      const response =
        await fetch(
          `${API_BASE_URL}/api/documents/upload`,
          {
            method: 'POST',
            body: formData,
          }
        );

      const data =
        await response.json();

      if (!response.ok) {

        throw new Error(
          data.detail ||
          'Document upload failed.'
        );
      }

      const documentData: DocumentData = {
        documentId:
          data.document_id,

        documentName:
          data.document_name,

        pdfHash:
          data.pdf_hash,

        pages:
          data.pages,

        chunks:
          data.chunks,
      };

      setProcessedDocument(
        documentData
      );

      setUploadMessage(
        `Document processed successfully — ${data.pages} pages, ${data.chunks} chunks`
      );

      onContinue?.(
        documentData,
        context
      );

    } catch (error) {

      const message =
        error instanceof Error
          ? error.message
          : 'Unable to connect to HARA backend.';

      setUploadError(
        message
      );

    } finally {

      setUploading(false);
    }
  };

  return (
    <div className="p-5 space-y-5">

      {/* Page Header */}
      <div className="flex items-center justify-between">

        <div>

          <div className="text-[11px] font-semibold text-tata-600 uppercase tracking-wider">
            Step 1
          </div>

          <h2 className="text-xl font-bold text-slate-800">
            Item Definition
          </h2>

        </div>

        <div className="text-[11px] text-sval-muted">
          ISO 26262 Part 3 — Clause 5
        </div>

      </div>


      {/* Engineering Document */}
      <Card>

        <CardHeader>
          <CardTitle>
            Engineering Document Upload
          </CardTitle>
        </CardHeader>

        <CardContent>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            className="hidden"
            onChange={
              handleFileChange
            }
          />

          <div
            onClick={() =>
              fileInputRef.current?.click()
            }
            onDragOver={(event) => {
              event.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={() =>
              setDragActive(false)
            }
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
              dragActive
                ? 'border-tata-500 bg-blue-50'
                : 'border-slate-300 hover:border-tata-400 hover:bg-slate-50'
            }`}
          >

            <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />

            <p className="text-sm text-slate-600 font-medium">
              Drag & drop engineering PDF here, or click to browse
            </p>

            <p className="text-[11px] text-sval-muted mt-1">
              Supports PDF — engineering specifications,
              FMEA, architecture documents
            </p>

          </div>


          {/* Documents */}
          <div className="mt-4 space-y-2">

            <div className="text-[11px] font-semibold uppercase tracking-wider text-sval-muted">
              Uploaded Documents
            </div>

            {files.length === 0 &&
            !processedDocument ? (

              <div className="flex items-center gap-3 px-3 py-2.5 bg-slate-50 border border-slate-200 rounded text-sm">

                <FileText className="w-4 h-4 text-slate-400 shrink-0" />

                <span className="text-slate-500 font-medium flex-1">
                  No documents uploaded yet
                </span>

              </div>

            ) : (

              <>

                {processedDocument &&
                files.length === 0 && (

                  <div className="flex items-center gap-3 px-3 py-2.5 bg-green-50 border border-green-200 rounded text-sm">

                    <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0" />

                    <span className="text-green-700 font-medium flex-1 truncate">
                      {processedDocument.documentName}
                    </span>

                    <span className="text-[10px] text-green-600">
                      {processedDocument.pages} pages
                    </span>

                  </div>
                )}

                {files.map((file) => (

                  <div
                    key={file.name}
                    className="flex items-center gap-3 px-3 py-2.5 bg-slate-50 border border-slate-200 rounded text-sm"
                  >

                    <FileText className="w-4 h-4 text-tata-600 shrink-0" />

                    <span className="text-slate-700 font-medium flex-1 truncate">
                      {file.name}
                    </span>

                    <span className="text-[10px] text-slate-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>

                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        removeFile(file.name);
                      }}
                      className="p-1 rounded hover:bg-slate-200"
                      title="Remove file"
                    >
                      <X className="w-4 h-4 text-slate-500" />
                    </button>

                  </div>

                ))}

              </>

            )}

          </div>


          {/* Status */}
          {uploadMessage && (

            <div className="mt-3 px-3 py-2.5 bg-green-50 border border-green-200 rounded text-[12px] text-green-700">
              {uploadMessage}
            </div>

          )}

          {uploadError && (

            <div className="mt-3 px-3 py-2.5 bg-red-50 border border-red-200 rounded text-[12px] text-red-700">
              {uploadError}
            </div>

          )}

        </CardContent>

      </Card>


      {/* System / Item Context */}
      <Card>

        <CardHeader>
          <CardTitle>
            System / Item Context
          </CardTitle>
        </CardHeader>

        <CardContent>

          <div className="grid grid-cols-2 gap-x-5 gap-y-4">

            <Field
              label="System / Item"
              placeholder="e.g. Electronic Braking System (EBS)"
              value={systemItem}
              onChange={
                setSystemItem
              }
            />

            <Field
              label="Intended Function"
              placeholder="e.g. Decelerate vehicle on driver demand"
              value={intendedFunction}
              onChange={
                setIntendedFunction
              }
            />

            <Field
              label="Operational Scenario"
              placeholder="e.g. Normal braking at varying speeds and road conditions"
              textarea
              value={operationalScenario}
              onChange={
                setOperationalScenario
              }
            />

            <Field
              label="Operating Conditions"
              placeholder="e.g. -40°C to +85°C, all road surfaces, dry/wet/snow"
              textarea
              value={operatingConditions}
              onChange={
                setOperatingConditions
              }
            />

          </div>

        </CardContent>

      </Card>


      {/* Continue */}
      <div className="flex justify-end pt-1">

        <button
          type="button"
          onClick={
            handleContinue
          }
          disabled={uploading}
          className="px-5 py-2.5 bg-tata-700 hover:bg-tata-800 disabled:bg-slate-400 text-white text-sm font-semibold rounded transition-colors shadow-sm flex items-center gap-2"
        >

          {uploading ? (

            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Processing Document...
            </>

          ) : (

            <>
              Continue to HARA Analysis
              <CheckCircle2 className="w-4 h-4" />
            </>

          )}

        </button>

      </div>

    </div>
  );
}


function Field({
  label,
  placeholder,
  value,
  onChange,
  textarea,
}: {
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  textarea?: boolean;
}) {

  return (

    <div>

      <label className="block text-[11px] font-semibold text-slate-600 mb-1.5">
        {label}
      </label>

      {textarea ? (

        <textarea
          value={value}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
          placeholder={placeholder}
          rows={3}
          className="w-full px-3 py-2 text-[13px] border border-slate-300 rounded text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-tata-300 focus:border-tata-400 resize-none"
        />

      ) : (

        <input
          type="text"
          value={value}
          onChange={(event) =>
            onChange(
              event.target.value
            )
          }
          placeholder={placeholder}
          className="w-full px-3 py-2 text-[13px] border border-slate-300 rounded text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-tata-300 focus:border-tata-400"
        />

      )}

    </div>
  );
}