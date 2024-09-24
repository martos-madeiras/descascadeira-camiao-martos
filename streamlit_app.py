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
    background-color: rgba(186, 186, 186);
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

def ler_ficheiro_txt(file):
    dados = []
    content = file.getvalue().decode('utf-8')
    for linha in content.split('\n'):
        linha = linha.strip()
        if linha:
            colunas = linha.split('~')
            dados.append(colunas)
    return dados

def analyze_data(dados_lidos, key_suffix):
    nomes_colunas = ['Data', 'Hora', 'Série', 'N.º Tronco', 'D min', 'D méd', 'D máx', 'Comprimento', 'a','Box', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'q', 'w','e','r','t','y','u','i','o','p']

    df = pd.DataFrame(dados_lidos, columns=nomes_colunas[:len(dados_lidos[0])])
    df.index = df.index + 1
    df['Box'] = pd.to_numeric(df['Box'], errors='coerce')

    st.dataframe(df)

    total_ntronco = df['N.º Tronco'].count()

    lst_horas = pd.to_datetime(df['Hora'], format='%H:%M:%S')

    total_nsegundos = (lst_horas[total_ntronco] - lst_horas[1]).total_seconds()-3600
    total_nhoras, remainder = divmod(total_nsegundos, 3600)
    total_nminutos, total_nsegundos = divmod(remainder, 60)

    total_nhoras = int(total_nhoras)
    total_nminutos = int(total_nminutos)
    total_nsegundos = int(total_nsegundos)
    tempo_total_min = (total_nhoras * 60) + total_nminutos +  (total_nsegundos / 60)
    quantidade_min = total_ntronco /  tempo_total_min

    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        data_analise = df['Data'].max()
        data_analise_str = data_analise.strftime('%Y-%m-%d') if pd.notna(data_analise) else 'Data não disponível'
    else:
        data_analise_str = 'Data não disponível'
    
    cor_texto = "rgb(194, 97, 30)"
    st.markdown(f'**Periodo da análise**: <span style="color:{cor_texto}; font-weight:bold;">{data_analise_str}</span>', unsafe_allow_html=True)
    st.markdown(f'**Quantidade Produzida**: <span style="color:{cor_texto}; font-weight:bold;">{total_ntronco}</span>', unsafe_allow_html=True)
    st.markdown(f'**Tempo total de trabalho**: <span style="color:{cor_texto}; font-weight:bold;">{total_nhoras}h:{total_nminutos}min:{total_nsegundos}seg</span>', unsafe_allow_html=True)
    st.markdown(f'**Quantidade por minuto**: <span style="color:{cor_texto}; font-weight:bold;">{quantidade_min:.2f} troncos/minuto</span>', unsafe_allow_html=True)
   
    box_descriptions = {
        1: "2200 M",
        2: "metal",
        3: "2200 G",
        4: "2200 F",
        5: "2500 M",
        6: "2500 F",
        7: "2500 G",
        8: "2650",
        9: "2800 G",
        10: "2800 F/M",
        11: "3100 G",
        12: "3100 F/M",
        13: "Outros",
    }
    contagem = df['Box'].value_counts().sort_index()
    contagem_df = contagem.to_frame().reset_index()
    contagem_df.columns = ['Box', 'Quantidade']

    contagem_df['Descrição'] = contagem_df['Box'].map(box_descriptions).fillna('Descrição não disponível')
    
    st.subheader("N.º de Troncos por cada Box:")
    st.dataframe(contagem_df.sort_values(by='Box'))

    box_filtrar = st.number_input("Apresentar registos detalhados para a Box n.º :", min_value=0, max_value=13, step=1, key=f"box_filter_{key_suffix}")
    
    troncos_box_filtrados = df[df['Box'] == box_filtrar]
    if not troncos_box_filtrados.empty:
        st.dataframe(troncos_box_filtrados)
    elif box_filtrar != 0:
        st.write(f"Nenhum tronco encontrado na Box {box_filtrar}.")

    return df

st.title('Dashboard - Descascadeira')

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
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index_label='Linha', sheet_name='Sheet1')
        excel_data = output.getvalue()
        st.download_button(
            label="Download Excel",
            data=excel_data,
            file_name=f"{uploaded_file.name.replace('.txt', '.xlsx')}",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_new_file"
        )

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
