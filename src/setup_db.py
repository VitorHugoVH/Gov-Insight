import os
from db import get_connection

def create_tables():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, "db", "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)

    conn.commit()
    cur.close()
    conn.close()

    print("Banco criado com sucesso!")

if __name__ == "__main__":
    create_tables()
