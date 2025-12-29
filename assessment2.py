"""
Understanding GIS: Assessment 2
@author [14202446]
"""
from time import perf_counter
from geopandas import read_file
from rasterio import open as rio_open
from numpy.random import uniform, seed


# set start time
start_time = perf_counter()	

# --- NO CODE ABOVE HERE ---


''' --- ALL CODE MUST BE INSIDE HERE --- '''

#basic structure in place, ready to start loading data
# --- NO CODE BELOW HERE ---
def generate_random_point_in_bbox(minx, miny, maxx, maxy):
  """Generate a random point within a bounding box using cartesian coordinates"""
  x = uniform(minx, maxx)
  y = uniform(miny,maxy)
  return(x,y)

def get_raster_value_at_point(x, y, raster_data, transform):
    """Extract the raster value at a given point"""
    # Convert from coordinates to array indices
    row, col = ~transform * (x, y)
    row, col = int(row), int(col)
    
    # Check bounds and return value
    if 0 <= row < raster_data.shape[0] and 0 <= col < raster_data.shape[1]:
        return raster_data[row, col]
    else:
        return 0
    
# Set seed for reproducibilit
seed(42)
# report runtime

#Load tweets data
tweets = read_file("data/wr/level3-tweets-subset.shp")
#load district polygons
distrcts = read_file("data/wr/gm-districts.shp")
#Align CRS if needed
if tweets.crs != distrcts.crs:
    tweets = tweets.to_crs(distrcts.crs)
    
#load population raster
with rio_open("data/wr/100m_pop_2019.tif") as pop_raster:
 pop_data = pop_raster.read(1)
 pop_transform = pop_raster.transform
 pop_crs = pop_raster.crs
 
 #Reproject both datasets to match the raster
 if str(tweets.crs) != str(pop_crs):
     tweets = tweets.to_crs(pop_crs)
     distrcts = distrcts.to_crs(pop_crs)
     
print(f"completed in: {perf_counter() - start_time} seconds")