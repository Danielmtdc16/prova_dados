import streamlit as st
import pandas as pd
import json, os

ARQ = "embalagens.json"

df = pd.read_csv('dados.csv', sep=';', decimal=',')
df.set_index('Codigo', inplace=True)
for coluna in ['Altura', 'Largura', 'Profundidade', 'Quantidade']:
    df[coluna] = pd.to_numeric(df[coluna], errors='coerce')
    df[coluna] = df[coluna].round(2)

df['volume_produto'] = (df['Altura'] * df['Largura'] * df['Profundidade']).round(2)
df['volume_total_produto'] = (df['volume_produto'] * df['Quantidade']).round(2)

def carregar():
    if os.path.exists(ARQ):
        return json.load(open(ARQ))
    return [
        {'nome': 'Caixa A', 'altura': 20, 'largura': 15, 'profundidade': 8},
        {'nome': 'Caixa B', 'altura': 30, 'largura': 25, 'profundidade': 40},
        {'nome': 'Caixa C', 'altura': 20, 'largura': 25, 'profundidade': 15},
        {'nome': 'Caixa D', 'altura': 8, 'largura': 8, 'profundidade': 4},
    ]

def salvar(lista):
    json.dump(lista, open(ARQ, "w"), indent=2)

def verificar_se_produto_cabe(linha):
    if pd.isna(linha['Altura']) or pd.isna(linha['Largura']) or pd.isna(linha['Profundidade']):
        return False
    if linha['Altura'] <= 0 or linha['Largura'] <= 0 or linha['Profundidade'] <= 0:
        return False

    for i, c in df_caixas_embalagem.iterrows():
        if (
                linha['Altura'] <= c['altura'] and
                linha['Largura'] <= c['largura'] and
                linha['Profundidade'] <= c['profundidade']
        ):
            return True
    return False

def procurar_embalagem(cod_pro, qtd):
    produto = df.loc[cod_pro]
    vol_total = produto["volume_produto"] * qtd
    for i, c in df_caixas_embalagem.sort_values("volume total").iterrows():
        dims_ok = (
                produto["Altura"] <= c["altura"] and
                produto["Largura"] <= c["largura"] and
                produto["Profundidade"] <= c["profundidade"]
        )
        vol_ok = vol_total <= c["volume total"]

        if dims_ok and vol_ok:
            return c
    return None


if "caixas" not in st.session_state:
    st.session_state.caixas = carregar()

df_caixas_embalagem = pd.DataFrame(st.session_state.caixas)
df_caixas_embalagem['volume total'] = (
        df_caixas_embalagem['altura'] *
        df_caixas_embalagem['largura']*
        df_caixas_embalagem['profundidade']
)

paginas = {
    '01': 'Ver todos os dados',
    '02': 'Embalagem Adequada'
}

pagina = st.sidebar.selectbox('Seleciona uma página', [paginas['01'], paginas['02']])

if pagina == paginas['01']:
    st.title("Análise de Dados de Estoque")
    linhas = st.slider("Selecione quantas linha deseja ver da base de dados", 100, 5000, 100, step=100)
    st.dataframe(df.head(linhas))

    st.metric('Quantidade de Produtos distintos', df['Produto'].nunique())

    df_dados_estranhos = df[
        df['Produto'].str.strip().eq('') |
        (df['Altura'] <= 0) |
        (df['Largura'] <= 0) |
        (df['Profundidade'] <= 0) |
        (df['Quantidade'] < 0) |
        df['Altura'].isna() |
        df['Largura'].isna() |
        df['Profundidade'].isna()
    ]

    st.subheader('Produtos com dados estranhos')
    st.dataframe(df_dados_estranhos)

    st.subheader('Produto que ocupa maior volume no estoque')
    st.dataframe(df.loc[df['volume_total_produto'].idxmax()].to_frame().T)

    st.subheader('Produto que possui o maior volume')
    st.dataframe(df.loc[df['volume_produto'].idxmax()].to_frame().T)

    st.subheader('Embalagens cadastradas')
    st.dataframe(df_caixas_embalagem)

    if st.checkbox("Clique para calcular quantos produtos não cabem em caixa alguma"):
        df['cabe_em_alguma_caixa'] = df.apply(verificar_se_produto_cabe, axis=1)
        qtd_produtos_nao_cabem = (df['cabe_em_alguma_caixa'] == False).sum()
        st.metric('Quantidade de produtos que não cabem em caixa alguma', qtd_produtos_nao_cabem)

    volume_menor_embalagem = df_caixas_embalagem['volume total'].min()
    produtos_menor_50 = df[df['volume_produto'] < volume_menor_embalagem * 0.5].shape[0]
    st.metric('Quantidade de produtos que ocupam menos de 50% da menor embalagem', produtos_menor_50)

    st.subheader('Cadastre uma nova embalagem')
    with st.form("nova_embalagem"):
        nome  = st.text_input("Nome")
        alt   = st.number_input("Altura (cm)",  min_value=1)
        larg  = st.number_input("Largura (cm)", min_value=1)
        prof  = st.number_input("Profundidade (cm)", min_value=1)
        adicionar = st.form_submit_button("Adicionar")

        if adicionar:
            st.session_state.caixas.append(
                {"nome": nome, "altura": alt, "largura": larg, "profundidade": prof}
            )
            salvar(st.session_state.caixas)
            st.success("Embalagem adicionada!")

            if hasattr(st, "rerun"):
                st.rerun()
            elif hasattr(st, "experimental_rerun"):
                st.experimental_rerun()


else:
    st.title(paginas['02'])

    with st.form('recomendar_embalagem'):
        cod_pro = st.text_input('Código do Produto')
        qtd = st.number_input('Quantidade', min_value=1, value=1)
        procurar = st.form_submit_button('Procurar Embalagem')


    if procurar:
        try:
            cod_pro = pd.to_numeric(cod_pro)
        except Exception:
            st.error('Código inválido!')
        if cod_pro not in df.index:
            st.error('O Código informado não existe!')
        else:
            embalagem = procurar_embalagem(cod_pro, int(qtd))
            if embalagem is None:
                st.warning('Não há nenhuma caixa disponível para embalar o produto!')
            else:
                st.success(f'Embalagem Recomendada: {embalagem['nome']}')
                st.table(embalagem)
                st.write('Detalhes do Produto Pesquisado')
                produto = df.loc[cod_pro]
                st.table(produto)