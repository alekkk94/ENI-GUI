# -*- coding: utf-8 -*-
"""
Created on Wed Feb  5 11:26:07 2025

@author: aleksandar
"""

import pandas as pd
import numpy as np
from sqlite import fetch_data
import plotly.graph_objects as go
def categorize():
    db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
    db_name = 'example.db'
    TABLE_NAME = "measurements_5min"
    
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    
    # Define the Name value you want to filter by
    name_value = '1_1_1'
    bess_data = fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,name_value)
    
    def categorize_hourly(window):
        
        mean_val = np.mean(window)
        std_dev=np.std(window)
        if np.abs(mean_val)<eps:
            return 1#'Idle'
        elif std_dev<threshold:
            return 2#'Arbitrage'
        else:
            return 3#'Fast control'
    
    
    eps=0.05
    threshold=0.5
    
    
    bess_data.set_index('Timestamp',inplace=True)
    bess_data["category"] = bess_data["P_AC"].rolling(window=12, min_periods=12).apply(categorize_hourly, raw=True)
    category_colors = {1: "blue", 2: "green", 3: "red"}
    bess_data = bess_data.dropna(subset=["category"])
    bess_data["category_shift"] = bess_data["category"].ne(bess_data["category"].shift()).cumsum()  # Unique segment ID

    fig = go.Figure()

    for i in bess_data['category_shift'].unique():
        condition = bess_data['category_shift']==i
        mask = condition | condition.shift( 1, fill_value=False)
        sub_data = bess_data[mask]
        category = sub_data['category'][0]
        color = category_colors.get(int(category), "black")
        fig.add_trace(go.Scatter(
            x=sub_data.index, 
            y=sub_data["P_AC"],
            mode="lines",
            line=dict(color=color, width=2),
            name=f"Category {int(category)}",
            showlegend=False  # Avoid duplicate legends
        ))
    
    # **Step 4: Customize Layout**
    fig.update_layout(
        title="Time-Series Plot with Category-Based Coloring",
        xaxis_title="Time",
        yaxis_title="Value",
        template="plotly_white"
    )
    
    return fig
def categorize2(bess_data):   
    # db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
    # db_name = 'example.db'
    # TABLE_NAME = "measurements_5min"
    
    # start_date = '2024-01-01'
    # end_date = '2024-01-31'
    
    # # Define the Name value you want to filter by
    # name_value = '1_1_1'
    # bess_data = fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,name_value)
    window=4
    category_change=0
    CV_threshold=0.1
    custom_threshold=2 # in PW
    custom_threshold2 = 10
    bess_data['behavior_change']=0
    for i in range(len(bess_data)):
        sub_data = bess_data.iloc[max(0,i-(window-1)):i+1]
        sub_data=sub_data[(sub_data['behavior_change']==sub_data['behavior_change'].max()) | (sub_data.index==sub_data.index[-1])]
    
        mean_val = np.mean(sub_data['P_AC'])
        if not sub_data['P_AC'].mean()==0:
            std_dev=np.std(sub_data['P_AC'])
        else:
            std_dev=0
        if mean_val ==0:
            CV=0
        else:
            CV = std_dev/abs(mean_val)
        custom_index = abs(sub_data.loc[sub_data.index==sub_data.index[-1],'P_AC'].values[0]-mean_val)
        try:
            custom_index2 = abs(sub_data.loc[sub_data.index==sub_data.index[-1],'P_AC'].values[0]-sub_data.loc[sub_data.index==sub_data.index[-2],'P_AC'].values[0])
        except:
            custom_index2=0
        if (CV > CV_threshold and custom_index>custom_threshold) or custom_index2>custom_threshold2:
            category_change+=1
            bess_data.loc[i,'behavior_change']=category_change
        else:
            bess_data.loc[i,'behavior_change']=category_change
    
    reliability_filter = 6
    for ind,i in pd.DataFrame(bess_data.groupby('behavior_change')['Name'].count()).iterrows():
        if i.values[0]>=reliability_filter:
            bess_data.loc[bess_data['behavior_change']==ind,'reliable_cycle']=1
        else:
            bess_data.loc[bess_data['behavior_change']==ind,'reliable_cycle']=0
    bess_data['Type'] = 'High output'
    for i in bess_data['behavior_change'].unique():
        subset = bess_data[bess_data['behavior_change']==i]
        if subset['reliable_cycle'].values[0]==0:
            bess_data.loc[subset.index,'Type']='Oscilating'
        elif abs(subset['P_AC'].mean())<20:
            bess_data.loc[subset.index,'Type']='Idle'
        elif abs(subset['P_AC'].mean())<100:
            bess_data.loc[subset.index,'Type']='Low output'
        
    return bess_data
    
