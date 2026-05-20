"""
Document Conversion Pipeline
Main entry point for converting Word documents to structured markdown format.
"""

import logging
import sys
import os
import argparse
from pathlib import Path
import io

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.document_extractor import DocumentExtractor
from src.ai_processor import AIProcessor
from src.template_generator import TemplateGenerator
from src.file_manager import FileManager
import config


def safe_print(message):
    """Print message with emoji fallback for Windows compatibility."""
    try:
        print(message)
    except UnicodeEncodeError:
        # Replace emojis with text equivalents for Windows compatibility
        emoji_replacements = {
            '🚀': '[START]',
            '📄': '[DOC]',
            '📁': '[FOLDER]',
            '✅': '[OK]',
            '❌': '[ERROR]',
            '⚠️': '[WARNING]',
            '🔍': '[SEARCH]',
            '📋': '[LIST]',
            '🎯': '[TARGET]',
            '📊': '[STATS]',
            '⚙️': '[SETTINGS]',
            '🧪': '[TEST]',
            '💾': '[SAVE]',
            '🤖': '[AI]',
            '💰': '[COST]',
            '🔧': '[FIX]',
            '👋': '[BYE]',
            '📑': '[DOCX]',
            '📝': '[FORMAT]'
        }
        
        safe_message = message
        for emoji, replacement in emoji_replacements.items():
            safe_message = safe_message.replace(emoji, replacement)
        
        print(safe_message)


def setup_logging():
    """Configure logging for the application with Unicode support."""
    os.makedirs(config.LOG_FOLDER, exist_ok=True)
    
    # Create custom formatter that handles Unicode safely
    class SafeFormatter(logging.Formatter):
        def format(self, record):
            try:
                return super().format(record)
            except UnicodeEncodeError:
                # Remove or replace problematic Unicode characters
                msg = record.getMessage()
                emoji_replacements = {
                    '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARNING]',
                    '🚀': '[START]', '📄': '[DOC]', '📁': '[FOLDER]',
                    '🤖': '[AI]', '💾': '[SAVE]', '📊': '[STATS]'
                }
                for emoji, replacement in emoji_replacements.items():
                    msg = msg.replace(emoji, replacement)
                record.msg = msg
                return super().format(record)
    
    # Create file handler with UTF-8 encoding
    file_handler = logging.FileHandler(config.LOG_FILE, encoding='utf-8')
    file_handler.setFormatter(SafeFormatter(config.LOG_FORMAT))
    
    # Create console handler with safe output
    console_handler = logging.StreamHandler(sys.stdout)
    if os.name == 'nt':  # Windows
        # Use a custom stream wrapper for Windows
        class SafeStreamWrapper:
            def __init__(self, stream):
                self.stream = stream
                
            def write(self, data):
                try:
                    self.stream.write(data)
                except UnicodeEncodeError:
                    # Replace problematic characters and retry
                    safe_data = data.encode('ascii', errors='replace').decode('ascii')
                    self.stream.write(safe_data)
                    
            def flush(self):
                self.stream.flush()
        
        console_handler.stream = SafeStreamWrapper(sys.stdout)
    
    console_handler.setFormatter(SafeFormatter(config.LOG_FORMAT))
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        handlers=[file_handler, console_handler]
    )
    
    return logging.getLogger(__name__)


