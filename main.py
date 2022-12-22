import pandas as pd

#This stops data truncation
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option("display.max_colwidth", None)

#open file
flat_file = pd.read_table('statement.txt', sep='\t',dtype='unicode')

print(flat_file)
