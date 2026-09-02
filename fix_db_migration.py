import re

with open('db_config.py', 'r', encoding='utf-8') as f:
    content = f.read()

bad_migration = """    # Migrations
    try:
        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()"""

# Remove the bad migration from the module level
content = content.replace(bad_migration, "")

# Add it safely inside init_db()
# Let's find a safe spot inside init_db. 
# init_db has a loop or something, then db.close(), then seed_db()
init_db_end = """
    db.close()
    seed_db()
"""

safe_migration = """
    # Migrations for existing DB
    try:
        db.execute(text("ALTER TABLE usuarios ADD COLUMN pode_excluir BOOLEAN DEFAULT FALSE;"))
        db.commit()
    except Exception:
        db.rollback()

    db.close()
    seed_db()
"""

if safe_migration not in content:
    content = content.replace(init_db_end, safe_migration)

with open('db_config.py', 'w', encoding='utf-8') as f:
    f.write(content)
print('Fixed db_config.py migration placement')
