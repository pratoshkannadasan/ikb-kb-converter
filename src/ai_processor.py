"""
AI Processor Module
Handles OpenAI integration for content structuring and template population.
"""

import logging
from openai import OpenAI
from typing import Dict, List, Optional, Tuple
import os
import re
import time
import json
from dotenv import load_dotenv


class APIUsageTracker:
    """Track OpenAI API usage and costs."""
    
    # GPT-4o mini pricing (per 1M tokens)
    INPUT_TOKEN_RATE = 0.60 / 1_000_000      # $0.60 per 1M input tokens
    CACHED_INPUT_TOKEN_RATE = 0.30 / 1_000_000  # $0.30 per 1M cached input tokens
    OUTPUT_TOKEN_RATE = 2.40 / 1_000_000     # $2.40 per 1M output tokens
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self.api_calls = 0
        
    def track_usage(self, response, model: str = "gpt-4o-mini"):
        """Track token usage from OpenAI response."""
        try:
            if hasattr(response, 'usage'):
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                
                # Calculate costs
                input_cost = prompt_tokens * self.INPUT_TOKEN_RATE
                output_cost = completion_tokens * self.OUTPUT_TOKEN_RATE
                call_cost = input_cost + output_cost
                
                # Update totals
                self.total_input_tokens += prompt_tokens
                self.total_output_tokens += completion_tokens
                self.total_cost += call_cost
                self.api_calls += 1
                
                # Log usage details
                self.logger.info(f"API Call #{self.api_calls} - Model: {model}")
                self.logger.info(f"  Input tokens: {prompt_tokens:,} (${input_cost:.6f})")
                self.logger.info(f"  Output tokens: {completion_tokens:,} (${output_cost:.6f})")
                self.logger.info(f"  Call cost: ${call_cost:.6f}")
                self.logger.info(f"  Running total: ${self.total_cost:.6f}")
                
        except Exception as e:
            self.logger.error(f"Error tracking API usage: {str(e)}")
    
    def get_usage_summary(self) -> Dict:
        """Get complete usage summary."""
        return {
            "total_api_calls": self.api_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "total_cost": self.total_cost,
            "average_cost_per_call": self.total_cost / self.api_calls if self.api_calls > 0 else 0,
            "input_token_rate": self.INPUT_TOKEN_RATE * 1_000_000,  # Show as per 1M
            "output_token_rate": self.OUTPUT_TOKEN_RATE * 1_000_000  # Show as per 1M
        }
    
    # REDUNDANT METHOD REMOVED - Use log_usage_summary() instead


