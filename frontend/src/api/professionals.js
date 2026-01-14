// Use relative URL - Vite proxy handles forwarding to backend
const API_BASE_URL = '/api/professionals';

/**
 * Fetch all professionals with optional source filter and search.
 * @param {Object} options - Filter options
 * @param {string|null} options.source - Optional source filter (direct, partner, internal)
 * @param {string|null} options.search - Optional search query
 * @returns {Promise<Array>} List of professionals
 */
export async function fetchProfessionals({ source = null, search = null } = {}) {
  const params = new URLSearchParams();
  if (source) params.append('source', source);
  if (search) params.append('search', search);
  
  const queryString = params.toString();
  const url = queryString ? `${API_BASE_URL}/?${queryString}` : `${API_BASE_URL}/`;
  
  const response = await fetch(url);
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to fetch professionals');
  }
  
  return response.json();
}

/**
 * Create a new professional.
 * @param {Object} data - Professional data
 * @param {File|null} resume - Optional resume file
 * @returns {Promise<Object>} Created professional
 */
export async function createProfessional(data, resume = null) {
  let body;
  let headers = {};
  
  if (resume) {
    // Use FormData for file upload
    body = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        body.append(key, value);
      }
    });
    body.append('resume', resume);
    // Don't set Content-Type - browser will set it with boundary
  } else {
    // Use JSON for regular data
    body = JSON.stringify(data);
    headers['Content-Type'] = 'application/json';
  }
  
  const response = await fetch(`${API_BASE_URL}/`, {
    method: 'POST',
    headers,
    body,
  });
  
  const result = await response.json();
  
  if (!response.ok) {
    // Format validation errors for display
    const errors = formatErrors(result);
    throw new Error(errors);
  }
  
  return result;
}

/**
 * Bulk create/update professionals.
 * @param {Array} professionals - Array of professional data
 * @returns {Promise<Object>} Bulk operation result with summary
 */
export async function bulkCreateProfessionals(professionals) {
  const response = await fetch(`${API_BASE_URL}/bulk/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(professionals),
  });
  
  const result = await response.json();
  
  if (!response.ok && response.status !== 207) {
    throw new Error(result.error || 'Bulk operation failed');
  }
  
  return result;
}

/**
 * Extract data from a PDF resume.
 * @param {File} resumeFile - PDF file
 * @param {string} method - Extraction method: "llm" or "python"
 * @param {string|null} openaiKey - OpenAI API key (required for LLM method)
 * @returns {Promise<Object>} Extracted professional data
 */
export async function extractResume(resumeFile, method = 'python', openaiKey = null) {
  const formData = new FormData();
  formData.append('resume', resumeFile);
  formData.append('method', method);
  if (openaiKey) {
    formData.append('openai_key', openaiKey);
  }
  
  const response = await fetch(`${API_BASE_URL}/extract-resume/`, {
    method: 'POST',
    body: formData,
  });
  
  const result = await response.json();
  
  if (!response.ok) {
    throw new Error(result.error || 'Failed to extract resume data');
  }
  
  return result;
}

/**
 * Format API validation errors into a readable string.
 * @param {Object} errors - Error object from API
 * @returns {string} Formatted error message
 */
function formatErrors(errors) {
  if (typeof errors === 'string') {
    return errors;
  }
  
  const messages = [];
  for (const [field, fieldErrors] of Object.entries(errors)) {
    if (Array.isArray(fieldErrors)) {
      messages.push(`${field}: ${fieldErrors.join(', ')}`);
    } else if (typeof fieldErrors === 'string') {
      messages.push(`${field}: ${fieldErrors}`);
    }
  }
  
  return messages.join('; ') || 'An error occurred';
}

/**
 * Delete a single professional by ID.
 * @param {number} id - Professional ID
 * @returns {Promise<void>}
 */
export async function deleteProfessional(id) {
  const response = await fetch(`${API_BASE_URL}/${id}/`, {
    method: 'DELETE',
  });
  
  if (!response.ok && response.status !== 204) {
    const error = await response.json();
    throw new Error(error.error || 'Failed to delete professional');
  }
}

/**
 * Bulk delete professionals by IDs.
 * @param {Array<number>} ids - Array of professional IDs
 * @returns {Promise<Object>} Result with deleted count and not_found IDs
 */
export async function bulkDeleteProfessionals(ids) {
  const response = await fetch(`${API_BASE_URL}/bulk-delete/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ids }),
  });
  
  const result = await response.json();
  
  if (!response.ok) {
    throw new Error(result.error || 'Bulk delete failed');
  }
  
  return result;
}

/**
 * Get CSV export URL with optional filters.
 * @param {Object} options - Filter options
 * @param {string|null} options.source - Optional source filter
 * @param {string|null} options.search - Optional search query
 * @returns {string} URL for CSV download
 */
export function getExportCSVUrl({ source = null, search = null } = {}) {
  const params = new URLSearchParams();
  if (source) params.append('source', source);
  if (search) params.append('search', search);
  
  const queryString = params.toString();
  return queryString ? `${API_BASE_URL}/export-csv/?${queryString}` : `${API_BASE_URL}/export-csv/`;
}

/**
 * Parse CSV text into array of professional objects.
 * @param {string} csvText - CSV text content
 * @returns {Array} Array of professional objects
 */
export function parseCSV(csvText) {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) {
    throw new Error('CSV must have a header row and at least one data row');
  }
  
  const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
  const requiredHeaders = ['first_name', 'last_name', 'email', 'source'];
  const missingHeaders = requiredHeaders.filter(h => !headers.includes(h));
  
  if (missingHeaders.length > 0) {
    throw new Error(`Missing required columns: ${missingHeaders.join(', ')}`);
  }
  
  const professionals = [];
  for (let i = 1; i < lines.length; i++) {
    const values = parseCSVLine(lines[i]);
    if (values.length !== headers.length) {
      console.warn(`Row ${i + 1} has ${values.length} values but expected ${headers.length}`);
      continue;
    }
    
    const professional = {};
    headers.forEach((header, index) => {
      const value = values[index]?.trim() || '';
      if (value) {
        professional[header] = value;
      }
    });
    
    // Only add if has required fields
    if (professional.first_name && professional.last_name && professional.email && professional.source) {
      professionals.push(professional);
    }
  }
  
  return professionals;
}

/**
 * Parse a single CSV line, handling quoted values.
 * @param {string} line - CSV line
 * @returns {Array} Array of values
 */
function parseCSVLine(line) {
  const values = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      values.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  values.push(current);
  
  return values;
}
