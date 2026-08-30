import os

def get_solution_code():
    path = os.environ.get('CURRENT_SOLUTION_PATH')
    if not path or not os.path.exists(path):
        raise ValueError(f"Solution path not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()
