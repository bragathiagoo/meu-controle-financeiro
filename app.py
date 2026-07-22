import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Configuração da página e visual
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("💸 Meu Controle Financeiro Oficial")

# 4 Arquivos invisíveis para salvar seus dados (o código cria sozinho)
ARQUIVO_FIXOS = "gastos_fixos.csv"
ARQUIVO_VARIAVEIS = "gastos_variaveis.csv"
ARQUIVO_EXTRAS = "receitas_extras.csv"
ARQUIVO_ECONOMIAS = "economias.csv"

# Funções blindadas para ler e salvar os dados
def carregar_dados(arquivo, colunas):
    if os.path.exists(arquivo):
        df = pd.read_csv(arquivo)
        if "Mês" not in df.columns:
            df["Mês"] = "Julho" 
        return df
    else:
        return pd.DataFrame(columns=colunas)

def salvar_dados(df, arquivo):
    df.to_csv(arquivo, index=False)

# Carregando a memória do app
df_fixos = carregar_dados(ARQUIVO_FIXOS, ["Mês", "Descrição", "Valor"])
df_var = carregar_dados(ARQUIVO_VARIAVEIS, ["Mês", "Descrição", "Valor", "Categoria"])
df_extras = carregar_dados(ARQUIVO_EXTRAS, ["Mês", "Descrição", "Valor"])
df_economias = carregar_dados(ARQUIVO_ECONOMIAS, ["Mês", "Descrição", "Valor"])

# ==========================================
# BARRA LATERAL: MÊS E METAS
# ==========================================
st.sidebar.header("📅 Mês de Referência")
lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", lista_meses, index=6)

st.sidebar.header("💰 Entradas Oficiais")
salario_base = st.sidebar.number_input("Salário/Receita Mensal (R$)", min_value=0.0, value=5000.0, step=100.0)
meta_investimento = st.sidebar.number_input("Meta de Poupança do Mês (R$)", min_value=0.0, value=500.0, step=50.0)

# Filtrando os dados na memória para mostrar SÓ O MÊS SELECIONADO
df_fixos_mes = df_fixos[df_fixos["Mês"] == mes_selecionado]
df_var_mes = df_var[df_var["Mês"] == mes_selecionado]
df_extras_mes = df_extras[df_extras["Mês"] == mes_selecionado]

# ==========================================
# SISTEMA DE ABAS (TABS)
# ==========================================
aba1, aba2, aba3 = st.tabs(["📝 Lançamentos do Mês", "📊 Balanço e Gráficos", "🏦 Cofre (Economias)"])

# --- ABA 1: LANÇAMENTOS ---
with aba1:
    st.header(f"Lançamentos de {mes_selecionado}")
    col_esq, col_meio, col_dir = st.columns(3)
    
    with col_esq:
        st.subheader("📋 Gasto Fixo")
        with st.form("form_fixo", clear_on_submit=True):
            desc_fixo = st.text_input("Descrição")
            valor_fixo = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Adicionar Fixo") and desc_fixo:
                novo_fixo = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_fixo, "Valor": valor_fixo}])
                df_fixos = pd.concat([df_fixos, novo_fixo], ignore_index=True)
                salvar_dados(df_fixos, ARQUIVO_FIXOS)
                st.rerun()
        st.dataframe(df_fixos_mes[["Descrição", "Valor"]], use_container_width=True, hide_index=True)

    with col_meio:
        st.subheader("🛒 Gasto Variável")
        with st.form("form_var", clear_on_submit=True):
            desc_var = st.text_input("Descrição")
            valor_var = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            categoria_var = st.selectbox("Categoria", ["Mercado", "Restaurante", "Gasolina", "Itens de Casa", "Imprevisto", "Farmácia", "Outros"])
            if st.form_submit_button("Adicionar Variável") and desc_var:
                novo_var = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_var, "Valor": valor_var, "Categoria": categoria_var}])
                df_var = pd.concat([df_var, novo_var], ignore_index=True)
                salvar_dados(df_var, ARQUIVO_VARIAVEIS)
                st.rerun()
        st.dataframe(df_var_mes[["Descrição", "Valor", "Categoria"]], use_container_width=True, hide_index=True)

    with col_dir:
        st.subheader("🤑 Renda Extra (PIX, Vendas)")
        with st.form("form_extra", clear_on_submit=True):
            desc_extra = st.text_input("Descrição (Ex: PIX, Dívida paga)")
            valor_extra = st.number_input("Valor Recebido (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Adicionar Extra") and desc_extra:
                novo_extra = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_extra, "Valor": valor_extra}])
                df_extras = pd.concat([df_extras, novo_extra], ignore_index=True)
                salvar_dados(df_extras, ARQUIVO_EXTRAS)
                st.rerun()
        st.dataframe(df_extras_mes[["Descrição", "Valor"]], use_container_width=True, hide_index=True)

