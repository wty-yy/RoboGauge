# -*- coding: utf-8 -*-
'''
@File    : file_utils.py
@Time    : 2025/12/27 17:14:29
@Author  : wty-yy
@Version : 1.0
@Blog    : https://wty-yy.github.io/
@Desc    : Common File Utilities
'''
import tarfile
import shutil
import os
from pathlib import Path
import logging

def log_msg(logger: logging.Logger, msg: str, level: str):
    if logger:
        getattr(logger, level)(msg)
    else:
        print(msg)

def compress_directory(source_dir, output_filename=None, delete_original=True, logger: logging.Logger=None):
    """
    Compress a directory into a .tar.xz file using LZMA compression.
    
    Args:
        source_dir (str | Path): Path to the directory to compress.
        output_filename (str | Path, optional): Output path. Defaults to source_dir + ".tar.xz".
        delete_original (bool): Whether to delete the source directory after successful compression.
    """
    source_dir = Path(source_dir)
    if not source_dir.exists():
        log_msg(logger, f"⚠️ Source directory for compression not found: {source_dir}", "warning")
        return

    if output_filename is None:
        output_filename = source_dir.with_suffix('.tar.xz')
    else:
        output_filename = Path(output_filename)

    log_msg(logger, f"📦 Compressing logs: {source_dir.name} -> {output_filename.name} ...", "info")
    
    try:
        with tarfile.open(output_filename, "w:xz") as tar:
            tar.add(source_dir, arcname=source_dir.name)
        
        log_msg(logger, f"✅ Compression finished: {output_filename}", "info")

        if delete_original:
            shutil.rmtree(source_dir)
            log_msg(logger, f"🗑️ Deleted original directory: {source_dir}", "info")
            
    except Exception as e:
        log_msg(logger, f"❌ Failed to compress directory {source_dir}: {e}", "error")
        # If compression failed, ensure we don't leave a half-baked file
        if output_filename.exists():
            os.remove(output_filename)
