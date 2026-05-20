"""
Configuration Settings for Document Conversion Pipeline
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_TEMPERATURE = 0.3
OPENAI_MAX_TOKENS = 4000
OPENAI_TIMEOUT = 60
MAX_RETRIES = 3

# File Paths
INPUT_FOLDER = "docs"
OUTPUT_FOLDER = "converted_docs"
DOCX_OUTPUT_FOLDER = "converted_docs/docx"
MARKDOWN_OUTPUT_FOLDER = "converted_docs/markdown"
TEMPLATE_FILE = "IKB_Document_Template.md"
LOG_FOLDER = "logs"

# Processing Settings
BATCH_SIZE = 5
MAX_FILE_SIZE_MB = 50
SUPPORTED_EXTENSIONS = ['.docx', '.pdf']

# PDF Processing Settings
PDF_PROCESSING_SETTINGS = {
    'extract_tables': True,   # Extract tables from PDFs
    'preserve_layout': True,  # Maintain document structure
}

# Output Format Settings
DEFAULT_OUTPUT_FORMAT = "docx"  # Options: "docx", "markdown", "both"
ENABLE_DUAL_OUTPUT = True
USD_TO_MYR_RATE = float(os.getenv("USD_TO_MYR_RATE", "4.24"))

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = os.path.join(LOG_FOLDER, "conversion.log")

# Template Validation Rules
REQUIRED_SECTIONS = [
    "Document Information",
    "Key Features", 
    "Detailed Information",
    "Pricing Information",
    "Eligibility",
    "How to Subscribe",
    "Terms and Conditions",
    "FAQ",
    "Customer Support"
]

# Simplified and More Effective AI Processing Prompts
SYSTEM_PROMPT = """You are a document conversion specialist focused on creating structured knowledge base documents for telecommunications services. You excel at:

1. Analyzing telecommunications service documents accurately
2. Extracting key information systematically  
3. Organizing content according to specific templates
4. Creating clear, structured markdown documents
5. Maintaining accuracy while improving readability

Always follow the provided template structure exactly and ensure all sections are properly formatted with actual content from the source document.

When following the template, ALWAYS replace "# IKB Document Structure Template" with the actual document title from the source content. The main header should be the service/document name, NOT the template name.

IMPORTANT: 
- Do NOT include or copy the "General Rules" section from the template in the converted document. The "General Rules" section is for internal guidance only and should be omitted from the final output.
- Preserve ALL hyperlinks found in the source document
- Convert links to proper markdown format: [link text](URL)
- Include links in appropriate sections (especially Customer Support, How to Subscribe)
- For table links, maintain the link within the table structure
- If a link's display text differs from URL, preserve both

Extract and structure as much meaningful content as possible from the source document while maintaining accuracy and completeness.
"""

# Dynamic and Adaptive Structure Prompt
STRUCTURE_PROMPT_TEMPLATE = """
You are an intelligent document converter that adapts template sections based on document content.

TEMPLATE STRUCTURE (ADAPTIVE):
{template}

SOURCE DOCUMENT:
{content}

CONTENT ANALYSIS:
{analysis}

**ADAPTIVE CONVERSION INSTRUCTIONS:**

1. **Smart Title Extraction**:
   - Use the actual service/product name from the document
   - Include version, edition, or variant if mentioned
   - Format: "[Service Name] - [Type]" (e.g., "CelcomDigi Roaming Plus - International Data Package")

2. **Intelligent Section Mapping**:
   Based on the document type, adapt sections as follows:

   **For Product Documents**:
   - Keep: Key Features, Pricing Information, Eligibility, How to Subscribe
   - Enhance: Detailed Information → Service Overview + Coverage Details
   - Adapt: FAQ → Product-specific questions

   **For Troubleshooting Documents**:
   - Keep: Document Information, Customer Support
   - Replace: Key Features → Common Issues
   - Replace: Pricing Information → Troubleshooting Steps (table format)
   - Replace: How to Subscribe → Resolution Process
   - Enhance: FAQ → Troubleshooting FAQ

   **For Technical Documents**:
   - Keep: Document Information, Customer Support
   - Replace: Key Features → Technical Specifications
   - Replace: Pricing Information → Configuration Requirements
   - Replace: Eligibility → System Requirements
   - Replace: How to Subscribe → Setup Instructions

