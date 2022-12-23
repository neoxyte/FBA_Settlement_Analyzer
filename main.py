import pandas as pd

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

def main_table(settlement_df):
    '''Returns a dataframe consisting of all columns'''
    settlement_analysis = pd.concat([get_units_sold(settlement_df), get_nonsales_units(settlement_df)], axis=1)
    settlement_analysis['Total Units'] = settlement_analysis['Units Sold'] + settlement_analysis['Non-Sale Units']
    settlement_analysis = pd.concat([settlement_analysis, get_salesbased_revenue(settlement_df), get_commission(settlement_df),get_fba_fees(settlement_df), get_nonsales_revenue(settlement_df)], axis=1)
    settlement_analysis['Total Revenue'] =settlement_analysis['Sales Revenue'] + settlement_analysis['Commission'] + settlement_analysis['FBA Fees'] + settlement_analysis['Non-Sales Revenue'] 
    return settlement_analysis

def get_storage(settlement_df):
    storage_fee = settlement_df.loc[(settlement_df['amount-description'] == 'Storage Fee')]
    storage_fee = storage_fee[['amount-description', 'amount']]
    return storage_fee

'''def nonsku_table(settlement_df):
    nonsku_df=  settlement_df[['sku', 'amount']]
    return print('Non SKU Table')
    SKU: IIf([Current_statement]![sku] Is Not Null,[Current_statement]![sku],Switch([amount-description]="Previous Reserve Amount Balance","00-PREVIOUS_RESERVE_BALANCE",
    [amount-description]="Current Reserve Amount","00-CURRENT_RESERVE_BALANCE",
    [amount-description]="RemovalComplete","00-REMOVALS_TOTAL",[amount-description]="Adjustment","00-ADJUSTMENT",
    [amount-description]="DisposalComplete","00-DISPOSAL_TOTAL",[amount-description]="FBACustomerReturnPerUnitFee",
    "00-CUSTOMER_UNIT_RETURN",[amount-description]="Shipping label purchase","00-SHIPPING_LABELS_TOTAL",[amount-description]="Storage Fee",
    "00-STORAGE_MONTHLY_FEE",[amount-description]="Shipping label purchase for return","00-SHIPPING_LABEL_RETURN",[amount-description]="Subscription Fee",
    "00-SUBSCRIPTION",[amount-description]="INCORRECT_FEES_NON_ITEMIZED","00-INCORRECT_FEE_NON_ITEMIZED",[amount-description]="FBAInboundTransportationFee","00-FBAINBOUNDTRANSPORTFEE"))
'''



def print_report(finalized_report):
    '''Print report. Currently its CSV but I will make this excel with multiple worksheets'''
    return finalized_report.to_csv(input('Desired Output File Name: '))

settlement_df = pd.read_table(input("Statement File Name: "), sep='\t', dtype=dtypes)
print_report(main_table(settlement_df))

#TODO
#Get all the non sku items into it's own spot
#Tie in Monthly Storage to SKU
#Write all line items accounted for and non accounted for and double check final report against access


'''Personal Notes'''
#this report is just for a general idea of unit movement and should not be used for inventory management
#we can compare inventory reports against settlement reports in the future
#compensated clawback no units potentially involved, look into in future
# "FBA Pick and Pack Fee" return reimbursement does not have SKUS accounted for in report. So have to add that somehow, for now ill add it as a nonsku item
#add something that checks if taxes cancel out properly