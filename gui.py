import sqlite3
from datetime import datetime, date, timedelta
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, ttk, messagebox, Toplevel, Label, Frame, StringVar, END, LEFT, RIGHT

# Definir adaptadores personalizados para datetime e date
def adapt_datetime(dt):
    return dt.isoformat()

def adapt_date(d):
    return d.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s.decode())

def convert_date(s):
    return date.fromisoformat(s.decode())

def convert_timestamp(val):
    datepart, timepart = val.decode().split(" ")
    year, month, day = map(int, datepart.split("-"))
    timepart_full = timepart.split(".")
    hours, minutes, seconds = map(int, timepart_full[0].split(":"))
    if len(timepart_full) == 2:
        microseconds = int(timepart_full[1])
    else:
        microseconds = 0
    return datetime(year, month, day, hours, minutes, seconds, microseconds)

# Registrar os adaptadores e conversores
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_adapter(date, adapt_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("date", convert_date)
sqlite3.register_converter("timestamp", convert_timestamp)

# Função para criar conexão com o banco de dados
def create_connection():
    return sqlite3.connect('loja_ju.db', 
                         detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)


# No início do arquivo, adicione esta variável global
global tree_produtos, tree_clientes, label_total

# Variáveis globais
global combo_clientes, combo_produtos, entry_quantidade, entry_valor, label_estoque, tree_vendas, tree_itens_venda, label_total, tree_vendas
itens_venda = []

def criar_banco_dados():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Tabela de clientes com código sequencial
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes
                      (codigo_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
                       nome TEXT NOT NULL,
                       telefone TEXT,
                       data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Tabela de produtos
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       tipo TEXT NOT NULL,
                       cor TEXT,
                       tamanho TEXT,
                       preco_custo REAL,
                       preco_venda REAL,
                       quantidade INTEGER)''')
    
    # Tabela de vendas
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       cliente_id TEXT,
                       valor_total REAL,
                       data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                       FOREIGN KEY (cliente_id) REFERENCES clientes (codigo_cliente))''')
    
    # Tabela de itens de venda
    cursor.execute('''CREATE TABLE IF NOT EXISTS itens_venda
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       venda_id INTEGER,
                       produto_id INTEGER,
                       quantidade INTEGER,
                       valor_unitario REAL,
                       FOREIGN KEY (venda_id) REFERENCES vendas (id),
                       FOREIGN KEY (produto_id) REFERENCES produtos (id))''')
    
    # Tabela de pagamentos
    cursor.execute('''CREATE TABLE IF NOT EXISTS pagamentos
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       cliente_id TEXT,
                       venda_id INTEGER,
                       valor_pago REAL,
                       data_pagamento DATETIME,
                       FOREIGN KEY (cliente_id) REFERENCES clientes (codigo_cliente),
                       FOREIGN KEY (venda_id) REFERENCES vendas (id))''')
    
    conn.commit()
    conn.close()

# Certifique-se de chamar esta função no início do seu programa
criar_banco_dados()

