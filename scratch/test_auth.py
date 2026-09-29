# scratch/test_auth.py
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from auth_manager import resolve_role, load_roles_config

def test_roles():
    print("Testing Role Resolution...")
    test_cases = [
        ("gunturputraananta@gmail.com", "admin"),
        ("retentionmobilejabar@gmail.com", "manager"),
        ("someone_else@gmail.com", "viewer"),
        ("employee@telkomsel.co.id", "viewer"),
    ]
    
    for email, expected in test_cases:
        actual = resolve_role(email)
        assert actual == expected, f"Failed for {email}: expected {expected}, got {actual}"
        print(f"  [PASS] {email} -> {actual}")

    print("\nRole permissions:")
    config = load_roles_config()
    for role, perms in config.get("permissions", {}).items():
        print(f"  Role '{role}': {perms}")

if __name__ == "__main__":
    test_roles()
