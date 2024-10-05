import os
from tkinter import ttk
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog, messagebox
import tkinter.simpledialog as simpledialog
from PIL import Image, ImageTk, ImageGrab
from point import Point

import numpy as np
import platform
from collections import defaultdict
from enum import Enum

def is_point_inside_polygon(point, polygon):
        # point: a tuple of (x, y) coordinates of the point
        # polygon: a list of tuples of (x, y) coordinates of the vertices of the polygon

        # Calculate the area of the quadrilateral formed by the four points
        x1, y1 = polygon[0]
        x2, y2 = polygon[1]
        x3, y3 = polygon[2]
        x4, y4 = polygon[3]
        area_quad = abs(x1 * y2 + x2 * y3 + x3 * y4 + x4 * y1 - x2 * y1 - x3 * y2 - x4 * y3 - x1 * y4) / 2

        # Divide the quadrilateral into two triangles by drawing a diagonal
        triangle1 = [point, polygon[0], polygon[2]]
        triangle2 = [point, polygon[1], polygon[3]]

        # Calculate the area of each triangle formed by the point and two adjacent vertices of the quadrilateral
        area_tri1 = abs(triangle1[0][0] * triangle1[1][1] + triangle1[1][0] * triangle1[2][1] + triangle1[2][0] * triangle1[0][1]
                        - triangle1[1][0] * triangle1[0][1] - triangle1[2][0] * triangle1[1][1] - triangle1[0][0] * triangle1[2][1]) / 2

        area_tri2 = abs(triangle2[0][0] * triangle2[1][1] + triangle2[1][0] * triangle2[2][1] + triangle2[2][0] * triangle2[0][1]
                        - triangle2[1][0] * triangle2[0][1] - triangle2[2][0] * triangle2[1][1] - triangle2[0][0] * triangle2[2][1]) / 2

        # If the sum of the areas of the two triangles is equal to the area of the quadrilateral, then the point is inside the polygon
        if area_tri1 + area_tri2 == area_quad:
            return True
        else:
            return False
def rotation_angle(p0, p1):
    # compute rotation angle
    x = p1.x - p0.x
    y = p1.y - p0.y
    # print(x)
    angle = np.degrees(np.arctan2(y, x))
    if angle < 0:
        angle = 360 + angle
    angle = np.radians(angle)
    return angle

def compute_edge_length(p0, p1):
    x = abs(p1.x - p0.x)
    y = abs(p1.y - p0.y)
    length = np.sqrt(x**2 + y**2)
    return length

def map_p2(p0, p1, p2):
    """
    Given three points `p0`, `p1`, and `p2`, maps the point `p2` to a new point `mapped_p2` that is on the line passing through `p2` 
    which parellels to the line passing through `p0` and `p1`, such that `mapped_p2` is the closest point to the line `p0``p1`.
    Returns the `mapped_p2` point.

    Args:
        p0 (Point): The first point on the line.
        p1 (Point): The second point on the line.
        p2 (Point): The point to be mapped.

    Returns:
        mapped_p2 (Point): The new location of p2
    """
    def is_clockwise(p1, p2, p3):
        """
        Returns True if the three points p1, p2, and p3 are in clockwise order,
        and False otherwise.
        """
        # Compute the cross product of the vectors formed by the points
        cross_product = (p2[0] - p1[0]) * (p3[1] - p2[1]) - (p2[1] - p1[1]) * (p3[0] - p2[0])

        # Check the sign of the cross product
        if cross_product < 0:
            return True
        else:
            return False
    def line_equation(x1, y1, x2, y2):
        """
        Returns the equation of the line passing through the two points (x1, y1) and (x2, y2)
        in the form ax + by + c = 0.
        """
        if x2 == x1:
            return (1, 0, -x1)  # special case for vertical line
        m = (y2 - y1) / (x2 - x1)
        a = m
        b = -1
        c = -m * x1 + y1
        return (a, b, c)
    a, b, c = line_equation(*p0, *p1)

    # the distance of a point (m, n) to the line ax + by +c =0
    # is：|ma + nb + c| / sqrt(a^2 + b^2)
    distance = (abs(p2.x * a + p2.y * b + c)) / (np.sqrt(a ** 2 + b ** 2))
    
    # determine the orientation of p2
    p2_is_clockwise = is_clockwise(p0, p1, p2)

    # get the perpendicular vector
    if(p2_is_clockwise):
        perpendicular_vec = ((p1.y - p0.y), -(p1.x - p0.x))
    else:
        perpendicular_vec = (-(p1.y - p0.y), (p1.x - p0.x))


    # normalize it to unit vector
    magnitude = np.sqrt(perpendicular_vec[0] ** 2 + perpendicular_vec[1] ** 2)

    perpendicular_vec = (perpendicular_vec[0] / magnitude, perpendicular_vec[1] / magnitude)

    mapped_p2 = Point([int(p1.x + distance * perpendicular_vec[0]),int(p1.y + distance * perpendicular_vec[1])])

    # print(f'Point 0: {p0}, Point 1:{p1}, Point 2:{p2}')
    # print(f'equation: {a}x+{b}y+{c}=0')
    # print(f'is_clockwise: {p2_is_clockwise}')
    # print(f'distance: {distance}')
    # print(f'perpendicular_vec: {perpendicular_vec}')
    return mapped_p2