def atualizar_tabela_clientes():
    """Atualiza a tabela de clientes com os dados do banco"""
    # Limpar tabela
    for item in tree_clientes.get_children():
        tree_clientes.delete(item)
    
    # Buscar dados atualizados
    conn = create_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT codigo_cliente, nome, COALESCE(telefone, '-') as telefone
        FROM clientes
        ORDER BY codigo_cliente
    """)
    
    # Inserir dados na tabela
    for row in cursor.fetchall():
        codigo, nome, telefone = row
        tree_clientes.insert("", "end", values=(
            codigo,  # Não precisa mais formatar como string
            nome,
            telefone
        ))
    
    conn.close()

def cadastrar_cliente():
    """Cadastra um novo cliente no banco de dados"""
    nome = entry_nome.get().strip()
    telefone = entry_telefone.get().strip()
    
    if not nome:
        messagebox.showerror("Erro", "Por favor, preencha o nome do cliente.")
        return
    
    # Se o telefone estiver vazio, usar None
    if not telefone:
        telefone = None
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO clientes (nome, telefone, data_cadastro)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (nome, telefone))
        
        conn.commit()
        messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso!")
        
        # Limpar campos
        entry_nome.delete(0, END)
        entry_telefone.delete(0, END)
        
        # Atualizar tabela
        atualizar_tabela_clientes()
        
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Erro", f"Erro ao cadastrar cliente: {str(e)}")
    finally:
        conn.close()

def excluir_cliente(event=None):
    """Exclui um cliente selecionado"""
    selected_item = tree_clientes.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Por favor, selecione um cliente para excluir.")
        return

    resposta = messagebox.askyesno("Confirmar exclusão", "Tem certeza que deseja excluir este cliente?")
    if resposta:
        codigo_cliente = tree_clientes.item(selected_item)['values'][0]

        conn = create_connection()
        cursor = conn.cursor()
        try:
            # Verificar se o cliente tem vendas
            cursor.execute("SELECT COUNT(*) FROM vendas WHERE cliente_id = ?", (codigo_cliente,))
            if cursor.fetchone()[0] > 0:
                messagebox.showerror("Erro", "Não é possível excluir um cliente que possui vendas registradas.")
                return

            cursor.execute("DELETE FROM clientes WHERE codigo_cliente = ?", (codigo_cliente,))
            conn.commit()
            tree_clientes.delete(selected_item)
            messagebox.showinfo("Sucesso", "Cliente excluído com sucesso.")
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o cliente: {str(e)}")
        finally:
            conn.close()

def abrir_cadastro_clientes():
    global entry_nome, entry_telefone, tree_clientes

    # Limpar canvas existente
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")

    # Criar formulário de cadastro
    canvas.create_text(700, 50, text="Cadastro de Clientes", font=("Arial", 24))

    canvas.create_text(550, 120, text="Nome:", anchor="e", font=("Arial", 12))
    entry_nome = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 120, window=entry_nome, anchor="w")

    canvas.create_text(550, 160, text="Telefone:", anchor="e", font=("Arial", 12))
    entry_telefone = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 160, window=entry_telefone, anchor="w")

    btn_cadastrar = Button(window, text="Cadastrar", command=cadastrar_cliente, 
                          font=("Arial", 12), bg="#4CAF50", fg="white")
    canvas.create_window(650, 290, window=btn_cadastrar)

    btn_excluir = Button(window, text="Excluir", command=excluir_cliente, 
                        font=("Arial", 12), bg="#f44336", fg="white")
    canvas.create_window(750, 290, window=btn_excluir)

    # Adicionar tabela de clientes
    tree_clientes = ttk.Treeview(window, columns=("Código", "Nome", "Telefone"), show="headings")
    tree_clientes.heading("Código", text="Código")
    tree_clientes.heading("Nome", text="Nome")
    tree_clientes.heading("Telefone", text="Telefone")
    canvas.create_window(700, 500, window=tree_clientes, width=800, height=300)

    # Adicionar evento de tecla para excluir cliente
    tree_clientes.bind("<Delete>", excluir_cliente)

    # Preencher a tabela com os clientes cadastrados
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_cliente, nome, telefone FROM clientes")
    for cliente in cursor.fetchall():
        tree_clientes.insert("", "end", values=cliente)
    conn.close()

def cadastrar_produto():
    global tree_produtos
    
    tipo = entry_tipo.get()
    cor = entry_cor.get()
    tamanho = entry_tamanho.get()
    preco_custo = float(entry_preco_custo.get())
    preco_venda = preco_custo * 2  # Calculando o preço de venda como três vezes o preço de custo
    quantidade = int(entry_quantidade.get())

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO produtos (tipo, cor, tamanho, preco_custo, preco_venda, quantidade) VALUES (?, ?, ?, ?, ?, ?)",
                   (tipo, cor, tamanho, preco_custo, preco_venda, quantidade))
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Limpar campos após cadastro
    entry_tipo.delete(0, END)
    entry_cor.delete(0, END)
    entry_tamanho.delete(0, END)
    entry_preco_custo.delete(0, END)
    entry_quantidade.delete(0, END)

    # Inserir novo produto na tabela
    if 'tree_produtos' in globals() and tree_produtos:
        tree_produtos.insert("", "end", values=(novo_id, tipo, cor, tamanho, preco_custo, preco_venda, quantidade))
    else:
        print("Erro: A tabela de produtos não foi encontrada.")

    messagebox.showinfo("Sucesso", "Produto cadastrado com sucesso!")

def excluir_produto(event=None):
    selected_item = tree_produtos.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Por favor, selecione um produto para excluir.")
        return

    resposta = messagebox.askyesno("Confirmar exclusão", "Tem certeza que deseja excluir este produto?")
    if resposta:
        produto_id = tree_produtos.item(selected_item)['values'][0]

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
            conn.commit()
            tree_produtos.delete(selected_item)
            messagebox.showinfo("Sucesso", "Produto excluído com sucesso.")
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o produto: {str(e)}")
        finally:
            conn.close()

def preencher_campos_produto(event):
    global entry_tipo, entry_cor, entry_tamanho, entry_preco_custo, entry_quantidade, tree_produtos
    
    item_selecionado = tree_produtos.selection()[0]
    valores = tree_produtos.item(item_selecionado, 'values')
    
    # Limpar campos existentes
    entry_tipo.delete(0, END)
    entry_cor.delete(0, END)
    entry_tamanho.delete(0, END)
    entry_preco_custo.delete(0, END)
    entry_quantidade.delete(0, END)
    
    # Preencher campos com os dados do produto selecionado
    entry_tipo.insert(0, valores[1])
    entry_cor.insert(0, valores[2])
    entry_tamanho.insert(0, valores[3])
    entry_preco_custo.insert(0, valores[4])
    entry_quantidade.insert(0, valores[6])

def abrir_cadastro_produtos():
    global entry_tipo, entry_cor, entry_tamanho, entry_preco_custo, entry_quantidade, tree_produtos

    # Limpar canvas existente
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")

    # Criar formulário de cadastro
    canvas.create_text(700, 50, text="Cadastro de Produtos", font=("Arial", 24))

    canvas.create_text(550, 120, text="Tipo:", anchor="e", font=("Arial", 12))
    entry_tipo = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 120, window=entry_tipo, anchor="w")

    canvas.create_text(550, 160, text="Cor:", anchor="e", font=("Arial", 12))
    entry_cor = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 160, window=entry_cor, anchor="w")

    canvas.create_text(550, 200, text="Tamanho:", anchor="e", font=("Arial", 12))
    entry_tamanho = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 200, window=entry_tamanho, anchor="w")

    canvas.create_text(550, 240, text="Preço de Custo:", anchor="e", font=("Arial", 12))
    entry_preco_custo = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 240, window=entry_preco_custo, anchor="w")

    canvas.create_text(550, 280, text="Quantidade:", anchor="e", font=("Arial", 12))
    entry_quantidade = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 280, window=entry_quantidade, anchor="w")

    btn_cadastrar = Button(window, text="Cadastrar", command=cadastrar_produto, 
                          font=("Arial", 12), bg="#4CAF50", fg="white")
    canvas.create_window(650, 330, window=btn_cadastrar)

    btn_atualizar = Button(window, text="Atualizar", command=atualizar_produto, 
                          font=("Arial", 12), bg="#2196F3", fg="white")
    canvas.create_window(750, 330, window=btn_atualizar)

    btn_excluir = Button(window, text="Excluir", command=excluir_produto, 
                        font=("Arial", 12), bg="#f44336", fg="white")
    canvas.create_window(850, 330, window=btn_excluir)

    # Adicionar tabela de produtos
    tree_produtos = ttk.Treeview(window, columns=("ID", "Tipo", "Cor", "Tamanho", "Preço Custo", "Preço Venda", "Quantidade"), show="headings")
    tree_produtos.heading("ID", text="ID")
    tree_produtos.heading("Tipo", text="Tipo")
    tree_produtos.heading("Cor", text="Cor")
    tree_produtos.heading("Tamanho", text="Tamanho")
    tree_produtos.heading("Preço Custo", text="Preço Custo")
    tree_produtos.heading("Preço Venda", text="Preço Venda")
    tree_produtos.heading("Quantidade", text="Quantidade")
    canvas.create_window(700, 500, window=tree_produtos, width=800, height=300)

    # Adicionar evento de clique duplo
    tree_produtos.bind("<Double-1>", preencher_campos_produto)

    # Adicionar evento de tecla para excluir produto
    tree_produtos.bind("<Delete>", excluir_produto)

    # Preencher a tabela com os produtos cadastrados
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, cor, tamanho, preco_custo, preco_venda, quantidade FROM produtos")
    for produto in cursor.fetchall():
        tree_produtos.insert("", "end", values=produto)
    conn.close()

def atualizar_produto():
    global tree_produtos
    
    item_selecionado = tree_produtos.selection()
    if not item_selecionado:
        messagebox.showwarning("Aviso", "Por favor, selecione um produto para atualizar.")
        return

    id_produto = tree_produtos.item(item_selecionado)['values'][0]
    tipo = entry_tipo.get()
    cor = entry_cor.get()
    tamanho = entry_tamanho.get()
    preco_custo = float(entry_preco_custo.get())
    preco_venda = preco_custo * 2
    quantidade = int(entry_quantidade.get())

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE produtos SET tipo=?, cor=?, tamanho=?, preco_custo=?, preco_venda=?, quantidade=? WHERE id=?",
                   (tipo, cor, tamanho, preco_custo, preco_venda, quantidade, id_produto))
    conn.commit()
    conn.close()

    # Atualizar a tabela
    tree_produtos.item(item_selecionado, values=(id_produto, tipo, cor, tamanho, preco_custo, preco_venda, quantidade))

    messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")

    # Limpar campos após atualização
    entry_tipo.delete(0, END)
    entry_cor.delete(0, END)
    entry_tamanho.delete(0, END)
    entry_preco_custo.delete(0, END)
    entry_quantidade.delete(0, END)

def consultar_clientes():
    """Retorna lista de clientes para combobox"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_cliente, nome FROM clientes ORDER BY codigo_cliente")
    clientes = cursor.fetchall()
    conn.close()
    return [f"{codigo} - {nome}" for codigo, nome in clientes]

