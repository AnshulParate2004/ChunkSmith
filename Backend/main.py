from pathlib import Path
from unstructured.partition.pdf import partition_pdf
import os
import json
import pickle

class PDFPartitioner:
    """Handles PDF partitioning with configurable options"""
    
    # Fixed image output directory
    IMAGE_OUTPUT_DIR = r"D:\MultiModulRag\Backend\SmartChunkClubing\Images"
    
    # Supported languages mapping
    SUPPORTED_LANGUAGES = {
        "afrikaans": "afr", "amharic": "amh", "arabic": "ara", "assamese": "asm",
        "azerbaijani": "aze", "azerbaijani_cyrilic": "aze_cyrl", "belarusian": "bel",
        "bengali": "ben", "tibetan": "bod", "bosnian": "bos", "breton": "bre",
        "bulgarian": "bul", "catalan": "cat", "cebuano": "ceb", "czech": "ces",
        "chinese_simplified": "chi_sim", "chinese": "chi_sim", "chinese_traditional": "chi_tra",
        "cherokee": "chr", "corsican": "cos", "welsh": "cym", "danish": "dan",
        "danish_fraktur": "dan_frak", "german": "deu", "german_fraktur": "deu_frak",
        "dzongkha": "dzo", "greek": "ell", "english": "eng", "esperanto": "epo",
        "estonian": "est", "basque": "eus", "persian": "fas", "filipino": "fil",
        "finnish": "fin", "french": "fra", "german_fraktur": "frk", "western_frisian": "fry",
        "scottish_gaelic": "gla", "irish": "gle", "galician": "glg", "gujarati": "guj",
        "haitian": "hat", "hebrew": "heb", "hindi": "hin", "croatian": "hrv",
        "hungarian": "hun", "armenian": "hye", "indonesian": "ind", "icelandic": "isl",
        "italian": "ita", "javanese": "jav", "japanese": "jpn", "kannada": "kan",
        "georgian": "kat", "kazakh": "kaz", "khmer": "khm", "korean": "kor",
        "lao": "lao", "latin": "lat", "latvian": "lav", "lithuanian": "lit",
        "malayalam": "mal", "marathi": "mar", "macedonian": "mkd", "maltese": "mlt",
        "mongolian": "mon", "malay": "msa", "burmese": "mya", "nepali": "nep",
        "dutch": "nld", "norwegian": "nor", "polish": "pol", "portuguese": "por",
        "pashto": "pus", "romanian": "ron", "russian": "rus", "sanskrit": "san",
        "sinhala": "sin", "slovak": "slk", "slovenian": "slv", "spanish": "spa",
        "albanian": "sqi", "serbian": "srp", "swedish": "swe", "tamil": "tam",
        "telugu": "tel", "thai": "tha", "turkish": "tur", "ukrainian": "ukr",
        "urdu": "urd", "uzbek": "uzb", "vietnamese": "vie", "yiddish": "yid"
    }
    
    def __init__(
        self,
        language: str,
        max_characters: int,
        new_after_n_chars: int,
        combine_text_under_n_chars: int,
        extract_images: bool = False,
        extract_tables: bool = False
    ):
        """
        Initialize PDF Partitioner
        
        Args:
            language: Language name (e.g., 'english', 'spanish', 'hindi') - REQUIRED
            max_characters: Maximum characters per chunk - REQUIRED
            new_after_n_chars: Start new chunk after this many characters - REQUIRED
            combine_text_under_n_chars: Combine small text blocks under this count - REQUIRED
            extract_images: Whether to extract images from PDF (default: False)
            extract_tables: Whether to parse tables as structured HTML (default: False)
        """
        # Language configuration (required)
        self.language = self._validate_language(language)
        
        # Chunking configuration (all required)
        self.max_characters = max_characters
        self.new_after_n_chars = new_after_n_chars
        self.combine_text_under_n_chars = combine_text_under_n_chars
        
        # Optional features
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        
        # Image output directory
        self.image_output_dir = Path(self.IMAGE_OUTPUT_DIR)
        
        # Create image directory if image extraction is enabled
        if self.extract_images:
            self.image_output_dir.mkdir(parents=True, exist_ok=True)
    
    def _validate_language(self, language: str) -> str:
        """Validate and convert language name to code"""
        lang_lower = language.lower().replace(" ", "_").replace("-", "_")
        
        if lang_lower in self.SUPPORTED_LANGUAGES:
            return self.SUPPORTED_LANGUAGES[lang_lower]
        else:
            raise ValueError(
                f"❌ Unsupported language '{language}'.\n"
                f"   Use PDFPartitioner.get_supported_languages() to see valid options.\n"
                f"   Examples: english, hindi, spanish, french, etc."
            )
    
    def partition_document(self, file_path: str):
        """
        Extract elements from PDF using unstructured
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of extracted elements
        """
        print(f"\n📄 Partitioning document: {file_path}")
        print(f"   Language: {self.language}")
        print(f"   Extract images: {self.extract_images}")
        print(f"   Extract tables: {self.extract_tables}")
        print(f"   Chunking: max={self.max_characters}, new_after={self.new_after_n_chars}, combine_under={self.combine_text_under_n_chars}")
        
        # Build partition parameters
        partition_params = {
            # Core parameters (always required)
            "filename": file_path,
            "strategy": "hi_res",
            "hi_res_model_name": "yolox",
            "chunking_strategy": "by_title",
            "include_orig_elements": True,
            
            # Language configuration
            "languages": [self.language],
            
            # Chunking parameters
            "max_characters": self.max_characters,
            "new_after_n_chars": self.new_after_n_chars,
            "combine_text_under_n_chars": self.combine_text_under_n_chars,
        }
        
        # Add image extraction parameters if enabled
        if self.extract_images:
            partition_params.update({
                "extract_images_in_pdf": True,
                "extract_image_block_to_payload": True,
                "extract_image_block_output_dir": str(self.image_output_dir),
                "extract_image_block_types": ["Image"],
            })
        
        # Add table extraction parameter if enabled
        if self.extract_tables:
            partition_params["infer_table_structure"] = True
        
        # Partition the PDF
        elements = partition_pdf(**partition_params)
        
        print(f"✅ Extracted {len(elements)} elements\n")
        return elements
    
    @classmethod
    def get_supported_languages(cls) -> list:
        """Get list of all supported language names"""
        return sorted(cls.SUPPORTED_LANGUAGES.keys())
    
    @classmethod
    def from_terminal_input(cls):
        """Create PDFPartitioner instance from terminal input with full validation"""
        print("\n" + "=" * 70)
        print(" " * 20 + "PDF PARTITIONER CONFIGURATION")
        print("=" * 70)
        
        # ============ PDF FILE PATH ============
        print("\n📁 PDF FILE PATH:")
        while True:
            pdf_path = input("  Enter PDF file path: ").strip()
            
            if not pdf_path:
                print("  ❌ Error: Path cannot be empty. Please try again.\n")
                continue
            
            if not os.path.exists(pdf_path):
                print(f"  ❌ Error: File does not exist: {pdf_path}")
                retry = input("  Do you want to try again? (yes/no): ").strip().lower()
                if retry not in ['yes', 'y']:
                    raise FileNotFoundError(f"PDF file not found: {pdf_path}")
                continue
            
            if not pdf_path.lower().endswith('.pdf'):
                print("  ⚠️  Warning: File does not have .pdf extension")
                proceed = input("  Do you want to proceed anyway? (yes/no): ").strip().lower()
                if proceed not in ['yes', 'y']:
                    continue
            
            print(f"  ✅ File found: {pdf_path}\n")
            break
        
        # ============ LANGUAGE CONFIGURATION ============
        print("📚 LANGUAGE CONFIGURATION:")
        print(f"  Available languages (showing first 10): {', '.join(cls.get_supported_languages()[:10])}...")
        print(f"  Total {len(cls.SUPPORTED_LANGUAGES)} languages supported")
        print("  Examples: english, hindi, spanish, french, german, japanese, chinese\n")
        
        while True:
            language = input("  Enter language: ").strip()
            
            if not language:
                print("  ❌ Error: Language cannot be empty. Please try again.\n")
                continue
            
            lang_lower = language.lower().replace(" ", "_").replace("-", "_")
            if lang_lower not in cls.SUPPORTED_LANGUAGES:
                print(f"  ❌ Error: Unsupported language '{language}'")
                print("     Type 'list' to see all languages, or try again")
                choice = input("  Your choice: ").strip().lower()
                
                if choice == 'list':
                    print("\n  Supported languages:")
                    langs = cls.get_supported_languages()
                    for i in range(0, len(langs), 5):
                        print("    " + ", ".join(langs[i:i+5]))
                    print()
                continue
            
            print(f"  ✅ Language set: {language}\n")
            break
        
        # ============ CHUNKING PARAMETERS ============
        print("📏 CHUNKING CONFIGURATION (All Required):")
        
        while True:
            try:
                max_characters = int(input("  Max characters per chunk: ").strip())
                if max_characters <= 0:
                    print("  ❌ Error: Must be a positive number\n")
                    continue
                break
            except ValueError:
                print("  ❌ Error: Please enter a valid integer\n")
        
        while True:
            try:
                new_after_n_chars = int(input("  Start new chunk after N chars: ").strip())
                if new_after_n_chars <= 0:
                    print("  ❌ Error: Must be a positive number\n")
                    continue
                break
            except ValueError:
                print("  ❌ Error: Please enter a valid integer\n")
        
        while True:
            try:
                combine_text_under_n_chars = int(input("  Combine text blocks under N chars: ").strip())
                if combine_text_under_n_chars < 0:
                    print("  ❌ Error: Must be a non-negative number\n")
                    continue
                break
            except ValueError:
                print("  ❌ Error: Please enter a valid integer\n")
        
        print(f"  ✅ Chunking configured\n")
        
        # ============ OPTIONAL FEATURES ============
        print("🔧 OPTIONAL FEATURES:")
        
        # Image extraction
        extract_images = input("  Do you want to extract images? (yes/no): ").strip().lower() in ['yes', 'y']
        if extract_images:
            print(f"  ✅ Images will be saved to: {cls.IMAGE_OUTPUT_DIR}")
        
        # Table extraction
        extract_tables = input("  Do you want to extract tables? (yes/no): ").strip().lower() in ['yes', 'y']
        if extract_tables:
            print("  ✅ Tables will be extracted as structured HTML")
        
        print("\n" + "=" * 70)
        print("✅ Configuration Complete!")
        print("=" * 70 + "\n")
        
        # Create instance
        partitioner = cls(
            language=language,
            max_characters=max_characters,
            new_after_n_chars=new_after_n_chars,
            combine_text_under_n_chars=combine_text_under_n_chars,
            extract_images=extract_images,
            extract_tables=extract_tables
        )
        
        # Return both partitioner and pdf_path
        return partitioner, pdf_path
    
    def get_config_summary(self) -> dict:
        """Get current configuration as dictionary"""
        return {
            "language": self.language,
            "extract_images": self.extract_images,
            "extract_tables": self.extract_tables,
            "image_output_dir": str(self.image_output_dir),
            "chunking": {
                "max_characters": self.max_characters,
                "new_after_n_chars": self.new_after_n_chars,
                "combine_text_under_n_chars": self.combine_text_under_n_chars
            }
        }


