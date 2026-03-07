"""
Simple script to check LaTeX installation and compile paper
"""
import subprocess
import os
import sys

def check_latex_installed():
    """Check if pdflatex is available"""
    try:
        result = subprocess.run(['pdflatex', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ LaTeX is installed!")
            print(result.stdout.split('\n')[0])
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("❌ LaTeX (pdflatex) is not installed or not in PATH")
        return False
    return False

def compile_latex(filename="paper.tex", runs=2):
    """Compile LaTeX document"""
    if not os.path.exists(filename):
        print(f"❌ File {filename} not found!")
        return False
    
    print(f"\n🔨 Compiling {filename}...")
    
    for i in range(runs):
        print(f"\n📄 Compilation run {i+1}/{runs}...")
        try:
            result = subprocess.run(['pdflatex', '-interaction=nonstopmode', filename],
                                  capture_output=True, text=True, timeout=60)
            
            if "Error" in result.stdout or result.returncode != 0:
                print("⚠️  Compilation had errors. Check the log file.")
                print("\nLast 20 lines of output:")
                print('\n'.join(result.stdout.split('\n')[-20:]))
                return False
            else:
                print(f"✅ Run {i+1} completed successfully")
        except subprocess.TimeoutExpired:
            print("❌ Compilation timed out")
            return False
        except Exception as e:
            print(f"❌ Error during compilation: {e}")
            return False
    
    pdf_file = filename.replace('.tex', '.pdf')
    if os.path.exists(pdf_file):
        print(f"\n✅ SUCCESS! PDF created: {pdf_file}")
        print(f"📊 PDF size: {os.path.getsize(pdf_file)} bytes")
        return True
    else:
        print(f"\n❌ PDF file {pdf_file} was not created")
        return False

def main():
    print("=" * 60)
    print("LaTeX Paper Compilation Helper")
    print("=" * 60)
    
    if not check_latex_installed():
        print("\n" + "=" * 60)
        print("INSTALLATION REQUIRED")
        print("=" * 60)
        print("\n📋 Please install LaTeX using one of these methods:\n")
        print("1. MiKTeX (Recommended for Windows):")
        print("   https://miktex.org/download")
        print("\n2. Overleaf (Online - No installation):")
        print("   https://www.overleaf.com")
        print("\n3. TeX Live:")
        print("   https://tug.org/texlive/")
        print("\nAfter installation, run this script again.")
        return
    
    # Try to compile
    success = compile_latex("paper.tex")
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Your paper is ready!")
        print("=" * 60)
        print("\n📄 Open 'paper.pdf' to view your compiled paper")
    else:
        print("\n" + "=" * 60)
        print("⚠️  Compilation Issues")
        print("=" * 60)
        print("\nCheck 'paper.log' for detailed error information")
        print("Common issues:")
        print("  - Missing packages: MiKTeX will prompt to install")
        print("  - Syntax errors: Check the .tex file")

if __name__ == "__main__":
    main()
