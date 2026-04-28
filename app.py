import streamlit as st
import pdfplumber
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import re
import base64
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Canhoteiro Pro - FBF",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==========================================
# ESTILIZAÇÃO CUSTOMIZADA (CSS)
# ==========================================
def local_css():
    st.markdown("""
        <style>
        /* Estilo Geral */
        .main {
            background-color: #f8f9fa;
        }
        
        /* Cabeçalho Customizado */
        .header-container {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            margin-bottom: 2rem;
            border-left: 5px solid #007bff;
        }
        
        .header-title {
            color: #1e293b;
            font-size: 2.5rem;
            font-weight: 800;
            margin-bottom: 0.5rem;
        }
        
        .header-subtitle {
            color: #64748b;
            font-size: 1.1rem;
        }

        /* Card de Upload */
        .stFileUploader {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            border: 2px dashed #cbd5e1;
        }

        /* Botões */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Logo Fixo */
        .logo-fixed {
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 120px;
            z-index: 1000;
            filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1));
            transition: transform 0.3s ease;
        }
        .logo-fixed:hover {
            transform: scale(1.05);
        }
        
        /* Estilo das Métricas */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem;
            color: #007bff;
        }
        </style>
    """, unsafe_allow_html=True)

local_css()

# ==========================================
# UTILITÁRIOS E LÓGICA
# ==========================================
def get_base64(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except:
        return None

def format_km(km):
    try:
        return f"{int(km):,}".replace(",", ".")
    except:
        return km

def separar_endereco_cidade(texto):
    if " - " in texto:
        partes = texto.split(" - ")
        cidade = partes[-1]
        endereco = " - ".join(partes[:-1])
        return endereco, cidade
    return texto, ""

# Inserção do Logo
logo_b64 = get_base64("logo.png")
if logo_b64:
    st.markdown(f'<img src="data:image/png;base64,{logo_b64}" class="logo-fixed">', unsafe_allow_html=True)

def gerar_pdf(dados, header_info):
    file_path = "canhoteira.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header da Tabela
    tabela_header = Table(header_info, colWidths=[350, 180])
    tabela_header.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e293b")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), 'LEFT'),
        ("FONTNAME", (0,0), (-1,0), 'Helvetica-Bold'),
        ("FONTSIZE", (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 8),
    ]))

    elements.append(tabela_header)
    elements.append(Spacer(1, 20))

    cinza_claro = colors.HexColor("#f1f5f9")
    
    for item in dados:
        bloco = [
            [f"CLIENTE: {item['cliente']}", f"Pedido: {item['pedido']}"],
            [f"END: {item['endereco']}", f"Valor: R$ {item['valor']}"],
            [f"CIDADE: {item['cidade']}", "A VISTA     PIX     BOLETO"],
            ["Assinatura: ________________________________", "DATA: ____/____/20____"]
        ]

        tabela = Table(bloco, colWidths=[350, 180])
        tabela.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),
            ("BACKGROUND", (0,0), (-1,0), cinza_claro),
            ("FONTNAME", (0,0), (-1,0), 'Helvetica-Bold'),
            ("FONTSIZE", (0,0), (-1,2), 10),
            ("FONTSIZE", (0,3), (1,3), 11),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("TOPPADDING", (0,0), (-1,-1), 10),
        ]))

        elements.append(KeepTogether([tabela, Spacer(1, 12)]))

    doc.build(elements)
    return file_path

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
st.markdown("""
    <div class="header-container">
        <div class="header-title">📦 CANHOTEIRO FBF</div>
        <div class="header-subtitle">Processamento inteligente de romaneios e geração de canhotos de entrega.</div>
    </div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Arraste ou selecione o romaneio em PDF", type="pdf", help="Apenas arquivos PDF gerados pelo sistema de romaneio.")

if uploaded_file:
    with st.spinner("Analisando romaneio..."):
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                texto = "\n".join([page.extract_text() or "" for page in pdf.pages])

            linhas = texto.split("\n")
            dados = []
            
            # Extração de Metadados
            numero, veiculo, motorista, conferente, data, hora_saida, km_inicial = "", "", "", "", "", "", ""

            for linha in linhas:
                if "CONTROLE DE ENTREGAS" in linha and "N" in linha:
                    numero = linha.split()[-1]
                if "VEICULO" in linha:
                    if "DATA:" in linha: data = linha.split("DATA:")[1].strip()
                    if "VEICULO :" in linha: veiculo = linha.split("VEICULO :")[1].split("PLACA")[0].strip()
                if "MOTORISTA" in linha:
                    motorista = linha.split("MOTORISTA :")[1].split("AJUDANTE")[0].strip()
                if "CONFERENTE" in linha:
                    conferente = linha.split("CONFERENTE:")[1].strip()
                if re.match(r"\d{2}/\d{2}/\d{4}", linha) and ":" in linha:
                    partes = linha.split()
                    if len(partes) >= 3:
                        hora_saida, km_inicial = partes[1], partes[2]

            # Extração de Pedidos
            for i, linha in enumerate(linhas):
                if re.match(r"\d+\s+\d{2}/\d{2}/\d{4}", linha):
                    partes = linha.split()
                    if len(partes) >= 6:
                        pedido, cliente, nf, valor = partes[0], " ".join(partes[2:-3]), partes[-3], partes[-2]
                        if nf == "0":
                            endereco = ""
                            for j in range(i, min(i+10, len(linhas))):
                                if "END:" in linhas[j]:
                                    endereco = linhas[j].replace("END:", "").strip()
                                    break
                            end_final, cidade = separar_endereco_cidade(endereco)
                            dados.append({"pedido": pedido, "cliente": cliente, "endereco": end_final, "cidade": cidade, "valor": valor})

            # Exibição de Resumo
            with col2:
                st.markdown("### Resumo da Carga")
                st.metric("Total de Entregas", len(dados))
                st.info(f"**Motorista:** {motorista}\n\n**Veículo:** {veiculo}")

            # Ações
            st.divider()
            
            # Preview dos Dados em Tabela Bonita
            with st.expander("🔍 Visualizar lista de entregas extraídas"):
                st.table(dados)

            if st.button("🚀 Gerar PDF de Canhotos"):
                header_info = [
                    ["CONTROLE DE ENTREGAS", f"Nº {numero}"],
                    [f"VEÍCULO: {veiculo}", f"DATA: {data}"],
                    [f"MOTORISTA: {motorista}", f"CONFERENTE: {conferente}"],
                    [f"HORA SAÍDA: {hora_saida}", f"KM INICIAL: {format_km(km_inicial)}"],
                    ["HORA CHEGADA: ____________________", "KM FINAL: ____________________"],
                    [f"TOTAL ENTREGAS: {len(dados)}", ""],
                    ["OCORRÊNCIAS:", ""],
                ]
                
                pdf_path = gerar_pdf(dados, header_info)
                file_name = f"Canhoteira_{data.replace('/', '-')}_N_{numero}.pdf"
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 BAIXAR PDF GERADO",
                        data=f,
                        file_name=file_name,
                        mime="application/pdf",
                        use_container_width=True
                    )
                st.balloons()

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")
else:
    st.markdown("""
        <div style="text-align: center; padding: 3rem; color: #64748b; border: 2px dashed #cbd5e1; border-radius: 15px;">
            <p style="font-size: 1.5rem;">Aguardando o upload do romaneio...</p>
            <p>Os dados serão processados automaticamente após o envio.</p>
        </div>
    """, unsafe_allow_html=True)
