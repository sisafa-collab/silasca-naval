import streamlit as st
import pytesseract
import re
from pdf2image import convert_from_bytes
import os # Para verificar a existência dos arquivos de imagem
import base64
import os
import streamlit as st
import pandas as pd

# =================================================================
# ⚓ SEÇÃO VISUAL E IDENTIDADE (TOPO CENTRALIZADO & SLOGAN FIXO)
# =================================================================

# --- 1. SLOGAN FIXO NO CANTO INFERIOR DIREITO (AGORA MAIOR) ---
if os.path.exists("slogan.png"):
    with open("slogan.png", "rb") as f:
        data_slogan = base64.b64encode(f.read()).decode()
        # Ampliado de 220px para 300px para máxima legibilidade no canto da tela
        st.markdown(
            f'<img src="data:image/png;base64,{data_slogan}" '
            f'style="position: fixed; bottom: 20px; right: 20px; width: 500px; z-index: 9999;">', 
            unsafe_allow_html=True
        )

# --- 2. LOGO CENTRALIZADO NO TOPO (AGORA MAIOR) ---
# Mudamos a calibração das colunas [1, 1.2, 1] para expandir o tamanho do logo central
col_logo_1, col_logo_2, col_logo_3 = st.columns([0.5, 2, 0.5]) 

with col_logo_2:
    if os.path.exists("LOGO_SILASCA.png"):
        st.image("LOGO_SILASCA.png", use_container_width=True)
    else:
        st.warning("⚠️ Arquivo 'LOGO_SILASCA.png' não encontrado no repositório.")

# --- 3. TÍTULOS E TEXTOS DO SISTEMA (COMPACTO EM VERMELHO E CINZA) ---
st.markdown("""
<div style="text-align: center; padding: 15px; border-top: 2px solid #bc3c31; margin-top: 10px; background-color: rgba(76, 73, 85, 0.04); border-radius: 0 0 12px 12px;">
    <p style="color: #bc3c31; font-weight: 900; font-size: 1.6rem; letter-spacing: 2px; line-height: 1.2; text-shadow: 0 0 6px rgba(188, 60, 49, 0.15); margin-bottom: 6px;">
        Analisador e Interpretador de Faturas 📜📜
    </p>
        <span style="color: #bc3c31; font-weight: 800;">🚨 Confira os dados antes de baixar as planilhas! 🚨</span>
    </p>
</div>
""", unsafe_allow_html=True)

# =================================================================
# 📊 CARREGAMENTO DA PLANILHA LOCAL DE REFERÊNCIA (VALORES / INDENIZAÇÕES)
# =================================================================
@st.cache_data
def carregar_tabela_referencia():
    # Tenta carregar XLSX ou CSV de forma inteligente
    if os.path.exists("CISSFA-2022-2023-2024.xlsx"):
        try:
            df_ref = pd.read_excel("CISSFA-2022-2023-2024.xlsx")
            df_ref['Código'] = df_ref['Código'].astype(str).str.strip().str.zfill(8)
            return df_ref
        except Exception as e:
            st.error(f"Erro ao ler XLSX (Falta o openpyxl?): {e}")
            return None
            
    elif os.path.exists("CISSFA-2022-2023-2024.csv"):
        try:
            # Tenta ler com separador padrão ou ponto e vírgula
            df_ref = pd.read_csv("CISSFA-2022-2023-2024.csv", sep=None, engine='python')
            df_ref['Código'] = df_ref['Código'].astype(str).str.strip().str.zfill(8)
            return df_ref
        except Exception as e:
            st.error(f"Erro ao ler CSV: {e}")
            return None
    else:
        return None

# --- 4. ÁREA TÉCNICA: PROCESSADOR OCR E INTELIGÊNCIA ---

# accept_multiple_files=True permite jogar vários PDFs de uma vez!
pdfs_carregados = st.file_uploader("Suba as faturas escaneadas em PDF", type=["pdf"], accept_multiple_files=True)

