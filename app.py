import streamlit as st
import pandas as pd
import os

# Configuração da página e visual
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("💸 Meu Controle Financeiro Oficial")

# Arquivos invisíveis para salvar seus dados (o app cria sozinho na sua pasta)
ARQUIVO_FIXOS = "gastos_fixos.csv"
ARQUIVO_VARIAVEIS = "gastos_variaveis.csv"

# Funções que leem e salvam os dados automaticamente
def carregar_dados(arquivo, colunas):
    if os.path.exists(arquivo):
        return pd.read_csv(arquivo)
    else:
        return pd.DataFrame(columns=colunas)

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

# Carregando a memória do app
df_fixos = carregar_dados(ARQUIVO_FIXOS, ["Descrição", "Valor"])
df_var = carregar_dados(ARQUIVO_VARIAVEIS, ["Descrição", "Valor", "Categoria"])

# ==========================================
# 1. BARRA LATERAL: RECEITAS E METAS
# ==========================================
st.sidebar.header("💰 Entradas e Metas")
salario = st.sidebar.number_input("Salário/Receita Mensal (R$)", min_value=0.0, value=5000.0, step=100.0)
meta_investimento = st.sidebar.number_input("Poupança / Investimento (R$)", min_value=0.0, value=500.0, step=50.0)

# ==========================================
# 2. ÁREA DE LANÇAMENTO DE GASTOS
# ==========================================
col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("📋 Cadastrar Gasto Fixo")
    # O formulário evita que a página recarregue antes da hora
    with st.form("form_fixo", clear_on_submit=True):
        desc_fixo = st.text_input("Descrição (Ex: Internet, Aluguel)")
        valor_fixo = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        submit_fixo = st.form_submit_button("Adicionar Fixo")
        
        if submit_fixo and desc_fixo:
            novo_fixo = pd.DataFrame([{"Descrição": desc_fixo, "Valor": valor_fixo}])
            df_fixos = pd.concat([df_fixos, novo_fixo], ignore_index=True)
            salvar_dados(df_fixos, ARQUIVO_FIXOS)
            st.success("Gasto Fixo registrado!")
            st.rerun()

    # Mostra a tabela atualizada
    st.dataframe(df_fixos, use_container_width=True, hide_index=True)

with col_dir:
    st.subheader("🛒 Cadastrar Gasto Variável")
    with st.form("form_var", clear_on_submit=True):
        desc_var = st.text_input("Descrição (Ex: Almoço, Padaria)")
        valor_var = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
        categoria_var = st.selectbox(
            "Categoria", 
            ["Mercado", "Restaurante", "Gasolina", "Itens de Casa", "Imprevisto", "Farmácia", "Outros"]
        )
        submit_var = st.form_submit_button("Adicionar Variável")
        
        if submit_var and desc_var:
            novo_var = pd.DataFrame([{"Descrição": desc_var, "Valor": valor_var, "Categoria": categoria_var}])
            df_var = pd.concat([df_var, novo_var], ignore_index=True)
            salvar_dados(df_var, ARQUIVO_VARIAVEIS)
            st.success("Gasto Variável registrado!")
            st.rerun()
            
    st.dataframe(df_var, use_container_width=True, hide_index=True)

# ==========================================
# 3. RESUMO E MATEMÁTICA FINANCEIRA
# ==========================================
st.divider()
st.subheader("📊 Resumo do Mês")

# Somando tudo
total_fixos = df_fixos["Valor"].sum() if not df_fixos.empty else 0.0
total_var = df_var["Valor"].sum() if not df_var.empty else 0.0
total_gastos = total_fixos + total_var

# Calculando a métrica principal: Salário - (Gastos + Investimento)
saldo_final = salario - (total_gastos + meta_investimento)

# Desenhando os cartões de resumo
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Gastos Fixos", f"R$ {total_fixos:.2f}")
c2.metric("Total Gastos Variáveis", f"R$ {total_var:.2f}")
c3.metric("Gastos Totais", f"R$ {total_gastos:.2f}")
c4.metric("A Poupar/Investir", f"R$ {meta_investimento:.2f}")

st.divider()

# ==========================================
# 4. RESULTADO FINAL
# ==========================================
if saldo_final > 0:
    st.success(f"✅ **Balanço Positivo!** Após pagar todas as contas e separar o dinheiro dos investimentos, ainda sobraram livres: **R$ {saldo_final:.2f}**")
elif saldo_final < 0:
    st.error(f"⚠️ **Balanço Negativo!** Suas contas e sua meta de investimento ultrapassaram sua receita. Faltaram **R$ {abs(saldo_final):.2f}** para fechar a conta.")
else:
    st.info(f"⚖️ **Empate Técnico!** Seu salário cobriu exatamente os gastos e os investimentos. Não sobrou nada, mas as metas foram atingidas.")