def consultar_produtos():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, cor, tamanho FROM produtos")
    produtos = cursor.fetchall()
    conn.close()
    return [f"{id} - {tipo} {cor} {tamanho}" for id, tipo, cor, tamanho in produtos]

def atualizar_info_produto(*args):
    produto_selecionado = combo_produtos.get().split(' - ')[0]
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, preco_venda FROM produtos WHERE id = ?", (produto_selecionado,))
    quantidade, preco_venda = cursor.fetchone()
    conn.close()
    
    label_estoque.config(text=f"Estoque: {quantidade}")
    entry_valor.delete(0, 'end')
    entry_valor.insert(0, f"{preco_venda:.2f}")

def consultar_vendas():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, c.nome, p.tipo, p.cor, p.tamanho, v.quantidade, v.valor_total, v.data_venda
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.codigo_cliente
        JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data_venda DESC
    """)
    vendas = cursor.fetchall()
    conn.close()
    return vendas

def atualizar_tabela_vendas():
    """Atualiza a tabela de histórico de vendas"""
    global tree_vendas
    # Limpar a tabela
    for i in tree_vendas.get_children():
        tree_vendas.delete(i)
    
    # Preencher com os dados atualizados
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.id, c.nome, v.valor_total, v.data_venda
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.codigo_cliente
        ORDER BY v.data_venda DESC
    """)
    vendas = cursor.fetchall()
    conn.close()

    for venda in vendas:
        # Formatar o valor e a data
        valor_formatado = f"R$ {venda[2]:.2f}"
        data_formatada = venda[3].strftime("%d/%m/%Y %H:%M")
        tree_vendas.insert("", "end", values=(venda[0], venda[1], valor_formatado, data_formatada))

