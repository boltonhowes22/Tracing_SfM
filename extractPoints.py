import os
import glob
import numpy as np
from skimage import io, color, morphology, measure

def extract_points(image_names, directory_to_search, suffixes, alt_names, output_file):
    """
    Extract points from skeletonized binary images corresponding to given image names.
    
    This function does the following:
      1. Searches for TIFF images in the provided directory whose filenames contain the base name of each image.
      2. For each found image, it further filters the files based on provided suffixes.
      3. Reads the selected image and converts it to grayscale (if needed).
      4. Creates a binary image by thresholding (pixels not white become True).
      5. Skeletonizes the binary image.
      6. Finds connected components in the skeleton.
      7. Downsamples the pixel indices in each connected component by a factor of 5.
      8. Writes the alternate name, x and y coordinates, suffix, and component number to the output file.
      
    Parameters:
      image_names (list of str): List of image file names.
      directory_to_search (str): Directory to search for TIFF images.
      suffixes (list of str): List of suffixes to look for in the image filenames.
      alt_names (list of str): Alternate names corresponding to image_names.
      output_file (str): File path for the output file.
      
    Output file format (each line):
      alt_name, x-coordinate, y-coordinate, suffix, component_index
    """
    
    # Open the output file in write text mode
    with open(output_file, 'wt') as f_out:
        # Get a list of all .tif files in the target directory
        listing = glob.glob(os.path.join(directory_to_search, '*.tif'))
        
        # Iterate over each image name provided in image_names
        for idx, image_name in enumerate(image_names):
            # Extract the base name (without extension) from the image name
            name_only, _ = os.path.splitext(os.path.basename(image_name))
            
            # Filter the listing to files whose names contain the base name
            matching_files = [file for file in listing if name_only in os.path.basename(file)]
            
            # Iterate over each suffix in the provided suffixes list
            for suffix in suffixes:
                # Further filter the matching files to those containing the current suffix
                files_with_suffix = [file for file in matching_files if suffix in os.path.basename(file)]
                
                # Process only if we found at least one file with the given suffix
                if files_with_suffix:
                    # Use the first matching file (assuming one match per suffix)
                    image_path = files_with_suffix[0]
                    
                    # Load the image using skimage.io.imread
                    this_image = io.imread(image_path)
                    
                    # If the image is in color (has 3 dimensions), convert it to grayscale
                    if this_image.ndim == 3:
                        this_image = color.rgb2gray(this_image)
                    
                    # Convert the image to a binary image:
                    # For uint8 images, treat pixels with values less than 255 as foreground.
                    # For floating point images (assumed in [0,1]), treat pixels less than 1.0 as foreground.
                    if this_image.dtype == np.uint8:
                        binary_image = this_image < 255
                    else:
                        binary_image = this_image < 1.0
                    
                    # Skeletonize the binary image to thin it down to a 1-pixel-wide representation
                    skeleton = morphology.skeletonize(binary_image)
                    
                    # Label connected components in the skeleton
                    # measure.label returns an array where each connected region has a unique label
                    labeled_image = measure.label(skeleton, connectivity=2)
                    
                    # Extract properties for each connected component (region)
                    regions = measure.regionprops(labeled_image)
                    
                    # For each connected component, process the pixel coordinates
                    for comp_idx, region in enumerate(regions, start=1):
                        # region.coords returns an array of (row, col) pixel coordinates
                        # Downsample the list of pixel coordinates by taking every 5th point
                        subsampled_coords = region.coords[::5]
                        
                        # Write each coordinate to the output file
                        for (y, x) in subsampled_coords:
                            # Format: alt_name, x, y, suffix, component index
                            f_out.write("{},{},{},{},{}\n".format(alt_names[idx], int(x), int(y), suffix, comp_idx))

# Example usage:
# image_names = ['image1.tif', 'image2.tif']
# directory_to_search = '/path/to/images'
# suffixes = ['_suffix1', '_suffix2']
# alt_names = ['AltName1', 'AltName2']
# output_file = '/path/to/output.txt'
# extract_points(image_names, directory_to_search, suffixes, alt_names, output_file)
