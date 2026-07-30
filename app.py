import streamlit as st
import pytesseract
import re
from pdf2image import convert_from_bytes
import os # Para verificar a existência dos arquivos de imagem
import base64
import pandas as pd
from dbfread import DBF
import tempfile
import difflib  # Biblioteca nativa do Python para busca flexível/aproximada (Fuzzy Match.. útil para documentos mal escaneados)

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
            # header=1 pula a primeira linha inútil e usa a linha 2 como cabeçalho
            df_ref = pd.read_excel(arquivo_xlsx, header=1)
        except Exception as e:
            st.error(f"Erro técnico ao abrir o XLSX: {e}")
            return None
            
    elif os.path.exists(arquivo_csv):
        try:
            # header=1 pula a primeira linha inútil no CSV também
            df_ref = pd.read_csv(arquivo_csv, sep=None, engine='python', header=1)
        except Exception as e:
            st.error(f"Erro técnico ao abrir o CSV: {e}")
            return None
    else:
        st.error("❌ Arquivo CISSFA não encontrado no servidor! Verifique se ele está na raiz do GitHub.")
        return None

    if df_ref is not None:
        # Remove espaços invisíveis dos cabeçalhos recém-definidos
        df_ref.columns = df_ref.columns.astype(str).str.strip()
        
        # Procura de forma flexível pela coluna 'Código'
        col_codigo = next((col for col in df_ref.columns if col.lower() in ['código', 'codigo', 'cod']), None)
        
        if col_codigo:
            # Padroniza a coluna encontrada para 'Código' e aplica a formatação de 8 dígitos
            if col_codigo != 'Código':
                df_ref.rename(columns={col_codigo: 'Código'}, inplace=True)
                
            df_ref['Código'] = df_ref['Código'].astype(str).str.strip().str.zfill(8)
            return df_ref
        else:
            st.error(f"❌ A coluna de código não foi encontrada na planilha! Colunas disponíveis identificadas: {list(df_ref.columns)}")
            return None

df_cissfa = carregar_tabela_referencia()
if df_cissfa is not None:
    st.success("✅ Tabela CISSFA carregada com sucesso!")
    # 🔍 PAINEL DE AUDITORIA DO CISSFA
    with st.expander("🔎 O que o sistema leu na Tabela CISSFA?"):
        st.write(f"**Total de registros carregados:** {df_cissfa.shape[0]} linhas e {df_cissfa.shape[1]} colunas.")
        st.write("**Colunas reconhecidas:**", list(df_cissfa.columns))
        st.markdown("**Amostra dos dados (Primeiras 50 linhas):**")
        st.dataframe(df_cissfa.head(50))
else:
    st.warning("⚠️ Operação da tabela CISSFA interrompida.")
    
st.markdown("### 🗄️ Upload do Banco de Dados")
bd_file = st.file_uploader("Suba o arquivo BD (.dbf, .xlsx ou .csv)", type=["dbf", "xlsx", "csv"])

