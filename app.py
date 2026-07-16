import streamlit as st
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

# Configuração da página
st.set_page_config(page_title="SISAFA - Leitor OCR", layout="wide")

st.title("⚓ SISAFA - Inspetor OCR (PDFs Escaneados)")
st.write("Suba um arquivo PDF escaneado para que o motor OCR converta em texto editável.")

# Upload do arquivo para a RAM
pdf_carregado = st.file_uploader("Arraste ou selecione seu PDF escaneado", type=["pdf"])

if pdf_carregado is not None:
    st.success("PDF carregado com sucesso em memória!")
    
    with st.spinner("Convertendo páginas em imagens e aplicando OCR (pode demorar alguns segundos)..."):
        try:
            # 1. Converte os bytes do PDF diretamente em imagens na memória RAM
            pdf_bytes = pdf_carregado.read()
            paginas = convert_from_bytes(pdf_bytes)
            num_paginas = len(paginas)
            
            st.metric(label="Total de Páginas Detectadas", value=num_paginas)
            
            # 2. Varre cada página aplicando o Tesseract OCR
            for i, imagem_pagina in enumerate(paginas):
                st.subheader(f"📄 Página {i + 1}")
                
                # Executa o OCR em português ('por')
                texto_extraido = pytesseract.image_to_string(imagem_pagina, lang='por')
                
                if texto_extraido.strip():
                    st.text_area(
                        label=f"Texto extraído via OCR (pág. {i + 1})",
                        value=texto_extraido,
                        height=350,
                        key=f"pag_ocr_{i}"
                    )
                else:
                    st.warning(f"O motor OCR não conseguiu identificar nenhum texto na página {i + 1}.")
                    
        except Exception as e:
            st.error(f"Erro no processamento de OCR: {e}")
            st.info("Dica: Verifique se as dependências do sistema operacional foram instaladas corretamente no servidor.")
