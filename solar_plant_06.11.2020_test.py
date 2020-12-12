# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random


def round_up_to_even(f):
    return np.ceil(f / 2.) * 2
# =============================================================================
# function for derating factors
# =============================================================================

def derating_bundled (no_of_ckts):
    derating_table=pd.read_excel("derating_factors.xlsx", index_col=0)      #taken from Lapp T33
    if no_of_ckts<10:
        factor=derating_table.iloc[0,no_of_ckts-1]
    elif no_of_ckts<=12:
        factor=derating_table.iloc[0,10]
    elif no_of_ckts<=14:
        factor=derating_table.iloc[0,11]
    elif no_of_ckts<=16:
        factor=derating_table.iloc[0,12]
    elif no_of_ckts<=18:
        factor=derating_table.iloc[0,13]
    elif no_of_ckts>=19:
        factor=derating_table.iloc[0,14]
    return (factor)

# =============================================================================
# function to extract cable details after voltage drop considerations (size, ampacity, price)
# =============================================================================
#%%
def cable_selection (current, voltage_level, device_rating, length_of_cable, no_cable_run, cable_type, cable_material, consider_vdrop):
    factor_for_temperature = 0.91 #for 40degrees
    factor_for_bundling = 1
    
    
    current_correction = current*1.1       #overcurrent percentage 10%
    current_correction = current_correction/(factor_for_temperature*factor_for_bundling)
    
    
    if cable_type=="DC":
        original_current=device_rating/voltage_level
        target_vdrop_pct=0.01
        length_of_cable=length_of_cable

        if voltage_level>=350 and voltage_level<1200:
            if cable_material=="Cu":
                df=pd.read_excel("0.60-1kV_Lappcable.xlsx", index_col=None)
            elif cable_material=="solar":
                df=pd.read_excel("1kV_Solar_Lappcable.xlsx", index_col=None)
        elif voltage_level>=1200 and voltage_level<3400:
            df=pd.read_excel("1.8-3kV_Lappcable.xlsx", index_col=None)
            
        elif voltage_level>=3400 and voltage_level<=6000:
            df=pd.read_excel("3-6kV_Lappcable.xlsx", index_col=None)

    elif cable_type=="AC":
        original_current=device_rating/(voltage_level*np.sqrt(3))
        target_vdrop_pct=0.005
        if voltage_level>=350 and voltage_level<600:
            df=pd.read_excel("0.60-1kV_Lappcable.xlsx", index_col=None)

        elif voltage_level>=600 and voltage_level<1800:
            df=pd.read_excel("1.8-3kV_Lappcable.xlsx", index_col=None)

        elif voltage_level>=1800 and voltage_level<=3500:
            df=pd.read_excel("3-6kV_Lappcable.xlsx", index_col=None)

    
    for i in range(len(df)):
        if current_correction<df.iloc[i,1]:
            cable_cost=df.iloc[i,2]/100
            cable_size=df.iloc[i,0]
            cable_current=df.iloc[i,1]
            break

    for i in range(len(df)):
        if cable_size==df.iloc[i,0]:
            if cable_type=="AC":
                voltagedrop_pu=df.iloc[i,5]             #per V/(A/km)
            elif cable_type=="DC":
                if cable_material=="Cu":
                    voltagedrop_pu=df.iloc[i,6]
                elif cable_material=="solar":
                    voltagedrop_pu=df.iloc[i,5]             #per V/(A/km)
            break
        
    if consider_vdrop =="Yes":      
        
        vdrop=current*length_of_cable/1000*voltagedrop_pu
        
        receiving_voltage=voltage_level-vdrop
        #    print(voltage_level,"\n",receiving_voltage,"\n")
       
        vdrop_pct=vdrop/voltage_level
        
        target_vdrop=target_vdrop_pct*voltage_level
        target_receiving_voltage=voltage_level-target_vdrop
        
        if vdrop_pct>=target_vdrop_pct:
            
            target_voltagedrop=voltage_level-target_receiving_voltage
            target_voltagedrop_pu=target_voltagedrop/(current*length_of_cable/1000)
            
            for i in range(len(df)):
                if cable_type=="AC":
                    if df.iloc[i,5]<=target_voltagedrop_pu:
                        voltagedrop_compensate=df.iloc[i,0]             #per V/(A/km)
                        compensate_cable_cost=df.iloc[i,2]/100
                        new_voltage_drop=voltage_level-df.iloc[i,5]*current*length_of_cable/1000
                        new_voltage_drop_pu=df.iloc[i,5]
                        break
                    
                elif cable_type=="DC":
                    if cable_material=="Cu":
                        new_voltage_drop_pu=df.iloc[i,6]
                    elif cable_material=="solar":
                        new_voltage_drop_pu=df.iloc[i,5]             #per V/(A/km)
                    if new_voltage_drop_pu<=target_voltagedrop_pu:
                        voltagedrop_compensate=df.iloc[i,0]             #per V/(A/km)
                        compensate_cable_cost=df.iloc[i,2]/100
                        new_voltage_drop=new_voltage_drop_pu*current*length_of_cable/1000
                        break

            if i == len(df)-1:
                voltagedrop_compensate=999.99

            if voltagedrop_compensate>300:

                while True:
                        
                    no_cable_run+=1
                    current=original_current/no_cable_run
                    return cable_selection (current, voltage_level, device_rating, length_of_cable, no_cable_run, cable_type, cable_material, consider_vdrop)
                    if voltagedrop_compensate<=300:break


        else:
            voltagedrop_compensate=cable_size
            compensate_cable_cost=cable_cost
            new_voltage_drop=receiving_voltage
            new_voltage_drop_pu=voltagedrop_pu
    else:
        voltagedrop_compensate=cable_size
        compensate_cable_cost=cable_cost
        if cable_type=="AC":
            new_voltage_drop_pu=df.iloc[i,5]             #per V/(A/km)
        elif cable_type=="DC":
            if cable_material=="Cu":
                new_voltage_drop_pu=df.iloc[i,6]
            elif cable_material=="solar":
                new_voltage_drop_pu=df.iloc[i,5]    
        receiving_voltage=0
        target_receiving_voltage=0
        new_voltage_drop=new_voltage_drop_pu*current*length_of_cable/1000
            
    return cable_size, voltagedrop_compensate, receiving_voltage, target_receiving_voltage, new_voltage_drop, new_voltage_drop_pu, compensate_cable_cost, no_cable_run
# =============================================================================

def trafo_rating(inverter_rating, total_inv_power, max_trafo_connection_points):
    
    trafo_table=pd.read_excel("trafo_standard_sizes.xlsx", index_col=0)
    trafo_index=len(trafo_table.columns)-1
    trafo_inv_ratio=trafo_table.iloc[0,trafo_index]*1e3/inverter_rating
    while trafo_inv_ratio>=max_trafo_connection_points:
        trafo_inv_ratio=trafo_table.iloc[0,trafo_index]*1e3/inverter_rating
        if trafo_inv_ratio<=max_trafo_connection_points:break
        trafo_index-=1
    selected_trafo=trafo_table.iloc[0,trafo_index]  #trafo_table.index[0]
    trafo_no=np.ceil(total_inv_power/(selected_trafo*1e3))
    return selected_trafo, trafo_no

def cost_compare(plant_details):
    total_cost_comparison=pd.DataFrame()
    acvolt_index=plant_details.index.get_loc("Inverter Output Voltage (V)")
    plantpower_index=plant_details.index.get_loc("Plant Power (W)")
    convpower_index=plant_details.index.get_loc("Converter Power (W)")
    invpower_index=plant_details.index.get_loc("Inverter Power (W)")
    trafopower_index=plant_details.index.get_loc("Trafo Power")
    cost_index=plant_details.index.get_loc("total_costs")#"total cable cost (€)"
         
    new_count=0
    new_count1=0
    new_count2=0

