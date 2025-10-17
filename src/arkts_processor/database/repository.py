"""
符号表数据仓库

提供符号表的CRUD操作和查询功能。
"""

from typing import ContextManager, Optional, List, Dict, Any, Generator, cast
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from pathlib import Path

from .schema import Base, SymbolModel, ScopeModel, ReferenceModel, TypeModel, SymbolRelationModel
from ..models import Symbol, Scope, Reference, Position, Range, TypeInfo, SymbolType, ScopeType


class DatabaseManager:
    """数据库连接管理器"""
    
    def __init__(self, db_path: str = "arkts_symbols.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.engine = create_engine(f"sqlite:///{db_path}", echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)
        
    def create_tables(self):
        """创建所有表"""
        Base.metadata.create_all(bind=self.engine)
        
    def drop_tables(self):
        """删除所有表"""
        Base.metadata.drop_all(bind=self.engine)
        
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """获取数据库会话上下文管理器"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


class SymbolRepository:
    """符号表数据仓库"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化符号仓库
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        
    # ========== 类型操作 ==========
    
    def save_type(self, type_info: TypeInfo, session: Session) -> TypeModel:
        """保存类型信息"""
        # 检查是否已存在
        existing = session.query(TypeModel).filter(
            TypeModel.name == type_info.name,
            TypeModel.is_array == type_info.is_array,
            TypeModel.nullable == type_info.nullable
        ).first()
        
        if existing:
            return existing
            
        type_model = TypeModel(
            name=type_info.name,
            is_primitive=type_info.is_primitive,
            is_array=type_info.is_array,
            is_generic=type_info.is_generic,
            generic_params=type_info.generic_params,
            nullable=type_info.nullable
        )
        
        session.add(type_model)
        session.flush()
        return type_model
    
    # ========== 作用域操作 ==========
    
    def save_scope(self, scope: Scope):
        """保存作用域"""
        with self.db_manager.get_session() as session:
            scope_model = ScopeModel(
                scope_type=scope.scope_type,
                file_path=scope.file_path,
                parent_id=scope.parent_id,
                start_line=scope.range.start.line,
                start_column=scope.range.start.column,
                start_offset=scope.range.start.offset,
                end_line=scope.range.end.line,
                end_column=scope.range.end.column,
                end_offset=scope.range.end.offset,
                meta_data=scope.metadata
            )
            
            session.add(scope_model)
            session.flush()
            scope.id = cast(int, scope_model.id)
            return scope_model.id
    
    def get_scope_by_id(self, scope_id: int) -> Optional[Scope]:
        """根据ID获取作用域"""
        with self.db_manager.get_session() as session:
            scope_model = session.query(ScopeModel).filter(ScopeModel.id == scope_id).first()
            if not scope_model:
                return None
            return self._scope_model_to_entity(scope_model)
    
    def get_scopes_by_file(self, file_path: str) -> List[Scope]:
        """获取文件的所有作用域"""
        with self.db_manager.get_session() as session:
            scope_models = session.query(ScopeModel).filter(
                ScopeModel.file_path == file_path
            ).all()
            return [self._scope_model_to_entity(sm) for sm in scope_models]
    
    # ========== 符号操作 ==========
    
    def save_symbol(self, symbol: Symbol):
        """保存符号"""
        with self.db_manager.get_session() as session:
            # 保存类型信息
            type_id = None
            if symbol.type_info:
                type_model = self.save_type(symbol.type_info, session)
                type_id = type_model.id
                
            return_type_id = None
            if symbol.return_type:
                return_type_model = self.save_type(symbol.return_type, session)
                return_type_id = return_type_model.id
            
            symbol_model = SymbolModel(
                name=symbol.name,
                symbol_type=symbol.symbol_type,
                file_path=symbol.file_path,
                scope_id=symbol.scope_id,
                start_line=symbol.range.start.line,
                start_column=symbol.range.start.column,
                start_offset=symbol.range.start.offset,
                end_line=symbol.range.end.line,
                end_column=symbol.range.end.column,
                end_offset=symbol.range.end.offset,
                type_id=type_id,
                return_type_id=return_type_id,
                visibility=symbol.visibility,
                is_static=symbol.is_static,
                is_abstract=symbol.is_abstract,
                is_readonly=symbol.is_readonly,
                is_async=symbol.is_async,
                is_exported=symbol.is_exported,
                is_export_default=symbol.is_export_default,
                extends=symbol.extends,
                implements=symbol.implements,
                documentation=symbol.documentation,
                decorators=symbol.decorators,
                meta_data=symbol.metadata
            )
            
            session.add(symbol_model)
            session.flush()
            symbol.id = cast(int, symbol_model.id)
            return symbol_model.id
    
    def get_symbol_by_id(self, symbol_id: int) -> Optional[Symbol]:
        """根据ID获取符号"""
        with self.db_manager.get_session() as session:
            symbol_model = session.query(SymbolModel).filter(SymbolModel.id == symbol_id).first()
            if not symbol_model:
                return None
            return self._symbol_model_to_entity(symbol_model)
    
    def get_symbols_by_name(self, name: str, file_path: Optional[str] = None) -> List[Symbol]:
        """根据名称查找符号"""
        with self.db_manager.get_session() as session:
            query = session.query(SymbolModel).filter(SymbolModel.name == name)
            if file_path:
                query = query.filter(SymbolModel.file_path == file_path)
            symbol_models = query.all()
            return [self._symbol_model_to_entity(sm) for sm in symbol_models]
    
    def get_symbols_by_file(self, file_path: str) -> List[Symbol]:
        """获取文件的所有符号"""
        with self.db_manager.get_session() as session:
            symbol_models = session.query(SymbolModel).filter(
                SymbolModel.file_path == file_path
            ).all()
            return [self._symbol_model_to_entity(sm) for sm in symbol_models]
    
    def get_symbols_by_type(self, symbol_type: SymbolType, file_path: Optional[str] = None) -> List[Symbol]:
        """根据类型查找符号"""
        with self.db_manager.get_session() as session:
            query = session.query(SymbolModel).filter(SymbolModel.symbol_type == symbol_type)
            if file_path:
                query = query.filter(SymbolModel.file_path == file_path)
            symbol_models = query.all()
            return [self._symbol_model_to_entity(sm) for sm in symbol_models]
    
    def get_symbol_at_position(self, file_path: str, line: int, column: int) -> Optional[Symbol]:
        """获取指定位置的符号"""
        with self.db_manager.get_session() as session:
            symbol_model = session.query(SymbolModel).filter(
                SymbolModel.file_path == file_path,
                SymbolModel.start_line <= line,
                SymbolModel.end_line >= line
            ).first()
            
            if symbol_model:
                # 进一步检查列范围
                if (symbol_model.start_line == line and symbol_model.start_column <= column) or \
                   (symbol_model.end_line == line and symbol_model.end_column >= column) or \
                   (symbol_model.start_line < line < symbol_model.end_line):
                    return self._symbol_model_to_entity(symbol_model)
            
            return None
    
    # ========== 引用操作 ==========
    
    def save_reference(self, reference: Reference) -> int:
        """保存引用"""
        with self.db_manager.get_session() as session:
            ref_model = ReferenceModel(
                symbol_id=reference.symbol_id,
                file_path=reference.file_path,
                reference_type=reference.reference_type,
                line=reference.position.line,
                column=reference.position.column,
                offset=reference.position.offset,
                context=reference.context,
                meta_data=reference.metadata
            )
            
            session.add(ref_model)
            session.flush()
            reference.id = cast(int, ref_model.id)
            return cast(int, ref_model.id)
    
    def get_references_by_symbol(self, symbol_id: int) -> List[Reference]:
        """获取符号的所有引用"""
        with self.db_manager.get_session() as session:
            ref_models = session.query(ReferenceModel).filter(
                ReferenceModel.symbol_id == symbol_id
            ).all()
            return [self._reference_model_to_entity(rm) for rm in ref_models]
    
    def get_references_by_file(self, file_path: str) -> List[Reference]:
        """获取文件中的所有引用"""
        with self.db_manager.get_session() as session:
            ref_models = session.query(ReferenceModel).filter(
                ReferenceModel.file_path == file_path
            ).all()
            return [self._reference_model_to_entity(rm) for rm in ref_models]
    
    # ========== 批量操作 ==========
    
    def save_symbols_batch(self, symbols: List[Symbol]) -> List[int]:
        """批量保存符号"""
        with self.db_manager.get_session() as session:
            ids = []
            for symbol in symbols:
                # 保存类型信息
                type_id = None
                if symbol.type_info:
                    type_model = self.save_type(symbol.type_info, session)
                    type_id = type_model.id
                    
                return_type_id = None
                if symbol.return_type:
                    return_type_model = self.save_type(symbol.return_type, session)
                    return_type_id = return_type_model.id
                
                symbol_model = SymbolModel(
                    name=symbol.name,
                    symbol_type=symbol.symbol_type,
                    file_path=symbol.file_path,
                    scope_id=symbol.scope_id,
                    start_line=symbol.range.start.line,
                    start_column=symbol.range.start.column,
                    start_offset=symbol.range.start.offset,
                    end_line=symbol.range.end.line,
                    end_column=symbol.range.end.column,
                    end_offset=symbol.range.end.offset,
                    type_id=type_id,
                    return_type_id=return_type_id,
                    visibility=symbol.visibility,
                    is_static=symbol.is_static,
                    is_abstract=symbol.is_abstract,
                    is_readonly=symbol.is_readonly,
                    is_async=symbol.is_async,
                    is_exported=symbol.is_exported,
                    is_export_default=symbol.is_export_default,
                    extends=symbol.extends,
                    implements=symbol.implements,
                    documentation=symbol.documentation,
                    decorators=symbol.decorators,
                    meta_data=symbol.metadata
                )
                
                session.add(symbol_model)
                session.flush()
                ids.append(symbol_model.id)
                symbol.id = cast(int, symbol_model.id)
                
            
            return ids
    
    def delete_symbols_by_file(self, file_path: str) -> int:
        """删除文件的所有符号"""
        with self.db_manager.get_session() as session:
            count = session.query(SymbolModel).filter(
                SymbolModel.file_path == file_path
            ).delete()
            return count
    
    # ========== 转换方法 ==========
    
    def _symbol_model_to_entity(self, model: SymbolModel) -> Symbol:
        """将数据库模型转换为实体"""
        type_info = None
        if model.type_info:
            type_info = TypeInfo(
                name=model.type_info.name,
                is_primitive=model.type_info.is_primitive,
                is_array=model.type_info.is_array,
                is_generic=model.type_info.is_generic,
                generic_params=model.type_info.generic_params or [],
                nullable=model.type_info.nullable
            )
        
        return_type = None
        if model.return_type_info:
            return_type = TypeInfo(
                name=model.return_type_info.name,
                is_primitive=model.return_type_info.is_primitive,
                is_array=model.return_type_info.is_array,
                is_generic=model.return_type_info.is_generic,
                generic_params=model.return_type_info.generic_params or [],
                nullable=model.return_type_info.nullable
            )
        
        return Symbol(
            id=model.id,
            name=model.name,
            symbol_type=model.symbol_type,
            file_path=model.file_path,
            scope_id=model.scope_id,
            range=Range(
                start=Position(model.start_line, model.start_column, model.start_offset),
                end=Position(model.end_line, model.end_column, model.end_offset)
            ),
            type_info=type_info,
            return_type=return_type,
            visibility=model.visibility,
            is_static=model.is_static,
            is_abstract=model.is_abstract,
            is_readonly=model.is_readonly,
            is_async=model.is_async,
            is_exported=getattr(model, 'is_exported', False),
            is_export_default=getattr(model, 'is_export_default', False),
            extends=model.extends or [],
            implements=model.implements or [],
            documentation=model.documentation,
            decorators=model.decorators or [],
            metadata=model.meta_data or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _scope_model_to_entity(self, model: ScopeModel) -> Scope:
        """将作用域模型转换为实体"""
        return Scope(
            id=model.id,
            scope_type=model.scope_type,
            file_path=model.file_path,
            parent_id=model.parent_id,
            range=Range(
                start=Position(model.start_line, model.start_column, model.start_offset),
                end=Position(model.end_line, model.end_column, model.end_offset)
            ),
            metadata=model.meta_data or {}
        )
    
    def _reference_model_to_entity(self, model: ReferenceModel) -> Reference:
        """将引用模型转换为实体"""
        return Reference(
            id=model.id,
            symbol_id=model.symbol_id,
            file_path=model.file_path,
            reference_type=model.reference_type,
            position=Position(model.line, model.column, model.offset),
            context=model.context,
            metadata=model.meta_data or {},
            created_at=model.created_at
        )
