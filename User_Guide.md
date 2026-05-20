# KB Document Conversion Tool — User Guide

**Version:** 1.0
**Last Updated:** March 2026

---

## What This Tool Does

The KB Document Conversion Tool automatically converts service documents (Word `.docx` and PDF `.pdf` files) into a standardised, structured format for use in the Internal Knowledge Base (KB).

Instead of manually reformatting each document, this tool uses AI to read the source document, extract all relevant information, and produce a clean, consistently structured output that follows the KB template — ready for review and upload.

### Business Value

| Without This Tool | With This Tool |
|---|---|
| Manual copy-paste and reformatting for every document | Automated conversion in under a minute per document |
| Inconsistent section naming and layout across documents | Consistent KB template structure every time |
| Easy to miss hyperlinks, pricing tables, or support contacts | Hyperlinks and tables are extracted and preserved |
| No visibility into conversion quality | Compliance score and validation report per document |

---

## Who Should Use This

This tool is intended for team members responsible for creating or maintaining KB knowledge articles, including:

- Business Analysts preparing knowledge base content
- Content owners submitting service documentation
- Team leads reviewing structured output before publication

---

## Prerequisites

Before using the tool, ensure the following are in place:

1. **Python installed** (version 3.9 or later)
2. **Tool dependencies installed** — run once in the project folder:
   ```
   pip install -r requirements.txt
   ```
3. **OpenAI API key configured** — a file named `.env` must exist in the project folder containing:
   ```
   OPENAI_API_KEY=your_key_here
   ```
   Contact your system administrator if you do not have an API key.

---

## How to Use — Web Interface

The recommended way to use the tool is through the web browser interface.

### Step 1: Start the Application

Open a terminal in the project folder and run:

```
python streamlit_app.py
```

Your browser will automatically open to `http://localhost:8501`. If it doesn't, open the URL manually.

### Step 2: Upload Your Documents

- Click **Browse files** or drag and drop your `.docx` or `.pdf` files into the upload area.
- You can upload multiple files at once for batch conversion.
- Maximum file size: **5 MB per file**.

### Step 3: Select Output Format

Choose how you want the converted documents saved:

| Option | Description | Recommended For |
|--------|-------------|-----------------|
| **DOCX** | Formatted Word document | Sharing, review, and publication |
| **Markdown** | Plain text with structured formatting | Direct upload to knowledge base systems |
| **Both** | Saves both formats simultaneously | When you need both versions |

> **Recommendation:** Select **DOCX** for most use cases. It produces a professionally styled Word document ready for review.

### Step 4: Convert

Click the **Convert Documents** button. A progress bar will show the current stage:

1. Extracting document content
2. Loading KB template
3. AI content structuring (this is the longest step — typically 15–30 seconds)
4. Validating and fixing content
5. Saving output file(s)

### Step 5: Download Results

Once conversion is complete, the results panel shows:

- A **compliance score** — how well the output matches the KB template structure
- **Content statistics** — word count, character count, tables found, hyperlinks found
- **API usage and cost** — tokens used and estimated cost
- **Download buttons** for each output file
- Any **validation warnings** to review

---

## Understanding the Output Structure

All converted documents follow the KB template with these sections:

| Section | What It Contains |
|---------|-----------------|
| **Document Information** | Title, document type, last updated date, version, provider |
| **Key Features** | Bullet-point summary of the most important aspects of the service |
| **Detailed Information** | In-depth content, broken into labelled subsections |
| **Pricing Information** | Pricing table with plan name, price, validity, data, and coverage |
| **Eligibility** | Who qualifies for the service |
| **How to Subscribe** | Step-by-step subscription process |
| **Terms and Conditions** | Key terms, limitations, and policies |
| **FAQ** | Common questions and answers extracted from the source |
| **Customer Support** | Contact details and support links |

> **Note:** The AI adapts this structure to the document type. For troubleshooting guides, "Pricing Information" may become "Troubleshooting Steps", and "How to Subscribe" may become "Resolution Process". Sections with no relevant content in the source are skipped rather than left blank.

### Output Example

Below is a sample of what a converted document looks like:

```
# 5G Home WiFi Device Bundle Campaign FAQs

## Document Information
- **Title**: 5G Home WiFi Device Bundle Campaign FAQs
- **Document Type**: Campaign FAQ
- **Last Updated**: 01/07/2025
- **Provider**: [Provider Name]

## Key Features
- Available for customers above the age of 18.
- Exclusive discount for existing postpaid customers above a monthly commitment threshold.
- Fair Usage Policy (FUP) of 1000GB; speed throttled to 512kbps after exceeding FUP.

## Pricing Information
| Plan/Package       | Price | Validity  | Data Allocation | Coverage |
|--------------------|-------|-----------|-----------------|----------|
| 5G Home WiFi Plan  | XX.XX | 24 months | 1000 GB         | National |

## Customer Support
- For support, visit [Provider Help Centre](https://example.com/support)
```

