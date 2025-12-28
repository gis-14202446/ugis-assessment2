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
tweets = read_file("./data/wr/level3-tweets-subset.shp")
#load district polygons
distrcts = read_file("./data/wr/gm-districts.shp")

print(f"completed in: {perf_counter() - start_time} seconds")