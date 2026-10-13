import os
import sys
import threading
from tree_sitter import Language, Parser

# --- Path Configuration (Calculated relatively) ---
LOG_FILE_PATH = None

try:
    # Determine the absolute path to the 'backend' directory from this file's location.
    # __file__ is in .../backend/app/codeReview/ConfigurationItem/service/ai/parser
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # Navigate 6 levels up from 'parser' to 'backend'
    BACKEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..', '..', '..', '..', '..'))

    if os.path.basename(BACKEND_DIR) != 'backend':
        raise FileNotFoundError(f"Could not determine 'backend' directory. Found '{BACKEND_DIR}' instead.")

    # Define all paths relative to the backend directory.
    LOG_DIR = os.path.join(BACKEND_DIR, 'logs')
    BUILD_DIR = os.path.join(BACKEND_DIR, 'ts_build')
    C_GRAMMAR_PATH = os.path.join(BACKEND_DIR, 'vendor', 'tree-sitter-c')
    CPP_GRAMMAR_PATH = os.path.join(BACKEND_DIR, 'vendor', 'tree-sitter-cpp')

    # Specific file paths
    LOG_FILE_PATH = os.path.join(LOG_DIR, 'bg_debug.txt')
    LIB_PATH = os.path.join(BUILD_DIR, 'languages.dll')

    # Ensure the log directory exists before any logging attempt.
    os.makedirs(LOG_DIR, exist_ok=True)

except Exception as e:
    # If path calculation fails, we cannot log to a file. Write to stderr as a last resort.
    import sys
    sys.stderr.write(f"[ts_loader] CRITICAL PATH CONFIGURATION ERROR: {e}\n")
    # Subsequent operations that depend on these paths will fail.

def log_debug(msg: str):
    """Appends a message to the central debug log file with line buffering."""
    if not LOG_FILE_PATH:
        import sys
        sys.stderr.write(f"[ts_loader] LOGGING_DISABLED | MESSAGE: {msg}\n")
        return
    try:
        # The log directory is created during path configuration.
        with open(LOG_FILE_PATH, "a", encoding="utf-8", buffering=1) as f:
            f.write(f"[ts_loader] {msg}\n")
    except Exception as e:
        # Fallback to stderr if logging fails.
        import sys
        sys.stderr.write(f"[ts_loader] LOGGING_ERROR: {e} | MESSAGE: {msg}\n")

# --- Global State ---
_C_LANG = None
_CPP_LANG = None
_build_lock = threading.Lock()
_initialized = False
TS_AVAILABLE = False

def _initialize_languages():
    """
    Builds the tree-sitter language library if it doesn't exist,
    and then loads the C and C++ languages. This function is thread-safe.
    """
    log_debug("--- _initialize_languages called ---")
    global _C_LANG, _CPP_LANG, _initialized, TS_AVAILABLE

    try:
        with _build_lock:
            log_debug("Acquired build lock.")
            if _initialized:
                log_debug("Already initialized, returning.")
                return

            log_debug("First time initialization.")
            log_debug(f"Build directory: {BUILD_DIR}")
            log_debug(f"Library path: {LIB_PATH}")
            log_debug(f"C grammar path: {C_GRAMMAR_PATH}")
            log_debug(f"C++ grammar path: {CPP_GRAMMAR_PATH}")

            # Create build directory if it doesn't exist
            if not os.path.exists(BUILD_DIR):
                log_debug(f"Build directory does not exist. Creating: {BUILD_DIR}")
                os.makedirs(BUILD_DIR)
                log_debug("Build directory created.")
            else:
                log_debug("Build directory already exists.")

            # Check if grammars exist
            if not os.path.exists(C_GRAMMAR_PATH) or not os.path.exists(CPP_GRAMMAR_PATH):
                log_debug(f"ERROR: Grammar directories not found. C exists: {os.path.exists(C_GRAMMAR_PATH)}, C++ exists: {os.path.exists(CPP_GRAMMAR_PATH)}")
                TS_AVAILABLE = False
                _initialized = True
                log_debug("Init failed: Grammar not found. Set TS_AVAILABLE=False.")
                return

            log_debug("Grammar directories found.")

            # Build the shared library if it doesn't exist
            if not os.path.exists(LIB_PATH):
                log_debug(f"Library not found at {LIB_PATH}. Starting build...")
                try:
                    Language.build_library(
                        LIB_PATH,
                        [C_GRAMMAR_PATH, CPP_GRAMMAR_PATH]
                    )
                    log_debug("Language.build_library call completed.")
                except Exception as e:
                    log_debug(f"FATAL: Failed to build language library: {e}")
                    import traceback
                    log_debug(traceback.format_exc())
                    TS_AVAILABLE = False
                    _initialized = True
                    log_debug("Init failed: Build error. Set TS_AVAILABLE=False.")
                    return
            else:
                log_debug("Language library already exists. Skipping build.")

            # Load the languages from the library
            log_debug("Attempting to load languages from library...")
            try:
                _C_LANG = Language(LIB_PATH, 'c')
                log_debug("C language loaded.")
                _CPP_LANG = Language(LIB_PATH, 'cpp')
                log_debug("C++ language loaded.")
                TS_AVAILABLE = True
                log_debug("Initialization successful. Set TS_AVAILABLE=True.")
            except Exception as e:
                log_debug(f"FATAL: Failed to load languages from library: {e}")
                import traceback
                log_debug(traceback.format_exc())
                TS_AVAILABLE = False
                log_debug("Init failed: Load error. Set TS_AVAILABLE=False.")

            _initialized = True
            log_debug("--- _initialize_languages finished ---")

    except Exception as e:
        log_debug(f"FATAL: Unhandled exception in _initialize_languages: {e}")
        import traceback
        log_debug(traceback.format_exc())
        TS_AVAILABLE = False
        _initialized = True

def get_language(language_name: str) -> Language:
    """
    Returns the tree-sitter Language object for the given language name.
    Initializes languages on first call.
    """
    if not _initialized:
        _initialize_languages()

    if not TS_AVAILABLE:
        raise RuntimeError("Tree-sitter languages are not available. Check logs for details.")

    if language_name.lower() == 'c':
        return _C_LANG
    elif language_name.lower() in ['cpp', 'c++']:
        return _CPP_LANG
    else:
        raise ValueError(f"Unsupported language: {language_name}")

def get_parser(language_name: str) -> Parser:
    """
    Returns a tree-sitter Parser configured for the given language.
    """
    lang_obj = get_language(language_name)
    parser = Parser()
    parser.set_language(lang_obj)
    return parser

# --- Initialize on import ---
_initialize_languages()
