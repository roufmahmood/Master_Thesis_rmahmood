# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors as mcolors
import matplotlib as mlt
import matplotlib.patches as mpatches


def round_up_to_even(f):
    return np.ceil(f / 2.) * 2
# =============================================================================
# function for derating factors
# =============================================================================

def derating_bundled (no_of_ckts):
    derating_table=pd.read_excel("derating_factors.xlsx", index_col=0)      #taken from Lapp T33
    no_of_ckts=int(no_of_ckts)
    if no_of_ckts<10:
        factor=derating_table.iloc[0,no_of_ckts-1]
#    elif no_of_ckts>10 and no_of_ckts <=12:
#        factor=derating_table.iloc[0,10]
    return (factor)
# =============================================================================
# function to extract cable details after voltage drop considerations (size, ampacity, price)
# =============================================================================
#%%
def cable_selection (current, voltage_level, device_rating, length_of_cable, no_cable_run, cable_type, cable_material, consider_vdrop, bundling):
    factor_for_temperature = 0.91 #for 40degrees
    if bundling >9:
        bundling=np.ceil(bundling/2)
#        bundling =8
        return cable_selection (current, voltage_level, device_rating, length_of_cable, no_cable_run, cable_type, cable_material, consider_vdrop, bundling)
    factor_for_bundling = derating_bundled (bundling)
    
    
    current_correction = current*1.1       #overcurrent percentage 10%
    current_correction = current_correction/(factor_for_temperature*factor_for_bundling)
    
    
    if cable_type=="DC":
        original_current=device_rating/voltage_level
        target_vdrop_pct=0.01
        length_of_cable=length_of_cable*2

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

#    for i in range(len(df)):
#        if (current*1.1)<df.iloc[i,1]:
##            cable_cost=df.iloc[i,2]/100
#            cable_old_size=df.iloc[i,0]
##            cable_current=df.iloc[i,1]
#            break

    for i in range(len(df)):
        if cable_size==df.iloc[i,0]:
            if cable_type=="AC":
                voltagedrop_pu=df.iloc[i,5]             #per V/(A/km)
            elif cable_type=="DC":
                if cable_material=="Cu":
                    voltagedrop_pu=df.iloc[i,6]
                elif cable_material=="solar":
                    voltagedrop_pu=df.iloc[i,5]             #per V/(A/km)
            cable_weight=df.iloc[i,4]
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
                cable_weight=df.iloc[i,4]
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
        receiving_voltage=0
        target_receiving_voltage=0
        new_voltage_drop=0
        new_voltage_drop_pu=0
        cable_weight=0
    
    if cable_size>300:
        print ("check problem")
    return cable_size, voltagedrop_compensate, receiving_voltage, target_receiving_voltage, new_voltage_drop, new_voltage_drop_pu, compensate_cable_cost, no_cable_run, cable_weight
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
    
    for i in range(len(plant_details.columns)):
        if plant_details.iloc[acvolt_index,i]==inverter_voltages[0]:
            total_cost_comparison.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            total_cost_comparison.at[new_count,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter per plant"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
            new_count1+=1
        elif plant_details.iloc[acvolt_index,i]==inverter_voltages[1]:
            total_cost_comparison.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            total_cost_comparison.at[new_count1,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter per plant"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
            new_count2+=1
        else:
            total_cost_comparison.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            total_cost_comparison.at[new_count1+new_count2,"PCS Power: "+str(int(plant_details.iloc[invpower_index,i]/1e3))+"kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter per plant"),i]))]=(round(plant_details.iloc[cost_index,i], 2))#+"M"
    
    total_cost_comparison=total_cost_comparison.T
    total_cost_comparison=total_cost_comparison.rename(columns=total_cost_comparison.iloc[0]).drop(total_cost_comparison.index[0])
    return total_cost_comparison