class AIProcessor:
    """Process document content using OpenAI GPT-4 for structuring."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        load_dotenv()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.usage_tracker = APIUsageTracker()  # Initialize cost tracking
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
            
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
        
    # LEGACY METHOD REMOVED - Use analyze_content_with_recommendations() instead
    
    def determine_document_type_enhanced(self, content: str) -> tuple:
        """Enhanced document type detection with category and type classification."""
        try:
            self.logger.info("Starting enhanced document type detection")
            
            # Get preview of content for classification
            content_preview = content[:2000]
            
            import config
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for classification
                messages=[
                    {"role": "system", "content": "You are a document classifier for telecommunications services."},
                    {"role": "user", "content": config.DOCUMENT_CLASSIFIER_PROMPT.format(content_preview=content_preview)}
                ],
                temperature=0.1,
                max_tokens=500
            )
            
            # Track usage
            self.usage_tracker.track_usage(response, "gpt-4o-mini")
            
            classification = response.choices[0].message.content.strip()
            
            # Parse the classification
            if ":" in classification:
                category, doc_type = classification.split(":", 1)
                combined_type = f"{category.lower()}_{doc_type.lower()}"
                self.logger.info(f"Document classified as: {combined_type}")
                return category.lower(), doc_type.lower(), combined_type
            else:
                # Fallback to simple classification
                return "general", "product", "general_product"
                
        except Exception as e:
            self.logger.warning(f"Enhanced classification failed: {str(e)}")
            # Fallback to original method
            original_type = "general"  # Simple fallback instead of calling removed method
            return original_type, "product", f"{original_type}_product"

    def structure_content_adaptive(self, document_content: str, template: str, hyperlinks: Optional[List[Dict]] = None) -> str:
        """Adaptive content structuring based on document type and context.
        
        Args:
            document_content (str): Raw document content
            template (str): Target template structure
            hyperlinks (Optional[List[Dict]]): List of hyperlinks found in document
            
        Returns:
            str: Structured content matching template with adaptive sections
        """
        try:
            self.logger.info("Starting adaptive AI content structuring")
            
            # Enhanced document classification
            category, doc_type, combined_type = self.determine_document_type_enhanced(document_content)
            
            # Content analysis with enhanced prompts
            content_analysis = self.analyze_content(document_content)
            
            # Use dynamic structure prompt
            import config
            prompt = config.STRUCTURE_PROMPT_TEMPLATE.format(
                template=template,
                content=document_content[:8000],  # Limit content for token management
                analysis=content_analysis
            )
            
            # Add hyperlink information if available
            if hyperlinks:
                hyperlink_info = self._format_hyperlinks_for_prompt(hyperlinks)
                prompt += f"\n\nHYPERLINKS FOUND IN DOCUMENT:\n{hyperlink_info}"
                prompt += "\n\nIMPORTANT: Preserve all hyperlinks in the appropriate sections. Convert them to markdown format [text](URL) and ensure they are placed in relevant sections like Customer Support, How to Subscribe, or within table content."
            
            # Add specific guidance for the detected type
            if combined_type in config.DOCUMENT_TYPE_PROMPTS:
                prompt += f"\n\nSPECIFIC FOCUS FOR {combined_type.upper()}:\n{config.DOCUMENT_TYPE_PROMPTS[combined_type]}"
            elif category in config.DOCUMENT_TYPE_PROMPTS:
                prompt += f"\n\nSPECIFIC FOCUS FOR {category.upper()}:\n{config.DOCUMENT_TYPE_PROMPTS[category]}"
            
            self.logger.info(f"Processing with adaptive approach for {combined_type}")
            
            # Process with adaptive approach
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for more focused extraction
                max_tokens=3500,  # Slightly reduced to leave more room for input
                timeout=config.OPENAI_TIMEOUT
            )
            
            # Track usage
            self.usage_tracker.track_usage(response, config.OPENAI_MODEL)
            
            structured_content = response.choices[0].message.content
            self.logger.info("Adaptive AI processing completed successfully")
            
            return structured_content
            
        except Exception as e:
            self.logger.error(f"Adaptive structuring failed: {str(e)}")
            # Fallback to basic content structure
            return self._create_fallback_structure(document_content[:6000])
    
    def structure_content_with_hyperlinks(self, document_content: str, template: str, hyperlinks: List[Dict]) -> str:
        """Enhanced content structuring with specific focus on hyperlink preservation.
        
        Args:
            document_content (str): Raw document content
            template (str): Target template structure
            hyperlinks (List[Dict]): List of hyperlinks found in document
            
        Returns:
            str: Structured content with preserved hyperlinks
        """
        try:
            self.logger.info(f"Starting hyperlink-aware content structuring with {len(hyperlinks)} links")
            
            # Create enhanced prompt focusing on hyperlink preservation
            hyperlink_info = self._format_hyperlinks_for_prompt(hyperlinks)
            
            import config
            prompt = f"""Please structure the following document content according to the provided template, with SPECIAL ATTENTION to preserving all hyperlinks.

TEMPLATE TO FOLLOW:
{template}

DOCUMENT CONTENT:
{document_content[:7000]}

HYPERLINKS FOUND IN DOCUMENT:
{hyperlink_info}

CRITICAL HYPERLINK REQUIREMENTS:
1. ALL hyperlinks must be preserved and included in the structured output
2. Convert hyperlinks to markdown format: [link text](URL)
3. Place hyperlinks in the most appropriate sections:
   - Customer support links → Customer Support section
   - Subscription/purchase links → How to Subscribe section
   - General information links → relevant content sections
   - Table links → maintain within table structure
4. If a hyperlink's original context is unclear, include it in the most relevant section
5. Ensure all {len(hyperlinks)} hyperlinks are accounted for in the final output

