# Please place any imports here.
# BEGIN IMPORTS

import numpy as np
import cv2
import random

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torchvision import transforms, datasets

# END IMPORTS

#########################################################
###              BASELINE MODEL
#########################################################

class AnimalBaselineNet(nn.Module):
    def __init__(self, num_classes=16):
        super(AnimalBaselineNet, self).__init__()
        # TODO: Define layers of model architecture
        # TODO-BLOCK-BEGIN
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=6, kernel_size=3, stride=2, padding=1)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv2d(in_channels=6, out_channels=12, kernel_size=3, stride=2, padding=1)
        self.conv3 = nn.Conv2d(in_channels=12, out_channels=24, kernel_size=3, stride=2, padding=1)
        self.fc = nn.Linear(8*8*24, 128)
        self.cls = nn.Linear(128, num_classes)
        # TODO-BLOCK-END

    def forward(self, x):
        x = x.contiguous().view(-1, 3, 64, 64).float()

        # TODO: Define forward pass
        # TODO-BLOCK-BEGIN
        x = self.conv1(x)  
        x = F.relu(x) 
        x = self.conv2(x) 
        x = F.relu(x) 
        x = self.conv3(x) 
        x = F.relu(x) 
        x = torch.flatten(x, 1)
        x = self.fc(x) 
        x = F.relu(x) 
        x = self.cls(x) 
        # TODO-BLOCK-END
        return x

def model_train(net, inputs, labels, criterion, optimizer):
    """
    Will be used to train baseline and student models.

    Inputs:
        net        network used to train
        inputs     (torch Tensor) batch of input images to be passed
                   through network
        labels     (torch Tensor) ground truth labels for each image
                   in inputs
        criterion  loss function
        optimizer  optimizer for network, used in backward pass

    Returns:
        running_loss    (float) loss from this batch of images
        num_correct     (torch Tensor, size 1) number of inputs
                        in this batch predicted correctly
        total_images    (float or int) total number of images in this batch

    Hint: Don't forget to zero out the gradient of the network before the backward pass. We do this before
    each backward pass as PyTorch accumulates the gradients on subsequent backward passes. This is useful
    in certain applications but not for our network.
    """
    
    # TODO: Foward pass
    # TODO-BLOCK-BEGIN
    foutputs = net.forward(inputs)
    # TODO-BLOCK-END

    # TODO: Backward pass
    # TODO-BLOCK-BEGIN 
    num_correct = 0
    total_images = 0
    optimizer.zero_grad()
    foutputs = net(inputs) 
    _, predicted = torch.max(foutputs.data, 1)
    num_correct += (predicted == labels.reshape((predicted.size()))).sum()
    total_images += labels.size(0)      
    running_loss = criterion(foutputs, labels.flatten())
    running_loss.backward()
    optimizer.step()           
    # TODO-BLOCK-END
    return running_loss, num_correct, total_images

#########################################################
###               DATA AUGMENTATION
#########################################################

class Shift(object):
    """
    Shifts input image by random x amount between [-max_shift, max_shift]
    and separate random y amount between [-max_shift, max_shift]. A positive
    shift in the x- and y- direction corresponds to shifting the image right
    and downwards, repectively.

    Inputs:
        max_shift  float; maximum magnitude amount to shift image in x and y directions.
    """
    
    def __init__(self, max_shift=10):
        self.max_shift = max_shift

    def __call__(self, image):
        """
        Inputs:
            image         3 x H x W image as torch Tensor

        Returns:
            shift_image   3 x H x W image as torch Tensor, shifted by random x
                          and random y amount, each amount between [-max_shift, max_shift].
                          Pixels outside original image boundary set to 0 (black).
        """
        image = image.numpy()
        _, H, W = image.shape
        # TODO: Shift image
        # TODO-BLOCK-BEGIN
        x_shift = np.random.uniform(-self.max_shift, self.max_shift+1)
        y_shift = np.random.uniform(-self.max_shift, self.max_shift+1)
        
        transform = np.float32([[1, 0, x_shift], [0, 1, y_shift]])
        
        image = cv2.warpAffine(image.transpose(1, 2, 0), transform, (W, H))
        image = image.transpose(2, 0, 1)
        # TODO-BLOCK-END

        return torch.Tensor(image)

    def __repr__(self):
        return self.__class__.__name__

class Contrast(object):
    """
    Randomly adjusts the contrast of an image. Uniformly select a contrast factor from
    [min_contrast, max_contrast]. Setting the contrast to 0 should set the intensity of all pixels to the
    mean intensity of the original image while a contrast of 1 returns the original image.

    Inputs:
        min_contrast    non-negative float; minimum magnitude to set contrast
        max_contrast    non-negative float; maximum magnitude to set contrast

    Returns:
        image        3 x H x W torch Tensor of image, with random contrast
                     adjustment
    """

    def __init__(self, min_contrast=0.3, max_contrast=1.0):
        self.min_contrast = min_contrast
        self.max_contrast = max_contrast

    def __call__(self, image):
        """
        Inputs:
            image         3 x H x W image as torch Tensor

        Returns:
            shift_image   3 x H x W torch Tensor of image, with random contrast
                          adjustment
        """
        image = image.numpy()
        _, H, W = image.shape

        # TODO: Change image contrast
        # TODO-BLOCK-BEGIN
        contrast = np.random.uniform(self.min_contrast, self.max_contrast)
        if(contrast == 1):
            image = image 
        else: 
            means = np.mean(image, axis = (1, 2))             
            image[0] = ((image[0] - means[0]) * contrast) + means[0]
            image[1] = ((image[1] - means[1]) * contrast) + means[1]
            image[2] = ((image[2] - means[2]) * contrast) + means[2] 
            
        # TODO-BLOCK-END

        return torch.Tensor(image)

    def __repr__(self):
        return self.__class__.__name__

