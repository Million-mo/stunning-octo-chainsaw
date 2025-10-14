#!/usr/bin/env python3
"""
环境验证脚本

检查所有依赖是否正确安装，并验证基本功能。
"""

import sys


def check_python_version():
    """检查 Python 版本"""
    print("检查 Python 版本...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python 版本过低: {version.major}.{version.minor}.{version.micro}")
        print("  需要 Python 3.9 或更高版本")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n检查依赖包...")
    
    dependencies = [
        ("tree-sitter", "tree_sitter"),
        ("tree-sitter-arkts-open", "tree_sitter_arkts_open"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
    ]
    
    all_ok = True
    for pkg_name, import_name in dependencies:
        try:
            __import__(import_name)
            print(f"  ✓ {pkg_name}")
        except ImportError:
            print(f"  ✗ {pkg_name} 未安装")
            print(f"    安装命令: pip install {pkg_name}")
            all_ok = False
    
    return all_ok


def check_arkts_processor():
    """检查 arkts_processor 包"""
    print("\n检查 arkts_processor 包...")
    try:
        from arkts_processor import SymbolService, SymbolType
        print("  ✓ arkts_processor 已安装")
        return True
    except ImportError:
        print("  ✗ arkts_processor 未安装")
        print("    请在项目根目录运行: pip install -e .")
        return False


def test_parser():
    """测试解析器"""
    print("\n测试 ArkTS 解析器...")
    try:
        import tree_sitter_arkts_open as ts_arkts
        from tree_sitter import Language, Parser
        
        # 创建解析器
        ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")
        parser = Parser()
        parser.set_language(ARKTS_LANGUAGE)
        
        # 测试解析
        code = b"class Test { }"
        tree = parser.parse(code)
        
        if tree and tree.root_node:
            print(f"  ✓ 解析器工作正常")
            print(f"    根节点类型: {tree.root_node.type}")
            return True
        else:
            print("  ✗ 解析失败")
            return False
            
    except Exception as e:
        print(f"  ✗ 解析器测试失败: {e}")
        return False


def test_symbol_service():
    """测试符号服务"""
    print("\n测试符号服务...")
    try:
        import tree_sitter_arkts_open as ts_arkts
        from tree_sitter import Language, Parser
        from arkts_processor import SymbolService
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        # 创建临时代码文件
        code_fd, code_path = tempfile.mkstemp(suffix=".ets")
        with os.fdopen(code_fd, 'w') as f:
            f.write("class TestClass { method() { } }")
        
        try:
            # 初始化服务
            service = SymbolService(db_path=db_path)
            
            # 配置解析器
            ARKTS_LANGUAGE = Language(ts_arkts.language(), "arkts")
            parser = Parser()
            parser.set_language(ARKTS_LANGUAGE)
            service.set_parser(parser)
            
            # 处理文件
            result = service.process_file(code_path)
            
            if result and result['symbols'] > 0:
                print(f"  ✓ 符号服务工作正常")
                print(f"    提取符号数: {result['symbols']}")
                print(f"    作用域数: {result['scopes']}")
                return True
            else:
                print("  ✗ 未提取到符号")
                return False
                
        finally:
            # 清理临时文件
            try:
                os.unlink(db_path)
                os.unlink(code_path)
            except:
                pass
            
    except Exception as e:
        print(f"  ✗ 符号服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 70)
    print("ArkTS 符号表服务 - 环境验证")
    print("=" * 70)
    
    results = []
    
    # 1. 检查 Python 版本
    results.append(("Python 版本", check_python_version()))
    
    # 2. 检查依赖包
    results.append(("依赖包", check_dependencies()))
    
    # 3. 检查 arkts_processor
    results.append(("arkts_processor", check_arkts_processor()))
    
    # 4. 测试解析器
    results.append(("ArkTS 解析器", test_parser()))
    
    # 5. 测试符号服务
    results.append(("符号服务", test_symbol_service()))
    
    # 总结
    print("\n" + "=" * 70)
    print("验证结果总结")
    print("=" * 70)
    
    all_passed = True
    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{name:20s} : {status}")
        if not passed:
            all_passed = False
    
    print("=" * 70)
    
    if all_passed:
        print("\n🎉 所有检查都通过了！您可以开始使用符号服务了。")
        print("\n下一步:")
        print("  1. 查看示例: python examples/complete_example.py")
        print("  2. 阅读文档: README.md")
        print("  3. 运行测试: pytest tests/ -v")
        return 0
    else:
        print("\n⚠️  部分检查失败，请根据上面的提示修复问题。")
        print("\n常见问题:")
        print("  - 缺少依赖: pip install -r requirements.txt")
        print("  - arkts_processor 未安装: pip install -e .")
        print("  - 解析器问题: pip install --upgrade tree-sitter-arkts-open")
        return 1


if __name__ == "__main__":
    sys.exit(main())
