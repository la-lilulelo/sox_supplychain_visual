import streamlit.components.v1 as components
from pyvis.network import Network
import streamlit as st
import pandas as pd
import os

st.title('Network Graph Visualisation of SOX Index Constituents')
st.text('Node colour corresponds to a quintile based scoring system derived from a composite\nof inventory to sales growth and forward to trailing sales growth ratios.') 
st.text('Nodes that appear green indicate favourable inventory and sales trends, while those\nin red indicate the opposite.')
st.text('Node size corresponds to trailing twelve month revenue.')
st.text('Click on a company node to view its supplier and customer relationships. Zoom with the scroll wheel and click + drag to navigate.')

def create_network():
    data = pd.read_excel(os.getcwd() + '/data/supplychain_bbg-v01.xlsx')
    metadata = pd.read_excel(os.getcwd() + '/data/metadata-v01.xlsx')
    
    data = data[['supplier', 'pct_cost', 'company', 'ttm_sales', 'sales_to_inv_grwth', 'ttm_to_fwd_sls_grwth']]
    data = data.dropna()

    metadata = metadata.drop_duplicates(subset='name')
    metadata.index = metadata.name
    metadata = metadata.drop('name', axis=1)
    metadata_dict = metadata.to_dict('index')

    sales_map = data[['company', 'ttm_sales']].groupby(['company']).mean()
    minsales = sales_map.ttm_sales.min()
    sales_map = sales_map.to_dict()['ttm_sales']

    for supplier in list(set(data.supplier)):
        if supplier not in sales_map.keys():
            sales_map[supplier] = minsales

    very_positive = '#00D800'
    positive = '#BFEE90'
    neutral = '#FFFF98'
    negative = '#FF9898'
    very_negative = '#CD3232'

    for company in metadata_dict.keys():
        inv = metadata_dict[company]['inv_to_sls_gth'] # inventory / sales growth i.e. you want this to be small / negative
        sls = metadata_dict[company]['ttm_to_fwd_sls_gth'] # fwd / ttm sales growth i.e. you want this to be large / positive

        score = 0
        
        if inv < -0.75:
            score+=2
        elif -0.75 < inv < 0.75:
            score+=1
        elif 0.75 < inv < 1:
            score+=0
        elif 1 < inv < 1.5:
            score-=1
        elif inv > 1.5:
            score-=2
            
        if sls > 1.5:
            score+=2
        elif 1.5 > sls > 1.2:
            score+=1
        elif 1.2 > sls > 1:
            score+=0
        elif 1 > sls > 0.5:
            score-=1
        elif sls < 0.5:
            score-=2

        if score == 4:
            color = very_positive
        elif 2 <= score <= 3:
            color = positive
        elif -1 <= score <= 1:
            color = neutral
        elif -3 <= score <= -2:
            color = negative
        elif score == -4:
            color = very_negative
        
        metadata_dict[company]['color'] = color

    net = Network(
    notebook=True, 
    cdn_resources='remote',
    directed=True,
    bgcolor='#222222',
    font_color='white',
    height='700px',
    width='100%',
    select_menu=True,
    )

    nodes = list(set([*data.supplier, *data.company]))
    titles = [node + ': \n inventory to sales growth: '+ str(metadata_dict[node]['inv_to_sls_gth']) + '\n forward sales growth ratio: ' + str(metadata_dict[node]['ttm_to_fwd_sls_gth']) for node in nodes]
    values = [sales_map[node] for node in nodes]
    colours = [metadata_dict[node]['color'] for node in nodes]
    edges = [tuple(x) for x in data[['supplier','company','pct_cost']].values.tolist()]
    net.add_nodes(nodes, value=values, title=titles, color=colours)
    net.add_edges(edges)
    net.repulsion()

    return net
    
sox_supplychain = create_network()

try:
    path = '/tmp'
    sox_supplychain.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

except:
    path = '/html_files'
    sox_supplychain.save_graph(f'{path}/pyvis_graph.html')
    HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

components.html(HtmlFile.read(), height=700)
