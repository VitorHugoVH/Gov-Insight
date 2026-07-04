# gov_insight/src/crud.py
from db import get_connection

TABELAS = {
    "1": ("gov.entidades", "nome_entidade", ["nome_entidade"]),
    "2": ("gov.orgao", "nome_orgao", ["nome_orgao", "nome_entidade"]),
    "3": ("gov.empresas", "cpf_cnpj", ["cpf_cnpj", "nome_empresa"]),
    "4": ("gov.servidores", "matricula", ["matricula", "nome_entidade", "nome_orgao", "nome_do_servidor", "cargo"]),
    "5": ("gov.obras", "id_obra", ["id_obra", "nome_entidade", "categoria", "descricao", "situacao"]),
    "6": ("gov.contratos", "numero_do_contrato", ["numero_do_contrato", "numero_do_processo", "nome_empresa", "nome_entidade", "valor_final"])
}

def exibir_menu_crud():
    while True:
        print("\n" + "="*50)
        print("🛠️  SUBMENU - GERENCIAR DADOS DO BANCO (CRUD)")
        print("="*50)
        print("[1] ➕ Inserir Novo Registro")
        print("[2] 📝 Atualizar Registro Existente")
        print("[3] ❌ Excluir Registro")
        print("[0] ⬅️  Voltar ao Menu Principal")
        print("="*50)
        
        opcao = input("Escolha uma operação: ").strip()
        if opcao == "0":
            break
        elif opcao in ["1", "2", "3"]:
            escolher_tabela(opcao)
        else:
            print("⚠️ Opção inválida!")

def escolher_tabela(operacao):
    print("\nSelecione a tabela para a operação:")
    for k, v in TABELAS.items():
        print(f"[{k}] {v[0].split('.')[1].upper()}")
    print("[0] Cancelar")
    
    t_op = input("Escolha a tabela: ").strip()
    if t_op == "0" or t_op not in TABELAS:
        return

    nome_tabela, chave_primaria, colunas = TABELAS[t_op]
    
    if operacao == "1":
        executar_insert(nome_tabela, colunas)
    elif operacao == "2":
        executar_update(nome_tabela, chave_primaria, colunas)
    elif operacao == "3":
        executar_delete(nome_tabela, chave_primaria)

def executar_insert(tabela, colunas):
    print(f"\n--- Inserindo em {tabela.upper()} ---")
    valores = []
    for col in colunas:
        val = input(f"Informe o valor para '{col}': ").strip()
        valores.append(val if val != "" else None)
    
    placeholders = ", ".join(["%s"] * len(colunas))
    cols_str = ", ".join(colunas)
    query = f"INSERT INTO {tabela} ({cols_str}) VALUES ({placeholders});"
    
    executar_sql(query, tuple(valores), "Registro inserido com sucesso!")

def executar_update(tabela, chave, colunas):
    print(f"\n--- Atualizando em {tabela.upper()} ---")
    id_registro = input(f"Informe o valor da chave identificadora ({chave}) do registro que deseja alterar: ").strip()
    
    print("\nDeixe em branco os campos que NÃO deseja alterar:")
    set_clauses = []
    valores = []
    
    for col in colunas:
        if col == chave:
            continue
        novo_val = input(f"Novo valor para '{col}': ").strip()
        if novo_val != "":
            set_clauses.append(f"{col} = %s")
            valores.append(novo_val)
            
    if not set_clauses:
        print("⚠️ Nenhum campo foi alterado.")
        return
        
    valores.append(id_registro)
    set_str = ", ".join(set_clauses)
    query = f"UPDATE {tabela} SET {set_str} WHERE {chave} = %s;"
    
    executar_sql(query, tuple(valores), "Registro atualizado com sucesso!")

def executar_delete(tabela, chave):
    print(f"\n--- Excluindo de {tabela.upper()} ---")
    id_registro = input(f"Informe o valor da chave ({chave}) do registro a ser EXCLUÍDO: ").strip()
    
    confirmar = input(f"Tem certeza que deseja excluir o registro {id_registro}? (S/N): ").strip().upper()
    if confirmar != "S":
        print("Operação cancelada.")
        return
        
    query = f"DELETE FROM {tabela} WHERE {chave} = %s;"
    executar_sql(query, (id_registro,), "Registro excluído com sucesso!")

def executar_sql(query, valores, mensagem_sucesso):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, valores)
        conn.commit()
        print(f"🎉 {mensagem_sucesso}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao executar operação no banco: {e}")
    finally:
        cur.close()
        conn.close()