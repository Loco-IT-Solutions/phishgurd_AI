# test_setup.py
import sys
import importlib

packages = ["numpy", "pandas", "sklearn", "flask", "joblib"]
ok = True
for p in packages:
    try:
        importlib.import_module(p)
        print(f"[OK] {p}")
    except Exception as e:
        ok = False
        print(f"[MISSING] {p} -> {e}")

if not ok:
    print("\nInstall missing packages: pip install -r requirements.txt")
else:
    print("\nEnvironment looks good.")