3. **Dynamic Content Adaptation**:
   - **If pricing found**: Create comprehensive pricing tables
   - **If no pricing found**: Replace pricing section with relevant information table
   - **If troubleshooting steps found**: Structure as numbered procedures
   - **If technical specs found**: Create specification tables
   - **If contact info found**: Enhance customer support section

4. **Section Relevance Assessment**:
   Only include sections that have actual content. For sections without relevant content:
   - **Skip entirely** rather than using "Information not available"
   - **Merge related sections** for better flow
   - **Add custom sections** if document has unique content not covered by template

5. **Content-Aware Formatting**:
   - **Tables**: Use for pricing, specifications, troubleshooting steps, comparisons
   - **Lists**: Use for features, requirements, steps, conditions
   - **Paragraphs**: Use for descriptions, explanations, policies

**SMART EXTRACTION RULES:**
- Extract ALL specific data (numbers, prices, technical specs, contact details, links)
- Preserve ALL proper nouns (service names, locations, brands)
- Maintain ALL step-by-step procedures exactly as written
- Adapt table structures to match content type (pricing vs specs vs troubleshooting)
- Keep ALL contact information and support channels
- For Customer Support section: If no contact info found, use standard fallback text
- NEVER generate fictional contact details (phone numbers, emails, addresses)

**IMPORTANT**: Use actual content from the source document. If information is not available, write "Information not available in source document" rather than generic placeholders.
- If Customer Support section has no source content, use generic reference to official channels
- Write "Contact information not provided in source document" rather than generating fictional details

Return a dynamically structured document that matches the content type while following the template's professional format.
"""

# Enhanced Document Type Prompts with Specific Context
DOCUMENT_TYPE_PROMPTS = {
        # ROAMING CATEGORY
    "roaming_product": """
    ROAMING PRODUCT - Extract:
    - Country/region coverage with specific names
    - Data packages (GB amounts, speeds, validity)
    - Voice/SMS rates by destination zones
    - Activation methods and requirements
    - Daily/weekly/monthly package options
    - Fair usage policies and limitations
    """,
    
    "roaming_troubleshooting": """
    ROAMING TROUBLESHOOTING - Extract:
    - Common roaming issues and symptoms
    - Step-by-step resolution procedures
    - Network settings and APN configurations
    - Emergency contact methods while abroad
    - Service restoration procedures
    """,
    
    # FIBRE CATEGORY  
    "fibre_product": """
    FIBRE PRODUCT - Extract:
    - Speed tiers and bandwidth options
    - Monthly subscription costs and setup fees
    - Coverage areas and availability
    - Equipment and installation requirements
    - Contract terms and promotional offers
    """,
    
    "fibre_troubleshooting": """
    FIBRE TROUBLESHOOTING - Extract:
    - Connection issues and diagnostic steps
    - Speed optimization procedures
    - Equipment troubleshooting guides
    - Service outage reporting methods
    - Technical support escalation process
    """,
    
    # WIFI CATEGORY
    "wifi_product": """
    WIFI PRODUCT - Extract:
    - Hotspot locations and coverage maps
    - Access plans and usage allowances
    - Device compatibility requirements
    - Connection procedures and authentication
    - Security features and protocols
    """,

    "wifi_troubleshooting": """
    HOME WIFI TROUBLESHOOTING - Extract:
    - Common WiFi connection issues and symptoms (slow speed, no connection, intermittent drop, device not connecting)
    - Step-by-step resolution procedures exactly as in the document
    - Equipment checks (router, modem, cables, power supply)
    - Router/modem LED indicator meanings
    - Device-specific troubleshooting (model-specific reset, firmware update, etc.)
    - Network settings (SSID, password, APN if applicable)
    - Fair Usage Policy impact on speed and connectivity
    - Environmental factors affecting WiFi performance (distance, interference)
    - Instructions for resetting or reconfiguring equipment
    - Contact points for further assistance (support numbers, links, store visits)
    - Escalation process if the issue is unresolved
    - Any warnings or “do not” instructions from the document

    FORMATTING RULES:
    - Use ordered lists for troubleshooting steps
    - Use tables for LED status meanings, error codes
    - Keep technical terms exactly as stated in the source
    - Preserve all hyperlinks in markdown [text](URL) format
    - Do not paraphrase device error messages, status text, or button labels
    """,

    # MOBILE CATEGORY
    "mobile_product": """
    MOBILE PRODUCT (Prepaid & Postpaid) - Extract:
    - Plan names and types (clearly label as Prepaid, Postpaid, or Hybrid if stated)
    - Monthly fees or reload amounts
    - Included allowances (data, calls, SMS) with validity periods
    - Bonus or promotional data/call/SMS offers
    - Data speed limits, throttling policies, or FUP
    - Add-on options (data passes, voice packs, roaming add-ons)
    - Device bundle availability (if included with plan)
    - Activation/subscription process (in-store, app, USSD, online)
    - Eligibility requirements
    - Contract terms (if any)
    - Channels where the offer is promoted (app, website, in-store)
    - Multilingual customer-facing content (keep EN, BM, CH separate if provided)
    - Internal campaign notes or promotional banners
    - Related FAQs
    - All official links preserved in markdown [text](URL) format

    FORMATTING RULES:
    - Use tables for plan comparisons and allowance breakdowns
    - Use bullet lists for features, eligibility, activation steps
    - Preserve all prices, numbers, and data caps exactly as in source
    """,

    "mobile_troubleshooting": """
    MOBILE TROUBLESHOOTING (Prepaid & Postpaid) - Extract:
    - Common issues (e.g., unable to make calls, no data, payment errors, balance deduction)
    - Step-by-step resolution procedures exactly as in source
    - Network settings (APN, LTE/5G toggle, roaming enablement)
    - Account checks (balance, bill payment status, credit limit)
    - SIM card troubleshooting (reseating, replacement)
    - Service suspension and reactivation process
    - USSD codes or app navigation steps for diagnostics
    - Contact channels for further support (phone, live chat, in-store)
    - Escalation process if unresolved
    - Warnings or notes provided in the document

    FORMATTING RULES:
    - Use ordered lists for troubleshooting steps
    - Use tables for error codes, USSD codes, or plan-specific fixes
    - Preserve button labels, system messages, and USSD code formats exactly
    - Keep all hyperlinks in markdown [text](URL) format
    """,
    
    # FALLBACK
    "general": """
    GENERAL DOCUMENT - Extract:
    - All available service information
    - Pricing and plan details
    - Contact and support information
    - Terms and conditions
    """
}

# Document Classifier Prompt for Better Type Detection
DOCUMENT_CLASSIFIER_PROMPT = """
Analyze this document and classify it accurately:

