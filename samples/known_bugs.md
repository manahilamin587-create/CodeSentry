# Seeded bugs (answer key)

| File | Issue | Type |
|---|---|---|
| sample_app1/db.py | SQL injection (string concatenation) | security |
| sample_app1/config.py | Hardcoded password | security |
| sample_app1/config.py | Hardcoded API key | security |
| sample_app1/utils.py | Command injection via os.system | security |
| sample_app1/utils.py | Command injection via shell=True | security |
| sample_app1/utils.py | eval on user input | security |
| sample_app1/bugs.py | Unused imports (json, sys) | bug |
| sample_app1/bugs.py | Division by zero on empty list | bug |
| sample_app1/bugs.py | Wrong return type (str vs int) | bug |
| sample_app1/bugs.py | Undefined variable | bug |
| sample_app2/app.py | Weak hash (MD5) | security |
| sample_app2/app.py | Unsafe yaml.load | security |
| sample_app2/app.py | Flask debug=True, binds 0.0.0.0 | security |
| sample_app2/requirements.txt | Vulnerable dependencies | security |