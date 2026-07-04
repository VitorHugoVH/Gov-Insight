import os
from db import get_connection

def create_tables():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    schema_path = os.path.join(base_dir, "db", "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection()
    cur = conn.cursor()

    print("🧹 Limpando estruturas anteriores...")
    cur.execute("DROP SCHEMA IF EXISTS gov CASCADE;")
    conn.commit()

    # ✅ public precisa existir ANTES do unaccent
    cur.execute("CREATE SCHEMA IF NOT EXISTS public;")
    cur.execute("GRANT ALL ON SCHEMA public TO PUBLIC;")
    cur.execute("CREATE SCHEMA IF NOT EXISTS gov;")
    conn.commit()

    print("🔧 Habilitando extensões...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA public;")
    conn.commit()

    # ✅ Wrapper IMMUTABLE necessário para usar unaccent em índices
    cur.execute("""
        CREATE OR REPLACE FUNCTION gov.unaccent_immutable(text)
        RETURNS text AS $$
            SELECT public.unaccent($1)
        $$ LANGUAGE sql IMMUTABLE;
    """)
    conn.commit()

    print("🧱 Criando tabelas no schema 'gov'...")
    cur.execute(sql)
    conn.commit()

    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'gov'
        ORDER BY table_name;
    """)
    tabelas = [r[0] for r in cur.fetchall()]
    print(f"📋 Tabelas criadas ({len(tabelas)}): {', '.join(tabelas)}")

    cur.close()
    conn.close()
    print("✅ Banco criado com sucesso!")