class DocumentConversionPipeline:
    """Main pipeline for document conversion."""
    
    def __init__(self):
        self.logger = setup_logging()
        self.logger.info("Initializing Document Conversion Pipeline")
        
        # Validate configuration
        try:
            config.validate_config()
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            sys.exit(1)
        
        # Initialize components
        self.document_extractor = DocumentExtractor()
        self.ai_processor = AIProcessor(config.OPENAI_API_KEY)
        self.template_generator = TemplateGenerator(config.TEMPLATE_FILE)
        self.file_manager = FileManager(config.INPUT_FOLDER, config.OUTPUT_FOLDER)
        
        self.logger.info("Pipeline initialization complete")
    
    def convert_single_document(self, file_path: str) -> str:
        """Convert a single document.
        
        Args:
            file_path (str): Path to the document to convert
            
        Returns:
            str: Path to the converted document
        """
        try:
            self.logger.info(f"🚀 Converting document: {os.path.basename(file_path)}")
            
            # Step 1: Extract content from document
            self.logger.info("📄 Step 1: Extracting document content...")
            document_summary = self.document_extractor.get_document_summary(file_path)
            content = document_summary['cleaned_text']
            hyperlinks = document_summary.get('hyperlinks', [])
            
            if not content.strip():
                raise ValueError("No content extracted from document")
            
            # Log extraction results including hyperlinks
            stats = document_summary['summary_stats']
            self.logger.info(f"✓ Content extracted: {len(content)} chars, {stats['total_words']} words")
            self.logger.info(f"✓ Found {stats['total_tables']} tables and {stats['total_links']} hyperlinks")
            
            # Step 2: Load template
            self.logger.info("📋 Step 2: Loading template...")
            template = self.template_generator.load_template()
            self.logger.info("✓ Template loaded successfully")
            
            # Step 3: Enhanced AI processing with hyperlinks and document context
            self.logger.info("🤖 Step 3: AI content structuring with hyperlinks preservation...")
            
            # Create enhanced context for AI processing
            processing_context = {
                'content': content,
                'template': template,
                'document_summary': document_summary,
                'hyperlinks': hyperlinks,
                'metadata': document_summary['metadata']
            }
            
            # Debug hyperlinks data structure
            self.logger.debug(f"Hyperlinks variable type: {type(hyperlinks)}, value: {hyperlinks}")
            
            # Log hyperlink processing status
            if hyperlinks and len(hyperlinks) > 0:
                self.logger.info(f"🔗 Processing {len(hyperlinks)} hyperlinks found in document")
                for i, link in enumerate(hyperlinks[:3], 1):  # Log first 3 links as examples
                    self.logger.info(f"  Link {i}: '{link['text']}' -> {link['url']} [{link['type']}]")
                if len(hyperlinks) > 3:
                    self.logger.info(f"  ... and {len(hyperlinks) - 3} more hyperlinks")
            else:
                self.logger.info(f"📝 No hyperlinks found in document (hyperlinks={hyperlinks})")
            
            # Multi-level AI processing with hyperlink support
            structured_content = None
            processing_method = None
            
            # Choose optimal processing method based on hyperlink presence
            if hyperlinks and len(hyperlinks) > 0:
                self.logger.info(f"🔗 Hyperlinks detected ({len(hyperlinks)}), using hyperlink-aware processing priority")
                
                # For documents with hyperlinks, prioritize hyperlink-specific processing
                try:
                    self.logger.info("🔧 Attempting hyperlink-aware recommendation processing...")
                    structured_content = self.ai_processor.structure_content_with_recommendations(
                        processing_context['content'], 
                        processing_context['template'], 
                        hyperlinks
                    )
                    processing_method = "hyperlink-recommendation-based"
                    self.logger.info("✓ Hyperlink-aware recommendation processing completed successfully")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Hyperlink-aware recommendation processing failed: {str(e)}")
                    
                    # Try dedicated hyperlink processing as priority fallback
                    try:
                        self.logger.info("🔧 Attempting dedicated hyperlink processing...")
                        structured_content = self.ai_processor.structure_content_with_hyperlinks(
                            processing_context['content'], 
                            processing_context['template'], 
                            hyperlinks
                        )
                        processing_method = "hyperlink-enhanced"
                        self.logger.info("✓ Dedicated hyperlink processing completed successfully")
                        
                    except Exception as e2:
                        self.logger.warning(f"⚠️ Dedicated hyperlink processing failed: {str(e2)}")
                        # Fall back to standard processing
                        structured_content = None
            else:
                self.logger.info("📝 No hyperlinks detected, using standard processing priority")
            
            # Standard processing fallback chain if hyperlink processing failed or no hyperlinks
            if not structured_content:
                # Try recommendation-aware processing first (most advanced)
                try:
                    self.logger.info("🎯 Attempting recommendation-based AI processing...")
                    structured_content = self.ai_processor.structure_content_with_recommendations(
                        processing_context['content'], 
                        processing_context['template'], 
                        hyperlinks
                    )
                    processing_method = "recommendation-based"
                    self.logger.info("✓ Recommendation-based AI processing completed successfully")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ Recommendation-based processing failed: {str(e)}")
                    
                    # Try adaptive processing as fallback
                    try:
                        self.logger.info("🔄 Attempting adaptive AI processing...")
                        structured_content = self.ai_processor.process_with_retry_adaptive(
                            processing_context['content'], 
                            processing_context['template'], 
                            max_retries=config.MAX_RETRIES, 
                            hyperlinks=hyperlinks
                        )
                        processing_method = "adaptive"
                        self.logger.info("✓ Adaptive AI processing completed successfully")
                        
                    except Exception as e2:
                        self.logger.warning(f"⚠️ Adaptive processing failed: {str(e2)}")
                        
                        # Use enhanced hyperlink processing as final fallback (if not already tried)
                        if processing_method != "hyperlink-enhanced":
                            try:
                                self.logger.info("🔧 Attempting enhanced hyperlink processing...")
                                structured_content = self.ai_processor.structure_content_with_hyperlinks(
                                    processing_context['content'], 
                                    processing_context['template'], 
                                    hyperlinks
                                )
                                processing_method = "hyperlink-enhanced"
                                self.logger.info("✓ Enhanced hyperlink processing completed successfully")
                                
                            except Exception as e3:
                                self.logger.error(f"❌ All AI processing methods failed: {str(e3)}")
                                # Create basic fallback structure
                                structured_content = self.ai_processor._create_fallback_structure(processing_context['content'])
                                processing_method = "fallback"
                                self.logger.warning("⚠️ Using basic fallback structure")
                        else:
                            self.logger.error(f"❌ All AI processing methods failed: {str(e2)}")
                            # Create basic fallback structure
                            structured_content = self.ai_processor._create_fallback_structure(processing_context['content'])
                            processing_method = "fallback"
                            self.logger.warning("⚠️ Using basic fallback structure")
            
            if not structured_content or not structured_content.strip():
                raise ValueError("AI processing failed to generate structured content")
            
            # Step 4: Validate result with enhanced feedback
            self.logger.info("✅ Step 4: Validating structured content...")
            is_valid, compliance_score, issues = self.ai_processor.validate_structure(structured_content)
            
            if is_valid:
                self.logger.info(f"✓ Content validation PASSED (Score: {compliance_score:.2f})")
            else:
                self.logger.warning(f"⚠️ Content validation FAILED (Score: {compliance_score:.2f})")
                if issues:
                    self.logger.warning(f"Issues found: {'; '.join(issues[:3])}")
                    if len(issues) > 3:
                        self.logger.warning(f"... and {len(issues) - 3} more issues")
                
                # Apply content fixes if possible
                self.logger.info("🔧 Attempting to fix content issues...")
                try:
                    fixed_content, remaining_issues = self.template_generator.validate_and_fix_content(structured_content)
                    
                    if len(remaining_issues) < len(issues):
                        structured_content = fixed_content
                        self.logger.info(f"✓ Fixed {len(issues) - len(remaining_issues)} issues")
                        self.logger.info(f"Remaining issues: {len(remaining_issues)}")
                    else:
                        self.logger.warning("Could not automatically fix content issues")
                except Exception as fix_error:
                    self.logger.warning(f"Content fixing failed: {str(fix_error)}")
            
            # Enhanced hyperlink validation if hyperlinks were found
            if hyperlinks:
                self.logger.info("🔗 Performing comprehensive hyperlink validation...")
                try:
                    # Validate hyperlink preservation
                    self.ai_processor._validate_hyperlink_preservation(structured_content, hyperlinks)
                    
                    # Count actual markdown links in the output
                    import re
                    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', structured_content)
                    preserved_count = len(markdown_links)
                    original_count = len(hyperlinks)
                    
                    if preserved_count == original_count:
                        self.logger.info(f"✅ Perfect hyperlink preservation: {preserved_count}/{original_count} links preserved")
                    elif preserved_count > 0:
                        self.logger.warning(f"⚠️ Partial hyperlink preservation: {preserved_count}/{original_count} links preserved")
                        # Log which links were preserved
                        preserved_urls = [url for text, url in markdown_links]
                        original_urls = [link['url'] for link in hyperlinks]
                        missing_urls = set(original_urls) - set(preserved_urls)
                        if missing_urls:
                            self.logger.warning(f"Missing URLs: {list(missing_urls)[:3]}{'...' if len(missing_urls) > 3 else ''}")
                    else:
                        self.logger.error(f"❌ No hyperlinks preserved in output despite {original_count} found in input")
                        
                    # If using hyperlink-aware processing method, expect better preservation
                    if processing_method in ["hyperlink-recommendation-based", "hyperlink-enhanced"]:
                        preservation_rate = preserved_count / original_count if original_count > 0 else 0
                        if preservation_rate < 0.8:  # Expect at least 80% preservation with hyperlink-aware methods
                            self.logger.warning(f"⚠️ Low hyperlink preservation rate ({preservation_rate:.1%}) for hyperlink-aware method")
                    
                except Exception as link_error:
                    self.logger.warning(f"⚠️ Hyperlink validation failed: {str(link_error)}")
            
            # Step 5: Save converted document in chosen format
            self.logger.info("💾 Step 5: Saving converted document...")
            original_filename = os.path.basename(file_path)
            base_filename = "converted_" + os.path.splitext(original_filename)[0]
            
            # Determine output format
            output_format = getattr(config, 'DEFAULT_OUTPUT_FORMAT', 'docx')
            self.logger.info(f"📁 Output format: {output_format}")
            
            # Save document(s)
            try:
                saved_files = self.template_generator.save_document_dual_format(
                    structured_content, base_filename, output_format
                )
                
                # Log the saved files
                for format_type, path in saved_files.items():
                    self.logger.info(f"✓ {format_type.upper()} saved to: {os.path.relpath(path)}")
                
                # For backward compatibility, return the primary output path
                primary_output = saved_files.get(output_format, next(iter(saved_files.values())))
                
            except Exception as save_error:
                self.logger.error(f"❌ Failed to save document: {str(save_error)}")
                # Create fallback save
                fallback_path = os.path.join(config.OUTPUT_FOLDER, f"{base_filename}.md")
                os.makedirs(os.path.dirname(fallback_path), exist_ok=True)
                with open(fallback_path, 'w', encoding='utf-8') as f:
                    f.write(structured_content)
                self.logger.info(f"✓ Fallback save to: {fallback_path}")
                primary_output = fallback_path
            
            # Step 6: Final quality check
            self.logger.info("📊 Step 6: Final quality validation...")
            try:
                final_is_valid, final_issues = self.template_generator.validate_markdown(structured_content)
                
                if final_is_valid:
                    self.logger.info("✓ Final validation PASSED")
                else:
                    self.logger.warning(f"⚠️ Final validation issues: {'; '.join(final_issues[:2])}")
                    if len(final_issues) > 2:
                        self.logger.warning(f"... and {len(final_issues) - 2} more issues")
            except Exception as validation_error:
                self.logger.warning(f"⚠️ Final validation failed: {str(validation_error)}")
            
            # Step 7: Log processing summary
            self.logger.info("📈 Processing Summary:")
            self.logger.info(f"  • Processing method: {processing_method}")
            self.logger.info(f"  • Content length: {len(structured_content)} characters")
            self.logger.info(f"  • Hyperlinks processed: {len(hyperlinks)}")
            self.logger.info(f"  • Validation score: {compliance_score:.2f}")
            
            # Log API usage for this conversion
            try:
                usage_summary = self.ai_processor.usage_tracker.get_usage_summary()
                self.logger.info(f"  • API calls: {usage_summary.get('total_api_calls', 0)}")
                self.logger.info(f"  • Token usage: {usage_summary.get('total_tokens', 0):,}")
                self.logger.info(f"  • Processing cost: ${usage_summary.get('total_cost', 0):.6f}")
            except Exception as usage_error:
                self.logger.warning(f"Could not retrieve usage statistics: {str(usage_error)}")
            
            self.logger.info(f"✅ Document conversion completed successfully: {os.path.relpath(primary_output)}")
            return primary_output
            
        except ValueError as ve:
            self.logger.error(f"❌ Validation error converting {file_path}: {str(ve)}")
            raise
        except FileNotFoundError as fe:
            self.logger.error(f"❌ File not found: {str(fe)}")
            raise
        except PermissionError as pe:
            self.logger.error(f"❌ Permission denied: {str(pe)}")
            raise
        except Exception as e:
            self.logger.error(f"❌ Unexpected error converting {file_path}: {str(e)}")
            self.logger.error(f"Error type: {type(e).__name__}")
            raise
    
    def convert_all_documents(self) -> list:
        """Convert all documents in the input folder.
        
        Returns:
            list: List of converted document paths
        """
        try:
            self.logger.info("🚀 Starting batch conversion of all documents")
            
            # Step 1: Scan for documents
            doc_files = self.file_manager.scan_documents()
            if not doc_files:
                self.logger.warning("No documents found in input folder")
                return []
            
            self.logger.info(f"📁 Found {len(doc_files)} documents to process")
            
            # Step 2: Validate files
            validation = self.file_manager.validate_input_files(doc_files)
            valid_files = validation['valid_files']
            
            if validation['invalid_count'] > 0:
                self.logger.warning(f"⚠️  {validation['invalid_count']} files are invalid and will be skipped")
                for invalid in validation['invalid_files']:
                    self.logger.warning(f"  - {invalid['file']}: {invalid['reason']}")
            
            self.logger.info(f"✅ Processing {len(valid_files)} valid files")
            
            # Step 3: Process each document
            converted_files = []
            failed_files = []
            
            for i, file_path in enumerate(valid_files, 1):
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📄 Processing {i}/{len(valid_files)}: {os.path.basename(file_path)}")
                self.logger.info(f"{'='*60}")
                
                try:
                    output_path = self.convert_single_document(file_path)
                    converted_files.append(output_path)
                    self.logger.info(f"✅ Success: {os.path.basename(output_path)}")
                    
                except Exception as e:
                    self.logger.error(f"❌ Failed to convert {os.path.basename(file_path)}: {str(e)}")
                    failed_files.append({
                        'file': file_path,
                        'error': str(e)
                    })
            
            # Step 4: Summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info("📊 CONVERSION SUMMARY")
            self.logger.info(f"{'='*60}")
            self.logger.info(f"✅ Successfully converted: {len(converted_files)} files")
            self.logger.info(f"❌ Failed conversions: {len(failed_files)} files")
            self.logger.info(f"📁 Total processed: {len(valid_files)} files")
            
            if failed_files:
                self.logger.info(f"\n❌ Failed files:")
                for failed in failed_files:
                    self.logger.info(f"  - {os.path.basename(failed['file'])}: {failed['error']}")
            
            # Step 5: Cleanup
            self.file_manager.cleanup_temp()
            
            # Step 6: Log API usage summary
            self.logger.info(f"\n{'='*60}")
            self.ai_processor.log_usage_summary()
            
            return converted_files
            
        except Exception as e:
            self.logger.error(f"❌ Batch conversion failed: {str(e)}")
            raise


