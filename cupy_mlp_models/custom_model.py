import random
import cupy as cp
from features import GREEN, RED, RESET
from cupy_utils.utils import cupy_array
from nn_utils.activation_functions import relu
from nn_utils.loss_functions import cross_entropy_loss
from cupy_utils.utils import axons_initialization

def forward_pass_activations(input_feature, layers_parameters):
    neurons = cp.array(input_feature)
    total_activations = len(layers_parameters)
    neurons_activations = [neurons]
    for layer_idx in range(total_activations):
        axons = layers_parameters[layer_idx][0]
        dentrites = layers_parameters[layer_idx][1]
        if layer_idx != total_activations-1:
            neurons = relu(cp.dot(neurons, axons))
        else:
            neurons = (cp.dot(cp.sum(cp.stack(neurons_activations[1:]), axis=0), axons) + dentrites)
        neurons_activations.append(neurons)
    return neurons_activations

def update_layers_parameters(neurons_activations, neurons_loss, layers_parameters, learning_rate):
    total_parameters = len(layers_parameters)
    for layer_idx in range(total_parameters):
        axons = layers_parameters[-(layer_idx+1)][0]
        dentrites = layers_parameters[-(layer_idx+1)][1]
        current_activation = neurons_activations[-(layer_idx+1)]
        previous_activation = neurons_activations[-(layer_idx+2)]
        if layer_idx == 0:
            backprop_parameters_nudge = learning_rate * cp.dot(previous_activation.transpose(), neurons_loss)
            dentrites -= ((learning_rate * cp.sum(neurons_loss, axis=0)) / current_activation.shape[0])
            axons -= (backprop_parameters_nudge / current_activation.shape[0])        
        else:
            oja_parameters_nudge = 0.01 * (cp.dot(previous_activation.transpose(), current_activation) - cp.dot(cp.dot(current_activation.transpose(), current_activation), axons.transpose()).transpose())
            axons += (oja_parameters_nudge / current_activation.shape[0])

def training_layers(dataloader, layers_parameters, learning_rate):
    per_batch_stress = []
    for i, (input_batch, expected_batch) in enumerate(dataloader):
        neurons_activations = forward_pass_activations(input_batch, layers_parameters)
        avg_last_neurons_stress, neurons_stress_to_backpropagate = cross_entropy_loss(neurons_activations[-1], cp.array(expected_batch))
        # layers_stress = calculate_layers_stress(neurons_stress_to_backpropagate, neurons_activations, layers_parameters)
        update_layers_parameters(neurons_activations, neurons_stress_to_backpropagate, layers_parameters, learning_rate)
        print(f"Loss each batch {i+1}: {avg_last_neurons_stress}\r", end="", flush=True)
        per_batch_stress.append(avg_last_neurons_stress)
        if i == 1000:
            break
    return cp.mean(cp.array(per_batch_stress))

def test_layers(dataloader, layers_parameters):
    correct_predictions = []
    wrong_predictions = []
    model_predictions = []
    for i, (input_image_batch, expected_batch) in enumerate(dataloader):
        expected_batch = cupy_array(expected_batch)
        model_output = forward_pass_activations(input_image_batch, layers_parameters)[-1]
        batched_accuracy = cp.array(expected_batch.argmax(-1) == (model_output).argmax(-1)).astype(cp.float16).mean()
        for each in range(100):
            if model_output[each].argmax(-1) == expected_batch[each].argmax(-1):
                correct_predictions.append((model_output[each].argmax(-1).item(), expected_batch[each].argmax(-1).item()))
            else:
                wrong_predictions.append((model_output[each].argmax(-1).item(), expected_batch[each].argmax(-1).item()))
        print(f"Number of sample: {i+1}\r", end="", flush=True)
        model_predictions.append(batched_accuracy)
    random.shuffle(correct_predictions)
    random.shuffle(wrong_predictions)
    print(f"{GREEN}MODEL Correct Predictions{RESET}")
    [print(f"Digit Image is: {GREEN}{expected}{RESET} Model Prediction: {GREEN}{prediction}{RESET}") for i, (prediction, expected) in enumerate(correct_predictions) if i < 10]
    print(f"{RED}MODEL Wrong Predictions{RESET}")
    [print(f"Digit Image is: {RED}{expected}{RESET} Model Prediction: {RED}{prediction}{RESET}") for i, (prediction, expected) in enumerate(wrong_predictions) if i < 10]
    return cp.mean(cp.array(model_predictions)).item()

def model(network_architecture, training_loader, validation_loader, learning_rate, epochs):
    network_parameters = [axons_initialization(network_architecture[feature_idx], network_architecture[feature_idx+1]) for feature_idx in range(len(network_architecture)-1)]
    for epoch in range(epochs):
        print(f'EPOCH: {epoch+1}')
        model_stress = training_layers(dataloader=training_loader, layers_parameters=network_parameters, learning_rate=learning_rate)
        model_accuracy = test_layers(dataloader=validation_loader, layers_parameters=network_parameters)
        # print(f'accuracy: {model_accuracy}')
        print(f'Average loss per epoch: {model_stress} accuracy: {model_accuracy}')
