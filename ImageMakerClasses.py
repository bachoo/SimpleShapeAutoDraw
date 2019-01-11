import numpy as np
from xml.etree import ElementTree as et
import sys
import os
import config
import copy
import pandas as pd

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
        # add this one separately to do backgrounds
        self.bg_rect_maker = RectMakerCorners()
        # puts patterns n the form to be added as strings
        self.patterns = [('url(#' + p.attrib['id'] + ')') for p in self.pattern_root.find('{'
                                                                      'http://www.w3.org/2000/svg}defs').getchildren()]

    def make_1shape_image_set(self, N, save_location, start_n = 1, image_name_root='image_',
                              mask_name_root='mask_', data_file_name='image_data_file.csv',
                              pattern_save_name = 'original_pattern.svg'):
        """make N single shape images and store them at a specfied location"""
        """CAVEAT: currently all allowed shapes have to return the same number of parameters when generating a random 
        parameter set."""
        num_digits = (np.floor(np.log10(N+start_n))).astype(int)
        digit_string = '%0{:d}d'.format(num_digits) # string that will be used to add the numbers to the filename
        image_name_pattern = os.path.join(save_location, image_name_root + digit_string)
        if mask_name_root is not None:
            mask_name_pattern = os.path.join(save_location, mask_name_root + digit_string)
        else:
            mask_name_pattern = None

        image_properties = self.random_1shape_config()
        column_names = list(image_properties.keys())
        data_array = pd.DataFrame(data=np.zeros((N,len(column_names))),columns=column_names)

        for imagei in range(N):
            image_name = image_name_pattern % (imagei+start_n)
            if mask_name_root is not None:
                mask_name = mask_name_pattern % (imagei+start_n)
            else:
                mask_name = None
            image_properties = self.make_1shape_image(image_file_root=image_name,mask_file_root=mask_name)
            #write to data array
            data_array.iloc[imagei,:] = [image_properties[k] for k in column_names]

        if data_file_name is not None:
            data_array.to_csv(os.path.join(save_location,data_file_name),index=False)
            # leave out index. Find having the index leads to confusion
        if pattern_save_name is not None:
            self.pattern_tree.write(os.path.join(save_location,pattern_save_name))



    def make_1shape_image(self, image_file_root, mask_file_root=None, **kwargs):
        """Makes an image at the save location in which a patterned shape is added to a patterned location"""
        image_properties = self.random_1shape_config()
        # replace any random kwargs with given arguments
        for k,x in kwargs:
            image_properties[k] = x

        obj_shape = self.shapes[image_properties['obj_shape_index']]
        obj_pattern = self.patterns[image_properties['obj_pattern_index']]
        bg_pattern = self.patterns[image_properties['bg_pattern_index']]

        def make_1_shape_image_sub(bg_fill, obj_fill,file_name):
            new_tree = copy.deepcopy(self.pattern_tree)
            root = new_tree.getroot()
            layer1 = next(element for element in root.getchildren()
                          if (element.tag == '{http://www.w3.org/2000/svg}g' and element.attrib['id'] == 'layer1'))
            layer2 = next(element for element in root.getchildren()
                          if (element.tag == '{http://www.w3.org/2000/svg}g' and element.attrib['id'] == 'layer2'))
            # add background
            self.bg_rect_maker.add_shape(layer2, x0=0,y0=0,
                                         width=config.bg_size[0],height=config.bg_size[1],
                                         fill='white')
            self.bg_rect_maker.add_shape(layer2, x0=0, y0=0,
                                         width=config.bg_size[0], height=config.bg_size[1],
                                         fill=bg_fill)
            # add background
            obj_shape.add_shape(layer1, fill= 'white',
                                             **{k:v for k,v in image_properties.items() if k not in
                                                ['obj_shape_index','obj_pattern_index','bg_pattern_index']}
                                             ) # logic of above is that all properties other than these in the config
                                             # are for the shape.
            obj_shape.add_shape(layer1, fill= obj_fill,
                                             **{k:v for k,v in image_properties.items() if k not in
                                                ['obj_shape_index','obj_pattern_index','bg_pattern_index']}
                                             )
            svg_loc = file_name + '.svg'
            png_loc = file_name + '.png'
            new_tree.write(svg_loc)
            # this exports the drawing, so if we want it to be a consistent square we have to keep everything inside
            # the background rectangle. Experimented with exporting the background object specifically but the coordinates
            # for export are not those given in creating the image. If desirable best to get the coordinates by picking
            # out the background rectangle and requesting coordinates as:
            #        x = os.system("inkscape -z %s -I object_id -X "%(svg_loc))
            # etc.
            os.system("%s -z %s -w %d -h %d -D -e %s"%(self.inkscape_command,svg_loc,
                                                       config.im_size[0],config.im_size[1],png_loc))
        make_1_shape_image_sub(bg_pattern, obj_pattern, image_file_root)
        if mask_file_root is not None:
            make_1_shape_image_sub('black', 'white', mask_file_root)
        return image_properties

    def random_1shape_config(self):
        """randomly generate everything needed for making a 1 shape image"""
        """NOTE: when changing this method the fields in the returned dictionary should match those parameters 
        passed to make_1_shape_image method"""
        image_config = {}
        shape_index = self.random_obj_shape()
        image_config['obj_shape_index'] = shape_index
        image_config['obj_pattern_index'] = self.random_pattern()
        image_config['bg_pattern_index'] = self.random_pattern()

        obj_props = self.shapes[shape_index].random_props()
        for k,v in obj_props.items():
            image_config[k] = v

        return image_config

    def random_pattern(self):
        """Returns a random pattern index from those available"""
        return np.random.randint(len(self.patterns))

    def random_obj_shape(self):
        """Returns a random shape index from those available"""
        return np.random.randint(len(self.shapes))


