import pandas as pd
import xlsxwriter
import numpy as np
import PySimpleGUI as sg

pd.set_option('display.precision', 2)

#ignores runtime warnings
import warnings
warnings.filterwarnings("ignore")

#data types for settlement flat file v2
dtypes = {
    "settlement-id": "category",
    "settlement-start-date": "category",
    "settlement-end-date": "category",
    "deposit-date": "category",
    "total-amount": "float64",
    "currency": "category",
    "transaction-type": "category",
    "order-id": "category",
    "merchant-order-id": "category",
    "adjustment-id": "category",
    "shipment-id": "category",
    "marketplace-name": "category",
    "amount-type": "category",
    "amount-description": "category",
    "amount": "float64",
    "fulfillment-id": "category",
    "posted-date": "category",
    "posted-date-time": "category",
    "order-item-code": "category",
    "merchant-order-item-id": "category",
    "merchant-adjustment-item-id": "category",
    "sku": "category",
    "quantity-purchased": "Int64",
    "promotion-id": "category",
}

def get_units_sold(settlement_df):
    '''Get's all units sold (only units charged a comission via AFN)'''
    units_sold = settlement_df.loc[(settlement_df['fulfillment-id']== 'AFN') & (settlement_df['amount-description']=='Commission')]
    units_sold = units_sold[['sku','quantity-purchased']]
    units_sold = units_sold.groupby('sku').sum()
    return units_sold.rename(columns={'quantity-purchased':'Units Sold'})

def get_nonsales_units(settlement_df):
    '''Returns units taken from inventory and compensated but not as sale'''
    #ns_units = settlement_df.loc[(settlement_df['amount-description'] == 'WAREHOUSE_LOST') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE') | (settlement_df['amount-description'] == 'FREE_REPLACEMENT_REFUND_ITEMS')]
    ns_units = settlement_df.loc[(settlement_df['amount-description'] == 'FREE_REPLACEMENT_REFUND_ITEMS') | (settlement_df['amount-description'] == 'RefundCommission') | (settlement_df['amount-description'] == 'REVERSAL_REIMBURSEMENT') 
                                 | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE_EXCEPTION') 
                                 | (settlement_df['amount-description'] == 'WAREHOUSE_LOST') |  (settlement_df['amount-description'] == 'WAREHOUSE_LOST_MANUAL') ]
    ns_units = ns_units[['sku', 'quantity-purchased']]
    #clawback_units =settlement_df.loc[ (settlement_df['amount-description'] == 'COMPENSATED_CLAWBACK') ]
    #clawback_units = clawback_units[['sku', 'quantity-purchased']]
    ns_units = ns_units.groupby('sku').sum()
    #clawback_units = clawback_units.groupby('sku').sum()
    #ns_units = ns_units['quantity-purchased'] - clawback_units['quantity-purchased']
    return ns_units.rename(columns={'quantity-purchased':'Non-Sale Units'})

def get_merchantfulfilled_units(settlement_df):
    mf_units = settlement_df.loc[(settlement_df['fulfillment-id']== 'MFN') & (settlement_df['amount-description']=='Principal')]
    mf_units = mf_units[['sku', 'quantity-purchased']]
    mf_units = mf_units.groupby('sku').sum()
    mf_units.loc[~(mf_units==0).all(axis=1)]
    return mf_units.rename(columns={'quantity-purchased':'Merchant Fulfilled Units'})

def get_salesbased_revenue(settlement_df):
    '''returns the column for sales based revenue (only comission without fees'''
    sales_revenue = settlement_df.loc[(settlement_df['amount-description'] == 'Principal')]
    sales_revenue = sales_revenue[['sku', 'amount']]
    sales_revenue = sales_revenue.groupby('sku').sum()
    return sales_revenue.rename(columns={'amount':'Sales Revenue'})

def get_average_sales_price(settlement_df):
    units = get_units_sold(settlement_df)
    sales_revenue = get_salesbased_revenue(settlement_df)
    sales_revenue['Average Price'] =  sales_revenue['Sales Revenue'] / units['Units Sold']
    return sales_revenue['Average Price']

def get_commission(settlement_df):
    '''Return comission Column'''
    commission = settlement_df.loc[(settlement_df['amount-description'] == 'Commission')]
    commission = commission[['sku', 'amount']]
    commission = commission.groupby('sku').sum()
    return commission.rename(columns={'amount':'Commission'})

