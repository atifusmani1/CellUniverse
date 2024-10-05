"""Converts Cell Universe data into a radial tree plot."""
"""Attempt to push after Nil took ownership... and after redirecting to new URL... and the next morning"""
"""And now it's back to me"""

import argparse
import csv
import math
import sys
from pathlib import Path

from config import *

from svgwrite import Drawing

from parseColony import parseColony

import random
import time

SVG_SIZE = 512

def _print_error(msg):
    print(f'ERROR: {msg}', file=sys.stderr)


class CellNode(object):
    '''Object representing an instance of a single cell over time.'''

    def __init__(self, object_id, parent_id, initial_frame):
        self._object_id = object_id
        self._parent_id = parent_id
        self._start_frame = initial_frame
        self._end_frame = initial_frame + 1
        self._children = []

        self.angle = 0.0
        self.pie_angle = [] # angles of leaves based on root

    def exists_in(self, frame):
        '''Set the latest frame the cell exists in.'''
        self._end_frame = frame + 1

    @property
    def object_id(self):
        return self._object_id

    @property
    def parent_id(self):
        return self._parent_id

    @property
    def start_frame(self):
        return self._start_frame

    @property
    def end_frame(self):
        return self._end_frame

    @property
    def children(self):
        return self._children

def generateRandomColors(number_of_colors):
    colors = set()
    while len(colors) < number_of_colors:
        colors.add("#"+''.join([random.choice('0123456789ABCDEF') for j in range(6)]))
    colors = sorted(list(colors))
    return colors

def getGenerations(node):
    if not node.children: return 1
    return max([getGenerations(child) for child in node.children]) + 1

def angle_spacing_generator(count):
    spacing = 2*math.pi/count
    for i in range(count):
        yield i*spacing+(3*math.pi/4)


def get_leaf_count(node):
    '''Retruns the number of leaf nodes the plot has in total.'''
    if not node.children:
        return 1
    return sum([get_leaf_count(child) for child in node.children])


def set_angles_and_frames(node, angle_spacings, lowest_angle, angleFile, frameFile):
    '''Sets the angles for all of the nodes.'''
    if not node.children:
        node.angle = next(angle_spacings)
        node.pie_angle = [node.angle+(lowest_angle/2)]
    else:
        angles = []
        pie_angles = []
        for child in node.children:
            angle,pie_angle = set_angles_and_frames(child, angle_spacings, lowest_angle, angleFile, frameFile)
            angles.append(angle)
            pie_angles += pie_angle
        node.angle = sum(angles)/len(node.children)
        node.pie_angle = pie_angles
    angleFile.write(",\n\t\"b"+node.object_id+"\": "+str(node.angle))
    frameFile.write(",\n\t\"b"+node.object_id+"\": ["+str(node.start_frame)+","+str(node.end_frame)+"]")
    return (node.angle,node.pie_angle)


def convert_to_tree(rows):
    '''Returns a list of the root nodes. Will also return last image number'''
    merge_dict = {}
    root_list = []
    last_image = 0

    for row in rows:
        frame = int(row['ImageNumber'])
        last_image = max(last_image, frame)
        object_id = row['ObjectID'].strip()
        parent_id = row['ParentObjectID'].strip()

        if object_id in merge_dict:
            merge_dict[object_id].exists_in(frame)
        else:
            node = CellNode(object_id, parent_id, frame)
            merge_dict[object_id] = node

            if parent_id == '':
                root_list.append(node)
            else:
                merge_dict[parent_id].children.append(node)

    return (root_list, last_image)


def compress_edge(root):
    # find the furthest the individual cell goes
    node = root.children[0]
    while len(node.children) == 1:
        node = node.children[0]

    # compress
    if not node.children:
        root.exists_in(node.end_frame)
        root.children.clear()
    else:
        root.exists_in(node.children[0].start_frame - 1)
        root.children.clear()
        root.children.extend(node.children)


def compress_tree(node):
    if len(node.children) == 1:
        compress_edge(node)
    for child in node.children:
        compress_tree(child)


def draw_radial_tree_node(svg_drawing, tree_plot, node, rad_grad, step_size):
    tree_plot.add(svg_drawing.line(
        start=(step_size*node.start_frame, 0),
        end=(step_size*node.end_frame, 0),
        transform=f'translate({SVG_SIZE/2} {SVG_SIZE/2}) '
                  f'rotate({round(-180*node.angle/math.pi, 9)})'))

    if node.children:
        for child in node.children:
            draw_radial_tree_node(svg_drawing, tree_plot, child, rad_grad, step_size)

        angles = [child.angle for child in node.children]
        max_angle = max(angles)
        min_angle = min(angles)

        path = svg_drawing.path(
            f'M{round(step_size*node.end_frame*math.cos(-max_angle), 9)},'
            f'{round(step_size*node.end_frame*math.sin(-max_angle), 9)}',
            transform=f'translate({SVG_SIZE/2} {SVG_SIZE/2})')
        path.push_arc(
            (round(step_size*node.end_frame*math.cos(-min_angle), 9),
             round(step_size*node.end_frame*math.sin(-min_angle), 9)),
            0,
            (round(step_size*node.end_frame, 9), round(step_size*node.end_frame, 9)),
            large_arc=False,
            absolute=True)
        tree_plot.add(path)