def atualizar_estoque_e_valor(produto_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, preco_venda FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()
    conn.close()
    return resultado  # Retorna (quantidade, preco_venda)

def calcular_total_venda():
    """Calcula o total da venda atual baseado nos itens da tree_itens_venda"""
    total = 0.0
    for item in tree_itens_venda.get_children():
        valores = tree_itens_venda.item(item)['values']
        total += float(valores[4])  # Soma o subtotal de cada item
    return total

def atualizar_label_total():
    """Atualiza o label com o total da venda"""
    global label_total
    total = calcular_total_venda()
    label_total.config(text=f"R$ {total:.2f}")

def adicionar_item_venda():
    """Adiciona um item à venda atual"""
    if not combo_produtos.get():
        messagebox.showerror("Erro", "Por favor, selecione um produto.")
        return

    try:
        produto_id = combo_produtos.get().split(' - ')[0]
        quantidade = int(entry_quantidade.get())
        valor_unitario = float(entry_valor.get())
        
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
        if valor_unitario <= 0:
            raise ValueError("O valor unitário deve ser maior que zero.")
            
    except ValueError as e:
        messagebox.showerror("Erro", f"Valores inválidos: {str(e)}")
        return

    # Verificar estoque
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,))
    estoque_atual = cursor.fetchone()[0]
    conn.close()

    if estoque_atual < quantidade:
        messagebox.showerror("Erro", f"Estoque insuficiente. Disponível: {estoque_atual}")
        return

    # Calcular subtotal
    subtotal = quantidade * valor_unitario

    # Adicionar à tabela de itens
    tree_itens_venda.insert("", "end", values=(
        produto_id,
        combo_produtos.get().split(' - ')[1],
        quantidade,
        f"{valor_unitario:.2f}",
        f"{subtotal:.2f}"
    ))

    # Atualizar total
    atualizar_label_total()

    # Limpar campos
    combo_produtos.set('')
    entry_quantidade.delete(0, 'end')
    entry_valor.delete(0, 'end')
    label_estoque.config(text="Estoque: ")

