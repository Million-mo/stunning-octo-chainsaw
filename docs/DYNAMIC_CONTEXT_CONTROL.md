# 动态上下文控制方案设计 - 技术细节总结

## 概述

本文档详细描述了代码 Chunk 服务中**动态上下文控制方案**的技术实现细节，该方案旨在为不同大小的代码块（Chunk）提供智能化的上下文增强策略，以优化 RAG 系统中的检索和召回效果。

## 设计理念

### 核心思想

根据 Chunk 大小实施**分级上下文增强策略**，避免"一刀切"的上下文处理方式：

- **小型 Chunk (<500 tokens)**: 丰富上下文信息，补充语义不足
- **中型 Chunk (500-2000 tokens)**: 平衡策略，摘要 + 完整内容双向量
- **大型 Chunk (>2000 tokens)**: 层级化拆分，避免上下文冗余

### 设计目标

1. ✅ **提升召回准确性**: 为小型 Chunk 添加足够的上下文信息
2. ✅ **控制噪声引入**: 动态调整上下文详细程度，避免过多无关信息
3. ✅ **优化 Embedding 效果**: 生成最适合向量化的文本结构
4. ✅ **保持语义完整性**: 确保每个 Chunk 的语义边界清晰

## 技术架构

### 1. 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                 ChunkService (主服务)                    │
│              协调上下文增强流程                            │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌─────────────────┐  ┌──────────────┐
│ChunkExtractor│  │ContextEnricher  │  │ChunkMetadata │
│              │  │                 │  │   Builder    │
│提取代码块     │  │✨动态上下文增强✨│  │构建元数据     │
└──────────────┘  └─────────────────┘  └──────────────┘
```

### 2. 关键模块

| 模块 | 文件路径 | 主要职责 |
|------|---------|---------|
| **ContextEnricher** | `chunk_service/enricher.py` | 上下文增强核心逻辑 |
| **ChunkMetadataBuilder** | `chunk_service/metadata_builder.py` | 元数据构建与标签生成 |
| **ChunkExtractor** | `chunk_service/extractor.py` | 代码块提取 |

## 上下文增强策略详解

### 策略 1: 分级元数据头

根据 Chunk 类型和大小，动态选择元数据头的详细程度。

#### 实现位置
`src/arkts_processor/chunk_service/enricher.py`

#### 核心方法

```python
def format_metadata_headers(self, chunk: CodeChunk, symbol: Symbol) -> str:
    """
    格式化元数据头 - 根据 Chunk 类型选择不同格式
    
    Args:
        chunk: CodeChunk 对象
        symbol: 符号对象
        
    Returns:
        元数据头字符串
    """
    if chunk.type == ChunkType.COMPONENT:
        # ArkUI 组件使用丰富的元数据头
        return self._format_component_headers(chunk, symbol)
    else:
        # 通用类型使用标准元数据头
        return self._format_general_headers(chunk, symbol)
```

#### 元数据头层级

**优先级分层**：

1. **必要层 (L1)** - 始终包含
   - `file`: 文件路径
   - `type`: Chunk 类型（function/class/component）
   - `name`: 符号名称

2. **重要层 (L2)** - 中小型 Chunk 包含
   - `context`: 所属上下文（类名/模块名）
   - `imports`: 导入依赖列表
   - `tags`: 语义标签

3. **辅助层 (L3)** - 小型 Chunk 包含
   - `decorators`: 装饰器列表
   - `visibility`: 可见性（public/private）
   - `parameters`: 函数参数（简化签名）
   - `return_type`: 返回类型

4. **详细层 (L4)** - ArkUI 组件特化
   - `component_type`: 组件类型（Entry/Component）
   - `state_vars`: 状态变量列表
   - `lifecycle_hooks`: 生命周期方法
   - `event_handlers`: 事件处理器

### 策略 2: 通用函数/类的上下文增强

#### 元数据头格式

```python
def _format_general_headers(self, chunk: CodeChunk, symbol: Symbol) -> List[str]:
    """
    通用元数据头 - 适用于函数、类、接口等
    """
    headers = []
    
    # L1: 必要层
    headers.append(f"# file: {chunk.path}")
    
    # L2: 重要层 - 上下文信息
    if chunk.context:
        if chunk.type == ChunkType.FUNCTION:
            headers.append(f"# class: {chunk.context}")
        elif chunk.type == ChunkType.CLASS:
            headers.append(f"# module: {chunk.context}")
    
    headers.append(f"# {chunk.type.value}: {chunk.name}")
    
    # L2: 依赖关系
    if chunk.imports:
        imports_str = ", ".join(chunk.imports)
        headers.append(f"# imports: [{imports_str}]")
    
    # L3: 辅助信息（条件添加）
    if chunk.metadata:
        if chunk.metadata.decorators:
            decorators_str = ", ".join(chunk.metadata.decorators)
            headers.append(f"# decorators: [{decorators_str}]")
        
        if chunk.metadata.tags:
            tags_str = ", ".join(chunk.metadata.tags)
            headers.append(f"# tags: [{tags_str}]")
        
        if chunk.metadata.return_type:
            headers.append(f"# type: {chunk.metadata.return_type.name}")
    
    return headers
