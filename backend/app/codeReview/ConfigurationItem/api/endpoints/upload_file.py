"""
代码审查文件上传API端点
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import os
import zipfile
import uuid
import shutil
from pathlib import Path
from ...config import ZIP_FOLDER, EXTRACT_FOLDER, ALLOWED_EXTENSIONS, ALL_SUPPORTED_EXTENSIONS, MAX_ZIP_SIZE_MB
from ...db.deps import get_db
from ...db.repository import FileRepository
from ...utils.logger import log_info, log_debug, log_warning, log_error

router = APIRouter()

@router.post("/upload_file", summary="Upload a ZIP file for C/C++ code review")
def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Check file extension
    filename = file.filename
    log_info(f"[上传] 开始上传文件: {filename}", "upload_file")
    ext = os.path.splitext(filename)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        log_warning(f"[上传] 非法扩展名: {ext}, 文件: {filename}", "upload_file")
        raise HTTPException(status_code=400, detail=f"只允许上传ZIP格式文件，当前文件格式: {ext}")

    # Generate a unique folder name for this upload
    unique_id = str(uuid.uuid4())
    zip_save_path = os.path.join(ZIP_FOLDER, f"{unique_id}{ext}")
    extract_path = os.path.join(EXTRACT_FOLDER, unique_id)
    
    try:
        # Save ZIP file
        os.makedirs(os.path.dirname(zip_save_path), exist_ok=True)
        with open(zip_save_path, "wb") as f:
            f.write(file.file.read())
        log_debug(f"[上传] ZIP已保存: {zip_save_path}", "upload_file")
        
        # Check ZIP file size
        zip_size_mb = os.path.getsize(zip_save_path) / (1024 * 1024)
        log_info(f"[上传] ZIP文件大小: {zip_size_mb:.2f} MB", "upload_file")
        if zip_size_mb > MAX_ZIP_SIZE_MB:
            # Clean up
            os.remove(zip_save_path)
            log_warning(f"[上传] ZIP文件过大: {zip_size_mb:.2f} MB > {MAX_ZIP_SIZE_MB} MB", "upload_file")
            raise HTTPException(
                status_code=400, 
                detail=f"压缩包过大（{zip_size_mb:.2f} MB），请清理非源码文件后重新上传。\n\n"
                       f"建议操作：\n"
                       f"1. 仅保留源码文件（C/C++: .c/.cpp/.h/.hpp，FPGA: .v/.vhd/.vhdl）\n"
                       f"2. 删除编译产物（.o/.obj/.exe/.dll等）\n"
                       f"3. 删除临时文件和文档（.txt/.pdf/.doc等）\n"
                       f"4. 删除图片和媒体文件\n\n"
                       f"当前限制: {MAX_ZIP_SIZE_MB} MB"
            )
        
        # Create extraction directory
        os.makedirs(extract_path, exist_ok=True)
        log_debug(f"[上传] 解压目录创建: {extract_path}", "upload_file")
        
        # Extract ZIP file with proper filename decoding (handle Chinese names)
        def _decode_zip_name(name: str) -> str:
            try:
                # If the UTF-8 flag is not set, Python decodes using cp437 by default.
                # Reinterpret bytes as gbk to fix common Chinese ZIPs created on Windows.
                return name.encode('cp437').decode('gbk')
            except Exception:
                return name

        def _is_safe_path(base: Path, target: Path) -> bool:
            try:
                base_resolved = base.resolve()
                target_resolved = target.resolve()
                return str(target_resolved).startswith(str(base_resolved))
            except Exception:
                return False

        with zipfile.ZipFile(zip_save_path, 'r') as zip_ref:
            log_info(f"[解压] ZIP条目数量: {len(zip_ref.infolist())}", "upload_file")
            error_entries = 0
            entries = []
            # 第一遍：构建解码后的名称列表
            for zinfo in zip_ref.infolist():
                name = (zinfo.filename or "").replace('\\', '/').strip('/')
                if not name:
                    continue
                if not (zinfo.flag_bits & 0x800):
                    decoded = _decode_zip_name(name)
                else:
                    decoded = name
                entries.append((zinfo, decoded))

            # 根据所有解码后的名称，推断应存在的目录集合（含所有父级目录）
            dir_set = set()
            for _z, decoded in entries:
                parts = [p for p in decoded.split('/') if p]
                cur = []
                for i in range(len(parts) - 1):
                    cur.append(parts[i])
                    dir_set.add('/'.join(cur))

            # 第二遍：执行解压
            for zinfo, decoded in entries:
                try:
                    dest_path = Path(extract_path) / Path(decoded)
                    # Security: prevent path traversal and absolute paths
                    if not _is_safe_path(Path(extract_path), dest_path):
                        log_warning(f"[解压] 跳过可疑路径: original='{zinfo.filename}', decoded='{decoded}', dest='{dest_path}'", "upload_file")
                        continue

                    is_dir_entry = False
                    # 1) Python 提供的目录判断
                    if getattr(zinfo, 'is_dir', None) and zinfo.is_dir():
                        is_dir_entry = True
                    # 2) 名称约定（尾随斜杠）
                    elif decoded.endswith('/'):
                        is_dir_entry = True
                    # 3) 通过目录集合推断（无斜杠目录项）
                    elif decoded in dir_set:
                        is_dir_entry = True

                    if is_dir_entry:
                        dest_path.mkdir(parents=True, exist_ok=True)
                        log_debug(f"[解压] 创建目录: {dest_path}", "upload_file")
                        continue

                    # 文件：确保父目录存在
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    with zip_ref.open(zinfo, 'r') as src, open(dest_path, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
                    log_debug(f"[解压] 写入文件: original='{zinfo.filename}', decoded='{decoded}', dest='{dest_path}'", "upload_file")
                except Exception as e:
                    error_entries += 1
                    log_error(f"[解压] 处理条目失败: original='{zinfo.filename}', decoded='{decoded}'", "upload_file", e)
            if error_entries:
                log_warning(f"[解压] 条目处理失败数量: {error_entries}", "upload_file")
        
        # Check if there are any valid source files (C/C++ or FPGA)
        valid_files = []
        for root, _, files in os.walk(extract_path):
            for file in files:
                file_ext = os.path.splitext(file)[-1].lower()
                if file_ext in ALL_SUPPORTED_EXTENSIONS:
                    full_path = os.path.join(root, file)
                    valid_files.append(full_path)
        log_info(f"[扫描] 支持的源文件数量: {len(valid_files)}", "upload_file")
        
        if not valid_files:
            # Clean up if no valid files found
            shutil.rmtree(extract_path, ignore_errors=True)
            os.remove(zip_save_path)
            raise HTTPException(status_code=400, detail="ZIP文件中未找到有效的代码审查文件（支持C/C++和FPGA代码）")
        
        # Create DB record
        file_repo = FileRepository(db)
        file_data = {
            "file_name": filename,
            "file_path": zip_save_path,
            "extract_path": extract_path,
            "status": "uploaded",
            "file_count": len(valid_files)
        }
        db_file = file_repo.create_file(file_data)
        db.commit()  # 提交事务确保数据保存
        log_info(f"[上传] DB记录创建成功: file_id={db_file.id}, file_count={len(valid_files)}", "upload_file")

        return {
            "file_id": db_file.id, 
            "file_name": filename,
            "file_count": len(valid_files)
        }
    
    except zipfile.BadZipFile:
        # Clean up in case of error
        if os.path.exists(zip_save_path):
            os.remove(zip_save_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)
        log_warning(f"[上传] 无效的ZIP文件: {filename}", "upload_file")
        raise HTTPException(status_code=400, detail="无效的ZIP文件")
    
    except HTTPException as he:
        # Clean up in case of controlled client error (e.g., 400)
        if os.path.exists(zip_save_path):
            os.remove(zip_save_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)
        log_warning(f"[上传] 客户端错误: {filename} -> {he.detail}", "upload_file")
        raise
    except Exception as e:
        # Clean up in case of error
        if os.path.exists(zip_save_path):
            os.remove(zip_save_path)
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path, ignore_errors=True)
        log_error(f"[上传] 文件处理错误: {filename}", "upload_file", e)
        raise HTTPException(status_code=500, detail=f"文件处理错误: {str(e)}")
