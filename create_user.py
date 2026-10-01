import getpass

import db

db.init_db()
username = input("Username: ").strip()
role = input("Role (finance_manager or viewer): ").strip()
password = getpass.getpass("Password (hidden while typing): ")

db.add_user(username, password, role)
print("Saved user:", username, "with role", role)