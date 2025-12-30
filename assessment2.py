"""
Understanding GIS: Assessment 2
@author [14202446]
"""
from time import perf_counter
from geopandas import read_file
from rasterio import open as rio_open
from numpy.random import uniform, seed
from numpy import zeros
from shapely.geometry import Point
from matplotlib.pyplot import subplots
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
from rasterio.plot import show as rio_show
from matplotlib.colors import LinearSegmentedColormap



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
    
def weighted_redistribution(tweets_gdf, districts_gdf, weight_raster, weight_transform, n_iterations= 100):
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

def create_density_surface(points_gdf, raster_template, cell_size=500):
   """
    Create a density surface by counting points in each cell.
    Using 500m cells for a good visualization scale.
    """
   bounds = raster_template.bounds
   
   width = int((bounds.right - bounds.left) / cell_size)
   height = int((bounds.top - bounds.bottom) / cell_size)
    
   density = zeros((height, width))
   
   for _, point in points_gdf.iterrows():
     x, y = point.geometry.x, point.geometry.y
        
     col = int((x - bounds.left) / cell_size)
     row = int((bounds.top - y) / cell_size)
        
     if 0 <= row < height and 0 <= col < width:
            density[row, col] += 1
    
   from rasterio.transform import from_bounds
   transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, width, height)
    
   return density, transform   
# Set seed for reproducibilit
seed(42)
# report runtime

#Load tweets data
tweets = read_file("data/wr/level3-tweets-subset.shp")
#load district polygons
districts = read_file("data/wr/gm-districts.shp")
#Align CRS if needed
if tweets.crs != districts.crs:
    tweets = tweets.to_crs(districts.crs)
    
#load population raster
with rio_open("data/wr/100m_pop_2019.tif") as pop_raster:
 pop_data = pop_raster.read(1)
 pop_transform = pop_raster.transform
 pop_crs = pop_raster.crs
 
 #Reproject both datasets to match the raster
 if str(tweets.crs) != str(pop_crs):
     tweets = tweets.to_crs(pop_crs)
     districts = districts.to_crs(pop_crs)
 
# Run the algorithm
redistributed_tweets = weighted_redistribution(
  tweets_gdf=tweets,
  districts_gdf=districts, 
  weight_raster=pop_data,
  weight_transform=pop_transform,
  n_iterations=100
)

# Generate density surfaces for visualization
with rio_open("./data/wr/100m_pop_2019.tif") as pop_raster:
    original_density, density_transform = create_density_surface(tweets, pop_raster, cell_size=500)
    redistributed_density, _ = create_density_surface(redistributed_tweets, pop_raster, cell_size=500)

# Create side-by-side comparison
fig,(ax1, ax2) = subplots(1, 2, figsize=(20, 10))

# Let panel: Original
ax1.set_title("Original Tweet Locations (False Hotspots)", fontsize=14, fontweight='bold')
ax1.axis('off')

rio_show(pop_data, ax=ax1, transform=pop_transform, cmap='YlOrRd', alpha=0.3)
districts.plot(ax=ax1, facecolor='none', edgecolor='black', linewidth=1)
rio_show(original_density, ax=ax1, transform=density_transform,
         cmap=LinearSegmentedColormap.from_list('hotspot', [(0,0,0,0), (0,0,1,0.6), (1,0,0,0.8)]))
tweets.plot(ax=ax1, markersize=5, color='blue', alpha=0.5)

ax1.legend(handles=[
    Patch(facecolor='red', alpha=0.6, label='High Tweet Density'),
    Patch(facecolor='none', edgecolor='black', label='Districts'),
    Patch(facecolor='yellow', alpha=0.3, label='Population Density')
], loc='upper right')
ax1.add_artist(ScaleBar(dx=1, units="m", location="lower left"))

# Right panel: Redistributed
ax2.set_title("Redistributed Tweet Locations (Weighted by Population)", fontsize=14, fontweight='bold')
ax2.axis('off')

rio_show(pop_data, ax=ax2, transform=pop_transform, cmap='YlOrRd', alpha=0.3)
districts.plot(ax=ax2, facecolor='none', edgecolor='black', linewidth=1)
rio_show(redistributed_density, ax=ax2, transform=density_transform,
         cmap=LinearSegmentedColormap.from_list('hotspot', [(0,0,0,0), (0,0,1,0.6), (1,0,0,0.8)]))
redistributed_tweets.plot(ax=ax2, markersize=5, color='green', alpha=0.5)

ax2.legend(handles=[Patch(facecolor='red', alpha=0.6, label='High Tweet Density'),
    Patch(facecolor='none', edgecolor='black', label='Districts'),
    Patch(facecolor='yellow', alpha=0.3, label='Population Density')], loc='upper right')
ax2.add_artist(ScaleBar(dx=1, units="m", location="lower left"))

fig.suptitle('Weight Redistribution: Addressing False Hotspots in Royal Wedding Twitter Data', fontsize=16, fontweight='bold', y=0.98)

print(f"completed in: {perf_counter() - start_time} seconds")