import { useState } from 'react';
import { createProfessional, extractResume } from '../api/professionals';

const SOURCE_OPTIONS = [
  { value: 'direct', label: 'Direct' },
  { value: 'partner', label: 'Partner' },
  { value: 'internal', label: 'Internal' },
];

const initialFormState = {
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  source: 'direct',
  company_name: '',
  job_title: '',
};

export default function ProfessionalForm({ onSuccess }) {
  const [formData, setFormData] = useState(initialFormState);
  const [resumeFile, setResumeFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  
  // Resume extraction settings
  const [extractionMethod, setExtractionMethod] = useState('python');
  const [openaiKey, setOpenaiKey] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setError(null);
    setSuccess(false);
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file && file.type === 'application/pdf') {
      setResumeFile(file);
      setError(null);
    } else if (file) {
      setError('Please select a PDF file');
      setResumeFile(null);
    }
  };

  const handleExtractResume = async () => {
    if (!resumeFile) {
      setError('Please select a resume file first');
      return;
    }

    if (extractionMethod === 'llm' && !openaiKey) {
      setError('Please enter your OpenAI API key for LLM extraction');
      return;
    }

    setExtracting(true);
    setError(null);

    try {
      const extracted = await extractResume(
        resumeFile,
        extractionMethod,
        extractionMethod === 'llm' ? openaiKey : null
      );
      
      // Fill form with extracted data
      setFormData((prev) => ({
        ...prev,
        first_name: extracted.first_name || prev.first_name,
        last_name: extracted.last_name || prev.last_name,
        email: extracted.email || prev.email,
        phone: extracted.phone || prev.phone,
        company_name: extracted.company_name || prev.company_name,
        job_title: extracted.job_title || prev.job_title,
      }));
      
      setSuccess(false); // Clear success to show extraction worked
    } catch (err) {
      setError(err.message);
    } finally {
      setExtracting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const data = {
        first_name: formData.first_name.trim(),
        last_name: formData.last_name.trim(),
        email: formData.email.trim(),
        source: formData.source,
      };
      
      if (formData.phone.trim()) {
        data.phone = formData.phone.trim();
      }
      if (formData.company_name.trim()) {
        data.company_name = formData.company_name.trim();
      }
      if (formData.job_title.trim()) {
        data.job_title = formData.job_title.trim();
      }

      await createProfessional(data, resumeFile);
      setSuccess(true);
      setFormData(initialFormState);
      setResumeFile(null);
      // Reset file input
      const fileInput = document.getElementById('resume');
      if (fileInput) fileInput.value = '';
      onSuccess?.();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <h2 className="text-xl font-semibold text-gray-800 mb-4">
        Add Professional
      </h2>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-md text-sm">
          {error}
        </div>
      )}

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-md text-sm">
          Professional added successfully!
        </div>
      )}

      {/* Resume Upload Section */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-3">
          Upload Resume (Optional - Auto-fill form)
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-3">
          <div>
            <label htmlFor="resume" className="block text-sm text-gray-600 mb-1">
              PDF Resume
            </label>
            <input
              type="file"
              id="resume"
              accept=".pdf"
              onChange={handleResumeChange}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </div>
          
          <div>
            <label htmlFor="extractionMethod" className="block text-sm text-gray-600 mb-1">
              Extraction Method
            </label>
            <select
              id="extractionMethod"
              value={extractionMethod}
              onChange={(e) => setExtractionMethod(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="python">Basic (Python - No API key needed)</option>
              <option value="llm">LLM (OpenAI - More accurate)</option>
            </select>
          </div>
        </div>

        {extractionMethod === 'llm' && (
          <div className="mb-3">
            <label htmlFor="openaiKey" className="block text-sm text-gray-600 mb-1">
              OpenAI API Key
            </label>
            <input
              type="password"
              id="openaiKey"
              value={openaiKey}
              onChange={(e) => setOpenaiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        <button
          type="button"
          onClick={handleExtractResume}
          disabled={!resumeFile || extracting}
          className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {extracting ? 'Extracting...' : 'Extract & Fill Form'}
        </button>
        
        {resumeFile && (
          <span className="ml-3 text-sm text-gray-500">
            Selected: {resumeFile.name}
          </span>
        )}
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* First Name - Required */}
          <div>
            <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
              First Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="first_name"
              name="first_name"
              value={formData.first_name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="John"
            />
          </div>

          {/* Last Name - Required */}
          <div>
            <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
              Last Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              id="last_name"
              name="last_name"
              value={formData.last_name}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Doe"
            />
          </div>

          {/* Email - Required */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="john@example.com"
            />
          </div>

          {/* Phone - Optional */}
          <div>
            <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
              Phone
            </label>
            <input
              type="tel"
              id="phone"
              name="phone"
              value={formData.phone}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="+14155551234"
            />
            <p className="mt-1 text-xs text-gray-500">E.164 format (e.g., +14155551234)</p>
          </div>

          {/* Source - Required */}
          <div>
            <label htmlFor="source" className="block text-sm font-medium text-gray-700 mb-1">
              Source <span className="text-red-500">*</span>
            </label>
            <select
              id="source"
              name="source"
              value={formData.source}
              onChange={handleChange}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              {SOURCE_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Company Name - Optional */}
          <div>
            <label htmlFor="company_name" className="block text-sm font-medium text-gray-700 mb-1">
              Company Name
            </label>
            <input
              type="text"
              id="company_name"
              name="company_name"
              value={formData.company_name}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Acme Inc"
            />
          </div>

          {/* Job Title - Optional */}
          <div>
            <label htmlFor="job_title" className="block text-sm font-medium text-gray-700 mb-1">
              Job Title
            </label>
            <input
              type="text"
              id="job_title"
              name="job_title"
              value={formData.job_title}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Software Engineer"
            />
          </div>
        </div>

        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full md:w-auto px-6 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? 'Adding...' : 'Add Professional'}
          </button>
        </div>
      </form>
    </div>
  );
}
