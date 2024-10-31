import sqlite3
from datetime import datetime, date, timedelta
import pytz
from tkinter import Tk, Canvas, Entry, Button, PhotoImage, ttk, messagebox, Toplevel, Label, Frame, StringVar, END, LEFT, RIGHT, BOTH


FUSO_HORARIO = pytz.timezone('America/Sao_Paulo')

# Definir adaptadores personalizados para datetime e date
def adapt_datetime(dt):
    """Converte datetime para string ISO com fuso horário"""
    if dt.tzinfo is None:
        dt = FUSO_HORARIO.localize(dt)
    return dt.isoformat()

def adapt_date(d):
    return d.isoformat()

def convert_datetime(s):
    """Converte string ISO para datetime com fuso horário"""
    dt = datetime.fromisoformat(s.decode())
    if dt.tzinfo is None:
        dt = FUSO_HORARIO.localize(dt)
    return dt

def convert_date(s):
    return date.fromisoformat(s.decode())

def convert_timestamp(val):
    """Converte timestamp para datetime com fuso horário"""
    try:
        # Tenta converter diretamente se estiver em formato ISO
        dt = datetime.fromisoformat(val.decode())
        if dt.tzinfo is None:
            dt = FUSO_HORARIO.localize(dt)
        return dt
    except ValueError:
        try:
            # Tenta o formato antigo "YYYY-MM-DD HH:MM:SS.mmmmmm"
            datepart, timepart = val.decode().split(" ")
            year, month, day = map(int, datepart.split("-"))
            timepart_full = timepart.split(".")
            hours, minutes, seconds = map(int, timepart_full[0].split(":"))
            if len(timepart_full) == 2:
                microseconds = int(timepart_full[1])
            else:
                microseconds = 0
            dt = datetime(year, month, day, hours, minutes, seconds, microseconds)
            return FUSO_HORARIO.localize(dt)
        except (ValueError, IndexError):
            # Se falhar, tenta interpretar como data simples
            try:
                dt = datetime.strptime(val.decode(), "%Y-%m-%d")
                return FUSO_HORARIO.localize(dt)
            except ValueError:
                # Se tudo falhar, retorna a data atual
                return datetime.now(FUSO_HORARIO)

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


global combo_clientes, combo_produtos, entry_quantidade, entry_valor, label_estoque
global tree_vendas, tree_itens_venda, label_total, tree_produtos, tree_clientes, entry_preco_venda
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
    
    if not telefone:
        telefone = "-"
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        agora = datetime.now(FUSO_HORARIO)
        cursor.execute("""
            INSERT INTO clientes (nome, telefone, data_cadastro)
            VALUES (?, ?, ?)
        """, (nome, telefone, agora))
        
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
    preco_venda = float(entry_preco_venda.get())
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
    entry_preco_venda.delete(0, END)
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
    global entry_tipo, entry_cor, entry_tamanho, entry_preco_custo, entry_quantidade, tree_produtos, entry_preco_venda
    
    item_selecionado = tree_produtos.selection()[0]
    valores = tree_produtos.item(item_selecionado, 'values')
    
    # Limpar campos existentes
    entry_tipo.delete(0, END)
    entry_cor.delete(0, END)
    entry_tamanho.delete(0, END)
    entry_preco_custo.delete(0, END)
    entry_preco_venda.delete(0, END)
    entry_quantidade.delete(0, END)
    
    # Preencher campos com os dados do produto selecionado
    entry_tipo.insert(0, valores[1])
    entry_cor.insert(0, valores[2])
    entry_tamanho.insert(0, valores[3])
    entry_preco_custo.insert(0, valores[4])
    entry_preco_venda.insert(0, valores[5])
    entry_quantidade.insert(0, valores[6])

