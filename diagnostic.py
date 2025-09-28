# diagnostic.py - Run this to check what's wrong with your setup
import os
import sys
import subprocess
from pathlib import Path

def check_system():
    print("🔍 OPTION TRADING SYSTEM DIAGNOSTICS")
    print("=" * 50)
    
    # Check 1: Current directory and files
    print("\n1. 📁 CHECKING FILES AND DIRECTORIES:")
    current_dir = Path.cwd()
    print(f"   Current directory: {current_dir}")
    
    required_files = [
        "streamlit_app.py",
        "main.py", 
        "SmartOptionChainExcel.exe",
        "SmartOptionChainExcel_Zerodha.xlsm"
    ]
    
    required_dirs = [
        "automation",
        "api",
        "config", 
        "utils"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file} - Found")
        else:
            print(f"   ❌ {file} - MISSING")
    
    for dir_name in required_dirs:
        if Path(dir_name).exists():
            print(f"   ✅ {dir_name}/ - Found")
        else:
            print(f"   ❌ {dir_name}/ - MISSING")
    
    # Check 2: Python modules
    print("\n2. 🐍 CHECKING PYTHON MODULES:")
    modules_to_check = [
        "streamlit",
        "pandas", 
        "asyncio",
        "pathlib",
        "subprocess",
        "logging"
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"   ✅ {module} - Available")
        except ImportError:
            print(f"   ❌ {module} - MISSING (run: pip install {module})")
    
    # Check 3: File permissions
    print("\n3. 🔐 CHECKING FILE PERMISSIONS:")
    exe_file = Path("SmartOptionChainExcel.exe")
    if exe_file.exists():
        if os.access(exe_file, os.X_OK):
            print(f"   ✅ EXE file is executable")
        else:
            print(f"   ❌ EXE file is not executable (run: chmod +x {exe_file})")
    
    excel_file = Path("SmartOptionChainExcel_Zerodha.xlsm")
    if excel_file.exists():
        if os.access(excel_file, os.R_OK):
            print(f"   ✅ Excel file is readable")
        else:
            print(f"   ❌ Excel file is not readable")
    
    # Check 4: Import test
    print("\n4. 📦 TESTING IMPORTS:")
    try:
        from main import OptionTradingSystem
        print("   ✅ Main system import successful")
    except ImportError as e:
        print(f"   ❌ Main system import failed: {e}")
        print("   💡 Suggestion: Create missing automation modules")
    
    # Check 5: System info
    print("\n5. 💻 SYSTEM INFO:")
    print(f"   Python version: {sys.version}")
    print(f"   Operating system: {os.name}")
    print(f"   Platform: {sys.platform}")
    
    # Check 6: Streamlit test
    print("\n6. 🌐 STREAMLIT TEST:")
    try:
        result = subprocess.run([sys.executable, "-c", "import streamlit; print('Streamlit OK')"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ Streamlit is working")
        else:
            print(f"   ❌ Streamlit error: {result.stderr}")
    except Exception as e:
        print(f"   ❌ Streamlit test failed: {e}")
    
    # Recommendations
    print("\n" + "=" * 50)
    print("🎯 RECOMMENDATIONS:")
    
    if not Path("automation").exists():
        print("   1. Create automation directory and modules")
        print("      mkdir automation")
        print("      touch automation/__init__.py")
    
    if not Path("SmartOptionChainExcel.exe").exists():
        print("   2. Copy your SmartOptionChainExcel.exe to this directory")
    
    if not Path("SmartOptionChainExcel_Zerodha.xlsm").exists():
        print("   3. Copy your Excel file to this directory")
    
    print("   4. Run: pip install -r requirements.txt")
    print("   5. Then run: streamlit run streamlit_app.py")
    
    print("\n✨ Run this script again after making changes!")

if __name__ == "__main__":
    check_system()