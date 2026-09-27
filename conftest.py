"""pytest 引导：把项目根目录（qimiao/）加入 sys.path。

让 pytest 在任意工作目录下执行都能 import 到 main / core / modules：
    pytest                  # 在 qimiao/ 里跑
    pytest qimiao/tests     # 在上层目录跑
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
