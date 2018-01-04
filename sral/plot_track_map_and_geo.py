#! /opt/local/bin/python2.7

import os
import subprocess
import sys
import logging
import argparse
import datetime, time
import numpy as np
import netCDF4 as nc
import matplotlib
import matplotlib.pyplot as plt
from   mpl_toolkits.basemap import Basemap
from   matplotlib           import gridspec, cm
import warnings
import matplotlib.collections as mcoll
import matplotlib.path as mpath
warnings.filterwarnings('ignore')

def colorline(
              x, y, z=None, cmap=plt.get_cmap('copper'), norm=plt.Normalize(0.0, 1.0),
              linewidth=3, alpha=1.0):
    """
        http://nbviewer.ipython.org/github/dpsanders/matplotlib-examples/blob/master/colorline.ipynb
        http://matplotlib.org/examples/pylab_examples/multicolored_line.html
        Plot a colored line with coordinates x and y
        Optionally specify colors in the array z
        Optionally specify a colormap, a norm function and a line width
        """
    
    # Default colors equally spaced on [0,1]:
    if z is None:
        z = np.linspace(0.0, 1.0, len(x))
    
    # Special case if a single number:
    if not hasattr(z, "__iter__"):  # to check for numerical input -- this is a hack
        z = np.array([z])

    z = np.asarray(z)

    segments = make_segments(x, y)
    lc = mcoll.LineCollection(segments, array=z, cmap=cmap, norm=norm,
                          linewidth=linewidth, alpha=alpha)

    ax = plt.gca()
    ax.add_collection(lc)

    return lc