def finalizar_venda():
    """Finaliza a venda atual"""
    if not combo_clientes.get():
        messagebox.showerror("Erro", "Por favor, selecione um cliente.")
        return

    if not tree_itens_venda.get_children():
        messagebox.showerror("Erro", "Adicione pelo menos um item à venda.")
        return

    try:
        # Obter o código do cliente (primeira parte antes do hífen)
        cliente_id = combo_clientes.get().split(' - ')[0]
        valor_total = calcular_total_venda()
        
        conn = create_connection()
        cursor = conn.cursor()
        
        # Iniciar transação
        conn.execute("BEGIN TRANSACTION")
        
        try:
            # Inserir venda
            cursor.execute("""
                INSERT INTO vendas (cliente_id, valor_total, data_venda)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (cliente_id, valor_total))
            
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            for item in tree_itens_venda.get_children():
                valores = tree_itens_venda.item(item)['values']
                produto_id = valores[0]
                quantidade = int(valores[2])
                valor_unitario = float(valores[3])

                cursor.execute("""
                    INSERT INTO itens_venda (venda_id, produto_id, quantidade, valor_unitario)
                    VALUES (?, ?, ?, ?)
                """, (venda_id, produto_id, quantidade, valor_unitario))
                
                # Atualizar estoque
                cursor.execute("""
                    UPDATE produtos 
                    SET quantidade = quantidade - ? 
                    WHERE id = ?
                """, (quantidade, produto_id))

            conn.commit()
            messagebox.showinfo("Sucesso", "Venda finalizada com sucesso!")
            
            # Limpar a tela de vendas
            limpar_venda()
            # Atualizar a tabela de vendas
            atualizar_tabela_vendas()
            
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Erro ao finalizar venda: {str(e)}")
            return
        finally:
            conn.close()

    except Exception as e:
        messagebox.showerror("Erro", f"Erro inesperado: {str(e)}")
        return

def limpar_venda():
    """Limpa todos os campos e a tabela de itens da venda atual"""
    combo_clientes.set('')
    combo_produtos.set('')
    entry_quantidade.delete(0, 'end')
    entry_valor.delete(0, 'end')
    label_estoque.config(text="Estoque: ")
    
    # Limpar tabela de itens
    for item in tree_itens_venda.get_children():
        tree_itens_venda.delete(item)
    
    # Atualizar total
    atualizar_label_total()

def limpar_tela():
    for widget in canvas.winfo_children():
        widget.destroy()
    canvas.delete("all")

def cliente_combobox(frame):
    """Cria e retorna um combobox para seleção de clientes."""
    cliente_var = StringVar()
    combobox = ttk.Combobox(frame, textvariable=cliente_var, width=30)
    return combobox, cliente_var

def produto_combobox(frame):
    """Cria e retorna um combobox para seleção de produtos."""
    produto_var = StringVar()
    combobox = ttk.Combobox(frame, textvariable=produto_var, width=30)
    return combobox, produto_var

def abrir_cadastro_vendas():
    global combo_clientes, combo_produtos, entry_quantidade, entry_valor, label_estoque, tree_itens_venda, label_total, tree_vendas
    # Limpar canvas e configurar background
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")
    canvas.create_text(700, 30, text="Cadastro de Vendas", font=("Arial", 24))

    # Frame principal para a venda
    frame_venda = Frame(window)
    canvas.create_window(700, 80, window=frame_venda, width=800)

    # Seleção do cliente
    Label(frame_venda, text="Cliente:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    global combo_clientes
    combo_clientes = ttk.Combobox(frame_venda, width=40)
    combo_clientes['values'] = consultar_clientes()
    combo_clientes.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)

    # Frame para adicionar itens
    frame_itens = Frame(window)
    canvas.create_window(700, 180, window=frame_itens, width=800)

    # Seleção do produto
    Label(frame_itens, text="Produto:", font=("Arial", 12)).grid(row=0, column=0, sticky="e", padx=5, pady=5)
    global combo_produtos
    combo_produtos = ttk.Combobox(frame_itens, width=40)
    combo_produtos['values'] = consultar_produtos()
    combo_produtos.grid(row=0, column=1, columnspan=2, sticky="w", padx=5, pady=5)
    combo_produtos.bind('<<ComboboxSelected>>', atualizar_info_produto)

    # Quantidade e valor
    Label(frame_itens, text="Quantidade:", font=("Arial", 12)).grid(row=1, column=0, sticky="e", padx=5, pady=5)
    global entry_quantidade, entry_valor, label_estoque
    entry_quantidade = Entry(frame_itens, width=10)
    entry_quantidade.grid(row=1, column=1, sticky="w", padx=5, pady=5)
    
    label_estoque = Label(frame_itens, text="Estoque: ", font=("Arial", 12))
    label_estoque.grid(row=1, column=2, sticky="w", padx=5, pady=5)

    Label(frame_itens, text="Valor Unitário:", font=("Arial", 12)).grid(row=2, column=0, sticky="e", padx=5, pady=5)
    entry_valor = Entry(frame_itens, width=15)
    entry_valor.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    # Botão de adicionar item (ajustado para ficar mais visível)
    btn_adicionar = Button(frame_itens, text="Adicionar Item", command=adicionar_item_venda, 
                          font=("Arial", 12), bg="#4CAF50", fg="white")
    btn_adicionar.grid(row=3, column=0, columnspan=3, pady=15)  # Aumentado o pady

    # Tabela de itens da venda atual
    global tree_itens_venda
    tree_itens_venda = ttk.Treeview(window, columns=("ID", "Produto", "Quantidade", "Valor Unit.", "Subtotal"), 
                                   show="headings", height=5)
    for col in ("ID", "Produto", "Quantidade", "Valor Unit.", "Subtotal"):
        tree_itens_venda.heading(col, text=col)
    canvas.create_window(700, 350, window=tree_itens_venda, width=800)

    # Frame para totalização e finalização
    frame_total = Frame(window)
    canvas.create_window(700, 450, window=frame_total, width=800)

    Label(frame_total, text="Total da Venda:", font=("Arial", 14, "bold")).pack(side=LEFT, padx=10)
    label_total = Label(frame_total, text="R$ 0,00", font=("Arial", 14, "bold"))
    label_total.pack(side=LEFT, padx=10)

    # Botões de finalização (ajustados para melhor visibilidade)
    btn_finalizar = Button(frame_total, text="Finalizar Venda", command=finalizar_venda, 
                          font=("Arial", 12), bg="#2196F3", fg="white")
    btn_finalizar.pack(side=RIGHT, padx=10)
    
    btn_cancelar = Button(frame_total, text="Cancelar", command=limpar_venda, 
                         font=("Arial", 12), bg="#f44336", fg="white")
    btn_cancelar.pack(side=RIGHT, padx=10)

    # Histórico de vendas
    Label(window, text="Histórico de Vendas", font=("Arial", 14, "bold")).place(x=700, y=500, anchor="center")
    
    tree_vendas = ttk.Treeview(window, columns=("ID", "Cliente", "Total", "Data"), 
                              show="headings", height=6)
    tree_vendas.heading("ID", text="ID")
    tree_vendas.heading("Cliente", text="Cliente")
    tree_vendas.heading("Total", text="Total")
    tree_vendas.heading("Data", text="Data")
    
    tree_vendas.column("ID", width=50)
    tree_vendas.column("Cliente", width=200)
    tree_vendas.column("Total", width=100)
    tree_vendas.column("Data", width=150)
    
    canvas.create_window(700, 600, window=tree_vendas, width=800)
    
    # Adicionar eventos
    tree_itens_venda.bind("<Delete>", remover_item_venda)
    tree_itens_venda.bind("<Double-1>", editar_item_venda)

    # Carregar vendas existentes
    atualizar_tabela_vendas()

def abrir_dashboard():
    """Abre a tela de dashboard com indicadores de desempenho"""
    # Limpar canvas e configurar background
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")
    canvas.create_text(700, 30, text="Dashboard", font=("Arial", 24))

    # Frame principal
    frame_dashboard = Frame(window)
    canvas.create_window(700, 350, window=frame_dashboard, width=800)

    # Estilo para os frames de indicadores
    style_frame = {"relief": "ridge", "borderwidth": 2, "padx": 15, "pady": 15}
    style_titulo = {"font": ("Arial", 14, "bold"), "pady": 10}
    style_valor = {"font": ("Arial", 12), "pady": 5}

    # Frame Clientes
    frame_clientes = Frame(frame_dashboard, **style_frame)
    frame_clientes.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    Label(frame_clientes, text="Clientes", **style_titulo).pack()
    
    total_clientes = obter_dados_clientes()
    Label(frame_clientes, text=f"Total de Clientes: {total_clientes}", **style_valor).pack()

    # Frame Vendas
    frame_vendas = Frame(frame_dashboard, **style_frame)
    frame_vendas.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    Label(frame_vendas, text="Vendas", **style_titulo).pack()
    
    vendas_mes, vendas_trimestre = obter_dados_vendas()
    Label(frame_vendas, text=f"Vendas (Mês Atual): R$ {vendas_mes:.2f}", **style_valor).pack()
    Label(frame_vendas, text=f"Vendas (3 Meses): R$ {vendas_trimestre:.2f}", **style_valor).pack()

    # Frame Recebimentos
    frame_recebimentos = Frame(frame_dashboard, **style_frame)
    frame_recebimentos.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    Label(frame_recebimentos, text="Recebimentos", **style_titulo).pack()
    
    recebido_mes, recebido_trimestre = obter_dados_recebimentos()
    Label(frame_recebimentos, text=f"Recebido (Mês Atual): R$ {recebido_mes:.2f}", **style_valor).pack()
    Label(frame_recebimentos, text=f"Recebido (3 Meses): R$ {recebido_trimestre:.2f}", **style_valor).pack()

    # Frame Lucro
    frame_lucro = Frame(frame_dashboard, **style_frame)
    frame_lucro.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    
    Label(frame_lucro, text="Lucro Líquido", **style_titulo).pack()
    
    lucro_mes, lucro_trimestre = obter_dados_lucro()
    Label(frame_lucro, text=f"Lucro (Mês Atual): R$ {lucro_mes:.2f}", **style_valor).pack()
    Label(frame_lucro, text=f"Lucro (3 Meses): R$ {lucro_trimestre:.2f}", **style_valor).pack()

    # Configurar grid
    frame_dashboard.grid_columnconfigure(0, weight=1)
    frame_dashboard.grid_columnconfigure(1, weight=1)

def obter_dados_clientes():

    conn = create_connection()
    cursor = conn.cursor()
    
    # Total de clientes
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]
    
   
    conn.close()
    return total_clientes

def obter_dados_vendas():
    """Retorna o total de vendas do mês atual e dos últimos 3 meses"""
    conn = create_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    primeiro_dia_tres_meses = (hoje - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Vendas do mês atual
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) FROM vendas 
        WHERE data_venda >= ?
    """, (primeiro_dia_mes,))
    vendas_mes = cursor.fetchone()[0]
    
    # Vendas dos últimos 3 meses
    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) FROM vendas 
        WHERE data_venda >= ?
    """, (primeiro_dia_tres_meses,))
    vendas_trimestre = cursor.fetchone()[0]
    
    conn.close()
    return vendas_mes, vendas_trimestre

def obter_dados_recebimentos():
    """Retorna o total recebido no mês atual e nos últimos 3 meses"""
    conn = create_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    primeiro_dia_tres_meses = (hoje - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Recebimentos do mês atual
    cursor.execute("""
        SELECT COALESCE(SUM(valor_pago), 0) FROM pagamentos 
        WHERE data_pagamento >= ?
    """, (primeiro_dia_mes,))
    recebido_mes = cursor.fetchone()[0]
    
    # Recebimentos dos últimos 3 meses
    cursor.execute("""
        SELECT COALESCE(SUM(valor_pago), 0) FROM pagamentos 
        WHERE data_pagamento >= ?
    """, (primeiro_dia_tres_meses,))
    recebido_trimestre = cursor.fetchone()[0]
    
    conn.close()
    return recebido_mes, recebido_trimestre

def obter_dados_lucro():
    """Retorna o lucro líquido do mês atual e dos últimos 3 meses"""
    conn = create_connection()
    cursor = conn.cursor()
    
    hoje = datetime.now()
    primeiro_dia_mes = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    primeiro_dia_tres_meses = (hoje - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query para calcular o lucro líquido
    query_lucro = """
        SELECT COALESCE(SUM((iv.valor_unitario - p.preco_custo) * iv.quantidade), 0) as lucro_liquido
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        JOIN produtos p ON iv.produto_id = p.id
        WHERE v.data_venda >= ?
    """
    
    # Lucro do mês atual
    cursor.execute(query_lucro, (primeiro_dia_mes,))
    lucro_mes = cursor.fetchone()[0]
    
    # Lucro dos últimos 3 meses
    cursor.execute(query_lucro, (primeiro_dia_tres_meses,))
    lucro_trimestre = cursor.fetchone()[0]
    
    # Debug: imprimir detalhes do cálculo
    cursor.execute("""
        SELECT 
            v.id as venda_id,
            v.data_venda,
            p.id as produto_id,
            p.tipo,
            iv.quantidade,
            p.preco_custo,
            iv.valor_unitario,
            (iv.valor_unitario - p.preco_custo) * iv.quantidade as lucro_item
        FROM vendas v
        JOIN itens_venda iv ON v.id = iv.venda_id
        JOIN produtos p ON iv.produto_id = p.id
        WHERE v.data_venda >= ?
        ORDER BY v.data_venda DESC
    """, (primeiro_dia_mes,))
    

    conn.close()
    return lucro_mes, lucro_trimestre

def abrir_contas_receber():
    # Limpar canvas e configurar background
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")
    canvas.create_text(700, 30, text="Contas a Receber", font=("Arial", 24))

    # Frame para filtros
    frame_filtros = Frame(window)
    canvas.create_window(700, 80, window=frame_filtros, width=800)

    # Combobox de clientes
    Label(frame_filtros, text="Filtrar por Cliente:", font=("Arial", 12)).pack(side=LEFT, padx=5)
    combo_filtro_clientes = ttk.Combobox(frame_filtros, width=40)
    combo_filtro_clientes['values'] = ['Todos os Clientes'] + consultar_clientes()
    combo_filtro_clientes.set('Todos os Clientes')
    combo_filtro_clientes.pack(side=LEFT, padx=5)

    # Botão de filtrar
    btn_filtrar = Button(frame_filtros, text="Filtrar", 
                        command=lambda: filtrar_contas(tree_contas, combo_filtro_clientes.get()),
                        font=("Arial", 12), bg="#2196F3", fg="white")
    btn_filtrar.pack(side=LEFT, padx=5)

    # Tabela de contas a receber
    tree_contas = ttk.Treeview(window, 
                              columns=("ID", "Data", "Cliente", "Total", "Pago", "Saldo"),
                              show="headings", 
                              height=10)

    # Configuração das colunas
    tree_contas.heading("ID", text="ID")
    tree_contas.heading("Data", text="Data")
    tree_contas.heading("Cliente", text="Cliente")
    tree_contas.heading("Total", text="Total Venda")
    tree_contas.heading("Pago", text="Valor Pago")
    tree_contas.heading("Saldo", text="Saldo")

    tree_contas.column("ID", width=50, anchor="center")
    tree_contas.column("Data", width=100, anchor="center")
    tree_contas.column("Cliente", width=200)
    tree_contas.column("Total", width=100, anchor="e")
    tree_contas.column("Pago", width=100, anchor="e")
    tree_contas.column("Saldo", width=100, anchor="e")

    canvas.create_window(700, 250, window=tree_contas, width=800)

    # Frame para pagamentos
    frame_pagamento = Frame(window)
    canvas.create_window(700, 400, window=frame_pagamento, width=800)

    Label(frame_pagamento, text="Registrar Pagamento", 
          font=("Arial", 14, "bold")).pack(pady=10)

    frame_campos = Frame(frame_pagamento)
    frame_campos.pack()

    # Campo para valor do pagamento
    Label(frame_campos, text="Valor do Pagamento: R$", 
          font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
    entry_valor = Entry(frame_campos, width=15, font=("Arial", 12))
    entry_valor.grid(row=0, column=1, padx=5, pady=5)

    # Botão de registrar pagamento
    btn_registrar = Button(frame_campos, 
                          text="Registrar Pagamento",
                          command=lambda: registrar_pagamento(tree_contas, entry_valor),
                          font=("Arial", 12), 
                          bg="#4CAF50", 
                          fg="white")
    btn_registrar.grid(row=0, column=2, padx=20, pady=5)

    # Frame para resumo
    frame_resumo = Frame(window)
    canvas.create_window(700, 500, window=frame_resumo, width=800)

    Label(frame_resumo, text="Resumo Financeiro", 
          font=("Arial", 14, "bold")).pack(pady=10)

    # Alteração aqui: criar label_total como global
    global label_total_receber
    label_total_receber = Label(frame_resumo, 
                               text=f"Total a Receber: R$ {calcular_total_receber():.2f}",
                               font=("Arial", 12))
    label_total_receber.pack(pady=5)

    # Carregar dados iniciais
    carregar_contas(tree_contas)

def carregar_contas(tree, cliente_filtro=None):
    """Carrega as contas a receber na tabela"""
    for item in tree.get_children():
        tree.delete(item)

    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            v.id,
            v.data_venda,
            c.nome,
            v.valor_total,
            COALESCE((
                SELECT SUM(valor_pago) 
                FROM pagamentos 
                WHERE venda_id = v.id
            ), 0) as valor_pago,
            v.valor_total - COALESCE((
                SELECT SUM(valor_pago) 
                FROM pagamentos 
                WHERE venda_id = v.id
            ), 0) as saldo
        FROM vendas v
        JOIN clientes c ON v.cliente_id = c.codigo_cliente
        WHERE v.valor_total > COALESCE((
            SELECT SUM(valor_pago) 
            FROM pagamentos 
            WHERE venda_id = v.id
        ), 0)
    """

    if cliente_filtro and cliente_filtro != 'Todos os Clientes':
        codigo_cliente = cliente_filtro.split(' - ')[0]
        query += " AND c.codigo_cliente = ?"
        cursor.execute(query, (codigo_cliente,))
    else:
        cursor.execute(query)

    for row in cursor.fetchall():
        venda_id, data_venda, cliente, total, pago, saldo = row
        tree.insert("", "end", values=(
            venda_id,
            data_venda.strftime("%d/%m/%Y"),
            cliente,
            f"R$ {total:.2f}",
            f"R$ {pago:.2f}",
            f"R$ {saldo:.2f}"
        ))

    conn.close()

