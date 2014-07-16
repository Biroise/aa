
import aa
from datetime import datetime
import matplotlib.pyplot as plt

f = aa.open('/home/ambroise/atelier/anniversaire/MERRA100.prod.assim.inst3_3d_asm_Cp.19880711.SUB.nc')
#f = open('/home/ambroise/atelier/anniversaire/tmp.grib')
t = f.t(time=datetime(1988, 7, 11, 9), levels=500, latitude=(60, 90))
t.plot
plt.show()