def make_segments(x, y):
    """
        Create list of line segments from x and y coordinates, in the correct format
        for LineCollection: an array of the form numlines x (points per line) x 2 (x
        and y) array
        """
    
    points = np.array([x, y]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    return segments

input_root = '.'
input_path = 'S3A_SR_2_WAT____20171015T113957_20171015T122800_20171017T052947_2882_023_208______MAR_O_ST_002.SEN3'
input_file = 'standard_measurement.nc'
pad        = 1.0
xdist      = 20
ydist      = 10
dpi        = 300
proj       = 'mill'
my_file    = os.path.join(input_root,input_path,input_file)

# open netCDF
nc_fid = nc.Dataset(my_file)

# get coordinate variables
lon_01    = nc_fid.variables['lon_01'][:]
lat_01    = nc_fid.variables['lat_01'][:]
lon_20_ku = nc_fid.variables['lon_cor_20_ku'][:]
lat_20_ku = nc_fid.variables['lat_cor_20_ku'][:]
lon_20_c  = nc_fid.variables['lon_20_c'][:]
lat_20_c  = nc_fid.variables['lat_20_c'][:]

# clip longitude if required (not needed for Miller projection)
if proj != 'mill':
   lon_01[lon_01>180.]       = lon_01[lon_01>180.]-360.
   lon_20_ku[lon_20_ku>180.] = lon_20_ku[lon_20_ku>180.]-360.
   lon_20_c[lon_20_c>180.]   = lon_20_c[lon_20_c>180.]-360.

# get surface classes
surf_type_class_20_ku = nc_fid.variables['surf_type_class_20_ku'][:].astype('int')

# get variables
ssha_20_ku=nc_fid.variables['ssha_20_ku'][:]
swh_ocean_20_ku=nc_fid.variables['swh_ocean_20_ku'][:]
nc_fid.close()

# SAR Ku
ocean_wv   = np.where([surf_type_class_20_ku == 0])[1]
sea_ice_wv = np.where([surf_type_class_20_ku == 1])[1]
lead_wv    = np.where([surf_type_class_20_ku == 2])[1]
unclass_wv = np.where([surf_type_class_20_ku == 3])[1]

ssha_20_ku[np.abs(ssha_20_ku)>1.0] =np.nan
swh_ocean_20_ku[np.abs(swh_ocean_20_ku)>10.0] =np.nan

#plt.plot(ssha_20_ku[ocean_wv]/np.nanmax(ssha_20_ku[ocean_wv]))
#plt.plot(swh_ocean_20_ku[ocean_wv]/np.nanmax(swh_ocean_20_ku[ocean_wv]),'r')
#plt.show()
#asdf

print '--------------------'
print 'Num lon points 20_ku:            '+str(np.shape(lon_20_ku)[0])
print 'Num lon points 20_c:             '+str(np.shape(lon_20_c)[0])
print 'Num lon points 1:                '+str(np.shape(lon_01)[0])

print 'Num SSH points 20_ku:            '+str(np.shape(ssha_20_ku)[0])
print 'Num SWH points 20_Ku:            '+str(np.shape(swh_ocean_20_ku)[0])
print '--------------------'

print '------Extents: Ku---'
print np.nanmin(lon_20_ku)
print np.nanmax(lon_20_ku)
print np.nanmin(lat_20_ku)
print np.nanmax(lat_20_ku)
print '----------C---------'
print np.nanmin(lon_20_c)
print np.nanmax(lon_20_c)
print np.nanmin(lat_20_c)
print np.nanmax(lat_20_c)
print '--------------------'

minlon_plot = 150
maxlon_plot = 170
minlat_plot = -70
maxlat_plot = 10
LON_0 = np.nanmean(lon_01)

#figure 1
fig1 = plt.figure(figsize=(xdist, ydist), dpi=dpi)
fsz = xdist
plt.rc('font',size=14)

#gridspec paramaters
gs  = gridspec.GridSpec(6, 6)
gs.update(hspace=0.4)

#map
matplotlib.rcParams['contour.negative_linestyle'] = 'solid'
m     = Basemap(projection=proj,llcrnrlat=minlat_plot,urcrnrlat=maxlat_plot,\
                llcrnrlon=minlon_plot,urcrnrlon=maxlon_plot,lon_0=LON_0, resolution='i')

#plot main map
X_20_ku,Y_20_ku = m(lon_20_ku, lat_20_ku)

axes = plt.subplot(gs[0:, 0])
m.scatter(X_20_ku[ocean_wv],Y_20_ku[ocean_wv],s=5.0, c=ssha_20_ku[ocean_wv], cmap=cm.RdBu,marker='.',zorder=0)
plt.clim(-0.5,0.5)
cbar=plt.colorbar()
cbar.ax.tick_params(labelsize=12)
cbar.set_label('SSHA [m]', labelpad=-55, y=0.5, rotation=90,fontsize=14)

zordcoast=10
m.fillcontinents(color=[0.7,0.7,0.7],zorder=zordcoast)
m.drawcoastlines(color='k',linewidth=0.5,zorder=zordcoast+1)
m.drawcountries(color='k',linewidth=0.25,zorder=zordcoast+2)
m.drawparallels(np.arange(-100,  100,  20), labels=[1,0,0,0],fontsize=fsz,linewidth=0.1)
m.drawmeridians(np.arange(-180, 180, 20), labels=[0,0,0,1],fontsize=fsz,linewidth=0.1)

axes = plt.subplot(gs[0:, 1])

m.scatter(X_20_ku[ocean_wv],Y_20_ku[ocean_wv],s=5.0, c=(swh_ocean_20_ku[ocean_wv]), cmap=cm.CMRmap_r,marker='.',zorder=0)
cbar=plt.colorbar()
cbar.ax.tick_params(labelsize=12)
cbar.set_label('SWH [m]', labelpad=-30, y=0.5, rotation=90,fontsize=14)

zordcoast=10
m.fillcontinents(color=[0.7,0.7,0.7],zorder=zordcoast)
m.drawcoastlines(color='k',linewidth=0.5,zorder=zordcoast+1)
m.drawcountries(color='k',linewidth=0.25,zorder=zordcoast+2)
m.drawparallels(np.arange(-100,  100,  20), labels=[0,0,0,0],fontsize=fsz,linewidth=0.1)
m.drawmeridians(np.arange(-180, 180, 20), labels=[0,0,0,1],fontsize=fsz,linewidth=0.1)

axes = plt.subplot(gs[0:, 2])

m     = Basemap(projection=proj,llcrnrlat=-89,urcrnrlat=10,\
                llcrnrlon=150,urcrnrlon=184,lon_0=LON_0, resolution='i')
X_20_ku,Y_20_ku = m(lon_20_ku, lat_20_ku)

m.plot(X_20_ku[unclass_wv],Y_20_ku[unclass_wv],markersize=1.0,linewidth=0.0,marker='.',color='0.8',markerfacecolor='0.8',fillstyle='full',zorder=0)
m.plot(X_20_ku[ocean_wv],Y_20_ku[ocean_wv],markersize=5.0,linewidth=0.0,marker='.',color='#4682b4',markerfacecolor='#4682b4',fillstyle='full',zorder=1)
m.plot(X_20_ku[sea_ice_wv],Y_20_ku[sea_ice_wv],markersize=5.0,linewidth=0.0,marker='.',color='#8a2be2',markerfacecolor='#8a2be2',fillstyle='full',zorder=2)
m.plot(X_20_ku[lead_wv],Y_20_ku[lead_wv],markersize=1.0,linewidth=0.0,marker='.',color='#3cb371',markerfacecolor='#3cb371',fillstyle='full',zorder=3)
zordcoast=10
m.fillcontinents(color=[0.7,0.7,0.7],zorder=zordcoast)
m.drawcoastlines(color='k',linewidth=0.5,zorder=zordcoast+1)
m.drawcountries(color='k',linewidth=0.25,zorder=zordcoast+2)
m.drawparallels(np.arange(-100,  100,  20), labels=[0,1,1,1],fontsize=fsz,linewidth=0.1)
m.drawmeridians(np.arange(-180, 180, 20), labels=[0,0,0,1],fontsize=fsz,linewidth=0.1)
px,py=m([180, 183, 183, 180, 180],[-70.5, -70.5, -72.5, -72.5, -70.5])
m.plot(px,py,color='k',linewidth=1.0,zorder=20)

#plot inset map
axes = plt.subplot(gs[5, -1])
m     = Basemap(projection=proj,llcrnrlat=-71.9,urcrnrlat=-71.5,\
                llcrnrlon=181.3,urcrnrlon=182,lon_0=181.65, resolution='i')
X_20_ku,Y_20_ku = m(lon_20_ku, lat_20_ku)

X_20_ku,Y_20_ku = m(lon_20_ku, lat_20_ku)
m.plot(X_20_ku[unclass_wv],Y_20_ku[unclass_wv],markersize=1.0,linewidth=0.0,marker='.',color='0.8',markerfacecolor='0.8',fillstyle='full',zorder=0)
m.plot(X_20_ku[sea_ice_wv],Y_20_ku[sea_ice_wv],markersize=5.0,linewidth=0.0,marker='.',color='#8a2be2',markerfacecolor='#8a2be2',markeredgecolor='#8a2be2',fillstyle='full',zorder=2)
m.plot(X_20_ku[lead_wv],Y_20_ku[lead_wv],markersize=5.0,linewidth=0.0,marker='.',color='#3cb371',markerfacecolor='#3cb371',markeredgecolor='#3cb371',fillstyle='full',zorder=3)
m.fillcontinents(color=[0.7,0.7,0.7],zorder=zordcoast)
m.drawcoastlines(color='k',linewidth=0.5,zorder=zordcoast+1)
m.drawcountries(color='k',linewidth=0.25,zorder=zordcoast+2)
m.drawparallels(np.arange(-100,  100,  20), labels=[0,0,0,0],fontsize=fsz,linewidth=0.1)
m.drawmeridians(np.arange(-180, 180, 30), labels=[0,0,0,0],fontsize=fsz,linewidth=0.1)
axes.set_position([0.30, 0.115, 0.3, 0.17])

# plot waveforms
axes = plt.subplot(gs[0:3, 4:])

VAR=ssha_20_ku[(lon_20_ku > minlon_plot) & (lon_20_ku < maxlon_plot)]
LAT=lat_20_ku[(lon_20_ku > minlon_plot) & (lon_20_ku < maxlon_plot)]
plt.plot(LAT,VAR,linewidth=0.6, color='k')
plt.scatter(LAT[VAR>0],VAR[VAR>0],s=0.1,c=VAR[VAR>0],cmap=cm.Reds,zorder=10)
plt.scatter(LAT[VAR<=0],VAR[VAR<=0],s=0.1,c=VAR[VAR<=0],cmap=cm.Blues_r,zorder=10)
plt.xlabel('Latitude',fontsize=fsz)
plt.ylabel('Sea surface height anomaly [m]',fontsize=fsz)

axes = plt.subplot(gs[4:6, 4:])
VAR=swh_ocean_20_ku[(lon_20_ku > minlon_plot) & (lon_20_ku < maxlon_plot)]
LAT=lat_20_ku[(lon_20_ku > minlon_plot) & (lon_20_ku < maxlon_plot)]
plt.plot(LAT,VAR,linewidth=0.6, color='k')
plt.scatter(LAT,VAR,s=0.1,c=VAR,cmap=cm.CMRmap_r,zorder=10)
plt.xlabel('Latitude',fontsize=fsz)
plt.ylabel('Significant wave height [m]',fontsize=fsz)

plt.savefig('Track_Map_Geo.png')