def get_average_commision_per_unit(settlement_df):
    '''Returns Average Comission per Unit'''
    units = get_units_sold(settlement_df)
    commission = get_commission(settlement_df)
    commission['Commision Per Unit'] = commission['Commission'] / units['Units Sold']
    return commission['Commision Per Unit']

def get_commission_percent(settlement_df):
    '''Returns Comission as a percent'''
    comission = get_commission(settlement_df)
    sales_revenue = get_salesbased_revenue(settlement_df)
    comission['Commission Percent'] = (comission['Commission']/ sales_revenue['Sales Revenue'])*-1
    return comission['Commission Percent']

def get_fba_fees(settlement_df):
    '''Get all FBA fees'''
    fba_fees = settlement_df.loc[(settlement_df['amount-description'] == 'FBAPerOrderFulfillmentFee') | (settlement_df['amount-description'] == 'FBAPerUnitFulfillmentFee')
                                  | (settlement_df['amount-description'] == 'FBAWeightBasedFee') | (settlement_df['amount-description'] == 'FBAWeightBasedFee') ]
    fba_fees = fba_fees[['sku', 'amount']]
    fba_fees = fba_fees.groupby('sku').sum()
    return fba_fees.rename(columns={'amount':'FBA Fees'})

def get_average_fba_fees(settlement_df):
    '''Gets an average fba fee per units'''
    units = get_units_sold(settlement_df)
    fba_fees = get_fba_fees(settlement_df)
    fba_fees['FBA Fee Average'] = fba_fees['FBA Fees'] / units['Units Sold']
    return fba_fees['FBA Fee Average']

def get_nonsales_revenue(settlement_df):
    '''Get revenue for the following: COMPENSATED_CLAWBACK, FREE_REPLACEMENT_REFUND_ITEMS, RefundCommission, RestockingFee, REVERSAL_REIMBURSEMENT,
    WAREHOUSE_DAMAGE, WAREHOUSE_DAMAGE_EXCEPTION, WAREHOUSE_LOST, WAREHOUSE_LOST_MANUAL '''
    #these are non sale revenue by SKU
    ns_revenue = settlement_df.loc[(settlement_df['amount-description'] == 'COMPENSATED_CLAWBACK') | (settlement_df['amount-description'] == 'FREE_REPLACEMENT_REFUND_ITEMS')  
                                   |(settlement_df['amount-description'] == 'RefundCommission') | (settlement_df['amount-description'] == 'REVERSAL_REIMBURSEMENT') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE')
                                    | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE_EXCEPTION') | (settlement_df['amount-description'] == 'WAREHOUSE_LOST') 
                                    |  (settlement_df['amount-description'] == 'WAREHOUSE_LOST_MANUAL') | (settlement_df['amount-description'] == 'VariableClosingFee') 
                                    | ((settlement_df['amount-description'] == 'RestockingFee') )]
    ns_revenue = ns_revenue[['sku', 'amount']]
    ns_revenue = ns_revenue.groupby('sku').sum()
    return ns_revenue.rename(columns={'amount':'Non-Sales Revenue'})

def get_non_skus(settlement_df):
    '''Gets line items without a SKU  from the flat file. Such as Subscription, Monthly Storage, Reserve, Etc'''
    nonskus= settlement_df.loc[(settlement_df['amount-description'] == 'Subscription Fee')|
    (settlement_df['amount-description'] == 'Previous Reserve Amount Balance') | (settlement_df['amount-description'] == 'Current Reserve Amount') |
    (settlement_df['amount-description'] == 'RemovalComplete') | (settlement_df['amount-description'] == 'Adjustment')|
    (settlement_df['amount-description'] == 'DisposalComplete') | (settlement_df['amount-description'] == 'FBACustomerReturnPerUnitFee') |
    (settlement_df['amount-description'] == 'Shipping label purchase') | (settlement_df['amount-description'] == 'Shipping label purchase for return') |
    (settlement_df['amount-description'] == 'INCORRECT_FEES_NON_ITEMIZED') | (settlement_df['amount-description'] == 'FBAInboundTransportationFee')|
    (settlement_df['amount-description'] == 'FBA Pick & Pack Fee') |
    (settlement_df['amount-description'] == 'StorageRenewalBilling')  ]
    nonskus = nonskus[['amount-description', 'amount']]
    nonskus = nonskus.groupby('amount-description').sum()
    nonskus = nonskus.rename(index={'StorageRenewalBilling':'Long-Term Storage Fee'})
    nonskus = nonskus.loc[~(nonskus==0).all(axis=1)]
    return nonskus

