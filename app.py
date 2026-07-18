import streamlit as st
import pytesseract
import re
from pdf2image import convert_from_bytes
import os # Para verificar a existência dos arquivos de imagem
import base64
import os
import streamlit as st

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
                    # 🎯 INTELIGÊNCIA DE CAPTURA: GUIA DE APRESENTAÇÃO DA MB (BLINDADA)
                    # =========================================================

                    # 1. DIVISÃO FLEXÍVEL: Aceita espaços extras e procura também por "GUIA DE APRESENTAÇÃO"
                    # Adicionamos parênteses de captura para não perder o texto divisor se precisar dele
                    blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL|GUIA\s+DE\s+APRESENTA[CÇ][AÃ]O', texto_completo)

                    # 2. FILTRO INTELIGENTE: Às vezes o OCR lê "T1TULAR" ou "USUARI0". 
                    # Usamos um Regex mais tolerante para identificar se o bloco realmente é uma guia.
                    guias_validas = [b for b in blocos_guia if re.search(r'(?i)T[I1]TULAR', b) or re.search(r'(?i)USU[ÁA]RIO', b)]

                    if guias_validas:
                        st.markdown(f"### 📑 Identificadas {len(guias_validas)} Guia(s) de Apresentação")
                        
                        for i, guia in enumerate(guias_validas, 1):
                            with st.container(border=True):
                                st.markdown(f"**GUIA #{i}**")
                                
                                # ---------------------------------------------------------
                                # 1. CAÇA O TITULAR (Tolerante a ausência do NIP e quebras de linha)
                                # Lê: "Titular" -> pega o NIP (se tiver) -> pega o Nome até o fim da linha
                                # ---------------------------------------------------------
                                match_titular = re.search(r'(?i)T[i1]tular[\s:]*([\d\.\-]+)?\s*([^\n]+)', guia)
                                
                                nip_titular = match_titular.group(1).strip() if match_titular and match_titular.group(1) else "N/A"
                                nome_titular = match_titular.group(2).strip() if match_titular and match_titular.group(2) else "Não identificado"
                                
                                # Limpa lixos comuns do OCR no final do nome
                                nome_titular = re.sub(r'[-_:\.\s]+$', '', nome_titular)

                                # ---------------------------------------------------------
                                # 2. CAÇA O USUÁRIO (Tolerante a espaços na relação, ex: "FILHO (A)")
                                # ---------------------------------------------------------
                                # Busca relação (pode ter espaços) até encontrar um traço ou dois pontos, depois pega o Nome
                                match_usuario = re.search(r'(?i)Usu[aá]rio[\s:]*([A-Za-zÀ-Úà-ú\s\(\)]+?)[\s\-–:]+([^\n]+)', guia)
                                
                                if match_usuario:
                                    relacao_usu = match_usuario.group(1).strip()
                                    nome_usu = match_usuario.group(2).strip()
                                else:
                                    # Plano B: Se não achar a "relação" com traço, tenta pegar só o nome na frente
                                    match_usu_fallback = re.search(r'(?i)Usu[aá]rio[\s:]*([^\n]+)', guia)
                                    relacao_usu = "N/A"
                                    nome_usu = match_usu_fallback.group(1).strip() if match_usu_fallback else "Não identificado"
                                
                                nome_usu = re.sub(r'[-_:\.\s]+$', '', nome_usu)

                                # --- Exibe os Dados Pessoais ---
                                col1, col2 = st.columns(2)
                                col1.write(f"🛡️ **Titular:** {nome_titular} \n\n**NIP:** `{nip_titular}`")
                                col2.write(f"👤 **Usuário:** {nome_usu} \n\n**Relação:** `{relacao_usu}`")
                                
                                # ---------------------------------------------------------
                                # 3. CAÇA OS PROCEDIMENTOS (Tolerante a símbolos estranhos separando os códigos)
                                # ---------------------------------------------------------
                                # Procura exatos 8 dígitos, ignora espaços/traços/pontos, e captura o nome do procedimento
                                procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–]*([^\n\r]+)', guia)
                                
                                if procedimentos:
                                    st.markdown("**🩺 Procedimentos Identificados:**")
                                    for cod, desc in procedimentos:
                                        # Limpa espaços extras ou hifens perdidos na descrição
                                        desc_limpa = desc.strip(" -_.")
                                        st.caption(f"🔹 `{cod}` - {desc_limpa}")
                                else:
                                    st.caption("⚠️ *Nenhum código CBHPM/TUSS de 8 dígitos localizado nesta guia.*")
                    
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