```

#### 输出示例

**小型函数 (约 50 tokens)**:
```
# file: src/services/user_service.ts
# class: UserService
# function: getUserProfile
# imports: [UserRepo, AuthService]
# tags: [async, public]
# type: Promise<User>

async function getUserProfile(id: string): Promise<User> {
  return await UserRepo.findById(id);
}
```

**中型类 (约 800 tokens)**:
```
# file: src/models/user.ts
# class: User
# imports: [BaseModel, Validator]
# tags: [class, has-constructor]

export class User extends BaseModel {
  // ... 完整类定义 ...
}
```

### 策略 3: ArkUI 组件的特化增强

#### 元数据头格式

```python
def _format_component_headers(self, chunk: CodeChunk, symbol: Symbol) -> List[str]:
    """
    ArkUI 组件元数据头 - 包含组件特有信息
    """
    headers = []
    
    # L1: 必要层
    headers.append(f"# file: {chunk.path}")
    headers.append(f"# component: {chunk.name}")
    
    # L4: ArkUI 详细层
    if chunk.metadata:
        if chunk.metadata.component_type:
            headers.append(f"# component_type: {chunk.metadata.component_type}")
        
        if chunk.metadata.decorators:
            decorators_str = ", ".join(chunk.metadata.decorators)
            headers.append(f"# decorators: [{decorators_str}]")
        
        # 状态变量 - 关键信息
        if chunk.metadata.state_vars:
            state_vars_str = ", ".join([
                f"{var['name']}: {var['type']}" 
                for var in chunk.metadata.state_vars
            ])
            headers.append(f"# state_vars: [{state_vars_str}]")
        
        # 生命周期方法 - 组件行为特征
        if chunk.metadata.lifecycle_hooks:
            hooks_str = ", ".join(chunk.metadata.lifecycle_hooks)
            headers.append(f"# lifecycle_hooks: [{hooks_str}]")
    
    # L2: 依赖关系
    if chunk.imports:
        imports_str = ", ".join(chunk.imports)
        headers.append(f"# imports: [{imports_str}]")
    
    # L2: 语义标签
    if chunk.metadata and chunk.metadata.tags:
        tags_str = ", ".join(chunk.metadata.tags)
        headers.append(f"# tags: [{tags_str}]")
    
    return headers
```

#### 输出示例

```
# file: src/views/Login.ets
# component: LoginView
# component_type: Entry
# decorators: [@Component, @Entry]
# state_vars: [username: string, password: string, isLoading: boolean]
# lifecycle_hooks: [aboutToAppear, onPageShow]
# imports: [router, promptAction, UserService]
# tags: [ui-component, entry, has-state]

@Component
@Entry
struct LoginView {
  @State username: string = ''
  @State password: string = ''
  @State isLoading: boolean = false
  
  aboutToAppear() {
    // 初始化逻辑
  }
  
  onPageShow() {
    // 页面显示逻辑
  }
  
