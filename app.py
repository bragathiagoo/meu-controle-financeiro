
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import gspread
from google.oauth2.service_account import Credentials

# Configuração da página e visual
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("💸 Meu Controle Financeiro Oficial")

# Função mágica para formatar a moeda no padrão brasileiro (R$ 1.000,00)
def formatar_moeda(valor):
    try:
        valor_float = float(valor)
        return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ==========================================
# CONEXÃO COM O GOOGLE DRIVE
# ==========================================
# O @st.cache_resource faz o aplicativo logar no Google uma vez só, deixando tudo muito mais rápido
@st.cache_resource
def conectar_google():
    # Puxa o segredo do cofre do Streamlit
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    cliente = gspread.authorize(creds)
    # Abre a planilha pelo nome exato que você criou
    planilha = cliente.open("Banco de Dados App Financeiro")
    return planilha

planilha = conectar_google()

# Nomes exatos das abas que você criou lá no Google
ABA_FIXOS = "gastos_fixos"
ABA_VARIAVEIS = "gastos_variaveis"
ABA_EXTRAS = "receitas_extras"
ABA_ECONOMIAS = "economias"
ABA_METAS = "metas_mensais"

# Funções blindadas para ler e salvar no Google Sheets
def carregar_dados(nome_aba, colunas):
    aba = planilha.worksheet(nome_aba)
    dados = aba.get_all_records()
    df = pd.DataFrame(dados)
    if df.empty:
        return pd.DataFrame(columns=colunas)
    
    # Força os valores numéricos a serem reconhecidos para não quebrar a matemática
    for col in ["Valor", "Salario", "Meta"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df

def salvar_dados(df, nome_aba):
    aba = planilha.worksheet(nome_aba)
    aba.clear() # Limpa a gaveta
    # Prepara os dados retirando erros matemáticos e envia
    df_clean = df.fillna("")
    dados_lista = [df_clean.columns.values.tolist()] + df_clean.values.tolist()
    aba.update(dados_lista) # Guarda os dados novos

# ==========================================
# CARREGANDO A MEMÓRIA DO APP (DIRETO DA NUVEM)
# ==========================================
df_fixos = carregar_dados(ABA_FIXOS, ["Mês", "Descrição", "Valor"])
df_var = carregar_dados(ABA_VARIAVEIS, ["Mês", "Descrição", "Valor", "Categoria"])
df_extras = carregar_dados(ABA_EXTRAS, ["Mês", "Descrição", "Valor"])
df_economias = carregar_dados(ABA_ECONOMIAS, ["Mês", "Descrição", "Valor"])
df_metas = carregar_dados(ABA_METAS, ["Mês", "Salario", "Meta"])

# ==========================================
# BARRA LATERAL: MÊS E METAS
# ==========================================
st.sidebar.header("📅 Mês de Referência")
lista_meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
mes_selecionado = st.sidebar.selectbox("Selecione o Mês", lista_meses, index=6)

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
        salvar_dados(df_metas, ABA_METAS)
        st.success("Salvo na nuvem!")
        st.rerun()

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
                novo_fixo = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_fixo, "Valor": float(valor_fixo)}])
                df_fixos = pd.concat([df_fixos, novo_fixo], ignore_index=True)
                salvar_dados(df_fixos, ABA_FIXOS)
                st.rerun()
                
        edit_fixos = st.data_editor(df_fixos_mes[["Descrição", "Valor"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_fixos")
        
        total_fixos_aba1 = df_fixos_mes["Valor"].sum() if not df_fixos_mes.empty else 0.0
        st.info(f"Total Fixo: **{formatar_moeda(total_fixos_aba1)}**")
        
        if not edit_fixos.reset_index(drop=True).equals(df_fixos_mes[["Descrição", "Valor"]].reset_index(drop=True)):
            edit_fixos["Mês"] = mes_selecionado
            df_fixos = pd.concat([df_fixos[df_fixos["Mês"] != mes_selecionado], edit_fixos], ignore_index=True)
            salvar_dados(df_fixos, ABA_FIXOS)
            st.rerun()

    with col_meio:
        st.subheader("🛒 Gasto Variável")
        with st.form("form_var", clear_on_submit=True):
            desc_var = st.text_input("Descrição")
            valor_var = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            categoria_var = st.selectbox("Categoria", ["Mercado", "Restaurante", "Gasolina", "Itens de Casa", "Imprevisto", "Farmácia", "Outros"])
            if st.form_submit_button("Adicionar Variável") and desc_var:
                novo_var = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_var, "Valor": float(valor_var), "Categoria": categoria_var}])
                df_var = pd.concat([df_var, novo_var], ignore_index=True)
                salvar_dados(df_var, ABA_VARIAVEIS)
                st.rerun()
                
        edit_var = st.data_editor(df_var_mes[["Descrição", "Valor", "Categoria"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_var")
        
        total_var_aba1 = df_var_mes["Valor"].sum() if not df_var_mes.empty else 0.0
        st.info(f"Total Variável: **{formatar_moeda(total_var_aba1)}**")
        
        if not edit_var.reset_index(drop=True).equals(df_var_mes[["Descrição", "Valor", "Categoria"]].reset_index(drop=True)):
            edit_var["Mês"] = mes_selecionado
            df_var = pd.concat([df_var[df_var["Mês"] != mes_selecionado], edit_var], ignore_index=True)
            salvar_dados(df_var, ABA_VARIAVEIS)
            st.rerun()

    with col_dir:
        st.subheader("🤑 Renda Extra")
        with st.form("form_extra", clear_on_submit=True):
            desc_extra = st.text_input("Descrição (Ex: PIX)")
            valor_extra = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Adicionar Extra") and desc_extra:
                novo_extra = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_extra, "Valor": float(valor_extra)}])
                df_extras = pd.concat([df_extras, novo_extra], ignore_index=True)
                salvar_dados(df_extras, ABA_EXTRAS)
                st.rerun()
                
        edit_extras = st.data_editor(df_extras_mes[["Descrição", "Valor"]], num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_extras")
        
        total_extras_aba1 = df_extras_mes["Valor"].sum() if not df_extras_mes.empty else 0.0
        st.info(f"Total Extra: **{formatar_moeda(total_extras_aba1)}**")
        
        if not edit_extras.reset_index(drop=True).equals(df_extras_mes[["Descrição", "Valor"]].reset_index(drop=True)):
            edit_extras["Mês"] = mes_selecionado
            df_extras = pd.concat([df_extras[df_extras["Mês"] != mes_selecionado], edit_extras], ignore_index=True)
            salvar_dados(df_extras, ABA_EXTRAS)
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

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Receita Total", formatar_moeda(receita_total))
    c2.metric("Gastos Totais", formatar_moeda(total_gastos))
    c3.metric("Meta de Investimento", formatar_moeda(meta_investimento))
    c4.metric("Saldo Livre", formatar_moeda(saldo_final))

    st.divider()

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
    
    with st.expander("Acessar Console de Variáveis"):
        st.header("🏦 Patrimônio Acumulado")
        total_guardado = df_economias["Valor"].sum() if not df_economias.empty else 0.0
        
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
                    nova_economia = pd.DataFrame([{"Mês": mes_economia, "Descrição": desc_economia, "Valor": float(valor_economia)}])
                    df_economias = pd.concat([df_economias, nova_economia], ignore_index=True)
                    salvar_dados(df_economias, ABA_ECONOMIAS)
                    st.rerun()
                    
        with col_eco_dir:
            st.subheader("Log de Transações")
            edit_eco = st.data_editor(df_economias, num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_eco")
            if not edit_eco.reset_index(drop=True).equals(df_economias.reset_index(drop=True)):
                salvar_dados(edit_eco, ABA_ECONOMIAS)
                st.rerun()