class Rotate(object):
    """
    Rotates input image by random angle within [-max_angle, max_angle]. Positive angle corresponds to
    counter-clockwise rotation

    Inputs:
        max_angle  maximum magnitude of angle rotation, in degrees


    """
    def __init__(self, max_angle=10):
        self.max_angle = max_angle

    def __call__(self, image):
        """
        Inputs:
            image           image as torch Tensor

        Returns:
            rotated_image   image as torch Tensor; rotated by random angle
                            between [-max_angle, max_angle].
                            Pixels outside original image boundary set to 0 (black).
        """
        image = image.numpy()
        _, H, W  = image.shape

        # TODO: Rotate image
        # TODO-BLOCK-BEGIN
        angle = np.random.uniform(-self.max_angle, self.max_angle)
        rotation_matrix = cv2.getRotationMatrix2D((W/2, H/2), angle, 1)
        rotated_image = cv2.warpAffine(image.transpose(1, 2, 0), rotation_matrix, (W, H))
        rotated_image = rotated_image.transpose(2, 0, 1)
        image = rotated_image
        # TODO-BLOCK-END

        return torch.Tensor(image)

    def __repr__(self):
        return self.__class__.__name__

class HorizontalFlip(object):
    """
    Randomly flips image horizontally.

    Inputs:
        p          float in range [0,1]; probability that image should
                   be randomly rotated
    """
    def __init__(self, p=0.5):
        self.p = p

    def __call__(self, image):
        """
        Inputs:
            image           image as torch Tensor

        Returns:
            flipped_image   image as torch Tensor flipped horizontally with
                            probability p, original image otherwise.
        """
        image = image.numpy()
        _, H, W = image.shape

        # TODO: Flip image
        # TODO-BLOCK-BEGIN
        if np.random.rand() < self.p:
            flipped_image = cv2.flip(image.transpose(1, 2, 0), 1)
        else:
            flipped_image = image.transpose(1, 2, 0)
        flipped_image = flipped_image.transpose(2, 0, 1)
        image = flipped_image
        # TODO-BLOCK-END

        return torch.Tensor(image)

    def __repr__(self):
        return self.__class__.__name__

#########################################################
###             STUDENT MODEL
#########################################################

def get_student_settings(net):
    """
    Return transform, batch size, epochs, criterion and
    optimizer to be used for training.
    """
    dataset_means = [123./255., 116./255.,  97./255.]
    dataset_stds  = [ 54./255.,  53./255.,  52./255.]

    # TODO: Create data transform pipeline for your model
    # transforms.ToPILImage() must be first, followed by transforms.ToTensor()
    # TODO-BLOCK-BEGIN

    # TODO-BLOCK-END

    # TODO: Settings for dataloader and training. These settings
    # will be useful for training your model.
    # TODO-BLOCK-BEGIN
    
    # TODO-BLOCK-END

    # TODO: epochs, criterion and optimizer
    # TODO-BLOCK-BEGIN

    # TODO-BLOCK-END

    return transform, batch_size, epochs, criterion, optimizer

class AnimalStudentNet(nn.Module):
    def __init__(self, num_classes=16):
        super(AnimalStudentNet, self).__init__()
        # TODO: Define layers of model architecture
        # TODO-BLOCK-BEGIN

        # TODO-BLOCK-END

    def forward(self, x):
        x = x.contiguous().view(-1, 3, 64, 64).float()

        # TODO: Define forward pass
        # TODO-BLOCK-BEGIN

        # TODO-BLOCK-END
        return x

#########################################################
###             ADVERSARIAL IMAGES
#########################################################

def get_adversarial(img, output, label, net, criterion, epsilon):
    """
    Generates adversarial image by adding a small epsilon
    to each pixel, following the sign of the gradient.

    Inputs:
        img        (torch Tensor) image propagated through network
        output     (torch Tensor) output from forward pass of image
                   through network
        label      (torch Tensor) true label of img
        net        image classification model
        criterion  loss function to be used
        epsilon    (float) perturbation value for each pixel

    Outputs:
        perturbed_img   (torch Tensor, same dimensions as img)
                        adversarial image, clamped such that all values
                        are between [0,1]
                        (Clamp: all values < 0 set to 0, all > 1 set to 1)
        noise           (torch Tensor, same dimensions as img)
                        matrix of noise that was added element-wise to image
                        (i.e. difference between adversarial and original image)

    Hint: After the backward pass, the gradient for a parameter p of the network can be accessed using p.grad
    """

    # TODO: Define forward pass
    # TODO-BLOCK-BEGIN
    net.eval()
    img.requires_grad = True
    output = net(img)
    loss = criterion(output, label)
    loss.backward()

    gradient_sign = torch.sign(img.grad.data)

    perturbed_image = img + epsilon * gradient_sign
    perturbed_image = torch.clamp(perturbed_image, 0, 1)

    noise = perturbed_image - img
    # TODO-BLOCK-END

    return perturbed_image, noise