  build() {
    // UI 构建
  }
}
```

## 语义标签生成系统

### 标签提取逻辑

实现位置：`src/arkts_processor/chunk_service/metadata_builder.py`

```python
def _extract_tags(self, symbol: Symbol) -> List[str]:
    """
    提取语义标签 - 多维度标签系统
    """
    tags = []
    
    # 维度 1: 符号属性
    if symbol.is_async: tags.append("async")
    if symbol.is_static: tags.append("static")
    if symbol.is_abstract: tags.append("abstract")
    if symbol.is_readonly: tags.append("readonly")
    
    # 维度 2: 可见性
    if symbol.visibility == Visibility.PUBLIC:
        tags.append("public")
    elif symbol.visibility == Visibility.PRIVATE:
        tags.append("private")
    
    # 维度 3: 符号类型
    if symbol.symbol_type == SymbolType.COMPONENT:
        tags.append("ui-component")
        if symbol.component_type:
            tags.append(symbol.component_type.lower())
    
    # 维度 4: 函数特性
    elif symbol.symbol_type in [SymbolType.FUNCTION, SymbolType.METHOD]:
        tags.append("function")
        if not self._has_side_effects(symbol):
            tags.append("pure-function")
    
    # 维度 5: ArkUI 特有
    if symbol.name in self.LIFECYCLE_HOOKS:
        tags.append("lifecycle")
    
    return tags
```

### 标签体系

| 标签类别 | 标签示例 | 用途 |
|---------|---------|------|
| **属性标签** | `async`, `static`, `readonly` | 描述符号的代码属性 |
| **可见性标签** | `public`, `private`, `protected` | 描述访问控制 |
| **类型标签** | `function`, `class`, `interface` | 描述符号类型 |
| **纯度标签** | `pure-function`, `has-side-effects` | 描述函数纯度 |
| **UI 标签** | `ui-component`, `entry`, `preview` | ArkUI 组件特征 |
| **生命周期标签** | `lifecycle`, `event-handler` | ArkUI 行为特征 |

### 标签的作用

1. **检索优化**: 支持基于标签的过滤和排序
2. **语义理解**: 帮助 embedding 模型理解代码特性
3. **权重调整**: 在 RAG 系统中作为重排序的依据

## 动态噪声控制机制

### 问题背景

为小型函数添加过多上下文可能引入噪声，降低检索精度。

### 解决方案

#### 1. Token 预算控制

```python
# 伪代码示例（当前实现的设计思路）
def calculate_context_budget(chunk_size: int) -> dict:
    """
    根据 chunk 大小计算上下文预算
    
    Args:
        chunk_size: Chunk 的 token 数量
        
    Returns:
        上下文预算配置
    """
    if chunk_size < 100:
        # 小型 Chunk: 充足的上下文预算
        return {
            "max_context_tokens": 200,  # 最多 200 tokens 上下文
            "include_siblings": True,    # 包含兄弟节点
            "include_parents": True,     # 包含父节点
            "detail_level": "high"       # 高详细度
        }
    elif chunk_size < 500:
        # 中小型 Chunk: 适度上下文
        return {
            "max_context_tokens": 100,
            "include_siblings": False,
            "include_parents": True,
            "detail_level": "medium"
        }
    else:
        # 大型 Chunk: 最少上下文
        return {
            "max_context_tokens": 50,
            "include_siblings": False,
            "include_parents": False,
            "detail_level": "low"
        }
```

#### 2. 上下文优先级队列

当前实现通过**元数据头分层**实现优先级控制：

```
L1 (必要) > L2 (重要) > L3 (辅助) > L4 (详细)
```

根据 token 预算，从高优先级到低优先级依次添加上下文，直到达到预算上限。

#### 3. 兄弟节点简化策略

**目标**: 为小型函数提供同一作用域内的其他方法签名，但不包含完整实现。

**实现思路**（未来扩展）:

```python
def _get_sibling_signatures(symbol: Symbol, scope: Scope) -> List[str]:
    """
    获取兄弟节点的简化签名
    
    Returns:
        签名列表，如: ["getName(): string", "setAge(age: number): void"]
    """
    siblings = []
    for sibling_symbol in scope.symbols.values():
        if sibling_symbol.id != symbol.id:
            sig = f"{sibling_symbol.name}({_format_params(sibling_symbol.parameters)})"
            if sibling_symbol.return_type:
                sig += f": {sibling_symbol.return_type.name}"
            siblings.append(sig)
    return siblings[:5]  # 最多 5 个兄弟节点
