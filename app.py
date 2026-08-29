import streamlit as st
import pandas as pd
import plotly.express as px
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Configuração da página e visual
st.set_page_config(page_title="Controle Financeiro", layout="wide")
st.title("💸 Meu Controle Financeiro Oficial")

# Função mágica para formatar a moeda
def formatar_moeda(valor):
    try:
        valor_float = float(valor)
        return f"R$ {valor_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# O TRADUTOR BLINDADO
def limpar_valor(valor_str):
    try:
        v = str(valor_str).strip()
        if v == "": return 0.0
        if "," in v and "." in v:
            if v.rfind(",") > v.rfind("."):
                v = v.replace(".", "").replace(",", ".")
            else:
                v = v.replace(",", "")
        elif "," in v:
            v = v.replace(",", ".")
        return float(v)
    except:
        return 0.0

# ==========================================
# CONEXÃO COM O GOOGLE DRIVE
@st.cache_resource
def conectar_google():
    cred_dict = json.loads(st.secrets["google_credentials"])
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(cred_dict, scopes=scopes)
    cliente = gspread.authorize(creds)
    planilha = cliente.open_by_url("https://docs.google.com/spreadsheets/d/16A0r6INv0qiW-aVz7gf3oniz4J_ZmjH_7I3lKz4UthI/edit?gid=0#gid=0")
    return planilha

planilha = conectar_google()

ABA_FIXOS = "gastos_fixos"
ABA_VARIAVEIS = "gastos_variaveis"
ABA_EXTRAS = "receitas_extras"
ABA_ECONOMIAS = "economias"
ABA_METAS = "metas_mensais"