#    "PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS units: "+str(int(plant_details.iloc[plant_details.iloc[plant_details.index.get_loc("No. of inverters"),i]]))

    for i in range(len(plant_details.columns)):
        if plant_details.iloc[acvolt_index,i]==inverter_voltages[0]:
            total_cost_comparison.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            total_cost_comparison.at[new_count,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("No. of inverters"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
            new_count1+=1
        elif plant_details.iloc[acvolt_index,i]==inverter_voltages[1]:
            total_cost_comparison.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            total_cost_comparison.at[new_count1,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("No. of inverters"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
            new_count2+=1
        else:
            total_cost_comparison.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            total_cost_comparison.at[new_count1+new_count2,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("No. of inverters"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
    
    total_cost_comparison=total_cost_comparison.T
    total_cost_comparison=total_cost_comparison.rename(columns=total_cost_comparison.iloc[0]).drop(total_cost_comparison.index[0])
    return total_cost_comparison
#%%
def cost_compare_1(plant_details):
    cost_comparison=pd.DataFrame()
    length_comparison=pd.DataFrame()
    
    for new_count in range(len(plant_details.columns)):
        cost_comparison.at[new_count,"index"]="Inv Voltage:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+"kV\nInv & Conv\nPower:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3)+"kW"

        cost_comparison.at[new_count,"cost of string cable"]=plant_details.iloc[plant_details.index.get_loc("cost of string cable (€)"), new_count]
        cost_comparison.at[new_count,"cost of comb conv cable"]=plant_details.iloc[plant_details.index.get_loc("cost of comb conv cable (€)"), new_count]
        cost_comparison.at[new_count,"cost of conv inv cable"]=plant_details.iloc[plant_details.index.get_loc("cost of conv inv cable (€)"), new_count]
        cost_comparison.at[new_count,"cost of inv trafo cable"]=plant_details.iloc[plant_details.index.get_loc("cost of inv trafo cable (€)"), new_count]
        
        length_comparison.at[new_count,"index"]="Inv Voltage:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+"kV\nInv & Conv\nPower:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3)+"kW"

        length_comparison.at[new_count,"total_string_cable_length"]=plant_details.iloc[plant_details.index.get_loc("total_string_cable_len"), new_count]
        length_comparison.at[new_count,"total_comb_conv_cable_length"]=plant_details.iloc[plant_details.index.get_loc("total_comb_conv_cable_len"), new_count]
        length_comparison.at[new_count,"total_conv_inv_cable_length"]=plant_details.iloc[plant_details.index.get_loc("total_conv_inv_cable_len"), new_count]
        length_comparison.at[new_count,"total_inv_trafo_cable_length"]=plant_details.iloc[plant_details.index.get_loc("total_inv_trafo_cable_len"), new_count]


#    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])
    cost_comparison=cost_comparison.T
    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])

    length_comparison=length_comparison.T
    length_comparison=length_comparison.rename(columns=length_comparison.iloc[0]).drop(length_comparison.index[0])
    
    return cost_comparison.T, length_comparison.T
#%%
def cost_breakdown(plant_details):
    cost_comparison=pd.DataFrame()

    for new_count in range(len(plant_details.columns)):
        cost_comparison.at[new_count,"index"]="Inv Voltage: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+" kV\nPCS Power: "+str(int((plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3))+" kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("No. of inverters"), new_count]))

        cost_comparison.at[new_count,"total DC cabling cost"]=plant_details.iloc[plant_details.index.get_loc("total DC cabling cost"), new_count]
        cost_comparison.at[new_count,"total AC cabling cost"]=plant_details.iloc[plant_details.index.get_loc("total AC cabling cost"), new_count]
        cost_comparison.at[new_count,"total converter costs"]=plant_details.iloc[plant_details.index.get_loc("total_converter_costs"), new_count]
        cost_comparison.at[new_count,"total inverter costs"]=plant_details.iloc[plant_details.index.get_loc("total_inverter_costs"), new_count]
        cost_comparison.at[new_count,"total transformer costs"]=plant_details.iloc[plant_details.index.get_loc("total transformer costs"), new_count]
        cost_comparison.at[new_count,"total switchgear costs"]=plant_details.iloc[plant_details.index.get_loc("total switchgear costs"), new_count]

#    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])
    cost_comparison=cost_comparison.T
    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])

   
    return cost_comparison.T
#%%
def PCS_cost_breakdown(plant_details):
    cost_comparison=pd.DataFrame()

    for new_count in range(len(plant_details.columns)):
        cost_comparison.at[new_count,"index"]="Inv Voltage: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+"kV\nPCS Power:"+str(int((plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3))+"kW\nPCS Units:"+str(int(plant_details.iloc[plant_details.index.get_loc("No. of inverters"), new_count]))
        cost_comparison.at[new_count,"total PCS semiconductor costs"]=plant_details.iloc[plant_details.index.get_loc("total PCS semiconductor costs"), new_count]
        cost_comparison.at[new_count,"total PCS filter costs"]=plant_details.iloc[plant_details.index.get_loc("total PCS filter costs"), new_count]
        cost_comparison.at[new_count,"total PCS fixed costs"]=plant_details.iloc[plant_details.index.get_loc("total PCS fixed costs"), new_count]

#    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])
    cost_comparison=cost_comparison.T
    cost_comparison=cost_comparison.rename(columns=cost_comparison.iloc[0]).drop(cost_comparison.index[0])

   
    return cost_comparison.T
#%%

def get_inv_price (inv_power, inv_voltage, inv_df):
    for i in range(len(inv_df)):
        if inv_power == inv_df.loc[i,"Inverter_power (kVA)"] and inv_voltage==inv_df.loc[i,'L-L voltage (V)']:
            inv_price=inv_df.loc[i,'total inv price']
            inv_semiconductor_price=inv_df.loc[i,'total semiconductors price']
            inv_filter_price=inv_df.loc[i,'total filter price']
            break
    return inv_price, inv_semiconductor_price, inv_filter_price
#%%

def get_conv_price (conv_power, conv_voltage, conv_df):
    for i in range(len(conv_df)):
        if conv_power == conv_df.loc[i,'Booster\nPower (W)'] and conv_voltage==conv_df.loc[i,'Booster Equivalent\nA.C. Voltage (V)']:
            conv_price=conv_df.loc[i,'total conv price']
            conv_semiconductor_price=conv_df.loc[i,'total semiconductors price']
            conv_filter_price=conv_df.loc[i,'total filter price']
            break
    return conv_price, conv_semiconductor_price, conv_filter_price

#%%


def get_trafo_price(trafo_power, trafo_LV_voltage, trafo_df):
    for i in range(len(trafo_df)):
        if trafo_power == trafo_df.loc[i,'Transformer Power (MVA)'] and trafo_LV_voltage==trafo_df.loc[i,'Low Voltage (kV)']:
            trafo_price=trafo_df.loc[i,'Price (€)']
            break
    return trafo_price