Focus on creating a complete, well-structured document that maintains all the original hyperlinks while following the template structure exactly."""
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3500,
                timeout=config.OPENAI_TIMEOUT
            )
            
            # Track usage
            self.usage_tracker.track_usage(response, config.OPENAI_MODEL)
            
            structured_content = response.choices[0].message.content
            self.logger.info("Hyperlink-aware AI processing completed successfully")
            
            # Validate that hyperlinks are preserved
            self._validate_hyperlink_preservation(structured_content, hyperlinks)
            
            return structured_content
            
        except Exception as e:
            self.logger.error(f"Hyperlink-aware structuring failed: {str(e)}")
            # Fallback to adaptive processing
            return self.structure_content_adaptive(document_content, template, hyperlinks)
    
    def _format_hyperlinks_for_prompt(self, hyperlinks: List[Dict]) -> str:
        """Format hyperlinks for inclusion in AI prompt.
        
        Args:
            hyperlinks (List[Dict]): List of hyperlink dictionaries
            
        Returns:
            str: Formatted hyperlink information
        """
        if not hyperlinks:
            return "No hyperlinks found in document."
        
        formatted_links = []
        for i, link in enumerate(hyperlinks, 1):
            location = link.get('location', 'unknown')
            link_type = link.get('type', 'unknown')
            text = link.get('text', 'No text')
            url = link.get('url', 'No URL')
            
            if link_type == 'table_cell':
                row = link.get('row', '?')
                col = link.get('column', '?')
                location_detail = f"{location} (Table row {row}, col {col})"
            else:
                location_detail = location
            
            formatted_links.append(f"{i}. Text: '{text}' | URL: {url} | Location: {location_detail}")
        
        return "\n".join(formatted_links)
    
    def _validate_hyperlink_preservation(self, structured_content: str, original_hyperlinks: List[Dict]) -> None:
        """Validate that hyperlinks are preserved in the structured content.
        
        Args:
            structured_content (str): The AI-generated structured content
            original_hyperlinks (List[Dict]): Original hyperlinks from document
        """
        try:
            # Count markdown links in output
            import re
            markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', structured_content)
            
            preserved_count = len(markdown_links)
            original_count = len(original_hyperlinks)
            
            self.logger.info(f"Hyperlink preservation check: {preserved_count}/{original_count} links found in output")
            
            if preserved_count < original_count:
                missing_count = original_count - preserved_count
                self.logger.warning(f"⚠️ {missing_count} hyperlinks may be missing from structured output")
            else:
                self.logger.info("✓ All hyperlinks appear to be preserved")
                
        except Exception as e:
            self.logger.warning(f"Could not validate hyperlink preservation: {str(e)}")
    
    
    def analyze_content_with_recommendations(self, document_content: str) -> str:
        """Analyze content and extract template adaptation recommendations.
        
        Args:
            document_content (str): Raw document content
            
        Returns:
            str: Analysis with explicit template recommendations
        """
        try:
            import config
            self.logger.info("Analyzing content for template recommendations")
            
            # Enhanced analysis prompt that specifically asks for recommendations
            analysis_prompt = f"""
            Analyze this document content and provide specific template adaptation recommendations:

            CONTENT TO ANALYZE:
            {document_content[:6000]}

            Please provide:
            1. CONTENT ANALYSIS: Document type, key themes, and structure
            2. TEMPLATE RECOMMENDATIONS: Specific adaptations needed for optimal template mapping
            3. SECTION PRIORITIES: Which template sections need emphasis or modification
            4. FORMATTING SUGGESTIONS: Special formatting requirements (tables, lists, etc.)
            
            Focus on actionable recommendations that will improve the final structured output.
            """
            
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert document analyst providing specific template adaptation recommendations."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1,
                max_tokens=1500,
                timeout=config.OPENAI_TIMEOUT
            )
            
            # Track usage
            self.usage_tracker.track_usage(response, config.OPENAI_MODEL)
            
            analysis_with_recommendations = response.choices[0].message.content
            self.logger.info("Content analysis with recommendations completed")
            
            return analysis_with_recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to analyze content with recommendations: {str(e)}")
            # Fallback to basic analysis
            return self.analyze_content(document_content)
    
    def _extract_recommendations_from_analysis(self, analysis: str) -> Dict[str, str]:
        """Extract specific recommendations from the analysis.
        
        Args:
            analysis (str): Analysis text containing recommendations
            
        Returns:
            Dict[str, str]: Extracted recommendations by category
        """
        try:
            recommendations = {
                'template_adaptations': '',
                'section_priorities': '',
                'formatting_suggestions': '',
                'content_focus': ''
            }
            
            # Extract recommendations using text patterns
            import re
            
            # Look for template recommendations
            template_match = re.search(r'TEMPLATE RECOMMENDATIONS?:(.+?)(?=\n\d+\.|$)', analysis, re.DOTALL | re.IGNORECASE)
            if template_match:
                recommendations['template_adaptations'] = template_match.group(1).strip()
            
            # Look for section priorities
            section_match = re.search(r'SECTION PRIORITIES?:(.+?)(?=\n\d+\.|$)', analysis, re.DOTALL | re.IGNORECASE)
            if section_match:
                recommendations['section_priorities'] = section_match.group(1).strip()
            
            # Look for formatting suggestions
            format_match = re.search(r'FORMATTING SUGGESTIONS?:(.+?)(?=\n\d+\.|$)', analysis, re.DOTALL | re.IGNORECASE)
            if format_match:
                recommendations['formatting_suggestions'] = format_match.group(1).strip()
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to extract recommendations: {str(e)}")
            return {'template_adaptations': '', 'section_priorities': '', 'formatting_suggestions': '', 'content_focus': ''}
    
    def structure_content_with_recommendations(self, document_content: str, template: str, hyperlinks: Optional[List[Dict]] = None) -> str:
        """Structure content using LLM-recommended template adaptations.
        
        Args:
            document_content (str): Raw document content
            template (str): Target template structure
            hyperlinks (Optional[List[Dict]]): List of hyperlinks found in document
            
        Returns:
            str: Structured content with applied recommendations
        """
        try:
            import config
            self.logger.info("Starting content structuring with LLM recommendations")
            
            # Step 1: Get analysis with specific recommendations
            analysis_with_recommendations = self.analyze_content_with_recommendations(document_content)
            
            # Step 2: Extract actionable recommendations
            recommendations = self._extract_recommendations_from_analysis(analysis_with_recommendations)
            
            # Step 3: Enhanced document classification
            category, doc_type, combined_type = self.determine_document_type_enhanced(document_content)
            
            # Step 4: Create recommendation-aware prompt WITH HYPERLINKS
            prompt = self._create_recommendation_aware_prompt(
                document_content, template, analysis_with_recommendations, recommendations, combined_type, hyperlinks
            )
            
            self.logger.info(f"Processing with recommendations for {combined_type}")
            
            # Log hyperlink info for debugging
            if hyperlinks and len(hyperlinks) > 0:
                self.logger.info(f"🔗 Processing with {len(hyperlinks)} hyperlinks included in prompt")
                # Debug: Show first few hyperlinks
                for i, link in enumerate(hyperlinks[:2], 1):
                    self.logger.debug(f"  Hyperlink {i}: '{link.get('text', '')}' -> {link.get('url', '')}")
                if len(hyperlinks) > 2:
                    self.logger.debug(f"  ... and {len(hyperlinks) - 2} more hyperlinks")
            else:
                self.logger.info(f"📝 Processing without hyperlinks (hyperlinks={hyperlinks})")
            
            # Step 5: Process with recommendation-enhanced prompt
            response = self.client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": config.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=3500,
                timeout=config.OPENAI_TIMEOUT
            )
            
            # Track usage
            self.usage_tracker.track_usage(response, config.OPENAI_MODEL)
            
            structured_content = response.choices[0].message.content
            self.logger.info("Recommendation-based structuring completed successfully")
            
            # Validate hyperlinks if provided
            if hyperlinks:
                self._validate_hyperlink_preservation(structured_content, hyperlinks)
            
            return structured_content
            
        except Exception as e:
            self.logger.error(f"Recommendation-based structuring failed: {str(e)}")
            # Fallback to adaptive method WITH hyperlinks
            return self.structure_content_adaptive(document_content, template, hyperlinks)
    
    def _create_recommendation_aware_prompt(self, document_content: str, template: str, 
                                          analysis: str, recommendations: Dict[str, str], 
                                          doc_type: str, hyperlinks: Optional[List[Dict]] = None) -> str:
        """Create a structuring prompt that incorporates LLM recommendations.
        
        Args:
            document_content (str): Raw content
            template (str): Target template
            analysis (str): Content analysis with recommendations
            recommendations (Dict[str, str]): Extracted recommendations
            doc_type (str): Document type
            hyperlinks (Optional[List[Dict]]): List of hyperlinks found in document
            
        Returns:
            str: Enhanced prompt with recommendations
        """
        try:
            import config
            
            # Base prompt
            base_prompt = config.STRUCTURE_PROMPT_TEMPLATE.format(
                template=template,
                content=document_content[:7000],  # Reserve space for recommendations
                analysis=analysis
            )
            
            # Add hyperlink information if available
            if hyperlinks:
                hyperlink_info = self._format_hyperlinks_for_prompt(hyperlinks)
                base_prompt += f"\n\nHYPERLINKS TO PRESERVE:\n{hyperlink_info}"
                base_prompt += f"\n\nCRITICAL: All {len(hyperlinks)} hyperlinks must be preserved in the structured output using markdown format [text](URL)."
            
            # Add recommendation-specific instructions
            recommendation_instructions = "\n\nAPPLY THESE SPECIFIC RECOMMENDATIONS:\n"
            
            if recommendations['template_adaptations']:
                recommendation_instructions += f"\nTEMPLATE ADAPTATIONS:\n{recommendations['template_adaptations']}\n"
            
            if recommendations['section_priorities']:
                recommendation_instructions += f"\nSECTION PRIORITIES:\n{recommendations['section_priorities']}\n"
            
            if recommendations['formatting_suggestions']:
                recommendation_instructions += f"\nFORMATTING REQUIREMENTS:\n{recommendations['formatting_suggestions']}\n"
            
            # Add document-type specific guidance
            if doc_type in config.DOCUMENT_TYPE_PROMPTS:
                recommendation_instructions += f"\nDOCUMENT TYPE FOCUS ({doc_type.upper()}):\n{config.DOCUMENT_TYPE_PROMPTS[doc_type]}\n"
            
            # Final instruction to ensure recommendations are applied
            recommendation_instructions += """
            
            CRITICAL: Ensure that you implement ALL the above recommendations in your structured output.
            Adapt the template sections based on the specific recommendations provided.
            Pay special attention to the formatting suggestions and section priorities.
            """
            
            enhanced_prompt = base_prompt + recommendation_instructions
            
            return enhanced_prompt
            
        except Exception as e:
            self.logger.error(f"Failed to create recommendation-aware prompt: {str(e)}")
            # Fallback to base prompt
            import config
            return config.STRUCTURE_PROMPT_TEMPLATE.format(
                template=template,
                content=document_content[:8000],
                analysis=analysis
            )

    def validate_structure(self, structured_content: str) -> Tuple[bool, float, List[str]]:
        """Enhanced template compliance validation with detailed feedback.
        
        Args:
            structured_content (str): AI-generated content
            
        Returns:
            Tuple[bool, float, List[str]]: (is_compliant, compliance_score, issues)
        """
        try:
            self.logger.info("Validating structured content compliance")
            
            issues = []
            
            if not structured_content or len(structured_content.strip()) < 100:
                issues.append("Content too short or empty")
                return False, 0.0, issues
            
            # Check for required sections
            import config
            required_sections = config.REQUIRED_SECTIONS
            sections_found = 0
            missing_sections = []
            
            for section in required_sections:
                if section.lower() in structured_content.lower():
                    sections_found += 1
                else:
                    missing_sections.append(section)
            
            if missing_sections:
                issues.append(f"Missing sections: {', '.join(missing_sections[:3])}")
            
            # Check for markdown formatting
            has_headers = structured_content.count('#') >= 3
            has_tables = '|' in structured_content and structured_content.count('|') >= 6
            has_bullets = ('- ' in structured_content or '* ' in structured_content)
            has_numbered_lists = bool(re.search(r'^\d+\.\s+', structured_content, re.MULTILINE))
            
            # Advanced content checks
            has_pricing_table = bool(re.search(r'\|\s*.*[Pp]rice.*\s*\|', structured_content))
            has_feature_list = len(re.findall(r'^[-*]\s+.+', structured_content, re.MULTILINE)) >= 3
            has_contact_info = any(term in structured_content.lower() for term in ['phone', 'email', 'contact', 'support', 'links'])
            
            # Calculate compliance score
            section_score = (sections_found / len(required_sections)) * 0.3
            format_score = (
                (1 if has_headers else 0) * 0.15 +
                (1 if has_tables else 0) * 0.15 +
                (1 if has_bullets else 0) * 0.1 +
                (1 if has_numbered_lists else 0) * 0.1
            )
            content_score = (
                (1 if has_pricing_table else 0) * 0.1 +
                (1 if has_feature_list else 0) * 0.05 +
                (1 if has_contact_info else 0) * 0.05
            )
            
            compliance_score = section_score + format_score + content_score
            
            # Add specific issues
            if not has_headers:
                issues.append("Missing proper header structure")
            if not has_tables:
                issues.append("No tables found for pricing information")
            if not has_feature_list:
                issues.append("Insufficient feature bullet points")
            if not has_pricing_table:
                issues.append("No pricing table detected")
            
            is_compliant = compliance_score >= 0.7 and len(issues) <= 2
            
            self.logger.info(f"Validation complete - Compliance score: {compliance_score:.2f} ({'PASS' if is_compliant else 'FAIL'})")
            if issues:
                self.logger.warning(f"Validation issues: {'; '.join(issues)}")
            
            return is_compliant, compliance_score, issues
            
        except Exception as e:
            self.logger.error(f"Error validating structure: {str(e)}")
            return False, 0.0, [f"Validation error: {str(e)}"]
    
    def process_with_retry_adaptive(self, content: str, template: str, max_retries: int = 3, hyperlinks: Optional[List[Dict]] = None) -> str:
        """Process content with adaptive retry logic and enhanced error handling.
        
        Args:
            content (str): Document content to process
            template (str): Template to use
            max_retries (int): Maximum number of retry attempts
            hyperlinks (Optional[List[Dict]]): List of hyperlinks found in document
            
        Returns:
            str: Processed content
        """
        for attempt in range(1, max_retries + 1):
            try:
                self.logger.info(f"Adaptive processing attempt {attempt}/{max_retries}")
                
                if attempt > 1:
                    # Add delay between retries
                    wait_time = min(30, 5 * attempt)
                    self.logger.info(f"Waiting {wait_time} seconds before retry")
                    time.sleep(wait_time)
                
                # Use adaptive processing method with hyperlinks
                result = self.structure_content_adaptive(content, template, hyperlinks)
                
                # Validate the result
                is_valid, score, issues = self.validate_structure(result)
                
                if is_valid or attempt == max_retries:
                    if not is_valid:
                        self.logger.warning(f"Final attempt produced suboptimal result (score: {score:.2f})")
                    return result
                else:
                    self.logger.warning(f"Attempt {attempt} failed validation (score: {score:.2f}), retrying...")
                    continue
                    
            except Exception as e:
                self.logger.error(f"Adaptive attempt {attempt} failed: {str(e)}")
                
                if attempt == max_retries:
                    # Final attempt - use fallback
                    self.logger.error("All adaptive attempts failed, using fallback processing")
                    return self.handle_processing_errors(e, content, attempt)
                else:
                    # Try to handle the error and continue
                    try:
                        fallback_result = self.handle_processing_errors(e, content, attempt)
                        if fallback_result != content:  # Only return if we got a processed result
                            return fallback_result
                    except:
                        continue  # Continue to next attempt
        
        # This should never be reached, but just in case
        return self._create_minimal_fallback(content)
    
    def handle_processing_errors(self, error: Exception, content: str, attempt: int) -> str:
        """Handle and recover from processing errors with fallback strategies.
        
        Args:
            error (Exception): The error that occurred
            content (str): Original content being processed
            attempt (int): Current attempt number
            
        Returns:
            str: Fallback content or re-raised exception
        """
        try:
            error_type = type(error).__name__
            error_msg = str(error)
            
            self.logger.error(f"Processing error (attempt {attempt}): {error_type} - {error_msg}")
            
            # Rate limit error handling
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                self.logger.warning("Rate limit detected, implementing exponential backoff")
                wait_time = min(60, 2 ** attempt)
                time.sleep(wait_time)
                raise error  # Re-raise to trigger retry
            
            # Token limit error handling
            elif "token" in error_msg.lower() and "limit" in error_msg.lower():
                self.logger.warning("Token limit exceeded, attempting content truncation")
                if len(content) > 4000:
                    truncated_content = content[:4000] + "\n\n[Content truncated due to length]"
                    return self._create_fallback_structure(truncated_content)
                
            # API key or authentication errors
            elif "api" in error_msg.lower() and ("key" in error_msg.lower() or "auth" in error_msg.lower()):
                self.logger.error("API authentication error - check API key")
                raise error  # Don't retry auth errors
            
            # Network/connection errors
            elif any(term in error_msg.lower() for term in ["connection", "network", "timeout"]):
                self.logger.warning("Network error detected, will retry")
                raise error  # Re-raise to trigger retry
            
            # Content parsing errors
            elif "json" in error_msg.lower() or "parse" in error_msg.lower():
                self.logger.warning("Content parsing error, using fallback structure")
                return self._create_fallback_structure(content)
            
            # Unknown errors - create fallback
            else:
                self.logger.warning(f"Unknown error, creating fallback structure: {error_type}")
                return self._create_fallback_structure(content)
                
        except Exception as fallback_error:
            self.logger.error(f"Error in error handling: {str(fallback_error)}")
            return self._create_minimal_fallback(content)
    
    def _create_fallback_structure(self, content: str) -> str:
        """Create a basic structured fallback when AI processing fails.
        
        Args:
            content (str): Original content
            
        Returns:
            str: Basic structured content
        """
        try:
            # Extract basic information inline
            title = "Service Document"
            lines = content.split('\n')
            for line in lines[:10]:  # Check first 10 lines
                line = line.strip()
                if line and len(line) < 100:
                    # Look for title-like patterns
                    if any(keyword in line.lower() for keyword in ['celcom', 'digi', 'roaming', 'plan', 'service']):
                        title = line
                        break
            
            # Extract provider inline
            content_lower = content.lower()
            if 'celcomdigi' in content_lower:
                provider = 'CelcomDigi'
            elif 'celcom' in content_lower:
                provider = 'Celcom'
            elif 'digi' in content_lower:
                provider = 'Digi'
            else:
                provider = 'CelcomDigi'
            
            fallback_content = f"""# {title}
