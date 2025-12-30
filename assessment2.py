"""
Understanding GIS: Assessment 2
@author [14202446]
"""
from time import perf_counter
from geopandas import read_file
from rasterio import open as rio_open
from numpy.random import uniform, seed
from shapely.geometry import Point


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
    
def weighted_redisdtribution(tweets_gdf, districts_gdf, weight_raster, weight_transform, n_iterations= 100):
  """Redistribute tweets based on population density weighting"""
  redistributed_tweets = tweets_gdf.copy()
  
  # Create spatial index for efficient lookups
  districts_sindex = districts_gdf.sindex
  redistributed_count = 0
    
  for idx, tweet in tweets_gdf.iterrows():
      # Use spatial index to find candidate districts
      possible_matches_index = list(districts_sindex.intersection(tweet.geometry.bounds))
      possible_matches = districts_gdf.iloc[possible_matches_index]
      precise_matches = possible_matches[possible_matches.contains(tweet.geometry)]
        
      if len(precise_matches) == 0:
          continue
        
      # Get the district polygon
      district = precise_matches.iloc[0]
      district_geom = district.geometry
      minx, miny, maxx, maxy = district_geom.bounds
      
      max_weight = 0
      best_point = None
     
      # Try n random points and pick the best
      for _ in range(n_iterations):
         rand_x, rand_y = generate_random_point_in_bbox(minx, miny, maxx, maxy)
         rand_point = Point(rand_x, rand_y)
            
         # Make sure point is actually inside the district
         if not district_geom.contains(rand_point):
             continue
            
         # Sample population density
         weight = get_raster_value_at_point(rand_x, rand_y, weight_raster, weight_transform)
            
         # Keep track of best candidate
         if weight > max_weight:
             max_weight = weight
             best_point = rand_point
        
      # Update location if we found a better spot
      if best_point is not None and max_weight > 0:
          redistributed_tweets.at[idx, 'geometry'] = best_point
          redistributed_count += 1
    
  print(f"Redistributed {redistributed_count}/{len(tweets_gdf)} tweets")
  return redistributed_tweets  
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
 
# Run the algorithm
redistributed_tweets = weighted_redistribution(
  tweets_gdf=tweets,
  districts_gdf=districts, 
  weight_raster=pop_data,
  weight_transform=pop_transform,
  n_iterations=100
)

     
print(f"completed in: {perf_counter() - start_time} seconds")