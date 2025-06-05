#!/usr/bin/env python3
"""
Configuration validation script for FastAPI Voice Agent System
"""
import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True

def check_dependencies():
    """Check if all required dependencies can be imported"""
    dependencies = [
        ("fastapi", "FastAPI framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("sqlalchemy", "Database ORM"),
        ("asyncpg", "PostgreSQL driver"),
        ("redis", "Redis client"),
        ("openai", "OpenAI API client"),
        ("anthropic", "Anthropic API client"),
        ("google-generativeai", "Google Gemini API"),
        ("websockets", "WebSocket support"),
        ("httpx", "HTTP client"),
        ("jwt", "JWT token handling"),
        ("passlib", "Password hashing"),
        ("python-multipart", "Form data support"),
    ]
    
    missing_deps = []
    
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"✅ {description} ({module})")
        except ImportError:
            print(f"❌ {description} ({module}) - Not installed")
            missing_deps.append(module)
    
    return len(missing_deps) == 0, missing_deps

def check_environment():
    """Check environment configuration"""
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        return True
    else:
        print("❌ .env file not found")
        return False

def check_directory_structure():
    """Check if all required directories exist"""
    required_dirs = [
        "api/v1",
        "core/config",
        "core/logging",
        "core/security",
        "models/internal",
        "models/external",
        "services/call",
        "wss",
        "data/db",
        "tests",
        "logs"
    ]
    
    missing_dirs = []
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ - Missing")
            missing_dirs.append(dir_path)
    
    return len(missing_dirs) == 0, missing_dirs

def main():
    """Main validation function"""
    print("🔍 FastAPI Voice Agent System - Configuration Validation")
    print("=" * 60)
    
    all_good = True
    
    # Check Python version
    print("\n📋 Python Version Check:")
    if not check_python_version():
        all_good = False
    
    # Check dependencies
    print("\n📦 Dependency Check:")
    deps_ok, missing_deps = check_dependencies()
    if not deps_ok:
        all_good = False
        print(f"\n💡 To install missing dependencies:")
        print(f"   pip install {' '.join(missing_deps)}")
    
    # Check environment
    print("\n⚙️  Environment Check:")
    if not check_environment():
        all_good = False
        print("💡 Run ./setup.sh to create a template .env file")
    
    # Check directory structure
    print("\n📁 Directory Structure Check:")
    structure_ok, missing_dirs = check_directory_structure()
    if not structure_ok:
        all_good = False
    
    # Final result
    print("\n" + "=" * 60)
    if all_good:
        print("✅ All checks passed! The system is ready to run.")
        print("💡 Run: python main.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
