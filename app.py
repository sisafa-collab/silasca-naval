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
            f'style="position: fixed; bottom: 20px; right: 20px; width: 300px; z-index: 9999;">', 
            unsafe_allow_html=True
        )

# --- 2. LOGO CENTRALIZADO NO TOPO (AGORA MAIOR) ---
# Mudamos a calibração das colunas [1, 1.2, 1] para expandir o tamanho do logo central
col_logo_1, col_logo_2, col_logo_3 = st.columns([1, 1.2, 1]) 

with col_logo_2:
    if os.path.exists("LOGO_SILASCA.png"):
        st.image("LOGO_SILASCA.png", use_container_width=True)
    else:
        st.warning("⚠️ Arquivo 'LOGO_SILASCA.png' não encontrado no repositório.")

# --- 3. TÍTULOS E TEXTOS DO SISTEMA (CORRIGIDOS) ---
st.markdown("""
    <div style="text-align: center; padding: 20px; border-top: 2px solid #2e6b54; margin-top: 10px; background-color: rgba(46, 107, 84, 0.05); border-radius: 0 0 15px 15px;">
        <p style="
            color: #2e6b54; 
            font-weight: 900; 
            font-size: 2rem; 
            letter-spacing: 3px; 
            line-height: 1.2;
            text-shadow: 0 0 8px rgba(46, 107, 84, 0.3);
            margin-bottom: 8px;
        ">
            Analisador e Interpretador de Faturas
        </p>
        
        <p style="
            color: #4c4955; 
            font-size: 1.15rem; 
            font-weight: 700; 
            margin-top: 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        ">
            Foco absoluto na leitura e interpretação de faturas escaneadas.<br>
            <span style="color: #bc3c31;">🚨 Confira os dados antes de baixar as planilhas! 🚨</span>
        </p>
    </div>
""", unsafe_allow_html=True)

# Upload do arquivo para a RAM
pdf_carregado = st.file_uploader("Suba a fatura escaneada em PDF", type=["pdf"])

if pdf_carregado is not None:
    st.success("PDF carregado com sucesso na memória!")
    
    with st.spinner("Convertendo páginas e executando leitura por OCR..."):
        try:
            # 1. Converte os bytes do PDF em imagens na memória
            pdf_bytes = pdf_carregado.read()
            paginas = convert_from_bytes(pdf_bytes)
            num_paginas = len(paginas)
            
            # Unifica o texto extraído de todas as páginas
            texto_completo = ""
            for idx, imagem_pagina in enumerate(paginas):
                texto_pagina = pytesseract.image_to_string(imagem_pagina, lang='por')
                texto_completo += f"\n--- INÍCIO DA PÁGINA {idx + 1} ---\n{texto_pagina}\n--- FIM DA PÁGINA {idx + 1} ---\n"
            
            st.info("💡 Processamento concluído. Use as ferramentas abaixo para interpretar a fatura.")
            
            # --- PAINEL DE ANÁLISE INTERATIVA ---
            aba_bruta, aba_filtros = st.tabs(["📄 Texto Bruto Completo", "🔍 Buscador e Capturador Inteligente"])
            
            # ABA 1: TEXTO BRUTO DO DOCUMENTO (Cabeçalhos, tabelas quebradas, parágrafos)
            with aba_bruta:
                st.subheader("Visualização Integral do Documento")
                st.write("Aqui está o texto exatamente na ordem física em que o OCR conseguiu ler:")
                st.text_area(
                    label="Conteúdo extraído", 
                    value=texto_completo, 
                    height=500,
                    key="texto_bruto_fatura"
                )
                
            # ABA 2: BUSCADOR E CAPTURADOR (Para interpretar dados soltos)
            with aba_filtros:
                st.subheader("Interpretação e Filtro de Informações")
                st.write("Filtre o texto bruto para localizar termos cruciais sem precisar varrer o documento inteiro com os olhos.")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 🎯 Captura Automática de Padrões")
                    
                    # Capturador de NIP/CPF
                    nips_ou_cpfs = re.findall(r"\b(?:\d{2}\.\d{4}\.\d{2}|\d{3}\.\d{3}\.\d{3}-\d{2}|\d{8}|\d{11})\b", texto_completo)
                    if nips_ou_cpfs:
                        st.success(f"Identificadores localizados ({len(nips_ou_cpfs)}):")
                        st.write(list(set(nips_ou_cpfs))) # Remove duplicatas na exibição
                    else:
                        st.warning("Nenhum padrão de NIP ou CPF foi identificado automaticamente.")
                        
                    # Capturador de Valores Monetários
                    valores = re.findall(r"(?:R\$\s*)?\b\d{1,3}(?:\.\d{3})*,\d{2}\b", texto_completo, re.IGNORECASE)
                    if valores:
                        st.success(f"Valores em Reais localizados ({len(valores)}):")
                        st.write(list(set(valores)))
                    else:
                        st.warning("Nenhum valor no formato 'R$ XX,XX' foi identificado automaticamente.")
                        
                with col2:
                    st.markdown("#### 🔎 Busca Manual por Palavra-Chave")
                    termo_busca = st.text_input("Digite o termo que quer encontrar (ex: 'NUP', 'fatura', 'hospital', o nome de um exame...):")
                    
                    if termo_busca:
                        linhas = texto_completo.split('\n')
                        linhas_encontradas = [l.strip() for l in linhas if termo_busca.lower() in l.lower()]
                        
                        if linhas_encontradas:
                            st.success(f"Encontradas {len(linhas_encontradas)} ocorrências:")
                            for linha in linhas_encontradas:
                                st.code(linha, language="text")
                        else:
                            st.warning(f"O termo '{termo_busca}' não foi encontrado no documento.")
                            
        except Exception as e:
            st.error(f"Erro ao ler e processar o PDF: {e}")