def carregar_dados(nome_aba, colunas):
    try:
        aba = planilha.worksheet(nome_aba)
        dados = aba.get_all_records(value_render_option="UNFORMATTED_VALUE")
        df = pd.DataFrame(dados)
        if df.empty:
            return pd.DataFrame(columns=colunas)
        for col in ["Valor", "Salario", "Meta"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
        return df
    except Exception as e:
        st.error(f"🚨 ERRO CONFESSADO NA ABA '{nome_aba}': {e}")
        st.stop()
    return df

def salvar_dados(df, nome_aba):
    aba = planilha.worksheet(nome_aba)
    aba.clear()
    df_salvar = df.copy()
    for col in ["Valor", "Salario", "Meta"]:
        if col in df_salvar.columns:
            df_salvar[col] = pd.to_numeric(df_salvar[col], errors="coerce").fillna(0.0)
    df_clean = df_salvar.fillna("")
    
    dados_lista = [df_clean.columns.tolist()]
    for row in df_clean.itertuples(index=False):
        linha = []
        for col, val in zip(df_clean.columns, row):
            if col in ["Valor", "Salario", "Meta"]:
                try:
                    linha.append(float(val))
                except:
                    linha.append(0.0)
            else:
                linha.append(str(val))
        dados_lista.append(linha)
    aba.update(dados_lista, value_input_option="RAW")

# ==========================================
# CARREGANDO A MEMÓRIA DO APP
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
hoje = datetime.now()
indice_mes = hoje.month - 1 

if hoje.day >= 20:
    indice_mes += 1
if indice_mes > 11:
    indice_mes = 0

mes_selecionado = st.sidebar.selectbox("Selecione o Mês", lista_meses, index=indice_mes)

metas_do_mes = df_metas[df_metas["Mês"] == mes_selecionado]
salario_salvo = float(metas_do_mes["Salario"].values[0]) if not metas_do_mes.empty else 5000.0
meta_salva = float(metas_do_mes["Meta"].values[0]) if not metas_do_mes.empty else 500.0

st.sidebar.header(f"💰 Entradas de {mes_selecionado}")
with st.sidebar.form("form_metas"):
    salario_base_str = st.text_input("Salário Mensal (R$)", value=f"{salario_salvo:.2f}")
    meta_investimento_str = st.text_input("Meta de Poupança (R$)", value=f"{meta_salva:.2f}")
    submit_metas = st.form_submit_button("Salvar Valores do Mês")

salario_base = limpar_valor(salario_base_str)
meta_investimento = limpar_valor(meta_investimento_str)

if submit_metas:
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
# SISTEMA DE ABAS (TABS)
# ==========================================
aba1, aba2, aba3 = st.tabs(["📝 Lançamentos do Mês", "📊 Balanço e Gráficos", "🏦 Patrimônio"])

# --- ABA 1: LANÇAMENTOS ---
with aba1:
    st.header(f"Lançamentos de {mes_selecionado}")
    col_esq, col_meio, col_dir = st.columns(3)
    
    with col_esq:
        st.subheader("📋 Gasto Fixo")
        with st.form("form_fixo", clear_on_submit=True):
            desc_fixo = st.text_input("Descrição")
            valor_fixo_str = st.text_input("Valor (R$)", placeholder="Ex: 1,20 ou 1.20")
            if st.form_submit_button("Adicionar Fixo") and desc_fixo:
                v_fixo = limpar_valor(valor_fixo_str)
                novo_fixo = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_fixo, "Valor": v_fixo}])
                df_fixos = pd.concat([df_fixos, novo_fixo], ignore_index=True)
                salvar_dados(df_fixos, ABA_FIXOS)
                st.rerun()
                
        edit_fixos = st.data_editor(
            df_fixos_mes[["Descrição", "Valor"]], 
            num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_fixos",
            column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", step=0.01)}
        )
        
        if not edit_fixos.reset_index(drop=True).equals(df_fixos_mes[["Descrição", "Valor"]].reset_index(drop=True)):
            edit_fixos["Mês"] = mes_selecionado
            df_fixos = pd.concat([df_fixos[df_fixos["Mês"] != mes_selecionado], edit_fixos], ignore_index=True)
            salvar_dados(df_fixos, ABA_FIXOS)
            st.rerun()

    with col_meio:
        st.subheader("🛒 Gasto Variável")
        with st.form("form_var", clear_on_submit=True):
            desc_var = st.text_input("Descrição")
            valor_var_str = st.text_input("Valor (R$)", placeholder="Ex: 1,20 ou 1.20")
            categoria_var = st.selectbox("Categoria", ["Mercado", "Restaurante", "Gasolina", "Itens de Casa", "Imprevisto", "Farmácia", "Outros"])
            
            if st.form_submit_button("Adicionar Variável") and desc_var:
                v_var = limpar_valor(valor_var_str)
                novo_var = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_var, "Valor": v_var, "Categoria": categoria_var}])
                df_var = pd.concat([df_var, novo_var], ignore_index=True)
                salvar_dados(df_var, ABA_VARIAVEIS)
                st.rerun()
                
        edit_var = st.data_editor(
            df_var_mes[["Descrição", "Valor", "Categoria"]], 
            num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_var",
            column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", step=0.01)}
        )
        
        if not edit_var.reset_index(drop=True).equals(df_var_mes[["Descrição", "Valor", "Categoria"]].reset_index(drop=True)):
            edit_var["Mês"] = mes_selecionado
            df_var = pd.concat([df_var[df_var["Mês"] != mes_selecionado], edit_var], ignore_index=True)
            salvar_dados(df_var, ABA_VARIAVEIS)
            st.rerun()

    with col_dir:
        st.subheader("🤑 Renda Extra")
        with st.form("form_extra", clear_on_submit=True):
            desc_extra = st.text_input("Descrição (Ex: PIX)")
            valor_extra_str = st.text_input("Valor (R$)", placeholder="Ex: 1,20 ou 1.20")
            if st.form_submit_button("Adicionar Extra") and desc_extra:
                v_extra = limpar_valor(valor_extra_str)
                novo_extra = pd.DataFrame([{"Mês": mes_selecionado, "Descrição": desc_extra, "Valor": v_extra}])
                df_extras = pd.concat([df_extras, novo_extra], ignore_index=True)
                salvar_dados(df_extras, ABA_EXTRAS)
                st.rerun()
                
        edit_extras = st.data_editor(
            df_extras_mes[["Descrição", "Valor"]], 
            num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_extras",
            column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", step=0.01)}
        )
        
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
    
    # --- O NOVO PAINEL DE COMANDO (3 GRÁFICOS) ---
    st.subheader("📊 Raio-X das Despesas")
    
    col_graf1, col_graf2, col_graf3 = st.columns(3)
    
    with col_graf1:
        st.markdown("**1. Total: Fixo vs Variável**")
        if total_gastos > 0:
            df_macro = pd.DataFrame({"Tipo": ["Fixo", "Variável"], "Valor": [total_fixos, total_var]})
            fig_macro = px.pie(df_macro, values="Valor", names="Tipo", hole=0.4, color_discrete_sequence=["#FF7F0E", "#1F77B4"])
            fig_macro.update_traces(textposition='inside', textinfo='percent+label')
            fig_macro.update_layout(showlegend=False) 
            st.plotly_chart(fig_macro, use_container_width=True)
        else:
            st.info("Nenhuma despesa registrada.")

    with col_graf2:
        st.markdown("**2. Raio-X: Gastos Fixos**")
        if not df_fixos_mes.empty and total_fixos > 0:
            gastos_fixos_agrupados = df_fixos_mes.groupby("Descrição")["Valor"].sum().reset_index()
            fig_fixos = px.pie(gastos_fixos_agrupados, values="Valor", names="Descrição", hole=0.4)
            fig_fixos.update_traces(textposition='inside', textinfo='percent+label')
            fig_fixos.update_layout(showlegend=False)
            st.plotly_chart(fig_fixos, use_container_width=True)
        else:
            st.info("Nenhum gasto fixo para detalhar.")

    with col_graf3:
        st.markdown("**3. Raio-X: Gastos Variáveis**")
        if not df_var_mes.empty and total_var > 0:
            gastos_var_agrupados = df_var_mes.groupby("Categoria")["Valor"].sum().reset_index()
            fig_var = px.pie(gastos_var_agrupados, values="Valor", names="Categoria", hole=0.4)
            fig_var.update_traces(textposition='inside', textinfo='percent+label')
            fig_var.update_layout(showlegend=False)
            st.plotly_chart(fig_var, use_container_width=True)
        else:
            st.info("Nenhum gasto variável para detalhar.")
            
    with st.expander("Ver tabelas detalhadas (Valores em Reais)"):
        col_tab1, col_tab2 = st.columns(2)
        with col_tab1:
            if not df_fixos_mes.empty and total_fixos > 0:
                st.markdown("**Gastos Fixos**")
                st.dataframe(gastos_fixos_agrupados, use_container_width=True, hide_index=True)
        with col_tab2:
            if not df_var_mes.empty and total_var > 0:
                st.markdown("**Gastos Variáveis**")
                st.dataframe(gastos_var_agrupados, use_container_width=True, hide_index=True)