class ShapeMaker(object):
    """A parent class to make shapes shapes to an svg element (like a layer)"""
    def __init__(self):
        # style string shared by a number of shapes but generally gets replaced
        self.style_string = 'opacity:1;fill:{:s};fill-opacity:1;stroke:none;stroke-width:3.11315393' \
                            ';stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;' \
                            'stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'

    def add_shape(self, parent_element, cx, cy, size, fill, shape_id=None):
        pass

    def random_props(self):
        """get a set of random properties for an object (except for fill). Ranges taken from config."""
        random_props = dict()
        random_props['shape_id'] = np.random.randint(1000,9999)
        random_props['cx'] = rand_range(None,config.obj_centre_lims[0],config.obj_centre_lims[2])
        random_props['cy'] = rand_range(None, config.obj_centre_lims[1], config.obj_centre_lims[3])
        random_props['size'] = rand_range(None,config.obj_size[0],config.obj_size[1])
        return random_props


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

class RectMakerCorners(object):
    """like rect maker but you provide the corners x0,yo,x1,y1 instead"""
    def __init__(self):
        super().__init__()
        self.style_string = 'opacity:1;fill:{:s};fill-opacity:1;stroke:none;stroke-width:3.11315393' \
                            ';stroke-linecap:round;stroke-linejoin:round;stroke-miterlimit:4;' \
                            'stroke-dasharray:none;stroke-dashoffset:0;stroke-opacity:1'

    def add_shape(self, parent_element, x0, y0,width,height, fill, shape_id=None):
        if shape_id == None:
            shape_id = np.random.randint(1000, 9999)

        shape_properties = {'x': str(x0),
                            'y': str(y0),
                            'width': str(width),
                            'height': str(height),
                            'id': 'rect{:d}'.format(shape_id).zfill(4),
                            'style': self.style_string.format(str(fill))}
        rect = et.SubElement(parent_element, "ns0:rect", **shape_properties)

def rand_range(shape,low=0,high=1):
    """convenience function for getting a set of random numbers in a range"""
    return np.random.random(shape)*(high-low) + low

if __name__ == "__main__":
    # tests written for my computer but you see how they work

    # make image maker
    image_maker_1 = ImageMaker()

    #make image pair
    image_maker_1.make_1shape_image(image_file_root='test_images/image_1',
                                    mask_file_root='test_images/mask_1')

    #make set of 100 images
    image_maker_1.make_1shape_image_set(10,'test_image_set')
