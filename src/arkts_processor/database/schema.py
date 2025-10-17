"""
数据库Schema定义

使用SQLAlchemy定义符号表、作用域表、引用表等数据模型。
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, 
    Float, DateTime, ForeignKey, Enum as SQLEnum,
    Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.sqlite import JSON
from datetime import datetime

from ..models import SymbolType, ScopeType, ReferenceType, Visibility


Base = declarative_base()


class TypeModel(Base):
    """类型信息表"""
    __tablename__ = "types"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    is_primitive = Column(Boolean, default=False)
    is_array = Column(Boolean, default=False)
    is_generic = Column(Boolean, default=False)
    generic_params = Column(JSON, default=list)
    element_type_id = Column(Integer, ForeignKey("types.id"), nullable=True)
    nullable = Column(Boolean, default=False)
    
    # 自引用关系
    element_type = relationship("TypeModel", remote_side=[id], backref="array_types")
    
    __table_args__ = (
        Index("idx_type_name", "name"),
    )
    
    def __repr__(self):
        return f"<TypeModel(id={self.id}, name='{self.name}')>"


class ScopeModel(Base):
    """作用域表"""
    __tablename__ = "scopes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    scope_type = Column(SQLEnum(ScopeType), nullable=False)
    file_path = Column(String(512), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("scopes.id"), nullable=True)
    
    # 位置信息
    start_line = Column(Integer, nullable=False)
    start_column = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    end_column = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    
    # 元数据
    meta_data = Column(JSON, default=dict)
    
    # 关系
    parent = relationship("ScopeModel", remote_side=[id], backref="children")
    symbols = relationship("SymbolModel", back_populates="scope", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_scope_file", "file_path"),
        Index("idx_scope_parent", "parent_id"),
        Index("idx_scope_range", "start_line", "end_line"),
    )
    
    def __repr__(self):
        return f"<ScopeModel(id={self.id}, type={self.scope_type.value}, file='{self.file_path}')>"


class SymbolModel(Base):
    """符号表"""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    symbol_type = Column(SQLEnum(SymbolType), nullable=False)
    file_path = Column(String(512), nullable=False, index=True)
    scope_id = Column(Integer, ForeignKey("scopes.id"), nullable=False)
    
    # 位置信息
    start_line = Column(Integer, nullable=False)
    start_column = Column(Integer, nullable=False)
    start_offset = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    end_column = Column(Integer, nullable=False)
    end_offset = Column(Integer, nullable=False)
    
    # 类型信息
    type_id = Column(Integer, ForeignKey("types.id"), nullable=True)
    return_type_id = Column(Integer, ForeignKey("types.id"), nullable=True)
    
    # 访问控制
    visibility = Column(SQLEnum(Visibility), default=Visibility.PUBLIC)
    is_static = Column(Boolean, default=False)
    is_abstract = Column(Boolean, default=False)
    is_readonly = Column(Boolean, default=False)
    is_async = Column(Boolean, default=False)
    
    # Export 信息
    is_exported = Column(Boolean, default=False)  # 是否通过 export 导出
    is_export_default = Column(Boolean, default=False)  # 是否为 export default
    
    # 继承和实现
    extends = Column(JSON, default=list)  # List[str]
    implements = Column(JSON, default=list)  # List[str]
    
    # 参数和成员（存储ID列表）
    parameter_ids = Column(JSON, default=list)  # List[int]
    member_ids = Column(JSON, default=list)  # List[int]
    
    # 文档和装饰器
    documentation = Column(Text, nullable=True)
    decorators = Column(JSON, default=list)  # List[str]
    
    # 元数据
    meta_data = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    scope = relationship("ScopeModel", back_populates="symbols")
    type_info = relationship("TypeModel", foreign_keys=[type_id])
    return_type_info = relationship("TypeModel", foreign_keys=[return_type_id])
    references = relationship("ReferenceModel", back_populates="symbol", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_symbol_name", "name"),
        Index("idx_symbol_file", "file_path"),
        Index("idx_symbol_type", "symbol_type"),
        Index("idx_symbol_scope", "scope_id"),
        Index("idx_symbol_position", "file_path", "start_line", "start_column"),
        UniqueConstraint("name", "file_path", "start_line", "start_column", name="uq_symbol_location"),
    )
    
    def __repr__(self):
        return f"<SymbolModel(id={self.id}, name='{self.name}', type={self.symbol_type.value})>"


class ReferenceModel(Base):
    """引用表"""
    __tablename__ = "references"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    file_path = Column(String(512), nullable=False, index=True)
    reference_type = Column(SQLEnum(ReferenceType), nullable=False)
    
    # 位置信息
    line = Column(Integer, nullable=False)
    column = Column(Integer, nullable=False)
    offset = Column(Integer, nullable=False)
    
    # 引用上下文
    context = Column(Text, nullable=True)
    
    # 元数据
    meta_data = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关系
    symbol = relationship("SymbolModel", back_populates="references")
    
    __table_args__ = (
        Index("idx_ref_symbol", "symbol_id"),
        Index("idx_ref_file", "file_path"),
        Index("idx_ref_type", "reference_type"),
        Index("idx_ref_position", "file_path", "line", "column"),
    )
    
    def __repr__(self):
        return f"<ReferenceModel(id={self.id}, symbol_id={self.symbol_id}, type={self.reference_type.value})>"


class SymbolRelationModel(Base):
    """符号关系表"""
    __tablename__ = "symbol_relations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    to_symbol_id = Column(Integer, ForeignKey("symbols.id"), nullable=False)
    relation_type = Column(String(50), nullable=False)
    
    # 元数据
    meta_data = Column(JSON, default=dict)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_relation_from", "from_symbol_id"),
        Index("idx_relation_to", "to_symbol_id"),
        Index("idx_relation_type", "relation_type"),
        UniqueConstraint("from_symbol_id", "to_symbol_id", "relation_type", name="uq_symbol_relation"),
    )
    
    def __repr__(self):
        return f"<SymbolRelationModel(from={self.from_symbol_id}, to={self.to_symbol_id}, type='{self.relation_type}')>"