def rgb_to_grayscale(r, g, b):
    return 0.2989 * r + 0.5870 * g + 0.1140 * b 

class ImageCanvasFrame(Frame):
    KWARGS = {
        "padding": 0
    }
    def __init__(self, root, idx, folder_selected, frame_files, **kwargs):
        # Merge default kwargs with user-supplied kwargs
        self.merged_kwargs = {**self.KWARGS, **kwargs}
        super().__init__(root, **self.merged_kwargs)

        # idx indicates which ImageCanvasFrame it is.
        # 1 for the left frame, 2 for the right frame
        self.idx = idx
        self.folder_selected = folder_selected
        self.frame_files = frame_files

        self.imageCanvas = ImageCanvas(self, idx, folder_selected, frame_files)
        self.imageCanvas.pack()

        # Add a frame to hold the image navigation elements
        image_navigation_frame = Frame(self)
        image_navigation_frame.pack()

        # Add a button to switch to the previous image
        self.previous_image_button = Button(image_navigation_frame, text="Prev", width=5, command=self.switch_to_previous_image)
        self.previous_image_button.pack(side=LEFT)

        # Add a text box for specifying the image
        self.frame_number_text_box = Entry(image_navigation_frame, width=5)
        self.frame_number_text_box.pack(side=LEFT)

        # Add a label to show the maximum number of images
        self.max_images_label = Label(image_navigation_frame, text=f"/{len(frame_files)}") 
        self.max_images_label.pack(side=LEFT)

        # Add a Jump button to the image navigation frame
        self.jump_button = Button(image_navigation_frame, text="Jump", width=5, command=self.jump_to_image)
        self.jump_button.pack(side=LEFT)

        # Add a button to switch to the next image
        self.next_image_button = Button(image_navigation_frame, text="Next", width=5, command=self.switch_to_next_image)
        self.next_image_button.pack(side=LEFT)

        cell_count_frame = Frame(self)
        cell_count_frame.pack()

        cell_count_label = Label(cell_count_frame, text="Cell Count in the canvas:")
        cell_count_label.pack(side=LEFT)

        self.cell_count_text_box = Entry(cell_count_frame, width=5)
        self.cell_count_text_box.pack(side=LEFT)

        # Add a new bounding box button to the frame
        self.new_bounding_box_button = Button(self, text="New Bounding Box", command=self.new_bounding_box, width=20)
        self.new_bounding_box_button.pack()

        # Add a delete bounding box button to the frame
        self.delete_bounding_box_button = Button(self, text="Delete Bounding Box", command=self.delete_bounding_box, width=20)
        self.delete_bounding_box_button.pack()

        # Add a select bounding box button to the frame
        self.select_bounding_box_button = Button(self, text="Select Bounding Box", command=self.select_bounding_box, width=20)
        self.select_bounding_box_button.pack()

        # Add a mouse position frame to the frame
        self.mouse_position_frame = MousePositionFrame(self)
        self.mouse_position_frame.pack()

        # Add a bounding box frame to the frame
        self.bouding_box_info_frame = BoundingBoxInfoFrame(self)
        self.bouding_box_info_frame.pack()

        if(idx == 1):
            self.imageCanvas.load_image(0)
        elif(idx == 2):
            self.imageCanvas.load_image(10)

        self.imageCanvas.bind('<ButtonPress-1>', self.imageCanvas.left_press_down)
        self.imageCanvas.bind('<Motion>', self.imageCanvas.mouse_move)

    # New Bounding Box Button Callback
    def new_bounding_box(self):
        self.imageCanvas.status = ImageCanvasStatus.DRAWING
        self.new_bounding_box_button.configure(state='disable')
        self.delete_bounding_box_button.configure(state='normal')
        self.select_bounding_box_button.configure(state='normal')


    # Delete Bounding Box Button Callback
    def delete_bounding_box(self):
        self.imageCanvas.status = ImageCanvasStatus.DELETING
        self.new_bounding_box_button.configure(state='normal')
        self.delete_bounding_box_button.configure(state='disable')
        self.select_bounding_box_button.configure(state='normal')


    # Select Bounding Box Button Callback
    def select_bounding_box(self):
        self.imageCanvas.status = ImageCanvasStatus.SELECTING
        self.new_bounding_box_button.configure(state='normal')
        self.delete_bounding_box_button.configure(state='normal')
        self.select_bounding_box_button.configure(state='disable')


    # Enter pick cell color mode
    # This function is called when the pick button in the input panel is pressed
    def pick_cell_color(self):
        self.imageCanvas.status = ImageCanvasStatus.PICKING_CELL_COLOR
        self.new_bounding_box_button.configure(state='normal')
        self.delete_bounding_box_button.configure(state='normal')
        self.select_bounding_box_button.configure(state='normal')
        return True

    # Enter pick background color mode
    # This function is called when the pick button in the input panel is pressed
    def pick_background_color(self):
        self.imageCanvas.status = ImageCanvasStatus.PICKING_BACKGROUND_COLOR
        self.new_bounding_box_button.configure(state='normal')
        self.delete_bounding_box_button.configure(state='normal')
        self.select_bounding_box_button.configure(state='normal')
        return True

    # Enter Idle mode
    # This function is called after picking a color
    def idle_mode(self):
        self.imageCanvas.status = ImageCanvasStatus.IDLE
        self.new_bounding_box_button.configure(state='normal')
        self.delete_bounding_box_button.configure(state='normal')
        self.select_bounding_box_button.configure(state='normal')
    
    def switch_to_previous_image(self):
        curr_frame_number = int(self.frame_number_text_box.get())
        self.imageCanvas.load_image(curr_frame_number - 1)

    def switch_to_next_image(self):
        curr_frame_number = int(self.frame_number_text_box.get())
        self.imageCanvas.load_image(curr_frame_number + 1)
    
    def jump_to_image(self):
        self.imageCanvas.load_image(int(self.frame_number_text_box.get()))
