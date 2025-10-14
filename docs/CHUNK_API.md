# 代码 Chunk 服务 API 文档

## 概述

代码 Chunk 服务提供基于 AST 的智能代码分割功能，将 ArkTS 代码按语义单元（函数、类、组件等）分割成结构化的代码块（Chunk），并为每个 Chunk 添加上下文信息，使其适用于 RAG（检索增强生成）等应用场景。

## 核心特性

- **语义完整性**：基于 AST 分析，代码块边界对齐语义单元
- **上下文增强**：自动添加文件路径、类名、导入依赖等上下文信息
- **ArkUI 特化**：支持 ArkUI 组件、装饰器、状态变量等特性
- **持久化存储**：支持 Chunk 的数据库存储和查询
- **关系追溯**：保留 imports、调用、继承等依赖关系

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 基本使用

```python
import tree_sitter
import tree_sitter_arkts as ts_arkts
from arkts_processor.symbol_service.service import SymbolService
from arkts_processor.chunk_service.service import ChunkService

# 1. 设置解析器
ARKTS_LANGUAGE = tree_sitter.Language(ts_arkts.language())
parser = tree_sitter.Parser(ARKTS_LANGUAGE)

# 2. 初始化服务
symbol_service = SymbolService("symbols.db")
symbol_service.set_parser(parser)

chunk_service = ChunkService(symbol_service, "chunks.db")

# 3. 生成 Chunk
chunks = chunk_service.generate_chunks("path/to/file.ets")

# 4. 查询 Chunk
chunk = chunk_service.get_chunk_by_id(chunks[0].chunk_id)
print(chunk.name, chunk.type)
```

## 核心数据模型

### CodeChunk

代码块的核心数据模型。

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `chunk_id` | str | 唯一标识符，格式：`{文件路径}#{符号路径}` |
| `type` | ChunkType | Chunk 类型（function/class/component 等） |
| `path` | str | 源文件相对路径 |
| `name` | str | 主符号名称 |
| `context` | str | 层级上下文（类名/模块名） |
| `source` | str | 完整源代码文本（增强后） |
| `imports` | List[str] | 依赖的外部符号 |
| `comments` | str | 文档注释 |
| `metadata` | ChunkMetadata | 扩展元数据 |

**方法：**

- `to_dict()`: 转换为字典
- `get_enriched_source()`: 获取增强后的源代码（用于 embedding）

### ChunkMetadata

Chunk 的扩展元数据。

**字段说明：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `range` | PositionRange | 代码位置范围 |
| `decorators` | List[str] | 装饰器列表 |
| `visibility` | str | 可见性（public/private/protected） |
| `parameters` | List[Parameter] | 函数参数列表 |
| `return_type` | TypeInfo | 返回值类型 |
| `dependencies` | List[str] | 依赖的符号列表 |
| `tags` | List[str] | 语义标签 |

**ArkUI 特有字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| `component_type` | str | 组件类型（Entry/Component/Preview） |
| `state_vars` | List[Dict] | @State 状态变量 |
| `lifecycle_hooks` | List[str] | 生命周期方法 |
| `event_handlers` | List[str] | 事件处理器 |
| `resource_refs` | List[str] | 资源引用 |

### ChunkType (枚举)

Chunk 类型枚举值：

- `FUNCTION`: 函数/方法
- `CLASS`: 类
- `COMPONENT`: ArkUI 组件
- `MODULE`: 模块/命名空间
- `INTERFACE`: 接口
- `ENUM`: 枚举
- `FILE`: 小型工具文件

## API 参考

### ChunkService

主服务类，提供 Chunk 生成和管理功能。

#### 构造函数

```python
ChunkService(symbol_service: SymbolService, db_path: str = "arkts_chunks.db")
```

**参数：**
- `symbol_service`: 符号服务实例
- `db_path`: Chunk 数据库路径

#### generate_chunks

为单个文件生成所有 Chunk。

```python
def generate_chunks(file_path: str, save_to_db: bool = True) -> List[CodeChunk]
```

**参数：**
- `file_path`: 文件路径
- `save_to_db`: 是否保存到数据库（默认 True）

**返回：**
- `List[CodeChunk]`: 生成的 Chunk 列表

**示例：**

```python
chunks = chunk_service.generate_chunks("src/views/Login.ets")
for chunk in chunks:
    print(f"{chunk.name} ({chunk.type.value})")
```

#### generate_chunks_batch

批量生成多个文件的 Chunk。

```python
def generate_chunks_batch(file_paths: List[str], save_to_db: bool = True) -> Dict[str, List[CodeChunk]]
```

