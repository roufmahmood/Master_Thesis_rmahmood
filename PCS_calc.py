# -*- coding: utf-8 -*-
"""
Created on Tue Jun 23 10:14:32 2020

@author: rmahmood
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#from mp1_toolkits.mplot3d import Axes3D




# =============================================================================
# Inductor price extrapolation
# =============================================================================

def inductor_price_extrapolate (power_required_choke, freq_required_choke):
    
    power_sample_choke=240e3    #kW  3 phase          
    price_sample_choke=750      #Euro
    freq_sample_choke=48e3
    if freq_required_choke==freq_sample_choke:
        price_of_required_choke=(price_sample_choke*power_required_choke)/power_sample_choke
    else:
        if freq_required_choke<48e3:
            price_sample_choke=price_sample_choke/1.3
        else:
            price_sample_choke=price_sample_choke*1.3
        price_of_required_choke=(price_sample_choke*power_required_choke)/power_sample_choke
    return price_of_required_choke

# =============================================================================

# =============================================================================
# Capacitor price extrapolation
# =============================================================================
#voltage_device=3300
#AC_or_DC="DC"
def capacitor_price_extrapolate (voltage_device, filter_capacitance, AC_or_DC):
    mod_index=0.7
    voltage_sample_cap=800    #V           
    price_sample_cap=100      #Euro
    sample_capacitance=25e-6
    sample_capacitance_double=25e-6*2
    price_sample_cap_double=1.3*price_sample_cap      #Euro
    cap_database_df=pd.DataFrame()
    for i in range(1,200):
        cap_database_df.at[i, 'Capacitance 800V rated (µF)']=25*i
        cap_database_df.at[i, 'Cap price']=(0.3*i+0.7)*price_sample_cap
    cap_database_df=cap_database_df.reset_index(drop=True)
    if AC_or_DC=="AC":
        if voltage_device==400:
            series_no=1
        elif voltage_device==1500:
            series_no=2
        else:
            series_no=4
    else:
        if voltage_device==1500:
            series_no=3
        else:
            series_no=6
        voltage_device=voltage_device*2/(mod_index*np.sqrt(3))


#    cap_infostring='Capacitance '+str(round(voltage_device,2))+' V'+AC_or_DC+' rated (µF)'
    cap_database_df.at[:, 'Capacitance '+str(round(voltage_device,2))+' V'+AC_or_DC+' rated (µF)']=cap_database_df.loc[:, 'Capacitance 800V rated (µF)']/series_no

    for i in range(len(cap_database_df)):
        if cap_database_df.iloc[i, 2]>=filter_capacitance:
            selected_capacitance=cap_database_df.iloc[i, 2]
            if AC_or_DC=="AC":
                selected_capacitance_price=cap_database_df.loc[i, 'Cap price']*series_no*3
            else:
                selected_capacitance_price=cap_database_df.loc[i, 'Cap price']*series_no
            break
        else:continue

#    cap_database_df.at[:, 'Cap price ']=cap_database_df.at[:, 'Cap price']*series_no


#    sample_capacitance_new=sample_capacitance/series_no
#    parallel_no=int(filter_capacitance/sample_capacitance_new)
#    total_cap_units_per_phase=parallel_no+series_no
#    total_cap_units_3_phase=total_cap_units_per_phase*3
#    voltage_device=voltage_device*2/(mod_index*np.sqrt(3))
#    price_of_required_choke=(price_sample_choke*power_required_choke)/power_sample_choke
    return selected_capacitance, selected_capacitance_price
# =============================================================================

# =============================================================================
# SiC price extrapolation
# =============================================================================
def sic_price_extrapol(sample_current_rating_normal, sample_current_rating_derated, sample_price, module_df, AC_or_DC):        #price of SiC module
    ratio=sample_current_rating_normal/sample_current_rating_derated
    if AC_or_DC=="AC":          
        for i in range(len(module_df)):
            required_current=module_df.loc[i,"Current @25degC"]
            overcurrent=required_current*1.1       
            extrapol_device_current_rating=ratio*overcurrent
            if module_df.loc[i,"Voltage"]==3300:
                module_df.at[i, 'Cost of SiC devices']=sample_price*3.5*extrapol_device_current_rating/sample_current_rating_normal  #factor of 3.5 as price difference between 1.7 kV and 3.3 kV MOSFET
            else:
                module_df.at[i, 'Cost of SiC devices']=sample_price*extrapol_device_current_rating/sample_current_rating_normal

    
    else:
        sample_price=sample_price*3.5
        for i in range(len(module_df)):
            required_current=module_df.loc[i,"Current @25degC"]
            overcurrent=required_current*1.1       
            extrapol_device_current_rating=ratio*overcurrent
            module_df.at[i, 'Cost of SiC devices']=sample_price*extrapol_device_current_rating/sample_current_rating_normal

    return module_df

# =============================================================================

# =============================================================================
# function to calculate LCL values in inverter
# =============================================================================
def lcl_inverter (inverter_level, line_line_voltage, inverter_power, udc_max, fs, ripple_percent=0.4, fN=50):

    # =============================================================================
    # Calculations of dependent variables
    # =============================================================================

    mmax=0.7                  #maximum modulation index = 1.15
    n=inverter_level-1          #inverter level either 2 or 3
    iac = inverter_power/(line_line_voltage/np.sqrt(3))
    i_ripple = ripple_percent*iac*np.sqrt(2)
    lf = (udc_max*np.sqrt(3)*mmax)/(8*3*n*fs*i_ripple)
    f_res_min = 10*fN               #min resonance frequency of filter
    f_res_max = fs/10            #max resonance frequency of filter

    # =============================================================================
    # LCL values calculation 
    # =============================================================================

    grid_inverter_choke_ratio = 0.1

    l_main = (lf*(1+grid_inverter_choke_ratio)/grid_inverter_choke_ratio)
    l_grid = grid_inverter_choke_ratio * l_main
    cap=1/((2*np.pi*f_res_max)**2*lf)

    # =============================================================================
    # return function value
    # =============================================================================
    return (l_main, cap, l_grid)

# =============================================================================
# function to calculate LC of Boost converter
# Output voltage ripple is assumed as 10% of Output Voltage, Input current ripple is 40% of Input Current
# =============================================================================

def lc_booster (Power_booster, V_in, V_out, fs=32e3):
    
    T=1/fs
    Toff=V_in*T/V_out
    Ton=T-Toff   
    V_ripp=0.1*V_out
    duty_cycle = 1-V_in/V_out
    I_out=Power_booster/V_out
    I_input=Power_booster/V_in
    I_ripp=0.4*I_input
    L=V_in*duty_cycle/(fs*I_ripp)
#    L=(V_out*V_in/Power_booster)/(8*fs)
#    L=(1-duty_cycle)*duty_cycle*(V_out*V_in/Power_booster)/(2*fs)#V_in*duty_cycle/(fs*I_ripp)
#    L=((1-duty_cycle)**2)*duty_cycle*(V_out**2/Power_booster)/(2*fs)#V_in*duty_cycle/(fs*I_ripp)
    C=I_out*duty_cycle/(fs*V_ripp)
    I_peak=I_input+I_ripp/2

    return (L,C, I_ripp, I_input, I_peak)


# =============================================================================
#%%
def cost_compare_plots(results_df, PCS_type):
    plt.figure()
    cost_comparison=cost_compare(results_df, PCS_type)
    if PCS_type=="Inverter" or PCS_type=="PCS":  
        x=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,0], 'bo', linewidth=1.5, label=cost_comparison.keys()[0]+" VAC")
        y=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,1], 'r-', linewidth=1.5, label=cost_comparison.keys()[1]+" VAC")
        z=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,2], 'm-', linewidth=1.5, label=cost_comparison.keys()[2]+" VAC")
    elif PCS_type=="Converter":
        y=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,0], 'r-', label=cost_comparison.keys()[0]+" V DC")
        z=plt.plot(list((cost_comparison.index[:])), cost_comparison.iloc[:,1], 'm-', label=cost_comparison.keys()[1]+" V DC")
    plt.xticks(rotation=90, fontsize=8)
    plt.yticks(fontsize=8)
    plt.grid(linestyle=':', linewidth=0.5)
#    plt.ylim([0, maximum*1.1])
    plt.title("Power Conversion System Costs (€/MW)", fontsize=8, fontweight="bold")
    plt.legend(fontsize=8)
    plt.xlabel("Scenarios", fontsize=8, fontweight="bold")
    plt.ylabel('Costs (€/MW)', fontsize=8, fontweight="bold")
    fig = plt.gcf()
    fig.set_size_inches(8, 4.57)
    fig.savefig(str(PCS_type)+"_cost_comparison", dpi=2000, quality=95, bbox_inches='tight', filetype="png")  
    if PCS_type=="Inverter":
        return (x,y,z)
    elif PCS_type=="Converter":
        return (y,z)

#%%
def cost_compare(power_electronics, type_PCS):
    voltages = [400., 1500., 3300.]
    factor_for_AC_to_DC=2/(modulation_index*np.sqrt(3))
    power_electronics=power_electronics.T
    power_electronics=power_electronics.rename(columns=power_electronics.iloc[0])
    total_cost_comparison=pd.DataFrame()
    if type_PCS=="Converter":
        acvolt_index=power_electronics.index.get_loc('Booster output Voltage\nD.C. (V)')
        invpower_index=power_electronics.index.get_loc('Booster\nPower (W)')
        cost_index=power_electronics.index.get_loc("total conv price (€/MW)")#"total cable cost (€)"
        xlabel_string="Converter\nPower: "
        voltages=np.round(np.multiply(voltages,factor_for_AC_to_DC),2)
    elif type_PCS=="Inverter":
        acvolt_index=power_electronics.index.get_loc('L-L voltage (V)')
        invpower_index=power_electronics.index.get_loc('Inverter_power (kVA)')
        cost_index=power_electronics.index.get_loc("total inv price (€/MW)")#"total cable cost (€)"
        xlabel_string="Inverter\nPower: "
    elif type_PCS=="PCS":
        acvolt_index=power_electronics.index.get_loc('L-L voltage (V)')
        invpower_index=power_electronics.index.get_loc('Inverter_power (kVA)')
        cost_index=power_electronics.index.get_loc("total price (€/MW)")#"total cable cost (€)"
        xlabel_string="Inverter\nPower: "
#    convpower_index=plant_details.index.get_loc("Converter Power (W)")
#    invpower_index=plant_details.index.get_loc("Inverter Power (W)")
#    trafopower_index=plant_details.index.get_loc("Trafo Power")

    new_count=0
    new_count1=0
    new_count2=0
    
    for i in range(len(power_electronics.columns)):
        if round(power_electronics.iloc[acvolt_index,i],2)==voltages[0]:
            total_cost_comparison.at[new_count,"Scenario"]=str(int(voltages[0]))
            total_cost_comparison.at[new_count,xlabel_string+str(int(power_electronics.iloc[invpower_index,i]/1e3))+"kW"]=(round(power_electronics.iloc[cost_index,i], 7))#+"M"
            new_count1+=1
        elif round(power_electronics.iloc[acvolt_index,i],2)==voltages[1]:
            total_cost_comparison.at[new_count1,"Scenario"]=str(int(voltages[1]))
            total_cost_comparison.at[new_count1,xlabel_string+str(int(power_electronics.iloc[invpower_index,i]/1e3))+"kW"]=(round(power_electronics.iloc[cost_index,i], 7))#+"M"
            new_count2+=1
        elif round(power_electronics.iloc[acvolt_index,i],2)==voltages[2]:
            if type_PCS=="Converter":
                total_cost_comparison.at[new_count1+1,"Scenario"]=str(int(voltages[2]))
                total_cost_comparison.at[new_count1+1,xlabel_string+str(int(power_electronics.iloc[invpower_index,i]/1e3))+"kW"]=(round(power_electronics.iloc[cost_index,i], 7))#+"M"if type_PCS=="Converter":
            elif type_PCS=="Inverter" or type_PCS=="PCS":    
                total_cost_comparison.at[new_count1+new_count2,"Scenario"]=str(int(voltages[2]))
                total_cost_comparison.at[new_count1+new_count2,xlabel_string+str(int(power_electronics.iloc[invpower_index,i]/1e3))+"kW"]=(round(power_electronics.iloc[cost_index,i], 7))#+"M"
    
    total_cost_comparison=total_cost_comparison.T
    total_cost_comparison=total_cost_comparison.rename(columns=total_cost_comparison.iloc[0]).drop(total_cost_comparison.index[0])
    return total_cost_comparison

#%%

inverter_unit_df=pd.read_excel("inverter_sic_devices.xlsx")
inverter_unit_df.at[:, 'Current @25degC']=np.divide(inverter_unit_df.loc[:,"Power"],(np.sqrt(3)*inverter_unit_df.loc[:,"Voltage"]))
inverter_unit_df=sic_price_extrapol(325, 225, 728.63098, inverter_unit_df, "AC")        #price of SiC module CAS300M17BM2

booster_unit_df=pd.read_excel("booster_sic_devices.xlsx")
booster_unit_df.at[:, 'Current @25degC']=np.divide(booster_unit_df.loc[:,"Power"], 1000)       # 1000 V because input voltage of booster
booster_unit_df=sic_price_extrapol(325, 225, 728.63098, booster_unit_df, "DC")        #price of SiC module extrapolated from IGBT 3.5 times the same voltage and current

# =============================================================================
# heat sink dimensions and temperature details
# =============================================================================

#model fischer elektronik LA V 7 300 12
        
heat_sink_width=0.125                   #m
heat_sink_height=0.074                  #m
heat_sink_length=0.3                    #m

heat_sink_volume=heat_sink_width*heat_sink_height*heat_sink_length
heat_sink_thermalresistance=0.04       #K/W
max_temp_rise = 20  #Kelvin
device_amb_temp=40
heatsink_ref_temp=60      #heat sink reference temperature
heat_sink_price=128.94  #https://www.buerklin.com/en/High-power-cooling-system-LAV-7-300-Cooling-systems-60%C2%A0mm/p/80B4974
# =============================================================================

price_per_module=728.63098        #€ per unit from digikey for more than 51 Nos 1.7kV SiC Mosfet
for i in range(len(inverter_unit_df)):
    if inverter_unit_df.loc[i, 'Level']==2:
        modules_per_inv=3
        price_per_module=492.19         #force price of 1.2kV SiC Module CAS300M12BM2
    elif inverter_unit_df.loc[i, 'Level']==3:
        modules_per_inv=9
        price_per_module=inverter_unit_df.at[i, 'Cost of SiC devices']  #use extrapolated price from 1.7kV module CAS300M17BM2
    inverter_unit_df.at[i, 'No. of SiC\npower modules\nper inverter']=modules_per_inv
    inverter_unit_df.at[i, 'Cost of SiC devices\nper inverter']=modules_per_inv*price_per_module

for i in range(len(booster_unit_df)):
    if booster_unit_df.loc[i, 'Voltage']==1500:
        modules_per_conv=1    #0.5 factor to consider only one switch as price is for half bridge module
    elif booster_unit_df.loc[i, 'Voltage']==3300:
        modules_per_conv=2
    price_per_module=booster_unit_df.at[i, 'Cost of SiC devices']  #use extrapolated price from 1.7kV module CAS300M17BM2
    booster_unit_df.at[i, 'No. of SiC\npower modules\nper converter']=modules_per_conv
    booster_unit_df.at[i, 'Cost of SiC devices\nper converter']=modules_per_conv*price_per_module


#%%
# =============================================================================
# LCL size list
# =============================================================================

lcl_df1=pd.DataFrame()
count=0
modulation_index=0.7
DCvoltage=2500
ACvoltage=modulation_index*np.sqrt(3)*DCvoltage/2
for ac_voltages in [400, 1500, 3300]:
    
    if ac_voltages==400:
        power=150000
        inv_level=2
        lcl_df1.at[count, 'Inverter_power (kVA)']= power
        lcl_df1.at[count, 'Sampling Freq (Hz)']= 32000
        lcl_df1.at[count, 'L-L voltage (V)']= ac_voltages
        lcl_df1.at[count, 'Current (A)']=np.divide(lcl_df1.loc[count,'Inverter_power (kVA)'],(np.sqrt(3)*lcl_df1.loc[count,'L-L voltage (V)']))
        lcl_df1.at[count, 'Inverter Level']= inv_level
        lcl_df1.at[count, 'DC link voltage (V)']= 1000#ac_voltages*2/(modulation_index*np.sqrt(3))
        lcl_df1.at[count, 'Main Choke (µH)']= lcl_inverter (inv_level, ac_voltages, power, 1000, 32000)[0]*1e6
        choke_price_extrapolation=inductor_price_extrapolate (power, 32000)
        lcl_df1.at[count, 'Main Choke (µH) price']= choke_price_extrapolation
        lcl_df1.at[count, 'Capacitor (µF)']= lcl_inverter (inv_level, ac_voltages, power, 1000, 32000)[1]*1e6
        lcl_df1.at[count, 'Capacitor (µF) selected']= capacitor_price_extrapolate (ac_voltages, lcl_df1.loc[count, 'Capacitor (µF)'], "AC")[0]
        lcl_df1.at[count, 'Capacitor (µF) price']= capacitor_price_extrapolate (ac_voltages, lcl_df1.loc[count, 'Capacitor (µF)'], "AC")[1]
        lcl_df1.at[count, 'Grid Choke (µH)']= lcl_inverter (inv_level, ac_voltages, power, 1000, 32000)[2]*1e6
        lcl_df1.at[count, 'Grid Choke (µH) price']= choke_price_extrapolation*0.1       #Grid choke is 10% of Main choke
        count+=1
    
    else:
        inv_level = 3
        for power in range (150000,550000, 50000):
            lcl_df1.at[count, 'Inverter_power (kVA)']= power
            lcl_df1.at[count, 'Sampling Freq (Hz)']= 48000
            lcl_df1.at[count, 'L-L voltage (V)']= ac_voltages
            lcl_df1.at[count, 'Current (A)']=np.divide(lcl_df1.loc[count,'Inverter_power (kVA)'],(np.sqrt(3)*lcl_df1.loc[count,'L-L voltage (V)']))
            lcl_df1.at[count, 'Inverter Level']= inv_level
            lcl_df1.at[count, 'DC link voltage (V)']= ac_voltages*2/(modulation_index*np.sqrt(3))
            lcl_df1.at[count, 'Main Choke (µH)']= lcl_inverter (inv_level, ac_voltages, power, ac_voltages*2/(modulation_index*np.sqrt(3)), 48000)[0]*1e6
            choke_price_extrapolation=inductor_price_extrapolate (power, 48000)
            lcl_df1.at[count, 'Main Choke (µH) price']= choke_price_extrapolation
            lcl_df1.at[count, 'Capacitor (µF)']= lcl_inverter (inv_level, ac_voltages, power, ac_voltages*2/(modulation_index*np.sqrt(3)), 48000)[1]*1e6
            capacitor_extrapolation=capacitor_price_extrapolate (ac_voltages, lcl_df1.loc[count, 'Capacitor (µF)'], "AC")
            lcl_df1.at[count, 'Capacitor (µF) selected']= capacitor_extrapolation[0]
            lcl_df1.at[count, 'Capacitor (µF) price']= capacitor_extrapolation[1]
            lcl_df1.at[count, 'Grid Choke (µH)']= lcl_inverter (inv_level, ac_voltages, power, ac_voltages*2/(modulation_index*np.sqrt(3)), 48000)[2]*1e6
            lcl_df1.at[count, 'Grid Choke (µH) price']= choke_price_extrapolation*0.1       #Grid choke is 10% of Main choke
            count+=1

lcl_df1.at[:, 'total filter price']=lcl_df1.loc[:, 'Main Choke (µH) price']+lcl_df1.loc[:, 'Capacitor (µF) price']+lcl_df1.loc[:, 'Grid Choke (µH) price']
lcl_df1.at[:, 'total semiconductors price']=inverter_unit_df.loc[:, 'Cost of SiC devices\nper inverter']
lcl_df1.at[:, '€/MW (filter)']=lcl_df1.loc[:, 'total filter price']/(lcl_df1.loc[:, 'Inverter_power (kVA)']/1e6)
lcl_df1.at[:, '€/MW (semiconductor)']=lcl_df1.loc[:, 'total semiconductors price']/(lcl_df1.loc[:, 'Inverter_power (kVA)']/1e6)
lcl_df1.at[:, 'total inv price']=lcl_df1.loc[:, 'total filter price']+lcl_df1.loc[:, 'total semiconductors price']
lcl_df1.at[:, 'total inv price (€/MW)']=(lcl_df1.loc[:, 'total filter price']+lcl_df1.loc[:, 'total semiconductors price'])/(lcl_df1.loc[:, 'Inverter_power (kVA)']/1e6)


# =============================================================================



# =============================================================================
# LC Booster size list
# =============================================================================

booster_df=pd.DataFrame()
count=0
for new_booster_acvoltage in (1500, 3300):
#    losses = .02*new_booster_power
#    no_of_heat_sinks=losses*heat_sink_thermal_resistance/20
    for new_booster_power in range(150000, 550000, 50000):
        new_booster_dcvoltage=new_booster_acvoltage*2/(modulation_index*np.sqrt(3))
        booster_df.at[count, 'Booster\nPower (W)']= new_booster_power
        booster_df.at[count, 'Booster input Voltage\nD.C. (V)'] = 1000
        booster_df.at[count, 'Booster output Voltage\nD.C. (V)'] = new_booster_dcvoltage
        booster_df.at[count, 'Booster Equivalent\nA.C. Voltage (V)'] = new_booster_acvoltage
        booster_df.at[count, 'Sampling\nfreq (Hz)'] = 32e3
        booster_df.at[count, 'Inductor (µH)'] =lc_booster (new_booster_power, 1000, new_booster_dcvoltage, fs=32e3)[0]
        booster_df.at[count, 'Inductor price'] = inductor_price_extrapolate (new_booster_power, 32000)
        booster_df.at[count, 'Capacitor (µF)'] =lc_booster (new_booster_power, 1000, new_booster_dcvoltage, fs=32e3)[1]*1e6
        capacitor_extrapolation=capacitor_price_extrapolate (ac_voltages, booster_df.loc[count, 'Capacitor (µF)'], "DC")
        booster_df.at[count, 'Capacitor (µF) selected']= capacitor_extrapolation[0]
        booster_df.at[count, 'Capacitor (µF) price']= capacitor_extrapolation[1]
        count+=1

booster_df.at[:, 'total filter price']=booster_df.loc[:, 'Inductor price']+booster_df.loc[:, 'Capacitor (µF) price']
booster_df.at[:, '€/MW']=booster_df.loc[:, 'total filter price']/(booster_df.loc[:, 'Booster\nPower (W)']/1e6)

booster_df.at[:, 'total semiconductors price']=booster_unit_df.loc[:, 'Cost of SiC devices\nper converter']

booster_df.at[:, '€/MW (semiconductor)']=booster_df.loc[:, 'total semiconductors price']/(booster_df.loc[:, 'Booster\nPower (W)']/1e6)
booster_df.at[:, 'total conv price']=booster_df.loc[:, 'total filter price']+booster_df.loc[:, 'total semiconductors price']
booster_df.at[:, 'total conv price (€/MW)']=(booster_df.loc[:, 'total filter price']+booster_df.loc[:, 'total semiconductors price'])/(booster_df.loc[:, 'Booster\nPower (W)']/1e6)

# =============================================================================

#lcl_df1.to_excel("lcl_list.xlsx")
#booster_df.to_excel("booster_lc_list.xlsx")
pcs_df=lcl_df1.copy()
for i in range(len(pcs_df)):
    if pcs_df.loc[i, 'L-L voltage (V)']==400 :
        pcs_df.at[i, 'total price (€)']=lcl_df1.loc[i, 'total inv price']
    else:
        pcs_df.at[i, 'total price (€)']=lcl_df1.loc[i, 'total inv price']+ booster_df.loc[(i-1), 'total conv price']
        
pcs_df.at[:, 'total price (€/MW)']=pcs_df.loc[:, 'total price (€)']/pcs_df.loc[:, 'Inverter_power (kVA)']

#cost_compare_plots(lcl_df1, "Inverter")
#cost_compare_plots(booster_df, "Converter")
cost_compare_plots(pcs_df, "PCS")


