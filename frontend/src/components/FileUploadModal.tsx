import React, { useState, useRef, useEffect } from 'react';
import {
  Upload,
  X,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Loader,
  HardDrive,
  FileJson,
  FileText,
  Sheet,
  Code
} from 'lucide-react';

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadComplete: (data: any) => void;
}

interface ConversionStatus {
  status: string;
  current_file?: string;
  progress: number;
  message: string;
  total_rows: number;
  flagged_transactions: number;
}

export const FileUploadModal: React.FC<FileUploadModalProps> = ({
  isOpen,
  onClose,
  onUploadComplete,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [conversionStatus, setConversionStatus] = useState<ConversionStatus>({
    status: 'ready',
    progress: 0,
    message: 'Ready',
    total_rows: 0,
    flagged_transactions: 0,
  });
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const statusPollInterval = useRef<ReturnType<typeof setInterval> | null>(null);

  const ALLOWED_FORMATS = ['.csv', '.json', '.jsonl', '.xlsx', '.xls', '.xml'];

  const getFileIcon = (filename: string) => {
    const ext = filename.toLowerCase().split('.').pop();
    switch (ext) {
      case 'json':
      case 'jsonl':
        return <FileJson className="w-6 h-6 text-blue-400" />;
      case 'csv':
        return <Sheet className="w-6 h-6 text-green-400" />;
      case 'xlsx':
      case 'xls':
        return <Sheet className="w-6 h-6 text-emerald-400" />;
      case 'xml':
        return <Code className="w-6 h-6 text-purple-400" />;
      default:
        return <FileText className="w-6 h-6 text-slate-400" />;
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();

      if (ALLOWED_FORMATS.includes(ext)) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError(`Invalid format. Allowed: ${ALLOWED_FORMATS.join(', ')}`);
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      const file = files[0];
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();

      if (ALLOWED_FORMATS.includes(ext)) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError(`Invalid format. Allowed: ${ALLOWED_FORMATS.join(', ')}`);
      }
    }
  };

  const pollConversionStatus = async () => {
    try {
      const response = await fetch('/api/ingest/conversion-status');
      const data = await response.json();
      setConversionStatus(data);

      if (data.status === 'ready' && conversionStatus.status !== 'ready') {
        // Conversion complete
        if (statusPollInterval.current) {
          clearInterval(statusPollInterval.current);
          statusPollInterval.current = null;
        }
        onUploadComplete(data.last_result);
      }
    } catch (e) {
      console.error('Failed to poll conversion status:', e);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('dataset_type', 'transaction');
    formData.append('auto_infer', 'true');

    try {
      const response = await fetch('/api/ingest/upload-and-convert', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const result = await response.json();

      // Start polling for status updates
      setConversionStatus({
        status: 'converting',
        current_file: selectedFile.name,
        progress: 50,
        message: 'Converting file format...',
        total_rows: 0,
        flagged_transactions: 0,
      });

      statusPollInterval.current = setInterval(pollConversionStatus, 1000);
      await pollConversionStatus();

    } catch (e) {
      setError(e instanceof Error ? e.message : 'Upload failed');
      setIsUploading(false);
    }
  };

  useEffect(() => {
    return () => {
      if (statusPollInterval.current) {
        clearInterval(statusPollInterval.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  const statusColors = {
    ready: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/40',
    converting: 'bg-amber-500/20 text-amber-400 border-amber-500/40',
    error: 'bg-rose-500/20 text-rose-400 border-rose-500/40',
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#0f1419]/95 border border-slate-700/60 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-slate-700/40">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/20 border border-cyan-500/40 flex items-center justify-center">
              <Upload className="w-5 h-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-100 font-mono">Dataset Upload</h2>
              <p className="text-xs text-slate-400">Auto-convert & analyze transaction data</p>
            </div>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading}
            className="text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* File Selection Area */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${isDragging
                ? 'border-cyan-400 bg-cyan-500/10'
                : 'border-slate-600 bg-slate-900/20 hover:border-cyan-400/50'
              } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
            onClick={() => !isUploading && fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              onChange={handleFileSelect}
              accept={ALLOWED_FORMATS.join(',')}
              className="hidden"
              disabled={isUploading}
            />

            {selectedFile ? (
              <div className="space-y-3">
                <div className="flex justify-center">
                  {getFileIcon(selectedFile.name)}
                </div>
                <div>
                  <p className="font-mono font-bold text-slate-100 text-sm">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                {!isUploading && (
                  <p className="text-xs text-cyan-400 cursor-pointer hover:text-cyan-300">
                    Click to change file
                  </p>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-center">
                  <HardDrive className="w-12 h-12 text-slate-500" />
                </div>
                <div>
                  <p className="font-bold text-slate-100 text-sm">
                    Drag & drop your dataset here
                  </p>
                  <p className="text-xs text-slate-400 mt-1">
                    or click to browse
                  </p>
                </div>
              </div>
            )}

            <div className="mt-4 pt-4 border-t border-slate-600/50">
              <p className="text-xs text-slate-400 font-mono">
                Supported: JSON, CSV, XLSX, XLS, XML
              </p>
            </div>
          </div>

          {/* Conversion Status */}
          {isUploading && (
            <div className="space-y-4">
              {/* Status Pill */}
              <div className={`flex items-center space-x-3 px-4 py-3 rounded-lg border ${statusColors[conversionStatus.status as keyof typeof statusColors]}`}>
                {conversionStatus.status === 'converting' ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : conversionStatus.status === 'error' ? (
                  <AlertCircle className="w-4 h-4" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                <span className="text-sm font-mono font-bold">
                  {conversionStatus.message}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400 font-mono">Progress</span>
                  <span className="text-xs font-bold text-cyan-400 font-mono">
                    {conversionStatus.progress}%
                  </span>
                </div>
                <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 transition-all duration-300 rounded-full"
                    style={{ width: `${conversionStatus.progress}%` }}
                  />
                </div>
              </div>

              {/* Metrics */}
              {conversionStatus.total_rows > 0 && (
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-900/50 border border-slate-700/40 rounded-lg p-3">
                    <p className="text-xs text-slate-400 mb-1">Total Rows</p>
                    <p className="text-lg font-bold text-cyan-400 font-mono">
                      {conversionStatus.total_rows.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-slate-900/50 border border-slate-700/40 rounded-lg p-3">
                    <p className="text-xs text-slate-400 mb-1">Flagged</p>
                    <p className="text-lg font-bold text-rose-400 font-mono">
                      {conversionStatus.flagged_transactions.toLocaleString()}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 rounded-lg p-4 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-rose-400">Error</p>
                <p className="text-xs text-rose-300 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Format Info */}
          <div className="bg-slate-900/30 border border-slate-700/40 rounded-lg p-4">
            <p className="text-xs text-slate-400 font-mono mb-3">
              ℹ Supported Format Details:
            </p>
            <ul className="text-xs text-slate-400 space-y-1.5 font-mono">
              <li>• <span className="text-cyan-400">JSON/JSONL:</span> Nested structures auto-flattened</li>
              <li>• <span className="text-green-400">CSV:</span> Flexible delimiter detection</li>
              <li>• <span className="text-emerald-400">Excel:</span> XLSX & XLS multi-sheet support</li>
              <li>• <span className="text-purple-400">XML:</span> Recursive element extraction</li>
            </ul>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700/40 p-6 flex items-center justify-between bg-slate-900/30">
          <p className="text-xs text-slate-500 font-mono">
            {selectedFile ? `Ready to convert ${selectedFile.name}` : 'Select a file to proceed'}
          </p>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 text-sm font-mono font-bold text-slate-400 hover:text-slate-100 border border-slate-600 rounded-lg hover:border-slate-500 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={handleUpload}
              disabled={!selectedFile || isUploading}
              className="px-6 py-2 text-sm font-mono font-bold text-black bg-gradient-to-r from-cyan-400 to-blue-400 rounded-lg hover:from-cyan-300 hover:to-blue-300 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              <span>{isUploading ? 'Converting...' : 'Convert & Analyze'}</span>
              {!isUploading && <ChevronRight className="w-4 h-4" />}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
