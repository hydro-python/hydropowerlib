from tkinter import filedialog
import pandas as pd
import numpy as np

jdl=pd.Series([])
files = filedialog.askopenfilename(title="Select files with water flow values for the plant:", filetypes = [("csv files", "*.csv")], multiple=1)
for file in files:
    df = pd.read_csv(file)
    jdl=jdl.append(to_append=df["Q"],ignore_index=True)
jdl=pd.Series(jdl.sort_values(ascending=False).values,index=jdl.index/max(jdl.index)*100)
val=np.interp(np.arange(0,100,1), jdl.index, jdl.values,left=0, right=0)[30]
print(val)


