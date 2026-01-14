import { useState } from 'react';
import { bulkCreateProfessionals, parseCSV } from '../api/professionals';

const SOURCE_OPTIONS = ['direct', 'partner', 'internal'];

export default function BulkUpload({ onSuccess }) {
  const [csvFile, setCsvFile] = useState(null);
  const [parsedData, setParsedData] = useState([]);
  const [parseError, setParseError] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCsvFile(file);
      setParsedData([]);
      setParseError(null);
      setUploadResult(null);

      // Read and parse CSV
      const reader = new FileReader();
      reader.onload = (event) => {
        try {
          const text = event.target.result;
          const data = parseCSV(text);
          setParsedData(data);
        } catch (err) {
          setParseError(err.message);
        }
      };
      reader.onerror = () => {
        setParseError('Failed to read file');
      };
      reader.readAsText(file);
    }
  };

  const handleUpload = async () => {
    if (parsedData.length === 0) {
      setParseError('No valid data to upload');
      return;
    }

    setUploading(true);
    setUploadResult(null);

    try {
      const result = await bulkCreateProfessionals(parsedData);
      setUploadResult(result);
      
      // If all succeeded, reset form
      if (result.summary.failed === 0) {
        setCsvFile(null);
        setParsedData([]);
        const fileInput = document.getElementById('csvFile');
        if (fileInput) fileInput.value = '';
        onSuccess?.();
      }
    } catch (err) {
      setParseError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const validateRow = (row) => {
    const errors = [];
    if (!row.first_name) errors.push('Missing first name');
    if (!row.last_name) errors.push('Missing last name');
    if (!row.email) errors.push('Missing email');
    if (!row.source) errors.push('Missing source');
    if (row.source && !SOURCE_OPTIONS.includes(row.source)) {
      errors.push(`Invalid source: ${row.source}`);
    }
    return errors;
  };

  const downloadTemplate = () => {
    const template = 'first_name,last_name,email,phone,source,company_name,job_title\nJohn,Doe,john@example.com,+14155551234,direct,Acme Inc,Engineer\n';
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'professionals_template.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full text-left"
      >
        <h2 className="text-xl font-semibold text-gray-800">
          Bulk Upload
        </h2>
        <svg
          className={`w-5 h-5 text-gray-500 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-4">
            Upload a CSV file to add multiple professionals at once. The CSV should have headers:
            <code className="ml-1 px-1 py-0.5 bg-gray-100 rounded text-xs">
              first_name, last_name, email, phone, source, company_name, job_title
            </code>
          </p>

          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={downloadTemplate}
              className="text-sm text-blue-600 hover:text-blue-800 underline"
            >
              Download CSV Template
            </button>
          </div>

          <div className="mb-4">
            <input
              type="file"
              id="csvFile"
              accept=".csv"
              onChange={handleFileChange}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>

          {parseError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
              {parseError}
            </div>
          )}

          {uploadResult && (
            <div className={`mb-4 p-3 rounded-md text-sm ${
              uploadResult.summary.failed === 0
                ? 'bg-green-50 border border-green-200 text-green-700'
                : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
            }`}>
              <p className="font-medium">Upload Complete:</p>
              <ul className="mt-1 list-disc list-inside">
                <li>Created: {uploadResult.summary.created}</li>
                <li>Updated: {uploadResult.summary.updated}</li>
                <li>Failed: {uploadResult.summary.failed}</li>
              </ul>
              {uploadResult.summary.failed > 0 && (
                <div className="mt-2">
                  <p className="font-medium">Errors:</p>
                  <ul className="mt-1 text-xs">
                    {uploadResult.results
                      .filter((r) => !r.success)
                      .map((r) => (
                        <li key={r.index} className="text-red-600">
                          Row {r.index + 1}: {JSON.stringify(r.error)}
                        </li>
                      ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {parsedData.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-medium text-gray-700 mb-2">
                Preview ({parsedData.length} rows)
              </h3>
              <div className="overflow-x-auto max-h-64 border border-gray-200 rounded-md">
                <table className="min-w-full divide-y divide-gray-200 text-xs">
                  <thead className="bg-gray-50 sticky top-0">
                    <tr>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">#</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">First Name</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Last Name</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Email</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Phone</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Source</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Company</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Job Title</th>
                      <th className="px-2 py-2 text-left font-medium text-gray-500">Status</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {parsedData.map((row, index) => {
                      const errors = validateRow(row);
                      return (
                        <tr key={index} className={errors.length > 0 ? 'bg-red-50' : ''}>
                          <td className="px-2 py-1.5 text-gray-500">{index + 1}</td>
                          <td className="px-2 py-1.5">{row.first_name || '-'}</td>
                          <td className="px-2 py-1.5">{row.last_name || '-'}</td>
                          <td className="px-2 py-1.5">{row.email || '-'}</td>
                          <td className="px-2 py-1.5">{row.phone || '-'}</td>
                          <td className="px-2 py-1.5">{row.source || '-'}</td>
                          <td className="px-2 py-1.5">{row.company_name || '-'}</td>
                          <td className="px-2 py-1.5">{row.job_title || '-'}</td>
                          <td className="px-2 py-1.5">
                            {errors.length === 0 ? (
                              <span className="text-green-600">Valid</span>
                            ) : (
                              <span className="text-red-600" title={errors.join(', ')}>
                                Invalid
                              </span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {parsedData.length > 0 && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="px-6 py-2 bg-green-600 text-white font-medium rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {uploading ? 'Uploading...' : `Upload ${parsedData.length} Professionals`}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
