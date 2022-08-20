# Imports here
import os.path

import numpy as np
# import seaborn as sb
import cv2
# from workspace_utils import active_session
import tqdm
from PIL import Image
from collections import OrderedDict

import torch
from torch import nn
from torch import optim
import torch.nn.functional as F
from torchvision import datasets, transforms, models

data_dir = 'D:\DiplomSoft\Classification_man_or_woman\data\Peta_all_classes\Gender'
# data_dir = 'D:\DiplomSoft\Classification_man_or_woman\data\Peta_all_classes\Age'
train_dir = data_dir + '/Train'
valid_dir = data_dir + '/Val'
test_dir = data_dir + '/Val'
img_resize = 256

# os.environ["CUDA_VISIBLE_DEVICES"]="0"
PATH_SAVE_MODEL = 'vgg_16_256_Gender.pth'

# Define transforms for the training, validation, and testing sets
training_transforms = transforms.Compose([transforms.Resize(img_resize),
                                          transforms.RandomRotation(30),
                                          transforms.RandomResizedCrop(224),
                                          transforms.RandomHorizontalFlip(),
                                          transforms.ToTensor(),
                                          transforms.Normalize([0.485, 0.456, 0.406],
                                                               [0.229, 0.224, 0.225])])

validation_transforms = transforms.Compose([transforms.Resize(img_resize),
                                            transforms.CenterCrop(224),
                                            transforms.ToTensor(),
                                            transforms.Normalize([0.485, 0.456, 0.406],
                                                                 [0.229, 0.224, 0.225])])

testing_transforms = transforms.Compose([transforms.Resize(img_resize),
                                         transforms.CenterCrop(224),
                                         transforms.ToTensor(),
                                         transforms.Normalize([0.485, 0.456, 0.406],
                                                              [0.229, 0.224, 0.225])])


