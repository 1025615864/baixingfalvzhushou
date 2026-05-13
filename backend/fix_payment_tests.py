import re

with open("tests/test_payment_service.py", "r", encoding="utf-8") as f:
    content = f.read()

# Find all test functions and add _ensure_test_user call at the beginning
# Pattern: async def test_...\n    """..."""\n    # Arrange\n    service = PaymentService()
# We need to add _ensure_test_user(db) after service = PaymentService() in tests that use user_id=1

# Let's find all occurrences and add the ensure call before UserBalance creation
lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    new_lines.append(line)
    # Check if this line creates a UserBalance with user_id=1
    if 'user_balance = UserBalance(user_id=1' in line or 'user_balance = UserBalance(user_id=1,' in line:
        # Check if we already added ensure call in this function
        # Look back to find if there's already an _ensure_test_user call
        found_ensure = False
        for j in range(len(new_lines)-1, max(len(new_lines)-30, -1), -1):
            if '_ensure_test_user' in new_lines[j]:
                found_ensure = True
                break
        if not found_ensure:
            # Insert _ensure_test_user before this line
            indent = len(line) - len(line.lstrip())
            new_lines.insert(-1, ' ' * indent + 'await _ensure_test_user(db)')
    i += 1

new_content = '\n'.join(new_lines)

with open("tests/test_payment_service.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Fixed test_payment_service.py")