def abrir_cadastro_produtos():
    global entry_tipo, entry_cor, entry_tamanho, entry_preco_custo, entry_quantidade, tree_produtos, entry_preco_venda

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

    canvas.create_text(550, 280, text="Preço de Venda: ", anchor="e", font=("Arial, 12"))
    entry_preco_venda = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560,280, window=entry_preco_venda, anchor="w")

    canvas.create_text(550, 320, text="Quantidade:", anchor="e", font=("Arial", 12))
    entry_quantidade = Entry(window, width=40, font=("Arial", 12))
    canvas.create_window(560, 320, window=entry_quantidade, anchor="w")

    btn_cadastrar = Button(window, text="Cadastrar", command=cadastrar_produto, 
                          font=("Arial", 12), bg="#4CAF50", fg="white")
    canvas.create_window(650, 360, window=btn_cadastrar)

    btn_atualizar = Button(window, text="Atualizar", command=atualizar_produto, 
                          font=("Arial", 12), bg="#2196F3", fg="white")
    canvas.create_window(750, 360, window=btn_atualizar)

    btn_excluir = Button(window, text="Excluir", command=excluir_produto, 
                        font=("Arial", 12), bg="#f44336", fg="white")
    canvas.create_window(850, 360, window=btn_excluir)

    # Adicionar tabela de produtos
    tree_produtos = ttk.Treeview(window, columns=("ID", "Tipo", "Cor", "Tamanho", "Preço Custo", "Preço Venda", "Quantidade"), show="headings")
    tree_produtos.heading("ID", text="ID")
    tree_produtos.heading("Tipo", text="Tipo")
    tree_produtos.heading("Cor", text="Cor")
    tree_produtos.heading("Tamanho", text="Tamanho")
    tree_produtos.heading("Preço Custo", text="Preço Custo")
    tree_produtos.heading("Preço Venda", text="Preço Venda")
    tree_produtos.heading("Quantidade", text="Quantidade")
    canvas.create_window(700, 540, window=tree_produtos, width=800, height=300)

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

def excluir_venda(event=None):
    selected_item = tree_vendas.selection()
    if not selected_item:
        messagebox.showwarning("Aviso", "Por favor, selecione uma venda para excluir.")
        return

    resposta = messagebox.askyesno("Confirmar exclusão", "Tem certeza que deseja excluir esta venda?")
    if resposta:
        venda_id = tree_vendas.item(selected_item)['values'][0]

        conn = create_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
            conn.commit()
            tree_vendas.delete(selected_item)
            messagebox.showinfo("Sucesso", "Venda excluída com sucesso.")
        except sqlite3.Error as e:
            conn.rollback()
            messagebox.showerror("Erro", f"Ocorreu um erro ao excluir o produto: {str(e)}")
        finally:
            conn.close()

