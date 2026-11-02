"""让构建脚本在 Windows 的 cp1252 控制台/管道下也能打印中文。

PEP 517 在 Windows 上会用系统 ANSI 代码页（常见 cp1252）包装 ``sys.stdout``；
直接 ``print("下载 ...")`` 会抛 ``UnicodeEncodeError``。构建脚本在导入时调用
:func:`use_utf8_stdio`，把标准输出/错误流切到 UTF-8，并对无法编码的字符转义。
"""

from __future__ import annotations

import sys


def use_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="backslashreplace")
        except (AttributeError, ValueError, OSError):
            # 流已关闭或被替换时保持原样即可，不应影响构建。
            pass