#%%
def cost_compare_plots(scenario, results_df, maximum):
    plt.figure()
    cost_comparison=np.divide(cost_compare(results_df),1)
    x=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,0], 'bo', label=cost_comparison.keys()[0]+"V\nbase case\n(4 x 3 MW Trafo)")
    y=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,1], 'r-', label=cost_comparison.keys()[1]+"V")
    z=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,2], 'm-', label=cost_comparison.keys()[2]+"V")
    
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(linestyle=':', linewidth=1.5)
    plt.ylim([0, maximum*1.1])
    plt.title("PV Plant\nTotal Costs (€) with\nper "+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(fontsize=8)
    plt.yticks(np.multiply([0, 0.5, 1, 1.5, 2, 2.5, 2.75],1e6),[0, "0.50 M", "1 M","1.50 M","2 M","2.50 M","2.75 M"], fontsize=8)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('Total costs (€)', fontsize=8, fontweight="bold")
    fig = plt.gcf()
    fig.set_size_inches(6, 3)
    fig.savefig("PV"+scenario+"_cost_comparison", dpi=2000, quality=95, bbox_inches='tight', filetype="png")  
    return (x,y,z)

#%%
def cost_length_plots(scenario, results_df, maximum):
    fig, (ax1,ax2) = plt.subplots(2, 1)

    cost_compare, length_comparison=cost_compare_1(results_df)
    length_comparison=length_comparison*1e-3
    cost_compare.plot.bar(ax=ax1, stacked=True, grid=True, sharex=True, legend=True, title="PV Plant\n"+str(plant_power/1e6)+"MW power plant total cost breakdown (€)\n"
                          +"with per "+" ".join(scenario.split('_'))+" total costs", ylim=[0, maximum*1.1], fontsize=16)
    ax1.set_ylabel('Total costs (€)', fontsize=16)
    length_comparison.plot.bar(ax=ax2, stacked=True, legend=True, grid=True, ylim=[0, 300])
    ax2.set_ylabel('Total length (km)', fontsize=16)
    ax2.set_xlabel('Scenarios', fontsize=16)
    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig("PV"+scenario, dpi=1000, quality=80, bbox_inches='tight', filetype="png") 
    return fig
#%%
def cost_breakdown_plots(scenario, results_df):
    fig, ax1 = plt.subplots(1, 1)

    cost_compare=np.divide(cost_breakdown(results_df),1)
    cost_compare.plot.bar(ax=ax1, stacked=True, sharex=True, legend=True)#, ylim=[0, maximum*1.1])

    ax1.set_title(("PV Plant\n"+str(int(plant_power/1e6))+" MW power plant total cost breakdown (€)\n"+"with per "+" ".join(scenario.split('_'))),fontsize=8, fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.set_ylabel('Total costs in (€)', fontsize=8, fontweight="bold")
    ax1.set_xlabel('Scenarios', fontsize=8, fontweight="bold")
#    plt.legend(fontsize=14)
    plt.yticks(np.multiply([0, .25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5, 2.75],1e6),[0, "0.25 M", "0.50 M", "0.75 M","1 M","1.25 M","1.50 M","1.75 M","2 M","2.25 M","2.50 M","2.75 M"], fontsize=8)
    plt.xticks(fontsize=6.5)
    plt.grid(linestyle=':', linewidth=0.5)
    fig = plt.gcf()
    fig.set_size_inches(8, 4.57)
    fig.savefig("PV"+scenario+"_cost_breakdown", dpi=2000, quality=95, bbox_inches='tight', filetype="png") 
    return fig
#%%
def PCS_cost_breakdown_plots(scenario, results_df):
    fig, ax1 = plt.subplots(1, 1)

    cost_compare=np.divide(PCS_cost_breakdown(results_df),1)
    cost_compare.plot.bar(ax=ax1, stacked=True, sharex=True, legend=True)#, ylim=[0, maximum*1.1])

    ax1.set_title(("12 MW Total Power Conversion System\nCost Breakdown (€)"), fontsize=8, fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.set_ylabel('Costs (€)', fontsize=8, fontweight="bold")
    ax1.set_xlabel('Scenarios', fontsize=8, fontweight="bold")
#    plt.legend(fontsize=14)
    plt.yticks(np.multiply([0, .25, 0.5, 0.75, 1, 1.25],1e6),[0, "0.25 M", "0.50 M", "0.75 M","1 M","1.25 M"], fontsize=8)
    plt.xticks(fontsize=6.5)
    plt.grid(linestyle=':', linewidth=0.5)
    fig = plt.gcf()
    fig.set_size_inches(8, 4.57)
    fig.savefig("PV"+scenario+"_PCS_cost_breakdown", dpi=2000, quality=95, bbox_inches='tight', filetype="png") 
    return fig
#%%
def vdrop_plots(scenario, results_df):#, maximum):
    vdrop_df=pd.DataFrame()
    new_vdrop_df=pd.DataFrame()
    vdrop_index=results_df.index.get_loc("rec_volt")
    new_vdrop_index=results_df.index.get_loc("new voltage drop")
    acvolt_index=results_df.index.get_loc("Inverter Output Voltage (V)")
    plantpower_index=results_df.index.get_loc("Plant Power (W)")
    convpower_index=results_df.index.get_loc("Converter Power (W)")
    invpower_index=results_df.index.get_loc("Inverter Power (W)")
    trafopower_index=results_df.index.get_loc("Trafo Power")
    cost_index=results_df.index.get_loc( "total cable cost (€)")
    
    new_count=0
    new_count1=0
    new_count2=0
    
    for i in range(len(results_df.columns)):
        if results_df.iloc[acvolt_index,i]==inverter_voltages[0]:
            vdrop_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            vdrop_df.at[new_count,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[vdrop_index,i], 2))#+"M"
            new_vdrop_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            new_vdrop_df.at[new_count,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_vdrop_index,i], 2))#+"M"
            new_count1+=1
        elif results_df.iloc[acvolt_index,i]==inverter_voltages[1]:
            vdrop_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            vdrop_df.at[new_count1,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[vdrop_index,i], 2))#+"M"
            new_vdrop_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            new_vdrop_df.at[new_count1,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_vdrop_index,i], 2))#+"M"
            new_count2+=1
        else:
            vdrop_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            vdrop_df.at[new_count1+new_count2,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[vdrop_index,i], 2))#+"M"
            new_vdrop_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            new_vdrop_df.at[new_count1+new_count2,"Converter\nPower: "+str(int(results_df.iloc[convpower_index,i]/1e3))+"kW\nInverter\nPower: "+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_vdrop_index,i], 2))#+"M"
    
    vdrop_df=vdrop_df.T
    vdrop_df=vdrop_df.rename(columns=vdrop_df.iloc[0]).drop(vdrop_df.index[0])
    new_vdrop_df=new_vdrop_df.T
    new_vdrop_df=new_vdrop_df.rename(columns=new_vdrop_df.iloc[0]).drop(new_vdrop_df.index[0])
    
    plt.figure()
    
    x=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,0], 'bo', label=vdrop_df.keys()[0]+"V")
    a=plt.plot(list((vdrop_df.index[:])), [400*0.995 for l in range(len(vdrop_df.iloc[:,0]))], 'go', label=vdrop_df.keys()[0]+"V voltage drop limit")
    x1=plt.plot(list((new_vdrop_df.index[:])), new_vdrop_df.iloc[:,0], 'ro', label=new_vdrop_df.keys()[0]+"V new voltage drop")

    y=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,1], 'r-', label=vdrop_df.keys()[1]+"V")
    b=plt.plot(list((vdrop_df.index[:])), [1500*0.995 for l in range(len(vdrop_df.iloc[:,1]))], 'c-', label=vdrop_df.keys()[1]+"V voltage drop limit")
    y1=plt.plot(list((new_vdrop_df.index[:])), new_vdrop_df.iloc[:,1], 'y-', label=new_vdrop_df.keys()[1]+"V new voltage drop")

    z=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,2], 'm-', label=vdrop_df.keys()[2]+"V")
    c=plt.plot(list((vdrop_df.index[:])), [3300*0.995 for l in range(len(vdrop_df.iloc[:,2]))], 'y-', label=vdrop_df.keys()[2]+"V voltage drop limit")
    z1=plt.plot(list((new_vdrop_df.index[:])), new_vdrop_df.iloc[:,2], 'b-', label=new_vdrop_df.keys()[2]+"V new voltage drop")

    plt.xticks(rotation=90)
    plt.grid(linestyle=':', linewidth=0.5)
#    plt.ylim([0, maximum*1.1])
    plt.title("Voltage Drop "+" ".join(scenario.split('_')), fontsize=16)
    plt.legend(fontsize=14)
    plt.xlabel("Scenarios", fontsize=16)
    plt.ylabel('V', fontsize=16)
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig("PV"+scenario+"_voltage_drop", dpi=1000, quality=95, bbox_inches='tight', filetype="png")  
    return (x,y,z,a,b,c,x1,y1,z1)
#%%
def cross_section_plots(scenario, results_df):#, maximum):
    crosssection_df=pd.DataFrame()
    new_crosssection_df=pd.DataFrame()
    crosssection_index=results_df.index.get_loc("orig_cable_size")
    new_crosssection_index=results_df.index.get_loc("vdrop_compensate")
    acvolt_index=results_df.index.get_loc("Inverter Output Voltage (V)")
    plantpower_index=results_df.index.get_loc("Plant Power (W)")
    convpower_index=results_df.index.get_loc("Converter Power (W)")
    invpower_index=results_df.index.get_loc("Inverter Power (W)")
    trafopower_index=results_df.index.get_loc("Trafo Power")
    cost_index=results_df.index.get_loc( "total cable cost (€)")
    
    new_count=0
    new_count1=0
    new_count2=0
    
    for i in range(len(results_df.columns)):
        if results_df.iloc[acvolt_index,i]==inverter_voltages[0]:
            crosssection_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            crosssection_df.at[new_count,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            new_crosssection_df.at[new_count,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
            new_count1+=1
        elif results_df.iloc[acvolt_index,i]==inverter_voltages[1]:
            crosssection_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            crosssection_df.at[new_count1,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            new_crosssection_df.at[new_count1,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
            new_count2+=1
        else:
            crosssection_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            crosssection_df.at[new_count1+new_count2,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            new_crosssection_df.at[new_count1+new_count2,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
    
    crosssection_df=crosssection_df.T
    crosssection_df=crosssection_df.rename(columns=crosssection_df.iloc[0]).drop(crosssection_df.index[0])
    new_crosssection_df=new_crosssection_df.T
    new_crosssection_df=new_crosssection_df.rename(columns=new_crosssection_df.iloc[0]).drop(new_crosssection_df.index[0])
    
    plt.figure()

    x=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,0], 'bo', label=crosssection_df.keys()[0]+"V cross-section before voltage drop")
#    a=plt.plot(list((vdrop_df.index[:])), [400*0.995 for l in range(len(vdrop_df.iloc[:,0]))], 'go', label=vdrop_df.keys()[0]+"V voltage drop limit")
    x1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,0], 'ro', label=new_crosssection_df.keys()[0]+"V cross-section after voltage drop")

    y=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,1], 'g-', label=crosssection_df.keys()[1]+"V cross-section before voltage drop")