def atualizar_tabela_vendas():
    global tree_vendas
    # Limpar a tabela
    for i in tree_vendas.get_children():
        tree_vendas.delete(i)
    
    # Preencher com os dados atualizados
    conn = create_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT v.id, c.nome, v.valor_total, v.data_venda
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.codigo_cliente
            ORDER BY v.data_venda DESC
        """)
        vendas = cursor.fetchall()
        
        for venda in vendas:
            # Formatar o valor e a data
            valor_formatado = f"R$ {venda[2]:.2f}"
            # Garantir que a data seja um objeto datetime
            if isinstance(venda[3], datetime):
                data_venda = venda[3]
            else:
                data_venda = convert_timestamp(venda[3].encode())
            data_formatada = data_venda.strftime("%d/%m/%Y %H:%M")
            
            tree_vendas.insert("", "end", values=(
                venda[0],
                venda[1],
                valor_formatado,
                data_formatada
            ))
    except Exception as e:
        print(f"Erro ao atualizar tabela de vendas: {e}")
    finally:
        conn.close()

def atualizar_estoque_e_valor(produto_id):
    """Retorna a quantidade em estoque e preço de venda de um produto"""
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT quantidade, preco_venda FROM produtos WHERE id = ?", (produto_id,))
    resultado = cursor.fetchone()
    conn.close()
    
    if resultado is None:
        return 0, 0.0  # Retorna valores padrão se o produto não for encontrado
    return resultado

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
        messagebox.showwarning("Aviso", "Por favor, selecione um produto.")
        return
    
    try:
        quantidade = int(entry_quantidade.get())
        if quantidade <= 0:
            raise ValueError("A quantidade deve ser maior que zero")
    except ValueError as e:
        messagebox.showerror("Erro", f"Quantidade inválida: {str(e)}")
        return

    # Obter ID do produto (primeira parte antes do hífen)
    produto_id = combo_produtos.get().split(' - ')[0]
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar estoque e preços (normal e promocional)
        cursor.execute("""
            SELECT tipo, cor, tamanho, quantidade, preco_venda, promocao, preco_promocional 
            FROM produtos 
            WHERE id = ?
        """, (produto_id,))
        
        produto = cursor.fetchone()
        if not produto:
            messagebox.showerror("Erro", "Produto não encontrado.")
            return
            
        tipo, cor, tamanho, estoque, preco_normal, em_promocao, preco_promocional = produto
        
        if estoque < quantidade:
            messagebox.showerror("Erro", f"Estoque insuficiente. Disponível: {estoque}")
            return
        
        # Determinar qual preço usar
        preco_venda = preco_promocional if em_promocao and preco_promocional is not None else preco_normal
        
        # Calcular subtotal
        subtotal = quantidade * preco_venda
        
        # Verificar se o produto já está na lista
        for item in tree_itens_venda.get_children():
            valores = tree_itens_venda.item(item)['values']
            if valores[0] == produto_id:  # Se encontrar o mesmo produto
                nova_qtd = valores[2] + quantidade
                if nova_qtd > estoque:
                    messagebox.showerror("Erro", f"Estoque insuficiente. Disponível: {estoque}")
                    return
                    
                novo_subtotal = nova_qtd * preco_venda
                tree_itens_venda.item(item, values=(
                    produto_id,
                    f"{tipo} - {cor} - {tamanho}",
                    nova_qtd,
                    f"{preco_venda:.2f}",
                    f"{novo_subtotal:.2f}"
                ))
                break
        else:  # Se não encontrar o produto na lista
            # Adicionar novo item
            tree_itens_venda.insert("", "end", values=(
                produto_id,
                f"{tipo} - {cor} - {tamanho}",
                quantidade,
                f"{preco_venda:.2f}",
                f"{subtotal:.2f}"
            ))
        
        # Limpar campos
        entry_quantidade.delete(0, END)
        entry_quantidade.insert(0, "1")
        combo_produtos.set("")  # Limpar seleção de produto
        
        # Atualizar total
        atualizar_label_total()
        
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao adicionar item: {str(e)}")
    finally:
        conn.close()

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
            agora = datetime.now(FUSO_HORARIO)
            cursor.execute("""
                INSERT INTO vendas (cliente_id, valor_total, data_venda)
                VALUES (?, ?, ?)
            """, (cliente_id, valor_total, agora))
            
            venda_id = cursor.lastrowid

            # Inserir itens da venda
            for item in tree_itens_venda.get_children():
                valores = tree_itens_venda.item(item)['values']
                produto_id = valores[0]
                quantidade = int(valores[2])
                valor_unitario = float(valores[3])

                # Verificar estoque antes de finalizar
                estoque_atual, _ = atualizar_estoque_e_valor(produto_id)
                if estoque_atual < quantidade:
                    raise ValueError(f"Estoque insuficiente para o produto ID {produto_id}")

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
        except ValueError as e:
            conn.rollback()
            messagebox.showerror("Erro", str(e))
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
    tree_vendas.bind("<Delete>", excluir_venda)

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

    # Criar notebook (sistema de abas)
    notebook = ttk.Notebook(window)
    canvas.create_window(700, 350, window=notebook, width=800, height=600)

    # Aba de Contas a Receber
    tab_contas = Frame(notebook)
    notebook.add(tab_contas, text="Contas a Receber")

    # Aba de Histórico de Pagamentos
    tab_historico = Frame(notebook)
    notebook.add(tab_historico, text="Histórico de Pagamentos")

    # Frame para filtros (na aba de contas)
    frame_filtros = Frame(tab_contas)
    frame_filtros.pack(pady=10)

    # Combobox de clientes
    Label(frame_filtros, text="Filtrar por Cliente:", font=("Arial", 12)).pack(side=LEFT, padx=5)
    combo_filtro_clientes = ttk.Combobox(frame_filtros, width=40)
    combo_filtro_clientes['values'] = ['Todos os Clientes'] + consultar_clientes()
    combo_filtro_clientes.set('Todos os Clientes')
    combo_filtro_clientes.pack(side=LEFT, padx=5)

    btn_filtrar = Button(frame_filtros, text="Filtrar", 
                        command=lambda: filtrar_contas(tree_contas, combo_filtro_clientes.get()),
                        font=("Arial", 12), bg="#2196F3", fg="white")
    btn_filtrar.pack(side=LEFT, padx=5)

    # Tabela de contas a receber
    tree_contas = ttk.Treeview(tab_contas, 
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

    tree_contas.pack(pady=10, padx=10, fill=BOTH, expand=True)

    # Frame para pagamentos
    frame_pagamento = Frame(tab_contas)
    frame_pagamento.pack(pady=10)

    # Campo para valor do pagamento
    Label(frame_pagamento, text="Valor do Pagamento: R$", 
          font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5)
    entry_valor = Entry(frame_pagamento, width=15, font=("Arial", 12))
    entry_valor.grid(row=0, column=1, padx=5, pady=5)

    # Botão de registrar pagamento
    btn_registrar = Button(frame_pagamento, 
                          text="Registrar Pagamento",
                          command=lambda: registrar_pagamento(tree_contas, entry_valor),
                          font=("Arial", 12), 
                          bg="#4CAF50", 
                          fg="white")
    btn_registrar.grid(row=0, column=2, padx=20, pady=5)

    frame_filtros_historico = Frame(tab_historico)
    frame_filtros_historico.pack(pady=10)

    Label(frame_filtros_historico, text="Filtrar por Cliente:", font=("Arial", 12)).pack(side=LEFT, padx=5)
    combo_filtro_historico = ttk.Combobox(frame_filtros_historico, width=40)
    combo_filtro_historico['values'] = ['Todos os Clientes'] + consultar_clientes()
    combo_filtro_historico.set('Todos os Clientes')
    combo_filtro_historico.pack(side=LEFT, padx=5)

    # Filtros de data
    Label(frame_filtros_historico, text="De:", font=("Arial", 12)).pack(side=LEFT, padx=5)
    data_inicial = Entry(frame_filtros_historico, width=10)
    data_inicial.pack(side=LEFT, padx=2)
    
    Label(frame_filtros_historico, text="Até:", font=("Arial", 12)).pack(side=LEFT, padx=5)
    data_final = Entry(frame_filtros_historico, width=10)
    data_final.pack(side=LEFT, padx=2)

    btn_filtrar_historico = Button(frame_filtros_historico, text="Filtrar", 
                                 command=lambda: filtrar_historico_pagamentos(
                                     tree_historico, 
                                     combo_filtro_historico.get(),
                                     data_inicial.get(),
                                     data_final.get()
                                 ),
                                 font=("Arial", 12), bg="#2196F3", fg="white")
    btn_filtrar_historico.pack(side=LEFT, padx=5)

    # Tabela de histórico de pagamentos
    tree_historico = ttk.Treeview(tab_historico, 
                                 columns=("ID", "Data Pagamento", "Cliente", "Venda", "Valor Pago"),
                                 show="headings", 
                                 height=15)

    tree_historico.heading("ID", text="ID")
    tree_historico.heading("Data Pagamento", text="Data Pagamento")
    tree_historico.heading("Cliente", text="Cliente")
    tree_historico.heading("Venda", text="Venda")
    tree_historico.heading("Valor Pago", text="Valor Pago")

    tree_historico.column("ID", width=50, anchor="center")
    tree_historico.column("Data Pagamento", width=150, anchor="center")
    tree_historico.column("Cliente", width=200)
    tree_historico.column("Venda", width=100, anchor="center")
    tree_historico.column("Valor Pago", width=100, anchor="e")

    tree_historico.pack(pady=10, padx=10, fill=BOTH, expand=True)

    # Carregar dados iniciais
    carregar_contas(tree_contas)
    carregar_historico_pagamentos(tree_historico)

def carregar_historico_pagamentos(tree, cliente_filtro=None, data_inicial=None, data_final=None):
    """Carrega o histórico de pagamentos na tabela"""
    for item in tree.get_children():
        tree.delete(item)

    conn = create_connection()
    cursor = conn.cursor()

    query = """
        SELECT 
            p.id,
            p.data_pagamento,
            c.nome,
            p.venda_id,
            p.valor_pago
        FROM pagamentos p
        JOIN clientes c ON p.cliente_id = c.codigo_cliente
        WHERE 1=1
    """
    params = []

    if cliente_filtro and cliente_filtro != 'Todos os Clientes':
        codigo_cliente = cliente_filtro.split(' - ')[0]
        query += " AND c.codigo_cliente = ?"
        params.append(codigo_cliente)

    if data_inicial:
        try:
            data_inicial = datetime.strptime(data_inicial, "%d/%m/%Y")
            query += " AND date(p.data_pagamento) >= date(?)"
            params.append(data_inicial.strftime("%Y-%m-%d"))
        except ValueError:
            pass

    if data_final:
        try:
            data_final = datetime.strptime(data_final, "%d/%m/%Y")
            query += " AND date(p.data_pagamento) <= date(?)"
            params.append(data_final.strftime("%Y-%m-%d"))
        except ValueError:
            pass

    query += " ORDER BY p.data_pagamento DESC"

    cursor.execute(query, params)
    for row in cursor.fetchall():
        pagamento_id, data_pagamento, cliente, venda_id, valor = row
        tree.insert("", "end", values=(
            pagamento_id,
            data_pagamento.strftime("%d/%m/%Y %H:%M") if isinstance(data_pagamento, datetime) 
            else convert_timestamp(data_pagamento.encode()).strftime("%d/%m/%Y %H:%M"),
            cliente,
            f"#{venda_id}",
            f"R$ {valor:.2f}"
        ))

    conn.close()

def filtrar_historico_pagamentos(tree, cliente_filtro, data_inicial, data_final):
    """Filtra o histórico de pagamentos"""
    carregar_historico_pagamentos(tree, cliente_filtro, data_inicial, data_final)

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

    # Criar janela de edição
    janela_edicao = Toplevel()
    janela_edicao.title("Editar Item")
    janela_edicao.geometry("300x150")

    # Campos de edição
    Label(janela_edicao, text="Quantidade:").pack(pady=5)
    entry_quantidade = Entry(janela_edicao)
    entry_quantidade.insert(0, quantidade_atual)
    entry_quantidade.pack(pady=5)

    def salvar_edicao():
        try:
            nova_quantidade = int(entry_quantidade.get())
            if nova_quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero")

            # Verificar estoque e preço atual
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT quantidade, preco_venda, promocao, preco_promocional 
                FROM produtos 
                WHERE id = ?
            """, (produto_id,))
            estoque_atual, preco_normal, em_promocao, preco_promocional = cursor.fetchone()
            conn.close()

            if estoque_atual < nova_quantidade:
                messagebox.showerror("Erro", f"Estoque insuficiente. Disponível: {estoque_atual}")
                return

            # Determinar qual preço usar
            preco_venda = preco_promocional if em_promocao and preco_promocional is not None else preco_normal

            # Atualizar item na tabela
            subtotal = nova_quantidade * preco_venda
            tree_itens_venda.item(selected_item, values=(
                produto_id,
                valores[1],  # Nome do produto permanece o mesmo
                nova_quantidade,
                f"{preco_venda:.2f}",
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

def calcular_total_receber():
    """Calcula o total de valores a receber"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Calcula o total de vendas
        cursor.execute("""
            SELECT COALESCE(SUM(valor_total), 0)
            FROM vendas
        """)
        total_vendas = cursor.fetchone()[0]
        
        # Calcula o total já pago
        cursor.execute("""
            SELECT COALESCE(SUM(valor_pago), 0)
            FROM pagamentos
        """)
        total_pago = cursor.fetchone()[0]
        
        # O total a receber é a diferença
        total_receber = total_vendas - total_pago
        
        return total_receber
        
    except sqlite3.Error as e:
        print(f"Erro ao calcular total a receber: {e}")
        return 0.0
    finally:
        conn.close()

def atualizar_total_receber():
    """Atualiza o label com o total a receber"""
    global label_total_receber
    if 'label_total_receber' in globals():
        total = calcular_total_receber()
        label_total_receber.config(text=f"Total a Receber: R$ {total:.2f}")

def registrar_pagamento(tree, entry_valor):
    """Registra um novo pagamento"""
    selected_item = tree.selection()
    if not selected_item:
        messagebox.showerror("Erro", "Selecione uma venda para registrar o pagamento.")
        return

    try:
        valor = float(entry_valor.get())
        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero")
    except ValueError as e:
        messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
        return

    venda_id = tree.item(selected_item)['values'][0]
    
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Obter informações da venda
        cursor.execute("""
            SELECT v.cliente_id, v.valor_total, 
                   (SELECT COALESCE(SUM(valor_pago), 0) FROM pagamentos WHERE venda_id = v.id)
            FROM vendas v
            WHERE v.id = ?
        """, (venda_id,))
        
        cliente_id, valor_total, valor_ja_pago = cursor.fetchone()
        saldo = valor_total - valor_ja_pago

        if valor > saldo:
            messagebox.showerror("Erro", f"Valor excede o saldo devedor (R$ {saldo:.2f})")
            return

        # Registrar o pagamento
        agora = datetime.now(FUSO_HORARIO)
        cursor.execute("""
            INSERT INTO pagamentos (cliente_id, venda_id, valor_pago, data_pagamento)
            VALUES (?, ?, ?, ?)
        """, (cliente_id, venda_id, valor, agora))

        conn.commit()
        messagebox.showinfo("Sucesso", "Pagamento registrado com sucesso!")
        
        # Limpar campo de valor
        entry_valor.delete(0, END)
        
        # Atualizar as tabelas
        carregar_contas(tree)
        atualizar_total_receber()
        

            
    except sqlite3.Error as e:
        conn.rollback()
        messagebox.showerror("Erro", f"Erro ao registrar pagamento: {str(e)}")
    finally:
        conn.close()

def carregar_contas(tree):
    """Carrega as contas a receber na tabela"""
    for item in tree.get_children():
        tree.delete(item)

    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                v.id,
                v.data_venda,
                c.nome,
                v.valor_total,
                COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0) as valor_pago,
                v.valor_total - COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0) as saldo
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.codigo_cliente
            WHERE v.valor_total > COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0)
            ORDER BY v.data_venda DESC
        """)
        
        for row in cursor.fetchall():
            venda_id, data_venda, cliente, valor_total, valor_pago, saldo = row
            
            # Converter e formatar a data
            if isinstance(data_venda, datetime):
                data_formatada = data_venda.strftime("%d/%m/%Y %H:%M")
            else:
                data_formatada = convert_timestamp(data_venda.encode()).strftime("%d/%m/%Y %H:%M")
            
            tree.insert("", "end", values=(
                venda_id,
                data_formatada,
                cliente,
                f"R$ {valor_total:.2f}",
                f"R$ {valor_pago:.2f}",
                f"R$ {saldo:.2f}"
            ))
            
    except sqlite3.Error as e:
        print(f"Erro ao carregar contas: {e}")
    finally:
        conn.close()

def filtrar_contas(tree, cliente_filtro):
    """Filtra as contas a receber por cliente"""
    for item in tree.get_children():
        tree.delete(item)

    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        query = """
            SELECT 
                v.id,
                v.data_venda,
                c.nome,
                v.valor_total,
                COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0) as valor_pago,
                v.valor_total - COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0) as saldo
            FROM vendas v
            JOIN clientes c ON v.cliente_id = c.codigo_cliente
            WHERE v.valor_total > COALESCE((SELECT SUM(valor_pago) FROM pagamentos WHERE venda_id = v.id), 0)
        """
        
        params = []
        
        # Adicionar filtro de cliente se não for "Todos os Clientes"
        if cliente_filtro and cliente_filtro != 'Todos os Clientes':
            codigo_cliente = cliente_filtro.split(' - ')[0]
            query += " AND c.codigo_cliente = ?"
            params.append(codigo_cliente)
            
        query += " ORDER BY v.data_venda DESC"
        
        cursor.execute(query, params)
        
        for row in cursor.fetchall():
            venda_id, data_venda, cliente, valor_total, valor_pago, saldo = row
            
            # Converter e formatar a data
            if isinstance(data_venda, datetime):
                data_formatada = data_venda.strftime("%d/%m/%Y %H:%M")
            else:
                data_formatada = convert_timestamp(data_venda.encode()).strftime("%d/%m/%Y %H:%M")
            
            tree.insert("", "end", values=(
                venda_id,
                data_formatada,
                cliente,
                f"R$ {valor_total:.2f}",
                f"R$ {valor_pago:.2f}",
                f"R$ {saldo:.2f}"
            ))
            
        # Atualizar o total após a filtragem
        atualizar_total_receber()
            
    except sqlite3.Error as e:
        print(f"Erro ao filtrar contas: {e}")
        messagebox.showerror("Erro", f"Erro ao filtrar contas: {str(e)}")
    finally:
        conn.close()

def adicionar_coluna_promocao():
    """Adiciona a coluna promocao na tabela produtos se ela não existir"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        # Verificar se a coluna existe
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = [info[1] for info in cursor.fetchall()]
        
        if 'promocao' not in colunas:
            cursor.execute("""
                ALTER TABLE produtos
                ADD COLUMN promocao INTEGER DEFAULT 0
            """)
            conn.commit()
            print("Coluna promocao adicionada com sucesso!")
    except sqlite3.Error as e:
        print(f"Erro ao adicionar coluna: {e}")
    finally:
        conn.close()

def abrir_promocoes():
    """Abre a tela de promoções"""
    global tree_promocoes
    
    # Limpar canvas e configurar background
    canvas.delete("all")
    canvas.create_image(0, 0, image=FotoBG, anchor="nw")
    canvas.create_text(700, 30, text="Promoções", font=("Arial", 24))

    # Frame principal
    frame_promocoes = Frame(window)
    canvas.create_window(700, 350, window=frame_promocoes, width=800)

    # Criar notebook para abas
    notebook = ttk.Notebook(frame_promocoes)
    notebook.pack(fill=BOTH, expand=True)

    # Aba de Produtos em Promoção
    tab_produtos = Frame(notebook)
    notebook.add(tab_produtos, text="Produtos em Promoção")

    # Aba de Gerenciar Promoções
    tab_gerenciar = Frame(notebook)
    notebook.add(tab_gerenciar, text="Gerenciar Promoções")

    # Tabela de produtos em promoção (primeira aba)
    tree_promocoes = ttk.Treeview(tab_produtos, 
                                 columns=("ID", "Tipo", "Cor", "Tamanho", "Preço Normal", "Preço Promocional"),
                                 show="headings", 
                                 height=15)

    tree_promocoes.heading("ID", text="ID")
    tree_promocoes.heading("Tipo", text="Tipo")
    tree_promocoes.heading("Cor", text="Cor")
    tree_promocoes.heading("Tamanho", text="Tamanho")
    tree_promocoes.heading("Preço Normal", text="Preço Normal")
    tree_promocoes.heading("Preço Promocional", text="Preço Promocional")

    tree_promocoes.column("ID", width=50, anchor="center")
    tree_promocoes.column("Tipo", width=150)
    tree_promocoes.column("Cor", width=100)
    tree_promocoes.column("Tamanho", width=100)
    tree_promocoes.column("Preço Normal", width=100, anchor="e")
    tree_promocoes.column("Preço Promocional", width=100, anchor="e")

    tree_promocoes.pack(pady=10, padx=10, fill=BOTH, expand=True)

    # Frame para gerenciamento de promoções (segunda aba)
    frame_gerenciar = Frame(tab_gerenciar)
    frame_gerenciar.pack(pady=10, fill=BOTH, expand=True)

    # Combobox para selecionar produto
    Label(frame_gerenciar, text="Selecionar Produto:", font=("Arial", 12)).pack(pady=5)
    combo_produtos = ttk.Combobox(frame_gerenciar, width=40)
    combo_produtos['values'] = consultar_produtos()
    combo_produtos.pack(pady=5)

    # Campo para preço promocional
    Label(frame_gerenciar, text="Preço Promocional:", font=("Arial", 12)).pack(pady=5)
    entry_preco_promo = Entry(frame_gerenciar, width=15)
    entry_preco_promo.pack(pady=5)

    # Botões
    frame_botoes = Frame(frame_gerenciar)
    frame_botoes.pack(pady=10)

    btn_adicionar = Button(frame_botoes, 
                          text="Adicionar à Promoção",
                          command=lambda: adicionar_promocao(combo_produtos.get(), entry_preco_promo.get()),
                          font=("Arial", 12), 
                          bg="#4CAF50", 
                          fg="white")
    btn_adicionar.pack(side=LEFT, padx=5)

    btn_remover = Button(frame_botoes, 
                        text="Remover da Promoção",
                        command=lambda: remover_promocao(combo_produtos.get()),
                        font=("Arial", 12), 
                        bg="#f44336", 
                        fg="white")
    btn_remover.pack(side=LEFT, padx=5)

    # Carregar produtos em promoção
    carregar_produtos_promocao()

def adicionar_promocao(produto_info, preco_promo):
    """Adiciona um produto à lista de promoções"""
    if not produto_info or not preco_promo:
        messagebox.showerror("Erro", "Por favor, preencha todos os campos.")
        return

    try:
        produto_id = produto_info.split(' - ')[0]
        preco_promocional = float(preco_promo)

        if preco_promocional <= 0:
            raise ValueError("O preço promocional deve ser maior que zero")

        conn = create_connection()
        cursor = conn.cursor()

        # Verificar preço atual
        cursor.execute("SELECT preco_venda FROM produtos WHERE id = ?", (produto_id,))
        preco_atual = cursor.fetchone()[0]

        if preco_promocional >= preco_atual:
            messagebox.showerror("Erro", "O preço promocional deve ser menor que o preço normal.")
            return

        # Atualizar produto como em promoção
        cursor.execute("""
            UPDATE produtos 
            SET promocao = 1, preco_promocional = ? 
            WHERE id = ?
        """, (preco_promocional, produto_id))

        conn.commit()
        messagebox.showinfo("Sucesso", "Produto adicionado à promoção!")
        
        # Atualizar a tabela
        carregar_produtos_promocao()

    except ValueError as e:
        messagebox.showerror("Erro", f"Valor inválido: {str(e)}")
    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao adicionar promoção: {str(e)}")
    finally:
        conn.close()

def remover_promocao(produto_info):
    """Remove um produto da lista de promoções"""
    if not produto_info:
        messagebox.showerror("Erro", "Por favor, selecione um produto.")
        return

    try:
        produto_id = produto_info.split(' - ')[0]
        
        conn = create_connection()
        cursor = conn.cursor()

        # Remover produto da promoção
        cursor.execute("""
            UPDATE produtos 
            SET promocao = 0, preco_promocional = NULL 
            WHERE id = ?
        """, (produto_id,))

        conn.commit()
        messagebox.showinfo("Sucesso", "Produto removido da promoção!")
        
        # Atualizar a tabela
        carregar_produtos_promocao()

    except sqlite3.Error as e:
        messagebox.showerror("Erro", f"Erro ao remover promoção: {str(e)}")
    finally:
        conn.close()

def carregar_produtos_promocao():
    """Carrega os produtos em promoção na tabela"""
    for item in tree_promocoes.get_children():
        tree_promocoes.delete(item)

    conn = create_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, tipo, cor, tamanho, preco_venda, preco_promocional
            FROM produtos
            WHERE promocao = 1
            ORDER BY tipo, cor, tamanho
        """)

        for row in cursor.fetchall():
            produto_id, tipo, cor, tamanho, preco_normal, preco_promo = row
            tree_promocoes.insert("", "end", values=(
                produto_id,
                tipo,
                cor,
                tamanho,
                f"R$ {preco_normal:.2f}",
                f"R$ {preco_promo:.2f}"
            ))

    except sqlite3.Error as e:
        print(f"Erro ao carregar produtos em promoção: {e}")
    finally:
        conn.close()

