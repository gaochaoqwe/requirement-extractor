
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

# 函数功能：添加版本上报
# 输入：一个包含字符串的数组
# 输出：一个包含字符串的数组，如果数组中不包含"版本上报"，则在末尾添加
def add_version_report_if_missing(cehsixiang_list):
    # 检查数组中是否已经包含"版本上报"
    contains_version_report = any("版本" in s for s in cehsixiang_list)
    # 如果没有包含，则在数组末尾添加
    if not contains_version_report:
        cehsixiang_list.append("软件版本上报")
    return cehsixiang_list