def display_menu():
    """Display the main menu options."""
    safe_print("🚀 Document Conversion Pipeline")
    safe_print("=" * 50)
    safe_print("Select processing mode:")
    safe_print("1. 📄 Convert single document")
    safe_print("2. 📁 Batch convert all documents")
    safe_print("3. 🎯 Convert selected documents")
    safe_print("4. 📊 Show document list and status")
    safe_print("5. ⚙️  Change output format")
    safe_print("6. 🧪 Run tests")
    safe_print("7. ❌ Exit")
    safe_print("-" * 50)

def select_output_format():
    """Allow user to select output format."""
    import config
    
    current_format = getattr(config, 'DEFAULT_OUTPUT_FORMAT', 'docx')
    
    safe_print(f"\n📝 Current output format: {current_format.upper()}")
    safe_print("\nSelect output format:")
    safe_print("1. 📄 Markdown (.md) - For technical editing")
    safe_print("2. 📑 DOCX (.docx) - For stakeholder editing")
    safe_print("3. 📋 Both formats")
    safe_print("4. ← Back to main menu")
    
    try:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            config.DEFAULT_OUTPUT_FORMAT = "markdown"
            safe_print("✅ Output format set to Markdown")
        elif choice == "2":
            config.DEFAULT_OUTPUT_FORMAT = "docx"
            safe_print("✅ Output format set to DOCX")
        elif choice == "3":
            config.DEFAULT_OUTPUT_FORMAT = "both"
            safe_print("✅ Output format set to Both (Markdown + DOCX)")
        elif choice == "4":
            return
        else:
            safe_print("❌ Invalid choice. Please try again.")
            return select_output_format()
            
        safe_print(f"📁 Files will be saved to:")
        if config.DEFAULT_OUTPUT_FORMAT in ["markdown", "both"]:
            safe_print(f"   • Markdown: {config.MARKDOWN_OUTPUT_FOLDER}")
        if config.DEFAULT_OUTPUT_FORMAT in ["docx", "both"]:
            safe_print(f"   • DOCX: {config.DOCX_OUTPUT_FOLDER}")
        
    except KeyboardInterrupt:
        safe_print("\n\nOperation cancelled.")
        return