# --- ABA 3: PATRIMÔNIO ---
with aba3:
    st.header("🏦 Patrimônio Acumulado")
    senha = st.text_input("Digite o PIN para acessar o cofre:", type="password")
    
    if senha == "190":  
        total_guardado = df_economias["Valor"].sum() if not df_economias.empty else 0.0
        st.metric("Total Acumulado (Todos os meses)", formatar_moeda(total_guardado))
        st.divider()
        
        col_eco_esq, col_eco_dir = st.columns(2)
        with col_eco_esq:
            st.subheader("Registrar Nova Entrada")
            with st.form("form_economia", clear_on_submit=True):
                mes_economia = st.selectbox("Mês do depósito", lista_meses, index=lista_meses.index(mes_selecionado))
                desc_economia = st.text_input("Descrição (Ex: Poupança, CDB, Caixinha)")
                valor_economia_str = st.text_input("Valor Guardado (R$)", placeholder="Ex: 1,20 ou 1.20")
                
                if st.form_submit_button("Guardar Dinheiro") and desc_economia:
                    v_eco = limpar_valor(valor_economia_str)
                    nova_economia = pd.DataFrame([{"Mês": mes_economia, "Descrição": desc_economia, "Valor": v_eco}])
                    df_economias = pd.concat([df_economias, nova_economia], ignore_index=True)
                    salvar_dados(df_economias, ABA_ECONOMIAS)
                    st.rerun()
                    
        with col_eco_dir:
            st.subheader("Log de Transações")
            edit_eco = st.data_editor(
                df_economias, 
                num_rows="dynamic", use_container_width=True, hide_index=True, key="ed_eco",
                column_config={"Valor": st.column_config.NumberColumn("Valor", format="R$ %.2f", step=0.01)}
            )
            if not edit_eco.reset_index(drop=True).equals(df_economias.reset_index(drop=True)):
                salvar_dados(edit_eco, ABA_ECONOMIAS)
                st.rerun()
                
    elif senha != "":
        st.error("Acesso negado. PIN incorreto.")