def get_storage(settlement_df):
    '''Gets storage Fee'''
    storage_fee = settlement_df.loc[(settlement_df['amount-description'] == 'Storage Fee')]
    storage_fee = storage_fee[['amount-description', 'amount']]
    storage_fee = storage_fee['amount'].sum()
    return storage_fee

def monthly_storage_charged(settlement_df):
    '''Returns True/False if monthly storaged was charged'''
    return get_storage(settlement_df) != 0

def lts_charged(settlement_df):
    '''Returns if long term storage was charged'''
    longterm_storage_fee = settlement_df.loc[(settlement_df['amount-description'] == 'StorageRenewalBilling')]
    longterm_storage_fee = longterm_storage_fee[['amount-description', 'amount']]
    longterm_storage_fee = longterm_storage_fee['amount'].sum()
    return longterm_storage_fee != 0

def get_lts_with_sku(lts_df):
    '''Returns a data frame with long term storage by SKU'''
    sku_fnsku = manage_fba_inventory_df[['sku', 'fnsku']]
    sku_fnsku = sku_fnsku.groupby('fnsku').sum()
    lts_storage = lts_df[['fnsku', 'amount-charged']]
    lts_storage = lts_storage.groupby('fnsku').sum()
    lts_by_sku= pd.concat((sku_fnsku, lts_storage), axis=1)
    lts_by_sku = lts_by_sku[lts_by_sku['amount-charged'].notna()]
    lts_by_sku = lts_by_sku.rename(columns={'amount-charged':'LTS Fee'})
    lts_by_sku = lts_by_sku.groupby('sku').sum() * -1
    return lts_by_sku

def get_storage_with_sku(monthly_storage_df, manage_fba_inventory_df):
    '''Returns a data frame with monthly storage by SKU'''
    sku_fnsku = manage_fba_inventory_df[['sku', 'fnsku']]
    sku_fnsku = sku_fnsku.groupby('fnsku').sum()
    monthly_storage = monthly_storage_df[['fnsku', 'estimated_monthly_storage_fee']]
    monthly_storage = monthly_storage.groupby('fnsku').sum()
    storage_by_sku = pd.concat((sku_fnsku, monthly_storage), axis=1)
    storage_by_sku = storage_by_sku[storage_by_sku['estimated_monthly_storage_fee'].notna()]
    storage_by_sku = storage_by_sku.rename(columns={'estimated_monthly_storage_fee':'Storage Fee'})
    return (storage_by_sku.groupby('sku').sum() * -1)

def get_asin_and_title(manage_fba_inventory_df):
    '''Returns the ASIN and Title of the SKUS based on FBA Archive'''
    asins_and_skus_df = manage_fba_inventory_df[['sku', 'asin', 'product-name']]
    asins_and_skus_df = asins_and_skus_df.groupby('sku').sum()
    asins_and_skus_df['product-name'] = asins_and_skus_df['product-name'].str[:40]
    return asins_and_skus_df

def get_advertising_spend(advertising_df):
    '''Gets the spend of advertising by SKU'''
    advertising_by_sku = advertising_df[['Advertised SKU', 'Spend']]
    advertising_by_sku = advertising_by_sku.rename(columns={"Advertised SKU": 'sku', 'Spend': 'Advertising Spend'})
    return advertising_by_sku.groupby('sku').sum() * -1

def get_cost(helium10_df):
    cost = helium10_df[['SKU','PRODUCT COST', 'SHIPPING COST']]
    cost = cost.rename(columns={"SKU": 'sku', 'PRODUCT COST': 'Product Cost', 'SHIPPING COST': 'Packing Cost'})
    cost['Cost Per Unit'] = cost['Product Cost']  + cost['Packing Cost']
    cost = cost.groupby('sku').sum()
    index_dropping = cost[cost['Cost Per Unit'] == 0].index
    cost.drop(index_dropping, inplace=True)
    return cost