```

**元数据头示例**（未来可能的格式）:

```
# file: src/models/user.ts
# class: User
# method: getName
# siblings: [setName(name: string): void, getAge(): number, setAge(age: number): void]
# tags: [public, pure-function]

getName(): string {
  return this.name;
}
```

## 依赖关系追溯

### 依赖提取

实现位置：`src/arkts_processor/chunk_service/metadata_builder.py`

```python
def calculate_dependencies(self, symbol: Symbol) -> List[str]:
    """
    计算符号的依赖关系
    """
    dependencies = set()
    
    # 1. 从类型信息中提取
    if symbol.type_info and not symbol.type_info.is_primitive:
        dependencies.add(symbol.type_info.name)
    
    if symbol.return_type and not symbol.return_type.is_primitive:
        dependencies.add(symbol.return_type.name)
    
    # 2. 从参数中提取
    for param in symbol.parameters:
        if param.type_info and not param.type_info.is_primitive:
            dependencies.add(param.type_info.name)
    
    # 3. 从继承和实现中提取
    dependencies.update(symbol.extends)
    dependencies.update(symbol.implements)
    
    # 4. 从成员中提取
    for member in symbol.members:
        if member.type_info and not member.type_info.is_primitive:
            dependencies.add(member.type_info.name)
    
    # 5. ArkUI 资源引用
    if symbol.resource_refs:
        dependencies.update(symbol.resource_refs)
    
    return sorted(list(dependencies))
```

### 依赖关系的用途

1. **相关 Chunk 查询**: 通过 `get_related_chunks()` 查找依赖的代码块
2. **上下文增强**: 在 `imports` 字段中展示
3. **知识图谱**: 构建代码依赖关系图

## 实际应用示例

### 示例 1: 小型工具函数

**原始代码** (约 30 tokens):
```typescript
function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}
```

**增强后** (约 80 tokens，上下文占比 63%):
```
# file: src/utils/date_helper.ts
# module: DateHelper
# function: formatDate
# tags: [public, pure-function]
# type: string

function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}
```

**分析**:
- ✅ 添加了文件路径和模块上下文
- ✅ 标记为纯函数，有助于理解其特性
- ✅ 上下文与代码比例合理（约 2:1）

### 示例 2: 中型类方法

**原始代码** (约 150 tokens):
```typescript
async getUserProfile(userId: string): Promise<UserProfile> {
  const user = await this.userRepo.findById(userId);
  if (!user) throw new NotFoundException();
  return this.transformToProfile(user);
}
```

**增强后** (约 180 tokens，上下文占比 17%):
```
# file: src/services/user_service.ts
# class: UserService
# method: getUserProfile
# imports: [UserRepo, NotFoundException]
# tags: [async, public]
# type: Promise<UserProfile>

async getUserProfile(userId: string): Promise<UserProfile> {
  const user = await this.userRepo.findById(userId);
  if (!user) throw new NotFoundException();
  return this.transformToProfile(user);
}
```

**分析**:
- ✅ 上下文适度，不会淹没主要内容
- ✅ 依赖关系清晰（UserRepo, NotFoundException）
- ✅ 异步特性明确标记

### 示例 3: ArkUI 组件

**原始代码** (约 300 tokens):
```typescript
@Component
@Entry
struct LoginView {
  @State username: string = ''
  @State password: string = ''
  
  aboutToAppear() {
    console.log('Login page loaded');
  }
  
  async handleLogin() {
    await AuthService.login(this.username, this.password);
  }
  
