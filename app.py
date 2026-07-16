import streamlit as st
import pytesseract
import re
from pdf2image import convert_from_bytes
import os # Para verificar a existência dos arquivos de imagem

# Configuração de segurança da página
st.set_page_config(page_title="⚓SILASCA NAVAL⚓", layout="wide")

# --- 1. CABEÇALHO VISUAL (LOGO CENTRALIZADO NO TOPO) ---
# As colunas laterais (2.5) espremem a coluna central (1) para o logo não ficar gigante
col_logo_1, col_logo_2, col_logo_3 = st.columns([2.5, 1, 2.5]) 

with col_logo_2:
    if os.path.exists("LOGO_SILASCA.png"):
        # use_container_width=True fará a imagem respeitar exatamente o tamanho da coluna 2
        st.image("LOGO_SILASCA.png", use_container_width=True)
    else:
        st.warning("⚠️ Arquivo 'LOGO_SILASCA.png' não encontrado no repositório.")


# --- 2. TÍTULOS E TEXTOS DO SISTEMA ---
st.markdown("<h1 style='text-align: center;'>⚓ SISAFA - Analisador e Interpretador de OCR</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Foco absoluto na leitura, interpretação e busca de termos dentro do texto bruto extraído de faturas escaneadas.</p>", unsafe_allow_html=True)
st.write("---") # Linha divisória







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


# --- 4. RODAPÉ VISUAL (SLOGAN CENTRALIZADO NO BAIXO) ---
st.write("---") # Linha divisória antes do rodapé
# Espaçador vertical para empurrar o slogan para baixo
st.markdown("<br><br>", unsafe_allow_html=True) 

# Coluna central ligeiramente maior (2) para acomodar o texto do slogan
col_slogan_1, col_slogan_2, col_slogan_3 = st.columns([1.5, 2, 1.5])

with col_slogan_2:
    if os.path.exists("slogan.png"):
        st.image("slogan.png", use_container_width=True)
    else:
        st.warning("⚠️ Arquivo 'slogan.png' não encontrado no repositório.")