def main_table(settlement_df):
    '''Returns a dataframe consisting of all columns'''
    settlement_analysis = pd.concat([asins_and_skus_df, get_units_sold(settlement_df), get_nonsales_units(settlement_df), get_merchantfulfilled_units(settlement_df)], axis=1)
    settlement_analysis['Total Units'] = settlement_analysis['Units Sold'] + settlement_analysis['Non-Sale Units'] + settlement_analysis['Merchant Fulfilled Units']
    settlement_analysis = pd.concat([settlement_analysis, get_salesbased_revenue(settlement_df), get_commission(settlement_df), get_commission_percent(settlement_df), get_average_commision_per_unit(settlement_df),get_fba_fees(settlement_df), get_average_fba_fees(settlement_df), get_nonsales_revenue(settlement_df), get_average_sales_price(settlement_df)], axis=1)
    settlement_analysis['Amazon Revenue'] = settlement_analysis['Sales Revenue'] + settlement_analysis['Commission'] + settlement_analysis['FBA Fees'] + settlement_analysis['Non-Sales Revenue'] 
    settlement_analysis['Amazon Revenue'] = settlement_analysis['Amazon Revenue'].fillna(0)
    if monthly_storage_charged(settlement_df):
        settlement_analysis = pd.concat([settlement_analysis, storage_sku_df], axis=1)
        settlement_analysis['Storage Fee'] = settlement_analysis['Storage Fee'].fillna(0)
        #settlement_analysis = settlement_analysis.dropna(subset=['Storage Fee'])
    if adding_advertising:
        settlement_analysis = pd.concat([settlement_analysis, advertising_spend], axis=1)
        settlement_analysis['Advertising Spend'] = settlement_analysis['Advertising Spend'].fillna(0)
        if monthly_storage_charged(settlement_df):
            settlement_analysis['Total Return'] = settlement_analysis['Amazon Revenue'] + settlement_analysis['Storage Fee'] + settlement_analysis['Advertising Spend']
            settlement_analysis['Total (w/o Advertising)'] = settlement_analysis['Amazon Revenue'] + settlement_analysis['Storage Fee'] 
        else:
            settlement_analysis['Total Return'] = settlement_analysis['Amazon Revenue'] + settlement_analysis['Advertising Spend']
            settlement_analysis['Total (w/o Advertising)']  = settlement_analysis['Amazon Revenue'] 
        index_dropping = settlement_analysis[(settlement_analysis['Amazon Revenue'] ==0) & (settlement_analysis['Advertising Spend'] ==0) & (settlement_analysis['Total Return'] ==0)].index
        settlement_analysis.drop(index_dropping, inplace=True)
    else:
        if monthly_storage_charged(settlement_df):
            settlement_analysis['Total Return'] = settlement_analysis['Amazon Revenue'] + settlement_analysis['Storage Fee'] 
        else:
            settlement_analysis['Total Return'] = settlement_analysis['Amazon Revenue']
    if lts_charged(settlement_df):
        settlement_analysis = pd.concat([settlement_analysis, lts_sku_df], axis=1)
        #settlement_analysis.to_csv("debug.csv")
        #print(settlement_analysis.columns.tolist())
        settlement_analysis['LTS Fee'] = settlement_analysis['LTS Fee'].fillna(0)
        settlement_analysis['Total Return'] = settlement_analysis['Total Return']  + settlement_analysis['LTS Fee']
    settlement_analysis['Return Per Unit'] = settlement_analysis['Total Return'] /  settlement_analysis['Total Units']
    if adding_advertising:
        settlement_analysis['Return Per Unit (w/o Advertising)'] = settlement_analysis['Total (w/o Advertising)'] / settlement_analysis['Total Units']
    if adding_cost:
        settlement_analysis = pd.concat([settlement_analysis, product_cost_df], axis=1)
        settlement_analysis.fillna({'Packing Cost':0, 'Cost Per Unit':0, 'Product Cost': 0}, inplace=True)
        settlement_analysis['Total Cost'] = settlement_analysis['Cost Per Unit'] * settlement_analysis['Total Units'] * -1
        if adding_advertising:
            settlement_analysis['Cost (w/ Advertising'] = settlement_analysis['Total Cost']  + settlement_analysis['Advertising Spend']
        settlement_analysis['Total Profit'] = settlement_analysis['Total Cost'] + settlement_analysis['Total Return'] 
        #possibly delete non-sale revenue from above, run 2 reports and compare
        #settlement_analysis.replace([np.inf, -np.inf], np.nan, inplace=True) 
        #settlement_analysis = settlement_analysis.dropna(subset=['Total Return'])
        settlement_analysis = settlement_analysis.sort_values('Total Profit', ascending=False)
        settlement_analysis["ROI"] = settlement_analysis["Total Profit"] / settlement_analysis['Total Cost'] * -1 
        if adding_advertising:
            settlement_analysis["ROI w/ advertising"] = settlement_analysis["Total Profit"] / settlement_analysis['Cost (w/ Advertising'] * -1 
            settlement_analysis["ROI Difference"] = settlement_analysis["ROI w/ advertising"] - settlement_analysis["ROI"]
        #settlement_analysis = settlement_analysis.dropna(subset=['Commission'])
        settlement_analysis = settlement_analysis.dropna(subset=['Total Profit'])
    else:
        #settlement_analysis.replace([np.inf, -np.inf], np.nan, inplace=True) 
        #settlement_analysis = settlement_analysis.dropna(subset=['Total Return'])
        #settlement_analysis = settlement_analysis.dropna(subset=['Commission'])
        settlement_analysis = settlement_analysis.sort_values('Total Return', ascending=False)
    settlement_analysis = settlement_analysis.fillna(0)
    settlement_analysis.replace([np.inf, -np.inf], np.nan, inplace=True)
    return  rename_columns(settlement_analysis)