def filtrar_contas(tree, cliente_filtro):
    """Filtra as contas pelo cliente selecionado"""
    carregar_contas(tree, cliente_filtro)

def atualizar_resumo_financeiro():
    """Atualiza o label com o total a receber"""
    global label_total_receber
    total = calcular_total_receber()
    label_total_receber.config(text=f"Total a Receber: R$ {total:.2f}")

def registrar_pagamento(tree, entry_valor):
    """Registra um pagamento para a venda selecionada"""
    selected = tree.selection()
    if not selected:
        messagebox.showwarning("Aviso", "Selecione uma venda para registrar o pagamento.")
        return

    try:
        valor = float(entry_valor.get().replace("R$", "").strip())
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
    except ValueError as e:
        messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
        return

    venda_id = tree.item(selected[0])['values'][0]
    saldo_atual = float(tree.item(selected[0])['values'][5].replace("R$", "").replace(",", ".").strip())

    if valor > saldo_atual:
        messagebox.showerror("Erro", "O valor do pagamento não pode ser maior que o saldo devedor.")
        return

    conn = create_connection()
    cursor = conn.cursor()

    try:
        # Obter o cliente_id da venda
        cursor.execute("SELECT cliente_id FROM vendas WHERE id = ?", (venda_id,))
        cliente_id = cursor.fetchone()[0]

        # Registrar o pagamento
        cursor.execute("""
            INSERT INTO pagamentos (cliente_id, venda_id, valor_pago, data_pagamento)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (cliente_id, venda_id, valor))

        conn.commit()
        messagebox.showinfo("Sucesso", "Pagamento registrado com sucesso!")

        # Limpar e atualizar
        entry_valor.delete(0, END)
        carregar_contas(tree)
        
        # Atualizar o resumo financeiro
        atualizar_resumo_financeiro()

    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Erro", f"Erro ao registrar pagamento: {str(e)}")
    finally:
        conn.close()

def calcular_total_receber():
    """Calcula o total a receber de todas as vendas"""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(
            valor_total - COALESCE((
                SELECT SUM(valor_pago) 
                FROM pagamentos 
                WHERE venda_id = vendas.id
            ), 0)
        ), 0) as total_receber
        FROM vendas
        WHERE valor_total > COALESCE((
            SELECT SUM(valor_pago) 
            FROM pagamentos 
            WHERE venda_id = vendas.id
        ), 0)
    """)

    total = cursor.fetchone()[0]
    conn.close()
    return total