DOCUMENT CONTENT (First 2000 characters):
{content_preview}

**CLASSIFICATION CRITERIA:**

**Primary Category** (Choose one):
- ROAMING: International usage, travel, country lists, roaming rates
- FIBRE: Home broadband, internet plans, installation, speed tiers
- WIFI: Hotspots, wireless access, public WiFi, connection guides
- MOBILE: Voice plans, SMS packages, local data, postpaid/prepaid
- BUSINESS: Corporate services, enterprise solutions, bulk accounts
- DEVICE: Phones, modems, equipment, specifications, compatibility

**Secondary Type** (Choose one):
- PRODUCT: Packages, plans, pricing, features, subscription info
- TROUBLESHOOTING: Issues, problems, solutions, fixes, diagnostics
- TECHNICAL: Specifications, requirements, setup, configuration
- GUIDE: Instructions, how-to, tutorials, procedures

**Detection Keywords Found**:
List the specific keywords that led to this classification.

**Recommended Template Adaptations**:
Suggest which template sections should be modified, added, or removed for this document type.

Return: PRIMARY_CATEGORY:SECONDARY_TYPE (e.g., "ROAMING:PRODUCT" or "FIBRE:TROUBLESHOOTING")
"""

def validate_config():
    """Enhanced configuration validation."""
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key is required.")
    
    # Create ALL necessary directories
    directories = [
        OUTPUT_FOLDER,
        DOCX_OUTPUT_FOLDER,  
        MARKDOWN_OUTPUT_FOLDER, 
        LOG_FOLDER
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    if not os.path.exists(TEMPLATE_FILE):
        raise FileNotFoundError(f"Template file not found: {TEMPLATE_FILE}")
    
    return True

if __name__ == "__main__":
    try:
        validate_config()
        print("Configuration validation successful!")
    except Exception as e:
        print(f"Configuration error: {e}")
