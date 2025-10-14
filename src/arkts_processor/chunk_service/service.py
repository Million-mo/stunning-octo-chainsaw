"""
Chunk 服务主类

提供代码块生成、查询和管理的统一接口。
"""

from typing import List, Optional, Dict, Any
from pathlib import Path

from ..symbol_service.service import SymbolService
from ..database.repository import DatabaseManager
from .extractor import ChunkExtractor
from .enricher import ContextEnricher
from .metadata_builder import ChunkMetadataBuilder
from .repository import ChunkRepository
from ..chunk_models import CodeChunk, ChunkType, ChunkSearchResult


class ChunkService:
    """Chunk 服务主类"""
    
    def __init__(self, 
                 symbol_service: SymbolService,
                 db_path: str = "arkts_chunks.db"):
        """
        初始化 Chunk 服务
        
        Args:
            symbol_service: 符号服务实例
            db_path: Chunk 数据库路径
        """
        self.symbol_service = symbol_service
        
        # 初始化数据库
        self.db_manager = DatabaseManager(db_path)
        self.repository = ChunkRepository(self.db_manager)
        
        # 初始化各个组件
        self.metadata_builder = ChunkMetadataBuilder()
        self.enricher = ContextEnricher()
    
    def generate_chunks(self, file_path: str, save_to_db: bool = True) -> List[CodeChunk]:
        """
        为单个文件生成所有 Chunk
        
        Args:
            file_path: 文件路径
            save_to_db: 是否保存到数据库
            
        Returns:
            CodeChunk 列表
        """
        # 首先使用 SymbolService 处理文件
        process_result = self.symbol_service.process_file(file_path)
        
        # 获取符号和作用域
        symbols = self.symbol_service.repository.get_symbols_by_file(file_path)
        scopes = self.symbol_service.repository.get_scopes_by_file(file_path)
        
        # 读取源代码
        with open(file_path, 'rb') as f:
            source_code = f.read()
        
        # 创建 ChunkExtractor
        extractor = ChunkExtractor(file_path, source_code)
        
        # 提取原始 Chunk
        raw_chunks = extractor.extract_chunks(symbols, scopes)
        
        # 构建元数据
        for chunk in raw_chunks:
            if chunk.symbol_id:
                # 查找对应的符号
                symbol = next((s for s in symbols if s.id == chunk.symbol_id), None)
                if symbol:
                    # 构建元数据
                    metadata = self.metadata_builder.build_metadata(symbol, chunk.source)
                    chunk.metadata = metadata
        
        # 上下文增强
        enriched_chunks = self.enricher.enrich_chunks(raw_chunks, symbols, scopes)
        
        # 保存到数据库
        if save_to_db:
            self.repository.save_chunks_batch(enriched_chunks)
        
        return enriched_chunks
    
    def generate_chunks_batch(self, 
                            file_paths: List[str], 
                            save_to_db: bool = True) -> Dict[str, List[CodeChunk]]:
        """
        批量生成多个文件的 Chunk
        
        Args:
            file_paths: 文件路径列表
            save_to_db: 是否保存到数据库
            
        Returns:
            文件路径到 CodeChunk 列表的映射
        """
        results = {}
        
        for file_path in file_paths:
            try:
                chunks = self.generate_chunks(file_path, save_to_db)
                results[file_path] = chunks
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                results[file_path] = []
        
        return results
    
    def get_chunk_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """
        根据 chunk_id 获取 Chunk
        
        Args:
            chunk_id: Chunk 唯一标识
            
        Returns:
            CodeChunk 对象或 None
        """
        return self.repository.get_chunk_by_id(chunk_id)
    
    def get_chunks_by_file(self, file_path: str) -> List[CodeChunk]:
        """
        获取文件的所有 Chunk
        
        Args:
            file_path: 文件路径
            
        Returns:
            CodeChunk 列表
        """
        return self.repository.get_chunks_by_file(file_path)
    
    def get_chunks_by_type(self, chunk_type: ChunkType, file_path: Optional[str] = None) -> List[CodeChunk]:
        """
        按类型获取 Chunk
        
        Args:
            chunk_type: Chunk 类型
            file_path: 文件路径（可选）
            
        Returns:
            CodeChunk 列表
        """
        return self.repository.get_chunks_by_type(chunk_type, file_path)
    
    def search_chunks(self, query: str, limit: int = 10) -> List[CodeChunk]:
        """
        搜索 Chunk（基于名称的简单搜索）
        
        注：语义搜索需要嵌入向量，当前仅支持名称搜索
        
        Args:
            query: 搜索查询
            limit: 结果数量限制
            
        Returns:
            CodeChunk 列表
        """
        chunks = self.repository.search_chunks_by_name(query)
        return chunks[:limit]
    
    def get_related_chunks(self, chunk_id: str) -> List[CodeChunk]:
        """
        获取相关的 Chunk（基于依赖关系）
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            相关 CodeChunk 列表
        """
        # 获取当前 Chunk
        chunk = self.repository.get_chunk_by_id(chunk_id)
        if not chunk:
            return []
        
        related_chunks = []
        
        # 基于导入依赖查找相关 Chunk
        if chunk.imports:
            for import_name in chunk.imports:
                # 搜索名称匹配的 Chunk
                matching_chunks = self.repository.search_chunks_by_name(import_name)
                related_chunks.extend(matching_chunks)
        
        # 基于同一上下文查找相关 Chunk（同一个类或模块）
        if chunk.context:
            context_chunks = self.repository.get_chunks_by_file(chunk.path)
            for ctx_chunk in context_chunks:
                if ctx_chunk.context == chunk.context and ctx_chunk.chunk_id != chunk.chunk_id:
                    related_chunks.append(ctx_chunk)
        
        # 去重
        seen_ids = set()
        unique_chunks = []
        for related in related_chunks:
            if related.chunk_id not in seen_ids:
                seen_ids.add(related.chunk_id)
                unique_chunks.append(related)
        
        return unique_chunks
    
    def refresh_file(self, file_path: str) -> List[CodeChunk]:
        """
        刷新文件的 Chunk（删除旧的，生成新的）
        
        Args:
            file_path: 文件路径
            
        Returns:
            新生成的 CodeChunk 列表
        """
        # 删除旧的 Chunk
        self.repository.delete_chunks_by_file(file_path)
        
        # 重新生成
        return self.generate_chunks(file_path, save_to_db=True)
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """
        删除 Chunk
        
        Args:
            chunk_id: Chunk ID
            
        Returns:
            是否删除成功
        """
        return self.repository.delete_chunk(chunk_id)
    
    def delete_chunks_by_file(self, file_path: str) -> int:
        """
        删除文件的所有 Chunk
        
        Args:
            file_path: 文件路径
            
        Returns:
            删除的数量
        """
        return self.repository.delete_chunks_by_file(file_path)
    
    def get_statistics(self, file_path: Optional[str] = None) -> Dict[str, int]:
        """
        获取统计信息
        
        Args:
            file_path: 文件路径（可选）
            
        Returns:
            统计字典
        """
        return self.repository.get_statistics(file_path)
    
    def export_chunks_to_json(self, file_path: str, output_path: str):
        """
        将文件的 Chunk 导出为 JSON
        
        Args:
            file_path: 源文件路径
            output_path: 输出 JSON 文件路径
        """
        import json
        
        chunks = self.get_chunks_by_file(file_path)
        chunks_data = [chunk.to_dict() for chunk in chunks]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)
    
    def get_embedable_texts(self, file_path: str) -> List[Dict[str, str]]:
        """
        获取可用于 embedding 的文本列表
        
        Args:
            file_path: 文件路径
            
        Returns:
            包含 chunk_id 和增强文本的字典列表
        """
        chunks = self.get_chunks_by_file(file_path)
        
        embedable_texts = []
        for chunk in chunks:
            embedable_texts.append({
                "chunk_id": chunk.chunk_id,
                "text": chunk.get_enriched_source(),
                "metadata": {
                    "type": chunk.type.value,
                    "name": chunk.name,
                    "path": chunk.path,
                    "context": chunk.context
                }
            })
        
        return embedable_texts