def adicionar_colunas_promocao():
    """Adiciona as colunas necessárias para promoções na tabela produtos"""
    conn = create_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("PRAGMA table_info(produtos)")
        colunas = [info[1] for info in cursor.fetchall()]
        
        if 'promocao' not in colunas:
            cursor.execute("""
                ALTER TABLE produtos
                ADD COLUMN promocao INTEGER DEFAULT 0
            """)
        
        if 'preco_promocional' not in colunas:
            cursor.execute("""
                ALTER TABLE produtos
                ADD COLUMN preco_promocional REAL
            """)
            
        conn.commit()
    except sqlite3.Error:
        pass
    finally:
        conn.close()

adicionar_colunas_promocao()

window = Tk()
window.geometry("1200x740")
window.configure(bg = "#F8EBFF")

FotoBG = PhotoImage(file=r"assets/Background.png")
FotoClientes = PhotoImage(file=r"assets/Clientes.png")
FotoProdutos = PhotoImage(file=r"assets/Produtos.png")
FotoVendas = PhotoImage(file=r"assets/Vendas.png")
FotoRelatorios = PhotoImage(file=r"assets/Relatorios.png")
FotoContasAReceber = PhotoImage(file=r"assets/ContasAReceber.png")
FotoPromocoes = PhotoImage(file=r"assets/Promocoes.png")