if pdfs_carregados:
    st.success(f"⚓ {len(pdfs_carregados)} documento(s) carregado(s) no passadiço!")
    
    # Processa cada PDF individualmente
    for pdf_carregado in pdfs_carregados:
        
        # Cria o "Box" expansível para cada arquivo
        with st.expander(f"📂 Inspeção do Arquivo: {pdf_carregado.name}", expanded=False):
            
            with st.spinner(f"Executando varredura OCR em {pdf_carregado.name}..."):
                try:
                    pdf_bytes = pdf_carregado.read()
                    paginas = convert_from_bytes(pdf_bytes)
                    
                    texto_completo = ""
                    for idx, imagem_pagina in enumerate(paginas):
                        texto_pagina = pytesseract.image_to_string(imagem_pagina, lang='por')
                        texto_completo += f"\n--- INÍCIO DA PÁGINA {idx + 1} ---\n{texto_pagina}\n"
                    
                    st.info("💡 Varredura concluída.")

                    # =========================================================
                    # 🎯 SISAFA NAVAL v5: EXTRAÇÃO ZONAL COM SUBTRAÇÃO DE RUÍDO
                    # =========================================================

                    # 1. CORTA O PDF EM GUIAS (Âncora principal inquebrável)
                    blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL', texto_completo)

                    # Filtra apenas blocos que possuam a seção "DADOS DO USUÁRIO"
                    guias_validas = [b for b in blocos_guia if re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO', b)]

                    if guias_validas:
                        st.markdown(f"### 📑 Identificadas {len(guias_validas)} Guia(s) de Apresentação")
                        
                        for i, guia in enumerate(guias_validas, 1):
                            with st.container(border=True):
                                st.markdown(f"**GUIA #{i}**")
                                
                                # Variáveis padrão de segurança
                                nome_usu, nip_usu, vinculo_usu, tipo_usu = "N/A", "N/A", "N/A", "N/A"
                                
                                # =========================================================
                                # ZONA 1: DADOS DO USUÁRIO (ESTRATÉGIA DE SUBTRAÇÃO)
                                # =========================================================
                                bloco_usuario = re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO(.*?)(?=DADOS\s+DO\s+ENCAMINHAMENTO|MOTIVO\s+DO\s+ENCAMINHAMENTO|$)', guia, re.DOTALL)
                                
                                if bloco_usuario:
                                    txt_usr = bloco_usuario.group(1)
                                    
                                    # 1º PASSO: Achata tudo para uma única linha (Mata o problema das colunas quebradas do Tesseract)
                                    txt_usr_linha = re.sub(r'\s+', ' ', txt_usr)
                                    
                                    # 2º PASSO: Caça Direta Inconfundível
                                    # Caça NIP (Qualquer sequência exata de 8 dígitos isolada)
                                    match_nip = re.search(r'\b\d{8}\b', txt_usr_linha)
                                    if match_nip: nip_usu = match_nip.group(0)
                                        
                                    # Caça Vínculo
                                    match_vinc = re.search(r'(?i)\b(TITULAR|DEPENDENTE)\b', txt_usr_linha)
                                    if match_vinc: vinculo_usu = match_vinc.group(1).upper()
                                        
                                    # Caça Tipo
                                    match_tipo = re.search(r'(?i)\b(DIRETO|INDIRETO)\b', txt_usr_linha)
                                    if match_tipo: tipo_usu = match_tipo.group(1).upper()
                                        
                                    # 3º PASSO: Caça Nome por Subtração de Rótulos
                                    # Removemos todas as "etiquetas" que o OCR lê do grid. 
                                    ruido_labels = r'(?i)\b(NOME SOCIAL|NOME|NIP|POSTO|V[ÍI]NCULO|TIPO|TITULAR|DEPENDENTE|DIRETO|INDIRETO|DADOS DO USU[ÁA]RIO)\b'
                                    txt_sem_labels = re.sub(ruido_labels, '', txt_usr_linha)
                                    
                                    # Removemos também o NIP que já guardamos, para que não suje o nome
                                    if nip_usu != "N/A":
                                        txt_sem_labels = txt_sem_labels.replace(nip_usu, '')
                                    
                                    # O que restou é o nome sujo com caracteres estranhos do grid (| , _ , :). Limpamos mantendo apenas letras.
                                    nome_bruto = re.sub(r'[^A-Za-zÀ-Úà-ú\s]', ' ', txt_sem_labels)
                                    
                                    # Remove espaços duplos
                                    nome_usu = re.sub(r'\s+', ' ', nome_bruto).strip()
                                    if not nome_usu:
                                        nome_usu = "Não identificado"

                                # --- Renderização do Painel Pessoal ---
                                col1, col2 = st.columns(2)
                                col1.write(f"👤 **Nome:** {nome_usu} \n\n**NIP:** `{nip_usu}`")
                                col2.write(f"🔗 **Vínculo:** `{vinculo_usu}` \n\n**Tipo:** `{tipo_usu}`")
                                
                                # =========================================================
                                # ZONA 2: MOTIVO DO ENCAMINHAMENTO (PROCEDIMENTOS)
                                # =========================================================
                                bloco_motivo = re.search(r'(?i)MOTIVO\s+DO\s+ENCAMINHAMENTO(.*?)(?=AUTORIZA[CÇ][AÃ]O|ASSINATURA|TOTAL|VISTO|$)', guia, re.DOTALL)
                                
                                if bloco_motivo:
                                    txt_mot = bloco_motivo.group(1) 
                                    
                                    # Procura 8 dígitos seguidos de qualquer texto
                                    procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–\|]*([^\n\r]+)', txt_mot)
                                    
                                    if procedimentos:
                                        st.markdown("**🩺 Exames / Procedimentos Faturados:**")
                                        
                                        for cod, desc in procedimentos:
                                            # Regra Anti-Colisão: Se o código for igual ao NIP capturado acima, ignora.
                                            if cod == nip_usu: continue 
                                            
                                            desc_limpa = re.sub(r'[_\|]+', '', desc).strip()
                                            if len(desc_limpa) > 2: # Evita imprimir descrições formadas só por pontos soltos
                                                st.caption(f"🔹 `{cod}` - {desc_limpa}")
                                    else:
                                        st.caption("⚠️ *Nenhum código CBHPM/TUSS identificado nesta zona.*")
                                else:
                                    st.caption("⚠️ *Bloco 'Motivo do Encaminhamento' não localizado pelo OCR.*")
                    
                    st.divider() # Separa as guias das ferramentas brutas
                    
                    # =========================================================
                    # 🛠️ FERRAMENTAS GENÉRICAS (Para o resto da fatura)
                    # =========================================================
                    aba_bruta, aba_filtros = st.tabs(["📄 Texto Bruto Integral", "🔍 Capturador de NIPs/Valores Soltos e Busca"])
                    
                    with aba_bruta:
                        st.text_area("Conteúdo extraído via OCR", value=texto_completo, height=400, key=f"txt_{pdf_carregado.name}")
                        
                    with aba_filtros:
                        colA, colB = st.columns(2)
                        with colA:
                            st.markdown("#### 🎯 NIPs e Valores Soltos no Documento")
                            nips = list(set(re.findall(r"\b(?:\d{2}\.\d{4}\.\d{2}|\d{8})\b", texto_completo)))
                            if nips:
                                st.success(f"NIPs avulsos localizados: {len(nips)}")
                                st.write(nips)
                            
                            valores = list(set(re.findall(r"(?:R\$\s*)?\b\d{1,3}(?:\.\d{3})*,\d{2}\b", texto_completo)))
                            if valores:
                                st.info(f"Valores avulsos localizados: {len(valores)}")
                                st.write(valores)
                                
                        with colB:
                            st.markdown("#### 🔎 Busca Manual")
                            termo = st.text_input("Buscar termo (ex: NUP, hospital):", key=f"busc_{pdf_carregado.name}")
                            if termo:
                                linhas_encontradas = [l.strip() for l in texto_completo.split('\n') if termo.lower() in l.lower()]
                                if linhas_encontradas:
                                    st.success(f"Encontradas {len(linhas_encontradas)} ocorrências:")
                                    for linha in linhas_encontradas:
                                        st.code(linha, language="text")

                except Exception as e:
                    st.error(f"Erro ao processar {pdf_carregado.name}: {e}")

