import streamlit as st
import pandas as pd
import os
import plotly.express as px

# Configuração da página e visual
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("💸 Meu Controle Financeiro Oficial")

# Função mágica para formatar a moeda no padrão brasileiro (R$ 1.000,00)
def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# 5 Arquivos invisíveis para salvar seus dados
ARQUIVO_FIXOS = "gastos_fixos.csv"
ARQUIVO_VARIAVEIS = "gastos_variaveis.csv"
ARQUIVO_EXTRAS = "receitas_extras.csv"
ARQUIVO_ECONOMIAS = "economias.csv"
ARQUIVO_METAS = "metas_mensais.csv"

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
df_metas = carregar_dados(ARQUIVO_METAS, ["Mês", "Salario", "Meta"])

# ==========================================
# BARRA LATERAL: MÊS E METAS
# ==========================================
st.sidebar.header("📅 Mês de Referência")
lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", lista_meses, index=6)

# Puxa o salário e a meta específicos do mês selecionado.
metas_do_mes = df_metas[df_metas["Mês"] == mes_selecionado]
salario_salvo = float(metas_do_mes["Salario"].values[0]) if not metas_do_mes.empty else 5000.0
meta_salva = float(metas_do_mes["Meta"].values[0]) if not metas_do_mes.empty else 500.0

st.sidebar.header(f"💰 Entradas de {mes_selecionado}")
with st.sidebar.form("form_metas"):
    salario_base = st.number_input("Salário Mensal (R$)", min_value=0.0, value=salario_salvo, step=100.0)
    meta_investimento = st.number_input("Meta de Poupança (R$)", min_value=0.0, value=meta_salva, step=50.0)
    
    if st.form_submit_button("Salvar Valores do Mês"):
        df_metas = df_metas[df_metas["Mês"] != mes_selecionado]
        nova_meta = pd.DataFrame([{"Mês": mes_selecionado, "Salario": salario_base, "Meta": meta_investimento}])
        df_metas = pd.concat([df_metas, nova_meta], ignore_index=True)
        salvar_dados(df_metas, ARQUIVO_METAS)
        st.rerun()

# Filtrando os dados na memória para mostrar SÓ O MÊS SELECIONADO
df_fixos_mes = df_fixos[df_fixos["Mês"] == mes_selecionado].copy()
df_var_mes = df_var[df_var["Mês"] == mes_selecionado].copy()
df_extras_mes = df_extras[df_extras["Mês"] == mes_selecionado].copy()