# --- ABA 2: BALANÇO E MATEMÁTICA ---
with aba2:
    st.subheader(f"Resumo Financeiro de {mes_selecionado}")
    
    total_fixos = df_fixos_mes["Valor"].sum() if not df_fixos_mes.empty else 0.0
    total_var = df_var_mes["Valor"].sum() if not df_var_mes.empty else 0.0
    total_gastos = total_fixos + total_var
    
    # Soma o salário base da lateral com tudo que você recebeu de extra no mês
    total_extras = df_extras_mes["Valor"].sum() if not df_extras_mes.empty else 0.0
    receita_total = salario_base + total_extras
    
    saldo_final = receita_total - (total_gastos + meta_investimento)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Total (Salário + Extras)", f"R$ {receita_total:.2f}")
    c2.metric("Gastos Totais", f"R$ {total_gastos:.2f}")
    c3.metric("Meta de Investimento", f"R$ {meta_investimento:.2f}")
    c4.metric("Saldo Livre", f"R$ {saldo_final:.2f}")

    st.divider()

    if saldo_final > 0:
        st.success(f"✅ **Balanço Positivo!** Após pagar as contas e separar o investimento, sobraram livres: **R$ {saldo_final:.2f}**")
    elif saldo_final < 0:
        st.error(f"⚠️ **Balanço Negativo!** Suas contas e sua meta ultrapassaram suas receitas. Faltaram **R$ {abs(saldo_final):.2f}**.")
    else:
        st.info(f"⚖️ **Empate Técnico!** Sua receita cobriu exatamente os gastos e os investimentos.")

    st.divider()
    st.subheader("🍕 Para onde foi o dinheiro dos Gastos Variáveis?")
    if not df_var_mes.empty:
        gastos_por_categoria = df_var_mes.groupby("Categoria")["Valor"].sum().reset_index()
        col_grafico, col_tabela = st.columns([2, 1]) 
        with col_grafico:
            fig = px.pie(gastos_por_categoria, values="Valor", names="Categoria", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with col_tabela:
            st.dataframe(gastos_por_categoria, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum gasto variável registrado neste mês ainda para gerar o gráfico.")

# --- ABA 3: COFRE E ECONOMIAS ---
with aba3:
    st.header("🏦 Patrimônio Acumulado")
    
    # Diferente dos gastos, o cofre soma TODOS os meses da história para mostrar o total guardado
    total_guardado = df_economias["Valor"].sum() if not df_economias.empty else 0.0
    
    st.metric("Total Acumulado (Todos os meses)", f"R$ {total_guardado:.2f}")
    st.divider()
    
    col_eco_esq, col_eco_dir = st.columns(2)
    with col_eco_esq:
        st.subheader("Adicionar nova economia")
        with st.form("form_economia", clear_on_submit=True):
            # Permite escolher o mês retroativo se você esqueceu de lançar
            mes_economia = st.selectbox("Mês do depósito", lista_meses, index=lista_meses.index(mes_selecionado))
            desc_economia = st.text_input("Descrição (Ex: Poupança, CDB, Caixinha)")
            valor_economia = st.number_input("Valor Guardado (R$)", min_value=0.0, step=50.0)
            
            if st.form_submit_button("Guardar Dinheiro") and desc_economia:
                nova_economia = pd.DataFrame([{"Mês": mes_economia, "Descrição": desc_economia, "Valor": valor_economia}])
                df_economias = pd.concat([df_economias, nova_economia], ignore_index=True)
                salvar_dados(df_economias, ARQUIVO_ECONOMIAS)
                st.success("Dinheiro guardado no cofre!")
                st.rerun()
                
    with col_eco_dir:
        st.subheader("Histórico de Depósitos")
        st.dataframe(df_economias, use_container_width=True, hide_index=True)