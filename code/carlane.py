import os
import json
import numpy as np
from PIL import Image, ImageDraw


from mrcnn import utils
from mrcnn.config import Config


############################################################
#  Configurations
############################################################


class CarlaneConfig(Config):
    """Configuration for training on the toy  dataset.
    Derives from the base Config class and overrides some values.
    """
    # Give the configuration a recognizable name
    NAME = "carlane"
    
    BACKBONE = "resnet50"

    # We use a GPU with 12GB memory, which can fit two images.
    # Adjust down if you use a smaller GPU.
    IMAGES_PER_GPU = 2
    
    # NUMBER OF GPUS to use
    GPU_COUNT = 2

    # Number of classes (including background)
    NUM_CLASSES = 1 + 21  # Background + 21 carlane classes

    # Number of training steps per epoch
    STEPS_PER_EPOCH = 400

    # Minimum probability value to accept a detected instance
    # ROIs below this threshold are skipped    
    DETECTION_MIN_CONFIDENCE = 0.7
    
    # Non-maximum suppression threshold for detection
    DETECTION_NMS_THRESHOLD = 0.3
    
    # Image mean(RGB)
    MEAB_PIXEL = np.array([115.5, 115.9, 116.2])


############################################################
#  Dataset
############################################################

class CarlaneDataset(utils.Dataset):


    def load_carlane(self, dataset_dir, subset):
        """Load a subset of the Carlane dataset
        dataset_dir: Root directory of the dataset
        subset: Subset to load: train or val

        """ 
        assert subset in ["train", "val"]
        
        # train_val.json:{
        #    "train": xx,
        #    "val":xx,
        #    "classes":xx
        #    }
        # train, val: [image_name,...]
        # classes: [(class_name, class_id),...]
       
        data = json.load(
            open(os.path.join(dataset_dir, 'train_val.json'), 'r'))

        classes = data['classes']
        for c in classes:
            self.add_class("carlane", c[1], c[0])

        self.class_map = {}
        for c in classes:
            self.class_map[c[0]] = c[1]

        image_names = data[subset]

        # Add images and Load annotaions
        for image_name in image_names:
            json_path = os.path.join(dataset_dir, image_name + '.json')
            annotation = json.load(open(json_path))
            annotation = annotation['datalist']
            polygons = [a['arr'] for a in annotation]
            polygons = [[(xy['x'], xy['y']) for xy in p] for p in polygons]
            polygon_types = [a['type'] for a in annotation]

            image_path = os.path.join(dataset_dir, image_name + '.jpg')
            image = Image.open(image_path)
            width, height = image.size

            self.add_image(
                "carlane",
                image_id=image_name,
                path=image_path,
                width=width,
                height=height,
                polygons=polygons,
                polygon_types=polygon_types)

    def load_mask(self, image_id):
        """Generate instance masks for an image
        
        Returns:
         masks:  A bool array of shape [height, width, instance count] with
             one mask per instance
         polygon_ids: a 1d array of class IDs of the instance masks
        """
                
        # Convert polygons to a bitmap mask of shape
        # [height, width, insstance_count]
        info = self.image_info[image_id]
        polygons = info["polygons"]
        polygon_types = info["polygon_types"]
        mask = np.zeros([info["height"], info["width"], len(polygons)], dtype=np.uint8)
        for i, polygon in enumerate(polygons):
            m = Image.new('L', (info["width"], info["height"]), color=0)
            draw = ImageDraw.Draw(m)
            draw.polygon(polygon, fill=1, outline=1)
            mask[:, :, i] = np.array(m)
        polygon_ids = np.array([self.class_map[t] for t in polygon_types])
        return mask.astype(np.bool), polygon_ids.astype(np.int32)

    def image_reference(self, image_id):
        """Return the path of the image"""
        info = self.image_info[image_id]
        if info["source"] == "carlane":
            return info["path"]
        else:
            super(self.__class__, self).image_reference(image_id)