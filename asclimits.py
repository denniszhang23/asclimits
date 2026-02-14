import camelot
import pandas as pd
import numpy as np

#parse through file
file_path = r'C:\Users\admin\Downloads\ASC2024_Route_Book_260201_133015.pdf'
tables = camelot.read_pdf(file_path, pages='23', flavor='lattice')

df = tables[0].df
indexes = df[0]
speeds = df[6]

#replaces blank spots with what the speed limit should be
fillspeed = (speeds.replace(r'^\s*$', np.nan, regex = True)).ffill()
fillspeed = fillspeed.iloc[1:].copy()
same = fillspeed != fillspeed.shift()
fixindex = indexes.iloc[1:].copy()
location_change = fixindex[same]

# speed changes at these locations/indexes 
print(location_change.values)