---

## Supported Document Types

The tool automatically detects the type of document and tailors its extraction accordingly.

| Category | Types Supported | Examples |
|----------|----------------|---------|
| **Mobile** | Product plans, troubleshooting guides | Postpaid/prepaid plan docs, SIM card issues |
| **Fibre** | Product plans, troubleshooting guides | Home broadband plans, connection fault guides |
| **WiFi** | Product plans, troubleshooting guides | Hotspot plans, router setup guides |
| **Roaming** | Product plans, troubleshooting guides | International roaming passes, roaming FAQ |
| **General** | Any other service document | Agent guides, billing dispute guides |

---

## Understanding Quality Indicators

After conversion, the tool reports:

### Compliance Score
A percentage (0–100%) reflecting how closely the output matches the required KB template structure. Scores are calculated based on:
- Required sections present
- Markdown headers, tables, and bullet points found
- Pricing table detected
- Contact information included

A score of **70% or above** indicates a well-structured output. Scores below 70% may mean the source document had limited content in certain areas.

### Validation Warnings
These are informational notices about sections that could not be fully populated from the source. Common warnings include:

| Warning | What It Means |
|---------|---------------|
| "Missing sections: FAQ" | The source document had no FAQ content |
| "No pricing table detected" | No pricing data found in the source |
| "Too many placeholder values" | Several fields could not be extracted — review manually |

> Validation warnings do **not** mean the conversion failed. They flag areas that may need a human review before publishing.

### Hyperlink Preservation
The tool tracks how many hyperlinks were found in the source and how many were preserved in the output. A preservation rate of **90%+** is excellent.

---

## Cost per Conversion

The tool uses the OpenAI GPT-4o Mini model. Approximate costs:

| Document Size | Estimated Cost (USD) |
|---------------|---------------------|
| Small (< 2,000 words) | ~$0.003 |
| Medium (2,000–5,000 words) | ~$0.006 |
| Large (5,000+ words) | ~$0.010 |

Exact cost per conversion is shown in the results panel after each run. The tool makes 2–3 API calls per document (classification, analysis, and structuring).

---

## Output File Locations

Converted files are saved automatically to the following folders within the project:

| Format | Folder |
|--------|--------|
| Markdown (`.md`) | `converted_docs/markdown/` |
| Word Document (`.docx`) | `converted_docs/docx/` |

Files are named: `converted_<original_filename>.<ext>`

---

## Limitations & Known Considerations

| Limitation | Detail |
|------------|--------|
| **Maximum file size** | 5 MB per file via the web UI (50 MB via CLI) |
| **Scanned PDFs** | PDFs that are scanned images (not text-based) cannot be processed — the tool requires selectable text |
| **Content truncation** | Very long documents (>8,000 words of relevant content) may have later sections truncated to fit within AI processing limits |
| **Generated contact details** | The AI will never fabricate phone numbers, emails, or addresses. If contact info is absent from the source, the output will state "Contact information not provided in source document" |
| **AI accuracy** | The output is AI-generated and should be reviewed by a subject-matter expert before publishing, especially for pricing figures and eligibility criteria |
| **Processing time** | Each document takes approximately 15–45 seconds depending on length and AI response time |

---

## Frequently Asked Questions

**Q: Can I convert multiple documents at once?**
Yes. Upload multiple files in the same session and click Convert. The tool processes them sequentially and shows individual results for each file.

**Q: What if the conversion output looks wrong or incomplete?**
Check the validation warnings in the results panel. If key sections are missing, it usually means the source document did not contain that information. You can also try re-running — AI outputs can vary slightly between runs.

**Q: Where do I find the converted files after downloading?**
Downloaded files go to your browser's default downloads folder. Copies are also saved to `converted_docs/docx/` and `converted_docs/markdown/` in the project folder.

**Q: Does the tool modify the original source document?**
No. Source documents in the `docs/` folder are read-only. The tool only creates new files in `converted_docs/`.

**Q: What happens if the AI service is unavailable?**
The tool will retry up to 3 times before generating a basic fallback document containing the raw extracted text. The fallback document will be clearly marked at the bottom.

---
