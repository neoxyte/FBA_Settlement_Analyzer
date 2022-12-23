import pandas as pd

#This stops data truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option("display.max_colwidth", None)

#data types for settlement flat file v2
'''dtypes = {
    "settlement-id": "category",
    "settlement-start-date": "category",
    "settlement-end-date": "category",
    "deposit-date": "category",
    "total-amount": "category",
    "currency": "category",
    "order-id": "category",
    "merchant-order-id": "category",
    "adjustment-id": "category",
    "shipment-id": "category",
    "marketplace-name": "category",
    "amount-type": "category",
    "amount-description": "category",
    "amount": "category",
    "fulfillment-id": "category",
    "posted-date": "category",
    "posted-date-time": "category",
    "order-item-code": "category",
    "merchant-order-item-id": "category",
    "merchant-adjustment-item-id": "category",
    "sku": "category",
    "quantity-purchased": "category",
    "promotion-id": "category",
}'''

#open file
df = pd.read_table('statement.txt', sep='\t', low_memory=False)


#obtain total of fba Fees
fba_fee_by_sku = df.loc[df['amount-description'] == 'FBAPerUnitFulfillmentFee']
fba_fee_by_sku = pd.melt(fba_fee_by_sku , id_vars =['sku'], value_vars =['amount'])
fba_fee_by_sku.groupby("sku")

#do top three lines for each line item needed