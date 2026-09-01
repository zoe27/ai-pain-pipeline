#!/usr/bin/env python3
"""
测试脚本 - 验证环境配置

运行: python test_setup.py
"""

import sys
import json
from pathlib import Path

def test_python_version():
    """测试 Python 版本"""
    print("🐍 检查 Python 版本...")
    version = sys.version_info
    print(f"   Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("   ❌ Python 版本太低，需要 3.9+")
        return False
    print("   ✅ Python 版本满足要求")
    return True


def test_dependencies():
    """测试依赖包"""
    print("\n📦 检查依赖包...")
    
    required = {
        "jsonschema": "JSON Schema 验证",
        "yaml": "YAML 配置解析",
        "flask": "Web Dashboard",
        "markdown": "Markdown 渲染"
    }
    
    missing = []
    for package, desc in required.items():
        try:
            __import__(package)
            print(f"   ✅ {package:15} - {desc}")
        except ImportError:
            print(f"   ❌ {package:15} - {desc} (未安装)")
            missing.append(package)
    
    if missing:
        print(f"\n   ⚠️  缺少依赖: {', '.join(missing)}")
        print(f"   运行: pip install -r requirements.txt")
        return False
    
    print("   ✅ 所有依赖已安装")
    return True


def test_file_structure():
    """测试文件结构"""
    print("\n📁 检查文件结构...")
    
    required_files = [
        "pipeline_orchestrator.py",
        "decision_dashboard.py",
        "requirements.txt",
        "README.md",
        "helpers/build_prd.py",
        "helpers/build_tech_spec.py",
        "contracts/prd.schema.json",
        "contracts/tech_spec.schema.json",
        ".claude/skills/prd-writer/SKILL.md",
        ".claude/skills/tech-architect/SKILL.md"
    ]
    
    missing = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (缺失)")
            missing.append(file_path)
    
    if missing:
        print(f"\n   ⚠️  缺少文件: {len(missing)} 个")
        return False
    
    print("   ✅ 所有必需文件存在")
    return True


def test_json_schemas():
    """测试 JSON Schema 文件"""
    print("\n📋 检查 JSON Schema...")
    
    schemas = [
        "contracts/prd.schema.json",
        "contracts/tech_spec.schema.json",
        "contracts/code_delivery.schema.json",
        "contracts/deployment.schema.json",
        "contracts/growth_metrics.schema.json"
    ]
    
    errors = []
    for schema_path in schemas:
        try:
            with open(schema_path) as f:
                json.load(f)
            print(f"   ✅ {schema_path}")
        except json.JSONDecodeError as e:
            print(f"   ❌ {schema_path} - 无效的 JSON")
            errors.append(schema_path)
        except FileNotFoundError:
            print(f"   ⚠️  {schema_path} - 文件不存在")
    
    if errors:
        return False
    
    print("   ✅ 所有 Schema 有效")
    return True


def test_example_pipelines():
    """测试示例 Pipeline"""
    print("\n🔍 检查示例 Pipeline...")
    
    runs_dir = Path("runs")
    if not runs_dir.exists():
        print("   ⚠️  runs/ 目录不存在 (正常，运行后会创建)")
        return True
    
    pipelines = [d for d in runs_dir.iterdir() if d.is_dir()]
    
    if not pipelines:
        print("   ℹ️  没有示例 Pipeline (运行后会创建)")
        return True
    
    print(f"   找到 {len(pipelines)} 个 Pipeline:")
    for pipeline in pipelines[:5]:  # 只显示前 5 个
        print(f"   📦 {pipeline.name}")
        
        # 检查关键文件
        key_files = ["_judgments", "1_pain_points.json", "2_scored_pain_points.json"]
        for key_file in key_files:
            if (pipeline / key_file).exists():
                print(f"      ✅ {key_file}")
    
    return True


def test_scripts_syntax():
    """测试脚本语法"""
    print("\n🔧 检查脚本语法...")
    
    scripts = [
        "pipeline_orchestrator.py",
        "decision_dashboard.py",
        "helpers/build_prd.py",
        "helpers/build_tech_spec.py"
    ]
    
    import py_compile
    errors = []
    
    for script in scripts:
        try:
            py_compile.compile(script, doraise=True)
            print(f"   ✅ {script}")
        except py_compile.PyCompileError as e:
            print(f"   ❌ {script} - 语法错误")
            errors.append(script)
    
    if errors:
        return False
    
    print("   ✅ 所有脚本语法正确")
    return True


def main():
    print("═" * 60)
    print("🧪 AI Pain Pipeline - 环境测试")
    print("═" * 60)
    
    tests = [
        ("Python 版本", test_python_version),
        ("依赖包", test_dependencies),
        ("文件结构", test_file_structure),
        ("JSON Schema", test_json_schemas),
        ("示例数据", test_example_pipelines),
        ("脚本语法", test_scripts_syntax)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n   ❌ 测试失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "═" * 60)
    print("📊 测试总结")
    print("═" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status:10} {name}")
    
    print("═" * 60)
    print(f"结果: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！环境配置正确。")
        print("\n下一步:")
        print("  1. 运行 ./setup_and_run.sh")
        print("  2. 或手动启动: python decision_dashboard.py --port 8080")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败。")
        print("\n修复建议:")
        print("  1. 激活虚拟环境: source .venv/bin/activate")
        print("  2. 安装依赖: pip install -r requirements.txt")
        print("  3. 重新运行测试: python test_setup.py")
        return 1


if __name__ == "__main__":
    sys.exit(main())
