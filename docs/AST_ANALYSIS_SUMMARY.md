# Tree-sitter-arkts AST 结构分析总结

## 关键发现

基于对 tree-sitter-arkts 实际解析输出的分析，发现了当前 `extractor.py` 中存在的多个节点结构不匹配问题。

### 1. 类声明 (class_declaration)

**实际 AST 结构：**
```
class_declaration
  ├── class (关键字)
  ├── identifier (类名) - 直接子节点，不是 field "name"
  ├── extends (可选)
  ├── type_annotation (继承的基类)
  ├── ERROR (implements - 当前语法不完全支持)
  └── class_body
      ├── property_declaration (属性)
      ├── constructor_declaration (构造函数)
      └── method_declaration (方法)
```

**当前代码问题：**
- ❌ 使用 `NodeHelper.get_field_by_name(node, "name")` - 错误！
- ❌ 使用 `NodeHelper.get_field_by_name(node, "body")` - 错误！
- ❌ 使用 `NodeHelper.get_field_by_name(node, "heritage")` - 错误！

**正确做法：**
- ✅ 类名是 `identifier` 类型的直接子节点
- ✅ 类体是 `class_body` 类型的直接子节点
- ✅ 继承信息通过 `extends` 关键字后的 `type_annotation` 获取
- ✅ 属性使用 `property_declaration`，不是 `property_identifier`
- ✅ 方法使用 `method_declaration`，不是 `method_definition`
- ✅ 构造函数使用 `constructor_declaration`，不是 `method_definition`

### 2. 接口声明 (interface_declaration)

**实际 AST 结构：**
```
interface_declaration
  ├── interface (关键字)
  ├── identifier (接口名) - 直接子节点
  └── object_type (接口体，不是 body)
      └── type_member (成员，可能有解析错误)
```

**当前代码问题：**
- ❌ 使用 field "name" 获取接口名 - 错误！
- ❌ 使用 field "body" 获取接口体 - 错误！应该是 `object_type`
- ❌ 使用 field "heritage" 获取继承 - 错误！

**正确做法：**
- ✅ 接口名是 `identifier` 类型的直接子节点
- ✅ 接口体是 `object_type` 类型的直接子节点
- ✅ 成员是 `type_member` 节点（注意：可能有解析错误）

### 3. 方法声明 (method_declaration)

**实际 AST 结构：**
```
method_declaration
  ├── public/private/protected (可选)
  ├── identifier (方法名) - 直接子节点
  ├── parameter_list (参数列表)
  ├── : (冒号)
  ├── type_annotation (返回类型)
  └── block_statement (方法体)
```

**当前代码问题：**
- ❌ 使用 `method_definition` 作为节点类型 - 错误！应该是 `method_declaration`
- ❌ 使用 field "name" 获取方法名 - 错误！
- ❌ 使用 field "parameters" 获取参数 - 错误！应该查找 `parameter_list` 子节点
- ❌ 使用 field "return_type" 获取返回类型 - 错误！

**正确做法：**
- ✅ 节点类型是 `method_declaration`
- ✅ 方法名是 `identifier` 类型的直接子节点
- ✅ 参数是 `parameter_list` 类型的直接子节点
- ✅ 返回类型是 `:` 后的 `type_annotation` 直接子节点

### 4. 函数声明 (function_declaration)

**实际 AST 结构：**
```
function_declaration
  ├── function (关键字)
  ├── identifier (函数名) - 直接子节点
  ├── parameter_list (参数列表)
  ├── : (冒号)
  ├── type_annotation (返回类型)
  └── block_statement (函数体)
```

**当前代码问题：**
- ❌ 使用 field "name" - 错误！
- ❌ 使用 field "parameters" - 错误！
- ❌ 使用 field "return_type" - 错误！

**正确做法：**
- ✅ 函数名是 `identifier` 类型的直接子节点
- ✅ 参数是 `parameter_list` 类型的直接子节点
- ✅ 返回类型是 `:` 后的 `type_annotation` 直接子节点

### 5. 参数列表 (parameter_list)

**实际 AST 结构：**
```
parameter_list
  ├── ( (左括号)
  ├── parameter
  │   ├── identifier (参数名) - 直接子节点
  │   ├── : (冒号)
  │   └── type_annotation (参数类型)
  ├── , (逗号)
  └── ) (右括号)
```

