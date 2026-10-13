import shutil
import os
import stat

try:
    from ..utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
except ImportError:
    try:
        from ...utils.logging_utils.logger import log_info, log_error, log_warning, log_debug
    except ImportError:
        from app.danamicTest.Regression.utils.logging_utils.logger import log_info, log_error, log_warning, log_debug

#模块功能：将所有的c和c++文件合并成一个text文本
#函数输入：
#          folder_path：原始代码的路径
#          output_file：合并后代码的路径
#函数输出：
#          合并后的txt文本
def Code_merging(folder_path, output_file):
    # 检查目标文件是否存在，如果不存在则创建

    if not os.path.exists(output_file):          #如果文件不存在，它将被创建。close() 方法立即被调用以关闭文件，从而创建一个空文件。
        open(output_file, 'w').close()
    files = [f for f in os.listdir(folder_path) if f.endswith('.c') or f.endswith('.cpp') or f.endswith('.h') or f.endswith(".H")]
    with open(output_file, 'w', errors='ignore') as merged_file:
        for file in files:
            file_path = os.path.join(folder_path, file)
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:  # 指定UTF-8编码
                merged_file.write(f.read())
                merged_file.write('\n')

# 函数功能：处理删除时遇到的只读文件或目录
def handle_remove_readonly(func, path, exc_info):
    """
    处理删除时遇到的只读文件或目录
    """
    # 修改路径的权限为可写
    os.chmod(path, stat.S_IWRITE)
    # 再次尝试执行删除操作
    func(path)

# folder_path = 'your_folder_path'  # 替换为你的文件夹路径
# output_file = 'merged_files.txt'  # 合并后的txt文件名

"""
    函数功能：合并指定源文件夹中的C/C++文件到目标文件夹

    参数说明：
        source_folder -- 需要扫描的源代码根目录路径
        target_folder -- 合并后的目标文件夹路径
        allowed_extensions -- 需要处理的文件扩展名列表（小写）
    """
def merge_c_and_cpp_files(source_folder: str,target_folder: str,allowed_extensions: tuple = ('.c', '.cpp', '.H', '.h')) -> None:
    try:  # 主逻辑异常捕获
        # ===== 1. 参数有效性验证 =====
        # 检查源文件夹是否存在
        if not os.path.exists(source_folder):
            log_info(f"源文件夹不存在: {source_folder}", Path(__file__).stem)
            return 0
        # 确认源路径是目录而不是文件
        if not os.path.isdir(source_folder):
            log_info(f"源路径不是文件夹: {source_folder}", Path(__file__).stem)
            return 0
        # ===== 2. 准备目标文件夹 =====
        # 如果目标文件夹已存在则完全删除
        if os.path.exists(target_folder):
            shutil.rmtree(target_folder, onerror=handle_remove_readonly)
        # 创建全新的空目标文件夹
        os.makedirs(target_folder, exist_ok=True)  # exist_ok防止竞态条件

        # ===== 3. 初始化文件计数器 =====
        # 用于跟踪重复文件名并生成唯一文件名
        file_counter = {}  # 格式：{原始文件名: 出现次数}

        # ===== 4. 遍历源文件系统 =====
        # 使用os.walk递归遍历所有子目录
        for root, _, files in os.walk(source_folder):
            # root : 当前目录路径（字符串）
            # _    : 子目录列表（此处不需要，用_忽略）
            # files: 当前目录下的文件列表

            # 遍历当前目录下的每个文件
            for filename in files:
                # ===== 5. 文件扩展名验证 =====
                # 分割文件名和扩展名（返回元组）
                _, extension = os.path.splitext(filename)
                # 统一转为小写进行比较（避免大小写不一致问题）
                ext_lower = extension.lower()

                # 检查是否在允许的扩展名列表中
                if ext_lower in allowed_extensions:
                    # ===== 6. 构造完整路径 =====
                    # 拼接完整的源文件路径
                    source_path = os.path.join(root, filename)

                    # ===== 7. 处理文件名冲突 =====
                    # 获取不包含扩展名的文件名
                    base_name = os.path.splitext(filename)[0]

                    # 检查是否已存在同名文件
                    if filename in file_counter:
                        # 递增计数器并生成新文件名
                        file_counter[filename] += 1
                        new_filename = f"{base_name}_{file_counter[filename]}{extension}"
                    else:
                        # 首次出现，初始化计数器
                        file_counter[filename] = 0
                        new_filename = filename  # 保持原文件名

                    # 构造目标文件路径
                    target_path = os.path.join(target_folder, new_filename)

                    # ===== 8. 执行文件复制 =====
                    # 使用copy2保留元数据（创建时间、权限等）
                    shutil.copy2(source_path, target_path)
                    # 打印操作日志
                    log_info(f"已复制: {source_path} -> {target_path}", Path(__file__).stem)

    except Exception as e:  # 捕获所有异常类型
        # 打印错误信息（包含原始异常信息）
        log_info(f"操作失败: {str(e)}", Path(__file__).stem)
        # 重新抛出异常供上层处理（可根据需求注释掉）
        raise  # 移除此行则不传播异常
#测试代码
# source_folder = 'C:/Users/Administrator/Desktop/c++xuexi/shuzhijisuan2.0_'
# target_folder = "D:/baxiang_ceshi/CODE_Copy"
# merge_folders(source_folder, target_folder)
