import streamlit as st
import pytesseract
import re
import pandas as pd
import io
from pdf2image import convert_from_bytes

# Configuração de segurança da página
st.set_page_config(page_title="SISAFA - Processador Inteligente", layout="wide")

st.title("⚓ SISAFA - Processador Inteligente de PDFs Escaneados")
st.write("Projetado para ler faturas sem padrão de credenciadas através de processamento flexível.")

# --- FUNÇÕES TÁTICAS DE EXTRAÇÃO INTELIGENTE (REGEX) ---
def extrair_dados_flexivel(texto):
    """
    Vasculha o texto extraído pelo OCR buscando padrões comuns de faturas.
    Não depende de colunas fixas ou cabeçalhos bonitos.
    """
    linhas = texto.split('\n')
    dados = []
    
    # Regex flexíveis para os dados militares e faturas
    regex_valor = r"(?:r\$\s*)?(\d{1,3}(?:\.\d{3})*(?:,\d{2}))"  # Pega valores como 1.250,00 ou 450,50
    regex_nip = r"\b(\d{2}\.\d{4}\.\d{2}|\d{8})\b"               # Pega NIPs formatados ou sequências de 8 dígitos
    
    for idx, linha in enumerate(linhas):
        linha_limpa = linha.lower().strip()
        
        # Ignora linhas sabidamente vazias ou de rodapé inútil
        if not linha_limpa or len(linha_limpa) < 5:
            continue
            
        # Tenta identificar dados na linha
        nips_encontrados = re.findall(regex_nip, linha)
        valores_encontrados = re.findall(regex_valor, linha_limpa)
        
        # Heurística: Se achar um NIP ou termos chaves e valores monetários na mesma linha
        if nips_encontrados and valores_encontrados:
            nip = nips_encontrados[0]
            # Pega o último valor monetário da linha (que costuma ser o valor do serviço/total)
            valor = valores_encontrados[-1] 
            
            # Tenta chutar um procedimento olhando o texto ao redor
            procedimento = "Procedimento Não Identificado"
            termos_procedimento = re.sub(regex_nip, "", linha) # remove o NIP
            termos_procedimento = re.sub(regex_valor, "", termos_procedimento, flags=re.IGNORECASE) # remove valores
            termos_procedimento = termos_procedimento.replace("r$", "").strip()
            
            if len(termos_procedimento) > 5:
                procedimento = termos_procedimento[:50] # Limita tamanho do texto
                
            dados.append({
                "Identificador (NIP/CPF)": nip,
                "Descrição/Procedimento": procedimento.upper(),
                "Valor Capturado": valor
            })
            
        # Caso não ache NIP, mas ache uma linha de "Total" com valor
        elif any(termo in linha_limpa for termo in ["total", "soma", "subtotal"]) and valores_encontrados:
            dados.append({
                "Identificador (NIP/CPF)": "TOTAL DA FATURA",
                "Descrição/Procedimento": "VALOR AGREGADO DETECTADO",
                "Valor Capturado": valores_encontrados[-1]
            })
            
    # Se o regex não pegou nada, gera pelo menos uma linha genérica pro usuário preencher
    if not dados:
        dados.append({
            "Identificador (NIP/CPF)": "Revisar Manualmente",
            "Descrição/Procedimento": "Não foi possível extrair dados estruturados automaticamente.",
            "Valor Capturado": "0,00"
        })
        
    return pd.DataFrame(dados)

# --- UPLOAD E EXECUÇÃO ---
pdf_carregado = st.file_uploader("Arraste ou selecione seu PDF escaneado", type=["pdf"])

if pdf_carregado is not None:
    st.success("PDF carregado com sucesso na memória!")
    
    with st.spinner("Convertendo PDF em imagens e aplicando OCR Inteligente..."):
        try:
            # 1. Converte em imagens
            pdf_bytes = pdf_carregado.read()
            paginas = convert_from_bytes(pdf_bytes)
            
            texto_completo = ""
            for imagem_pagina in paginas:
                # OCR em português
                texto_completo += pytesseract.image_to_string(imagem_pagina, lang='por') + "\n"
            
            st.subheader("📝 Dados Extraídos e Estruturados")
            st.info("Abaixo está a planilha gerada pelo algoritmo. Você pode clicar nas células para corrigir qualquer erro de leitura do OCR:")
            
            # 2. Processa o texto com a lógica flexível
            df_extraido = extrair_dados_flexivel(texto_completo)
            
            # 3. Exibe o editor de dados interativo (O usuário é o validador final!)
            df_confirmado = st.data_editor(df_extraido, num_rows="dynamic", use_container_width=True)
            
            # --- ÁREA DE DOWNLOAD SEGURO ---
            st.subheader("💾 Exportação de Resultados")
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                df_confirmado.to_excel(writer, index=False, sheet_name='SISAFA_Processado')
            
            buffer.seek(0)
            
            st.download_button(
                label="📥 Baixar Planilha Consolidada",
                data=buffer,
                file_name="fatura_sisafa_corrigida.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Erro no processamento do OCR: {e}")