#%%
def cost_compare_1(plant_details):
    cost_comparison=pd.DataFrame()
    length_comparison=pd.DataFrame()
    
    for new_count in range(len(plant_details.columns)):
        cost_comparison.at[new_count,"index"]="Inv Voltage:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+"kV\nInv & Conv\nPower:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3)+"kW"

        cost_comparison.at[new_count,"total battery cable cost"]=plant_details.iloc[plant_details.index.get_loc("total_battery_cable_cost"), new_count]
        cost_comparison.at[new_count,"total inverter cable cost"]=plant_details.iloc[plant_details.index.get_loc("total_inverter_cable_cost"), new_count]
        cost_comparison.at[new_count,"total trafo cable cost"]=plant_details.iloc[plant_details.index.get_loc("total_trafo_cable_cost"), new_count]
        
        length_comparison.at[new_count,"index"]="Inv Voltage:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+"kV\nInv & Conv\nPower:"+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3)+"kW"

        length_comparison.at[new_count,"total batt conv cable len"]=plant_details.iloc[plant_details.index.get_loc("total_batt_conv_cable_len"), new_count]
        length_comparison.at[new_count,"total conv inv cable len"]=plant_details.iloc[plant_details.index.get_loc("total_conv_inv_cable_len"), new_count]
        length_comparison.at[new_count,"total inv trafo cable len"]=plant_details.iloc[plant_details.index.get_loc("total_inv_trafo_cable_len"), new_count]


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
        cost_comparison.at[new_count,"index"]="Inv Voltage: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+" kV\nPCS Power: "+str(int((plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3))+" kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter per plant"), new_count]))

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
        cost_comparison.at[new_count,"index"]="Inv Voltage: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Output Voltage (V)"), new_count])/1e3)+" kV\nPCS Power: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter Power (W)"), new_count])/1e3)+" kW\nPCS Units: "+str(int(plant_details.iloc[plant_details.index.get_loc("Inverter per plant"), new_count]))
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
    cost_comparison=cost_compare(results_df)
    x=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,0], 'bo', label=cost_comparison.keys()[0]+"V\nbase case\n(4 x 3 MW Trafo)")
    y=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,1], 'r-', label=cost_comparison.keys()[1]+"V")
    z=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,2], 'm-', label=cost_comparison.keys()[2]+"V")
    
    
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(np.multiply([0, .25, 0.5, 0.75, 1, 1.25],1e6),[0, "0.25 M", "0.50 M", "0.75 M","1 M","1.25 M"], fontsize=8)
    plt.grid(linestyle=':', linewidth=1.5)
    plt.ylim([0, maximum*1.17])
    plt.title("Battery Plant\nTotal Costs (€) with\nper "+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(loc="lower right", fontsize=8)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('Total costs (€)', fontsize=8, fontweight="bold")
    fig = plt.gcf()
    fig.set_size_inches(6.3, 4.5)
    fig.tight_layout()
    fig.savefig("batt"+scenario+"_cost_comparison", dpi=2000, quality=95, bbox_inches='tight', filetype="jpeg")    
    return (x,y,z)

#%%
def cost_length_plots(scenario, results_df, maximum):
    fig, (ax1,ax2) = plt.subplots(2, 1)

    cost_compare, length_comparison=cost_compare_1(results_df)
    length_comparison=length_comparison*1e-3
    cost_compare.plot.bar(ax=ax1, stacked=True, grid=True, sharex=True, legend=True, title="Battery Plant\n"+str(plant_power/1e6)+"MW power plant\n"
                          +"per "+" ".join(scenario.split('_')), ylim=[0, maximum*1.1], fontsize=16)
    ax1.set_ylabel('Total costs (€)', fontsize=16)
    length_comparison.plot.bar(ax=ax2, stacked=True, legend=True, grid=True, ylim=[0, 10])
    ax2.set_ylabel('Total length (km)', fontsize=16)
    ax2.set_xlabel('Scenarios', fontsize=16)
    plt.yticks(fontsize=16)
    plt.xticks(fontsize=16)
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.tight_layout()
    fig.savefig("batt"+scenario, dpi=1000, quality=95, bbox_inches='tight', filetype="png") 
    return fig
#%%
def cost_breakdown_plots(scenario, results_df):
    fig, ax1 = plt.subplots(1, 1)

    cost_compare=np.divide(cost_breakdown(results_df),1)
    cost_compare.plot.bar(ax=ax1, stacked=True, sharex=True, legend=True)#, ylim=[0, maximum*1.1])

    ax1.set_title(("Battery Plant\n"+str(int(plant_power/1e6))+"MW battery power plant total costs breakdown (€)\n"+"with per "+" ".join(scenario.split('_'))),fontsize=8, fontweight="bold")
    ax1.legend(fontsize=8)
    ax1.set_ylabel('Total costs in (€)', fontsize=7, fontweight="bold")
    ax1.set_xlabel('Scenarios', fontsize=7, fontweight="bold")
    plt.yticks(np.multiply([0, .25, 0.5, 0.75, 1, 1.25, 1.5],1e6),[0, "0.25 M", "0.50 M", "0.75 M","1 M","1.25 M","1.50 M"], fontsize=8)
    plt.xticks(fontsize=6.5)
    plt.grid(linestyle=':', linewidth=0.5)
    fig = plt.gcf()
    fig.set_size_inches(8, 4.57)
    fig.savefig("batt"+scenario+"_cost_breakdown", dpi=2000, quality=95, bbox_inches='tight', filetype="jpeg") 
        
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
    plt.title("Battery Plant\nVoltage Drop "+" ".join(scenario.split('_')))
    plt.legend(fontsize=14)
    plt.xlabel("Scenarios", fontsize=16)
    plt.ylabel('V', fontsize=16)
    fig = plt.gcf()
    fig.set_size_inches(18.5, 10.5)
    fig.savefig("batt"+scenario+"_voltage_drop", dpi=1000, quality=95, bbox_inches='tight', filetype="png")  
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
            crosssection_df.at[new_count,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count,"Scenario"]=str(int(inverter_voltages[0]))
            new_crosssection_df.at[new_count,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
            new_count1+=1
        elif results_df.iloc[acvolt_index,i]==inverter_voltages[1]:
            crosssection_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            crosssection_df.at[new_count1,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            new_crosssection_df.at[new_count1,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
            new_count2+=1
        else:
            crosssection_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            crosssection_df.at[new_count1+new_count2,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[crosssection_index,i], 2))#+"M"
            new_crosssection_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            new_crosssection_df.at[new_count1+new_count2,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=(round(results_df.iloc[new_crosssection_index,i], 2))#+"M"
    
    crosssection_df=crosssection_df.T
    crosssection_df=crosssection_df.rename(columns=crosssection_df.iloc[0]).drop(crosssection_df.index[0])
    new_crosssection_df=new_crosssection_df.T
    new_crosssection_df=new_crosssection_df.rename(columns=new_crosssection_df.iloc[0]).drop(new_crosssection_df.index[0])
    
    plt.figure()

    x=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,0], 'bo', label=crosssection_df.keys()[0]+"V cross-section before derating")
#    a=plt.plot(list((vdrop_df.index[:])), [400*0.995 for l in range(len(vdrop_df.iloc[:,0]))], 'go', label=vdrop_df.keys()[0]+"V voltage drop limit")
    x1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,0], 'ro', label=new_crosssection_df.keys()[0]+"V cross-section after derating")

    y=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,1], 'g-', label=crosssection_df.keys()[1]+"V cross-section before derating")