canvas = Canvas(window, width=1200, height=740)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=FotoBG, anchor="nw")

BtnClientes = Button(window, text='Clientes', image=FotoClientes, command=abrir_cadastro_clientes)
BtnClientes.place(x=52.0, y=80.0)
BtnProdutos = Button(window, text='Produtos', image=FotoProdutos, command=abrir_cadastro_produtos)
BtnProdutos.place(x=52.0, y=180.0)
BtnVendas = Button(window, text='Vendas', image=FotoVendas, command=abrir_cadastro_vendas)
BtnVendas.place(x=52.0, y=280.0)
BtnContasAReceber = Button(window, text='Contas a Receber', image=FotoContasAReceber, command=abrir_contas_receber)
BtnContasAReceber.place(x=52.0, y=380.0)
BtnPromocoes = Button(window, text='Promoções', image=FotoPromocoes, command=abrir_promocoes)
BtnPromocoes.place(x=52.0, y=480.0)
BtnDashboard = Button(window, text='Dashboard', image=FotoRelatorios, command=abrir_dashboard)
BtnDashboard.place(x=52.0, y=580.0)

window.resizable(False, False)

try:
    import pyi_splash
    pyi_splash.close()
except ImportError:
    pass

window.mainloop()

#TODO - Criar a bag de produtos
#TODO - Autocomplete no nome dos clientes e produtos no cadastro de vendas