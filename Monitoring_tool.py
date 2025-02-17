# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 13:44:40 2025

@author: alekd
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date
from sqlite import fetch_data,fetch_all_inverters
from categorization import categorize,categorize2,categorize2_plot
# Set page title
st.set_page_config(page_title="BESSsence", layout="wide")
@st.cache_data
def categorize_internal(bess_data):
    processed_data = categorize2(bess_data)
    return processed_data

@st.cache_data
def fetch_data_internal(db_folder,db_name,TABLE_NAME,start_date,end_date,inverter):
    bess_data = fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,inverter)
    return bess_data
def fetch_all_inverters_internal(db_folder,db_name,TABLE_NAME,start_date,end_date):
    bess_data = fetch_all_inverters(db_folder,db_name,TABLE_NAME,start_date,end_date)
    return bess_data
# Display title
#st.title("Welcome to My Streamlit App")
st.markdown(
    "<h1 style='text-align: center;'>BESSsence</h1>", 
    unsafe_allow_html=True
)
# Display an image
col1, col2, col3 = st.columns([1, 2, 1])  # Middle column takes more space
with col2:
    st.image("assemini.png", width=700)

#DB INFO
db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
db_name = 'example.db'
TABLE_NAME = "measurements_5min"

# Sidebar menu for navigation
type_analysis = st.sidebar.selectbox("Type of analysis",[None,'Single inverter','All inverters'])