**参数：**
- `file_paths`: 文件路径列表
- `save_to_db`: 是否保存到数据库

**返回：**
- `Dict[str, List[CodeChunk]]`: 文件路径到 Chunk 列表的映射

#### get_chunk_by_id

根据 chunk_id 获取 Chunk。

```python
def get_chunk_by_id(chunk_id: str) -> Optional[CodeChunk]
```

**参数：**
- `chunk_id`: Chunk 唯一标识

**返回：**
- `CodeChunk` 对象或 None

#### get_chunks_by_file

获取文件的所有 Chunk。

```python
def get_chunks_by_file(file_path: str) -> List[CodeChunk]
```

**参数：**
- `file_path`: 文件路径

**返回：**
- `List[CodeChunk]`: Chunk 列表

#### get_chunks_by_type

按类型获取 Chunk。

```python
def get_chunks_by_type(chunk_type: ChunkType, file_path: Optional[str] = None) -> List[CodeChunk]
```

**参数：**
- `chunk_type`: Chunk 类型
- `file_path`: 文件路径（可选，用于过滤）

**返回：**
- `List[CodeChunk]`: Chunk 列表

**示例：**

```python
from arkts_processor.chunk_models import ChunkType

# 获取所有函数 Chunk
functions = chunk_service.get_chunks_by_type(ChunkType.FUNCTION)

# 获取某个文件的所有组件 Chunk
components = chunk_service.get_chunks_by_type(
    ChunkType.COMPONENT, 
    file_path="src/views/Home.ets"
)
```

#### search_chunks

搜索 Chunk（基于名称的简单搜索）。

```python
def search_chunks(query: str, limit: int = 10) -> List[CodeChunk]
```

**参数：**
- `query`: 搜索查询
- `limit`: 结果数量限制

**返回：**
- `List[CodeChunk]`: 匹配的 Chunk 列表

#### get_related_chunks

获取相关的 Chunk（基于依赖关系）。

```python
def get_related_chunks(chunk_id: str) -> List[CodeChunk]
```

**参数：**
- `chunk_id`: Chunk ID

**返回：**
- `List[CodeChunk]`: 相关 Chunk 列表

**相关性判断依据：**
- 导入依赖关系
- 同一上下文（同一类或模块）

#### refresh_file

刷新文件的 Chunk（删除旧的，生成新的）。

```python
def refresh_file(file_path: str) -> List[CodeChunk]
```

**参数：**
- `file_path`: 文件路径

**返回：**
- `List[CodeChunk]`: 新生成的 Chunk 列表

#### get_statistics

获取统计信息。

```python
def get_statistics(file_path: Optional[str] = None) -> Dict[str, int]
```

**参数：**
- `file_path`: 文件路径（可选）

**返回：**
- 统计字典，包含：
  - `total_chunks`: 总 Chunk 数
  - `by_type`: 按类型统计

**示例：**

```python
stats = chunk_service.get_statistics()
print(f"总 Chunk 数: {stats['total_chunks']}")
for chunk_type, count in stats['by_type'].items():
    print(f"  {chunk_type}: {count}")
```

#### export_chunks_to_json

将文件的 Chunk 导出为 JSON。

```python
def export_chunks_to_json(file_path: str, output_path: str)
```

**参数：**
- `file_path`: 源文件路径
- `output_path`: 输出 JSON 文件路径

#### get_embedable_texts

获取可用于 embedding 的文本列表。

```python
def get_embedable_texts(file_path: str) -> List[Dict[str, str]]
```

**参数：**
- `file_path`: 文件路径

**返回：**
- 字典列表，每个字典包含：
  - `chunk_id`: Chunk ID
  - `text`: 增强后的文本（包含上下文头）
  - `metadata`: 元数据（type, name, path, context）

**用途：**

用于生成 embedding 向量，支持语义检索。

**示例：**

```python
embedable = chunk_service.get_embedable_texts("src/utils/helper.ets")

for item in embedable:
    # 使用 embedding 模型生成向量
    vector = embedding_model.encode(item['text'])
    
    # 存储到向量数据库
    vector_db.insert(
        id=item['chunk_id'],
        vector=vector,
        metadata=item['metadata']
    )
```

## 上下文增强格式

每个 Chunk 的源代码在用于 embedding 前会添加元数据头。

### 通用格式

```
# file: {文件路径}
# class: {类名}
# function: {函数名}
# imports: [{导入列表}]
# decorators: [{装饰器列表}]
# tags: [{语义标签}]
# type: {返回类型}

{原始源代码}
```

### ArkUI 组件格式

