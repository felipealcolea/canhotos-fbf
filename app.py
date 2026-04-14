import streamlit as st
import pdfplumber
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import re

st.title("📦 CANHOTOS FBF")

uploaded_file = st.file_uploader("Envie o romaneio (PDF)", type="pdf")

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

def gerar_pdf(dados, header):
    file_path = "canhoteira.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []

    tabela_header = Table(header, colWidths=[360, 140])
    tabela_header.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("BACKGROUND", (0,1), (-1,1), colors.lightgrey),
        ("FONTSIZE", (0,0), (-1,-1), 12),
    ]))

    elements.append(tabela_header)
    elements.append(Spacer(1, 12))

    cinza = colors.Color(201/255, 201/255, 201/255)

    for item in dados:
        bloco = [
            [f"CLIENTE: {item['cliente']}", f"Pedido: {item['pedido']}"],
            [f"END: {item['endereco']}", f"Valor: R$ {item['valor']}"],
            [f"CIDADE: {item['cidade']}", "A VISTA     PIX     BOLETO"],
            ["Assinatura: ________________________________", "DATA: ____/____/20____"]
        ]

        tabela = Table(bloco, colWidths=[350, 200])
        tabela.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.5, colors.black),

            # 🔥 LINHA CINZA NO CLIENTE + PEDIDO
            ("BACKGROUND", (0,0), (-1,0), cinza),

            ("FONTSIZE", (0,0), (-1,2), 12),
            ("FONTSIZE", (0,3), (1,3), 13),
        ]))

        elements.append(KeepTogether([tabela, Spacer(1, 10)]))

    doc.build(elements)
    return file_path

if uploaded_file is not None:
    st.success("Arquivo carregado com sucesso!")

    with pdfplumber.open(uploaded_file) as pdf:
        texto = ""
        for page in pdf.pages:
            conteudo = page.extract_text()
            if conteudo:
                texto += conteudo + "\n"

    linhas = texto.split("\n")

    dados = []

    veiculo = ""
    motorista = ""
    conferente = ""
    data = ""
    hora_saida = ""
    km_inicial = ""
    numero = ""

    for linha in linhas:

        if "CONTROLE DE ENTREGAS" in linha and "N" in linha:
            partes = linha.split()
            numero = partes[-1]

        if "VEICULO" in linha:
            if "DATA:" in linha:
                data = linha.split("DATA:")[1].strip()
            if "VEICULO :" in linha:
                veiculo = linha.split("VEICULO :")[1].split("PLACA")[0].strip()

        if "MOTORISTA" in linha:
            motorista = linha.split("MOTORISTA :")[1].split("AJUDANTE")[0].strip()

        if "CONFERENTE" in linha:
            conferente = linha.split("CONFERENTE:")[1].strip()

        if re.match(r"\d{2}/\d{2}/\d{4}", linha) and ":" in linha:
            partes = linha.split()
            if len(partes) >= 3:
                hora_saida = partes[1]
                km_inicial = partes[2]

    for i, linha in enumerate(linhas):
        if re.match(r"\d+\s+\d{2}/\d{2}/\d{4}", linha):
            partes = linha.split()

            if len(partes) >= 6:
                pedido = partes[0]
                cliente = " ".join(partes[2:-3])
                nf = partes[-3]
                valor = partes[-2]

                if nf == "0":
                    endereco = ""

                    for j in range(i, i+5):
                        if j < len(linhas) and "END:" in linhas[j]:
                            endereco = linhas[j].replace("END:", "").strip()
                            break

                    endereco_final, cidade = separar_endereco_cidade(endereco)

                    dados.append({
                        "pedido": pedido,
                        "cliente": cliente,
                        "endereco": endereco_final,
                        "cidade": cidade,
                        "valor": valor
                    })

    header = [
        ["CONTROLE DE ENTREGAS", f"Nº {numero}"],
        [f"VEÍCULO: {veiculo}", f"DATA: {data}"],
        [f"MOTORISTA: {motorista}", f"CONFERENTE: {conferente}"],
        [f"HORA SAÍDA: {hora_saida}", f"KM INICIAL: {format_km(km_inicial)}"],
        ["HORA CHEGADA: ____________________", "KM FINAL: ____________________"],
        [f"TOTAL ENTREGAS: {len(dados)}", ""],
        ["OCORRÊNCIAS:", ""],
    ]

    if st.button("Gerar Canhoteira"):
        file_path = gerar_pdf(dados, header)

        with open(file_path, "rb") as f:
            st.download_button("📥 Baixar Canhoteira", f, file_name="canhoteira.pdf")

else:
    st.info("Aguardando envio do romaneio...")
