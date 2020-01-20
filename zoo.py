import os
import wget
import struct
import shutil
import logging

import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, UpSampling2D, concatenate
from tensorflow.keras.models import Model

from blocks import ConvBlock, BoundingBox, SightLoader

# disabling warnings and logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
tf.autograph.set_verbosity(tf.compat.v1.logging.ERROR)
logging.disable(logging.WARNING)

class YOLO9000Client(object):
	def __init__(self, nms_threshold=0.45, obj_threshold=0.5, net_h=416, net_w=416, anchors=[[116, 90, 156, 198, 373, 326], [30, 61, 62, 45, 59, 119], [10, 13, 16, 30, 33, 23]]):
		self.nms_threshold = nms_threshold
		self.obj_threshold = obj_threshold
		self.net_h, self.net_w = net_h, net_w
		self.anchors = anchors
		self.yolo_model = None
		self.all_labels = ["person", "bicycle", "car", "motorbike", "aeroplane", "bus", "train", "truck",
						"boat", "traffic light", "fire hydrant", "stop sign", "parking meter", "bench",
						"bird", "cat", "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
						"backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
						"sports ball", "kite", "baseball bat", "baseball glove", "skateboard", "surfboard",
						"tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
						"apple", "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake",
						"chair", "sofa", "pottedplant", "bed", "diningtable", "toilet", "tvmonitor", "laptop", "mouse",
						"remote", "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator",
						"book", "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"]

	def download_weights(self):
		"""
		Downloads the weights and checkpoints from 
		online and saves them locally
		"""

		if os.path.exists("./bin/yolov3.weights") and os.path.exists("./bin/yolov3.cfg"):
			print ("Weights and model config already exist. Proceeding to load YOLO9000Client...")
		else:
			print ("Downloading weights and model config. This may may take a moment...")
			weights_url = "https://pjreddie.com/media/files/yolov3.weights"
			config_url = "https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg"
	
			wget.download(weights_url, os.getcwd() + "/yolov3.weights")
			wget.download(config_url, os.getcwd() + "/yolov3.cfg")

			os.mkdir("./bin", 0o755) # configuring admin rights
			shutil.move("./yolov3.weights", "./bin/yolov3.weights")
			shutil.move("./yolov3.cfg", "./bin/yolov3.cfg")

			print ("\n\nWeights and config file downloaded successfully!")	

	def load_architecture(self):
		"""
		Returns tf.keras.models.Model instance
		"""
		inp_image = Input(shape=[None, None, 3])

		x = ConvBlock.get_conv_block(inp_image, [{'filter': 32, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 0},
										{'filter': 64, 'kernel': 3, 'stride': 2, 'bnorm': True, 'leaky': True, 'layer_idx': 1},
										{'filter': 32, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 2},
										{'filter': 64, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 3}])

		x = ConvBlock.get_conv_block(x, [{'filter': 128, 'kernel': 3, 'stride': 2, 'bnorm': True, 'leaky': True, 'layer_idx': 5},
							{'filter':  64, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 6},
							{'filter': 128, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 7}])

		x = ConvBlock.get_conv_block(x, [{'filter':  64, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 9},
							{'filter': 128, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 10}])

		x = ConvBlock.get_conv_block(x, [{'filter': 256, 'kernel': 3, 'stride': 2, 'bnorm': True, 'leaky': True, 'layer_idx': 12},
							{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 13},
							{'filter': 256, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 14}])

		for i in range(7):
			x = ConvBlock.get_conv_block(x, [{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 16+i*3},
								{'filter': 256, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 17+i*3}])
			
		skip_36 = x
			
		x = ConvBlock.get_conv_block(x, [{'filter': 512, 'kernel': 3, 'stride': 2, 'bnorm': True, 'leaky': True, 'layer_idx': 37},
							{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 38},
							{'filter': 512, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 39}])

		for i in range(7):
			x = ConvBlock.get_conv_block(x, [{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 41+i*3},
								{'filter': 512, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 42+i*3}])
			
		skip_61 = x
			
		x = ConvBlock.get_conv_block(x, [{'filter': 1024, 'kernel': 3, 'stride': 2, 'bnorm': True, 'leaky': True, 'layer_idx': 62},
							{'filter':  512, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 63},
							{'filter': 1024, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 64}])

		for i in range(3):
			x = ConvBlock.get_conv_block(x, [{'filter':  512, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 66+i*3},
								{'filter': 1024, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 67+i*3}])
			
		x = ConvBlock.get_conv_block(x, [{'filter':  512, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 75},
							{'filter': 1024, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 76},
							{'filter':  512, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 77},
							{'filter': 1024, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 78},
							{'filter':  512, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 79}], skip=False)

		yolo_82 = ConvBlock.get_conv_block(x, [{'filter': 1024, 'kernel': 3, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 80},
									{'filter':  255, 'kernel': 1, 'stride': 1, 'bnorm': False, 'leaky': False, 'layer_idx': 81}], skip=False)

		x = ConvBlock.get_conv_block(x, [{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 84}], skip=False)
		x = UpSampling2D(2)(x)
		x = concatenate([x, skip_61])

		x = ConvBlock.get_conv_block(x, [{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 87},
							{'filter': 512, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 88},
							{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 89},
							{'filter': 512, 'kernel': 3, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 90},
							{'filter': 256, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True, 'layer_idx': 91}], skip=False)

		yolo_94 = ConvBlock.get_conv_block(x, [{'filter': 512, 'kernel': 3, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 92},
									{'filter': 255, 'kernel': 1, 'stride': 1, 'bnorm': False, 'leaky': False, 'layer_idx': 93}], skip=False)

		x = ConvBlock.get_conv_block(x, [{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True, 'leaky': True,   'layer_idx': 96}], skip=False)
		x = UpSampling2D(2)(x)
		x = concatenate([x, skip_36])

		yolo_106 = ConvBlock.get_conv_block(x, [{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 99},
									{'filter': 256, 'kernel': 3, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 100},
									{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 101},
									{'filter': 256, 'kernel': 3, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 102},
									{'filter': 128, 'kernel': 1, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 103},
									{'filter': 256, 'kernel': 3, 'stride': 1, 'bnorm': True,  'leaky': True,  'layer_idx': 104},
									{'filter': 255, 'kernel': 1, 'stride': 1, 'bnorm': False, 'leaky': False, 'layer_idx': 105}], skip=False)

		model = Model(inp_image, [yolo_82, yolo_94, yolo_106])    
		return model

	def sigmoid(self, z):
		return 1 / (1 + np.exp(-z))

	def preprocess(self, image):
		"""
		Resizes image to appropriate dimensions
		"""
		new_h, new_w, _ = image.shape

		if (float(self.net_w)/new_w) < (float(self.net_h)/new_h):
			new_h = (new_h * self.net_w)//new_w
			new_w = self.net_w
		else:
			new_w = (new_w * self.net_h)//new_h
			new_h = self.net_h        

		resized = cv2.resize(image[:, :, ::-1]/255., (int(new_w), int(new_h)))

		new_image = np.ones((self.net_h, self.net_w, 3)) * 0.5
		new_image[int((self.net_h-new_h)//2):int((self.net_h+new_h)//2), int((self.net_w-new_w)//2):int((self.net_w+new_w)//2), :] = resized
		new_image = np.expand_dims(new_image, 0)

		return new_image

	def interval_overlap(self, int_a, int_b):
		x1, x2 = int_a
		x3, x4 = int_b

		if x3 < x1:
			if x4 < x1:
				return 0
			else:
				return min(x2, x4) - x1
		else:
			if x2 < x3:
				return 0
			else:
				return min(x2, x4) - x3	

	def bbox_iou(self, box1, box2):
		"""
		Finds IOU between `n` bounding boxes before non maximum suppression
		"""
		int_w = self.interval_overlap([box1.xmin, box1.xmax], [box2.xmin, box2.xmax])
		int_h = self.interval_overlap([box1.ymin, box1.ymax], [box2.ymin, box2.ymax])

		intersect = int_w * int_h

		w1, h1 = box1.xmax - box1.xmin, box1.ymax - box1.ymin
		w2, h2 = box2.xmax - box2.xmin, box2.ymax - box2.ymin

		union = w1*h1 + w2*h2 - intersect

		return float(intersect) / union		

	def non_maximum_suppression(self, bboxes):
		if len(bboxes) > 0:
			nb_class = len(bboxes[0].classes)
		else:
			return
			
		for c in range(nb_class):
			sorted_indices = np.argsort([-box.classes[c] for box in bboxes])

			for i in range(len(sorted_indices)):
				index_i = sorted_indices[i]

				if bboxes[index_i].classes[c] == 0: continue

				for j in range(i+1, len(sorted_indices)):
					index_j = sorted_indices[j]

					if self.bbox_iou(bboxes[index_i], bboxes[index_j]) >= self.nms_threshold:
						bboxes[index_j].classes[c] = 0

	def decode_output(self, preds, anchors):
		gridh, gridw = preds.shape[:2]
		nb_box = 3
		preds = preds.reshape([gridh, gridw, nb_box, -1])
		nb_class = preds.shape[-1] - 5

		boxes = []
		
		preds[..., :2]  = self.sigmoid(preds[..., :2])
		preds[..., 4:]  = self.sigmoid(preds[..., 4:])
		preds[..., 5:]  = preds[..., 4][..., np.newaxis] * preds[..., 5:]
		preds[..., 5:] *= preds[..., 5:] > self.obj_threshold

		for i in range(gridh * gridw):
			row = i / gridw
			col = i % gridw

			for b in range(nb_box):
				objectness = preds[int(row)][int(col)][b][4]

				if(objectness.all() <= self.obj_threshold): continue

				x, y, w, h = preds[int(row)][int(col)][b][:4]

				x = (col + x) / gridw 
				y = (row + y) / gridh 
				w = anchors[2 * b + 0] * np.exp(w) / self.net_w
				h = anchors[2 * b + 1] * np.exp(h) / self.net_h

				classes = preds[int(row)][col][b][5:]

				box = BoundingBox(x-w/2, y-h/2, x+w/2, y+h/2, objectness, classes)

				boxes.append(box)

		return boxes		

	def rectify_bboxes(self, bboxes, image_h, image_w):
		if (float(self.net_w)/image_w) < (float(self.net_h)/image_h):
			new_w = self.net_w
			new_h = (image_h * self.net_w)/ image_w
		else:
			new_h = self.net_w
			new_w = (image_w * self.net_h) / image_h
			
		for i in range(len(bboxes)):
			x_offset, x_scale = (self.net_w - new_w)/2./self.net_w, float(new_w)/self.net_w
			y_offset, y_scale = (self.net_h - new_h)/2./self.net_h, float(new_h)/self.net_h
			
			bboxes[i].xmin = int((bboxes[i].xmin - x_offset) / x_scale * image_w)
			bboxes[i].xmax = int((bboxes[i].xmax - x_offset) / x_scale * image_w)
			bboxes[i].ymin = int((bboxes[i].ymin - y_offset) / y_scale * image_h)
			bboxes[i].ymax = int((bboxes[i].ymax - y_offset) / y_scale * image_h)

		return bboxes

	def decode_boxes(self, boxes, random_coloring=True):
		final_boxes = []
		for box in boxes:
			label_str = ""
			label = -1

			for i in range(len(self.all_labels)):
				if box.classes[i] > self.obj_threshold:
					label_str += self.all_labels[i]
					label = i

					final_boxes.append([self.all_labels[i], box.classes[i]*100, {'xmin': box.xmin, 'ymin': box.ymin, 'xmax': box.xmax, 'ymax': box.ymax}])

		return final_boxes

	def load_model(self, default_path="./bin/yolov3.weights", verbose=True):
		"""
		Downloads weights and config, loads checkpoints into architecture
		"""
		self.download_weights() # downloading weights from online
		loader = SightLoader(default_path)
		
		self.yolo_model = self.load_architecture() # loading weights into model
		loader.load_weights(self.yolo_model, verbose)

	def get_predictions(self, image):
		"""
		Returns a list of BoundingBox metadata (class label, confidence score, coordinates)
		and the edited image with bounding boxes and their corresponding text labels
		"""
		image_h, image_w = image.shape[:2]

		if self.yolo_model == None:
			raise ValueError ("YOLO9000 weights needs to be downloaded and configured into the model before use. You can use the `load_model()` method to do so.")

		preds = self.yolo_model.predict(image)
		boxes = []

		for i in range(len(preds)):
			boxes += self.decode_output(preds[i][0], self.anchors[i])

		boxes = self.rectify_bboxes(boxes, image_h, image_w)
		self.non_maximum_suppression(boxes)

		bbox_list = self.decode_boxes(boxes)

		return bbox_list