```
# file: {文件路径}
# component: {组件名}
# component_type: {Entry/Component/Preview}
# decorators: [{装饰器列表}]
# state_vars: [{状态变量列表}]
# lifecycle_hooks: [{生命周期方法}]
# imports: [{导入列表}]
# tags: [{语义标签}]

{原始源代码}
```

## 使用场景

### 场景 1：为 RAG 系统生成代码块

```python
# 1. 处理整个项目
import glob

ets_files = glob.glob("src/**/*.ets", recursive=True)
results = chunk_service.generate_chunks_batch(ets_files)

# 2. 生成 embedding
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

for file_path, chunks in results.items():
    for chunk in chunks:
        text = chunk.get_enriched_source()
        embedding = model.encode(text)
        
        # 存储到向量数据库
        vector_db.insert(chunk.chunk_id, embedding, chunk.to_dict())
```

### 场景 2：代码理解辅助

```python
# 获取某个函数的完整上下文
chunk = chunk_service.get_chunk_by_id("src/utils/calc.ts#calculateScore")

print(f"函数: {chunk.name}")
print(f"所属: {chunk.context}")
print(f"依赖: {', '.join(chunk.imports)}")
print(f"标签: {', '.join(chunk.metadata.tags)}")

# 获取相关代码
related = chunk_service.get_related_chunks(chunk.chunk_id)
print(f"\n相关代码 ({len(related)} 个):")
for r in related:
    print(f"  - {r.name} ({r.type.value})")
```

### 场景 3：智能代码补全

```python
# 在当前文件中查找可用符号
current_file = "src/views/Home.ets"
chunks = chunk_service.get_chunks_by_file(current_file)

# 收集所有可导入的符号
available_symbols = []
for chunk in chunks:
    available_symbols.append({
        "name": chunk.name,
        "type": chunk.type.value,
        "context": chunk.context
    })

# 基于语义相似度排序
# ...
```

## 最佳实践

### 1. 批量处理大型项目

```python
import os
from pathlib import Path

def process_project(root_dir: str):
    ets_files = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.ets'):
                ets_files.append(os.path.join(root, file))
    
    # 批量处理，每次100个文件
    batch_size = 100
    for i in range(0, len(ets_files), batch_size):
        batch = ets_files[i:i + batch_size]
        chunk_service.generate_chunks_batch(batch)
        print(f"Processed {i + len(batch)}/{len(ets_files)} files")
```

### 2. 增量更新

```python
def update_file_chunks(file_path: str):
    """文件修改后更新其 Chunk"""
    # 删除旧 Chunk，生成新 Chunk
    new_chunks = chunk_service.refresh_file(file_path)
    
    # 更新向量数据库
    for chunk in new_chunks:
        text = chunk.get_enriched_source()
        embedding = embedding_model.encode(text)
        vector_db.upsert(chunk.chunk_id, embedding)
```

### 3. 定期清理

```python
def cleanup_orphaned_chunks():
    """清理已删除文件的 Chunk"""
    all_chunks = chunk_service.repository.get_all_chunks()
    
    for chunk in all_chunks:
        if not os.path.exists(chunk.path):
            chunk_service.delete_chunk(chunk.chunk_id)
            print(f"Deleted orphaned chunk: {chunk.chunk_id}")
```

## 性能考虑

- **批量处理**：使用 `generate_chunks_batch` 而非循环调用 `generate_chunks`
- **缓存策略**：Chunk 生成后会持久化，避免重复处理
- **增量更新**：只刷新修改的文件，使用 `refresh_file`
- **数据库优化**：定期执行 `VACUUM` 优化数据库

## 故障排除

### 问题：生成的 Chunk 数量为 0

**原因：**
- 文件解析失败
- 符号提取器未正确识别符号

**解决：**
```python
# 检查符号服务是否正常工作
symbols = symbol_service.get_document_symbols(file_path)
print(f"Symbols found: {len(symbols)}")
```

### 问题：元数据缺失

**原因：**
- 符号信息不完整

**解决：**
- 确保文件语法正确
- 检查 SymbolService 的配置

## 扩展功能

### 自定义 Chunk 类型

可以扩展 `ChunkType` 枚举支持更多类型：

```python
from arkts_processor.chunk_models import ChunkType

# 在实际使用中，建议通过配置或插件机制扩展
```

### 自定义元数据

可以通过 `metadata.tags` 添加自定义标签：

```python
# 在 ChunkMetadataBuilder 中添加自定义逻辑
```

## 相关资源

- [设计文档](../docs/chunk_design.md)
- [示例代码](../examples/chunk_example.py)
- [集成测试](../tests/test_chunk_integration.py)
