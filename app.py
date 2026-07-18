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
                    # 🎯 SISAFA NAVAL v4: EXTRAÇÃO ZONAL (BASEADO NO LAYOUT FÍSICO DA GUIA)
                    # =========================================================

                    # 1. CORTA O PDF EM GUIAS
                    blocos_guia = re.split(r'(?i)MARINHA\s+DO\s+BRASIL', texto_completo)

                    # Filtra apenas blocos que possuam a seção "DADOS DO USUÁRIO"
                    guias_validas = [b for b in blocos_guia if re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO', b)]

                    if guias_validas:
                        st.markdown(f"### 📑 Identificadas {len(guias_validas)} Guia(s) de Apresentação")
                        
                        for i, guia in enumerate(guias_validas, 1):
                            with st.container(border=True):
                                st.markdown(f"**GUIA #{i}**")
                                
                                # Variáveis em branco
                                nome_usu, nip_usu, vinculo_usu, tipo_usu = "N/A", "N/A", "N/A", "N/A"
                                
                                # =========================================================
                                # ZONA 1: DADOS DO USUÁRIO
                                # Captura tudo entre "DADOS DO USUÁRIO" e a próxima grande seção
                                # =========================================================
                                bloco_usuario = re.search(r'(?i)DADOS\s+DO\s+USU[ÁA]RIO(.*?)(?=DADOS\s+DO\s+ENCAMINHAMENTO|MOTIVO\s+DO\s+ENCAMINHAMENTO|$)', guia, re.DOTALL)
                                
                                if bloco_usuario:
                                    txt_usr = bloco_usuario.group(1) # Aqui dentro só tem lixo e dados do usuário
                                    
                                    # Caça NIP (Exatos 8 dígitos após a palavra NIP, ignorando quebras de linha e espaços)
                                    match_nip = re.search(r'(?i)NIP[\s:\|]*([\d]{8})', txt_usr)
                                    if match_nip: nip_usu = match_nip.group(1)
                                    
                                    # Caça Vínculo (Busca explicitamente TITULAR ou DEPENDENTE)
                                    match_vinc = re.search(r'(?i)(TITULAR|DEPENDENTE)', txt_usr)
                                    if match_vinc: vinculo_usu = match_vinc.group(1).upper()
                                    
                                    # Caça Tipo (Busca DIRETO ou INDIRETO)
                                    match_tipo = re.search(r'(?i)(DIRETO|INDIRETO)', txt_usr)
                                    if match_tipo: tipo_usu = match_tipo.group(1).upper()
                                    
                                    # Caça Nome (Pega tudo entre "Nome:" e a próxima palavra-chave "NIP" ou "Posto" ou "Vínculo")
                                    # O \s* limpa os espaços invisíveis nas bordas
                                    match_nome = re.search(r'(?i)Nome[\s:\|]+(.*?)(?=\s+NIP|\s+Posto|\s+V[íi]nculo|\n)', txt_usr, re.IGNORECASE)
                                    if match_nome: 
                                        # Limpa traços e restos do OCR
                                        nome_usu = re.sub(r'[_\|]+', '', match_nome.group(1)).strip()

                                # --- Renderização do Painel Pessoal ---
                                col1, col2 = st.columns(2)
                                col1.write(f"👤 **Nome:** {nome_usu} \n\n**NIP:** `{nip_usu}`")
                                col2.write(f"🔗 **Vínculo:** `{vinculo_usu}` \n\n**Tipo:** `{tipo_usu}`")
                                
                                # =========================================================
                                # ZONA 2: MOTIVO DO ENCAMINHAMENTO (PROCEDIMENTOS)
                                # =========================================================
                                bloco_motivo = re.search(r'(?i)MOTIVO\s+DO\s+ENCAMINHAMENTO(.*?)(?=AUTORIZA[CÇ][AÃ]O|ASSINATURA|TOTAL|$)', guia, re.DOTALL)
                                
                                if bloco_motivo:
                                    txt_mot = bloco_motivo.group(1) # Aqui dentro só tem a tabela de exames
                                    
                                    # Procura números de 8 dígitos e o texto subsequente, apenas DENTRO deste bloco
                                    procedimentos = re.findall(r'\b(\d{8})\b[\s\.\-–\|]*([^\n\r]+)', txt_mot)
                                    
                                    if procedimentos:
                                        st.markdown("**🩺 Exames / Procedimentos:**")
                                        for cod, desc in procedimentos:
                                            # Se por um milagre o OCR botou o NIP lá embaixo, a gente bloqueia
                                            if cod == nip_usu: continue 
                                            desc_limpa = re.sub(r'[_\|]+', '', desc).strip()
                                            st.caption(f"🔹 `{cod}` - {desc_limpa}")
                                    else:
                                        st.caption("⚠️ *Nenhum exame identificado nesta zona.*")
                                else:
                                    st.caption("⚠️ *Bloco 'Motivo do Encaminhamento' não localizado.*")
                    
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

