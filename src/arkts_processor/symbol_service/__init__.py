"""
符号表服务模块

提供符号提取、作用域分析、类型推导和引用解析功能。
"""

from .service import SymbolService
from .extractor import SymbolExtractor
from .scope_analyzer import ScopeAnalyzer
from .type_inference import TypeInferenceEngine
from .reference_resolver import ReferenceResolver
from .index_service import SymbolIndexService

__all__ = [
    "SymbolService",
    "SymbolExtractor",
    "ScopeAnalyzer",
    "TypeInferenceEngine",
    "ReferenceResolver",
    "SymbolIndexService",
]