## Document Information

- **Title**: {title}
- **Document Type**: Service Document
- **Last Updated**: Date not available in source document
- **Version**: Version not available in source document
- **Provider**: {provider}

## Key Features

- Service information available in source document
- Features and capabilities as described in original content
- Additional details available through customer service

## Detailed Information

### Service Overview

{content[:1000]}{"..." if len(content) > 1000 else ""}

## Pricing Information

| Plan/Package | Price | Details |
|--------------|-------|---------|
| Service Plan | See original document | Contact customer service for current pricing |

## Eligibility

- Eligibility requirements as specified in source document
- Contact customer service for detailed requirements

## How to Subscribe

1. Review service details in original document
2. Contact customer service for subscription process
3. Complete required documentation
4. Service activation as per terms

## Terms and Conditions

- Terms and conditions as specified in source document
- Subject to current service agreements
- Contact customer service for complete terms

## FAQ

**Q: How do I get more information about this service?**
A: Please contact customer service for detailed information.

**Q: What are the current pricing details?**
A: Pricing information is available through customer service channels.

## Customer Support

- Contact information available through official channels
- Customer service for detailed inquiries
- Support as per service terms
- Links to official support pages

*Note: This document was generated using fallback processing due to technical limitations. Please refer to original source for complete information.*
"""
            
            self.logger.info("Fallback structure created successfully")
            return fallback_content
            
        except Exception as e:
            self.logger.error(f"Error creating fallback structure: {str(e)}")
            return self._create_minimal_fallback(content)
    
    def _create_minimal_fallback(self, content: str) -> str:
        """Create minimal fallback content when all else fails."""
        return f"""# Document Processing Error

## Content Summary

The original document could not be fully processed due to technical limitations.

## Original Content (Partial)

{content[:500]}{"..." if len(content) > 500 else ""}

## Next Steps

Please contact technical support for assistance with this document.
"""
    
    # REDUNDANT METHOD REMOVED - Access usage_tracker.get_usage_summary() directly
    
    def log_usage_summary(self):
        """Log final API usage summary."""
        self.usage_tracker.log_session_summary()
