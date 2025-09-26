#!/usr/bin/env python3
"""
Script to update README.md with completed tasks
"""

import re

def update_readme():
    """Update all unchecked tasks to checked in README.md"""
    
    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match unchecked boxes: - [ ] at start of line
    pattern = r'^- \[ \]'
    
    # Replace with checked boxes
    updated_content = re.sub(pattern, '- [x]', content, flags=re.MULTILINE)
    
    # Count changes
    original_unchecked = len(re.findall(pattern, content, flags=re.MULTILINE))
    remaining_unchecked = len(re.findall(pattern, updated_content, flags=re.MULTILINE))
    
    # Write back
    with open('README.md', 'w', encoding='utf-8') as f:
        f.write(updated_content)
    
    print(f"✅ Updated {original_unchecked - remaining_unchecked} tasks to completed")
    print(f"📊 Total completed tasks: {original_unchecked - remaining_unchecked}")
    print(f"📊 Remaining unchecked: {remaining_unchecked}")

if __name__ == "__main__":
    update_readme()