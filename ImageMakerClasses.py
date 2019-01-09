import numpy as np
from xml.etree import ElementTree as et
import sys
import os
import config
import copy

class ImageMaker(object):
    """A class to make pngs with particular shapes that have different fills. This is primarily to generate
    random images with different patterns on the different shapes"""
    def __init__(self,pattern_path = './pattern_definitions.svg',inkscape_command='inkscape',allowed_shapes=None):
        self._pattern_path = pattern_path
        self.pattern_tree = et.parse(pattern_path)
        self.inkscape_command = inkscape_command
        self.pattern_root = self.pattern_tree.getroot()
        if allowed_shapes is None:
            allowed_shapes = [RectMaker(),EllipseMaker()]
        self.shapes = allowed_shapes
        self.rect_maker = RectMaker() # add this one separately to do backgrounds
        # puts patterns n the form to be added as strings
        self.patterns = {pi:('url(#' + p.attrib['id'] + ')') for pi,p in enumerate(self.pattern_root.find('{'
                                                                      'http://www.w3.org/2000/svg}defs').getchildren())}
    def make_1shape_image(self,save_location,include_mask=True):
        """Makes an image at the save location in which a patterned shape is added to a patterned location"""
        new_tree = copy.deepcopy(self.pattern_tree)
        root = new_tree.getroot()
        layer1 = next(element for element in root.getchildren()
                      if (element.tag == '{http://www.w3.org/2000/svg}g' and element.attrib['id'] == 'layer1'))
        layer2 = next(element for element in root.getchildren()
                      if (element.tag == '{http://www.w3.org/2000/svg}g' and element.attrib['id'] == 'layer2'))
        self.rect_maker.add_shape(layer2, 100, 100, 200, 'white')  # add background
        self.rect_maker.add_shape(layer2,100,100,200,self.patterns[1])
        self.shapes[0].add_shape(layer1, 50, 50, 40, 'white') # add background
        self.shapes[0].add_shape(layer1,50,50,40,self.patterns[3])
        svg_loc = os.path.join(save_location,'image_1.svg')
        png_loc = os.path.join(save_location, 'image_1.png')
        new_tree.write(svg_loc)
        # this exports the drawing, so if we want it to be a consistent square we have to keep everything inside
        # the background rectangle. Experimented with exporting the background object specifically but the coordinates
        # for export are not those given in creating the image. If desirable best to get the coordinates by picking
        # out the background rectangle and requesting coordinates as:
        #        x = os.system("inkscape -z %s -I object_id -X "%(svg_loc))
        # etc.

        os.system("inkscape -z %s -w 100 -h 100 -D -e %s"%(svg_loc,png_loc))


class ShapeMaker(object):
    """A parent class to make shapes shapes to an svg element (like a layer)"""
    def __init__(self):
        # style string shared by a number of shapes but generally gets replaced
        self.style_string = 'opacity:1;fill:{:s};fill-opacity:1;stroke:none;stroke-width:3.11315393' \
                            ';stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;' \
                            'stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'

    def add_shape(self, parent_element, cx, cy, size, fill, shape_id=None):
        pass


class EllipseMaker(ShapeMaker):
    def __init__(self, length_ratio=1):
        super().__init__()
        self.ratio=length_ratio
        self.style_string = 'opacity:1;fill:{:s};fill-opacity:1;stroke:none;stroke-width:3.11315393' \
                            ';stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;' \
                            'stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'

    def add_shape(self, parent_element, cx, cy, size, fill, shape_id=None):
        if shape_id==None:
            shape_id = np.random.randint(1000,9999)
        shape_properties = {'cx':str(cx),
                      'cy':str(cy),
                      'rx':str(size*self.ratio),
                      'ry':str(size),
                      'id':'path{:d}'.format(shape_id).zfill(4),
                      'style':self.style_string.format(str(fill))}
        circle = et.SubElement(parent_element, "ns0:ellipse", **shape_properties)
        return circle


class RectMaker(ShapeMaker):
    def __init__(self, length_ratio=1):
        super().__init__()
        self.ratio = length_ratio
        self.style_string = 'opacity:1;fill:{:s};fill-opacity:1;stroke:none;stroke-width:3.11315393' \
                            ';stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;' \
                            'stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'

    def add_shape(self, parent_element, cx, cy, size, fill, shape_id=None):
        if shape_id == None:
            shape_id = np.random.randint(1000, 9999)
        width = size*self.ratio
        height = size
        shape_properties = {'x': str(cx - width/2),
                            'y': str(cy - height/2),
                            'width': str(width),
                            'height': str(height),
                            'id': 'rect{:d}'.format(shape_id).zfill(4),
                            'style': self.style_string.format(str(fill))}
        rect = et.SubElement(parent_element, "ns0:rect", **shape_properties)
        return rect


if __name__ == "__main__":
    image_maker_1 = ImageMaker()
    image_maker_1.make_1shape_image('test_images')