# ==========================================
# SISTEMA DE ABAS (TABS) - CAMUFLAGEM ATIVADA
# ==========================================
aba1, aba2, aba3 = st.tabs(["📝 Lançamentos do Mês", "📊 Balanço e Gráficos", "💻 Códigos PYTHON"])

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
                
        edit_fixos = st.data_editor(df_fixos_mes[["Descrição", "Valor"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_fixos")
        if not edit_fixos.reset_index(drop=True).equals(df_fixos_mes[["Descrição", "Valor"]].reset_index(drop=True)):
            edit_fixos["Mês"] = mes_selecionado
            df_fixos = pd.concat([df_fixos[df_fixos["Mês"] != mes_selecionado], edit_fixos], ignore_index=True)
            salvar_dados(df_fixos, ARQUIVO_FIXOS)
            st.rerun()

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
                
        edit_var = st.data_editor(df_var_mes[["Descrição", "Valor", "Categoria"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_var")
        if not edit_var.reset_index(drop=True).equals(df_var_mes[["Descrição", "Valor", "Categoria"]].reset_index(drop=True)):
            edit_var["Mês"] = mes_selecionado
            df_var = pd.concat([df_var[df_var["Mês"] != mes_selecionado], edit_var], ignore_index=True)
            salvar_dados(df_var, ARQUIVO_VARIAVEIS)
            st.rerun()

    with col_dir:
        st.subheader("🤑 Renda Extra")
        with st.form("form_extra", clear_on_submit=True):
            desc_extra = st.text_input("Descrição (Ex: PIX)")
            valor_extra = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Adicionar Extra") and desc_extra:
                novo_extra = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_extra, "Valor": valor_extra}])
                df_extras = pd.concat([df_extras, novo_extra], ignore_index=True)
                salvar_dados(df_extras, ARQUIVO_EXTRAS)
                st.rerun()
                
        edit_extras = st.data_editor(df_extras_mes[["Descrição", "Valor"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_extras")
        if not edit_extras.reset_index(drop=True).equals(df_extras_mes[["Descrição", "Valor"]].reset_index(drop=True)):
            edit_extras["Mês"] = mes_selecionado
            df_extras = pd.concat([df_extras[df_extras["Mês"] != mes_selecionado], edit_extras], ignore_index=True)
            salvar_dados(df_extras, ARQUIVO_EXTRAS)
            st.rerun()

# --- ABA 2: BALANÇO E MATEMÁTICA ---
with aba2:
    st.subheader(f"Resumo Financeiro de {mes_selecionado}")
    
    total_fixos = df_fixos_mes["Valor"].sum() if not df_fixos_mes.empty else 0.0
    total_var = df_var_mes["Valor"].sum() if not df_var_mes.empty else 0.0
    total_gastos = total_fixos + total_var
    
    total_extras = df_extras_mes["Valor"].sum() if not df_extras_mes.empty else 0.0
    receita_total = salario_base + total_extras
    
    saldo_final = receita_total - (total_gastos + meta_investimento)

    # Formatando as caixas métricas com a nossa função do Brasil
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Total", formatar_moeda(receita_total))
    c2.metric("Gastos Totais", formatar_moeda(total_gastos))
    c3.metric("Meta de Investimento", formatar_moeda(meta_investimento))
    c4.metric("Saldo Livre", formatar_moeda(saldo_final))

    st.divider()

    # Formatando os textos de aviso
    if saldo_final > 0:
        st.success(f"✅ **Balanço Positivo!** Após pagar as contas e separar o investimento, sobraram livres: **{formatar_moeda(saldo_final)}**")
    elif saldo_final < 0:
        st.error(f"⚠️ **Balanço Negativo!** Faltaram **{formatar_moeda(abs(saldo_final))}** para cobrir tudo.")
    else:
        st.info(f"⚖️ **Empate Técnico!** Sua receita cobriu exatamente os gastos.")

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
        st.info("Nenhum gasto variável registrado neste mês.")

# --- ABA 3: ESCONDERIJO (CÓDIGOS PYTHON) ---
with aba3:
    st.caption("Ambiente de desenvolvimento e depuração do sistema.")
    
    # O botão mágico que esconde tudo
    with st.expander("Acessar Console de Variáveis"):
        st.header("🏦 Patrimônio Acumulado")
        total_guardado = df_economias["Valor"].sum() if not df_economias.empty else 0.0
        
        # Formatando o número gigante do patrimônio
        st.metric("Total Acumulado (Todos os meses)", formatar_moeda(total_guardado))
        st.divider()
        
        col_eco_esq, col_eco_dir = st.columns(2)
        with col_eco_esq:
            st.subheader("Registrar Nova Entrada")
            with st.form("form_economia", clear_on_submit=True):
                mes_economia = st.selectbox("Mês do depósito", lista_meses, index=lista_meses.index(mes_selecionado))
                desc_economia = st.text_input("Descrição (Ex: Poupança, CDB, Caixinha)")
                valor_economia = st.number_input("Valor Guardado (R$)", min_value=0.0, step=50.0)
                
                if st.form_submit_button("Guardar Dinheiro") and desc_economia:
                    nova_economia = pd.DataFrame([{"Mês": mes_economia, "Descrição": desc_economia, "Valor": valor_economia}])
                    df_economias = pd.concat([df_economias, nova_economia], ignore_index=True)
                    salvar_dados(df_economias, ARQUIVO_ECONOMIAS)
                    st.rerun()
                    
        with col_eco_dir:
            st.subheader("Log de Transações")
            edit_eco = st.data_editor(df_economias, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_eco")
            if not edit_eco.reset_index(drop=True).equals(df_economias.reset_index(drop=True)):
                salvar_dados(edit_eco, ARQUIVO_ECONOMIAS)
                st.rerun()