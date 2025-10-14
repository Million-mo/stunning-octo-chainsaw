# 测试目录

本目录包含 ArkTS 符号提取器项目的所有测试文件。

## 🧪 测试文件说明

### 核心功能测试

#### [test_extractor.py](./test_extractor.py)
基础符号提取器测试套件：
- 类声明符号提取
- 方法声明符号提取
- 属性声明符号提取
- 接口和枚举提取
- 作用域和继承关系

运行方式：
```bash
pytest tests/test_extractor.py -v
```

#### [test_arkui_support.py](./test_arkui_support.py)
ArkUI 框架支持测试：
- ArkUI 装饰器识别（@State、@Prop、@Link 等）
- 组件声明提取
- 生命周期方法检测
- UI 绑定和事件处理器提取
- 样式函数和资源引用

运行方式：
```bash
python tests/test_arkui_support.py
```

### 测试数据文件

#### [test_arkui_features.ets](./test_arkui_features.ets)
ArkUI 功能测试用例代码，包含：
- 入口组件（@Entry）
- 状态管理装饰器
- 组件属性和事件绑定
- 样式函数
- 生命周期方法
- 资源引用示例

### 历史测试文件

#### [test_fix.py](./test_fix.py)
早期 AST 节点修复测试

#### [test_extractor_fix.py](./test_extractor_fix.py)
符号提取器修复验证测试

#### [mpj_test.py](./mpj_test.py)
临时测试脚本

## 🚀 运行所有测试

```bash
# 运行 pytest 测试套件
pytest tests/ -v

# 运行 ArkUI 专项测试
python tests/test_arkui_support.py
```

## 📊 测试覆盖

当前测试覆盖的功能：
- ✅ 基础 ArkTS 语法符号提取（类、方法、属性、接口、枚举）
- ✅ ArkUI 装饰器识别（10+ 种装饰器）
- ✅ ArkUI 组件声明和结构
- ✅ 生命周期方法
- ✅ UI 绑定和事件处理
- ✅ 样式函数（@Styles）
- ✅ 资源引用（$r、$rawfile）

## 🐛 测试问题排查

如果测试失败，请检查：
1. tree-sitter-arkts-open 是否正确安装
2. Python 依赖是否完整（`pip install -r requirements.txt`）
3. 测试文件路径是否正确
4. 查看测试输出的详细错误信息

## 📝 添加新测试

添加新测试时请遵循以下原则：
1. 在 `test_extractor.py` 中添加基础功能测试
2. 在 `test_arkui_support.py` 中添加 ArkUI 特性测试
3. 为复杂场景创建对应的 `.ets` 测试文件
4. 确保测试覆盖正常情况和边界情况
5. 添加清晰的测试说明和断言信息