  build() {
    Column() {
      TextInput({ placeholder: 'Username' })
        .onChange((value) => { this.username = value })
      
      TextInput({ placeholder: 'Password', type: InputType.Password })
        .onChange((value) => { this.password = value })
      
      Button('Login')
        .onClick(() => this.handleLogin())
    }
  }
}
```

**增强后** (约 360 tokens，上下文占比 17%):
```
# file: src/views/Login.ets
# component: LoginView
# component_type: Entry
# decorators: [@Component, @Entry]
# state_vars: [username: string, password: string]
# lifecycle_hooks: [aboutToAppear]
# imports: [AuthService]
# tags: [ui-component, entry, has-state]

@Component
@Entry
struct LoginView {
  // ... 完整组件代码 ...
}
```

**分析**:
- ✅ 组件特征完整（装饰器、状态、生命周期）
- ✅ 有助于快速理解组件用途
- ✅ 上下文信息紧凑，避免冗余

## 性能优化

### 1. 批量增强优化

```python
def enrich_chunks(self, chunks: List[CodeChunk], symbols: List[Symbol], 
                 scopes: List[Scope]) -> List[CodeChunk]:
    """
    批量增强 - 减少重复计算
    """
    # 预先构建映射，避免重复查找
    symbol_map = {symbol.id: symbol for symbol in symbols if symbol.id}
    scope_map = {scope.id: scope for scope in scopes}
    
    enriched_chunks = []
    for chunk in chunks:
        if chunk.symbol_id and chunk.symbol_id in symbol_map:
            symbol = symbol_map[chunk.symbol_id]
            enriched_chunk = self.enrich_chunk(chunk, symbol, scope_map)
            enriched_chunks.append(enriched_chunk)
    
    return enriched_chunks
```

### 2. 元数据缓存

元数据构建结果会随 Chunk 一起持久化，避免重复计算。

## 测试覆盖

### 单元测试

文件：`tests/test_context_enricher.py`

测试覆盖：
- ✅ 函数 Chunk 增强
- ✅ 类 Chunk 增强
- ✅ ArkUI 组件增强
- ✅ 批量增强
- ✅ 空元数据处理
- ✅ 上下文路径构建

### 集成测试

文件：`tests/test_chunk_integration.py`

测试场景：
- ✅ 端到端 Chunk 生成
- ✅ 上下文增强验证
- ✅ 可嵌入文本生成

## 未来优化方向

### 1. 智能上下文预算

基于实际 token 计算，动态调整上下文详细度：

```python
# 未来实现
def estimate_tokens(text: str) -> int:
    """估算文本的 token 数量"""
    return len(text.split()) * 1.3  # 简化估算

def adjust_context_by_budget(chunk: CodeChunk, max_tokens: int):
    """根据 token 预算调整上下文"""
    current_tokens = estimate_tokens(chunk.source)
    if current_tokens < 100:
        return "high_detail"
    elif current_tokens < 500:
        return "medium_detail"
    else:
        return "low_detail"
```

### 2. 兄弟节点签名提取

为小型方法添加同一类中的其他方法签名，提供更丰富的上下文。

### 3. 层级化 Chunk 拆分

对于大型 Chunk (>2000 tokens)，自动拆分为父子结构：
- **父节点**: 只包含签名和摘要，不生成 embedding
- **子节点**: 包含具体实现，各自生成 embedding

### 4. 上下文重要性评分

基于依赖关系和引用频率，为上下文元素评分，优先保留重要信息。

## 总结

动态上下文控制方案通过以下机制实现智能化的上下文增强：

1. ✅ **分层元数据头**: L1-L4 四层优先级结构
2. ✅ **类型特化**: 通用格式 vs ArkUI 组件格式
3. ✅ **语义标签**: 多维度标签系统
4. ✅ **依赖追溯**: 完整的依赖关系提取
5. ✅ **批量优化**: 减少重复计算

**核心优势**:
- 小型 Chunk 获得足够的上下文信息，提升召回率
- 大型 Chunk 避免冗余，保持语义清晰
- ArkUI 组件获得特化处理，充分展现框架特性

**待完善方向**:
- Token 预算的精确控制
- 兄弟节点签名提取
- 大型 Chunk 的层级化拆分

---

**版本**: 1.0  
**更新时间**: 2025-10-14  
**相关文档**: [CHUNK_API.md](./CHUNK_API.md) | [CHUNK_README.md](./CHUNK_README.md)
