import streamlit as st
import pytesseract
import re
from pdf2image import convert_from_bytes
import os # Para verificar a existência dos arquivos de imagem
import base64
import pandas as pd
from dbfread import DBF
import tempfile

# =================================================================
# ⚓ SEÇÃO VISUAL E IDENTIDADE (TOPO CENTRALIZADO & SLOGAN FIXO)
# =================================================================

# --- 1. SLOGAN FIXO NO CANTO INFERIOR DIREITO (AGORA MAIOR) ---
if os.path.exists("slogan.png"):
    with open("slogan.png", "rb") as f:
        data_slogan = base64.b64encode(f.read()).decode()
        st.markdown(
            f'<img src="data:image/png;base64,{data_slogan}" '
            f'style="position: fixed; bottom: 20px; right: 20px; width: 500px; z-index: 9999;">', 
            unsafe_allow_html=True
        )

# --- 2. LOGO CENTRALIZADO NO TOPO (AGORA MAIOR) ---
col_logo_1, col_logo_2, col_logo_3 = st.columns([0.5, 2, 0.5]) 

with col_logo_2:
    if os.path.exists("LOGO_SILASCA.png"):
        st.image("LOGO_SILASCA.png", use_container_width=True)
    else:
        st.warning("⚠️ Arquivo 'LOGO_SILASCA.png' não encontrado no repositório.")

