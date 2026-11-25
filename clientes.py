from datetime import datetime
import os
import re
import sqlite3
import tkinter as tk
from tkinter import messagebox

# 1. Configura o caminho exato na mesma pasta do script
pasta_atual = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(pasta_atual, "clientes.db")

UFS_VALIDAS = {
    "AC",
    "AL",
    "AP",
    "AM",
    "BA",
    "CE",
    "DF",
    "ES",
    "GO",
    "MA",
    "MT",
    "MS",
    "MG",
    "PA",
    "PB",
    "PR",
    "PE",
    "PI",
    "RJ",
    "RN",
    "RS",
    "RO",
    "RR",
    "SC",
    "SP",
    "SE",
    "TO",
}


# 2. Inicializa o banco de dados
def inicializar_banco():
  conn = sqlite3.connect(caminho_banco)
  cursor = conn.cursor()
  cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL,
        telefone TEXT,
        cpf TEXT,
        endereco TEXT,
        cidade TEXT,
        estado TEXT,
        cep TEXT,
        data_nascimento TEXT,
        data_cadastro TEXT DEFAULT (strftime('%d/%m/%Y %H:%M:%S', 'now', 'localtime')),
        observacoes TEXT
    );
    """)
  conn.commit()
  conn.close()


# --- Funções de Validação e Formatação ---
def validar_cpf_matematico(cpf_numeros):
  if len(cpf_numeros) != 11 or cpf_numeros == cpf_numeros[0] * 11:
    return False
  for i in range(9, 11):
    soma = sum(int(cpf_numeros[num]) * ((i + 1) - num) for num in range(0, i))
    digito = ((soma * 10) % 11) % 10
    if digito != int(cpf_numeros[i]):
      return False
  return True


def apenas_numeros(texto):
  return texto.isdigit() or texto == ""


def controlar_tamanho_e_foco(entry_atual, max_len, proximo_widget=None):
  def callback(event):
    texto = entry_atual.get()
    # Remove qualquer caractere que não seja número caso cole texto
    limpo = "".join(filter(str.isdigit, texto))
    if len(limpo) > max_len:
      limpo = limpo[:max_len]
    if texto != limpo:
      entry_atual.delete(0, tk.END)
      entry_atual.insert(0, limpo)
    # Pula para o próximo campo automaticamente ao completar
    if (
        len(limpo) == max_len
        and proximo_widget
        and event.keysym not in ("BackSpace", "Delete", "Left", "Right")
    ):
      proximo_widget.focus()

  return callback


def formatar_cep(event):
  limpo = "".join(filter(str.isdigit, ent_cep.get()))[:8]
  if len(limpo) > 5:
    formatado = f"{limpo[:5]}-{limpo[5:]}"
  else:
    formatado = limpo
  ent_cep.delete(0, tk.END)
  ent_cep.insert(0, formatado)


def formatar_data(event):
  limpo = "".join(filter(str.isdigit, ent_data.get()))[:8]
  if len(limpo) > 4:
    formatado = f"{limpo[:2]}/{limpo[2:4]}/{limpo[4:]}"
  elif len(limpo) > 2:
    formatado = f"{limpo[:2]}/{limpo[2:]}"
  else:
    formatado = limpo
  ent_data.delete(0, tk.END)
  ent_data.insert(0, formatado)


def formatar_telefone_numero(event):
  limpo = "".join(filter(str.isdigit, ent_tel_num.get()))[:9]
  if len(limpo) == 9:
    formatado = f"{limpo[:5]}-{limpo[5:]}"
  elif len(limpo) > 4:
    formatado = f"{limpo[:4]}-{limpo[4:]}"
  else:
    formatado = limpo
  ent_tel_num.delete(0, tk.END)
  ent_tel_num.insert(0, formatado)


# 3. Validação completa e envio para o banco
def salvar_cliente():
  nome = ent_nome.get().strip()
  email = ent_email.get().strip()
  ddd = ent_ddd.get().strip()
  tel_num_limpo = "".join(filter(str.isdigit, ent_tel_num.get()))
  cpf_p1 = ent_cpf1.get().strip()
  cpf_p2 = ent_cpf2.get().strip()
  cpf_p3 = ent_cpf3.get().strip()
  cpf_dig = ent_cpf4.get().strip()
  endereco = ent_endereco.get().strip()
  cidade = ent_cidade.get().strip()
  estado = ent_estado.get().strip().upper()
  cep = ent_cep.get().strip()
  data_nasc = ent_data.get().strip()
  observacoes = txt_observacoes.get("1.0", tk.END).strip()

  # Validação Nome
  if len(nome) < 3 or any(char.isdigit() for char in nome):
    messagebox.showerror(
        "Erro no Nome",
        "Digite um nome válido (mínimo 3 letras e sem números).",
    )
    ent_nome.focus()
    return

  # Validação E-mail
  if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w{2,}$", email):
    messagebox.showerror(
        "Erro no E-mail",
        "Digite um e-mail válido (exemplo: cliente@email.com).",
    )
    ent_email.focus()
    return

  # Validação Telefone (DDD + Número em ordem)
  telefone_formatado = ""
  if ddd or tel_num_limpo:
    if len(ddd) != 2 or ddd.startswith("0"):
      messagebox.showerror(
          "Erro no DDD", "O DDD deve ter 2 dígitos válidos (ex: 11, 41)."
      )
      ent_ddd.focus()
      return
    if len(tel_num_limpo) not in (8, 9):
      messagebox.showerror(
          "Erro no Telefone", "O número de telefone deve ter 8 ou 9 dígitos."
      )
      ent_tel_num.focus()
      return
    if len(tel_num_limpo) == 9:
      num_ordenado = f"{tel_num_limpo[:5]}-{tel_num_limpo[5:]}"
    else:
      num_ordenado = f"{tel_num_limpo[:4]}-{tel_num_limpo[4:]}"
    telefone_formatado = f"({ddd}) {num_ordenado}"

  # Validação CPF separado
  cpf_completo_numeros = cpf_p1 + cpf_p2 + cpf_p3 + cpf_dig
  cpf_formatado = ""
  if cpf_completo_numeros:
    if len(cpf_completo_numeros) != 11 or not validar_cpf_matematico(
        cpf_completo_numeros
    ):
      messagebox.showerror(
          "Erro no CPF", "CPF inválido! Verifique os 11 dígitos informados."
      )
      ent_cpf1.focus()
      return
    cpf_formatado = f"{cpf_p1}.{cpf_p2}.{cpf_p3}-{cpf_dig}"

  # Validação Estado (UF)
  if estado and estado not in UFS_VALIDAS:
    messagebox.showerror(
        "Erro no Estado",
        f"'{estado}' não é uma sigla de estado válida (ex: PR, SP, RJ).",
    )
    ent_estado.focus()
    return

  # Validação CEP
  if cep and len(cep) != 9:
    messagebox.showerror(
        "Erro no CEP", "O CEP deve conter 8 números (formato: 00000-000)."
    )
    ent_cep.focus()
    return

  # Validação Data de Nascimento
  if data_nasc:
    try:
      data_obj = datetime.strptime(data_nasc, "%d/%m/%Y")
      if data_obj > datetime.now() or data_obj.year < 1900:
        raise ValueError
    except ValueError:
      messagebox.showerror(
          "Erro na Data",
          "Data de nascimento inválida! Use o formato DD/MM/AAAA.",
      )
      ent_data.focus()
      return

  # Salva no SQLite
  try:
    conn = sqlite3.connect(caminho_banco)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO clientes (nome, email, telefone, cpf, endereco, cidade, estado, cep, data_nascimento, observacoes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            nome,
            email,
            telefone_formatado,
            cpf_formatado,
            endereco,
            cidade,
            estado,
            cep,
            data_nasc,
            observacoes,
        ),
    )
    conn.commit()
    conn.close()

    messagebox.showinfo("Sucesso", f"Cliente '{nome}' cadastrado com sucesso!")
    limpar_campos()

  except Exception as e:
    messagebox.showerror(
        "Erro no Banco de Dados", f"Não foi possível salvar:\n{e}"
    )


def limpar_campos():
  for widget in [
      ent_nome,
      ent_email,
      ent_ddd,
      ent_tel_num,
      ent_cpf1,
      ent_cpf2,
      ent_cpf3,
      ent_cpf4,
      ent_endereco,
      ent_cidade,
      ent_estado,
      ent_cep,
      ent_data,
  ]:
    widget.delete(0, tk.END)
  txt_observacoes.delete("1.0", tk.END)
  ent_nome.focus()


# --- Interface Gráfica ---
inicializar_banco()

janela = tk.Tk()
janela.title("Cadastro de Clientes - SQLite")
janela.geometry("490x600")
janela.configure(padx=20, pady=15)

vcmd_num = (janela.register(apenas_numeros), "%P")

tk.Label(
    janela, text="Novo Cadastro de Cliente", font=("Arial", 14, "bold")
).pack(pady=(0, 15))

frame_campos = tk.Frame(janela)
frame_campos.pack(fill=tk.X)

# Linha 0: Nome
tk.Label(frame_campos, text="Nome *", font=("Arial", 9, "bold")).grid(
    row=0, column=0, sticky="w", pady=5
)
ent_nome = tk.Entry(frame_campos, width=40, font=("Arial", 10))
ent_nome.grid(row=0, column=1, sticky="w", pady=5, padx=(10, 0))

# Linha 1: E-mail
tk.Label(frame_campos, text="E-mail *", font=("Arial", 9, "bold")).grid(
    row=1, column=0, sticky="w", pady=5
)
ent_email = tk.Entry(frame_campos, width=40, font=("Arial", 10))
ent_email.grid(row=1, column=1, sticky="w", pady=5, padx=(10, 0))

# Linha 2: Telefone (DDD separado + Número)
tk.Label(frame_campos, text="Telefone (DDD)", font=("Arial", 9, "bold")).grid(
    row=2, column=0, sticky="w", pady=5
)
frame_tel = tk.Frame(frame_campos)
frame_tel.grid(row=2, column=1, sticky="w", pady=5, padx=(10, 0))

tk.Label(frame_tel, text="(", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
ent_ddd = tk.Entry(
    frame_tel,
    width=3,
    font=("Arial", 10),
    justify="center",
    validate="key",
    validatecommand=vcmd_num,
)
ent_ddd.pack(side=tk.LEFT)
tk.Label(frame_tel, text=") ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

ent_tel_num = tk.Entry(frame_tel, width=15, font=("Arial", 10))
ent_tel_num.pack(side=tk.LEFT)
tk.Label(
    frame_tel, text="  Ex: (41) 98765-4321", fg="gray", font=("Arial", 8)
).pack(side=tk.LEFT)

ent_ddd.bind("<KeyRelease>", controlar_tamanho_e_foco(ent_ddd, 2, ent_tel_num))
ent_tel_num.bind("<KeyRelease>", formatar_telefone_numero)

# Linha 3: CPF Separado (000 . 000 . 000 - 00)
tk.Label(frame_campos, text="CPF", font=("Arial", 9, "bold")).grid(
    row=3, column=0, sticky="w", pady=5
)
frame_cpf = tk.Frame(frame_campos)
frame_cpf.grid(row=3, column=1, sticky="w", pady=5, padx=(10, 0))

ent_cpf1 = tk.Entry(
    frame_cpf,
    width=4,
    font=("Arial", 10),
    justify="center",
    validate="key",
    validatecommand=vcmd_num,
)
ent_cpf2 = tk.Entry(
    frame_cpf,
    width=4,
    font=("Arial", 10),
    justify="center",
    validate="key",
    validatecommand=vcmd_num,
)
ent_cpf3 = tk.Entry(
    frame_cpf,
    width=4,
    font=("Arial", 10),
    justify="center",
    validate="key",
    validatecommand=vcmd_num,
)
ent_cpf4 = tk.Entry(
    frame_cpf,
    width=3,
    font=("Arial", 10),
    justify="center",
    validate="key",
    validatecommand=vcmd_num,
)

ent_cpf1.pack(side=tk.LEFT)
tk.Label(frame_cpf, text=" . ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
ent_cpf2.pack(side=tk.LEFT)
tk.Label(frame_cpf, text=" . ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
ent_cpf3.pack(side=tk.LEFT)
tk.Label(frame_cpf, text=" - ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
ent_cpf4.pack(side=tk.LEFT)

ent_cpf1.bind("<KeyRelease>", controlar_tamanho_e_foco(ent_cpf1, 3, ent_cpf2))
ent_cpf2.bind("<KeyRelease>", controlar_tamanho_e_foco(ent_cpf2, 3, ent_cpf3))
ent_cpf3.bind("<KeyRelease>", controlar_tamanho_e_foco(ent_cpf3, 3, ent_cpf4))
ent_cpf4.bind("<KeyRelease>", controlar_tamanho_e_foco(ent_cpf4, 2, None))

# Linha 4: Endereço
tk.Label(frame_campos, text="Endereço", font=("Arial", 9, "bold")).grid(
    row=4, column=0, sticky="w", pady=5
)
ent_endereco = tk.Entry(frame_campos, width=40, font=("Arial", 10))
ent_endereco.grid(row=4, column=1, sticky="w", pady=5, padx=(10, 0))

# Linha 5: Cidade
tk.Label(frame_campos, text="Cidade", font=("Arial", 9, "bold")).grid(
    row=5, column=0, sticky="w", pady=5
)
ent_cidade = tk.Entry(frame_campos, width=40, font=("Arial", 10))
ent_cidade.grid(row=5, column=1, sticky="w", pady=5, padx=(10, 0))

# Linha 6: Estado (UF)
tk.Label(frame_campos, text="Estado (UF)", font=("Arial", 9, "bold")).grid(
    row=6, column=0, sticky="w", pady=5
)
ent_estado = tk.Entry(frame_campos, width=6, font=("Arial", 10))
ent_estado.grid(row=6, column=1, sticky="w", pady=5, padx=(10, 0))

# Linha 7: CEP
tk.Label(frame_campos, text="CEP", font=("Arial", 9, "bold")).grid(
    row=7, column=0, sticky="w", pady=5
)
ent_cep = tk.Entry(frame_campos, width=15, font=("Arial", 10))
ent_cep.grid(row=7, column=1, sticky="w", pady=5, padx=(10, 0))
ent_cep.bind("<KeyRelease>", formatar_cep)

# Linha 8: Data de Nascimento
tk.Label(
    frame_campos, text="Data de Nascimento", font=("Arial", 9, "bold")
).grid(row=8, column=0, sticky="w", pady=5)
ent_data = tk.Entry(frame_campos, width=15, font=("Arial", 10))
ent_data.grid(row=8, column=1, sticky="w", pady=5, padx=(10, 0))
ent_data.bind("<KeyRelease>", formatar_data)

# Linha 9: Observações
tk.Label(frame_campos, text="Observações", font=("Arial", 9, "bold")).grid(
    row=9, column=0, sticky="nw", pady=5
)
txt_observacoes = tk.Text(
    frame_campos, width=30, height=4, font=("Arial", 10)
)
txt_observacoes.grid(row=9, column=1, sticky="w", pady=5, padx=(10, 0))

# Botões
frame_botoes = tk.Frame(janela)
frame_botoes.pack(pady=20)

btn_salvar = tk.Button(
    frame_botoes,
    text="💾 Salvar no Banco",
    bg="#28a745",
    fg="white",
    font=("Arial", 10, "bold"),
    padx=15,
    pady=6,
    command=salvar_cliente,
)
btn_salvar.pack(side=tk.LEFT, padx=10)

btn_limpar = tk.Button(
    frame_botoes,
    text="Limpar",
    font=("Arial", 10),
    padx=15,
    pady=6,
    command=limpar_campos,
)
btn_limpar.pack(side=tk.LEFT, padx=10)

janela.mainloop()