**当前代码问题：**
- ❌ 查找 `required_parameter` 和 `optional_parameter` - 可能不完全准确
- ❌ 使用 field "pattern" 获取参数名 - 错误！

**正确做法：**
- ✅ 参数是 `parameter` 类型的子节点
- ✅ 参数名是 `identifier` 类型的直接子节点
- ✅ 参数类型是 `:` 后的 `type_annotation` 直接子节点

### 6. 变量声明 (variable_declaration)

**实际 AST 结构：**
```
variable_declaration
  ├── const/let/var (关键字)
  ├── variable_declarator
  │   ├── identifier (变量名) - 直接子节点
  │   ├── : (冒号)
  │   ├── type_annotation (类型)
  │   ├── = (等号)
  │   └── expression (初始值)
  └── ; (分号)
```

**当前代码问题：**
- ⚠️ 基本正确，但字段访问方式需要调整
- ❌ 使用 field "name" - 应该查找 `identifier` 子节点
- ❌ 使用 field "type" - 应该查找 `type_annotation` 子节点

**正确做法：**
- ✅ 变量名是 `identifier` 类型的直接子节点
- ✅ 变量类型是 `type_annotation` 类型的直接子节点

### 7. 枚举声明 (enum_declaration)

**实际解析结果：**
```
ERROR (整个 enum 被识别为错误节点)
```

**问题：**
- ❌ tree-sitter-arkts 当前版本可能不完全支持 `enum` 语法
- ❌ 枚举会被解析为 ERROR 节点

**建议：**
- ⚠️ 暂时无法正确提取枚举信息
- 💡 可以考虑使用文本模式匹配作为临时方案

### 8. 类型别名 (type_alias_declaration)

**实际 AST 结构：**
```
type_declaration (注意：不是 type_alias_declaration)
  ├── type (关键字)
  ├── identifier (类型名)
  ├── = (等号)
  ├── type_annotation (类型定义)
  └── ; (分号)
```

**当前代码问题：**
- ❌ 使用 `type_alias_declaration` 作为节点类型 - 错误！应该是 `type_declaration`
- ❌ 使用 field "name" - 错误！
- ❌ 使用 field "value" - 错误！

**正确做法：**
- ✅ 节点类型是 `type_declaration`
- ✅ 类型名是 `identifier` 类型的直接子节点
- ✅ 类型定义是 `=` 后的 `type_annotation` 直接子节点

### 9. 根节点

**实际根节点类型：**
- ✅ `source_file` (已正确处理)

## 核心问题总结

1. **字段访问错误**：tree-sitter-arkts 的节点通常**不使用命名字段**，而是使用**直接子节点**
2. **节点类型错误**：多个节点类型名称不匹配
   - `method_definition` → `method_declaration`
   - `type_alias_declaration` → `type_declaration`
   - `property_identifier` → `property_declaration`
3. **节点结构理解错误**：
   - `class_body` 而不是 field "body"
   - `object_type` 而不是 field "body" (接口)
   - `parameter_list` 而不是 field "parameters"
   - 直接的 `identifier` 子节点而不是 field "name"

## 修复策略

1. **移除所有 `NodeHelper.get_field_by_name()` 调用**
2. **使用 `child_by_type()` 或遍历 `children` 查找特定类型的子节点**
3. **更新 `NODE_TYPE_MAPPING` 中的节点类型名称**
4. **重写节点访问方法，使用正确的子节点类型**

## 建议的辅助方法

```python
def get_child_by_type(node: Node, type_name: str) -> Optional[Node]:
    """通过类型获取子节点"""
    for child in node.children:
        if child.type == type_name:
            return child
    return None

def get_children_by_type(node: Node, type_name: str) -> List[Node]:
    """通过类型获取所有匹配的子节点"""
    return [child for child in node.children if child.type == type_name]

def get_identifier_name(node: Node) -> Optional[str]:
    """获取节点的 identifier 子节点的文本"""
    id_node = get_child_by_type(node, "identifier")
    if id_node:
        return self.traverser.get_node_text(id_node)
    return None
```
