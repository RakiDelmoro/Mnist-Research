import torch
from utils import digit_generator
from cupy_utils.utils import one_hot
from torch.utils.data import DataLoader
from torchvision import transforms, datasets
from cupy_mlp_models.residual_v2_utils import model

def main():
    EPOCHS = 100
    BATCH_SIZE = 2048
    IMAGE_WIDTH = 28
    IMAGE_HEIGHT = 28
    OJA_LEARNING_RATE = 0.001
    BACKPROP_LEARNING_RATE = 0.001
    NUMBER_OF_CLASSES = 10
    MIDDLE_LAYERS = [358] * 15
    INPUT_DATA_FEATURE_SIZE = IMAGE_HEIGHT*IMAGE_WIDTH
    INPUT_AND_OUTPUT_LAYERS = [INPUT_DATA_FEATURE_SIZE, NUMBER_OF_CLASSES]
    NETWORK_ARCHITECTURE = INPUT_AND_OUTPUT_LAYERS[:1] + MIDDLE_LAYERS + INPUT_AND_OUTPUT_LAYERS[1:]
    TRANSFORM = lambda x: torch.flatten(
        transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.5], std=[0.5])
        ])(x)
    ).type(dtype=torch.float32)
    TARGET_TRANSFORM = lambda x: torch.tensor(one_hot(x, number_of_classes=NUMBER_OF_CLASSES), dtype=torch.float32)
    
    training_dataset = datasets.MNIST('./training-data', download=True, train=True, transform=TRANSFORM, target_transform=TARGET_TRANSFORM)
    validation_dataset = datasets.MNIST('./training-data', download=True, train=False, transform=TRANSFORM, target_transform=TARGET_TRANSFORM)
    training_dataloader = DataLoader(training_dataset, batch_size=BATCH_SIZE, shuffle=True)
    validation_dataloader = DataLoader(validation_dataset, batch_size=BATCH_SIZE, shuffle=True)
    model(network_architecture=NETWORK_ARCHITECTURE, training_loader=training_dataloader, validation_loader=validation_dataloader, learning_rate=BACKPROP_LEARNING_RATE, epochs=EPOCHS)

main()