# --- 3. TÍTULOS E TEXTOS DO SISTEMA ---
st.markdown("""
<div style="text-align: center; padding: 15px; border-top: 2px solid #bc3c31; margin-top: 10px; background-color: rgba(76, 73, 85, 0.04); border-radius: 0 0 12px 12px;">
    <p style="color: #bc3c31; font-weight: 900; font-size: 1.6rem; letter-spacing: 2px; line-height: 1.2; text-shadow: 0 0 6px rgba(188, 60, 49, 0.15); margin-bottom: 6px;">
        Analisador e Interpretador de Faturas 📜
    </p>
    <p style="margin-bottom: 0;">
        <span style="color: #bc3c31; font-weight: 800;">🚨 Confira os dados antes de baixar as planilhas! 🚨</span>
    </p>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 📊 CARREGAMENTO DAS BASES DE DADOS (CISSFA LOCAL & BD UPLOAD)
# =================================================================

@st.cache_data
def carregar_tabela_referencia():
    # Tenta carregar XLSX ou CSV de forma inteligente direto do GitHub
    arquivo_xlsx = "CISSFA-2022-2023-2024.xlsx"
    arquivo_csv = "CISSFA-2022-2023-2024.csv"
    
    df_ref = None
    
    if os.path.exists(arquivo_xlsx):
        try:
            df_ref = pd.read_excel(arquivo_xlsx)
        except Exception as e:
            st.error(f"Erro técnico ao abrir o XLSX: {e}")
            return None
            
    elif os.path.exists(arquivo_csv):
        try:
            df_ref = pd.read_csv(arquivo_csv, sep=None, engine='python')
        except Exception as e:
            st.error(f"Erro técnico ao abrir o CSV: {e}")
            return None
    else:
        st.error("❌ Arquivo CISSFA não encontrado no servidor! Verifique se ele está na raiz do GitHub.")
        return None

    if df_ref is not None:
        # Normaliza os nomes das colunas para remover espaços laterais indesejados
        df_ref.columns = df_ref.columns.astype(str).str.strip()
        
        # Procura de forma flexível pela coluna 'Código' (aceita 'codigo', 'Código', etc.)
        col_codigo = next((col for col in df_ref.columns if col.lower() in ['código', 'codigo', 'cod']), None)
        
        if col_codigo:
            # Padroniza a coluna encontrada para 'Código' e aplica a formatação
            if col_codigo != 'Código':
                df_ref.rename(columns={col_codigo: 'Código'}, inplace=True)
                
            df_ref['Código'] = df_ref['Código'].astype(str).str.strip().str.zfill(8)
            return df_ref
        else:
            st.error(f"❌ A coluna de código não foi encontrada na planilha! Colunas disponíveis: {list(df_ref.columns)}")
            return None

df_cissfa = carregar_tabela_referencia()
if df_cissfa is not None:
    st.success("✅ Tabela CISSFA carregada e validada automaticamente pelo sistema.")
else:
    st.warning("⚠️ Operação da tabela CISSFA interrompida devido ao erro acima.")

st.markdown("### 🗄️ Upload do Banco de Dados")
bd_file = st.file_uploader("Suba o arquivo BD (.dbf, .xlsx ou .csv)", type=["dbf", "xlsx", "csv"])

df_bd = None
if bd_file:
    with st.spinner("Lendo Banco de Dados..."):
        try:
            if bd_file.name.lower().endswith('.dbf'):
                # Cria um arquivo temporário seguro para o DBFRead ler
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dbf") as tmp:
                    tmp.write(bd_file.read())
                    tmp_path = tmp.name
                df_bd = pd.DataFrame(iter(DBF(tmp_path)))
                os.remove(tmp_path) # Limpa o rastro logo em seguida
            elif bd_file.name.lower().endswith('.xlsx'):
                df_bd = pd.read_excel(bd_file)
            elif bd_file.name.lower().endswith('.csv'):
                df_bd = pd.read_csv(bd_file, sep=None, engine='python')
            
            # Padroniza NIP no BD (8 dígitos limpos)
            if 'NIP' in df_bd.columns:
                df_bd['NIP'] = df_bd['NIP'].astype(str).str.strip().str.zfill(8)
            st.success("✅ Banco de Dados carregado na memória com sucesso!")
        except Exception as e:
            st.error(f"Erro ao processar o BD: {e}")


# =================================================================
# ⚙️ ÁREA TÉCNICA: PROCESSADOR OCR E CRUZAMENTO DE DADOS
# =================================================================

st.markdown("### 📄 Processamento de Faturas")
pdfs_carregados = st.file_uploader("Suba as faturas escaneadas em PDF", type=["pdf"], accept_multiple_files=True)

# Lista tática para armazenar todas as guias de todos os PDFs
dados_consolidados_lasalus = []

if pdfs_carregados and df_bd is not None and df_cissfa is not None:
    st.success(f"⚓ {len(pdfs_carregados)} documento(s) pronto(s) para o processamento!")
    
    # Processa cada PDF individualmente
    for pdf_carregado in pdfs_carregados:
        
        with st.expander(f"📂 Inspeção do Arquivo: {pdf_carregado.name}", expanded=False):
            with st.spinner(f"Executando varredura OCR em {pdf_carregado.name}..."):
                try:
                    pdf_bytes = pdf_carregado.read()
                    paginas = convert_from_bytes(pdf_bytes)
                    
                    texto_completo = ""
                    for idx, imagem_pagina in enumerate(paginas):
                        texto_pagina = pytesseract.image_to_string(imagem_pagina, lang='por')
                        texto_completo += f"\n--- INÍCIO DA PÁGINA {idx + 1} ---\n{texto_pagina}\n"
                    
                    # 1. CORTA O PDF EM GUIAS
                    blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL', texto_completo)
                    guias_validas = [b for b in blocos_guia if re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO', b)]

                    if guias_validas:
                        st.markdown(f"**Identificadas {len(guias_validas)} Guia(s) neste arquivo:**")
                        
                        for i, guia in enumerate(guias_validas, 1):
                            with st.container(border=True):
                                # Variáveis padrão
                                nome_usu, nip_usu, vinculo_usu, tipo_usu = "N/A", "N/A", "N/A", "N/A"
                                
                                # --- ZONA 1: DADOS DO USUÁRIO ---
                                bloco_usuario = re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO(.*?)(?=DADOS\s+DO\s+ENCAMINHAMENTO|MOTIVO\s+DO\s+ENCAMINHAMENTO|$)', guia, re.DOTALL)
                                
                                if bloco_usuario:
                                    txt_usr = bloco_usuario.group(1)
                                    txt_usr_linha = re.sub(r'\s+', ' ', txt_usr)
                                    
                                    match_nip = re.search(r'\b\d{8}\b', txt_usr_linha)
                                    if match_nip: nip_usu = match_nip.group(0)
                                        
                                    match_vinc = re.search(r'(?i)\b(TITULAR|DEPENDENTE)\b', txt_usr_linha)
                                    if match_vinc: vinculo_usu = match_vinc.group(1).upper()
                                        
                                    match_tipo = re.search(r'(?i)\b(DIRETO|INDIRETO)\b', txt_usr_linha)
                                    if match_tipo: tipo_usu = match_tipo.group(1).upper()
                                        
                                    ruido_labels = r'(?i)\b(NOME SOCIAL|NOME|NIP|POSTO|V[ÍI]NCULO|TIPO|TITULAR|DEPENDENTE|DIRETO|INDIRETO|DADOS DO USU[ÁA]RIO)\b'
                                    txt_sem_labels = re.sub(ruido_labels, '', txt_usr_linha)
                                    if nip_usu != "N/A":
                                        txt_sem_labels = txt_sem_labels.replace(nip_usu, '')
                                    nome_bruto = re.sub(r'[^A-Za-zÀ-Úà-ú\s]', ' ', txt_sem_labels)
                                    nome_usu = re.sub(r'\s+', ' ', nome_bruto).strip()
                                    if not nome_usu: nome_usu = "Não identificado"

                                st.write(f"👤 **{nome_usu}** | NIP: `{nip_usu}`")
                                
                                # --- ZONA 2: PROCEDIMENTOS E CRUZAMENTO COM BD/CISSFA ---
                                bloco_motivo = re.search(r'(?i)MOTIVO\s+DO\s+ENCAMINHAMENTO(.*?)(?=AUTORIZA[CÇ][AÃ]O|ASSINATURA|TOTAL|VISTO|$)', guia, re.DOTALL)
                                
                                if bloco_motivo:
                                    procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–\|]*([^\n\r]+)', bloco_motivo.group(1))
                                    
                                    if procedimentos:
                                        for cod, desc in procedimentos:
                                            if cod == nip_usu: continue 
                                            desc_limpa = re.sub(r'[_\|]+', '', desc).strip()
                                            
                                            # ===============================================================
                                            # 🎯 REGRA DE NEGÓCIO: CRUZAMENTO COM BD E CISSFA
                                            # ===============================================================
                                            valor_final = 0.0
                                            status_cobranca = "Não Avaliado"
                                            
                                            if nip_usu != "N/A":
                                                info_militar = df_bd[df_bd['NIP'] == nip_usu]
                                                
                                                if not info_militar.empty:
                                                    # 1. Pega os parâmetros do militar
                                                    regra_imh = str(info_militar['IMH,C,1'].values[0]).strip().upper() if 'IMH,C,1' in info_militar.columns else "S"
                                                    tipo_dep_bd = str(info_militar['TIPO_DEP'].values[0]).strip().upper() if 'TIPO_DEP' in info_militar.columns else "D"
                                                    
                                                    # 2. Barreira Mestre: Se IMH,C,1 for "N", bloqueia!
                                                    if regra_imh == 'N':
                                                        valor_final = 0.0
                                                        status_cobranca = "NÃO INDENIZA (Isento)"
                                                        st.warning(f"⚠️ NIP {nip_usu} possui marcação 'N' no BD. Indenização zerada.")
                                                    
                                                    # 3. Se for 'S', procede com o cálculo normal
                                                    else:
                                                        info_cissfa = df_cissfa[df_cissfa['Código'] == cod]
                                                        if not info_cissfa.empty:
                                                            if tipo_dep_bd == 'I':
                                                                valor_final = info_cissfa['Valor 100%'].values[0]
                                                                status_cobranca = "Indeniza 100%"
                                                            else:
                                                                valor_final = info_cissfa['Valor 20%'].values[0]
                                                                status_cobranca = "Indeniza 20%"
                                                        else:
                                                            status_cobranca = "Código TUSS não achado no CISSFA"
                                                else:
                                                    status_cobranca = "NIP não achado no BD"
                                            
                                            st.caption(f"🔹 `{cod}` - {desc_limpa} -> **{status_cobranca}** (R$ {valor_final})")
                                            
                                            # Armazena na lista global
                                            dados_consolidados_lasalus.append({
                                                "Arquivo Origem": pdf_carregado.name,
                                                "NIP": nip_usu,
                                                "Nome do Usuário": nome_usu,
                                                "Código TUSS": cod,
                                                "Descrição Exame": desc_limpa,
                                                "Status Cálculo": status_cobranca,
                                                "Valor Cobrado (R$)": valor_final
                                            })
                except Exception as e:
                    st.error(f"Erro ao processar {pdf_carregado.name}: {e}")

# =================================================================
# 📥 MÓDULO DE EXPORTAÇÃO (PLANILHA FINAL LASALUS)
# =================================================================
if dados_consolidados_lasalus:
    st.divider()
    st.markdown("### 📊 Tabela Consolidada de Faturamento")
    
    df_final = pd.DataFrame(dados_consolidados_lasalus)
    
    # Mostra a tabela na tela para auditoria
    st.dataframe(df_final, use_container_width=True)
    
    # Gera o botão de Download Seguro (em memória, sem gravar no disco)
    csv_memoria = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Baixar Planilha Consolidada (CSV)",
        data=csv_memoria,
        file_name="faturamento_lasalus_auditado.csv",
        mime="text/csv",
    )
elif pdfs_carregados and (df_bd is None or df_cissfa is None):
    st.warning("⚠️ Carregue o Banco de Dados e garanta que a CISSFA foi carregada para iniciar o cruzamento.")