class vgg16_classifaer():
    def __init__(self,path_load_model=None,type_classifaer = None):

        if path_load_model==None:
            self.model = models.vgg16(pretrained=True)
            # self.model = models.resnet18(pretrained=True)
            self.top_acc = 0
            for parameter in self.model.parameters():
                parameter.requires_grad = False

            classifier = nn.Sequential(OrderedDict([('fc1', nn.Linear(25088, 5000)),
                                                    ('relu', nn.ReLU()),
                                                    ('drop', nn.Dropout(p=0.5)),
                                                    ('fc2', nn.Linear(5000, 2)), # need fixed
                                                    ('output', nn.LogSoftmax(dim=1))]))
            self.model.classifier = classifier
            # self.model.fc = classifier
            self.criterion = nn.NLLLoss()
            self.optimizer = optim.Adam(self.model.classifier.parameters(), lr=0.001)
        else:
            if os.path.exists(path_load_model):
                self.load_checkpoint(path_load_model)
            else:
                print('Файл с моделью не найден')



    def train(self,train_loader, validate_loader, epochs=15):

        steps = 0
        print_every = 40

        self.model.to('cuda')

        for e in range(epochs):

            self.model.train()
            running_loss = 0

            for images, labels in tqdm.tqdm(train_loader):
                steps += 1
                images, labels = images.to('cuda'), labels.to('cuda')
                self.optimizer.zero_grad()
                output = self.model.forward(images)
                loss = self.criterion(output, labels)
                loss.backward()
                self.optimizer.step()

                running_loss += loss.item()

                if steps % print_every == 0:
                    self.model.eval()
                    # Turn off gradients for validation, saves memory and computations
                    with torch.no_grad():
                        validation_loss, accuracy = self.validation(validate_loader)

                    print("Epoch: {}/{}.. ".format(e + 1, epochs),
                          "Training Loss: {:.3f}.. ".format(running_loss / print_every),
                          "Validation Loss: {:.3f}.. ".format(validation_loss / len(validate_loader)),
                          "Validation Accuracy: {:.3f}".format(accuracy / len(validate_loader)))
                    if self.top_acc < accuracy:
                        print('Save best model... ')
                        self.save_checkpoint()
                        self.top_acc = accuracy

                    running_loss = 0
                    self.model.train()

    def validation(self, validateloader):
        val_loss = 0
        accuracy = 0

        for images, labels in tqdm.tqdm(validateloader):
            images, labels = images.to('cuda'), labels.to('cuda')

            output = self.model.forward(images)
            val_loss += self.criterion(output, labels).item()

            probabilities = torch.exp(output)

            equality = (labels.data == probabilities.max(dim=1)[1])
            accuracy += equality.type(torch.FloatTensor).mean()

        return val_loss, accuracy

    def save_checkpoint(self):
        self.model.class_to_idx = training_dataset.class_to_idx
        checkpoint = {'arch': "vgg16",
                      'class_to_idx': self.model.class_to_idx,
                      'model_state_dict': self.model.state_dict(),
                      'top_acc': self.top_acc
                      }
        torch.save(checkpoint, PATH_SAVE_MODEL)

    def load_checkpoint(self,filepath):
        checkpoint = torch.load(filepath)
        if checkpoint['arch'] == 'vgg16':
            self.model = models.vgg16(pretrained=True)
            for param in self.model.parameters():
                param.requires_grad = False
        else:
            print("Architecture not recognized.")

        self.model.class_to_idx = checkpoint['class_to_idx']
        self.top_acc = checkpoint['top_acc']
        classifier = nn.Sequential(OrderedDict([('fc1', nn.Linear(25088, 5000)),
                                                ('relu', nn.ReLU()),
                                                ('drop', nn.Dropout(p=0.5)),
                                                ('fc2', nn.Linear(5000, len(checkpoint['class_to_idx']))),
                                                ('output', nn.LogSoftmax(dim=1))]))

        self.model.classifier = classifier
        self.model.load_state_dict(checkpoint['model_state_dict'])

    def process_image(self,image_path):
        pil_image = Image.open(image_path)

        # Resize
        if pil_image.size[0] > pil_image.size[1]:
            pil_image.thumbnail((5000, 256))
        else:
            pil_image.thumbnail((256, 5000))

        # Crop
        left_margin = (pil_image.width - 224) / 2
        bottom_margin = (pil_image.height - 224) / 2
        right_margin = left_margin + 224
        top_margin = bottom_margin + 224

        pil_image = pil_image.crop((left_margin, bottom_margin, right_margin, top_margin))

        # Normalize
        np_image = np.array(pil_image) / 255
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        np_image = (np_image - mean) / std
        # PyTorch expects the color channel to be the first dimension but it's the third dimension in the PIL image and Numpy array
        # Color channel needs to be first; retain the order of the other two dimensions.
        np_image = np_image.transpose((2, 0, 1))
        return np_image

    def predict(self,image_path, topk=5):
        ''' Predict the class (or classes) of an image using a trained deep learning model.
            '''
        self.model.eval()
        if torch.cuda.is_available():
            self.model.cuda()

        image = self.process_image(image_path)
        image = torch.from_numpy(image).type(torch.cuda.FloatTensor)
        # Returns a new tensor with a dimension of size one inserted at the specified position.
        image = image.unsqueeze(0)
        # device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        # image = image.to("cpu")
        output = self.model.forward(image)

        probabilities = torch.exp(output)

        # Probabilities and the indices of those probabilities corresponding to the classes
        top_probabilities, top_indices = probabilities.topk(topk)

        # Convert to lists
        top_probabilities = top_probabilities.detach().type(torch.FloatTensor).numpy().tolist()[0]
        top_indices = top_indices.detach().type(torch.FloatTensor).numpy().tolist()[0]

        # Convert topk_indices to the actual class labels using class_to_idx
        # Invert the dictionary so you get a mapping from index to class.

        idx_to_class = {value: key for key, value in self.model.class_to_idx.items()}
        top_classes = [idx_to_class[index] for index in top_indices]

        return top_probabilities, top_classes

    def test_accuracy(self, test_loader):
        # Do validation on the test set
        self.model.eval()
        self.model.to('cuda')

        with torch.no_grad():
            accuracy = 0
            for images, labels in tqdm.tqdm(test_loader):
                images, labels = images.to('cuda'), labels.to('cuda')
                output = self.model.forward(images)
                probabilities = torch.exp(output)
                equality = (labels.data == probabilities.max(dim=1)[1])
                accuracy += equality.type(torch.FloatTensor).mean()

            print("Test Accuracy: {}".format(accuracy / len(test_loader)))


if __name__=="__main__":
    model = vgg16_classifaer()
    #
    # # TODO: Load the datasets with ImageFolder
    # training_dataset = datasets.ImageFolder(train_dir, transform=training_transforms)
    # validation_dataset = datasets.ImageFolder(valid_dir, transform=validation_transforms)
    # testing_dataset = datasets.ImageFolder(test_dir, transform=testing_transforms)
    #
    # # TODO: Using the image datasets and the trainforms, define the dataloaders
    # train_loader = torch.utils.data.DataLoader(training_dataset, batch_size=64, shuffle=True)
    # validate_loader = torch.utils.data.DataLoader(validation_dataset, batch_size=32)
    # test_loader = torch.utils.data.DataLoader(testing_dataset, batch_size=32)
    # model.train(train_loader,test_loader, 400)
    # model.test_accuracy(test_loader)
    # print(model.predict('D:\DiplomSoft\Classification_man_or_woman\data\Peta_all_classes\Gender\\all\Female\\0001_001.jpg',1))
