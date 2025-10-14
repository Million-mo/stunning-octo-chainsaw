"""
ArkTS代码处理平台 - 符号表服务模块

提供ArkTS代码的符号表构建、分析和查询功能。
"""

__version__ = "0.1.0"

from .models import Symbol, Scope, SymbolType, ScopeType, Reference, ReferenceType
from .symbol_service.service import SymbolService

__all__ = [
    "SymbolService",
    "Symbol",
    "Scope",
    "SymbolType",
    "ScopeType",
    "Reference",
    "ReferenceType",
]