class ImageCanvasStatus(Enum):
    IDLE = 0
    IMAGE_LOADED = 1
    DRAWING = 2
    DELETING = 3
    SELECTING = 4
    PICKING_CELL_COLOR = 5
    PICKING_BACKGROUND_COLOR = 6

class FrameData:
    def __init__(self):
        self.image = None
        self.image_tk = None
        self.image_id = None
        self.selected_id = None
        self.temp_item = None      
        self.p0 = None             
        self.p1 = None             
        self.p2 = None             
        self.p3 = None             
        self.angle = None
        self.width = None
        self.length = None
        self.center = None
        self.current_id = None
        self.cell_dict = defaultdict(dict)

class ImageCanvas(Canvas):
    KWARGS = {
        "bg": "white",
        "width": 400,
        "height": 400,
    }
    def __init__(self, root, idx, folder_selected, frame_files, **kwargs):
        # Merge default kwargs with user-supplied kwargs
        self.merged_kwargs = {**self.KWARGS, **kwargs}
        super().__init__(root, **self.merged_kwargs)
        
        self.idx = idx
        self.folder_selected = folder_selected
        self.frame_files = frame_files
        self.zoom_factor = None    # Raw Image Width / Canvas Width
        self.canvas_width = self.merged_kwargs["width"]
        self.canvas_height = self.merged_kwargs["height"]
        self.plt = platform.system()
        self.status = ImageCanvasStatus.IDLE
    
        # variables for each 
        self.frame_data = [FrameData() for _ in frame_files]
        self.curr_frame_data = None

    # Define a function to handle button clicks
    def load_image(self, frame_index):
        if (frame_index < 0):
            messagebox.showerror(
                'Error', 'Frame index cannot be smaller than 0.')
            return
        elif (frame_index > len(self.frame_files)):
            messagebox.showerror(
                'Error', f'Frame index cannot be greater than {len(self.frame_files)}.')
            return
        self.curr_frame_idx = frame_index
        self.curr_frame_data = self.frame_data[frame_index]

        if(self.curr_frame_data.image is None):
            file_path = os.path.join(self.folder_selected, self.frame_files[frame_index])
            self.curr_frame_data.image = Image.open(file_path)

            # Calculate the aspect ratio of the image and the canvas
            image_width, image_height = self.curr_frame_data.image.size
            canvas_aspect_ratio = self.canvas_width / self.canvas_height
            image_aspect_ratio = image_width / image_height

            # If the image is wider than the canvas, resize it to fit the width of the canvas
            if image_aspect_ratio > canvas_aspect_ratio:
                self.new_canvas_width = self.canvas_width
                self.new_canvas_height = int(self.new_canvas_width / image_aspect_ratio)

            # If the image is taller than the canvas, resize it to fit the height of the canvas
            else:
                self.new_canvas_height = self.canvas_height
                self.new_canvas_width = int(self.new_canvas_height * image_aspect_ratio)

            # Resize the image and display it on the canvas
            self.curr_frame_data.image_resized = self.curr_frame_data.image.resize((self.new_canvas_width, self.new_canvas_height))
            self.config(width=self.new_canvas_width, height=self.new_canvas_height)

            self.curr_frame_data.image_tk = ImageTk.PhotoImage(self.curr_frame_data.image_resized)
            self.curr_frame_data.image_id = self.create_image(0, 0, anchor="nw", image=self.curr_frame_data.image_tk)

            self.zoom_factor = image_width / self.canvas_width
        else:
            # hide all objects on current canvas
            for item in self.find_all():
                self.itemconfig(item, state='hidden')
            
            # show objects in the current frame data
            self.itemconfig(self.curr_frame_data.image_id, state="normal")
            for cell in self.curr_frame_data.cell_dict.keys():
                self.itemconfig(cell, state="normal")

        self.master.frame_number_text_box.delete(0, 'end')
        self.master.frame_number_text_box.insert(0, frame_index)
        

        
    ####################################################
    #      Callback functions for canvas
    ####################################################
    def calculate_vertices2(self, p0, p1, p2):
        self.curr_frame_data.angle = rotation_angle(p0, p1)
        self.curr_frame_data.p2 = map_p2(p0, p1, p2)
        p2 = self.curr_frame_data.p2
        self.curr_frame_data.width = compute_edge_length(p1, p2)
        self.curr_frame_data.length = compute_edge_length(p0, p1)
        self.curr_frame_data.center = ((p0.x + p2.x) / 2, (p0.y + p2.y) / 2)
        self.curr_frame_data.p3 = Point([(p0.x + p2.x - p1.x), (p0.y + p2.y - p1.y)])

    def left_press_down(self, event):
        if self.curr_frame_data.temp_item is not None:
            self.delete(self.curr_frame_data.temp_item)

        if self.status == ImageCanvasStatus.DRAWING:
            self.curr_frame_data.p0 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            self.bind('<B1-Motion>', self.left_motion)
        
        elif self.status == ImageCanvasStatus.SELECTING:
            mx = self.canvasx(event.x)
            my = self.canvasy(event.y)
            # get canvas object ID of where mouse pointer is
            canvasobject = self.find_closest(mx, my, halo=5)

            if canvasobject == () or self.curr_frame_data.image_id == canvasobject[0]:
                return
            if(self.curr_frame_data.selected_id == None):
                self.curr_frame_data.selected_id = canvasobject[0]
                self.update_cell_label(self.curr_frame_data.selected_id)
                self.itemconfigure(self.curr_frame_data.selected_id, outline='red')
            elif self.curr_frame_data.selected_id == canvasobject[0]:
                self.itemconfigure(self.curr_frame_data.selected_id, outline='green')
                self.curr_frame_data.selected_id = None
                self.clear_cell_label()
            else:
                self.itemconfigure(self.curr_frame_data.selected_id, outline='green')
                self.curr_frame_data.selected_id = canvasobject[0]
                self.update_cell_label(self.curr_frame_data.selected_id)
                self.itemconfigure(self.curr_frame_data.selected_id, outline='red')
                
            
        elif self.status == ImageCanvasStatus.DELETING:
            mx = self.canvasx(event.x)
            my = self.canvasy(event.y)
            # get canvas object ID of where mouse pointer is
            canvasobject = self.find_closest(mx, my, halo=5)

            # print(canvasobject)
            # self.delete(canvasobject)

            if canvasobject == () or self.curr_frame_data.image_id == canvasobject[0]:
                return
            
            # first change the selected bounding box
            if(self.curr_frame_data.selected_id == None):
                self.curr_frame_data.selected_id = canvasobject[0]
                self.update_cell_label(self.curr_frame_data.selected_id)
                self.itemconfigure(self.curr_frame_data.selected_id, outline='red')
            elif self.curr_frame_data.selected_id == canvasobject[0]:
                # if the box to be deleted is the same, don't deselect it.
                pass
            else:
                self.itemconfigure(self.curr_frame_data.selected_id, outline='green')
                self.curr_frame_data.selected_id = canvasobject[0]
                self.update_cell_label(self.curr_frame_data.selected_id)
                self.itemconfigure(self.curr_frame_data.selected_id, outline='red')

            delete = messagebox.askokcancel('Warning', 'Delete this bounding box?')
            if delete is True:
                self.delete(canvasobject[0])
                del self.curr_frame_data.cell_dict[canvasobject[0]]
                self.curr_frame_data.selected_id = None
                self.clear_cell_label()
                #print("delete: {}".format(canvasobject[0]))
                # print(self.cell_dict)
        elif self.status == ImageCanvasStatus.PICKING_CELL_COLOR or self.status == ImageCanvasStatus.PICKING_BACKGROUND_COLOR:
            self.curr_frame_data.p0 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            self.bind('<B1-Motion>', self.left_motion)

    def left_motion(self, event):
        if self.status == ImageCanvasStatus.DRAWING:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)
            self.curr_frame_data.p1 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            self.curr_frame_data.temp_item = self.create_line(
                *self.curr_frame_data.p0, *self.curr_frame_data.p1, fill='red', width=3)
            self.bind('<ButtonRelease-1>', self.stop_left_move)
        elif self.status == ImageCanvasStatus.PICKING_CELL_COLOR or self.status == ImageCanvasStatus.PICKING_BACKGROUND_COLOR:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)
            self.curr_frame_data.p1 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            self.curr_frame_data.temp_item = self.create_rectangle(
                *self.curr_frame_data.p0, *self.curr_frame_data.p1, outline='red', width=3)
            self.bind('<ButtonRelease-1>', self.stop_left_move)
    def stop_left_move(self, event):
        if self.status == ImageCanvasStatus.DRAWING:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)

            self.curr_frame_data.p1 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])

            # print(self.p0)
            # print(self.p1)

            self.curr_frame_data.temp_item = self.create_line(
                *self.curr_frame_data.p0, *self.curr_frame_data.p1, fill='red', width=3)
            if self.plt == "Darwin":
                # 2 for MacOS Right-Click, 3 for Windows
                self.bind('<ButtonPress-2>', self.start_right_move)
            else:
                self.bind('<ButtonPress-3>', self.start_right_move)
        elif self.status == ImageCanvasStatus.PICKING_CELL_COLOR or self.status == ImageCanvasStatus.PICKING_BACKGROUND_COLOR:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)
            self.curr_frame_data.p1 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            self.curr_frame_data.temp_item = self.create_rectangle(
                *self.curr_frame_data.p0, *self.curr_frame_data.p1, outline='red', width=3)
            self.delete(self.curr_frame_data.temp_item)

            # calculate the raw coordinates
            raw_p0 = self.curr_frame_data.p0 * self.zoom_factor
            raw_p1 = self.curr_frame_data.p1 * self.zoom_factor

            # get the pixel colors from the raw image
            pixel_colors = []
            for x in range(int(raw_p0.x), int(raw_p1.x)):
                for y in range(int(raw_p0.y), int(raw_p1.y)):
                    pixel_colors.append(self.curr_frame_data.image.getpixel((x, y)))
            avg_color = tuple(np.mean(pixel_colors, axis=0, dtype=np.uint32))
            gray_scale_color = rgb_to_grayscale(*avg_color) / 255

            if(self.status == ImageCanvasStatus.PICKING_BACKGROUND_COLOR):
                background_color_entry = self.master.master.input_panel.background_color
                background_color_entry.delete(0, END)
                background_color_entry.insert(0, f'{gray_scale_color:.3f}')

                color_info_panel = self.master.master.informationPanel.colorInfoPanel
                color_info_panel.set_background_color(gray_scale_color)
            elif(self.status == ImageCanvasStatus.PICKING_CELL_COLOR):
                cell_color_entry = self.master.master.input_panel.cell_color
                cell_color_entry.delete(0, END)
                cell_color_entry.insert(0, f'{gray_scale_color:.3f}')

                color_info_panel = self.master.master.informationPanel.colorInfoPanel
                color_info_panel.set_cell_color(gray_scale_color)
            
            self.master.idle_mode()
            self.reset_var()
    def start_right_move(self, event):
        if self.status == ImageCanvasStatus.DRAWING:
            self.curr_frame_data.p2 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])
            if self.plt == "Darwin":
                self.bind('<B2-Motion>', self.right_motion)
            else:
                self.bind('<B3-Motion>', self.right_motion)
    
    def right_motion(self, event):
        if self.status == ImageCanvasStatus.DRAWING:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)

            self.curr_frame_data.p2 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])

            self.calculate_vertices2(self.curr_frame_data.p0, self.curr_frame_data.p1, self.curr_frame_data.p2)

            self.curr_frame_data.temp_item = self.create_polygon(self.curr_frame_data.p0[0], self.curr_frame_data.p0[1],
                                                        self.curr_frame_data.p1[0], self.curr_frame_data.p1[1],
                                                        self.curr_frame_data.p2[0], self.curr_frame_data.p2[1],
                                                        self.curr_frame_data.p3[0], self.curr_frame_data.p3[1],
                                                        fill='', outline='red', width=3)
            if self.plt == "Darwin":
                self.bind('<ButtonRelease-2>', self.stop_right_move)
            else:
                self.bind('<ButtonRelease-3>', self.stop_right_move)

    def stop_right_move(self, event):
        if self.status == ImageCanvasStatus.DRAWING:
            if self.curr_frame_data.temp_item is not None:
                self.delete(self.curr_frame_data.temp_item)

            self.curr_frame_data.p2 = Point([self.canvasx(event.x),
                            self.canvasy(event.y)])

            # print(self.p0)

            self.calculate_vertices2(self.curr_frame_data.p0, self.curr_frame_data.p1, self.curr_frame_data.p2)
            self.curr_frame_data.current_id = self.create_polygon(self.curr_frame_data.p0[0], self.curr_frame_data.p0[1],
                                                        self.curr_frame_data.p1[0], self.curr_frame_data.p1[1],
                                                        self.curr_frame_data.p2[0], self.curr_frame_data.p2[1],
                                                        self.curr_frame_data.p3[0], self.curr_frame_data.p3[1],
                                                        fill='', outline='red', width=3)
            # print(self.current_id)

            # check the center inside the image
            if self.curr_frame_data.center[0] > self.new_canvas_width or self.curr_frame_data.center[0] < 0 or \
                    self.curr_frame_data.center[1] > self.new_canvas_height or self.curr_frame_data.center[1] < 0:
                messagebox.showerror(
                'Error', 'The center of the bounding box is outside of the image! Please draw again.')
                self.delete(self.curr_frame_data.current_id)
            else:
                # print("add:{}".format(self.current_id))
                # save to cell_dict
                self.save_cell(self.curr_frame_data.current_id, self.curr_frame_data.center, self.curr_frame_data.width, self.curr_frame_data.length, self.curr_frame_data.angle)
                self.update_cell_label(self.curr_frame_data.current_id)
                self.itemconfigure(self.curr_frame_data.current_id, outline='green')
            self.reset_var()
    
    def mouse_move(self, event):
        mx, my = self.canvasx(event.x), self.canvasy(event.y)
        self.master.mouse_position_frame.set_position(mx * self.zoom_factor, my * self.zoom_factor)
    
    def save_cell(self, id, center, width, length, angle):
        self.curr_frame_data.cell_dict[id]["center"] = np.array(center) * self.zoom_factor
        self.curr_frame_data.cell_dict[id]["width"] = round(width * self.zoom_factor, 0)
        self.curr_frame_data.cell_dict[id]["length"] = round(length * self.zoom_factor, 0)
        self.curr_frame_data.cell_dict[id]["rotation"] = round(angle, 2)

    def reset_var(self):
        self.curr_frame_data.temp_item = None
        self.curr_frame_data.angle = None
        self.curr_frame_data.width = None
        self.curr_frame_data.length = None
        self.curr_frame_data.center = None
        # p0 is the cursor location when LB is pressed
        # p1 is the cursor location when LB is stopped/released
        # p2 is the cursor location when RB is pressed
        # p3 is calculated according to previous three points
        self.curr_frame_data.p0 = None
        self.curr_frame_data.p1 = None
        self.curr_frame_data.p2 = None
        self.curr_frame_data.p3 = None
        self.curr_frame_data.current_id = None
    def clear_cell_label(self):
        self.master.bouding_box_info_frame.clear_bounding_box_info()

    def update_cell_label(self, current_id):
        if current_id in self.curr_frame_data.cell_dict.keys():
            self.master.bouding_box_info_frame.set_bounding_box_info(self.curr_frame_data.cell_dict[current_id])
            
