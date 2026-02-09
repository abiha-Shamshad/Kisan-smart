import os

path = r"c:\Users\Each One Teach One\Desktop\Kisan smart\tests\unit\test_models.py"

with open(path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = 0
for i, line in enumerate(lines):
    # test_verify_valid_token
    if 'user = User(username="testuser", email="test@example.com")' in line and i + 2 < len(lines) and 'db_session.session.add(user)' in lines[i+1] and 'db_session.session.commit()' in lines[i+2]:
        indent = line[:line.find('user =')]
        new_lines.append(line)
        new_lines.append(f'{indent}user.set_password("Pass123!")\n')
        continue
    
    new_lines.append(line)

with open(path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print("Applied set_password fixes to test_models.py")
