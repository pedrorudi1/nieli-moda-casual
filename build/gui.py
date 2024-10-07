import sqlite3
from datetime import datetime, date
from pathlib import Path
from tkinter import *
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, ttk, messagebox, Toplevel, Label, Frame
from datetime import timedelta

# Definir adaptadores personalizados para datetime e date
def adapt_datetime(dt):
    return dt.isoformat()

def adapt_date(d):
    return d.isoformat()

def convert_datetime(s):
    return datetime.fromisoformat(s.decode())

def convert_date(s):
    return date.fromisoformat(s.decode())

# Registrar os adaptadores e conversores
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_adapter(date, adapt_date)
sqlite3.register_converter("datetime", convert_datetime)
sqlite3.register_converter("date", convert_date)

# Função para criar conexão com o banco de dados
def create_connection():
    return sqlite3.connect('loja_ju.db', detect_types=sqlite3.PARSE_DECLTYPES)


# No início do arquivo, adicione esta variável global
global tree_produtos, tree_clientes

# Variáveis globais
global combo_clientes, combo_produtos, entry_quantidade, entry_valor, label_estoque, tree_vendas, tree_itens_venda
itens_venda = []

def criar_banco_dados():
    conn = create_connection()
    cursor = conn.cursor()
    
    # Tabela de clientes
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes
                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       codigo_cliente TEXT UNIQUE,
                       nome TEXT NOT NULL,
                       telefone TEXT,
                       endereco TEXT,
                       cpf TEXT UNIQUE)''')
    
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

def cadastrar_cliente():
    global tree_clientes
    
    codigo_cliente = gerar_codigo_cliente()  # Você precisa implementar esta função
    nome = entry_nome.get()
    telefone = entry_telefone.get()
    endereco = entry_endereco.get()
    cpf = entry_cpf.get()

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clientes (codigo_cliente, nome, telefone, endereco, cpf) VALUES (?, ?, ?, ?, ?)",
                   (codigo_cliente, nome, telefone, endereco, cpf))
    conn.commit()
    conn.close()

    # Limpar campos após cadastro
    entry_nome.delete(0, END)
    entry_telefone.delete(0, END)
    entry_endereco.delete(0, END)
    entry_cpf.delete(0, END)

    # Inserir novo cliente na tabela
    if 'tree_clientes' in globals() and tree_clientes:
        tree_clientes.insert("", "end", values=(codigo_cliente, nome, telefone, endereco, cpf))
    else:
        print("Erro: A tabela de clientes não foi encontrada.")

    messagebox.showinfo("Sucesso", "Cliente cadastrado com sucesso!")

def gerar_codigo_cliente():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(CAST(codigo_cliente AS INTEGER)) FROM clientes")
    ultimo_codigo = cursor.fetchone()[0]
    conn.close()
    
    if ultimo_codigo is None:
        return "1"
    else:
        return str(int(ultimo_codigo) + 1)

def excluir_cliente(event=None):
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
    global entry_nome, entry_telefone, entry_endereco, entry_cpf, tree_clientes

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

    canvas.create_text(550, 200, text="Endereço:", anchor="e", font=("Arial", 12))
    entry_endereco = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 200, window=entry_endereco, anchor="w")

    canvas.create_text(550, 240, text="CPF:", anchor="e", font=("Arial", 12))
    entry_cpf = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 240, window=entry_cpf, anchor="w")

    btn_cadastrar = Button(window, text="Cadastrar", command=cadastrar_cliente, font=("Arial", 12))
    canvas.create_window(650, 290, window=btn_cadastrar)

    btn_excluir = Button(window, text="Excluir", command=excluir_cliente, font=("Arial", 12))
    canvas.create_window(750, 290, window=btn_excluir)

    # Adicionar tabela de clientes
    tree_clientes = ttk.Treeview(window, columns=("Código", "Nome", "Telefone", "Endereço", "CPF"), show="headings")
    tree_clientes.heading("Código", text="Código")
    tree_clientes.heading("Nome", text="Nome")
    tree_clientes.heading("Telefone", text="Telefone")
    tree_clientes.heading("Endereço", text="Endereço")
    tree_clientes.heading("CPF", text="CPF")
    canvas.create_window(700, 500, window=tree_clientes, width=800, height=300)

    # Adicionar evento de tecla para excluir cliente
    tree_clientes.bind("<Delete>", excluir_cliente)

    # Preencher a tabela com os clientes cadastrados
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_cliente, nome, telefone, endereco, cpf FROM clientes")
    for cliente in cursor.fetchall():
        tree_clientes.insert("", "end", values=cliente)
    conn.close()

def cadastrar_produto():
    global tree_produtos
    
    tipo = entry_tipo.get()
    cor = entry_cor.get()
    tamanho = entry_tamanho.get()
    preco_custo = float(entry_preco_custo.get())
    preco_venda = preco_custo * 3  # Calculando o preço de venda como três vezes o preço de custo
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

    btn_cadastrar = Button(window, text="Cadastrar", command=cadastrar_produto, font=("Arial", 12))
    canvas.create_window(650, 330, window=btn_cadastrar)

    btn_atualizar = Button(window, text="Atualizar", command=atualizar_produto, font=("Arial", 12))
    canvas.create_window(750, 330, window=btn_atualizar)

    btn_excluir = Button(window, text="Excluir", command=excluir_produto, font=("Arial", 12))
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
    preco_venda = preco_custo * 3  # Mantendo a lógica de preço de venda como 3x o preço de custo
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
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_cliente, nome FROM clientes")
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
        tree_vendas.insert("", "end", values=venda)

def adicionar_item_venda():
    if not combo_produtos.get():
        messagebox.showerror("Erro", "Por favor, selecione um produto.")
        return

    try:
        quantidade = int(entry_quantidade.get())
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
    except ValueError as e:
        messagebox.showerror("Erro", f"Quantidade inválida: {str(e)}")
        return

    try:
        valor = float(entry_valor.get())
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
    except ValueError as e:
        messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
        return

    produto = combo_produtos.get().split(' - ')[0]

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto,))
    estoque_atual = cursor.fetchone()[0]
    conn.close()

    if estoque_atual < quantidade:
        messagebox.showerror("Erro", "Não há produto suficiente em estoque.")
        return

    item = (produto, combo_produtos.get().split(' - ')[1], quantidade, valor, valor * quantidade)
    itens_venda.append(item)
    tree_itens_venda.insert("", "end", values=item)

    # Limpar campos após adicionar item
    combo_produtos.set('')
    entry_quantidade.delete(0, 'end')
    entry_valor.delete(0, 'end')
    label_estoque.config(text="Estoque: ")

def cadastrar_venda():
    if not combo_clientes.get():
        messagebox.showerror("Erro", "Por favor, selecione um cliente.")
        return

    if not combo_produtos.get():
        messagebox.showerror("Erro", "Por favor, selecione um produto.")
        return

    try:
        quantidade = int(entry_quantidade.get())
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero.")
    except ValueError as e:
        messagebox.showerror("Erro", f"Quantidade inválida: {str(e)}")
        return

    try:
        valor = float(entry_valor.get())
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")
    except ValueError as e:
        messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
        return

    produto = combo_produtos.get().split(' - ')[0]

    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto,))
    estoque_atual = cursor.fetchone()[0]
    conn.close()

    if estoque_atual < quantidade:
        messagebox.showerror("Erro", "Não há produto suficiente em estoque.")
        return

    # Registrar a venda no banco de dados
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO vendas (cliente_id, valor_total) VALUES (?, ?)",
                   (combo_clientes.get().split(' - ')[0], valor * quantidade))
    venda_id = cursor.lastrowid

    cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, quantidade, valor_unitario) VALUES (?, ?, ?, ?)",
                   (venda_id, produto, quantidade, valor))
    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
                   (quantidade, produto))

    conn.commit()
    conn.close()

    messagebox.showinfo("Sucesso", "Venda cadastrada com sucesso!")
    limpar_venda()

def limpar_venda():
    global itens_venda
    itens_venda = []

def excluir_venda_selecionada(event=None):
    excluir_venda()

def limpar_tela():
    for widget in canvas.winfo_children():
        widget.destroy()
    canvas.delete("all")

def cliente_combobox(frame):
    """Cria e retorna um combobox para seleção de clientes."""
    cliente_var = StringVar()
    combobox = ttk.Combobox(frame, textvariable=cliente_var, width=30)
    preencher_clientes(combobox)  # Preenche o combobox com os clientes cadastrados
    return combobox, cliente_var

def produto_combobox(frame):
    """Cria e retorna um combobox para seleção de produtos."""
    produto_var = StringVar()
    combobox = ttk.Combobox(frame, textvariable=produto_var, width=30)
    preencher_produtos(combobox)  # Preenche o combobox com os produtos cadastrados
    return combobox, produto_var

def abrir_cadastro_vendas():
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")
    
    canvas.create_text(400, 30, text="Cadastro de Vendas", font=("Arial", 18, "bold"))

    # Frame para os campos de entrada
    frame_campos = Frame(window)
    canvas.create_window(400, 200, window=frame_campos, width=700, height=300)

    # Campos de entrada
    Label(frame_campos, text="Cliente:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    cliente_combobox_widget, cliente_var = cliente_combobox(frame_campos)
    cliente_combobox_widget.grid(row=0, column=1, padx=5, pady=5)

    Label(frame_campos, text="Produto:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    produto_combobox_widget, produto_var = produto_combobox(frame_campos)
    produto_combobox_widget.grid(row=1, column=1, padx=5, pady=5)

    Label(frame_campos, text="Quantidade:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    entry_quantidade = Entry(frame_campos, width=10)
    entry_quantidade.grid(row=2, column=1, sticky="w", padx=5, pady=5)

    Label(frame_campos, text="Valor Sugerido:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    entry_valor = Entry(frame_campos, width=15)
    entry_valor.grid(row=3, column=1, sticky="w", padx=5, pady=5)

    # Botão para cadastrar a venda
    btn_cadastrar = Button(frame_campos, text="Cadastrar Venda", command=lambda: cadastrar_venda(cliente_var, produto_var, entry_quantidade, entry_valor))
    btn_cadastrar.grid(row=4, column=0, columnspan=2, pady=10)

def cadastrar_venda(cliente_var, produto_var, entry_quantidade, entry_valor):
    cliente = cliente_var.get()
    produto = produto_var.get()
    quantidade = entry_quantidade.get()
    valor_total = entry_valor.get()

    if not cliente or not produto or not quantidade or not valor_total:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    try:
        quantidade = int(quantidade)
        valor_total = float(valor_total)
    except ValueError:
        messagebox.showerror("Erro", "Por favor, insira valores válidos para quantidade e valor.")
        return

    # Verificar estoque do produto
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade FROM produtos WHERE id = ?", (produto.split(' - ')[0],))
    estoque = cursor.fetchone()

    if not estoque or estoque[0] < quantidade:
        messagebox.showerror("Erro", "Não há produto suficiente em estoque.")
        conn.close()
        return

    # Registrar a venda
    cursor.execute("INSERT INTO vendas (cliente_id, valor_total) VALUES (?, ?)",
                   (cliente.split(' - ')[0], valor_total))
    venda_id = cursor.lastrowid

    cursor.execute("INSERT INTO itens_venda (venda_id, produto_id, quantidade, valor_unitario) VALUES (?, ?, ?, ?)",
                   (venda_id, produto.split(' - ')[0], quantidade, valor_total))
    cursor.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
                   (quantidade, produto.split(' - ')[0]))

    conn.commit()
    conn.close()

    messagebox.showinfo("Sucesso", "Venda cadastrada com sucesso!")
    limpar_campos_venda(cliente_var, produto_var, entry_quantidade, entry_valor)

def limpar_campos_venda(cliente_var, produto_var, quantidade_entry, valor_total_entry):
    cliente_var.set('')
    produto_var.set('')
    quantidade_entry.delete(0, 'end')
    valor_total_entry.delete(0, 'end')

def abrir_dashboard():
    janela_dashboard = Toplevel(window)
    janela_dashboard.title("Dashboard")
    janela_dashboard.geometry("400x350")  # Aumentei um pouco a altura para acomodar a nova informação

    # Obter dados para o dashboard
    vendas_total, vendas_mes_atual, vendas_mes_anterior, total_clientes = obter_dados_dashboard()

    # Criar frame para organizar o layout
    frame_dashboard = Frame(janela_dashboard, borderwidth=2, relief="ridge")
    frame_dashboard.pack(fill="both", expand=True, padx=10, pady=10)

    # Título
    Label(frame_dashboard, text="Dashboard", font=("Arial", 16, "bold")).pack(pady=10)
    
    # Vendas
    Label(frame_dashboard, text="Vendas", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
    Label(frame_dashboard, text=f"Total de Vendas: R$ {vendas_total:.2f}", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
    Label(frame_dashboard, text=f"Vendas no Mês Atual: R$ {vendas_mes_atual:.2f}", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)
    Label(frame_dashboard, text=f"Vendas no Mês Anterior: R$ {vendas_mes_anterior:.2f}", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)

    # Clientes
    Label(frame_dashboard, text="Clientes", font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=5)
    Label(frame_dashboard, text=f"Total de Clientes Cadastrados: {total_clientes}", font=("Arial", 12)).pack(anchor="w", padx=10, pady=2)

def obter_dados_dashboard():
    conn = create_connection()
    cursor = conn.cursor()

    # Calcular datas relevantes
    hoje = datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)

    # Total de vendas
    cursor.execute("SELECT SUM(valor_total) FROM vendas")
    vendas_total = cursor.fetchone()[0] or 0

    # Vendas no mês atual
    cursor.execute("SELECT SUM(valor_total) FROM vendas WHERE data_venda >= ?", (primeiro_dia_mes_atual,))
    vendas_mes_atual = cursor.fetchone()[0] or 0

    # Vendas no mês anterior
    cursor.execute("SELECT SUM(valor_total) FROM vendas WHERE data_venda >= ? AND data_venda < ?", 
                   (primeiro_dia_mes_anterior, primeiro_dia_mes_atual))
    vendas_mes_anterior = cursor.fetchone()[0] or 0

    # Total de clientes cadastrados
    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    conn.close()

    return vendas_total, vendas_mes_atual, vendas_mes_anterior, total_clientes

def obter_total_vendas():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(valor_total) FROM vendas")
    total = cursor.fetchone()[0]
    conn.close()
    return total if total is not None else 0

def abrir_contas_receber():
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")

    canvas.create_text(600, 30, text="Contas a Receber", font=("Arial", 18, "bold"))

    # Frame para o total de vendas
    frame_total = Frame(window, borderwidth=2, relief="ridge")
    canvas.create_window(600, 80, window=frame_total, width=500)

    # Obter o total de vendas
    total_vendas = obter_total_vendas()
    Label(frame_total, text=f"Total de Vendas: R$ {total_vendas:,.2f}", font=("Arial", 14, "bold")).pack(pady=5)

    # Criar Treeview para exibir os clientes e valores
    tree = ttk.Treeview(window, columns=("Cliente", "Total de Vendas", "Valor Pago", "Saldo Devedor"), show="headings")
    tree.heading("Cliente", text="Cliente")
    tree.heading("Total de Vendas", text="Total de Vendas")
    tree.heading("Valor Pago", text="Valor Pago")
    tree.heading("Saldo Devedor", text="Saldo Devedor")
    tree.column("Cliente", width=150)
    tree.column("Total de Vendas", width=100)
    tree.column("Valor Pago", width=100)
    tree.column("Saldo Devedor", width=100)
    canvas.create_window(600, 300, window=tree, width=500, height=300)

    # Adicionar scrollbar
    scrollbar = ttk.Scrollbar(window, orient="vertical", command=tree.yview)
    canvas.create_window(850, 300, window=scrollbar, height=300)
    tree.configure(yscrollcommand=scrollbar.set)


    # Frame para registrar pagamento
    frame_pagamento = Frame(window)
    canvas.create_window(600, 500, window=frame_pagamento, width=600)

    Label(frame_pagamento, text="Registrar Pagamento:", font=("Arial", 12, "bold")).pack(side="left", padx=(0, 10))
    entry_valor = Entry(frame_pagamento, width=15)
    entry_valor.pack(side="left", padx=(0, 10))
    btn_pagar = Button(frame_pagamento, text="Pagar", command=lambda: registrar_pagamento(tree, entry_valor))
    btn_pagar.pack(side="left")

def preencher_clientes(combobox):
    """Preenche o combobox com os clientes cadastrados no banco de dados."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT codigo_cliente, nome FROM clientes")
    clientes = cursor.fetchall()
    conn.close()

    # Adiciona os clientes ao combobox no formato "código - nome"
    combobox['values'] = [f"{codigo} - {nome}" for codigo, nome in clientes]

def preencher_produtos(combobox):
    """Preenche o combobox com os produtos cadastrados no banco de dados."""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, tipo, cor, tamanho FROM produtos")
    produtos = cursor.fetchall()
    conn.close()

    # Adiciona os produtos ao combobox no formato "id - tipo cor tamanho"
    combobox['values'] = [f"{id} - {tipo} {cor} {tamanho}" for id, tipo, cor, tamanho in produtos]

window = Tk()
window.geometry("1200x740")
window.configure(bg = "#F8EBFF")

FotoBG = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\Background.png")
FotoClientes = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\Clientes.png")
FotoProdutos = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\Produtos.png")
FotoVendas = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\Vendas.png")
FotoRelatorios = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\Relatorios.png")
FotoContasAReceber = PhotoImage(file=r"C:\Users\pedro\Códigos\Repositório Pedro\Loja Ju\ContasAReceber.png")


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