date_start = st.sidebar.date_input('Starting date',date(2024,1,1))
date_end = st.sidebar.date_input('Ending date',date(2024,1,31))
start_date = date_start.strftime("%Y-%m-%d")
end_date = date_end.strftime("%Y-%m-%d")
if type_analysis=='Single inverter':
    menu = st.sidebar.selectbox("Select analysis", ["Home","Inverter efficiency","Time series","Categorize"])
    inverter = st.sidebar.selectbox("Select an Inverter", ["1_1_1","1_1_2","1_2_1","1_2_2","2_1_1","2_1_2","2_2_1","2_2_2","3_1_1","3_1_2","3_2_1","3_2_2","4_1_1","4_1_2","4_2_1","4_2_2"])
    
    
    #button_read_data = st.sidebar.button("Read data")
    #if button_read_data:
    bess_data = fetch_data_internal(db_folder,db_name,TABLE_NAME,start_date,end_date,inverter)
    bess_data['Direction'] = bess_data['P_AC'].apply(lambda v: 'Positive' if v>0 else 'Negative')
    bess_data['Abs_P_AC'] = bess_data['P_AC'].abs()
    if menu == "Inverter efficiency":
        st.header("Inverter efficiency")
        st.write("To be added.")
    
    elif menu == "Time series":
        st.header("Time series")
        # Define the Name value you want to filter by
        Timeseries_plot =st.sidebar.selectbox("Select plot", ["P=f(time)","SoC=f(time)","SoH=f(time)"])
        col_TS1, empty, col_TS2= st.columns([1,0.5, 1])
        with col_TS1:
            plot = go.Figure()
            if Timeseries_plot == 'P=f(time)':
                plot = px.line(bess_data,x='Timestamp',y='P_AC',title = 'P=f(time)')
                
            elif Timeseries_plot == 'SoC=f(time)':
                plot = px.line(bess_data,x='Timestamp',y='SoC',title = 'SoC=f(time)')
            elif Timeseries_plot == 'SoH=f(time)':
               plot = px.line(bess_data,x='Timestamp',y='SoH',title = 'SoH=f(time)')
            st.plotly_chart(plot)
        with col_TS2:
            if Timeseries_plot == 'SoC=f(time)':
                bess_data['range'] = pd.cut(bess_data['SoC'], bins=[0,20,40,60,80,100], labels=["0-20","20-40","40-60","60-80","80-100"], right=False)
                range_counts = bess_data['range'].value_counts().reset_index()
                range_counts.columns = ['range', 'count']
                SoC_pie = px.pie(range_counts, names='range', values='count', title="SoC Distribution in Ranges (0-100)")
                SoC_pie.update_layout(legend=dict(x=0.7, y=1,traceorder="normal"))
    
                st.plotly_chart(SoC_pie)
    elif menu == "Categorize":
        category_colors = {'Oscilating': "red", "High output": "green", "Low output": "blue","Idle":"orange"}
        col_cat1, empty, col_cat2= st.columns([1,0.5, 1])
    
        processed_bess_data = categorize_internal(bess_data)
        with col_cat1:
            plot = categorize2_plot(processed_bess_data,category_colors)
            st.plotly_chart(plot)
        with col_cat2:
            type_counts = processed_bess_data["Type"].value_counts().reset_index()
            type_counts.columns = ["Type", "Count"]
            plot_pie = px.pie(type_counts, values="Count", names="Type", title="Distribution of operation modes",color="Type",color_discrete_map=category_colors)
            st.plotly_chart(plot_pie)
        show_parameters = st.sidebar.checkbox("Show parameter details")
        if show_parameters:
            df_parameters = pd.DataFrame({'Coef of variation':[0.1],'Window analyzed for stats':['20 min'], 'Constant signal':['30 min'],'Upper threshold constant signal':[10],'Lower threshold constant signal':[2]})
    
            st.dataframe(df_parameters)
        V_SOC = st.sidebar.checkbox("Plot V=f(SoC)")
        if V_SOC:
            V_SOC_mode =st.sidebar.selectbox("Filter samples", ["All","Exclude oscilations","High P","Idle","Low P"])
            coloring_strategy = st.sidebar.selectbox("Coloring", ["Single","Positive/negative","Heatmap"])
            if V_SOC_mode=="Exclude oscilations":
                v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']!='Oscilating'],x="SoC",y="V",title="V = f(SoC)")
            elif V_SOC_mode=="All":
                v_soc_plot = px.scatter(processed_bess_data,x="SoC",y="V",title="V = f(SoC)")
            elif V_SOC_mode=="High P":
                if coloring_strategy=='Positive/negative':
                    v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']=='High output'],x="SoC",y="V",title="V = f(SoC)",color='Direction')
                elif coloring_strategy=='Heatmap':
                    v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']=='High output'],x="SoC",y="V",title="V = f(SoC)",color='Abs_P_AC',color_continuous_scale='RdBu')
                else:
                    v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']=='High output'],x="SoC",y="V",title="V = f(SoC)")
            elif V_SOC_mode=="Low P":
                v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']=='Low output'],x="SoC",y="V",title="V = f(SoC)")
            elif V_SOC_mode=="Idle":
                v_soc_plot = px.scatter(processed_bess_data[processed_bess_data['Type']=='Idle'],x="SoC",y="V",title="V = f(SoC)")
            st.plotly_chart(v_soc_plot)
elif type_analysis == 'All inverters':
    
    bess_data_all_inverter = fetch_all_inverters_internal(db_folder,db_name,TABLE_NAME,start_date,end_date)
    variable = st.sidebar.selectbox("Select a variable", ["P_AC","SoC","SoH","V"])
    grouped = bess_data_all_inverter.groupby('Timestamp')[variable]
    df_minmax = grouped.agg(['min', 'max']).reset_index()
    fig = go.Figure()

    # Add grey shaded area for min/max range
    fig.add_trace(go.Scatter(
        x=df_minmax['Timestamp'], 
        y=df_minmax['max'], 
        mode='lines',
        line=dict(width=0),
        name='Max',
        showlegend=False
    ))
    fig.add_trace(go.Scatter(
        x=df_minmax['Timestamp'], 
        y=df_minmax['min'], 
        mode='lines',
        line=dict(width=0),
        name='Min',
        fill='tonexty',  # Fill area between min and max
        fillcolor='rgba(50, 168, 82, 1)',
        showlegend=False
    ))
    
    
    
    # Update layout
    fig.update_layout(
        title=f"All inverters {variable}=f(time)",
        xaxis_title="Timestamp",
        yaxis_title="Value",
        template="plotly_white"
    )
    
    # Show plot
    st.plotly_chart(fig)