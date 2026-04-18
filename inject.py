import os

files = [
    "clean_columns.py", "clean_numeric.py", 
    "clean_missing.py", "clean_datatypes.py", 
    "clean_categorical.py", "clean_duplicates.py"
]

base_dir = r"C:\Users\HP-PC\Desktop\New folder"

for f in files:
    filepath = os.path.join(base_dir, f)
    with open(filepath, "r", encoding="utf-8") as file:
        content = file.read()
    
    if "checkpoint_state" not in content:
        content = content.replace("from logger import add_log", "from logger import add_log, checkpoint_state")
        
    lines = content.split('\n')
    new_lines = []
    
    for i in range(len(lines)):
        line = lines[i]
        new_lines.append(line)
        
        # We look specifically for the Apply/Drop/Create/Remove execution buttons
        if "if st.button(" in line and ("Apply" in line or "Drop Selected" in line or "Create Column" in line or "Remove Duplicates" in line):
            if i+1 < len(lines) and "checkpoint_state()" not in lines[i+1]:
                indent = len(line) - len(line.lstrip()) + 4
                new_lines.append(" "*indent + "checkpoint_state()")
                
    with open(filepath, "w", encoding="utf-8") as file:
        file.write("\n".join(new_lines))

print("Injection complete.")