def rename_columns(settlement_analysis):
    new_df = settlement_analysis
    new_df = new_df.rename(columns={
        "product-name": "Title",
        "Non-Sale Units": "N/S Units",
        "Merchant Fulfilled Units": "MF Units",
        "Total Units": "Total",
        "Commission": "Comm",
        "Commission Percent": "Comm %",
        "Commision Per Unit": "Comm/Unit",
        "FBA Fee Average": "Fee Avg",
        "Non-Sales Revenue": "N/S Rev",
        "Average Price": "Avg Price",
        "Amazon Revenue": "Amz Rev",
        "Return Per Unit": "Return/Unit",
        "Advertising Spend": "Ad Spend"})
    if monthly_storage_charged(settlement_df):
        new_df = new_df.rename(columns={
        "Storage Fee": "Storage"})
    if adding_advertising:
        new_df = new_df.rename(columns={
        "Total (w/o Advertising)": "Total before Ads",
        "Return Per Unit (w/o Advertising)": "Return/unit before Ads"})
    if adding_cost:
        new_df = new_df.rename(columns={
        "Product Cost": "Cost",
        "Packing Cost:": "Packing",
        "Cost Per Unit": "COGS",
        "Total Cost": "Total COGS"})
    #make sure to rename columns differently if adding cost/advertising
    return new_df

def get_overview(settlement_df):
    '''Returns a dataframe with totals for everything'''
    disbursement_total = settlement_df['amount'].sum()
    main_df = main_table(settlement_df)
    non_sku_df = get_non_skus(settlement_df)
    amazon_revenue = main_df['Amz Rev'].sum()
    overview ={
        #'Disbursement Total': disbursement_total,
        'Amazon Revenue': amazon_revenue
    }
    if monthly_storage_charged(settlement_df):
        storage_fee = storage_sku_df.sum()[0]
        overview['Storage Fee'] = storage_fee
    if adding_advertising:
        advertising_total = advertising_spend.sum()[0]
        overview['Advertising Total'] = advertising_total
    overview = pd.DataFrame.from_dict(overview,orient='index', columns=['amount'])
    overview = pd.concat([overview, non_sku_df])
    return overview

def get_non_sale_revenue_tab(settlement_df):
    '''Makes a dataframe for non-sale revenue (units and revenue)'''
    return True

def filter_niro_skus(final_table_df):
    return final_table_df.filter(like = 'NIRO', axis=0)

def filter_hd_skus(final_table_df):
    return final_table_df.filter(like = 'HD', axis=0)

def filter_other_skus(final_table_df):
    return final_table_df.filter(regex = r'MD|MED', axis=0)
#add MD here

def get_refunds(settlement_df, final_table_df):
    '''Returns a dataframe showing transcation type refund only'''
    refund_df = settlement_df.loc[settlement_df['transaction-type'] == 'Refund']
    refund_df = refund_df.groupby('sku').sum()
    refund_df = refund_df["amount"]
    refund_df = refund_df.rename("Refund Total")
    total_sales_df = final_table_df['Sales Revenue']
    refund_df = pd.concat([refund_df, total_sales_df], axis=1)
    refund_df = refund_df.replace(to_replace=0, value=np.nan)
    refund_df = refund_df.dropna(subset=["Refund Total"])
    refund_df['Refund Total'] = refund_df['Refund Total'] * -1
    refund_df['Refund Percentage of Sales'] = refund_df['Refund Total'] / refund_df['Sales Revenue']
    refund_df = refund_df.sort_values(by='Refund Percentage of Sales', ascending=False)
    return refund_df
    