df_bd = None
if bd_file:
    with st.spinner("Lendo Banco de Dados..."):
        try:
            if bd_file.name.lower().endswith('.dbf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".dbf") as tmp:
                    tmp.write(bd_file.read())
                    tmp_path = tmp.name
                
                dbf_table = DBF(
                    tmp_path, 
                    encoding='cp1252', 
                    ignore_missing_memofile=True,
                    char_decode_errors='ignore'
                )
                
                df_bd = pd.DataFrame(iter(dbf_table))
                os.remove(tmp_path)
                
            elif bd_file.name.lower().endswith('.xlsx'):
                df_bd = pd.read_excel(bd_file, dtype=str)
                
                
            elif bd_file.name.lower().endswith('.csv'):
                bd_file.seek(0)
                # 🛑 O PULO DO GATO: dtype=str força o Pandas a ler TUDO como texto puro!
                df_bd = pd.read_csv(bd_file, sep=None, engine='python', encoding='latin-1', dtype=str)
            
            if df_bd is not None and not df_bd.empty:
                df_bd.columns = df_bd.columns.astype(str).str.strip()
                
                col_nip = next((col for col in df_bd.columns if col.lower() in ['nip', 'c_nip']), None)
                if col_nip:
                    if col_nip != 'NIP':
                        df_bd.rename(columns={col_nip: 'NIP'}, inplace=True)
                    df_bd['NIP'] = df_bd['NIP'].astype(str).str.strip().str.zfill(8)
                    
            st.success("✅ Banco de Dados carregado na memória com sucesso!")
            # 🔍 PAINEL DE AUDITORIA DO BANCO DE DADOS (BD)
            with st.expander("🔎 O que o sistema leu no Banco de Dados (BD)?"):
                st.write(f"**Arquivo processado:** `{bd_file.name}`")
                st.write(f"**Dimensões da base:** {df_bd.shape[0]} linhas e {df_bd.shape[1]} colunas.")
                st.write("**Colunas reconhecidas:**", list(df_bd.columns))
                if 'NIP' in df_bd.columns:
                    st.info("✅ Coluna NIP identificada e padronizada com 8 dígitos.")
                else:
                    st.warning("⚠️ Atenção: A coluna NIP não foi encontrada automaticamente com esse nome.")
                st.markdown("**Amostra dos dados (Primeiras 50 linhas):**")
                st.dataframe(df_bd.head(50))

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
            with st.spinner(f"A executar varredura OCR em {pdf_carregado.name}..."):
                try:
                    pdf_bytes = pdf_carregado.read()
                    paginas = convert_from_bytes(pdf_bytes)
                    
                    texto_completo = ""
                    for idx, imagem_pagina in enumerate(paginas):
                        texto_pagina = pytesseract.image_to_string(imagem_pagina, lang='por')
                        texto_completo += f"\n--- INÍCIO DA PÁGINA {idx + 1} ---\n{texto_pagina}\n"
                    
                    busca_data = re.search(r'(\d{2}/\d{2}/\d{4})', texto_completo)
                    data_fatura = busca_data.group(1) if busca_data else "Data_Não_Encontrada"
                    
                    # ==========================================================
                    # 👁️ RAIO-X DO RADAR (TEXTO BRUTO DO OCR)
                    # ==========================================================
                    with st.expander("👁️ Ver Texto Bruto (Raio-X do OCR)", expanded=False):
                        st.text_area("Texto Extraído:", texto_completo, height=300)
                    
                    # FUNÇÃO GLOBAL DE LIMPEZA DE MOEDA PARA OS DOIS MODOS
                    def limpar_moeda(v):
                        v_str = str(v).upper().replace('R$', '').replace(' ', '')
                        if '.' in v_str and ',' in v_str: 
                            v_str = v_str.replace('.', '') 
                        v_str = v_str.replace(',', '.') 
                        try: return float(v_str)
                        except: return 0.0
                        
                    # ==========================================================
                    # 🚦 INTELIGÊNCIA DE DECISÃO: MODO RELATÓRIO vs MODO GUIA
                    # ==========================================================
                    is_fatura_tabela = bool(re.search(r'(?i)GUIA\s+DE\s+ENCAMINHAMENTO\s+PARA\s+EXAMES\s+EXTERNOS', texto_completo))
                    
                    if is_fatura_tabela:
                        st.info("📄 Formato de Fatura/Relatório em Tabela detetado (Padrão LASALUS)! A ler registos...")
                        
                        blocos_lasalus = re.split(r'(?i)GUIA\s+DE\s+ENCAMINHAMENTO\s+PARA\s+EXAMES\s+EXTERNOS', texto_completo)
                        if blocos_lasalus and len(blocos_lasalus[0].strip()) < 50:
                            blocos_lasalus = blocos_lasalus[1:]
                            
                        for i, bloco in enumerate(blocos_lasalus, 1):
                            exames_encontrados = 0
                            
                            # BUSCA DE NIP E NOME BLINDADA CONTRA ERROS DE OCR
                            match_nip = re.search(r'\b(\d{8})\b', bloco)
                            nip_usu = match_nip.group(1) if match_nip else "N/A"
                            
                            match_nome = re.search(r'(?i)(?:Paciente|Nome)[^\w]*([A-Za-zÀ-Úà-ú\s]{5,})', bloco)
                            nome_usu = match_nome.group(1).replace('Idade', '').strip() if match_nome else "Não identificado"
                            
                            if nip_usu == "N/A":
                                continue
                                
                            with st.container(border=True):
                                inicio_tabela = re.search(r'(?i)(?:CÓDIGO\s+DESCRIÇÃO|Relação\s+de\s+exame)', bloco)
                                if inicio_tabela:
                                    texto_tabela = bloco[inicio_tabela.end():]
                                    linhas = texto_tabela.split('\n')
                                    
                                    for linha in linhas:
                                        if re.search(r'(?i)(?:Guia\s+autorizada|IMPORTANTE|Declaro\s+que|Assinatura)', linha):
                                            break
                                            
                                        # ⚓ REGEX CEGO: Aceita códigos pela metade ou até linhas sem código
                                        match_linha = re.search(r'^\s*(?:([A-Za-z0-9]{3,10})\s+)?([A-Za-zÀ-Úà-ú].*)', linha)
                                        
                                        if match_linha:
                                            cod_ocr = match_linha.group(1) if match_linha.group(1) else ""
                                            if cod_ocr == nip_usu:
                                                continue 
                                                
                                            desc_bruta = match_linha.group(2)
                                            desc_limpa = re.sub(r'[\s\d\,\.\-]+$', '', desc_bruta).strip()
                                            exames_encontrados += 1
                                            
                                            # ===============================================================
                                            # 🎯 REGRA DE NEGÓCIO E MOTOR FUZZY (LASALUS)
                                            # ===============================================================
                                            valor_final = 0.0
                                            status_cobranca = "Não Avaliado"
                                            cod_final = cod_ocr
                                            desc_final = desc_limpa
                                            perfil_usu = "Desconhecido"
                                            perc_cobrar = 100
                                            
                                            if nip_usu != "N/A":
                                                cond_titular = df_bd.get('NIP_TIT,C,8', pd.Series(dtype=str)) == nip_usu
                                                cond_depend = df_bd.get('NIP_VINC,C,8', pd.Series(dtype=str)) == nip_usu
                                                info_militar = df_bd[cond_titular | cond_depend]
                                                
                                                if not info_militar.empty:
                                                    primeiro_nome_ocr = nome_usu.split()[0].upper() if nome_usu.split() else ""
                                                    registro = info_militar.iloc[0] 
                                                    for idx, row in info_militar.iterrows():
                                                        if primeiro_nome_ocr in str(row.get('NOME,C,80', '')).upper():
                                                            registro = row
                                                            break
                                                            
                                                    regra_imh = str(registro.get('IMH,C,1', 'S')).strip().upper()
                                                    tipo_dep_raw = str(registro.get('TIPO_DEP,C,1', '')).strip().upper()
                                                    
                                                    if tipo_dep_raw in ['NAN', 'NONE', 'NULL', ''] or len(tipo_dep_raw) == 0:
                                                        perfil_usu, perc_cobrar = "Titular", 20
                                                    elif tipo_dep_raw == 'D':
                                                        perfil_usu, perc_cobrar = "Dep. Direto", 20
                                                    else:
                                                        perfil_usu, perc_cobrar = "Dep. Indireto", 100
                                                        
                                                    if regra_imh == 'N':
                                                        valor_final, status_cobranca = 0.0, f"NÃO INDENIZA (Isento) - {perfil_usu}"
                                                    else:
                                                        # MOTOR FUZZY
                                                        info_cissfa = pd.DataFrame()
                                                        if cod_ocr and len(cod_ocr) >= 6:
                                                            match_cod = df_cissfa[df_cissfa['Código'].astype(str).str.contains(cod_ocr, na=False)]
                                                            if not match_cod.empty:
                                                                info_cissfa = match_cod
                                                                
                                                        if info_cissfa.empty:
                                                            opcoes_desc = df_cissfa['Descrição'].dropna().astype(str).tolist()
                                                            match_desc = difflib.get_close_matches(desc_limpa.upper(), opcoes_desc, n=1, cutoff=0.4)
                                                            if match_desc:
                                                                info_cissfa = df_cissfa[df_cissfa['Descrição'] == match_desc[0]]
                                                                
                                                        if not info_cissfa.empty:
                                                            cod_final = str(info_cissfa['Código'].values[0])
                                                            desc_final = str(info_cissfa['Descrição'].values[0])
                                                            if perc_cobrar == 100:
                                                                valor_final = limpar_moeda(info_cissfa['Valor 100%'].values[0])
                                                                status_cobranca = f"Indeniza 100% ({perfil_usu})"
                                                            else:
                                                                valor_final = limpar_moeda(info_cissfa['Valor 20%'].values[0])
                                                                status_cobranca = f"Indeniza 20% ({perfil_usu})"
                                                        else:
                                                            status_cobranca = "Exame não localizado na CISSFA"
                                                else:
                                                    status_cobranca = "NIP não achado no BD"
                                                
                                            st.caption(f"🔹 Lido OCR: `{cod_ocr}` {desc_limpa} ➡️ **Oficial CISSFA:** `{cod_final}` {desc_final} (R$ {valor_final:,.2f})")
                                            
                                            # Salva o resultado unificado
                                            dados_consolidados_lasalus.append({
                                                "Data": data_fatura,  
                                                "Arquivo": pdf_carregado.name,
                                                "NIP": nip_usu,
                                                "Nome Paciente": nome_usu,
                                                "Código (CISSFA)": cod_final,
                                                "Descrição Exame": desc_final,
                                                "Status": status_cobranca,
                                                "Valor (R$)": valor_final,
                                                "Perfil": perfil_usu
                                            })
                                if exames_encontrados == 0:
                                    st.warning(f"⚠️ A guia de {nome_usu} foi lida, mas nenhum exame foi detetado sob ela.")

                    else:
                        # ==========================================================
                        # ⚓ MODO CLÁSSICO: GUIA DE APRESENTAÇÃO DA MB (Padrão Antigo)
                        # ==========================================================
                        blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL', texto_completo)
                        guias_validas = [b for b in blocos_guia if re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO', b)]

                        if guias_validas:
                            st.markdown(f"**Identificadas {len(guias_validas)} Guia(s) de Apresentação neste arquivo:**")
                            
                            for i, guia in enumerate(guias_validas, 1):
                                with st.container(border=True):
                                    nome_usu, nip_usu = "Não identificado", "N/A"
                                    
                                    bloco_usuario = re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO(.*?)(?=DADOS\s+DO\s+ENCAMINHAMENTO|MOTIVO\s+DO\s+ENCAMINHAMENTO|$)', guia, re.DOTALL)
                                    if bloco_usuario:
                                        txt_usr_linha = re.sub(r'\s+', ' ', bloco_usuario.group(1))
                                        
                                        # CAÇA AO NIP E NOME BLINDADA
                                        match_nip = re.search(r'\b(\d{8})\b', txt_usr_linha)
                                        if match_nip: nip_usu = match_nip.group(1)
                                        
                                        match_nome = re.search(r'(?i)(?:NOME|SOCIAL)[^\w]*([A-Za-zÀ-Úà-ú\s]{5,})', txt_usr_linha)
                                        if match_nome: 
                                            nome_usu = match_nome.group(1).strip()
                                        else:
                                            # Limpeza bruta se não achar a palavra Nome
                                            ruido_labels = r'(?i)\b(NOME SOCIAL|NOME|NIP|POSTO|V[ÍI]NCULO|TIPO|TITULAR|DEPENDENTE|DIRETO|INDIRETO|DADOS DO USU[ÁA]RIO)\b'
                                            txt_sem_labels = re.sub(ruido_labels, '', txt_usr_linha)
                                            if nip_usu != "N/A": txt_sem_labels = txt_sem_labels.replace(nip_usu, '')
                                            nome_usu = re.sub(r'[^A-Za-zÀ-Úà-ú\s]', ' ', txt_sem_labels).strip()

                                    st.write(f"👤 **{nome_usu}** | NIP: `{nip_usu}`")
                                    
                                    bloco_motivo = re.search(r'(?i)MOTIVO\s+DO\s+ENCAMINHAMENTO(.*?)(?=AUTORIZA[CÇ][AÃ]O|ASSINATURA|TOTAL|VISTO|$)', guia, re.DOTALL)
                                    if bloco_motivo:
                                        procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–\|]*([^\n\r]+)', bloco_motivo.group(1))
                                        if procedimentos:
                                            for cod, desc in procedimentos:
                                                if cod == nip_usu: continue 
                                                desc_limpa = re.sub(r'[_\|]+', '', desc).strip()
                                                
                                                valor_final = 0.0
                                                status_cobranca = "Não Avaliado"
                                                cod_final = cod
                                                desc_final = desc_limpa
                                                perfil_usu = "Desconhecido"
                                                perc_cobrar = 100
                                                
                                                if nip_usu != "N/A":
                                                    cond_titular = df_bd.get('NIP_TIT,C,8', pd.Series(dtype=str)) == nip_usu
                                                    cond_depend = df_bd.get('NIP_VINC,C,8', pd.Series(dtype=str)) == nip_usu
                                                    info_militar = df_bd[cond_titular | cond_depend]
                                                    
                                                    if not info_militar.empty:
                                                        primeiro_nome_ocr = nome_usu.split()[0].upper() if nome_usu else ""
                                                        registro = info_militar.iloc[0] 
                                                        
                                                        for idx, row in info_militar.iterrows():
                                                            if primeiro_nome_ocr in str(row.get('NOME,C,80', '')).upper():
                                                                registro = row
                                                                break
                                                                
                                                        regra_imh = str(registro.get('IMH,C,1', 'S')).strip().upper()
                                                        tipo_dep_raw = str(registro.get('TIPO_DEP,C,1', '')).strip().upper()
                                                        
                                                        if tipo_dep_raw in ['NAN', 'NONE', 'NULL', ''] or len(tipo_dep_raw) == 0:
                                                            perfil_usu, perc_cobrar = "Titular", 20
                                                        elif tipo_dep_raw == 'D':
                                                            perfil_usu, perc_cobrar = "Dep. Direto", 20
                                                        else:
                                                            perfil_usu, perc_cobrar = "Dep. Indireto", 100
                                                            
                                                        if regra_imh == 'N':
                                                            valor_final, status_cobranca = 0.0, f"NÃO INDENIZA (Isento) - {perfil_usu}"
                                                        else:
                                                            # ===============================================================
                                                            # 🧠 MOTOR FUZZY DE APROXIMAÇÃO IMPLEMENTADO NO MODO CLÁSSICO!
                                                            # ===============================================================
                                                            info_cissfa = pd.DataFrame()
                                                            
                                                            # 1. Tenta por código primeiro
                                                            if cod and len(cod) >= 6:
                                                                match_cod = df_cissfa[df_cissfa['Código'].astype(str).str.contains(cod, na=False)]
                                                                if not match_cod.empty:
                                                                    info_cissfa = match_cod
                                                                    
                                                            # 2. Se falhar, busca fuzzy pela descrição
                                                            if info_cissfa.empty:
                                                                opcoes_desc = df_cissfa['Descrição'].dropna().astype(str).tolist()
                                                                match_desc = difflib.get_close_matches(desc_limpa.upper(), opcoes_desc, n=1, cutoff=0.4)
                                                                if match_desc:
                                                                    info_cissfa = df_cissfa[df_cissfa['Descrição'] == match_desc[0]]

                                                            if not info_cissfa.empty:
                                                                cod_final = str(info_cissfa['Código'].values[0])
                                                                desc_final = str(info_cissfa['Descrição'].values[0])
                                                                
                                                                if perc_cobrar == 100:
                                                                    valor_final = limpar_moeda(info_cissfa['Valor 100%'].values[0])
                                                                    status_cobranca = f"Indeniza 100% ({perfil_usu})"
                                                                else:
                                                                    valor_final = limpar_moeda(info_cissfa['Valor 20%'].values[0])
                                                                    status_cobranca = f"Indeniza 20% ({perfil_usu})"
                                                            else:
                                                                status_cobranca = "Exame não localizado na CISSFA"
                                                    else:
                                                        status_cobranca = "NIP não achado no BD"
                                                        
                                                st.caption(f"🔹 Lido OCR: `{cod}` {desc_limpa} ➡️ **Oficial CISSFA:** `{cod_final}` {desc_final} (R$ {valor_final:,.2f})")
                                                
                                                # MESMO FORMATO DA LASALUS (Impede quebra do painel)
                                                dados_consolidados_lasalus.append({
                                                    "Data": data_fatura,  # <--- ENCAIXE 3 AQUI
                                                    "Arquivo": pdf_carregado.name,
                                                    "NIP": nip_usu,
                                                    "Nome Paciente": nome_usu,
                                                    "Código (CISSFA)": cod_final,
                                                    "Descrição Exame": desc_final,
                                                    "Status": status_cobranca,
                                                    "Valor (R$)": valor_final,
                                                    "Perfil": perfil_usu
                                                })
                        else:
                            st.warning("⚠️ Nenhuma guia ou tabela de faturamento compatível foi localizada neste PDF.")

                except Exception as e:
                    st.error(f"Erro ao processar {pdf_carregado.name}: {e}")

# =================================================================================
# ✍️ PAINEL DO AUDITOR MILITAR (EDIÇÃO E RECALCULO AUTOMÁTICO)
# =================================================================================
if dados_consolidados_lasalus:
    st.divider()
    st.markdown("### ✍️ Painel de Correção de Faturamento")
    st.info("💡 **Atenção:** Clique na coluna **'NIP'** para trocar o militar, ou na coluna **'Código (CISSFA)'** para corrigir o exame. O sistema refaz a conta e puxa os nomes na hora!")
    
    # Transforma os dados em DataFrame para o Editor
    df_resultados = pd.DataFrame(dados_consolidados_lasalus)
    
    # Cria a Tabela Editável (Agora o NIP também é editável)
    df_editado = st.data_editor(
        df_resultados,
        column_config={
            "NIP": st.column_config.TextColumn("NIP - ✏️ EDITE AQUI", required=True),
            "Código (CISSFA)": st.column_config.TextColumn("Código (CISSFA) - ✏️ EDITE AQUI", required=True),
        },
        # Tranca as colunas que o usuário não deve mexer
        disabled=["Arquivo", "Nome Paciente", "Descrição Exame", "Status", "Valor (R$)", "Perfil"],
        hide_index=True,
        use_container_width=True,
        key="auditoria_editor"
    )
    
    # -----------------------------------------------------
    # 🔄 MOTOR DE RECALCULO (Dispara quando você edita)
    # -----------------------------------------------------
    for i in range(len(df_editado)):
        
        # --- 1. VERIFICAÇÃO DE MUDANÇA DE NIP ---
        nip_antigo = str(df_resultados.iloc[i].get("NIP", "")).strip()
        nip_novo = str(df_editado.iloc[i].get("NIP", "")).strip()
        
        if nip_novo != nip_antigo and nip_novo != "":
            # Procura o NIP novo no Banco de Dados
            # (Ajuste o nome das colunas 'NIP' e 'NOME' se no seu BD estiver diferente)
            paciente = df_bd[df_bd['NIP'].astype(str).str.strip() == nip_novo]
            
            if not paciente.empty:
                novo_nome = paciente['NOME'].values[0]
                df_editado.at[i, "Nome Paciente"] = novo_nome
                st.success(f"✅ Linha {i+1}: NIP corrigido. Paciente atualizado para **{novo_nome}**.")
            else:
                df_editado.at[i, "Nome Paciente"] = "NIP inexistente"
                st.error(f"❌ Linha {i+1}: NIP '{nip_novo}' inexistente no Banco de Dados!")

        # --- 2. VERIFICAÇÃO DE MUDANÇA DE CÓDIGO CISSFA ---
        cod_antigo = str(df_resultados.iloc[i].get("Código (CISSFA)", "")).strip()
        cod_novo = str(df_editado.iloc[i].get("Código (CISSFA)", "")).strip()
        
        if cod_novo != cod_antigo and cod_novo != "" and str(cod_novo).lower() != 'nan':
            nova_info = df_cissfa[df_cissfa['CÓDIGO'].astype(str).str.strip() == cod_novo]
            
            if not nova_info.empty:
                perfil_atual = str(df_editado.iloc[i].get("Perfil", ""))
                perc_cobrar = 100 if "Indireto" in perfil_atual else 20
                
                v_bruto = nova_info[f'VALOR {perc_cobrar}%'].values[0]
                v_str = str(v_bruto).upper().replace('R$', '').replace(' ', '')
                if '.' in v_str and ',' in v_str: v_str = v_str.replace('.', '')
                v_str = v_str.replace(',', '.')
                try: novo_valor = float(v_str)
                except: novo_valor = 0.0
                
                nova_desc = str(nova_info['DESCRIÇÃO'].values[0])
                
                st.success(f"✅ Atualização na linha {i+1}: Exame alterado para **{nova_desc}** (R$ {novo_valor:,.2f})")
                
                df_editado.at[i, "Descrição Exame"] = nova_desc
                df_editado.at[i, "Valor (R$)"] = novo_valor
                df_editado.at[i, "Status"] = f"Corrigido à Mão - Indeniza {perc_cobrar}%"
            else:
                st.error(f"❌ O código '{cod_novo}' não existe na tabela CISSFA!")

    # =================================================================
    # 📥 MÓDULO DE EXPORTAÇÃO (FILTRADO E FORMATADO)
    # =================================================================
    if dados_consolidados_lasalus:
        st.divider()
        st.markdown("### 📊 Tabela Pronta para Exportação (Final)")
        
        # 1. Copia o dataframe já editado/corrigido pelo auditor
        df_pre_export = df_editado.copy()
        
        # Garante que o valor é um número decimal para fazermos o filtro
        df_pre_export['Valor (R$)'] = pd.to_numeric(df_pre_export['Valor (R$)'], errors='coerce').fillna(0)
        
        # 2. FILTRO TÁTICO: Mantém APENAS valores maiores que zero
        df_pre_export = df_pre_export[df_pre_export['Valor (R$)'] > 0]
        
        # 3. Monta o DataFrame final com as 6 colunas exatas
        df_export = pd.DataFrame()
        
        # (A) NIP
        df_export["NIP (NNNNNNNN)"] = df_pre_export["NIP"]
        
        # (B) DATA
        if "Data" in df_pre_export.columns:
            datas = df_pre_export["Data"].astype(str)
        else:
            datas = "DATA_A_DEFINIR"
        df_export["DATA (DD/MM/AA)"] = datas
        
        # (C) VALOR
        df_export["VALOR (R$)"] = df_pre_export["Valor (R$)"]
        
        # (D) OSE?
        df_export["OSE? (s/n)"] = "s"
        
        # (E) DESCRIÇÃO COMPLETA
        if "Empresa" in df_pre_export.columns:
            empresas = df_pre_export["Empresa"].astype(str)
        else:
            empresas = "LASALUS"
            
        # 🛡️ BLINDAGEM DO CSV: Removemos pontos e vírgulas (;) e quebras de linha (\n) 
        # do texto do exame para o Excel não explodir as colunas!
        descricoes_limpas = df_pre_export["Descrição Exame"].astype(str).replace(r'[\n\r;]', ' ', regex=True)
        
        df_export["DESCRIÇÃO"] = (
            "Realização de exame laboratorial - " + 
            descricoes_limpas + 
            " - utilizado por usuário (a) do SSM, na empresa " + 
            empresas + 
            " no dia " + 
            datas + "."
        )
        
        # (F) NIP DEPENDENTE
        # 🛡️ REGRA TÁTICA: Se a palavra 'Dep' estiver no perfil, preenche. Se for titular, fica vazio.
        def classificar_nip_dep(row):
            perfil = str(row.get("Perfil", ""))
            if "Dep" in perfil:
                return row["NIP"]
            return ""
            
        df_export["NIP DEPENDENTE (NNNNNNNN)"] = df_pre_export.apply(classificar_nip_dep, axis=1)
        
        # Exibe a planilha lapidada na tela para o usuário ver o resultado do filtro
        st.dataframe(df_export, use_container_width=True, hide_index=True)
        
        # Gera o arquivo CSV (usando ponto e vírgula)
        csv_memoria = df_export.to_csv(index=False, sep=";", encoding='utf-8-sig').encode('utf-8-sig')
        
        st.download_button(
            label="📥 Baixar Planilha Consolidada (.CSV)",
            data=csv_memoria,
            file_name="faturamento_lasalus_auditado.csv",
            mime="text/csv",
        )
elif 'pdfs_carregados' in locals() and pdfs_carregados and (df_bd is None or df_cissfa is None):
    st.warning("⚠️ Carregue o Banco de Dados e garanta que a CISSFA foi carregada para iniciar o cruzamento.")