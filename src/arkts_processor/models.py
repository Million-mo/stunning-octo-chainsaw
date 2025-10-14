"""
符号表核心数据模型

定义符号、作用域、引用等基础数据结构。
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SymbolType(Enum):
    """符号类型枚举"""
    CLASS = "class"
    INTERFACE = "interface"
    METHOD = "method"
    FUNCTION = "function"
    VARIABLE = "variable"
    PARAMETER = "parameter"
    PROPERTY = "property"
    ENUM = "enum"
    ENUM_MEMBER = "enum_member"
    MODULE = "module"
    NAMESPACE = "namespace"
    TYPE_ALIAS = "type_alias"
    CONSTRUCTOR = "constructor"


class ScopeType(Enum):
    """作用域类型枚举"""
    GLOBAL = "global"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    BLOCK = "block"
    NAMESPACE = "namespace"


class ReferenceType(Enum):
    """引用类型枚举"""
    READ = "read"
    WRITE = "write"
    CALL = "call"
    DEFINITION = "definition"
    TYPE_REFERENCE = "type_reference"
    IMPORT = "import"
    EXPORT = "export"


class Visibility(Enum):
    """可见性枚举"""
    PUBLIC = "public"
    PRIVATE = "private"
    PROTECTED = "protected"
    INTERNAL = "internal"


@dataclass
class Position:
    """位置信息"""
    line: int
    column: int
    offset: int


@dataclass
class Range:
    """范围信息"""
    start: Position
    end: Position

    def contains(self, pos: Position) -> bool:
        """检查位置是否在范围内"""
        if self.start.line < pos.line < self.end.line:
            return True
        if self.start.line == pos.line == self.end.line:
            return self.start.column <= pos.column < self.end.column
        if self.start.line == pos.line:
            return self.start.column <= pos.column
        if self.end.line == pos.line:
            return pos.column < self.end.column
        return False


@dataclass
class TypeInfo:
    """类型信息"""
    name: str
    is_primitive: bool = False
    is_array: bool = False
    is_generic: bool = False
    generic_params: List[str] = field(default_factory=list)
    element_type: Optional['TypeInfo'] = None
    nullable: bool = False
    
    def to_string(self) -> str:
        """转换为字符串表示"""
        result = self.name
        if self.is_generic and self.generic_params:
            result += f"<{', '.join(self.generic_params)}>"
        if self.is_array:
            result += "[]"
        if self.nullable:
            result += "?"
        return result


@dataclass
class Symbol:
    """符号信息"""
    id: Optional[int]
    name: str
    symbol_type: SymbolType
    file_path: str
    range: Range
    scope_id: Optional[int] = None
    
    # 类型信息
    type_info: Optional[TypeInfo] = None
    return_type: Optional[TypeInfo] = None
    
    # 访问控制
    visibility: Visibility = Visibility.PUBLIC
    is_static: bool = False
    is_abstract: bool = False
    is_readonly: bool = False
    is_async: bool = False
    
    # 参数和成员
    parameters: List['Symbol'] = field(default_factory=list)
    members: List['Symbol'] = field(default_factory=list)
    
    # 继承和实现
    extends: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    
    # 元数据
    documentation: Optional[str] = None
    decorators: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __hash__(self):
        """计算哈希值"""
        return hash((self.name, self.symbol_type.value, self.file_path, 
                    self.range.start.line, self.range.start.column))

    def __eq__(self, other):
        """判断相等"""
        if not isinstance(other, Symbol):
            return False
        return (self.name == other.name and 
                self.symbol_type == other.symbol_type and
                self.file_path == other.file_path and
                self.range.start.line == other.range.start.line and
                self.range.start.column == other.range.start.column)


@dataclass
class Scope:
    """作用域信息"""
    id: Optional[int]
    scope_type: ScopeType
    file_path: str
    range: Range
    parent_id: Optional[int] = None
    
    # 符号集合
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    
    # 子作用域
    children: List['Scope'] = field(default_factory=list)
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_symbol(self, symbol: Symbol) -> None:
        """添加符号到作用域"""
        self.symbols[symbol.name] = symbol
        symbol.scope_id = self.id
    
    def lookup(self, name: str, recursive: bool = True) -> Optional[Symbol]:
        """查找符号"""
        # 在当前作用域查找
        if name in self.symbols:
            return self.symbols[name]
        
        # 递归查找父作用域
        if recursive and self.parent_id is not None:
            # 需要通过作用域管理器查找父作用域
            pass
        
        return None
    
    def get_all_symbols(self, recursive: bool = False) -> List[Symbol]:
        """获取所有符号"""
        symbols = list(self.symbols.values())
        if recursive:
            for child in self.children:
                symbols.extend(child.get_all_symbols(recursive=True))
        return symbols


@dataclass
class Reference:
    """符号引用信息"""
    id: Optional[int]
    symbol_id: int
    file_path: str
    position: Position
    reference_type: ReferenceType
    
    # 引用上下文
    context: Optional[str] = None
    
    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: Optional[datetime] = None


@dataclass
class SymbolRelation:
    """符号关系"""
    from_symbol_id: int
    to_symbol_id: int
    relation_type: str  # "calls", "extends", "implements", "uses", etc.
    metadata: Dict[str, Any] = field(default_factory=dict)
