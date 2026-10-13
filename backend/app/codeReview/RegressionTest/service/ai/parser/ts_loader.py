import os
import sys
import threading
from tree_sitter import Language, Parser

# 导入统一的日志系统
from ....utils.logger import log_debug

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
    # If path calculation fails, we cannot log to a file. Use debug logging instead.
    log_debug(f"[ts_loader] CRITICAL PATH CONFIGURATION ERROR: {e}")
    # Subsequent operations that depend on these paths will fail.

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
                # 方案1：尝试使用 tree-sitter-languages（如果可用）
                try:
                    from tree_sitter_languages import get_language as get_ts_language
                    _C_LANG = get_ts_language('c')
                    _CPP_LANG = get_ts_language('cpp')
                    log_debug("Loaded languages using tree-sitter-languages package")
                    TS_AVAILABLE = True
                    log_debug("Initialization successful. Set TS_AVAILABLE=True.")
                except ImportError:
                    log_debug("tree-sitter-languages not available, trying manual loading...")
                    raise  # 触发回退到手动加载
                
            except:
                # 方案2：手动从 DLL 加载（兼容多个版本）
                try:
                    import ctypes
                    lib = ctypes.CDLL(LIB_PATH)
                    
                    # 配置函数返回类型为 c_void_p（指针）
                    lib.tree_sitter_c.restype = ctypes.c_void_p
                    lib.tree_sitter_cpp.restype = ctypes.c_void_p
                    log_debug("Configured function return types")
                    
                    # 获取语言函数
                    tree_sitter_c_func = lib.tree_sitter_c
                    log_debug("Found tree_sitter_c function")
                    tree_sitter_cpp_func = lib.tree_sitter_cpp
                    log_debug("Found tree_sitter_cpp function")
                    
                    # 调用函数获取语言指针
                    c_lang_ptr = tree_sitter_c_func()
                    log_debug(f"Got C language pointer: {c_lang_ptr}")
                    cpp_lang_ptr = tree_sitter_cpp_func()
                    log_debug(f"Got C++ language pointer: {cpp_lang_ptr}")
                    
                    # 创建 Language 对象（兼容不同版本）
                    # tree-sitter 0.21.x: Language(pointer, name)
                    # tree-sitter 0.25.x: Language(pointer)
                    try:
                        # 尝试 0.21.x 的 API（需要 name 参数）
                        _C_LANG = Language(c_lang_ptr, name='c')
                        _CPP_LANG = Language(cpp_lang_ptr, name='cpp')
                        log_debug("Loaded using tree-sitter 0.21.x API (with name)")
                    except TypeError:
                        # 回退到 0.25.x 的 API（只需要指针）
                        _C_LANG = Language(c_lang_ptr)
                        _CPP_LANG = Language(cpp_lang_ptr)
                        log_debug("Loaded using tree-sitter 0.25.x API (pointer only)")
                    
                    log_debug("C language loaded.")
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