#    b=plt.plot(list((vdrop_df.index[:])), [1500*0.995 for l in range(len(vdrop_df.iloc[:,1]))], 'c-', label=vdrop_df.keys()[1]+"V voltage drop limit")
    y1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,1], 'y-', label=new_crosssection_df.keys()[1]+"V cross-section after voltage drop")

    z=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,2], 'm-', label=crosssection_df.keys()[2]+"V cross-section before voltage drop")
#    c=plt.plot(list((vdrop_df.index[:])), [3300*0.995 for l in range(len(vdrop_df.iloc[:,2]))], 'y-', label=vdrop_df.keys()[2]+"V voltage drop limit")
    z1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,2], 'b-', label=new_crosssection_df.keys()[2]+"V cross-section after voltage drop")

    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(linestyle=':', linewidth=0.5)
#    plt.ylim([0, maximum*1.1])
    plt.title("PV Plant\nCable cross section for voltage drop correction between Inverter & Transformer\n"+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(fontsize=7)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('Cable cross-section (mm2)', fontsize=8, fontweight="bold")
    fig = plt.gcf()
    fig.set_size_inches(6, 3)
    fig.savefig("PV"+scenario+"_cross_section", dpi=2000, quality=95, bbox_inches='tight', filetype="png")  
    return (x,y,z,x1,y1,z1)


#%%
def avg_vdrop_plots(scenario, results_df):#, maximum):
    vdrop_df=pd.DataFrame()
#    new_vdrop_df=pd.DataFrame()
    vdrop_index=results_df.index.get_loc("avg inv trafo individual v drop")
#    new_vdrop_index=results_df.index.get_loc("vdrop_compensate")
    acvolt_index=results_df.index.get_loc("Inverter Output Voltage (V)")
    plantpower_index=results_df.index.get_loc("Plant Power (W)")
    convpower_index=results_df.index.get_loc("Converter Power (W)")
    invpower_index=results_df.index.get_loc("Inverter Power (W)")
    trafopower_index=results_df.index.get_loc("Trafo Power")
    cost_index=results_df.index.get_loc( "total cable cost (€)")
    
    new_count=0
    new_count1=0
    new_count2=0
    
    for i in range(len(results_df.columns)):
        if results_df.iloc[acvolt_index,i]==inverter_voltages[0]:
            vdrop_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            vdrop_df.at[new_count,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
            new_count1+=1
        elif results_df.iloc[acvolt_index,i]==inverter_voltages[1]:
            vdrop_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            vdrop_df.at[new_count1,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
            new_count2+=1
        else:
            vdrop_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            vdrop_df.at[new_count1+new_count2,"PCS Power: \n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
    
    vdrop_df=vdrop_df.T
    vdrop_df=vdrop_df.rename(columns=vdrop_df.iloc[0]).drop(vdrop_df.index[0])
    
    plt.figure()
    
    # x=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,0]*100, 'bo', label=vdrop_df.keys()[0]+"V avg voltage drop")
#    a=plt.plot(list((vdrop_df.index[:])), [0.005 for l in range(len(vdrop_df.iloc[:,0]))], 'go', label=vdrop_df.keys()[0]+"V voltage drop limit")

    y=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,1]*100, 'g-', label=vdrop_df.keys()[1]+"V avg voltage drop")
#    b=plt.plot(list((vdrop_df.index[:])), [0.005 for l in range(len(vdrop_df.iloc[:,1]))], 'c-', label=vdrop_df.keys()[1]+"V voltage drop limit")

    # z=plt.plot(list((vdrop_df.index[:])), vdrop_df.iloc[:,2]*100, 'm-', label=vdrop_df.keys()[2]+"V avg voltage drop")
    c=plt.plot(list((vdrop_df.index[:])), [0.5 for l in range(len(vdrop_df.iloc[:,2]))], 'y-', label="voltage drop limit")


    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(linestyle=':', linewidth=0.5)
#    plt.ylim([0, maximum*1.1])
    plt.title("PV Plant\nAverage voltage drop between Inv-Trafo considering average cable length\nper "+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(fontsize=8)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('V drop %', fontsize=8, fontweight="bold")
    plt.ylim([0, 1])
    fig = plt.gcf()
    fig.set_size_inches(6, 3)
    fig.savefig("PV"+scenario+"_avg_vdrop", dpi=2000, quality=95, bbox_inches='tight', filetype="png")  
    return (y,c)#(x,y,z,c)


#%%
# =============================================================================
# Solar or Battery Module details
# =============================================================================
plant_type="solar" # "solar" or "battery"
if plant_type=="solar":
    module_power=540#float(input('Enter power of single solar or battery module (W): '))       #Enter power of a single solar or battery module/rack
    module_operating_voltage=41.01#float(input('Enter operating voltage of module (V):'))         #Enter solar or battery modules operating voltage
    module_height=2.274#float(input('Enter height of single module (mm):'))/1000                  #Enter height of solar/battery module, converted to m
    #module_depth=1.850#float(input('Enter depth of single module (mm):'))/1000                    #Enter depth of solar/battery module, converted to m
    #module_projection=1.850#float(input('Enter depth of single module (mm):'))/1000                    #Enter horizontal projection of solar/battery module, converted to m
    module_width=1.134#float(input('Enter width of single module (mm):'))/1000                    #Enter width of solar/battery module, converted to m
    #area_module=module_projection*module_width
    combiner_target_voltage= 1000
    rating_range=range(150000, 550000, 50000)
    converter_inverter_ratios=[1.]
else:
    module_power=55.5000#float(input('Enter power of single solar or battery module (W): '))       #Enter power of a single solar or battery module/rack
    module_operating_voltage=902#float(input('Enter operating voltage of module (V):'))         #Enter solar or battery modules operating voltage
    module_height=0.702#float(input('Enter height of single module (mm):'))/1000                  #Enter height of solar/battery module, converted to m
    module_width=0.442
    combiner_target_voltage= module_operating_voltage
    rating_range=range(module_power, 550000, 50000)
    converter_inverter_ratios= [1.]

# =============================================================================
# Inv price
# =============================================================================
#device_list_df=pd.read_excel("sic_devices.xlsx")
#device_list_df.at[:, 'Current @25degC']=np.divide(device_list_df.iloc[:,0],(np.sqrt(3)*device_list_df.loc[:,"Voltage"]))
#price_per_module=728.63098        #€ per unit from digikey for more than 51 Nos
#for i in range(len(device_list_df)):
#    if device_list_df.loc[i, 'Level']==2:
#        modules_per_inv=3
#    elif device_list_df.loc[i, 'Level']==3:
#        modules_per_inv=9
#    elif device_list_df.loc[i, 'Level']==5:
#        modules_per_inv=18
#    device_list_df.at[i, 'No. of SiC\npower modules\nper inverter']=modules_per_inv
#    device_list_df.at[i, 'Cost of SiC devices\nper inverter']=modules_per_inv*price_per_module
# =============================================================================



inv_width = 0.699       #m
inv_depth = 0.460       #m
conv_width = 0.699       #m
conv_depth = 0.460       #m
trafo_width=1.79
trafo_width1=1.41




# =============================================================================
# Plant details
# =============================================================================
plant_power=12000000#float(input('Enter power of power plant (kW):'))*1000                       #Enter total power of plant, converted to W
plant_area=120#float(input('Enter area of plant alloted in (m2):'))                         #Enter area of plant
trafo_eff=0.95
total_inverter_power_output = plant_power/trafo_eff  #Total power output of inverter considering 95% efficiency of transformer
inverter_efficiency=0.97
total_converter_power_output= total_inverter_power_output/inverter_efficiency
converter_efficiency= 0.99
total_combiner_power=total_converter_power_output/converter_efficiency
#combiner_power= 50000#float(input('Enter total power of combiner box (kW):'))*1000           #Enter total power of a combiner box, converted to W
#combiner_target_voltage= 1000
converter_present= True #bool(int(input('Is there a DC-DC converter used?')))                           #to check if a DC-DC converter used
with_neutral=0
max_no_of_mech_connections_trafo=3

modulation_index=0.7
factor_for_AC_to_DC=2/(modulation_index*np.sqrt(3))
per_switchgear_cost=15e3 #cost of a 22MVA, 20kV switchgear



if converter_present == True:
    total_combiner_power = total_converter_power_output
    converter_output_voltage=5500#float(input('Enter operating voltage of converter (V):'))        #Enter DC-DC converter operating voltage    
else:
    total_combiner_power = total_inverter_power_output
    converter_output_voltage="N/A"




#%%
plant_detail=pd.DataFrame()
plant_detail["index"]=["Plant Power (W)", "total solar panels", 
               "String Power (W)","String Voltage (V)","No. of strings", "panel per string", "string cable type (mm2)",
               "string output current rating (A)", "string cable type new (mm2)", "total_string_cable_len", "string_ckts per combiner\n/array size",
               "per array power", "total arrays", "array length", "array width", "Combiner power (W)", "Combiner voltage (V)", "arrays/combiners\nper converter", "total combiner power",
               "Converter Power (W)", "Converter Output Voltage (V)", "No. of converter", "comb conv cable type (mm2)", "comb conv output current (A)",
               "comb conv cable type new (mm2)", "comb_conv_ckts", "total_comb_conv_cable_len", 
               "Inverter Power (W)", "Inverter Output Voltage (V)","No. of inverters", "conv inv cable type (mm2)", "conv inv output current (A)",
               "conv inv cable type new (mm2)", "conv_inv_ckts", "total_conv_inv_cable_len", 
               "Trafo Power","No. of transformers","inv trafo cable type (mm2)", "inv trafo output current (A)",
               "inv trafo cable type new (mm2)", "inv_trafo_ckts", "total_inv_trafo_cable_len", "inv_trafo_cable_runs",
               "orig_cable_size", "vdrop_compensate", "rec_volt", "target_rec_volt", "new voltage drop",
               "longest string cable", "longest combiner to converter cable", "longest converter to inverter cable", "longest inv to trafo cable", "inv trafo individual v drops", "avg inv trafo individual v drop",
               "cable_list_array_converter", "cable_length_array_converter",  "cable_list_inv_trafo", "cable_length_inv_trafo", "inv_spots_x", "inv_spots_y", "trafo_spots_x", "trafo_spots_y",
               "total PCS semiconductor costs", "total PCS filter costs", "total PCS fixed costs", "total transformer costs", "total switchgear costs", 
               "cost of string cable (€)","cost of comb conv cable (€)","cost of conv inv cable (€)","cost of inv trafo cable (€)",
               "total DC cabling cost", "total AC cabling cost",
               "total_converter_costs", "total_inverter_costs", "total cable cost (€)", "total_costs"]#,
#               "area of plant"]

plant_detail=plant_detail.set_index('index')

plant_detail1=pd.DataFrame()

plant_detail1["index"]=["No. of strings", "panel per string", "string_ckts per combiner\n/array size",
                               "arrays per converter", "total arrays", "total arrays per side",
                               "total array lxw", "total array perside lxw",
                               "area of plant", "dimensions", "per side array no", "new dimensions", "array rows", "array_row_per_converter",
                               "array block y", "array length",
                               "inv per trafo", "inv per side"]

plant_detail1=plant_detail1.set_index('index')

#%%
inverter_voltages = [400., 1500., 3300.]
converter_voltages=np.multiply(inverter_voltages,factor_for_AC_to_DC)
per_trafo_rating=3e6
results={}
results1={}

for per_trafo_rating in [3, 4, 12]:

    scenario_desc="trafo_rating_"+str(int(per_trafo_rating))+"_MW"
    per_trafo_rating=per_trafo_rating*1e6
    globals()[scenario_desc]=plant_detail.copy()
    globals()[scenario_desc+"_components"]=plant_detail1.copy()
    print(scenario_desc)

    for converter_inverter_ratio in converter_inverter_ratios:
        df_index=1
        for inverter_output_voltage, converter_output_voltage in zip(inverter_voltages, converter_voltages):

            for rating in rating_range:
                combiner_power = module_power if plant_type=="battery" else 25000
                randommulti = 1
                actual_per_trafo_rating=per_trafo_rating
                if inverter_output_voltage==400.:
                    per_trafo_rating=3e6
            
#                if per_trafo_rating ==3*1e6 or per_trafo_rating ==4*1e6:
#                    combiner_power = 50000 if rating==400000 or rating==200000 or rating==450000 or rating==150000 else 25000
#                    randommulti = -1 if rating==400000 or rating==200000 or rating==450000 or rating==150000 else 1
#                else:
#                    combiner_power = 25000
#                    randommulti = 1

                per_inverter_rating = rating
    
    #            per_trafo_rating, trafo_per_plant=trafo_rating(per_inverter_rating, total_inverter_power_output, max_no_of_mech_connections_trafo)
    #            per_trafo_rating=per_trafo_rating*1e3
                
                trafo_per_plant=plant_power/per_trafo_rating

                inverter_per_trafo = (per_trafo_rating/trafo_eff)/per_inverter_rating
                if not inverter_per_trafo.is_integer():
                    inverter_per_trafo1=np.ceil(inverter_per_trafo)
                    inverter_per_trafo2=np.floor(inverter_per_trafo)
                    diff1=abs(inverter_per_trafo1-inverter_per_trafo)
                    diff2=abs(inverter_per_trafo-inverter_per_trafo2)
                    if diff1<0.5:
                        inverter_per_trafo=inverter_per_trafo1
                    elif diff2<0.5:
                        inverter_per_trafo=inverter_per_trafo2
    
    #                per_inverter_rating=per_trafo_rating/inverter_per_trafo
    #                per_inverter_rating=round(per_inverter_rating, -3)
                
                inverter_per_plant=inverter_per_trafo*trafo_per_plant
                inverter_per_plant= round_up_to_even(inverter_per_plant)
    
                if inverter_output_voltage==400. and (per_inverter_rating in list(range(200000, 550000, 50000))):# or converter_inverter_ratio in [2., 3.]):
                    per_trafo_rating=actual_per_trafo_rating
                    break
    
                if inverter_output_voltage==400.:
                    converter_inverter_ratio=1
                    converter_per_plant=inverter_per_plant
                    conv_per_inverter = inverter_per_trafo
                    per_converter_rating=per_inverter_rating/converter_inverter_ratio

                else:
                    per_converter_rating=per_inverter_rating/converter_inverter_ratio
                #            print (converter_per_plant)
                    conv_per_inverter=converter_inverter_ratio
                    converter_per_plant=conv_per_inverter*inverter_per_plant

                comb_per_converter=(per_converter_rating/combiner_power)
                if not comb_per_converter.is_integer():
                    comb_per_converter1=np.floor(per_converter_rating/combiner_power)
                    comb_per_converter2=np.ceil(per_converter_rating/combiner_power)
                    diff1=abs(comb_per_converter1-comb_per_converter)
                    diff2=abs(comb_per_converter2-comb_per_converter)
                    # print (str(comb_per_converter)+"  ")
                    if diff1<0.5:
                        comb_per_converter=comb_per_converter1
                        if comb_per_converter==0.:
                            comb_per_converter=1
                    elif diff2<0.5:
                        comb_per_converter=comb_per_converter2

                # print (str(comb_per_converter)+"\n")

                # comb_per_plant=np.ceil(total_combiner_power/combiner_power)
    
                # comb_per_converter=np.floor(comb_per_plant/converter_per_plant)
                # if comb_per_converter==0.:
                #     comb_per_converter=1
                
                total_combiner_power2=comb_per_converter*converter_per_plant*combiner_power
    
                increment=0
                while total_combiner_power2<total_combiner_power:
                    increment+=5e2
                    total_combiner_power2=comb_per_converter*converter_per_plant*(combiner_power+increment)
                combiner_power=combiner_power+increment
    
                comb_per_plant=comb_per_converter*converter_per_plant
    
                panel_per_string=0
                string_voltage=0
    
                if plant_type=="solar":
                    while string_voltage < combiner_target_voltage - module_operating_voltage:
                        string_voltage += module_operating_voltage
                        panel_per_string+=1
                        
                    string_power = panel_per_string * module_power
                    
                    #to estimate no of strings per combiner box
                    array_size=(combiner_power/string_power)
                    if not array_size.is_integer():
                        array_size1=np.floor(combiner_power/string_power)
                        array_size2=np.ceil(combiner_power/string_power)
                        diff1=abs(array_size1-array_size)
                        diff2=abs(array_size2-array_size)
                        # print (str(comb_per_converter)+"  ")
                        if diff1<0.5:
                            array_size=array_size1
                            if array_size==0.:
                                array_size=1
                        elif diff2<0.5:
                            array_size=array_size2
                    
                    
                    array_power=string_power*array_size
                    combiner_power=array_power

#                    while array_power<combiner_power:
#                        string_voltage += module_operating_voltage
#                        panel_per_string+=1
#                        string_power = panel_per_string * module_power
#                        array_power=string_power*array_size
                else:
                    array_size=0
                    array_power=module_power
                    string_voltage=combiner_target_voltage
                    string_power=array_power
    
                combiner_array_ratio = 1.0
            #    combiner_power=array_power*combiner_array_ratio
                combiner_operating_voltage=string_voltage
    
                #no of combiner for each converter
            #    comb_per_converter=np.ceil(per_converter_rating/combiner_power)
                conv_per_inverter=np.ceil(per_inverter_rating/per_converter_rating)
                converter_per_plant=conv_per_inverter*inverter_per_plant

                total_combiner=comb_per_plant
    
                total_solar_panels = array_size*panel_per_string*total_combiner

                #cable lengths

                array_length=module_height*1.5*array_size           #1.5 factor for projection considerations
                array_width=module_width*panel_per_string

# =============================================================================
# New cable calculation
# =============================================================================

    # =============================================================================
    # solar array dimensions 
    # =============================================================================
                plant_length=array_length*total_combiner/2
                plant_width=array_width*2 #+max(inv_width,inv_depth)*2+max(conv_width,conv_depth)*2+max(trafo_width, trafo_width1)*2
                plant_area=plant_length*plant_width
                optimum_plant_side=np.sqrt(plant_area)
                dimensions_info=str(round(plant_length))+"m x"+str(round(plant_width))+"m = "+str(round(plant_area))+"m2"

                perside_array_count=1
                while plant_width<optimum_plant_side:
                    perside_array_count+=1
                    plant_width=array_width*2*perside_array_count
                if perside_array_count>comb_per_converter:
                    perside_array_count=comb_per_converter
                    plant_width=array_width*2*perside_array_count
                elif comb_per_converter%perside_array_count==0:pass
                else:
                    perside_array_count1=perside_array_count
                    perside_array_count2=perside_array_count
                    while True:
                        perside_array_count1=perside_array_count1+1*randommulti
                        if comb_per_converter%perside_array_count1==0:
                            perside_array_count=perside_array_count1
                            break
                        elif comb_per_converter%perside_array_count1!=0:
                            perside_array_count2=perside_array_count2-1*randommulti
                            if comb_per_converter%perside_array_count2==0:
                                perside_array_count=perside_array_count2
                                break
#                    if (abs(perside_array_count1-perside_array_count)>abs(perside_array_count2-perside_array_count)) and (comb_per_converter%perside_array_count2==0):
#                        perside_array_count=perside_array_count2
#                    else:#if (abs(perside_array_count2-perside_array_count)>abs(perside_array_count1-perside_array_count)) and (comb_per_converter%perside_array_count1==0):
#                        perside_array_count=perside_array_count1
                    plant_width=array_width*2*perside_array_count

                plant_length=array_length*total_combiner/(2*perside_array_count)
                plant_area=plant_length*plant_width
                dimensions_info1=str(round(plant_length))+"m x"+str(round(plant_width))+"m = "+str(round(plant_area))+"m2"
                array_rows_per_conv=comb_per_converter/perside_array_count
                array_rows=(total_combiner/2)/perside_array_count
                array_block_length=array_rows_per_conv*array_length+1.5                         #1.5m for inverter installation
                array_block_width=array_width*perside_array_count
                


# =============================================================================
# Old stuff
# =============================================================================
                combiner_position = array_length/2
    
                string_cable_len=0
    
#                string_cable_lengths=[]

                if array_size==1:
                    print("array size is 1 - string to be connected direct to inverter")
                    string_cable_len+=2+2+array_width
                    longest_length_string_cmb=string_cable_len
                elif array_size%2!=0:
                   for  i in range(int(array_size//2)):
                       string_cable_len+=2+2+array_width+combiner_position-i*module_height*1.5
                       if i==0:
                           longest_length_string_cmb=string_cable_len
                   string_cable_len=string_cable_len*2
                   string_cable_len+=array_width+2 #estimated length from end of string to combiner
                elif array_size%2==0:
                   for  i in range(int(array_size//2)):
                       string_cable_len+=2+2+array_width+combiner_position-i*module_height*1.5
                       if i==0:
                           longest_length_string_cmb=string_cable_len
                   string_cable_len=string_cable_len*2
                string_cable_len+=(panel_per_string-1)*(module_width*1.25)*array_size         #interconnection between modules (module_width*1.25)m

                total_string_cable_length=string_cable_len*total_combiner
                per_unit_string_cable_length=total_string_cable_length/total_combiner

                current_output_string = string_power / string_voltage

                string_cable_size, string_cable_size_new, str_comb_receiving_voltage, str_comb_target_receiving_voltage, str_comb_new_voltage_drop, str_comb_new_voltage_drop_pu, string_cable_cost, string_comb_ckts=cable_selection (current_output_string, string_voltage, string_power, longest_length_string_cmb, 1, "DC", "solar", "Yes")
                total_string_cable_length=total_string_cable_length*string_comb_ckts
                total_string_cable_cost = string_cable_cost*total_string_cable_length


# =============================================================================
                

                if inverter_output_voltage==400.:
                    total_conv_inv_cable_len=0
                    current_output_converter = per_converter_rating/converter_output_voltage
                    per_unit_conv_inv_cable_len=total_conv_inv_cable_len/converter_per_plant
                    #type of cable
                    #adding 10% tolerance and derating factor
                    inverter_cable_size, inverter_cable_rating, inverter_cable_cost, inverter_cable_ckts = (0,0,0,0)
                    total_inverter_cable_cost=0                
                    inverter_cost_optimization=0
                    new_inverter_cable_cost=0
                    new_inverter_cable_size=0
                    new_inverter_cable_rating=0
                    conv_per_inverter=0
                    longest_length_conv_inv=0

                else:
                    conv_inv_cable_len=2 #2m cable between converter output and inverter input
                    longest_length_conv_inv=conv_inv_cable_len
                    
                    total_conv_inv_cable_len=conv_inv_cable_len*inverter_per_plant*2       #factor of 2 for +/- DC cables    
    
                    current_output_converter = per_converter_rating/converter_output_voltage

                    #type of cable
                    #adding 10% tolerance and derating factor

                    inverter_cable_size, inverter_cable_size_new, conv_inv_receiving_voltage, conv_inv_target_receiving_voltage, conv_inv_new_voltage_drop, conv_inv_new_voltage_drop_pu, inverter_cable_cost, conv_inv_ckts=cable_selection (current_output_converter, converter_output_voltage, per_converter_rating, longest_length_conv_inv, 1, "DC", "Cu", "Yes")

                    total_inverter_cable_cost=inverter_cable_cost*total_conv_inv_cable_len*conv_inv_ckts

#                    inverter_cost_optimization=cable_cost_optimization (total_inverter_cable_cost, current_output_converter, inverter_cable_ckts, total_conv_inv_cable_len,
#                                                                       converter_output_voltage, cable_type="DC")

#                    new_inverter_cable_cost=inverter_cost_optimization[0]
#                    new_inverter_cable_size=inverter_cost_optimization[1]
#                    new_inverter_cable_rating=inverter_cost_optimization[2]

    
            #    if total_inverter_cable_cost!=total_inverter_cable_cost1:
            #        print("difference 1 found")

                ###inverter to trafo cables
                if inverter_output_voltage==400.:
                    conv_per_inverter=1
                inv_trafo_cable_len=0

                inverter_per_trafo_one_side=np.ceil(inverter_per_trafo/2)

               



# =============================================================================
#               Inverter and converter prices
# =============================================================================
                lcl_df1=pd.read_excel("lcl_list.xlsx")
                
                PCS_fixed_cost=1500  #fixed cost for protection equipment
                per_inverter_price, per_inverter_semiconductor_price, per_inverter_filter_price = get_inv_price(rating, inverter_output_voltage, lcl_df1)
                
                per_inverter_price=per_inverter_price+PCS_fixed_cost #PCS_fixed_cost of 1500 euro for protection equipment
                
                total_inverter_costs=per_inverter_price*inverter_per_plant
                
                booster_df=pd.read_excel("booster_lc_list.xlsx")
                if inverter_output_voltage!=400:
                    per_converter_price, per_converter_semiconductor_price, per_converter_filter_price=get_conv_price(rating, inverter_output_voltage, booster_df)
                else:
                    per_converter_price, per_converter_semiconductor_price, per_converter_filter_price=(0,0,0)
                
                total_converter_costs=per_converter_price*converter_per_plant
                
                total_PCS_semiconductor_costs=(per_inverter_semiconductor_price+per_converter_semiconductor_price)*inverter_per_plant
                total_PCS_filter_costs=(per_inverter_filter_price+per_converter_filter_price)*inverter_per_plant
                total_PCS_fixed_costs=PCS_fixed_cost*inverter_per_plant

# =============================================================================
#               Transformer prices
# =============================================================================
                trafo_price_df=pd.read_excel("Transformer costs.xlsx")
                per_trafo_price = get_trafo_price(per_trafo_rating/1e6, inverter_output_voltage/1e3, trafo_price_df)
                total_trafo_price=per_trafo_price*trafo_per_plant
                total_switchgear_price=per_switchgear_cost*trafo_per_plant
# =============================================================================
# =============================================================================
#               plotting plant to compute cable lengths
# =============================================================================

                plt.figure()
                array_spots_x=[]
                array_spots_y=[]
                array_spots_x_oneside=[]
                array_spots_x_oneside1=[]

                array_spots_y_oneside=[]
                array_spots_x1=[]
                array_spots_y1=[]
                inv_spots_x=[]
                inv_spots_y=[]
                inv_spots_x1=[]
                inv_spots_y1=[]
                inv_spots_x2=[]
                inv_spots_y2=[]
                trafo_spots_x=[]
                trafo_spots_y=[]
                map_x=[]
                map_y=[]
                
                for i in range(int(perside_array_count*2)):
                    if i<perside_array_count:
                        array_spots_x.append((array_width/2)+array_width*i)
                        array_spots_x_oneside.append((array_width/2)+array_width*i)
                    else:
                        array_spots_x.append((array_width/2)+array_width*i+10) 

                plot_count=0
                for i in range(int(array_rows)):
                    if (i)%array_rows_per_conv==0:
                        array_spots_y.append((array_length/2)+array_length*i+1.5)#+plot_count)

                    else:
                        array_spots_y.append((array_length/2)+array_length*i+plot_count) 

                for i in range(int(array_rows*2/(array_rows_per_conv))):
                    if i >=(int(array_rows/(array_rows_per_conv))):
                        if i==(int(array_rows/(array_rows_per_conv))):
                            subtractvalue=(array_block_length)/2+(array_length*array_rows_per_conv*(i-1))+1.5
                        inv_spots_x.append(array_block_width/2+array_block_width+10)
#                        inv_spots_y.append((array_block_length)/2+(array_length*array_rows_per_conv*i)-1.5-subtractvalue)

                    else:
                        inv_spots_x.append(array_block_width/2)
                        inv_spots_y.append((array_block_length)/2+(array_length*array_rows_per_conv*i)+1.5)
                        inv_spots_x1.append(array_block_width/2)
                        inv_spots_y1.append((array_block_length)/2+(array_length*array_rows_per_conv*i)+1.5)
                inv_spots_y=inv_spots_y+inv_spots_y

                
                mid_index=int(len(inv_spots_x)/2)
                
                j=0
                l=0
                
                for i in range(len(inv_spots_x)):
                    if i in list(range(0,len(inv_spots_x),2)):
                        inv_spots_x2.append(inv_spots_x[:mid_index][j])
                        inv_spots_y2.append(inv_spots_y[:mid_index][j])
                        j+=1
                    else:
                        inv_spots_x2.append(inv_spots_x[mid_index:][l])
                        inv_spots_y2.append(inv_spots_y[mid_index:][l])
                        l+=1

                for i in range(int(trafo_per_plant)):
                    trafo_spots_x.append((max(array_spots_x)/2+array_width/4))
                    trafo_spots_y.append((max(array_spots_y)/(2*trafo_per_plant))+i*max(array_spots_y)/(trafo_per_plant))              

                for i in range(len(array_spots_y)):
                    for j in range(len(array_spots_x)):
#                        plt.plot(array_spots_x[j], array_spots_y[i], 'b.')
                        array_spots_x1.append(array_spots_x[j])
                        array_spots_y1.append(array_spots_y[i])
                for i in range(int(array_rows_per_conv)):
                        array_spots_x_oneside1=array_spots_x_oneside1+array_spots_x_oneside
                        
                # plt.plot(array_spots_x1, array_spots_y1, 'bs', label="PV array") 
                
                array_colors=["b.","b.","b.","b."]#["ks","ms","rs","cs"]
                colorcount=0
                for i in range(len(array_spots_y1)):
                    # while i < trafo_per_plant:
                    # plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], label="inverter")
                    if i+1 == (len(array_spots_y1)):
                        plt.plot(array_spots_x1[i], array_spots_y1[i], array_colors[colorcount], markersize=14, label="PV array")
                    else:
                        plt.plot(array_spots_x1[i], array_spots_y1[i], array_colors[colorcount], markersize=14)
                    if (i+1)%(inverter_per_trafo*comb_per_converter)==0:
                        colorcount+=1
                
                inv_colors=["kx","mx","rx","cx"]
                colorcount=0
                for i in range(int(inverter_per_plant)):
                    # while i < trafo_per_plant:
                    # plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], label="inverter")
                    if i+1 == (inverter_per_plant):
                        plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], markersize=14, label="inverter")
                    else:
                        plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], markersize=14)
                    if (i+1)%inverter_per_trafo==0:
                        colorcount+=1
                # plt.plot(-100, -100, "kx", label="inverter")

                plt.plot(trafo_spots_x, trafo_spots_y, 'go', label="transformer", markersize=14)


                plt.xlim([-50, plant_width*1.1])
                plt.ylim([-50, 350])
                plt.xticks([0, 50, 100, 150, 200, 250, 300,  max(array_spots_x1)], fontsize=16)
                plt.yticks([0, 50, 100, 150, 200, 250, max(array_spots_y1)], fontsize=16)
                plt.axis('scaled')
                plt.axis('equal')
                plt.xlabel('plant width (m)', fontsize=16, fontweight = "bold")
                plt.ylabel('plant length (m)', fontsize=16, fontweight = "bold")
                plt.legend(fontsize=15)
                plt.title("PV plant layout\n"+" ".join(scenario_desc.split('_'))+'\nArray per PCS:'+str(comb_per_converter)+'\nPCS Power:'+str(per_inverter_rating/1e3)+'kW'+'\nPCS per transformer:'+str(inverter_per_trafo), fontsize=16, fontweight = "bold")
                # plt.tight_layout()
                fig = plt.gcf()
                fig.set_size_inches(17.5, 11.5)
                if per_trafo_rating==3*1e6 and inverter_output_voltage==1500 and per_inverter_rating==450000:
                    plt.savefig((str(int(per_inverter_rating/1e3))+'kW'), dpi=600, bbox_inches='tight', quality=95,  filetype="png")  

# =============================================================================
#               length of array to inverter cables
# =============================================================================
                cable_length_array_converter=0
                cable_list_array_converter=[]
                count=0
                for i in range(int(len(array_spots_x_oneside)*array_rows_per_conv)):
                    length_x=abs(array_spots_x_oneside1[i]-inv_spots_x1[count])
                    length_y=abs(array_spots_y1[i]-inv_spots_y1[count])
                    cable_list_array_converter.append(length_x+length_y+4)
                    cable_length_array_converter+=length_x+length_y+4

                cable_length_array_converter=cable_length_array_converter*2*converter_per_plant

                total_comb_conv_cable_len=cable_length_array_converter
                current_output_combiner = array_power/combiner_operating_voltage

                #type of cable
                #adding 10% tolerance and derating factor
                longest_length_cmb_conv=max(cable_list_array_converter)
                avg_length_cmb_conv=np.mean(cable_list_array_converter)
                combiner_cable_size, combiner_cable_size_new, comb_conv_receiving_voltage, comb_conv_target_receiving_voltage, comb_conv_new_voltage_drop, comb_conv_new_voltage_drop_pu, combiner_cable_cost, comb_conv_ckts=cable_selection (current_output_combiner, combiner_operating_voltage, combiner_power, avg_length_cmb_conv*2, 1, "DC", "Cu", "Yes")

                total_converter_cable_cost=combiner_cable_cost*total_comb_conv_cable_len*comb_conv_ckts



# =============================================================================
#               length of inverter to trafo cables
# =============================================================================
                cable_length_inv_trafo=0
                cable_list_inv_trafo=[]
                count=0
                for i in range(int(inverter_per_trafo)):
                    length_x=abs(inv_spots_x2[i]-trafo_spots_x[count])
                    length_y=abs(inv_spots_y2[i]-trafo_spots_y[count])
                    cable_list_inv_trafo.append(length_x+length_y+4)
                    cable_length_inv_trafo+=length_x+length_y+4

                cable_length_inv_trafo=cable_length_inv_trafo*(3+with_neutral)*trafo_per_plant
                
                total_inv_trafo_cable_len= cable_length_inv_trafo     #factor of 3 for 3 phase AC cables and factor of 2 for inverter on both sides


                current_output_inverter = per_inverter_rating/(np.sqrt(3)*inverter_output_voltage)


                longest_length_inv_trafo=max(cable_list_inv_trafo)
                avg_inv_trafo_lengths=np.mean(cable_list_inv_trafo)
                
                trafo_cable_size, trafo_cable_size_new, inv_trafo_receiving_voltage, inv_trafo_target_receiving_voltage, inv_trafo_new_voltage_drop, inv_trafo_new_voltage_drop_pu, trafo_cable_cost, inv_trafo_ckts=cable_selection (current_output_inverter, inverter_output_voltage, per_inverter_rating, avg_inv_trafo_lengths, 1, "AC", "Cu", "Yes")
                
                
                individual_inv_trafo_vdrops = np.multiply(cable_list_inv_trafo, (1e-3*inv_trafo_new_voltage_drop_pu*current_output_inverter/inv_trafo_ckts/inverter_output_voltage))
                avg_inv_trafo_vdrop=np.mean(individual_inv_trafo_vdrops)

                total_inv_trafo_cable_len=total_inv_trafo_cable_len*inv_trafo_ckts
                total_trafo_cable_cost=trafo_cable_cost*total_inv_trafo_cable_len
                total_DC_cabling=total_string_cable_cost+total_converter_cable_cost+total_inverter_cable_cost
                total_AC_cabling=total_trafo_cable_cost
                total_cables_cost=total_string_cable_cost+total_converter_cable_cost+total_inverter_cable_cost+total_trafo_cable_cost
                total_costs=total_cables_cost+total_inverter_costs+total_converter_costs+total_trafo_price+total_switchgear_price
    # =============================================================================

                globals()[scenario_desc][df_index]=[plant_power, total_solar_panels,
                               string_power,string_voltage,array_size*total_combiner, panel_per_string, string_cable_size,
                               current_output_string, string_cable_size_new, total_string_cable_length, array_size,
                               array_power, total_combiner, array_length, array_width, combiner_power, combiner_operating_voltage, comb_per_converter, combiner_power*total_combiner,
                               per_converter_rating, converter_output_voltage, converter_per_plant, combiner_cable_size, current_output_combiner,
                               combiner_cable_size_new, comb_per_converter, total_comb_conv_cable_len,
                               per_inverter_rating, inverter_output_voltage, inverter_per_plant, inverter_cable_size, current_output_converter,
                               inverter_cable_rating, conv_per_inverter, total_conv_inv_cable_len,
                               per_trafo_rating, trafo_per_plant, trafo_cable_size, current_output_inverter,
                               trafo_cable_size_new, inverter_per_trafo, total_inv_trafo_cable_len, inv_trafo_ckts,
                               trafo_cable_size, trafo_cable_size_new, inv_trafo_receiving_voltage, inv_trafo_target_receiving_voltage,inv_trafo_new_voltage_drop,
                               longest_length_string_cmb, longest_length_cmb_conv, longest_length_conv_inv, longest_length_inv_trafo, individual_inv_trafo_vdrops, avg_inv_trafo_vdrop,
                               cable_list_array_converter, cable_length_array_converter, cable_list_inv_trafo, cable_length_inv_trafo, inv_spots_x2, inv_spots_y2, trafo_spots_x, trafo_spots_y,
                               total_PCS_semiconductor_costs, total_PCS_filter_costs, total_PCS_fixed_costs, total_trafo_price, total_switchgear_price,
                               total_string_cable_cost, total_converter_cable_cost, total_inverter_cable_cost, total_trafo_cable_cost,
                               total_DC_cabling, total_AC_cabling,
                               total_converter_costs, total_inverter_costs, total_cables_cost, total_costs]#,
                               #dimensions_info]          

                globals()[scenario_desc+"_components"][df_index]=[array_size*total_combiner, panel_per_string, array_size,
                               comb_per_converter, total_combiner, total_combiner/2,
                               np.sqrt(total_combiner), np.sqrt(total_combiner/2),
                               plant_area, dimensions_info, perside_array_count, dimensions_info1, array_rows, array_rows_per_conv,
                               array_block_length, array_length,
                               inverter_per_trafo, inverter_per_trafo_one_side]

                df_index+=1
                per_trafo_rating=actual_per_trafo_rating


    results.update({scenario_desc:globals()[scenario_desc]})
    results1.update({scenario_desc:globals()[scenario_desc+"_components"]})

#    results.update({scenario_desc+"_vdrop":globals()[scenario_desc].iloc[-6:-7,:]})


#%%
#plant_cable_and_area=plant_cable_and_area.set_index('index')
#plant_cable_and_area_transposed = plant_cable_and_area.T#.reset_index(drop=True) 
#%%
max_costs=[]
scenarios=list(results.keys())
for i in range(len(results)):
    cost_min_index=(results[scenarios[i]].iloc[len(results[scenarios[i]])-1,:]).values.argmin()
    print("min cost index ",cost_min_index)
    min_cost=(results[scenarios[i]].iloc[len(results[scenarios[i]])-1,:]).min()
    print("min cost", min_cost)
    if i==2:
        max_cost=(results[scenarios[i]].iloc[len(results[scenarios[i]])-1,:]).max()
        max_costs.append(max_cost)
        print("max cost", max_cost)
#%%

#for i in range(len(results)):
#    cost_length_plots(scenarios[i], results[scenarios[i]], max(max_costs))
#    cost_compare_plots(scenarios[i], results[scenarios[i]], max(max_costs))
#    cost_breakdown_plots(scenarios[i], results[scenarios[i]])
#    PCS_cost_breakdown_plots(scenarios[i], results[scenarios[i]])

#%%
#for i in range(len(results)):
#    vdrop_plots(scenarios[i], results[scenarios[i]])#, max(max_costs))
#    
#%%
#for i in range(len(results)):
#    cross_section_plots(scenarios[i], results[scenarios[i]])#, max(max_costs))
#%%
#for i in range(len(results)):
#    avg_vdrop_plots(scenarios[i], results[scenarios[i]])#, max(max_costs))
    
#%%

#ax3 = plt.subplot(313)
#cost_compare_plots(scenarios[2], results[scenarios[2]], 1e6)
#plt.gcf()
##plt.xticks(rotation=90)
#plt.grid(linestyle=':', linewidth=0.5)
#plt.ylim([0, 1e6])
#plt.title("Total Cable Costs ")
#plt.legend()
#plt.xlabel("Scenarios")
#
#ax1 = plt.subplot(311, sharex=ax3)
#cost_compare_plots(scenarios[0], results[scenarios[0]], 1e6)
#plt.title("Total Cable Costs ")
#
#ax2 = plt.subplot(312, sharex=ax3)
#cost_compare_plots(scenarios[1], results[scenarios[1]], 1e6)


# Set data
#plt.figure()
#for j in range(1):#len(results[scenarios[0]].columns)):
#
#    df=pd.DataFrame({
#    "total_converter_costs":[results[scenarios[1]].iloc[results[scenarios[1]].index.get_loc("total_converter_costs"),2]],
#    "total_inverter_costs":[results[scenarios[1]].iloc[results[scenarios[1]].index.get_loc("total_inverter_costs"),2]],
#    "total cable cost (€)":[results[scenarios[1]].iloc[results[scenarios[1]].index.get_loc("total cable cost (€)"),2]],
#    })
#    #rand_index=results[scenarios[0]].index.get_loc("total_converter_costs")
#    #results[scenarios[0]].iloc[rand_index,1]
#    
#     
#    # number of variable
#    categories=list(df)[:]
#    N = len(categories)
#     
#    # We are going to plot the first line of the data frame.
#    # But we need to repeat the first value to close the circular graph:
#    values=df.loc[0].values.flatten().tolist()
#    values += values[:1]
#    values
#     
#    # What will be the angle of each axis in the plot? (we divide the plot / number of variable)
#    angles = [n / float(N) * 2 * np.pi for n in range(N)]
#    angles += angles[:1]
#     
#    # Initialise the spider plot
#    plot_no=541+j
#    ax = plt.subplot(111, polar=True)
#     
#    # Draw one axe per variable + add labels labels yet
#    plt.xticks(angles[:-1], categories, color='grey', size=8)
#     
#    # Draw ylabels
#    ax.set_rlabel_position(0)
#    #plt.yticks([10,20,30], ["10","20","30"], color="grey", size=7)
#    #plt.ylim(0,40)
#     
#    # Plot data
#    ax.plot(angles, values, linewidth=1, linestyle='solid')
#     
#    # Fill area
#    ax.fill(angles, values, 'b', alpha=0.1)
#    
#trafo_rating_3_MW.to_excel("PV_3MW.xlsx")
#trafo_rating_4_MW.to_excel("PV_4MW.xlsx")
#trafo_rating_12_MW.to_excel("PV_12MW.xlsx")