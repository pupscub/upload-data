"""
PDF extraction services for resume parsing.
Supports two methods:
1. LLM (OpenAI) - Uses GPT to extract structured data
2. Python (pdfplumber) - Uses regex patterns to extract data
"""

import re
import json
import pdfplumber
from openai import OpenAI


def extract_with_llm(pdf_file, openai_api_key):
    """
    Extract professional data from PDF using OpenAI GPT.

    Args:
        pdf_file: File object or path to PDF
        openai_api_key: OpenAI API key

    Returns:
        dict with extracted fields: first_name, last_name, email, phone, company_name, job_title
    """
    # Extract text from PDF
    text = extract_text_from_pdf(pdf_file)

    if not text.strip():
        return {"error": "Could not extract text from PDF"}

    # Use OpenAI to extract structured data
    client = OpenAI(api_key=openai_api_key)

    prompt = f"""Extract the following information from this resume text. 
Return a JSON object with these fields:
- first_name: The person's first name
- last_name: The person's last name  
- email: Email address
- phone: Phone number (if found)
- company_name: Current or most recent company/employer
- job_title: Current or most recent job title

If a field cannot be found, use an empty string "".

Resume text:
{text[:4000]}

Return ONLY valid JSON, no other text."""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a resume parser. Extract information and return valid JSON only.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=500,
        )

        result_text = response.choices[0].message.content.strip()

        # Try to parse JSON from response
        # Handle case where response might have markdown code blocks
        if result_text.startswith("```"):
            result_text = re.sub(r"^```json?\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)

        result = json.loads(result_text)

        # Ensure all expected fields exist
        expected_fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "company_name",
            "job_title",
        ]
        for field in expected_fields:
            if field not in result:
                result[field] = ""

        return result

    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse LLM response: {str(e)}"}
    except Exception as e:
        return {"error": f"LLM extraction failed: {str(e)}"}


def extract_with_python(pdf_file):
    """
    Extract professional data from PDF using regex patterns.

    Args:
        pdf_file: File object or path to PDF

    Returns:
        dict with extracted fields: first_name, last_name, email, phone, company_name, job_title
    """
    text = extract_text_from_pdf(pdf_file)

    if not text.strip():
        return {"error": "Could not extract text from PDF"}

    result = {
        "first_name": "",
        "last_name": "",
        "email": "",
        "phone": "",
        "company_name": "",
        "job_title": "",
    }

    # Extract email
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    email_match = re.search(email_pattern, text)
    if email_match:
        result["email"] = email_match.group(0).lower()

    # Extract phone - various formats
    phone_patterns = [
        r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",  # US format
        r"\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}",  # International
    ]
    for pattern in phone_patterns:
        phone_match = re.search(pattern, text)
        if phone_match:
            # Clean phone number
            phone = re.sub(r"[^\d+]", "", phone_match.group(0))
            if len(phone) >= 10:
                result["phone"] = phone
                break

    # Try to extract name from first line (common resume format)
    lines = text.strip().split("\n")
    if lines:
        first_line = lines[0].strip()
        # Check if first line looks like a name (not an email, phone, or address)
        if first_line and not re.search(r"[@\d]", first_line) and len(first_line) < 50:
            name_parts = first_line.split()
            if len(name_parts) >= 2:
                result["first_name"] = name_parts[0]
                result["last_name"] = " ".join(name_parts[1:])
            elif len(name_parts) == 1:
                result["first_name"] = name_parts[0]

    # Try to extract job title (common patterns)
    job_patterns = [
        r"(?:^|\n)\s*([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Director|Analyst|Designer|Consultant|Specialist|Lead|Architect|Scientist|Administrator))",
        r"(?:Title|Position|Role)[\s:]+([^\n]+)",
    ]
    for pattern in job_patterns:
        job_match = re.search(pattern, text, re.MULTILINE)
        if job_match:
            result["job_title"] = job_match.group(1).strip()[:100]
            break

    # Try to extract company name
    company_patterns = [
        r"(?:at|@)\s+([A-Z][A-Za-z\s&.,]+(?:Inc|LLC|Ltd|Corp|Company|Co\.|Corporation)?)",
        r"(?:Company|Employer|Organization)[\s:]+([^\n]+)",
    ]
    for pattern in company_patterns:
        company_match = re.search(pattern, text)
        if company_match:
            result["company_name"] = company_match.group(1).strip()[:100]
            break

    return result


def extract_text_from_pdf(pdf_file):
    """
    Extract all text from a PDF file.

    Args:
        pdf_file: File object or path to PDF

    Returns:
        str: Extracted text
    """
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text_parts = []
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            return "\n".join(text_parts)
    except Exception as e:
        return ""
