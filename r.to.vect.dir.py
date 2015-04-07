#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  r.to.vect.dir
#
#  Author Adrien ANDRÉ <adrien.andre@laposte.net>
#
#  2014-12-30T15:05:59-0300
#

############################################################################
#
# MODULE:      r.to.vect.dir
# AUTHOR(S):   Adrien André
# PURPOSE:     Converts a raster map into a vector map according to a direction raster map
#
#############################################################################

#%Module
#% description: Converts a raster map into a vector map according to a direction raster map.
#% keyword: raster
#% keyword: conversion
#% keyword: geometry
#% keyword: vectorization
#% keyword: direction
#%end
#%option G_OPT_R_INPUT
#%end
#%option
#% key: output
#% required: yes
#% multiple: no
#% description: Stream vector map (r.watershed output)
#%end
#%option
#% key: direction
#% required: yes
#% multiple: no
#% description: Direction raster map (r.watershed output)
#%end
#%option
#% key: accumulation
#% required: yes
#% multiple: no
#% description: Accumulation raster map (r.watershed output)
#%end
#%option
#% key: distance
#% required: yes
#% multiple: no
#% description: Distance raster map (r.stream.distance output)
#%end


import sys

import grass.script as grass

from grass.pygrass.gis.region import Region

from grass.pygrass.raster     import RasterRowIO
from grass.pygrass.raster     import RasterSegment

from grass.pygrass.utils      import pixel2coor

from grass.pygrass.vector          import VectorTopo
from grass.pygrass.vector.geometry import Line


# Direction to i, j shifts list
shift = [( 0,  0),
         (-1,  1),
         (-1,  0),
         (-1, -1),
         ( 0, -1),
         ( 1, -1),
         ( 1,  0),
         ( 1,  1),
         ( 0,  1)]


def vect(stream_in_name, stream_out_name,
         direction_in_name, accumulation_in_name, distance_in_name):
    '''Builds vector map from stream raster map.'''

    # Instantiate maps
    print "Fetching maps..."
    stream_in       = RasterRowIO(stream_in_name)
    direction_in    = RasterSegment(direction_in_name)
    accumulation_in = RasterSegment(accumulation_in_name)
    distance_in     = RasterSegment(distance_in_name)

    # Initialize output
    stream_out      = VectorTopo(stream_out_name)
    # Define the new vector map attribute table columns
    columns = [(u"cat", "INTEGER PRIMARY KEY"),
               (u"fid", "INTEGER"),
               (u"accum", "DOUBLE"),
               (u"dist", "DOUBLE"),
               (u"source_i", "INTEGER"),
               (u"source_j", "INTEGER"),
               (u"target_i", "INTEGER"),
               (u"target_j", "INTEGER")]
    print "Opening output..."
    stream_out.open('w', tab_name = stream_out_name, tab_cols = columns)

    # Open maps
    print "Loading maps..."
    stream_in.open('r')
    direction_in.open(mode = 'r')
    accumulation_in.open(mode = 'r')
    distance_in.open(mode = 'r')

    # Get the current region to compute coordinates
    region = Region()
    x_shift = region.ewres*.5
    y_shift = region.nsres*.5*(-1.0)


    print "Processing..."
    # For each stream cell...
    i = 0
    for row in stream_in:

        j = 0
        for cell in row:

            if cell < 0:
                j += 1
                continue

            # Retrieve data (direction, accumulation and distance)
            direction    = direction_in[i, j]
            accumulation = accumulation_in[i, j]
            distance     = distance_in[i, j]

            # Get i and j shifts from direction
            (di, dj) = shift[direction]

            # Compute unit vector start and end geo coordinates
            (source_y, source_x) = pixel2coor((j,      i),      region)
            (target_y, target_x) = pixel2coor((j + dj, i + di), region)

            # Build unit vector
            stream_out.write(Line([(source_x + x_shift, source_y + y_shift),
                                   (target_x + x_shift, target_y + y_shift)]),
                             (cell, accumulation, distance, i, j, i + di, j + dj)
                             )

            j += 1

        i += 1

    # Commit database changes
    stream_out.table.conn.commit()

    # Close maps
    stream_in.close()
    direction_in.close()
    accumulation_in.close()
    stream_out.close()


def main():
    '''Main function.

    Usage: r.to.vect.dir input=stream output=stream direction=dir accumulation=acc distance=dist'''

    input        = options['input']
    output       = options['output']
    direction    = options['direction']
    accumulation = options['accumulation']
    distance     = options['distance']

    vect(input, output, direction, accumulation, distance)


if __name__ == '__main__':
    options, flags = grass.parser()
    sys.exit(main())