def get_statement_period(settlement_df):
    '''Returns a list with start and end date'''
    dates = settlement_df [settlement_df ['settlement-start-date'].notna()][['settlement-start-date', 'settlement-end-date']] 
    statement_start_date = dates.iloc[0][0]
    statement_end_date = dates.iloc[0][1]
    statement_period = [statement_start_date, statement_end_date]
    return statement_period

def export_report(filename):
    '''Export to Excel with multiple Worksheets. Uses settlement report date as suffix'''
    report_date_range = get_statement_period(settlement_df)
    start_date = report_date_range[0]
    start_date = start_date[:10]
    end_date = report_date_range[1]
    end_date = end_date[:10]
    filename = filename + "_" + start_date + "_to_" + end_date
    writer = pd.ExcelWriter(filename + ".xlsx", engine='xlsxwriter')
    finalized_report.to_excel(writer, sheet_name='Sales')
    overview_tab.to_excel(writer, sheet_name='Overview')
    niro_tab.to_excel(writer, sheet_name='NIRO')
    hd_tab.to_excel(writer, sheet_name='HD')
    other_tab.to_excel(writer, sheet_name='Other')
    #refund_tab.to_excel(writer, sheet_name="Refunds")
    writer.close()

flatfile_form = sg.FlexForm('Settlement Analyzer') 
layout = [
          [sg.Text('Please select Flat File (v2)')],
          [sg.Text('Statement File: ', size=(50, 1)), sg.FileBrowse()],
          [sg.Submit(), sg.Cancel()]
         ]
