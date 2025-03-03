import Metashape
import os

def read2DExport3D(chunk, path):
    """
    Reads a file containing 2D marker coordinates, projects these into 3D space using the
    dense cloud and camera parameters from the given chunk, and writes the 3D marker positions
    to an output file.
    
    Input file format (each line):
        camera name, x-Position in Pixel, y-Position in Pixel, lineType, lineNumber
        
    Output file format (each line):
        marker label, x-world, y-world, z-world, lineType, lineNumber
    """
    # Validate the input path and chunk
    if not path:
        print("Invalid path, script aborted")
        return 0
    if not os.path.isfile(path):
        print("Invalid path, script aborted")
        return 0
    if not chunk:
        print("Empty document, script aborted")
        return 0

    # Collect aligned, regular cameras from the chunk
    cameras = [camera for camera in chunk.cameras 
               if camera.transform and camera.type == Metashape.Camera.Type.Regular]
    if not cameras:
        print("Empty chunk, script aborted")
        return 0

    # Ensure the dense cloud is available in the chunk
    if not chunk.dense_cloud:
        print("Dense cloud is missing, script aborted")
        return 0

    # Get the dense cloud (surface), coordinate reference system (crs), and transformation matrix (T)
    surface = chunk.dense_cloud
    crs = chunk.crs
    T = chunk.transform.matrix

    # Open the input file for reading
    with open(path, "rt") as input_file:
        # Create an output file name based on the input file name
        if os.path.splitext(path)[1]:
            out_path = os.path.splitext(path)[0] + "_out.txt"
        else:
            out_path = path + "_out.txt"

        # Open the output file for writing
        with open(out_path, "wt") as output_file:
            lines = input_file.readlines()
            # Process each line from the input file
            for line in lines:
                # Skip lines that are too short to be valid
                if len(line) < 4:
                    continue

                # Parse the line into its components
                label, x_coord, y_coord, lineType, lineNumber = line.strip().split(",", 5)
                x_coord = float(x_coord)
                y_coord = float(y_coord)

                # Find the corresponding camera based on the label
                for camera in cameras:
                    if camera.label == label:
                        # Add a new marker to the chunk
                        marker = chunk.addMarker()
                        
                        # Create two rays from the camera for unprojection: one for z=0 and one for z=1
                        ray_origin = camera.unproject(Metashape.Vector([x_coord, y_coord, 0]))
                        ray_target = camera.unproject(Metashape.Vector([x_coord, y_coord, 1]))
                        
                        # Use the dense cloud to pick a 3D point along the ray
                        pickedPoint = surface.pickPoint(ray_origin, ray_target)
                        
                        # If a valid 3D point was found, process the marker
                        if pickedPoint is not None:
                            # Transform the picked point to the project's coordinate system
                            vector = T.mulp(pickedPoint)
                            # Project the transformed vector using the chunk's CRS
                            coord = crs.project(vector)
                            
                            # Update marker attributes
                            marker.label = label
                            marker.projections[camera] = Metashape.Marker.Projection(
                                Metashape.Vector([x_coord, y_coord]), True)
                            marker.reference.location = coord
                            marker.reference.enabled = True
                            
                            # Write the marker information to the output file
                            output_file.write("{:s},{:.6f},{:.6f},{:.6f},{:s},{:s}\n".format(
                                marker.label, coord.x, coord.y, coord.z, lineType, lineNumber))
                            
                            # Remove the marker from the chunk after processing
                            chunk.remove(marker)
                        break  # Stop searching for the camera once the correct one is found

                # Ensure data is written to disk after each processed line
                output_file.flush()

    print("Script finished")
    return 1

# Get the current chunk from the open Metashape document
chunk = Metashape.app.document.chunk
# Open a file dialog to select the input file with 2D marker coordinates
path = Metashape.app.getOpenFileName("Select the file with 2D marker coordinates:", filter="(*.txt) Text files;; (*.*) All files")

# Execute the conversion function
read2DExport3D(chunk, path)
