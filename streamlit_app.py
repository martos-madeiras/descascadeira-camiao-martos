import streamlit as st
import pandas as pd
import io
import os
import json
import tracemalloc

tracemalloc.start()

page_bg_img = '''
<style>
.stApp {
    background-image: url("https://i.imgur.com/aCy6SYL.jpeg");
    background-size: cover;
    background-attachment: scroll;
    padding: 0;
    margin: 0;
}

.main {
    background-color: rgba(186, 186, 50);
    padding: 20px; 
    border-radius: 10px;
    margin: 0 auto;
    max-width: 60%; 
}

body {
    margin: 0;
    padding: 0;
}
</style>
'''
st.markdown(page_bg_img, unsafe_allow_html=True)
st.markdown('<div class="main">', unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def load_existing_files():
    if os.path.exists('archive.json'):
        try:
            with open('archive.json', 'r') as f:
                content = f.read()
                return json.loads(content) if content else {}
        except json.JSONDecodeError:
            return {}
    return {}

def save_file_info(filename, data):
    existing_files = load_existing_files()
    existing_files[filename] = {
        'data': data
    }
    with open('archive.json', 'w') as f:
        json.dump(existing_files, f)
    load_existing_files.clear()

def delete_file(filename):
    existing_files = load_existing_files()
    if filename in existing_files:
        del existing_files[filename]
        with open('archive.json', 'w') as f:
            json.dump(existing_files, f)
        load_existing_files.clear()
        return True
    return False

# Função atualizada para ler ficheiros com novo formato
def ler_ficheiro_txt(file):
    try:
        # Tentar ler o conteúdo com 'utf-8' primeiro
        try:
            content = file.getvalue().decode('utf-8')
        except UnicodeDecodeError:
            # Se falhar, tentar com 'ISO-8859-1' ou 'Windows-1252'
            content = file.getvalue().decode('ISO-8859-1')

        # Inicializar variáveis
        dados_troncos = []
        metadados = {}

        linhas = content.split('\n')

        # Primeira linha: datas e horas
        primeira_linha = linhas[0].strip().split('~')
        data_inicio, hora_inicio, data_fim, hora_fim = primeira_linha

        # Segunda linha: valores numéricos
        segunda_linha = linhas[1].strip().split('~')
        valor_1, valor_2 = segunda_linha[:2]  # Aqui temos dois valores

        # Linhas de troncos (a partir da terceira linha até encontrar metadados)
        for linha in linhas[2:]:
            linha = linha.strip()
            if not linha or ":" in linha:
                # Parar ao encontrar uma linha que contém metadados (contém ":")
                break
            colunas = linha.split('~')
            if len(colunas) >= 3:
                dados_troncos.append(colunas[:3])

        # Metadados (linhas com ":")
        for linha in linhas[len(dados_troncos) + 2:]:
            if ":" in linha:
                chave, valor = linha.split(":")
                metadados[chave.strip()] = valor.strip()

        return {
            "data_inicio": data_inicio,
            "hora_inicio": hora_inicio,
            "data_fim": data_fim,
            "hora_fim": hora_fim,
            "valor_1": valor_1,
            "valor_2": valor_2,
            "dados_troncos": dados_troncos,
            "metadados": metadados
        }

    except Exception as e:
        st.error(f"Erro ao ler o ficheiro: {e}")
        return None
# Função de análise adaptada
def analyze_data(dados_lidos, key_suffix):
    # Exibir informações de data e hora
    st.write(f"**Data de Início:** {dados_lidos['data_inicio']} {dados_lidos['hora_inicio']}")
    st.write(f"**Data de Fim:** {dados_lidos['data_fim']} {dados_lidos['hora_fim']}")
    
    # Exibir os dois valores adicionais
    total_troncos = df_troncos['Quantidade'].astype(int).sum()
    st.write(f"**Qtd.M3 Total Toros:** {dados_lidos['valor_2']}")

    # Converter dados dos troncos em DataFrame
    colunas_troncos = ['BOX', 'Quantidade', 'M3']
    df_troncos = pd.DataFrame(dados_lidos['dados_troncos'], columns=colunas_troncos)

    # Exibir DataFrame dos troncos
    st.subheader("Dados dos Troncos")
    st.dataframe(df_troncos)


# Estrutura de tabs e funcionalidade
st.title('Dashboard Descascadeira-Camião')

tab1, tab2 = st.tabs(["Carregar Novo Ficheiro", "Arquivo de Ficheiros"])

with tab1:
    st.header("Upload do Ficheiro")
    
    uploaded_file = st.file_uploader("Formatos suportados: TXT", type="txt", key="uploader")
    
    if uploaded_file is not None:
        dados_lidos = ler_ficheiro_txt(uploaded_file)
        save_file_info(uploaded_file.name, dados_lidos)
        st.success(f"Dados analisados e arquivados como {uploaded_file.name}")
        
        st.subheader(f"Análise do arquivo carregado: {uploaded_file.name}")
        df = analyze_data(dados_lidos, "upload")

with tab2:
    st.header("Arquivos")
    existing_files = load_existing_files()
    
    if existing_files:
        selected_file = st.selectbox(
            "Selecione um ficheiro do arquivo:",
            list(existing_files.keys()),
            key="file_selector"
        )
    
        if st.button("🗑️ Eliminar Registo", key="delete_button"):
            if delete_file(selected_file):
                st.success(f"Arquivo {selected_file} excluído com sucesso.")
                st.rerun()
            else:
                st.error("Erro ao excluir o arquivo.")

        if selected_file:
            try:
                dados_lidos = existing_files[selected_file]['data']
                st.subheader(f"Análise do {selected_file}")
                df = analyze_data(dados_lidos, "archive")
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index_label='Linha', sheet_name='Sheet1')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"{selected_file.replace('.txt', '.xlsx')}",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_archive_file_{selected_file}"
                )
            except Exception as e:
                st.error(f"Erro ao carregar dados do arquivo: {str(e)}")
    else:
        st.write("Sem dados registados para mostrar. Por favor, envie um novo ficheiro.")