def verificar_estrutura_banco():
    """Verifica se as tabelas necessárias existem e estão corretas"""
    conn = create_connection()
    cursor = conn.cursor()
    
    # Verificar tabela de vendas
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='vendas'
    """)
    if not cursor.fetchone():
        print("Tabela de vendas não encontrada!")
        return False
    
    # Verificar tabela de pagamentos
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='pagamentos'
    """)
    if not cursor.fetchone():
        print("Tabela de pagamentos não encontrada!")
        return False
    
    # Verificar se existem vendas
    cursor.execute("SELECT COUNT(*) FROM vendas")
    num_vendas = cursor.fetchone()[0]
    
    conn.close()
    return True

# Chamar esta função no início do programa
verificar_estrutura_banco()

def remover_item_venda(event=None):
    """Remove um item selecionado da venda atual"""
    selected_item = tree_itens_venda.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Por favor, selecione um item para remover.")
        return

    resposta = messagebox.askyesno("Confirmar exclusão", "Tem certeza que deseja remover este item?")
    if resposta:
        tree_itens_venda.delete(selected_item)
        atualizar_label_total()  # Atualiza o total da venda após remover o item

def editar_item_venda(event=None):
    """Permite editar um item da venda"""
    selected_item = tree_itens_venda.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Por favor, selecione um item para editar.")
        return

    # Obter valores atuais
    valores = tree_itens_venda.item(selected_item)['values']
    produto_id = valores[0]
    quantidade_atual = valores[2]
    valor_atual = float(valores[3])

    # Criar janela de edição
    janela_edicao = Toplevel()
    janela_edicao.title("Editar Item")
    janela_edicao.geometry("300x150")

    # Campos de edição
    Label(janela_edicao, text="Quantidade:").pack(pady=5)
    entry_quantidade = Entry(janela_edicao)
    entry_quantidade.insert(0, quantidade_atual)
    entry_quantidade.pack(pady=5)

    Label(janela_edicao, text="Valor Unitário:").pack(pady=5)
    entry_valor = Entry(janela_edicao)
    entry_valor.insert(0, valor_atual)
    entry_valor.pack(pady=5)

    def salvar_edicao():
        try:
            nova_quantidade = int(entry_quantidade.get())
            novo_valor = float(entry_valor.get())

            if nova_quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero")
            if novo_valor <= 0:
                raise ValueError("O valor deve ser maior que zero")

            # Verificar estoque
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto_id,))
            estoque_atual = cursor.fetchone()[0]
            conn.close()

            if estoque_atual < nova_quantidade:
                messagebox.showerror("Erro", f"Estoque insuficiente. Disponível: {estoque_atual}")
                return

            # Atualizar item na tabela
            subtotal = nova_quantidade * novo_valor
            tree_itens_venda.item(selected_item, values=(
                produto_id,
                valores[1],  # Nome do produto permanece o mesmo
                nova_quantidade,
                f"{novo_valor:.2f}",
                f"{subtotal:.2f}"
            ))

            atualizar_label_total()
            janela_edicao.destroy()

        except ValueError as e:
            messagebox.showerror("Erro", f"Valores inválidos: {str(e)}")

    Button(janela_edicao, text="Salvar", command=salvar_edicao,
           bg="#4CAF50", fg="white").pack(pady=10)

