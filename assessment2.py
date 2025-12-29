"""
Understanding GIS: Assessment 2
@author [14202446]
"""
from time import perf_counter
from geopandas import read_file
from rasterio import open as rio_open


# set start time
start_time = perf_counter()	

# --- NO CODE ABOVE HERE ---


''' --- ALL CODE MUST BE INSIDE HERE --- '''

#basic structure in place, ready to start loading data
# --- NO CODE BELOW HERE ---

# report runtime

#Load tweets data
tweets = read_file(r"D:\p drive\data\wr\level3-tweets-subset.shp")
#load district polygons
distrcts = read_file(r"D:\p drive\data\wr\gm-districts.shp")
#Align CRS if needed
if tweets.crs != distrcts.crs:
    tweets = tweets.to_crs(distrcts.crs)
    
#load population raster
with rio_open(r"D:\p drive\data\wr\100m_pop_2019.tif") as pop_raster:
 pop_data = pop_raster.read(1)
 pop_transform = pop_raster.transform
 pop_crs = pop_raster.crs
 
 #Reproject both datasets to match the raster
 if str(tweets.crs) != str(pop_crs):
     tweets = tweets.to_crs(pop_crs)
     distrcts = distrcts.to_crs(pop_crs)
     
print(f"completed in: {perf_counter() - start_time} seconds")