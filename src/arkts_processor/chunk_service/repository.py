"""
Chunk 数据库存储层

提供 Chunk 的持久化存储和查询功能。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Index
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import Session

from ..database.schema import Base
from ..database.repository import DatabaseManager
from ..chunk_models import CodeChunk, ChunkType, ChunkMetadata, PositionRange, Parameter, TypeInfo


class ChunkModel(Base):
    """Chunk 数据库模型"""
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chunk_id = Column(String(512), unique=True, nullable=False, index=True)
    type = Column(String(50), nullable=False)
    path = Column(String(512), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    context = Column(String(255), nullable=True)
    source = Column(Text, nullable=False)
    imports = Column(SQLiteJSON, default=list)
    comments = Column(Text, nullable=True)
    metadata_json = Column(SQLiteJSON, nullable=True)
    symbol_id = Column(Integer, nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index("idx_chunk_id", "chunk_id"),
        Index("idx_chunk_path", "path"),
        Index("idx_chunk_name", "name"),
        Index("idx_chunk_type", "type"),
    )


class ChunkRepository:
    """Chunk 存储库"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化 Chunk 存储库
        
        Args:
            db_manager: 数据库管理器
        """
        self.db_manager = db_manager
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """确保 chunks 表存在"""
        ChunkModel.__table__.create(self.db_manager.engine, checkfirst=True)
    
    def save_chunk(self, chunk: CodeChunk) -> int:
        """
        保存单个 Chunk
        
        Args:
            chunk: CodeChunk 对象
            
        Returns:
            Chunk ID
        """
        with self.db_manager.get_session() as session:
            # 检查是否已存在
            existing = session.query(ChunkModel).filter_by(chunk_id=chunk.chunk_id).first()
            
            if existing:
                # 更新现有记录
                self._update_chunk_model(existing, chunk)
                existing.updated_at = datetime.utcnow()
                session.commit()
                return existing.id
            else:
                # 创建新记录
                chunk_model = self._chunk_to_model(chunk)
                session.add(chunk_model)
                session.commit()
                return chunk_model.id
    
    def save_chunks_batch(self, chunks: List[CodeChunk]) -> List[int]:
        """
        批量保存 Chunk
        
        Args:
            chunks: CodeChunk 列表
            
        Returns:
            Chunk ID 列表
        """
        chunk_ids = []
        with self.db_manager.get_session() as session:
            for chunk in chunks:
                # 检查是否已存在
                existing = session.query(ChunkModel).filter_by(chunk_id=chunk.chunk_id).first()
                
                if existing:
                    self._update_chunk_model(existing, chunk)
                    existing.updated_at = datetime.utcnow()
                    chunk_ids.append(existing.id)
                else:
                    chunk_model = self._chunk_to_model(chunk)
                    session.add(chunk_model)
                    session.flush()
                    chunk_ids.append(chunk_model.id)
            
            session.commit()
        
        return chunk_ids
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """
        根据 chunk_id 获取 Chunk
        
        Args:
            chunk_id: Chunk 唯一标识
            
        Returns:
            CodeChunk 对象或 None
        """
        with self.db_manager.get_session() as session:
            chunk_model = session.query(ChunkModel).filter_by(chunk_id=chunk_id).first()
            if chunk_model:
                return self._model_to_chunk(chunk_model)
        return None
    
    def get_chunks_by_file(self, file_path: str) -> List[CodeChunk]:
        """
        获取文件的所有 Chunk
        
        Args:
            file_path: 文件路径
            
        Returns:
            CodeChunk 列表
        """
        with self.db_manager.get_session() as session:
            chunk_models = session.query(ChunkModel).filter_by(path=file_path).all()
            return [self._model_to_chunk(model) for model in chunk_models]
    
    def get_chunks_by_type(self, chunk_type: ChunkType, file_path: Optional[str] = None) -> List[CodeChunk]:
        """
        按类型获取 Chunk
        
        Args:
            chunk_type: Chunk 类型
            file_path: 文件路径（可选）
            
        Returns:
            CodeChunk 列表
        """
        with self.db_manager.get_session() as session:
            query = session.query(ChunkModel).filter_by(type=chunk_type.value)
            
            if file_path:
                query = query.filter_by(path=file_path)
            
            chunk_models = query.all()
            return [self._model_to_chunk(model) for model in chunk_models]
    
    def search_chunks_by_name(self, name_pattern: str) -> List[CodeChunk]:
        """
        按名称搜索 Chunk
        
        Args:
            name_pattern: 名称模式（支持 SQL LIKE 语法）
            
        Returns:
            CodeChunk 列表
        """
        with self.db_manager.get_session() as session:
            chunk_models = session.query(ChunkModel).filter(
                ChunkModel.name.like(f"%{name_pattern}%")
            ).all()
            return [self._model_to_chunk(model) for model in chunk_models]
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """
        删除 Chunk
        
        Args:
            chunk_id: Chunk 唯一标识
            
        Returns:
            是否删除成功
        """
        with self.db_manager.get_session() as session:
            chunk_model = session.query(ChunkModel).filter_by(chunk_id=chunk_id).first()
            if chunk_model:
                session.delete(chunk_model)
                session.commit()
                return True
        return False
    
    def delete_chunks_by_file(self, file_path: str) -> int:
        """
        删除文件的所有 Chunk
        
        Args:
            file_path: 文件路径
            
        Returns:
            删除的 Chunk 数量
        """
        with self.db_manager.get_session() as session:
            count = session.query(ChunkModel).filter_by(path=file_path).delete()
            session.commit()
            return count
    
    def get_all_chunks(self, limit: Optional[int] = None) -> List[CodeChunk]:
        """
        获取所有 Chunk
        
        Args:
            limit: 限制数量（可选）
            
        Returns:
            CodeChunk 列表
        """
        with self.db_manager.get_session() as session:
            query = session.query(ChunkModel)
            
            if limit:
                query = query.limit(limit)
            
            chunk_models = query.all()
            return [self._model_to_chunk(model) for model in chunk_models]
    
    def get_statistics(self, file_path: Optional[str] = None) -> Dict[str, int]:
        """
        获取统计信息
        
        Args:
            file_path: 文件路径（可选）
            
        Returns:
            统计字典
        """
        with self.db_manager.get_session() as session:
            query = session.query(ChunkModel)
            
            if file_path:
                query = query.filter_by(path=file_path)
            
            total = query.count()
            
            # 按类型统计
            type_stats = {}
            for chunk_type in ChunkType:
                count = query.filter_by(type=chunk_type.value).count()
                type_stats[chunk_type.value] = count
            
            return {
                "total_chunks": total,
                "by_type": type_stats
            }
    
    def _chunk_to_model(self, chunk: CodeChunk) -> ChunkModel:
        """
        将 CodeChunk 转换为数据库模型
        
        Args:
            chunk: CodeChunk 对象
            
        Returns:
            ChunkModel 对象
        """
        metadata_json = None
        if chunk.metadata:
            metadata_json = chunk.metadata.to_dict()
        
        return ChunkModel(
            chunk_id=chunk.chunk_id,
            type=chunk.type.value,
            path=chunk.path,
            name=chunk.name,
            context=chunk.context,
            source=chunk.source,
            imports=chunk.imports,
            comments=chunk.comments,
            metadata_json=metadata_json,
            symbol_id=chunk.symbol_id
        )
    
    def _update_chunk_model(self, model: ChunkModel, chunk: CodeChunk):
        """
        更新数据库模型
        
        Args:
            model: ChunkModel 对象
            chunk: CodeChunk 对象
        """
        model.type = chunk.type.value
        model.path = chunk.path
        model.name = chunk.name
        model.context = chunk.context
        model.source = chunk.source
        model.imports = chunk.imports
        model.comments = chunk.comments
        
        if chunk.metadata:
            model.metadata_json = chunk.metadata.to_dict()
        
        if chunk.symbol_id:
            model.symbol_id = chunk.symbol_id
    
    def _model_to_chunk(self, model: ChunkModel) -> CodeChunk:
        """
        将数据库模型转换为 CodeChunk
        
        Args:
            model: ChunkModel 对象
            
        Returns:
            CodeChunk 对象
        """
        # 解析元数据
        metadata = None
        if model.metadata_json:
            metadata = self._dict_to_metadata(model.metadata_json)
        
        return CodeChunk(
            chunk_id=model.chunk_id,
            type=ChunkType(model.type),
            path=model.path,
            name=model.name,
            context=model.context or "",
            source=model.source,
            imports=model.imports or [],
            comments=model.comments,
            metadata=metadata,
            symbol_id=model.symbol_id,
            created_at=model.created_at,
            updated_at=model.updated_at
        )
    
    def _dict_to_metadata(self, data: Dict[str, Any]) -> ChunkMetadata:
        """
        将字典转换为 ChunkMetadata
        
        Args:
            data: 元数据字典
            
        Returns:
            ChunkMetadata 对象
        """
        # 解析位置范围
        range_data = data.get("range", {})
        position_range = PositionRange(
            start_line=range_data.get("start_line", 0),
            end_line=range_data.get("end_line", 0),
            start_column=range_data.get("start_column", 0),
            end_column=range_data.get("end_column", 0)
        )
        
        # 解析参数列表
        parameters = []
        for param_data in data.get("parameters", []):
            param = Parameter(
                name=param_data.get("name", ""),
                type=param_data.get("type", "any"),
                default_value=param_data.get("default_value")
            )
            parameters.append(param)
        
        # 解析返回类型
        return_type = None
        if "return_type" in data:
            rt_data = data["return_type"]
            return_type = TypeInfo(
                name=rt_data.get("name", ""),
                is_primitive=rt_data.get("is_primitive", False),
                is_array=rt_data.get("is_array", False),
                generic_params=rt_data.get("generic_params", [])
            )
        
        # 创建元数据对象
        metadata = ChunkMetadata(
            range=position_range,
            decorators=data.get("decorators", []),
            visibility=data.get("visibility", "public"),
            parameters=parameters,
            return_type=return_type,
            dependencies=data.get("dependencies", []),
            tags=data.get("tags", [])
        )
        
        # ArkUI 特有字段
        if "component_type" in data:
            metadata.component_type = data["component_type"]
        if "state_vars" in data:
            metadata.state_vars = data["state_vars"]
        if "lifecycle_hooks" in data:
            metadata.lifecycle_hooks = data["lifecycle_hooks"]
        if "event_handlers" in data:
            metadata.event_handlers = data["event_handlers"]
        if "resource_refs" in data:
            metadata.resource_refs = data["resource_refs"]
        
        return metadata