def show_document_list(file_manager):
    """Display available documents with indices."""
    safe_print("\n📋 Available Documents:")
    safe_print("-" * 80)
    
    doc_files = file_manager.scan_documents()
    if not doc_files:
        safe_print("❌ No documents found in docs/ folder")
        safe_print("💡 Supported formats: .docx, .pdf")
        return []
    
    for i, doc_path in enumerate(doc_files, 1):
        filename = os.path.basename(doc_path)
        file_size = os.path.getsize(doc_path) / (1024*1024)  # Size in MB
        file_ext = os.path.splitext(doc_path)[1].upper()
        
        # Add file type indicator
        if file_ext == '.PDF':
            type_indicator = "📄 PDF"
        elif file_ext == '.DOCX':
            type_indicator = "📑 DOCX"
        else:
            type_indicator = f"📋 {file_ext}"
        
        safe_print(f"{i:2d}. {type_indicator} {filename} ({file_size:.1f} MB)")
    
    safe_print("-" * 80)
    safe_print(f"Total: {len(doc_files)} documents (DOCX + PDF)")
    return doc_files

def convert_single_document_interactive(pipeline):
    """Interactive single document conversion."""
    safe_print("\n🔍 Single Document Conversion")
    safe_print("-" * 40)
    
    doc_files = show_document_list(pipeline.file_manager)
    if not doc_files:
        return
    
    while True:
        try:
            choice = input(f"\nSelect document (1-{len(doc_files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return
            
            index = int(choice) - 1
            if 0 <= index < len(doc_files):
                selected_file = doc_files[index]
                safe_print(f"\n🚀 Converting: {os.path.basename(selected_file)}")
                
                try:
                    output_path = pipeline.convert_single_document(selected_file)
                    safe_print(f"✅ Conversion successful!")
                    safe_print(f"📁 Output: {output_path}")
                    
                    # Show API usage for this conversion
                    usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
                    safe_print(f"\n💰 API Usage:")
                    safe_print(f"   Calls: {usage_summary['total_api_calls']}")
                    safe_print(f"   Cost: ${usage_summary['total_cost']:.6f}")
                    break
                    
                except Exception as e:
                    safe_print(f"❌ Conversion failed: {str(e)}")
                    break
            else:
                safe_print("❌ Invalid selection. Please try again.")
                
        except ValueError:
            safe_print("❌ Please enter a valid number or 'q' to quit.")

def convert_selected_documents_interactive(pipeline):
    """Interactive multi-document selection and conversion."""
    safe_print("\n🎯 Selected Documents Conversion")
    safe_print("-" * 45)
    
    doc_files = show_document_list(pipeline.file_manager)
    if not doc_files:
        return
    
    safe_print("\nSelection options:")
    safe_print("• Enter numbers separated by commas (e.g., 1,3,5)")
    safe_print("• Enter ranges with dash (e.g., 1-5)")
    safe_print("• Combine both (e.g., 1,3-5,8)")
    safe_print("• Enter 'all' for all documents")
    safe_print("• Enter 'q' to quit")
    
    while True:
        selection = input("\nYour selection: ").strip()
        
        if selection.lower() == 'q':
            return
        elif selection.lower() == 'all':
            selected_files = doc_files
            break
        else:
            try:
                selected_files = parse_selection(selection, doc_files)
                if selected_files:
                    break
                else:
                    safe_print("❌ No valid selections made. Please try again.")
            except Exception as e:
                safe_print(f"❌ Invalid selection format: {str(e)}")
                safe_print("Please use format like: 1,3,5 or 1-5 or 1,3-5,8")
    
    # Show selected files for confirmation
    safe_print(f"\n📋 Selected {len(selected_files)} documents:")
    for i, file_path in enumerate(selected_files, 1):
        safe_print(f"{i:2d}. {os.path.basename(file_path)}")
    
    confirm = input("\nProceed with conversion? (y/n): ").strip().lower()
    if confirm != 'y':
        safe_print("❌ Conversion cancelled.")
        return
    
    # Convert selected documents
    safe_print(f"\n🚀 Converting {len(selected_files)} documents...")
    converted_files = []
    failed_files = []
    
    for i, file_path in enumerate(selected_files, 1):
        safe_print(f"\n📄 Processing {i}/{len(selected_files)}: {os.path.basename(file_path)}")
        try:
            output_path = pipeline.convert_single_document(file_path)
            converted_files.append(output_path)
            safe_print(f"✅ Success: {os.path.basename(output_path)}")
        except Exception as e:
            failed_files.append((file_path, str(e)))
            safe_print(f"❌ Failed: {str(e)}")
    
    # Show results
    safe_print(f"\n📊 Conversion Results:")
    safe_print(f"✅ Successful: {len(converted_files)}")
    safe_print(f"❌ Failed: {len(failed_files)}")
    
    if failed_files:
        safe_print(f"\n❌ Failed files:")
        for file_path, error in failed_files:
            safe_print(f"  - {os.path.basename(file_path)}: {error}")
    
    # Show API usage summary
    usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
    safe_print(f"\n💰 API Usage Summary:")
    safe_print(f"   Total Calls: {usage_summary['total_api_calls']}")
    safe_print(f"   Total Cost: ${usage_summary['total_cost']:.6f}")
    if converted_files:
        safe_print(f"   Average Cost per Document: ${usage_summary['total_cost']/len(converted_files):.6f}")

def parse_selection(selection, doc_files):
    """Parse user selection string into list of files."""
    selected_indices = set()
    
    # Split by commas
    parts = selection.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            # Handle ranges
            start, end = part.split('-', 1)
            start_idx = int(start.strip()) - 1
            end_idx = int(end.strip()) - 1
            
            if 0 <= start_idx <= end_idx < len(doc_files):
                selected_indices.update(range(start_idx, end_idx + 1))
            else:
                raise ValueError(f"Range {part} is out of bounds")
        else:
            # Handle single numbers
            idx = int(part) - 1
            if 0 <= idx < len(doc_files):
                selected_indices.add(idx)
            else:
                raise ValueError(f"Index {part} is out of bounds")
    
    return [doc_files[i] for i in sorted(selected_indices)]

def run_tests_interactive():
    """Run the test runner interactively."""
    safe_print("\n🧪 Running Test Suite...")
    safe_print("-" * 30)
    
    try:
        import subprocess
        result = subprocess.run([sys.executable, 'run_tests.py'], capture_output=False)
        return result.returncode == 0
    except Exception as e:
        safe_print(f"❌ Failed to run tests: {str(e)}")
        return False

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Document Conversion Pipeline - Convert Word documents to structured markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Interactive mode
  python main.py --batch                   # Convert all documents
  python main.py --file "document.docx"    # Convert single document
  python main.py --select 1,3,5            # Convert selected documents by index
  python main.py --select 1-5              # Convert documents 1 through 5
  python main.py --list                    # List available documents
  python main.py --tests                   # Run test suite
        """
    )
    
    parser.add_argument('--batch', action='store_true',
                       help='Convert all documents in batch mode')
    parser.add_argument('--file', type=str,
                       help='Convert a single document by filename')
    parser.add_argument('--select', type=str,
                       help='Convert selected documents (e.g., "1,3,5" or "1-5")')
    parser.add_argument('--list', action='store_true',
                       help='List all available documents')
    parser.add_argument('--tests', action='store_true',
                       help='Run the test suite')
    parser.add_argument('--output', type=str,
                       help='Specify output directory (default: converted_docs)')
    parser.add_argument('--quiet', action='store_true',
                       help='Suppress verbose output')
    
    return parser.parse_args()

def run_command_line_mode(args):
    """Run in command-line mode based on arguments."""
    try:
        if args.list:
            # List documents
            file_manager = FileManager()
            doc_files = show_document_list(file_manager)
            return True
            
        elif args.tests:
            # Run tests
            return run_tests_interactive()
            
        elif args.batch:
            # Batch convert all documents
            safe_print("🚀 Batch Converting All Documents")
            pipeline = DocumentConversionPipeline()
            
            if not args.quiet:
                doc_files = pipeline.file_manager.scan_documents()
                safe_print(f"Found {len(doc_files)} documents to convert.")
            
            converted_files = pipeline.convert_all_documents()
            
            # Display summary
            usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
            safe_print(f"✅ Converted {len(converted_files)} documents")
            if not args.quiet:
                safe_print(f"📂 Output folder: {config.OUTPUT_FOLDER}")
                safe_print(f"💰 Total cost: ${usage_summary['total_cost']:.6f}")
            return True
            
        elif args.file:
            # Convert single file
            pipeline = DocumentConversionPipeline()
            
            # Find the file
            doc_files = pipeline.file_manager.scan_documents()
            target_file = None
            
            for doc_file in doc_files:
                if os.path.basename(doc_file) == args.file or doc_file == args.file:
                    target_file = doc_file
                    break
            
            if not target_file:
                safe_print(f"❌ File not found: {args.file}")
                return False
            
            safe_print(f"🚀 Converting: {os.path.basename(target_file)}")
            output_path = pipeline.convert_single_document(target_file)
            
            usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
            safe_print(f"✅ Conversion successful: {output_path}")
            if not args.quiet:
                safe_print(f"💰 Cost: ${usage_summary['total_cost']:.6f}")
            return True
            
        elif args.select:
            # Convert selected documents
            pipeline = DocumentConversionPipeline()
            doc_files = pipeline.file_manager.scan_documents()
            
            try:
                selected_files = parse_selection(args.select, doc_files)
                safe_print(f"🚀 Converting {len(selected_files)} selected documents")
                
                converted_files = []
                for i, file_path in enumerate(selected_files, 1):
                    if not args.quiet:
                        safe_print(f"📄 Processing {i}/{len(selected_files)}: {os.path.basename(file_path)}")
                    
                    try:
                        output_path = pipeline.convert_single_document(file_path)
                        converted_files.append(output_path)
                    except Exception as e:
                        safe_print(f"❌ Failed: {os.path.basename(file_path)} - {str(e)}")
                
                usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
                safe_print(f"✅ Converted {len(converted_files)} documents")
                if not args.quiet:
                    safe_print(f"💰 Total cost: ${usage_summary['total_cost']:.6f}")
                return True
                
            except Exception as e:
                safe_print(f"❌ Invalid selection format: {str(e)}")
                return False
        else:
            # No arguments provided, show help
            safe_print("No command specified. Use --help for usage information or run without arguments for interactive mode.")
            return False
            
    except Exception as e:
        print(f"❌ Command execution failed: {str(e)}")
        return False

def main():
    """Main function with support for both interactive and command-line modes."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Check if any command-line arguments were provided
        if any([args.batch, args.file, args.select, args.list, args.tests]):
            # Run in command-line mode
            success = run_command_line_mode(args)
            sys.exit(0 if success else 1)
        else:
            # Run in interactive mode
            main_interactive()
            
    except KeyboardInterrupt:
        safe_print("\n\n⚠️ Program interrupted by user. Goodbye!")
        sys.exit(0)
    except Exception as e:
        safe_print(f"\n❌ Unexpected error: {e}")
        logging.error(f"Main program error: {e}")
        sys.exit(1)

def main_interactive():
    """Interactive mode main function."""
    try:
        while True:
            display_menu()
            choice = input("Enter your choice (1-7): ").strip()
            
            if choice == '1':
                # Single document conversion
                pipeline = DocumentConversionPipeline()
                convert_single_document_interactive(pipeline)
                
            elif choice == '2':
                # Batch convert all documents
                safe_print("\n📁 Batch Converting All Documents")
                safe_print("-" * 40)
                pipeline = DocumentConversionPipeline()
                
                doc_files = pipeline.file_manager.scan_documents()
                if not doc_files:
                    safe_print("❌ No documents found in docs/ folder")
                    continue
                
                safe_print(f"Found {len(doc_files)} documents to convert.")
                confirm = input("Proceed with batch conversion? (y/n): ").strip().lower()
                
                if confirm == 'y':
                    safe_print("\n🚀 Starting batch conversion...")
                    converted_files = pipeline.convert_all_documents()
                    
                    # Display final summary
                    usage_summary = pipeline.ai_processor.usage_tracker.get_usage_summary()
                    safe_print(f"\n✅ Batch conversion complete!")
                    safe_print(f"📁 Converted {len(converted_files)} documents")
                    safe_print(f"📂 Output folder: {config.OUTPUT_FOLDER}")
                    safe_print(f"\n💰 API Usage Summary:")
                    safe_print(f"   Total API Calls: {usage_summary['total_api_calls']}")
                    safe_print(f"   Total Tokens: {usage_summary['total_tokens']:,}")
                    safe_print(f"   Total Cost: ${usage_summary['total_cost']:.6f}")
                    if converted_files:
                        safe_print(f"   Average Cost per Document: ${usage_summary['total_cost']/len(converted_files):.6f}")
                else:
                    safe_print("❌ Batch conversion cancelled.")
                
            elif choice == '3':
                # Convert selected documents
                pipeline = DocumentConversionPipeline()
                convert_selected_documents_interactive(pipeline)
                
            elif choice == '4':
                # Show document list and status
                file_manager = FileManager()
                show_document_list(file_manager)
                
                # Check for existing converted files
                converted_dir = Path(config.OUTPUT_FOLDER)
                if converted_dir.exists():
                    converted_files = list(converted_dir.glob('converted_*.md'))
                    safe_print(f"\n📁 Already converted: {len(converted_files)} files")
                    if converted_files:
                        safe_print("Converted files:")
                        for i, file_path in enumerate(converted_files[:10], 1):  # Show first 10
                            safe_print(f"  {i}. {file_path.name}")
                        if len(converted_files) > 10:
                            safe_print(f"  ... and {len(converted_files) - 10} more")
                
            elif choice == '5':
                # Change output format
                select_output_format()
                
            elif choice == '6':
                # Run tests
                run_tests_interactive()
                
            elif choice == '7':
                # Exit
                safe_print("\n👋 Goodbye!")
                break
                
            else:
                safe_print("❌ Invalid choice. Please select 1-7.")
            
            # Wait for user input before showing menu again
            if choice in ['1', '2', '3']:
                input("\nPress Enter to continue...")
            
    except KeyboardInterrupt:
        safe_print("\n\n⚠️ Program interrupted by user. Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()