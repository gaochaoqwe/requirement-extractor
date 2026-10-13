
try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug


from ..excel_processing.excel_reader import xinghaoxinxi_excel_to_dict

# 函数功能：将 Excel 表格中的第 1 列作为键，将后面的 17 列作为值，形成一个字典。
# 例：Key: 乐高拼图软件, Value: ['直-AAA', 4354535, '光电', '张无忌', '明教', '早早早', '啊啊啊', '拼图软件', '无', '星河战舰', '战舰', '综合自卫', 'dfgfsd', 'C', 'sdfg20211', 'ewrgfs111', '一般']
# 函数已迁移到 excel_reader.py 中
