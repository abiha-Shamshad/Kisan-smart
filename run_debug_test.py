import subprocess
import sys

def run_test():
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/integration",
        "-vv", "--color=no", "--tb=short"
    ]
    with open("full_test_debug.log", "w", encoding="utf-8") as f:
        subprocess.run(cmd, stdout=f, stderr=f)
    print("Test run completed. Check full_test_debug.log")

if __name__ == "__main__":
    run_test()
