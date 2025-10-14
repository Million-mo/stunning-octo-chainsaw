"""
代码 Chunk 数据模型

定义代码块、元数据、上下文等核心数据结构。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChunkType(Enum):
    """Chunk 类型枚举"""
    FUNCTION = "function"
    CLASS = "class"
    COMPONENT = "component"  # ArkUI 组件
    MODULE = "module"
    INTERFACE = "interface"
    ENUM = "enum"
    FILE = "file"  # 小型工具文件


@dataclass
class PositionRange:
    """位置范围信息"""
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    
    def to_dict(self) -> Dict[str, int]:
        """转换为字典"""
        return {
            "start_line": self.start_line,
            "end_line": self.end_line,
            "start_column": self.start_column,
            "end_column": self.end_column
        }


@dataclass
class Parameter:
    """参数信息"""
    name: str
    type: str
    default_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "type": self.type,
            "default_value": self.default_value
        }


@dataclass
class TypeInfo:
    """类型信息"""
    name: str
    is_primitive: bool = False
    is_array: bool = False
    generic_params: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "is_primitive": self.is_primitive,
            "is_array": self.is_array,
            "generic_params": self.generic_params
        }


@dataclass
class ChunkMetadata:
    """Chunk 元数据"""
    range: PositionRange
    decorators: List[str] = field(default_factory=list)
    visibility: str = "public"
    parameters: List[Parameter] = field(default_factory=list)
    return_type: Optional[TypeInfo] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # ArkUI 特有元数据
    component_type: Optional[str] = None  # Entry/Component/Preview
    state_vars: List[Dict[str, str]] = field(default_factory=list)  # @State 变量
    lifecycle_hooks: List[str] = field(default_factory=list)  # 生命周期方法
    event_handlers: List[str] = field(default_factory=list)  # 事件处理器
    resource_refs: List[str] = field(default_factory=list)  # 资源引用
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "range": self.range.to_dict(),
            "decorators": self.decorators,
            "visibility": self.visibility,
            "parameters": [p.to_dict() for p in self.parameters],
            "dependencies": self.dependencies,
            "tags": self.tags
        }
        
        if self.return_type:
            result["return_type"] = self.return_type.to_dict()
        
        # ArkUI 特有字段
        if self.component_type:
            result["component_type"] = self.component_type
        if self.state_vars:
            result["state_vars"] = self.state_vars
        if self.lifecycle_hooks:
            result["lifecycle_hooks"] = self.lifecycle_hooks
        if self.event_handlers:
            result["event_handlers"] = self.event_handlers
        if self.resource_refs:
            result["resource_refs"] = self.resource_refs
        
        return result


@dataclass
class CodeChunk:
    """代码块数据模型"""
    chunk_id: str  # 唯一标识符：{文件路径}#{符号路径}
    type: ChunkType
    path: str  # 源文件相对路径
    name: str  # 主符号名称
    context: str  # 层级上下文（类名/模块名）
    source: str  # 完整源代码文本（可能包含上下文增强）
    imports: List[str] = field(default_factory=list)  # 依赖的外部符号
    comments: Optional[str] = None  # 文档注释/说明
    metadata: Optional[ChunkMetadata] = None  # 扩展元数据
    
    # 内部字段
    symbol_id: Optional[int] = None  # 关联的符号ID
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "chunk_id": self.chunk_id,
            "type": self.type.value,
            "path": self.path,
            "name": self.name,
            "context": self.context,
            "source": self.source,
            "imports": self.imports,
            "comments": self.comments
        }
        
        if self.metadata:
            result["metadata"] = self.metadata.to_dict()
        
        if self.symbol_id:
            result["symbol_id"] = self.symbol_id
        
        if self.created_at:
            result["created_at"] = self.created_at.isoformat()
        
        if self.updated_at:
            result["updated_at"] = self.updated_at.isoformat()
        
        return result
    
    def get_enriched_source(self) -> str:
        """
        获取增强后的源代码（用于 embedding）
        
        返回包含上下文元数据头的源代码
        """
        # 如果已经包含增强头，直接返回
        if self.source.startswith("#"):
            return self.source
        
        # 否则返回原始源代码
        return self.source
    
    def __hash__(self):
        """计算哈希值"""
        return hash(self.chunk_id)
    
    def __eq__(self, other):
        """判断相等"""
        if not isinstance(other, CodeChunk):
            return False
        return self.chunk_id == other.chunk_id


@dataclass
class ChunkSearchResult:
    """Chunk 搜索结果"""
    chunk: CodeChunk
    score: float  # 相似度分数
    highlights: List[str] = field(default_factory=list)  # 高亮片段
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chunk": self.chunk.to_dict(),
            "score": self.score,
            "highlights": self.highlights
        }
