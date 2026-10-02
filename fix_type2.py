import re

with open('allseeingeye.py', 'r') as f:
    content = f.read()

content = content.replace("self.stats = {", "self.stats: Dict[str, Any] = {")

# also fix 313 error in allseeingeye.py
content = content.replace("""def _format_size(self, size_bytes: int) -> str:
        \"\"\"Format file size in human-readable format.\"\"\"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024 or unit == 'GB':
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024""", """def _format_size(self, size_bytes: int) -> str:
        \"\"\"Format file size in human-readable format.\"\"\"
        size_float = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_float < 1024 or unit == 'GB':
                return f"{size_float:.2f} {unit}"
            size_float /= 1024
        return "0 B\"\"\"""")

# Wait, better just do this with regex.
import re
content = re.sub(
    r"def _format_size\(self, size_bytes: int\) -> str:\n\s+\"\"\"Format file size in human-readable format\.\"\"\"\n\s+for unit in \['B', 'KB', 'MB', 'GB'\]:\n\s+if size_bytes < 1024 or unit == 'GB':\n\s+return f\"\{size_bytes:\.2f\} \{unit\}\"\n\s+size_bytes /= 1024",
    """def _format_size(self, size_bytes: int) -> str:
        \"\"\"Format file size in human-readable format.\"\"\"
        size_float = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_float < 1024 or unit == 'GB':
                return f"{size_float:.2f} {unit}"
            size_float /= 1024
        return "0.00 B\"\"\"""", content)

with open('allseeingeye.py', 'w') as f:
    f.write(content)
