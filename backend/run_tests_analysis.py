import subprocess

result = subprocess.run(
    ["python", "-m", "pytest", "tests/", "--tb=no", "-q", "--timeout=60"],
    capture_output=True, text=True
)

output = result.stdout + result.stderr
lines = output.split('\n')

# Only count actual test errors (lines starting with ERROR tests/)
test_error_lines = [l for l in lines if l.startswith('ERROR tests/')]
failed_lines = [l for l in lines if l.startswith('FAILED tests/')]
passed_lines = [l for l in lines if l.startswith('passed') or (' passed' in l and 'failed' in l)]

error_types = {}
for line in test_error_lines:
    if 'OperationalError' in line or 'sqlalchemy' in line:
        key = 'OperationalError'
    elif 'AttributeError' in line:
        key = 'AttributeError'
    elif 'ModuleNotFoundError' in line:
        key = 'ModuleNotFoundError'
    elif 'ImportError' in line:
        key = 'ImportError'
    elif 'TypeError' in line:
        key = 'TypeError'
    elif 'ValueError' in line:
        key = 'ValueError'
    elif 'FastAPIError' in line:
        key = 'FastAPIError'
    elif 'RuntimeError' in line:
        key = 'RuntimeError'
    elif 'NameError' in line:
        key = 'NameError'
    elif 'KeyError' in line:
        key = 'KeyError'
    elif 'ValidationError' in line:
        key = 'ValidationError'
    elif 'IntegrityError' in line:
        key = 'IntegrityError'
    else:
        key = 'Other'
    error_types[key] = error_types.get(key, 0) + 1

print(f"Total ERROR: {len(test_error_lines)}")
print(f"Total FAILED: {len(failed_lines)}")

if passed_lines:
    print(f"Summary: {passed_lines[-1].strip()}")

print("\nError types:")
for k, v in sorted(error_types.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

error_files = {}
for line in test_error_lines:
    parts = line.split('::')
    if len(parts) >= 2:
        fname = parts[0].replace('ERROR ', '')
        error_files[fname] = error_files.get(fname, 0) + 1

print("\nERROR by file:")
for k, v in sorted(error_files.items(), key=lambda x: -x[1]):
    print(f"  {k}: {v}")

failed_files = {}
for line in failed_lines:
    parts = line.split('::')
    if len(parts) >= 2:
        fname = parts[0].replace('FAILED ', '')
        failed_files[fname] = failed_files.get(fname, 0) + 1

print("\nFAILED by file (top 20):")
for k, v in sorted(failed_files.items(), key=lambda x: -x[1])[:20]:
    print(f"  {k}: {v}")
