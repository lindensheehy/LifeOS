import os
import sys
import shutil
import subprocess

# Resolve the root tracking/ directory dynamically
PYTHON_DIR = os.path.dirname(os.path.abspath(__file__))
TRACKING_DIR = os.path.dirname(PYTHON_DIR)

REQUIRED_DIRS = [
    os.path.join(TRACKING_DIR, "bin"),
    os.path.join(TRACKING_DIR, "cpp"),
]

def ensure_directories():
    """Ensures all required data and binary directories exist."""
    print("[*] Validating directory structure...")
    for directory in REQUIRED_DIRS:
        if not os.path.exists(directory):
            print(f"[+] Creating missing directory: {os.path.relpath(directory, TRACKING_DIR)}")
            os.makedirs(directory, exist_ok=True)
    return True

def compile_hooks():
    """Compiles any .cpp files in the cpp/ directory into bin/ if they are updated."""
    cpp_dir = os.path.join(TRACKING_DIR, "cpp")
    bin_dir = os.path.join(TRACKING_DIR, "bin")
    
    cpp_files = [f for f in os.listdir(cpp_dir) if f.endswith(".cpp")]
    
    if not cpp_files:
        print("[-] No .cpp files found in cpp/ directory to compile.")
        # Not strictly a failure, but nothing to do
        return True 

    if not shutil.which("g++"):
        print("[-] [CRITICAL ERROR] g++ was not found in your system PATH.")
        return False

    success = True
    for cpp_file in cpp_files:
        base_name = os.path.splitext(cpp_file)[0]
        cpp_path = os.path.join(cpp_dir, cpp_file)
        dll_path = os.path.join(bin_dir, f"{base_name}.dll")
        
        # Only compile if the DLL doesn't exist, or if the CPP file is newer
        if not os.path.exists(dll_path) or os.path.getmtime(cpp_path) > os.path.getmtime(dll_path):
            print(f"[*] Compiling {cpp_file} -> {base_name}.dll...")
            
            cmd = [
                "g++", "-shared", "-O2", "-o", dll_path, cpp_path, 
                "-Wl,--subsystem,windows", "-luser32"
            ]
            
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print(f"[+] Successfully compiled {base_name}.dll")
            else:
                print(f"[-] Compilation Failed for {cpp_file}:\n{result.stderr}")
                success = False
        else:
            print(f"[*] {base_name}.dll is up to date. Skipping compilation.")

    return success

def main():
    print("=== Telemetry Build Pre-Flight ===")
    
    if not ensure_directories():
        sys.exit(1)
        
    if not compile_hooks():
        sys.exit(1)
        
    print("=== Pre-Flight Complete ===")
    sys.exit(0)

if __name__ == "__main__":
    main()