def categorize2_plot(bess_data,category_colors):        
    
    
    fig = go.Figure()
    for i in bess_data['behavior_change'].unique():
        condition = bess_data['behavior_change']==i
        mask = condition | condition.shift( -1, fill_value=False)
        if bess_data[condition]['Type'].values[0] =='Oscilating':
            mask = condition | condition.shift(-1, fill_value=False) | condition.shift(1, fill_value=False)
        elif i>0: 
            if bess_data[bess_data['behavior_change']==i-1]['Type'].values[0]=='Oscilating':
                mask=condition #don't do anything as the previous cycle already plotted this line
        check_change_of_behavior = bess_data[bess_data['behavior_change'].isin([i,i-1])]['Type'].unique()
        if len(check_change_of_behavior)==2 and 'Oscilating' not in check_change_of_behavior:
            mask_transit = condition | condition.shift( -1, fill_value=False)
            sub_data_transit = bess_data[mask_transit].iloc[:2]
            category_transit='Oscilating'
            color = category_colors.get(category_transit, "white")
            fig.add_trace(go.Scatter(
                x=sub_data_transit.Timestamp, 
                y=sub_data_transit["P_AC"],
                mode="lines",
                line=dict(color=color, width=2),
                name=f"{category_transit}",
                showlegend=False # Avoid duplicate legends
            ))
            mask=condition
        sub_data = bess_data[mask]
        category = sub_data['Type'].values[1]
        behavior_cycle = sub_data['behavior_change'].values[1]
        color = category_colors.get(category, "white")
        #line_style = 'dash' if sub_data['reliable_cycle'].values[0]==0 else 'solid'
        fig.add_trace(go.Scatter(
            x=sub_data.Timestamp, 
            y=sub_data["P_AC"],
            mode="lines",
            line=dict(color=color, width=2),
            name=f"{category[:4]}: {behavior_cycle}",
            showlegend=False# Avoid duplicate legends
        ))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color=category_colors.get('Idle', "white")), name="Idle"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color=category_colors.get('Low output', "white")), name="Low output"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color=category_colors.get('High output', "white")), name="High output"))
    fig.add_trace(go.Scatter(x=[None], y=[None], mode='lines', line=dict(color=category_colors.get('Oscilating', "white")), name="Oscilating"))
    # **Step 4: Customize Layout**
    fig.update_layout(
        title="Categorization of operation modes",
        xaxis_title="Timestamp",
        yaxis_title="P_AC",
        template="plotly_white"
    )
    return fig
def categorize3_zscore(): #doesnt work   
    db_folder=r'C:\Users\alekd\OneDrive - Politecnico di Milano\Projects\ENI - BESSence\GUI'
    db_name = 'example.db'
    TABLE_NAME = "measurements_5min"
    
    start_date = '2024-01-01'
    end_date = '2024-01-31'
    
    # Define the Name value you want to filter by
    name_value = '1_1_1'
    bess_data = fetch_data(db_folder,db_name,TABLE_NAME,start_date,end_date,name_value)
    window=4
    category_change=0
    Z_score_threshold=1
    custom_threshold=2 # in PW
    custom_threshold2 = 10
    bess_data['behavior_change']=0
    for i in range(len(bess_data)):
        sub_data = bess_data.iloc[max(0,i-(window-1)):i+1]
        sub_data=sub_data[(sub_data['behavior_change']==sub_data['behavior_change'].max()) | (sub_data.index==sub_data.index[-1])]
    
        mean_val = np.mean(sub_data['P_AC'])
        if not sub_data['P_AC'].mean()==0:
            std_dev=np.std(sub_data['P_AC'])
        else:
            std_dev=0
        if not std_dev ==0:
            Z_score = abs(sub_data.iloc[-1]['P_AC'] - mean_val)/std_dev
        else:
            Z_score =0
        custom_index = abs(sub_data.loc[sub_data.index==sub_data.index[-1],'P_AC'].values[0]-mean_val)
        try:
            custom_index2 = abs(sub_data.loc[sub_data.index==sub_data.index[-1],'P_AC'].values[0]-sub_data.loc[sub_data.index==sub_data.index[-2],'P_AC'].values[0])
        except:
            custom_index2=0
        if (Z_score > Z_score_threshold and custom_index>custom_threshold) or custom_index2>custom_threshold2:
            category_change+=1
            bess_data.loc[i,'behavior_change']=category_change
        else:
            bess_data.loc[i,'behavior_change']=category_change
    
    reliability_filter = 6
    for ind,i in pd.DataFrame(bess_data.groupby('behavior_change')['Name'].count()).iterrows():
        if i.values[0]>=reliability_filter:
            bess_data.loc[bess_data['behavior_change']==ind,'reliable_cycle']=1
        else:
            bess_data.loc[bess_data['behavior_change']==ind,'reliable_cycle']=0
    bess_data['Type'] = 'High output'
    for i in bess_data['behavior_change'].unique():
        subset = bess_data[bess_data['behavior_change']==i]
        if subset['reliable_cycle'].values[0]==0:
            bess_data.loc[subset.index,'Type']='Oscilating'
        elif abs(subset['P_AC'].mean())<0.1:
            bess_data.loc[subset.index,'Type']='Idle'
        elif abs(subset['P_AC'].mean())<10:
            bess_data.loc[subset.index,'Type']='Low output'
        
            
    category_colors = {'Oscilating': "red", "High output": "black", "Low output": "blue","Idle":"orange"}
    
    fig = go.Figure()
    for i in bess_data['behavior_change'].unique():
        condition = bess_data['behavior_change']==i
        mask = condition | condition.shift( -1, fill_value=False)
        sub_data = bess_data[mask]
        category = sub_data['Type'].values[1]
        color = category_colors.get(category, "white")
        #line_style = 'dash' if sub_data['reliable_cycle'].values[0]==0 else 'solid'
        fig.add_trace(go.Scatter(
            x=sub_data.index, 
            y=sub_data["P_AC"],
            mode="lines",
            line=dict(color=color, width=2),
            name=f"{category}",
            showlegend=True  # Avoid duplicate legends
        ))
    
    # **Step 4: Customize Layout**
    fig.update_layout(
        title="Time-Series Plot with Category-Based Coloring",
        xaxis_title="Time",
        yaxis_title="Value",
        template="plotly_white"
    )
    return fig