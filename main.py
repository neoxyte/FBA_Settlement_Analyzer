import pandas as pd
import xlsxwriter

#This stops data truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option("display.max_colwidth", None)

#data types for settlement flat file v2
dtypes = {
    "settlement-id": "category",
    "settlement-start-date": "category",
    "settlement-end-date": "category",
    "deposit-date": "category",
    "total-amount": "category",
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
    '''Get's all units sold (only units charged an fba fee count here'''
    units_sold = settlement_df.loc[settlement_df['amount-description'] == 'FBAPerUnitFulfillmentFee']
    units_sold = units_sold[['sku','quantity-purchased']]
    units_sold = units_sold.groupby('sku').sum()
    return units_sold.rename(columns={'quantity-purchased':'Units Sold'})

def get_nonsales_units(settlement_df):
    '''Returns units taken from inventory and compensated but not as sale'''
    ns_units = settlement_df.loc[(settlement_df['amount-description'] == 'WAREHOUSE_LOST') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE') | (settlement_df['amount-description'] == 'FREE_REPLACEMENT_REFUND_ITEMS')]
    ns_units = ns_units[['sku', 'quantity-purchased']]
    ns_units = ns_units.groupby('sku').sum()
    return ns_units.rename(columns={'quantity-purchased':'Non-Sale Units'})

def get_salesbased_revenue(settlement_df):
    '''returns the column for sales based revenue (only comission without fees'''
    sales_revenue = settlement_df.loc[(settlement_df['amount-description'] == 'Principal')]
    sales_revenue = sales_revenue[['sku', 'amount']]
    sales_revenue = sales_revenue.groupby('sku').sum()
    return sales_revenue.rename(columns={'amount':'Sales Revenue'})

def get_commission(settlement_df):
    '''Return comission Column'''
    commission = settlement_df.loc[(settlement_df['amount-description'] == 'Commission')]
    commission = commission[['sku', 'amount']]
    commission = commission.groupby('sku').sum()
    return commission.rename(columns={'amount':'Commission'})

def get_fba_fees(settlement_df):
    '''Get all FBA fees'''
    fba_fees = settlement_df.loc[(settlement_df['amount-description'] == 'FBAPerOrderFulfillmentFee') | (settlement_df['amount-description'] == 'FBAPerUnitFulfillmentFee') | (settlement_df['amount-description'] == 'FBAWeightBasedFee')]
    fba_fees = fba_fees[['sku', 'amount']]
    fba_fees = fba_fees.groupby('sku').sum()
    return fba_fees.rename(columns={'amount':'FBA Fees'})

def get_nonsales_revenue(settlement_df):
    '''Get revenue for the following: COMPENSATED_CLAWBACK, FREE_REPLACEMENT_REFUND_ITEMS, RefundCommission, RestockingFee, REVERSAL_REIMBURSEMENT,
    WAREHOUSE_DAMAGE, WAREHOUSE_DAMAGE_EXCEPTION, WAREHOUSE_LOST, WAREHOUSE_LOST_MANUAL '''
    ns_revenue = settlement_df.loc[(settlement_df['amount-description'] == 'COMPENSATED_CLAWBACK') | (settlement_df['amount-description'] == 'FREE_REPLACEMENT_REFUND_ITEMS') | (settlement_df['amount-description'] == 'RefundCommission') | (settlement_df['amount-description'] == 'REVERSAL_REIMBURSEMENT') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE') | (settlement_df['amount-description'] == 'WAREHOUSE_DAMAGE_EXCEPTION') | (settlement_df['amount-description'] == 'WAREHOUSE_LOST') |  (settlement_df['amount-description'] == 'WAREHOUSE_LOST_MANUAL')]
    ns_revenue = ns_revenue[['sku', 'amount']]
    ns_revenue = ns_revenue.groupby('sku').sum()
    return ns_revenue.rename(columns={'amount':'Non-Sales Revenue'})

def get_non_skus(settlement_df):
    '''Gets line items without a SKU  from the flat file. Such as Subscription, Monthly Storage, Reserve, Etc'''
    #perhaps look into doing inverse logic next time
    nonskus= settlement_df.loc[(settlement_df['amount-description'] == 'Subscription Fee')|
    (settlement_df['amount-description'] == 'Previous Reserve Amount Balance') | (settlement_df['amount-description'] == 'Current Reserve Amount') |
    (settlement_df['amount-description'] == 'RemovalComplete') | (settlement_df['amount-description'] == 'Adjustment')|
    (settlement_df['amount-description'] == 'DisposalComplete') | (settlement_df['amount-description'] == 'FBACustomerReturnPerUnitFee') |
    (settlement_df['amount-description'] == 'Shipping label purchase') | (settlement_df['amount-description'] == 'Shipping label purchase for return') |
    (settlement_df['amount-description'] == 'INCORRECT_FEES_NON_ITEMIZED') | (settlement_df['amount-description'] == 'FBAInboundTransportationFee')|
    (settlement_df['amount-description'] == 'FBA Pick & Pack Fee') ]
    nonskus = nonskus[['amount-description', 'amount']]
    nonskus = nonskus.groupby('amount-description').sum()
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
    #confirm if this works with a previous report that doesn't have storage
    return get_storage(settlement_df) != 0

def get_storage_with_sku(monthly_storage_df, manage_fba_inventory_df):
    '''Returns a data frame with monthly storage by SKU'''
    sku_fnsku = manage_fba_inventory_df[['sku', 'fnsku']]
    sku_fnsku = sku_fnsku.groupby('fnsku').sum()
    monthly_storage = monthly_storage_df[['fnsku', 'estimated_monthly_storage_fee']]
    monthly_storage = monthly_storage.groupby('fnsku').sum()
    storage_by_sku = pd.concat((sku_fnsku, monthly_storage), axis=1)
    storage_by_sku = storage_by_sku[storage_by_sku['estimated_monthly_storage_fee'].notna()] #removes rows where nan in amount column
    storage_by_sku = storage_by_sku.rename(columns={'estimated_monthly_storage_fee':'Storage Fee'})
    return (storage_by_sku.groupby('sku').sum() * -1)

def get_asin_and_title(manage_fba_inventory_df):
    '''Returns the ASIN and Title of the SKUS based on FBA Archive'''
    asins_and_skus_df = manage_fba_inventory_df[['sku', 'asin', 'product-name']]
    asins_and_skus_df = asins_and_skus_df.groupby('sku').sum()
    asins_and_skus_df = asins_and_skus_df['product-name'].str[:40]
    return asins_and_skus_df

def get_advertising_spend(advertising_df):
    '''Gets the spend of advertising by SKU'''
    advertising_by_sku = advertising_df[['Advertised SKU', 'Spend']]
    advertising_by_sku = advertising_by_sku.rename(columns={"Advertised SKU": 'sku', 'Spend': 'Advertising Spend'})
    return advertising_by_sku.groupby('sku').sum() * -1

def main_table(settlement_df):
    '''Returns a dataframe consisting of all columns'''
    settlement_analysis = pd.concat([asins_and_skus_df, get_units_sold(settlement_df), get_nonsales_units(settlement_df)], axis=1)
    settlement_analysis['Total Units'] = settlement_analysis['Units Sold'] + settlement_analysis['Non-Sale Units']
    settlement_analysis = pd.concat([settlement_analysis, get_salesbased_revenue(settlement_df), get_commission(settlement_df),get_fba_fees(settlement_df), get_nonsales_revenue(settlement_df)], axis=1)
    settlement_analysis['Amazon Revenue'] = settlement_analysis['Sales Revenue'] + settlement_analysis['Commission'] + settlement_analysis['FBA Fees'] + settlement_analysis['Non-Sales Revenue'] 
    settlement_analysis['Amazon Revenue'] = settlement_analysis['Amazon Revenue'].fillna(0)
    if monthly_storage_charged(settlement_df):
        settlement_analysis = pd.concat([settlement_analysis, storage_sku_df], axis=1)
        settlement_analysis['Storage Fee'] = settlement_analysis['Storage Fee'].fillna(0)
    if adding_advertising:
        settlement_analysis = pd.concat([settlement_analysis, advertising_spend], axis=1)
        settlement_analysis['Advertising Spend'] = settlement_analysis['Advertising Spend'].fillna(0)
    settlement_analysis['Total Return'] = settlement_analysis['Amazon Revenue'] + settlement_analysis['Storage Fee'] + settlement_analysis['Advertising Spend']
    #Below drops if 3 columns = 0, this ensures only relevant columns are shown
    index_dropping = settlement_analysis[(settlement_analysis['Amazon Revenue'] ==0) & (settlement_analysis['Advertising Spend'] ==0) & (settlement_analysis['Total Return'] ==0)].index
    settlement_analysis.drop(index_dropping, inplace=True)
    return settlement_analysis.sort_values('Total Return', ascending=False)
    
def export_report(finalized_report, nonsku_report, filename):
    '''Export to Excel with multiple Worksheets'''
    writer = pd.ExcelWriter(filename + ".xlsx", engine='xlsxwriter')
    finalized_report.to_excel(writer, sheet_name='Overview')
    nonsku_report.to_excel(writer, sheet_name='Non SKU line items')
    for column in finalized_report:
        column_length = max(finalized_report[column].astype(str).map(len).max(), len(column))
        col_idx = finalized_report.columns.get_loc(column)
        writer.sheets['Overview'].set_column(col_idx, col_idx, column_length)
    writer.close()
    print("Exported to Excel as " + filename)

def get_statement_period(settlement_df):
    '''Returns a list with start and end date'''
    dates = settlement_df [settlement_df ['settlement-start-date'].notna()][['settlement-start-date', 'settlement-end-date']] 
    statement_start_date = dates.iloc[0][0]
    statement_end_date = dates.iloc[0][1]
    statement_period = [statement_start_date, statement_end_date]
    return statement_period
    
#settlement_df = pd.read_table(input("Statement File Name: "), sep='\t', dtype=dtypes)
settlement_df = pd.read_table('flatfile.txt', sep='\t', dtype=dtypes)

statement_timeframe =  get_statement_period(settlement_df)
print("\nStatement period start time: " + statement_timeframe[0])
print("Statement period end time: " + statement_timeframe[1])

#DEBUG uncomment the comments below to enable normal 
fba_inventory_report = 'fba_archive.csv' #input("Manage FBA Inventory Archive CSV report name: ")
manage_fba_inventory_df = pd.read_csv(fba_inventory_report, encoding = 'latin1')

asins_and_skus_df = get_asin_and_title(manage_fba_inventory_df)

if monthly_storage_charged(settlement_df):
    storage_report = 'november_storage.csv' #input("\nMonthly Storage was charged in this statement. Please enter corresponding monthly storage report.\n\nMonthly Storage Report CSV name: ")
    monthly_storage_df =  pd.read_csv(storage_report, encoding='latin1')
    storage_sku_df = get_storage_with_sku(monthly_storage_df, manage_fba_inventory_df)

adding_advertising = input("\nWould you like to add advertising(y/n): ").lower() == 'y'
if adding_advertising:
    #print("Please input filename for advertising xlsx report for the appropiate time range.")
    advertising_report = 'advertising_report.xlsx' #input("Sponsored products XLSX report name: ")
    advertising_df = pd.read_excel(advertising_report)
    advertising_spend = get_advertising_spend(advertising_df)

export_report(main_table(settlement_df), get_non_skus(settlement_df), 'debugoutput') #input("\nOutput filename?: "))

#figure out how to calculate units for MFN (principle)
#probably make it's own column for mfn

#revenue 
#revenue per unit
#net cost per unit
# advert spend total 	 advert per sale 	 net cost w/ advert 	 profit w/advert 	 total profit /advert 	roi w/ advert



#TODO
#Add in status text
#get rows where SKU is non existant (only showing as FNSKU) and put it in a seperate tab of report

#make all storage fees negative
#tab for just sales
#other tab for nonsales
#confirm sales against amazon fee preview
#



#Personal Notes
#this report is just for a general idea of unit movement and should not be used for inventory management just yet
#we can compare inventory reports against settlement reports in the future
#compensated clawback no units potentially involved, look into in future
# "FBA Pick and Pack Fee" return reimbursement does not have SKUS accounted for in report. So have to add that somehow, for now ill add it as a nonsku item
#add something that checks if taxes cancel out properly

