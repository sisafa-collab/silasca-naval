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
                    # 🎯 INTELIGÊNCIA DE CAPTURA ANCORADA: SISAFA NAVAL v2
                    # =========================================================

                    # Quebra flexível aceitando variações de espaços no divisor principal das OSEs
                    blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL|GUIA\s+DE\s+APRESENTA[CÇ][AÃ]O', texto_completo)

                    # Filtro inicial de blocos válidos
                    guias_validas = [b for b in blocos_guia if re.search(r'(?i)T[I1]TULAR', b) or re.search(r'(?i)USU[ÁA]RIO', b)]

                    if guias_validas:
                        st.markdown(f"### 📑 Identificadas {len(guias_validas)} Guia(s) de Apresentação")
                        
                        for i, guia in enumerate(guias_validas, 1):
                            with st.container(border=True):
                                st.markdown(f"**GUIA #{i}**")
                                
                                # ---------------------------------------------------------
                                # 1. CAPTURA DO TITULAR: ÂNCORA RÍGIDA PARA O NIP
                                # ---------------------------------------------------------
                                # Procura a palavra 'Titular', opcionalmente busca o padrão numérico colado nela, e isola o resto da linha
                                match_titular = re.search(r'(?i)T[i1]tular[\s:]*([\d\.\-]+)?\s*([^\n]+)', guia)
                                
                                nip_titular = "N/A"
                                nome_titular = "Não identificado"
                                
                                if match_titular:
                                    raw_nip = match_titular.group(1)
                                    raw_nome = match_titular.group(2)
                                    
                                    # Tratamento do NIP: Remove pontos/hifens para validação limpa
                                    if raw_nip:
                                        nip_limpo = re.sub(r'[\.\-]', '', raw_nip).strip()
                                        if len(nip_limpo) == 8:
                                            nip_titular = nip_limpo
                                    
                                    if raw_nome:
                                        nome_titular = raw_nome.strip(" -_.:")

                                # ---------------------------------------------------------
                                # 2. CAPTURA DO USUÁRIO: ISOLAMENTO POR QUEBRA DE LINHA
                                # ---------------------------------------------------------
                                # Captura a relação (Ex: FILHO, CONJUGE) e o Nome, limitando-se estritamente à linha do Usuário
                                match_usuario = re.search(r'(?i)Usu[aá]rio[\s:]*([A-Za-zÀ-Úà-ú\s\(\)]+?)[\s\-–:]+([^\n]+)', guia)
                                
                                if match_usuario:
                                    relacao_usu = match_usuario.group(1).strip(" -_.:")
                                    nome_usu = match_usuario.group(2).strip(" -_.:")
                                else:
                                    # Fallback caso a relação não use hifen/separador padrão do OCR
                                    match_usu_fallback = re.search(r'(?i)Usu[aá]rio[\s:]*([^\n]+)', guia)
                                    relacao_usu = "N/A"
                                    nome_usu = match_usu_fallback.group(1).strip(" -_.:") if match_usu_fallback else "Não identificado"

                                # Painel Visual de Identificação Militar
                                col1, col2 = st.columns(2)
                                col1.write(f"🛡️ **Titular:** {nome_titular} \n\n**NIP:** `{nip_titular}`")
                                col2.write(f"👤 **Usuário:** {nome_usu} \n\n**Relação:** `{relacao_usu}`")
                                
                                # ---------------------------------------------------------
                                # 3. CAPTURA DE PROCEDIMENTOS: ANTI-COLISÃO DE NIP
                                # ---------------------------------------------------------
                                # Captura todos os códigos de 8 dígitos seguidos por descrição
                                todos_procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–]*([^\n\r]+)', guia)
                                
                                procedimentos_filtrados = []
                                for cod, desc in todos_procedimentos:
                                    # ESTRATÉGIA ANTI-COLISÃO: Se o código de 8 dígitos localizado for IGUAL ao NIP do titular,
                                    # ou se a descrição contiver palavras de cadastro (como "Titular" ou "Usuário"), desconsidera!
                                    if cod == nip_titular:
                                        continue
                                    if re.search(r'(?i)titular|usu[áa]rio|marinha|relação', desc):
                                        continue
                                        
                                    procedimentos_filtrados.append((cod, desc.strip(" -_.")))
                                
                                # Renderização na Interface
                                if procedimentos_filtrados:
                                    st.markdown("**🩺 Procedimentos Clínicos Identificados:**")
                                    for cod, desc_limpa in procedimentos_filtrados:
                                        st.caption(f"🔹 `{cod}` - {desc_limpa}")
                                else:
                                    st.caption("⚠️ *Nenhum procedimento médico faturado nesta seção.*")
                    
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