def save_radial_tree_plot(filename, root_list, step_size):
    
    #  define some params
    white = "rgb(255, 255, 255)"
    black = "rgb(0, 0, 0)"

    #  create the drawing surface
    svg_drawing = Drawing(
        filename=filename,
        size=(SVG_SIZE, SVG_SIZE),
        debug=True)
    

    #  create defs, in this case, just a single gradient
    rad_grad = svg_drawing.radialGradient(("50%", "50%"), "100%", ("50%", "50%"), id="rad_grad")
    rad_grad.add_stop_color("0%", black, 255)
    rad_grad.add_stop_color("100%", white, 255)
    svg_drawing.defs.add(rad_grad)
    
    tree_plot = svg_drawing.mask(
        id='treeplot',
        style='stroke: black; stroke-width: 3; fill: none; stroke-linecap: round; stroke-opacity: 0.5;')  
    
    tree_plot.add(svg_drawing.rect( (0, 0), (SVG_SIZE, SVG_SIZE) ).fill(white))

    for root in root_list:
        draw_radial_tree_node(svg_drawing, tree_plot, root, rad_grad, step_size)    
    
    base_rect = svg_drawing.rect( (0, 0), (SVG_SIZE, SVG_SIZE), mask="url(#treeplot)").fill(black)
    svg_drawing.add(base_rect)  
    svg_drawing.add(tree_plot)

    svg_drawing.save()  
    
def save_pie_chart(filename, all_angles, step_size, colors):
    
    #  create the drawing surface
    svg_drawing = Drawing(
        filename=filename,
        size=(SVG_SIZE, SVG_SIZE),
        debug=True)
    
    start_x = SVG_SIZE//2
    start_y = SVG_SIZE//2
    radius = SVG_SIZE//2
    
    radians0 = all_angles[-1]
    for i in range(len(all_angles)):
        radians1 = all_angles[i]
        dx0 = radius*(math.sin(radians0))
        dy0 = radius*(math.cos(radians0))
        dx1 = radius*(math.sin(radians1))
        dy1 = radius*(math.cos(radians1))
    
        m0 = round(dy0, 9) 
        n0 = round(-dx0, 9) 
        m1 = round(-dy0 + dy1, 9)
        n1 = round(dx0 - dx1, 9)
    
        w = svg_drawing.path(d="M {0},{1} l {2},{3} a {4},{4} 0 0,0 {5},{6} z".format(start_x, start_y, m0, n0, radius, m1, n1),
                 fill = colors[i], 
                 stroke="none",
                )
        svg_drawing.add(w)
        radians0 = radians1
    
    svg_drawing.save()

def main():
    # Get the path to the output directory from the command-line
    parser = argparse.ArgumentParser(description='Generate a radial tree plot.')
    parser.add_argument('-seed', metavar='N', type=int, default=None, help='seed for random colors')
    parser.add_argument('output_path', metavar='OUTPUT_PATH', type=str,
                        help='the desired output path') 
    args = parser.parse_args()

    # Set rng seed
    seed = int(time.time() * 1000) % (2**32)
    if args.seed != None:
        seed = args.seed
    random.seed(seed)
    print(f'Seed: {seed}')

    # Load the data into memory
    rows = parseColony(args.output_path)

    # Merge individual cells temporally and generate tree
    # Create angle file
    root_list,last_image =  convert_to_tree(rows)
    leaf_counts = [get_leaf_count(root) for root in root_list]
    total_leaves = sum(leaf_counts)
    lowest_angle = 2*math.pi/total_leaves
    step_size = SVG_SIZE/2/(last_image+2)
    angle_spacings = angle_spacing_generator(total_leaves)

    angleFile = open(args.output_path+"/"+angleFilename, 'w')
    frameFile = open(args.output_path+"/"+frameFilename, 'w')

    angleFile.write("{\n\t\"name\": \"angle\"")
    frameFile.write("{\n\t\"name\": [\"start\",\"end\"]")
    for root in root_list:
        set_angles_and_frames(root, angle_spacings, lowest_angle, angleFile, frameFile)
    angleFile.write("\n}")
    frameFile.write("\n}")

    angleFile.close()
    frameFile.close()

    # Compress tree
    for root in root_list:
        compress_tree(root)


    # Draw the SVG radial tree plot
    save_radial_tree_plot(args.output_path+"/"+treeFilename, root_list, step_size)
    
    # Draw the SVG pie color chart
    all_angles = []
    for node in root_list:
        all_angles += node.pie_angle
    all_angles = sorted(all_angles)
    save_pie_chart(args.output_path+"/"+pieFilename, all_angles, step_size, generateRandomColors(len(all_angles)))
    

if __name__ == '__main__':
    main()
