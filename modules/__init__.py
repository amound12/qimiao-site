"""模块区：每个子目录是一个独立功能模块（乐高积木）。

加新功能 = 复制 _template 目录改名 + 在 .env 的 MODULES_ENABLED 登记。
模块之间禁止互相 import 内部实现，只通过 core.registry 的 MODULE 清单交流。
"""