#    b=plt.plot(list((vdrop_df.index[:])), [1500*0.995 for l in range(len(vdrop_df.iloc[:,1]))], 'c-', label=vdrop_df.keys()[1]+"V voltage drop limit")
    y1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,1], 'y-', label=new_crosssection_df.keys()[1]+"V cross-section after derating")

    z=plt.plot(list((crosssection_df.index[:])), crosssection_df.iloc[:,2], 'm-', label=crosssection_df.keys()[2]+"V cross-section before derating")
#    c=plt.plot(list((vdrop_df.index[:])), [3300*0.995 for l in range(len(vdrop_df.iloc[:,2]))], 'y-', label=vdrop_df.keys()[2]+"V voltage drop limit")
    z1=plt.plot(list((new_crosssection_df.index[:])), new_crosssection_df.iloc[:,2], 'b-', label=new_crosssection_df.keys()[2]+"V cross-section after derating")

    plt.ylim([0, 250])
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(linestyle=':', linewidth=0.5)
#    plt.ylim([0, maximum*1.1])
    plt.title("Battery Plant\nCable cross section for derating correction between Inverter & Transformer\n"+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(fontsize=7)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('Cable cross-section (mm2)', fontsize=8, fontweight="bold")
    fig = plt.gcf()
    fig.set_size_inches(6, 3)
    fig.savefig("batt"+scenario+"_cross_section", dpi=2000, quality=95, bbox_inches='tight', filetype="png")  
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
            vdrop_df.at[new_count,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
            new_count1+=1
        elif results_df.iloc[acvolt_index,i]==inverter_voltages[1]:
            vdrop_df.at[new_count1,"Scenario"]=str(int(inverter_voltages[1]))
            vdrop_df.at[new_count1,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
            new_count2+=1
        else:
            vdrop_df.at[new_count1+new_count2,"Scenario"]=str(int(inverter_voltages[2]))
            vdrop_df.at[new_count1+new_count2,"PCS Power:\n"+str(int(results_df.iloc[invpower_index,i]/1e3))+"kW"]=((results_df.iloc[vdrop_index,i]))#+"M"
    
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
    plt.title("Battery Plant\nAverage voltage drop between Inv-Trafo considering average cable length\nper "+" ".join(scenario.split('_')), fontsize=8, fontweight="bold")
    plt.legend(fontsize=8)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('V drop %', fontsize=8, fontweight="bold")
    plt.ylim([0, 1])
    fig = plt.gcf()
    fig.set_size_inches(6, 3)

    fig.savefig("batt"+scenario+"_avg_vdrop", dpi=1000, quality=95, bbox_inches='tight', filetype="png")  
    return (y,c)#(x,y,z,c)

#%%
# =============================================================================
# Solar or Battery Module details
# =============================================================================
plant_type="battery" # "solar" or "battery"
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
    #model taken from Samsung ESS model M8068 P2
    rack_power=55.5000*1e3#float(input('Enter power of single solar or battery module (W): '))       #Enter power of a single solar or battery module/rack
    module_operating_voltage=902#float(input('Enter operating voltage of module (V):'))         #Enter solar or battery modules operating voltage
    module_depth=0.702#float(input('Enter height of single module (mm):'))/1000                  #Enter height of solar/battery module, converted to m
    module_width=0.442
    module_height=2.124-0.16
    combiner_target_voltage= module_operating_voltage
    rating_range=range(150000, 550000, 50000)
    converter_inverter_ratios= [1.]
    
# =============================================================================
# Inv price
# =============================================================================
# device_list_df=pd.read_excel("sic_devices.xlsx")
# device_list_df.at[:, 'Current @25degC']=np.divide(device_list_df.iloc[:,0],(np.sqrt(3)*device_list_df.loc[:,"Voltage"]))
# price_per_module=728.63098        #€ per unit from digikey for more than 51 Nos
# for i in range(len(device_list_df)):
#     if device_list_df.loc[i, 'Level']==2:
#         modules_per_inv=3
#     elif device_list_df.loc[i, 'Level']==3:
#         modules_per_inv=9
#     elif device_list_df.loc[i, 'Level']==5:
#         modules_per_inv=18
#     device_list_df.at[i, 'No. of SiC\npower modules\nper inverter']=modules_per_inv
#     device_list_df.at[i, 'Cost of SiC devices\nper inverter']=modules_per_inv*price_per_module
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
plant_detail["index"]=["Plant Power (W)", "Trafo per plant", "Trafo Power",
            "Inverter per plant", "Inverter per Trafo", "Converter Power (W)", "Inverter Power (W)",  "Inverter Output Voltage (V)",
            "Battery rack power", "Battery rack power per converter","No of battery racks per conv",
            "battery array depth", "battery array width", "multipler",
            "inverter_cable_size", "inverter_cable_size_new",
            "cable_length_batt_converter", "cable_list_batt_converter", "cable_length_inv_trafo", "cable_list_inv_trafo",
            "Plant length", "Plant width", "Plant dimensions",
            "rec_volt", "new voltage drop", "orig_cable_size", "vdrop_compensate","avg inv trafo individual v drop",
            "total_batt_conv_cable_len", "total_conv_inv_cable_len", "total_inv_trafo_cable_len", "total trafo cable weight",
            "perMW_batt_conv_cable", "perMW_conv_inv_cable", "perMW_inv_trafo_cable",
            "total PCS semiconductor costs", "total PCS filter costs", "total PCS fixed costs", "total transformer costs", "total switchgear costs", 
            "total AC cabling cost", "total DC cabling cost", "total_converter_costs", "total_inverter_costs",
            "total_battery_cable_cost", "total_inverter_cable_cost", "total_trafo_cable_cost",
            "total cable cost (€)", "total_costs"]



plant_detail=plant_detail.set_index('index')


#%%

inverter_voltages = [400., 1500., 3300.]
converter_voltages=np.multiply(inverter_voltages,factor_for_AC_to_DC)
results={}

for per_trafo_rating in [3, 4, 12]:

    scenario_desc="trafo_rating_"+str(int(per_trafo_rating))+"_MW"
    per_trafo_rating=per_trafo_rating*1e6
    globals()[scenario_desc]=plant_detail.copy()
    print(scenario_desc)

    for converter_inverter_ratio in converter_inverter_ratios:
        df_index=1
        for inverter_output_voltage, converter_output_voltage in zip(inverter_voltages, converter_voltages):

            for rating in rating_range:
                combiner_power = rack_power if plant_type=="battery" else 25000
                per_inverter_rating = rating
                actual_per_trafo_rating=per_trafo_rating
                if inverter_output_voltage==400.:
                    per_trafo_rating=3e6
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
#                inverter_per_plant= round_up_to_even(inverter_per_plant)
    
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


                battery_power=rack_power
                batteryrack_per_conv=1
                while battery_power<per_converter_rating:
                    batteryrack_per_conv+=1
                    battery_power=battery_power+rack_power
                
                
                battery_array_width=batteryrack_per_conv*module_width
                battery_array_depth=module_depth
                
                
                batteryrack_per_plant=batteryrack_per_conv*converter_per_plant
                
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
    # =============================================================================
    # plant dimensions 
    # =============================================================================
                multiplier=4 if rating<250000 else 2
                plant_length=battery_array_depth*converter_per_plant/multiplier
                plant_width=battery_array_width*multiplier+max(inv_width,inv_depth)*multiplier+max(conv_width,conv_depth)*multiplier+max(trafo_width, trafo_width1)*2
                plant_area=plant_length*plant_width
                dimensions_info=str(round(plant_length))+"m x"+str(round(plant_width))+"m = "+str(round(plant_area))+"m2"
    # =============================================================================
    
    
                plt.figure()
                battery_spots_x=[]
                battery_spots_y=[]
                battery_spots_x1=[]
                battery_spots_y1=[]
                inv_spots_x=[]
                inv_spots_y=[]
                inv_spots_x1=[]
                inv_spots_y1=[]
                trafo_spots_x=[]
                trafo_spots_y=[]
                trafo_spots_x1=[]
                trafo_spots_y1=[]
                map_x=[]
                map_y=[]
                
                for i in range(int(batteryrack_per_conv*multiplier)):
                    battery_spots_x.append((module_width/2)+module_width*i)

                plot_count=0
                for i in range(int(inverter_per_plant/multiplier)):
                    if i>0 and i%2==0:
                        battery_spots_y.append((module_depth/2)+module_depth*i+module_width*2+plot_count)
                        plot_count+=module_width*2
                    else:
                        battery_spots_y.append((module_depth/2)+module_depth*i+plot_count)

                for i in range(int(4)):
                    buffer_dist=1.5
                    inv_spots_x.append(max(battery_spots_x)+(module_width/2)+inv_width+conv_width+buffer_dist+(inv_width+conv_width+1)*i)
                    
                plot_count=0


                inv_row=np.ceil(inverter_per_plant/4)
                for i in range(int(inv_row)):
                    inv_spots_y.append((max(battery_spots_y))/(inv_row*2)+i*((max(battery_spots_y)+(module_depth/2))/inv_row))

                trafo_spots_x.append(max(inv_spots_x)+((inv_width+conv_width)/2)+trafo_width/2+3)
               
                plot_count=0
                for i in range(int(trafo_per_plant)):
                    trafo_spots_y.append((max(inv_spots_y))/(trafo_per_plant*2)+i*((max(inv_spots_y)+(module_depth/2))/trafo_per_plant))



                for i in range(len(battery_spots_y)):
                    for j in range(len(battery_spots_x)):
#                        plt.plot(battery_spots_x[j], battery_spots_y[i], "b.")
                        battery_spots_x1.append(battery_spots_x[j])
                        battery_spots_y1.append(battery_spots_y[i])
                # plt.plot(battery_spots_x1, battery_spots_y1, "bs", label="battery racks")
                for i in range(len(inv_spots_y)):
                    for j in range(len(inv_spots_x)):
#                        plt.plot(inv_spots_x[j], inv_spots_y[i], 'kx')
                        inv_spots_x1.append(inv_spots_x[j])
                        inv_spots_y1.append(inv_spots_y[i])
                    if len(inv_spots_x1)>inverter_per_plant and len(inv_spots_y1)>inverter_per_plant:
                        drop_indexes=abs(len(inv_spots_x1)-inverter_per_plant)
                        for drop in range(int(drop_indexes)):
                            inv_spots_x1.pop()
                            inv_spots_y1.pop()
                battery_colors=["bs","bs","bs","bs"]#["ks","ms","rs","cs"]
                colorcount=0
                for i in range(len(battery_spots_y1)):
                    # while i < trafo_per_plant:
                    # plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], label="inverter")
                    if i+1 == (len(battery_spots_y1)):
                        plt.plot(battery_spots_x1[i]+3, battery_spots_y1[i]+2.5, battery_colors[colorcount], markersize=13, label="battery racks")
                    else:
                        plt.plot(battery_spots_x1[i]+3, battery_spots_y1[i]+2.5, battery_colors[colorcount], markersize=13)
#                    if (i+1)%(inverter_per_trafo*batteryrack_per_conv)==0:
#                        colorcount+=1
                inv_colors=["kx","mx","rx","cx"]
                colorcount=0
                for i in range(int(inverter_per_plant)):
                    # while i < trafo_per_plant:
                    # plt.plot(inv_spots_x2[i], inv_spots_y2[i], inv_colors[colorcount], label="inverter")
                    if i+1 == (inverter_per_plant):
                        plt.plot(inv_spots_x1[i]+3, inv_spots_y1[i]+2.5, inv_colors[colorcount], markersize=14, label="inverter")
                    else:
                        plt.plot(inv_spots_x1[i]+3, inv_spots_y1[i]+2.5, inv_colors[colorcount], markersize=14)
                    if (i+1)%inverter_per_trafo==0:
                        colorcount+=1
                # plt.plot(inv_spots_x1, inv_spots_y1, 'kx', label="inverter")
                for i in range(len(trafo_spots_y)):
                    for j in range(len(trafo_spots_x)):
#                        plt.plot(trafo_spots_x[j], trafo_spots_y[i], 'go')
                        trafo_spots_x1.append(trafo_spots_x[j])
                        trafo_spots_y1.append(trafo_spots_y[i])
                for i in range(len(trafo_spots_y1)):
                    if (i+1)==(len(trafo_spots_y1)):
                        plt.plot(trafo_spots_x1[i]+3, trafo_spots_y1[i]+2.5, 'go', label="transformer", markersize=14)
                    else:
                        plt.plot(trafo_spots_x1[i]+3, trafo_spots_y1[i]+2.5, 'go', markersize=14)
#                plt.xlim([0, plant_width*2])
#                plt.ylim([0, plant_length*2])
                plt.xticks([0, 5, 10, 15, 20, max(trafo_spots_x)+3], fontsize=16)
                plt.yticks([0, 5, 10, 15, max(battery_spots_y1)+3], fontsize=16)
                plt.legend(fontsize=15)
                plt.xlabel("Dimensions (m)", fontsize=16, fontweight = "bold")
                plt.ylabel('Dimensions (m)', fontsize=16, fontweight = "bold")
                # plt.axis('scaled')
                plt.axis('equal')
                plt.title("Battery plant layout\n"+" ".join(scenario_desc.split('_'))+'\nBattery Rack per PCS:'+str(batteryrack_per_conv)+'\nPCS Power:'+str(per_inverter_rating/1e3)+'kW'+'\nPCS per transformer:'+str(inverter_per_trafo), fontsize=16, fontweight="bold")
                # plt.tight_layout()
                fig = plt.gcf()
                fig.set_size_inches(16, 10.5)
                if per_trafo_rating==4*1e6 and inverter_output_voltage==1500 and per_inverter_rating==450000:
                    plt.savefig((str(int(per_inverter_rating/1e3))+'kW'), dpi=2000, bbox_inches='tight', quality=95,  filetype="png")
# =============================================================================
#               length of battery to inverter cables
# =============================================================================
                cable_length_batt_converter=0
                cable_list_batt_converter=[]
                count=0
                for i in range(len(battery_spots_y1)):
                    length_x=abs(battery_spots_x1[i]-inv_spots_x1[count])
                    length_y=abs(battery_spots_y1[i]-inv_spots_y1[count])
                    cable_list_batt_converter.append(length_x+length_y)
                    cable_length_batt_converter+=length_x+length_y
                    if (i+1)%batteryrack_per_conv==0:
                        count+=1

                cable_length_batt_converter=cable_length_batt_converter*2

                total_batt_conv_cable_len=cable_length_batt_converter
                current_output_battery = rack_power/module_operating_voltage

                #type of cable
                #adding 10% tolerance and derating factor
                longest_length_batt_conv=max(cable_list_batt_converter)
                avg_length_batt_conv=np.mean(cable_list_batt_converter)
                battery_cable_size, battery_cable_size_new, batt_conv_receiving_voltage, batt_conv_target_receiving_voltage, batt_conv_new_voltage_drop, batt_conv_new_voltage_drop_pu, batt_cable_cost, batt_conv_ckts, batt_conv_cable_weight=cable_selection (current_output_battery, module_operating_voltage, rack_power, avg_length_batt_conv, 1, "DC", "Cu", "Yes", batteryrack_per_conv*multiplier)

                total_batt_conv_cable_len=total_batt_conv_cable_len*batt_conv_ckts
                perMW_batt_conv_cable=total_batt_conv_cable_len/(plant_power/1e6)
                total_battery_cable_cost=batt_cable_cost*total_batt_conv_cable_len

# =============================================================================
                

                if inverter_output_voltage==400.:
                    total_conv_inv_cable_len=0
                    current_output_converter = per_converter_rating/converter_output_voltage
                    per_unit_conv_inv_cable_len=total_conv_inv_cable_len/converter_per_plant
                    longest_length_conv_inv=0

                    #type of cable
                    #adding 10% tolerance and derating factor
                    inverter_cable_size, inverter_cable_size_new, conv_inv_receiving_voltage, conv_inv_target_receiving_voltage, conv_inv_new_voltage_drop, conv_inv_new_voltage_drop_pu, inverter_cable_cost, conv_inv_ckts, conv_inv_cable_weight=(0,0,0,0,0,0,0,0,0)
                    total_inverter_cable_cost=0                
                    inverter_cost_optimization=0
                    new_inverter_cable_cost=0
                    new_inverter_cable_size=0
                    new_inverter_cable_rating=0
                    conv_per_inverter=0
                    perMW_conv_inv_cable=total_conv_inv_cable_len/(plant_power/1e6)

                else:
                    conv_inv_cable_len=2 #2m cable between converter output and inverter input
                    longest_length_conv_inv=conv_inv_cable_len
                    
                    total_conv_inv_cable_len=conv_inv_cable_len*inverter_per_plant*2       #factor of 2 for +/- DC cables    
    
                    current_output_converter = per_converter_rating/converter_output_voltage

                    #type of cable
                    #adding 10% tolerance and derating factor

                    inverter_cable_size, inverter_cable_size_new, conv_inv_receiving_voltage, conv_inv_target_receiving_voltage, conv_inv_new_voltage_drop, conv_inv_new_voltage_drop_pu, inverter_cable_cost, conv_inv_ckts, conv_inv_cable_weight=cable_selection (current_output_converter, converter_output_voltage, per_converter_rating, longest_length_conv_inv, 1, "DC", "Cu", "Yes", 1)
                    total_conv_inv_cable_len=total_conv_inv_cable_len*conv_inv_ckts
                    perMW_conv_inv_cable=total_conv_inv_cable_len/(plant_power/1e6)
                    total_inverter_cable_cost=inverter_cable_cost*total_conv_inv_cable_len

# =============================================================================
#               length of inverter to trafo cables
# =============================================================================
                cable_length_inv_trafo=0
                cable_list_inv_trafo=[]
                count=0
                for i in range(len(inv_spots_y1)):
                    length_x=abs(inv_spots_x1[i]-trafo_spots_x1[count])
                    length_y=abs(inv_spots_y1[i]-trafo_spots_y1[count])
                    cable_list_inv_trafo.append(length_x+length_y)
                    cable_length_inv_trafo+=length_x+length_y
                    if (i+1)%inverter_per_trafo==0:
                        count+=1
                    
                cable_length_inv_trafo=cable_length_inv_trafo*(3+with_neutral)
                
                total_inv_trafo_cable_len= cable_length_inv_trafo     #factor of 3 for 3 phase AC cables and factor of 2 for inverter on both sides


                current_output_inverter = per_inverter_rating/(np.sqrt(3)*inverter_output_voltage)


                longest_length_inv_trafo=max(cable_list_inv_trafo)
                avg_inv_trafo_lengths=np.mean(cable_list_inv_trafo)
                
                trafo_cable_size, trafo_cable_size_new, inv_trafo_receiving_voltage, inv_trafo_target_receiving_voltage, inv_trafo_new_voltage_drop, inv_trafo_new_voltage_drop_pu, trafo_cable_cost, inv_trafo_ckts, trafo_cable_weight=cable_selection (current_output_inverter, inverter_output_voltage, per_inverter_rating, avg_inv_trafo_lengths, 1, "AC", "Cu", "Yes", inverter_per_trafo)
                
                
                individual_inv_trafo_vdrops = np.multiply(cable_list_inv_trafo, (1e-3*inv_trafo_new_voltage_drop_pu*current_output_inverter/inv_trafo_ckts/inverter_output_voltage))
                avg_inv_trafo_vdrop=np.mean(individual_inv_trafo_vdrops)

                total_inv_trafo_cable_len=total_inv_trafo_cable_len*inv_trafo_ckts
                total_trafo_cable_weight=trafo_cable_weight*.001*total_inv_trafo_cable_len  #0.001 as cable weight given in kg/km so to convert to kg/m
                perMW_inv_trafo_cable=total_inv_trafo_cable_len/(plant_power/1e6)

                total_trafo_cable_cost=trafo_cable_cost*total_inv_trafo_cable_len
                
                total_DC_cabling=total_battery_cable_cost+total_inverter_cable_cost
                total_AC_cabling=total_trafo_cable_cost
                total_cables_cost=total_DC_cabling+total_AC_cabling
                total_costs=total_cables_cost+total_inverter_costs+total_converter_costs+total_trafo_price+total_switchgear_price
                
                globals()[scenario_desc][df_index]=[plant_power, trafo_per_plant, per_trafo_rating,
                       inverter_per_plant, inverter_per_trafo, per_converter_rating, per_inverter_rating, inverter_output_voltage,
                       rack_power, battery_power, batteryrack_per_conv,
                       battery_array_depth, battery_array_width, multiplier,
                       inverter_cable_size, inverter_cable_size_new,
                       cable_length_batt_converter, cable_list_batt_converter, cable_length_inv_trafo, cable_list_inv_trafo,
                       plant_length, plant_width, dimensions_info,
                       inv_trafo_receiving_voltage,inv_trafo_new_voltage_drop, trafo_cable_size, trafo_cable_size_new, avg_inv_trafo_vdrop,
                       total_batt_conv_cable_len, total_conv_inv_cable_len, total_inv_trafo_cable_len, total_trafo_cable_weight,
                       perMW_batt_conv_cable, perMW_conv_inv_cable, perMW_inv_trafo_cable,
                       total_PCS_semiconductor_costs, total_PCS_filter_costs, total_PCS_fixed_costs, total_trafo_price, total_switchgear_price,
                       total_AC_cabling,total_DC_cabling, total_converter_costs, total_inverter_costs,
                       total_battery_cable_cost, total_inverter_cable_cost, total_trafo_cable_cost,
                       total_cables_cost, total_costs]
            
                df_index+=1
                per_trafo_rating=actual_per_trafo_rating

    results.update({scenario_desc:globals()[scenario_desc]})
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
# %%

#for i in range(len(results)):
#    cost_length_plots(scenarios[i], results[scenarios[i]], max(max_costs))
#    cost_compare_plots(scenarios[i], results[scenarios[i]], max(max_costs))
#    cost_breakdown_plots(scenarios[i], results[scenarios[i]])

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
#trafo_rating_3_MW.to_excel("battery_3MW.xlsx")
#trafo_rating_4_MW.to_excel("battery_4MW.xlsx")
#trafo_rating_12_MW.to_excel("battery_12MW.xlsx")
#%%

#cable_weight_index=trafo_rating_3_MW.index.get_loc("total trafo cable weight")
#cable_cross_section_index=trafo_rating_3_MW.index.get_loc("vdrop_compensate")
#cable_total_length_index=trafo_rating_3_MW.index.get_loc("total_inv_trafo_cable_len")
#cable_weight_400=trafo_rating_3_MW.iloc[cable_weight_index,0]
#cable_weight_1500=trafo_rating_3_MW.iloc[cable_weight_index,8]
#cable_cross_section_400=trafo_rating_3_MW.iloc[cable_cross_section_index,0]
#cable_cross_section_1500=trafo_rating_3_MW.iloc[cable_cross_section_index,8]
#cable_total_length_400=trafo_rating_3_MW.iloc[cable_total_length_index,0]/1e3
#cable_total_length_1500=trafo_rating_3_MW.iloc[cable_total_length_index,8]/1e3
#
#voltages = ["400 V\nbase case\n150 kW PCS\n120mm2 cable", "1500 V\n500 kW PCS\n95mm2 cable"]
#cable_weights = [cable_weight_400, cable_weight_1500]
#cable_lengths = [cable_total_length_400, cable_total_length_1500]
#batt_comparison=pd.DataFrame()
#batt_comparison.at[:,"voltages"]=voltages 
#batt_comparison=batt_comparison.set_index('voltages')
#
#batt_comparison.at[:,"cable_weights"]=cable_weights 
#batt_comparison.at[:,"cable_lengths"]=cable_lengths
#
#mlt.rc('xtick', labelsize=8) 
#mlt.rc('ytick', labelsize=8)
#
#
## creating the bar plot 
#voltages = ["400 V\nbase case\n150 kW PCS\n120mm2 cable", "1500 V\n500 kW PCS\n95mm2 cable"]
#cable_weights = [cable_weight_400, cable_weight_1500]
#cable_lengths = [cable_total_length_400, cable_total_length_1500]
#
#fig = plt.figure()
#
#
#red_patch = mpatches.Patch(color='crimson', label='Cable Weight')
#blue_patch = mpatches.Patch(color='royalblue', label='Cable Length')
#
#ax = fig.add_subplot(111) # Create matplotlib axes
#
#ax2 = ax.twinx() # Create another axes that shares the same x-axis as ax.
#width = 0.1
#
#batt_comparison.cable_weights.plot(kind='bar', color='crimson', ax=ax, width=width, position=1)
#batt_comparison.cable_lengths.plot(kind='bar', color='royalblue', ax=ax2, width=width, position=0)
#
#ax.set_title('Cable Length and Weight comparison\nin battery power plants (3 MW Transformer)', fontsize=8, fontweight="bold")
#ax.set_xlabel('Scenarios', fontsize=8, fontweight="bold")
#ax2.set_ylim([0, 3])
#ax.set_yticks([0, 500, 1000, 1500, 2000, 2500, cable_weight_400, cable_weight_1500])
#ax2.set_yticks([0, 0.5, 1, 1.5,2,3,cable_total_length_400,cable_total_length_1500])
#plt.xticks(rotation=90)
#
#plt.grid(linestyle=":", linewidth=0.5)
#
#ax.set_ylabel('Weight of cable (kg)', color='crimson',fontsize=8, fontweight="bold")
#ax2.set_ylabel('Length of cable (km)', color='royalblue', fontsize=8, fontweight="bold")
#
#fig.set_size_inches(5, 4)
#plt.legend(handles=[red_patch, blue_patch], fontsize=8)
#
#fig.savefig("batt_criteria_compare", dpi=2000, quality=95, bbox_inches='tight', filetype="png") 
#
#plt.show()