button, filename = flatfile_form.Layout(layout).Read() 
flat_file = filename['Browse']
flatfile_form.close()
settlement_df = pd.read_table(flat_file, sep='\t', dtype=dtypes)
#invoiced_form = sg.FlexForm('Settlement Analyzer') 
#layout = [
#          [sg.Text('Would you like to add invoiced orders too?')],
#          [sg.Radio("Yes", "Radio1", default=False)], 
#          [sg.Radio("No", "Radio2", default=False)],
#          [sg.Submit(), sg.Cancel()]
#         ]
#button, add_invoiced =  invoiced_form.Layout(layout).Read() 
#invoiced_form.close()
#adding_invoiced = add_invoiced[0] 
adding_invoiced = False
if adding_invoiced:
    get_invoiced_form = sg.FlexForm('Settlement Analyzer') 
    layout = [
            [sg.Text('Please select Invoiced Flat File (v2)')],
            [sg.Text('Invoiced Flat File (V2): ', size=(50, 1)), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
            ]
    button, invoice_filename = get_invoiced_form.Layout(layout).Read() 
    invoiced_file = invoice_filename['Browse']
    get_invoiced_form.close()
    invoice_df = pd.read_table(invoiced_file, sep='\t', dtype=dtypes)
    #remove the total amount/date row from the invoiced one
    invoice_df =invoice_df.drop(index=0)
    combined_df = pd.concat([settlement_df, invoice_df])
    ''' remove when finished debuging combining invoiced and main settlements
    #debug
    print(combined_df)
    writer = pd.ExcelWriter("debug_output_1" + ".xlsx", engine='xlsxwriter')
    combined_df.to_excel(writer, sheet_name='Test')
    writer.close()
else:
    #otherdebug
    print(settlement_df)
    writer = pd.ExcelWriter("debug_output" + ".xlsx", engine='xlsxwriter')
    settlement_df.to_excel(writer, sheet_name="test1")
    writer.close()'''
statement_timeframe =  get_statement_period(settlement_df)
timeframe_layout = [  [sg.Text('Statement period start time: ' + statement_timeframe[0])],
            [sg.Text('Statement period end time: ' + statement_timeframe[1])],
            [sg.OK()]]
window = sg.Window('Window Title', timeframe_layout)
event = window.read()
window.close()
if adding_invoiced:
    settlement_df = combined_df
fba_archive_form = sg.FlexForm('Settlement Analyzer')
layout = [
          [sg.Text('Please select FBA Archive report')],
          [sg.Text('FBA Inventory Archive:', size=(50, 1)), sg.FileBrowse()],
          [sg.Submit(), sg.Cancel()]
         ]
button, fbaarchivename =  fba_archive_form.Layout(layout).Read() 
fba_inventory_report = fbaarchivename['Browse']
fba_archive_form.close()
manage_fba_inventory_df = pd.read_csv(fba_inventory_report, encoding = 'latin1')
asins_and_skus_df = get_asin_and_title(manage_fba_inventory_df)
if monthly_storage_charged(settlement_df):
    storage_form = sg.FlexForm('Settlement Analyzer') 
    storage_form_layout = [
            [sg.Text('Please select appropiate storage report (report corresponding to month before statement end date)')],
            [sg.Text('Statement Start Date: ' + statement_timeframe[0])],
            [sg.Text('Monthly Storage Report:', size=(50, 1)), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
            ]
    button, storagefilename = storage_form.Layout(storage_form_layout).Read() 
    storage_report= storagefilename['Browse']
    storage_form.close()
    monthly_storage_df =  pd.read_csv(storage_report, encoding='latin1')
    storage_sku_df = get_storage_with_sku(monthly_storage_df, manage_fba_inventory_df)
if lts_charged(settlement_df):
    storage_form = sg.FlexForm('Settlement Analyzer') 
    storage_form_layout = [
            [sg.Text('Long-Term Storage Detected. Please select appropiate LTS report (15th of current month, Inventory Surcharge Rep)')],
            [sg.Text('Statement Start Date: ' + statement_timeframe[0])],
            [sg.Text('Long-Term Storage Report:', size=(50, 1)), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
            ]
    button, storagefilename = storage_form.Layout(storage_form_layout).Read() 
    lts_report= storagefilename['Browse']
    storage_form.close()
    lts_df =  pd.read_csv(lts_report, encoding='latin1')
    lts_sku_df = get_lts_with_sku(lts_df)
option_form = sg.FlexForm('Settlement Analyzer') 
layout = [
          [sg.Text('Select the following optional parameters')],
          [sg.Radio("Use Helium 10 cost to calculate profit", "Radio1", default=False)], 
          [sg.Radio("Add Advertising Report", "Radio2", default=False)],
          [sg.Submit(), sg.Cancel()]
         ]
button, options =  option_form.Layout(layout).Read() 
option_form.close()
adding_cost = options[0] 
adding_advertising = options[1]
if adding_advertising:
    advertising_form = sg.FlexForm('Settlement Analyzer')
    layout = [
            [sg.Text('Please select appropiate Advertising Report')],
            [sg.Text('Statement period start time: ' + statement_timeframe[0])],
            [sg.Text('Statement period end time: ' + statement_timeframe[1])],
            [sg.Text('Amazon Advertising Report', size=(50, 1)), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
         ]
    button, adreportname =  advertising_form.Layout(layout).Read() 
    advertising_report = adreportname['Browse']
    advertising_form.close()
    advertising_df = pd.read_excel(advertising_report)
    advertising_spend = get_advertising_spend(advertising_df)
if adding_cost:
    cost_form = sg.FlexForm('Settlement Analyzer')
    layout = [
            [sg.Text('Please select latest helium10 report')],
            [sg.Text('Helium10 COGS report:', size=(50, 1)), sg.FileBrowse()],
            [sg.Submit(), sg.Cancel()]
            ]
    button, cost_form_input =  cost_form.Layout(layout).Read() 
    helium10= cost_form_input['Browse']
    cost_form.close()
    helium10_df = pd.read_csv(helium10)
    product_cost_df = get_cost(helium10_df)
finalized_report = main_table(settlement_df)
overview_tab = get_overview(settlement_df)
niro_tab = filter_niro_skus(finalized_report)
hd_tab = filter_hd_skus(finalized_report)
other_tab = filter_other_skus(finalized_report)
#refund_tab = get_refunds(settlement_df, finalized_report)
output_form= sg.FlexForm('Settlement Analyzer')
layout = [
        [sg.Text('Please type a file prefix')],
        [sg.Input()],
        [sg.Submit(), sg.Cancel()]
        ]
button, output_name =  output_form.Layout(layout).Read() 
output_form.close()
export_report(output_name[0])