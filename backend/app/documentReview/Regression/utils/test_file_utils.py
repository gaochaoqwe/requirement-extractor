import sys
import os
import glob
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../..')))
from .file_utils import read_uploaded_file

from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
UPLOAD_ROOT = str(BASE_DIR / 'uploads' / 'regression')

def test_list_and_read_files():
    # 列出所有文件
    files = glob.glob(os.path.join(UPLOAD_ROOT, "*"))
    sys.stderr.write("所有文件：\n")
    for f in files:
        sys.stderr.write(f"{f}\n")
    assert files, "regression目录下没有文件"

    # 取第一个文件名，提取file_id
    first_file = os.path.basename(files[0])
    file_id = first_file.split("_")[0]
    sys.stderr.write(f"\n测试file_id: {file_id}\n")

    # 调用算法函数读取内容
    try:
        content = read_uploaded_file(file_id)
        if content:
            sys.stderr.write("\n读取到的内容：\n")
            sys.stderr.write(f"{content}\n")
    except Exception as e:
        sys.stderr.write(f"读取文件异常: {e}\n")
        raise

if __name__ == "__main__":
    test_list_and_read_files()