# ✅ USAGE EXAMPLE - Interactive Terminal Mode

if __name__ == "__main__":
    try:
        # Get configuration and PDF path from terminal
        partitioner, pdf_path = PDFPartitioner.from_terminal_input()
        
        # Process the document
        elements = partitioner.partition_document(pdf_path)
        
        print("🎉 Processing completed successfully!")
        print(f"📊 Summary: {len(elements)} elements extracted")

        # Define output directories
        json_dir = r"D:\MultiModulRag\Backend\SmartChunkClubing\JSON"
        pickle_dir = r"D:\MultiModulRag\Backend\SmartChunkClubing\Pickel"

        # Create directories if they don’t exist
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(pickle_dir, exist_ok=True)

        # Extract filename (without extension)
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        # Define output paths
        json_path = os.path.join(json_dir, f"{base_name}.json")
        pickle_path = os.path.join(pickle_dir, f"{base_name}.pkl")

        # Dump to JSON
        try:
            with open(json_path, "w", encoding="utf-8") as jf:
                json.dump(
                    [el.to_dict() if hasattr(el, "to_dict") else str(el) for el in elements],
                    jf,
                    indent=4,
                    ensure_ascii=False
                )
            print(f"✅ JSON saved at: {json_path}")
        except Exception as e:
            print(f"❌ Error saving JSON: {e}")

        # Dump to Pickle
        try:
            with open(pickle_path, "wb") as pf:
                pickle.dump(elements, pf)
            print(f"✅ Pickle saved at: {pickle_path}")
        except Exception as e:
            print(f"❌ Error saving Pickle: {e}")

    except Exception as e:
        print(f"🚨 Error: {e}")
        
    except FileNotFoundError as e:
        print(f"\n❌ File Error: {e}")
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")