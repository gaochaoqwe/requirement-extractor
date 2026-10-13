<#
Quick validation script for the all_graph_parser call-graph extractor.
Run from project root (or any directory) with:

    powershell -ExecutionPolicy Bypass -File backend/tests/callTest/quick_validate.ps1

It will import the parser, analyse the sample C / C++ files in callTest,
and print the direct callees detected for each entry function.
#>

Write-Host "=== Call-graph quick validation ==="

$pythonCode = @"
import sys, pathlib, json

# Ensure the 'backend' package can be imported no matter the cwd.
backend_dir = pathlib.Path.cwd() / 'backend'
project_root = pathlib.Path.cwd()
sys.path.insert(0, str(backend_dir))

from app.staticAnalysis.service.ai.parser.all_graph_parser import (
    collect_function_with_dependencies as collect,
)

print('[debug] backend_dir =', backend_dir)
print('[debug] project_root =', project_root)
print('[debug] sys.path[0] =', sys.path[0])

test_root = backend_dir / 'tests' / 'callTest'
print('[info] Using test corpus at', test_root)

cases = [
    ('operate',   'c'),
    ('calculate', 'c'),
    ('compute',   'cpp'),
    ('perform',   'cpp'),
]

for fn, lang in cases:
    try:
        res = collect(fn, test_root, language=lang, max_depth=1)
        callees = res[fn]['calls']
        print(f'{fn:<10} ({lang}) ->', callees)
    except Exception as exc:
        print(f'[error] {fn}:', exc)
"@

$pythonCode | python -

Write-Host "=== Validation finished ===" 