def adicionar_coluna_data_cadastro():
    """Adiciona a coluna data_cadastro na tabela clientes se ela não existir"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna existe
        cursor.execute("PRAGMA table_info(clientes)")
        colunas = [info[1] for info in cursor.fetchall()]
        
        if 'data_cadastro' not in colunas:
            cursor.execute("""
                ALTER TABLE clientes
                ADD COLUMN data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            """)
            conn.commit()
            print("Coluna data_cadastro adicionada com sucesso!")
    except sqlite3.Error as e:
        print(f"Erro ao adicionar coluna: {e}")
    finally:
        conn.close()

# Chamar esta função ao iniciar o programa
adicionar_coluna_data_cadastro()

window = Tk()
window.geometry("1200x740")
window.configure(bg = "#F8EBFF")

FotoBG = PhotoImage(file=r"assets/Background.png")
FotoClientes = PhotoImage(file=r"assets/Clientes.png")
FotoProdutos = PhotoImage(file=r"assets/Produtos.png")
FotoVendas = PhotoImage(file=r"assets/Vendas.png")
FotoRelatorios = PhotoImage(file=r"assets/Relatorios.png")
FotoContasAReceber = PhotoImage(file=r"assets/ContasAReceber.png")


canvas = Canvas(window, width=1200, height=740)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=FotoBG, anchor="nw")

BtnClientes = Button(window, text='Clientes', image=FotoClientes, command=abrir_cadastro_clientes)
BtnClientes.place(x=52.0, y=196.0)
BtnProdutos = Button(window, text='Produtos', image=FotoProdutos, command=abrir_cadastro_produtos)
BtnProdutos.place(x=52.0, y=283.0)
BtnVendas = Button(window, text='Vendas', image=FotoVendas, command=abrir_cadastro_vendas)
BtnVendas.place(x=52.0, y=370.0)
BtnContasAReceber = Button(window, text='Contas a Receber', image=FotoContasAReceber, command=abrir_contas_receber)
BtnContasAReceber.place(x=52.0, y=457.0)
BtnDashboard = Button(window, text='Dashboard', image=FotoRelatorios, command=abrir_dashboard)
BtnDashboard.place(x=52.0, y=544.0)

window.resizable(False, False)
window.mainloop()