class MousePositionFrame(Frame):
    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)
        self.title = Label(self, text='Raw Image Coordinate')
        self.title.pack()
        self.coor = Label(self, text='(, )')
        self.coor.pack()
    def set_position(self, x, y):
        self.coor.config(text=f'({x:.2f}, {y:.2f})')

class BoundingBoxInfoFrame(Frame):
    def __init__(self, root, **kwargs):
        super().__init__(root, **kwargs)
        self.cell_label = Label(self, text="Current bounding box: ", relief='flat')
        self.cell_label.grid(row=4, column=0, sticky=W, padx=10, pady=5)
        self.center_label = Label(self, text="center: ", relief='flat')
        self.center_label.grid(row=5, column=0, sticky=W, padx=10, pady=5)
        self.width_label = Label(self, text="width: ", relief='flat')
        self.width_label.grid(row=6, column=0, sticky=W, padx=10, pady=5)
        self.length_label = Label(self, text="length: ", relief='flat')
        self.length_label.grid(row=7, column=0, sticky=W, padx=10, pady=5)
        self.rotation_label = Label(self, text="rotation: ", relief='flat')
        self.rotation_label.grid(row=8, column=0, sticky=W, padx=10, pady=5)

    def set_bounding_box_info(self, info):
        self.center_label.config(text=f'center: ({info["center"][0]:.2f}, {info["center"][1]:.2f})')
        self.width_label.config(text=f'width: ({info["width"]:.2f})')
        self.length_label.config(text=f'length: ({info["length"]:.2f})')
        self.rotation_label.config(text=f'roation: ({info["rotation"]:.2f})')
    
    def clear_bounding_box_info(self):
        self.center_label.config(text='center: ')
        self.width_label.config(text='width: ')
        self.length_label.config(text='length: ')
        self.rotation_label.config(text='roation: ')
