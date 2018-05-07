from joblib import Parallel, delayed
from PIL import Image, ImageChops, ImageOps,ImageFilter
from scipy import misc
from scipy.misc import toimage	
from skimage import color, io, filters, transform	
from skimage.morphology import skeletonize_3d 	
from skimage.util import invert, random_noise
import cv2
import glob
import numpy as np
import os
import PIL
import scipy
import shutil
import sys	

def gaussianresize(image):
	img = io.imread(image)
	img = np.invert(img)
	img = filters.gaussian(img, 3,multichannel = True)
	img = transform.resize(img, (52,52) ,mode='constant')
	misc.imsave(image,img)

def fixedsize(image):
	img = io.imread(image)
	img = transform.resize(img, (208,208) ,mode='constant') 
	misc.imsave(image,img)

def size208(image):
	desired_size = 208
	im = Image.open(image).convert('L')
	old_size = im.size  
	ratio = float(208)/max(old_size)
	new_size = tuple([int(x*ratio) for x in old_size])
	im = im.resize(new_size, Image.ANTIALIAS)
	new_im = Image.new("RGB", (208, 208))
	new_im = PIL.ImageOps.invert(new_im)
	new_im.paste(im, ((208-new_size[0])//2,(208-new_size[1])//2))
	new_im.save(image)
	
def blur(image):
	img = cv2.imread(image,0)
	blurred = cv2.blur(img, (5, 5))
	cv2.imwrite(image, blurred)

def crop(image):
    img = Image.open(image)
    bg = Image.new(img.mode, img.size, img.getpixel((0,0)))  
    diff = ImageChops.difference(img, bg)                
    diff = ImageChops.add(diff, diff, 2.0, -100)         
    bbox = diff.getbbox()       
    if bbox:                     
        img = img.crop(bbox)
        img.save(image)

def padding(image):
	old_im = Image.open(image)
	old_size = old_im.size
	new_size = ((old_size[0]+100), (old_size[1]+100))
	new_im = Image.new("RGB", new_size)   
	new_im = ImageOps.invert(new_im)
	new_im.paste(old_im, (int((new_size[0]-old_size[0])/2),int((new_size[1]-old_size[1])/2)))
	os.remove(image)
	new_im.save(image)

def binerize(image):
	img = cv2.imread(image,0)
	ret,thresh = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
	cv2.imwrite(image, thresh)

def remove(image):
	img = cv2.imread(image,0)
	ret,thresh = cv2.threshold(img,127,255,cv2.THRESH_BINARY_INV)
	new_img = np.zeros_like(thresh)                                        
	for value in np.unique(thresh)[1:]:                                      
		mask = np.uint8(thresh == value)                                    
		labels, stats = cv2.connectedComponentsWithStats(mask, 4)[1:3] 
		largest_label = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])      
		new_img[labels == largest_label] = value                          
	ret,thresh2 = cv2.threshold(new_img,127,255,cv2.THRESH_BINARY_INV)
	cv2.imwrite(image, thresh2)
	
def augment(rootdir):
	flist = os.listdir(rootdir)
	for i in range(0,len(flist)):
		flist[i] = os.path.join(rootdir, flist[i])
	Parallel(n_jobs = -1)(delayed(fixedsize)(n) for n in flist)			# Resizes all images to fixed size
	Parallel(n_jobs = -1)(delayed(binerize)(n) for n in flist)			# Smoothing: first binerize to remove stray noise
	Parallel(n_jobs = -1)(delayed(blur)(n) for n in flist)				# Smoothing: blur to smooth the pixelated edges
	Parallel(n_jobs = -1)(delayed(binerize)(n) for n in flist)			# Smoothing: second binerize to get clear output
	# Parallel(n_jobs = -1)(delayed(remove)(n) for n in flist) 			# Retains the largest connected segment in the image
	Parallel(n_jobs = -1)(delayed(crop)(n) for n in flist)				# Croping since rotated images have added padding
	Parallel(n_jobs = -1)(delayed(padding)(n) for n in flist)			# Adding fixed padding to all images
	Parallel(n_jobs = -1)(delayed(size208)(n) for n in flist)			# Resizing to redues line cuts 
	Parallel(n_jobs = -1)(delayed(gaussianresize)(n) for n in flist)	# Resize to ML specification and adds gaussian blur