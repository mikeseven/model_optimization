# Copyright 2023 Sony Semiconductor Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
import time
from typing import Callable, Tuple, List, Dict
from tqdm import tqdm

from model_compression_toolkit.constants import FOUND_TF
from model_compression_toolkit.data_generation.common.constants import DEFAULT_N_ITER, DEFAULT_DATA_GEN_BS
from model_compression_toolkit.data_generation.common.data_generation import get_data_generation_classes
from model_compression_toolkit.logger import Logger
from model_compression_toolkit.data_generation.common.data_generation_config import DataGenerationConfig, \
    ImageGranularity
from model_compression_toolkit.data_generation.common.enums import BatchNormAlignemntLossType, DataInitType, \
    BNLayerWeightingType, ImagePipelineType, ImageNormalizationType, SchedulerType, OutputLossType

if FOUND_TF:
    import tensorflow as tf
    from tensorflow.keras.layers import BatchNormalization
    from tensorflow.keras.optimizers.legacy import Optimizer, Adam
    from model_compression_toolkit.data_generation.keras.constants import DEFAULT_KERAS_INITIAL_LR, \
        DEFAULT_KERAS_OUTPUT_LOSS_MULTIPLIER
    from model_compression_toolkit.data_generation.keras.image_pipeline import (image_pipeline_dict,
                                                                                image_normalization_dict)
    from model_compression_toolkit.data_generation.keras.model_info_exctractors import (KerasActivationExtractor,
                                                                                        KerasOriginalBNStatsHolder)
    from model_compression_toolkit.data_generation.keras.optimization_functions.batchnorm_alignment_functions import \
        bn_alignment_loss_function_dict
    from model_compression_toolkit.data_generation.keras.optimization_functions.bn_layer_weighting_functions import \
        bn_layer_weighting_function_dict
    from model_compression_toolkit.data_generation.keras.optimization_functions.image_initilization import \
        image_initialization_function_dict
    from model_compression_toolkit.data_generation.keras.optimization_utils import KerasImagesOptimizationHandler, \
        KerasBatchStatsHolder
    from model_compression_toolkit.data_generation.keras.optimization_functions.output_loss_functions import \
        output_loss_function_dict
    from model_compression_toolkit.data_generation.keras.optimization_functions.scheduler_step_functions import \
        scheduler_step_function_dict

    # Function to create a DataGenerationConfig object with the specified configuration parameters for Tensorflow
    def get_tensorflow_data_generation_config(
            n_iter: int = DEFAULT_N_ITER,
            optimizer: Optimizer = Adam,
            data_gen_batch_size: int = DEFAULT_DATA_GEN_BS,
            initial_lr: float = DEFAULT_KERAS_INITIAL_LR,
            output_loss_multiplier: float = DEFAULT_KERAS_OUTPUT_LOSS_MULTIPLIER,
            scheduler_type: SchedulerType = SchedulerType.REDUCE_ON_PLATEAU,
            bn_alignment_loss_type: BatchNormAlignemntLossType = BatchNormAlignemntLossType.L2_SQUARE,
            output_loss_type: OutputLossType = OutputLossType.REGULARIZED_MIN_MAX_DIFF,
            data_init_type: DataInitType = DataInitType.Gaussian,
            layer_weighting_type: BNLayerWeightingType = BNLayerWeightingType.AVERAGE,
            image_granularity: ImageGranularity = ImageGranularity.BatchWise,
            image_pipeline_type: ImagePipelineType = ImagePipelineType.RANDOM_CROP_FLIP,
            image_normalization_type: ImageNormalizationType = ImageNormalizationType.KERAS_APPLICATIONS,
            extra_pixels: int = 0,
            bn_layer_types: List = [BatchNormalization],
            clip_images: bool = True,
            reflection: bool = True,
    ) -> DataGenerationConfig:
        """
        Function to create a DataGenerationConfig object with the specified configuration parameters.

        Args:
            n_iter (int): Number of iterations for the data generation process.
            optimizer (Optimizer): The optimizer to use for the data generation process.
            data_gen_batch_size (int): Batch size for data generation.
            initial_lr (float): Initial learning rate for the optimizer.
            output_loss_multiplier (float): Multiplier for the output loss during optimization.
            scheduler_type (SchedulerType): The type of scheduler to use.
            bn_alignment_loss_type (BatchNormAlignemntLossType): The type of BatchNorm alignment loss to use.
            output_loss_type (OutputLossType): The type of output loss to use.
            data_init_type (DataInitType): The type of data initialization to use.
            layer_weighting_type (BNLayerWeightingType): The type of layer weighting to use.
            image_granularity (ImageGranularity): The granularity of the images for optimization.
            image_pipeline_type (ImagePipelineType): The type of image pipeline to use.
            image_normalization_type (ImageNormalizationType): The type of image normalization to use.
            extra_pixels (int): Extra pixels to add to the input image size. Defaults to 0.
            bn_layer_types (List): List of BatchNorm layer types to be considered for data generation.
            clip_images (bool): Whether to clip images during optimization.
            reflection (bool): Whether to use reflection during optimization.

        Returns:
            DataGenerationConfig: Data generation configuration object.
        """

        # Create and return a DataGenerationConfig object with the specified parameters
        return DataGenerationConfig(
            n_iter=n_iter,
            optimizer=optimizer,
            data_gen_batch_size=data_gen_batch_size,
            initial_lr=initial_lr,
            scheduler_type=scheduler_type,
            bn_alignment_loss_type=bn_alignment_loss_type,
            output_loss_type=output_loss_type,
            data_init_type=data_init_type,
            layer_weighting_type=layer_weighting_type,
            image_granularity=image_granularity,
            image_pipeline_type=image_pipeline_type,
            image_normalization_type=image_normalization_type,
            extra_pixels=extra_pixels,
            bn_layer_types=bn_layer_types,
            clip_images=clip_images,
            reflection=reflection,
            output_loss_multiplier=output_loss_multiplier)


    def tensorflow_data_generation_experimental(
            model: tf.keras.Model,
            n_images: int,
            output_image_size: Tuple,
            data_generation_config: DataGenerationConfig) -> tf.Tensor:
        """
        Function to perform data generation using the provided model and data generation configuration.

        Args:
            model (Model): Keras model to generate data for.
            n_images (int): Number of images to generate.
            output_image_size (Tuple): Size of the output images.
            data_generation_config (DataGenerationConfig): Configuration for data generation.

        Returns:
            List[tf.Tensor]: Finalized list containing generated images.
        """
        # Get Data Generation functions and classes
        image_pipeline, normalization, bn_layer_weighting_fn, bn_alignment_loss_fn, output_loss_fn, \
            init_dataset = get_data_generation_classes(data_generation_config=data_generation_config,
                                                       output_image_size=output_image_size,
                                                       n_images=n_images,
                                                       image_pipeline_dict=image_pipeline_dict,
                                                       image_normalization_dict=image_normalization_dict,
                                                       bn_layer_weighting_function_dict=
                                                       bn_layer_weighting_function_dict,
                                                       image_initialization_function_dict=
                                                       image_initialization_function_dict,
                                                       bn_alignment_loss_function_dict=bn_alignment_loss_function_dict,
                                                       output_loss_function_dict=output_loss_function_dict)

        if not all(normalization[1]):
            Logger.exception(
                f'Invalid normalization std {normalization[1]} set to zero,'
                f'will lead to division by zero., Please choose non-zero normalization std')

        # Get the scheduler functions corresponding to the specified scheduler type
        scheduler_get_fn = scheduler_step_function_dict.get(data_generation_config.scheduler_type)

        # Check if the scheduler type is valid
        if scheduler_get_fn is None:
            Logger.exception(
                f'Invalid scheduler_type {data_generation_config.scheduler_type}.'
                f'Please choose one of {SchedulerType.get_values()}')

        # Create a scheduler object with the specified number of iterations
        scheduler = scheduler_get_fn(n_iter=data_generation_config.n_iter,
                                     initial_lr=data_generation_config.initial_lr)

        # Set the model to eval mode
        model.trainable = False

        # Create an activation extractor object to extract activations from the model
        activation_extractor = KerasActivationExtractor(model=model,
                                                        layer_types_to_extract_inputs=
                                                        data_generation_config.bn_layer_types,
                                                        image_granularity=data_generation_config.image_granularity,
                                                        image_input_manipulation=
                                                        image_pipeline.image_input_manipulation)

        # Create an orig_bn_stats_holder object to hold original BatchNorm statistics
        orig_bn_stats_holder = KerasOriginalBNStatsHolder(model=model,
                                                          bn_layer_types=data_generation_config.bn_layer_types)

        # Create an ImagesOptimizationHandler object for handling optimization
        all_imgs_opt_handler = KerasImagesOptimizationHandler(
            init_dataset=init_dataset,
            data_generation_config=data_generation_config,
            image_pipeline=image_pipeline,
            activation_extractor=activation_extractor,
            scheduler=scheduler,
            normalization_mean=normalization[0],
            normalization_std=normalization[1],
            model=model,
            orig_bn_stats_holder=orig_bn_stats_holder)

        # Compute the layer weights based on orig_bn_stats_holder
        bn_layer_weights = bn_layer_weighting_fn(orig_bn_stats_holder=orig_bn_stats_holder)

        # Get the current time to measure the total time taken
        total_time = time.time()

        # Create a tqdm progress bar for iterating over data_generation_config.n_iter iterations
        ibar = tqdm(range(data_generation_config.n_iter))

        # Perform data generation iterations
        for i_ter in ibar:

            # Randomly reorder the batches
            all_imgs_opt_handler.random_batch_reorder()

            # Iterate over each batch
            for i_batch in range(all_imgs_opt_handler.n_batches):
                # Get the random batch index
                random_batch_index = all_imgs_opt_handler.get_random_batch_index(index=i_batch)

                # Get the images to optimize and the optimizer for the batch
                imgs_to_optimize = all_imgs_opt_handler.get_images_by_batch_index(batch_index=random_batch_index)

                # Compute the gradients and the loss for the batch
                gradients, total_loss, bn_loss, output_loss = keras_compute_grads(imgs_to_optimize=imgs_to_optimize,
                                                                                  batch_index=random_batch_index,
                                                                                  activation_extractor=
                                                                                  activation_extractor,
                                                                                  all_imgs_opt_handler=
                                                                                  all_imgs_opt_handler,
                                                                                  bn_layer_weights=bn_layer_weights,
                                                                                  bn_alignment_loss_fn=
                                                                                  bn_alignment_loss_fn,
                                                                                  output_loss_fn=output_loss_fn,
                                                                                  output_loss_multiplier=
                                                                                  data_generation_config.
                                                                                  output_loss_multiplier)

                # Perform optimization step
                all_imgs_opt_handler.optimization_step(batch_index=random_batch_index,
                                                       images=imgs_to_optimize,
                                                       gradients=gradients,
                                                       loss=total_loss,
                                                       i_ter=i_ter)

                # Update the statistics based on the updated images
                if all_imgs_opt_handler.use_all_data_stats:
                    final_imgs = image_pipeline.image_output_finalize(images=imgs_to_optimize)
                    all_imgs_opt_handler.update_statistics(input_imgs=final_imgs,
                                                           batch_index=random_batch_index,
                                                           activation_extractor=activation_extractor)

            ibar.set_description(f"Total Loss: {total_loss.numpy().mean().item():.5f}, "
                                 f"BN Loss: {bn_loss.numpy().mean().item():.5f}, "
                                 f"Output Loss: {output_loss.numpy().mean().item():.5f}")

        # Return a list containing the finalized generated images
        generated_images_list = all_imgs_opt_handler.get_finilized_data_loader()
        Logger.info(f'Total time to generate {len(generated_images_list)} images (seconds): '
                    f'{int(time.time() - total_time)}')
        return generated_images_list

    # Compute the gradients and the loss for the batch
    def keras_compute_grads(imgs_to_optimize: tf.Tensor,
                            batch_index: int,
                            activation_extractor: KerasActivationExtractor,
                            all_imgs_opt_handler: KerasImagesOptimizationHandler,
                            bn_layer_weights: Dict,
                            bn_alignment_loss_fn: Callable,
                            output_loss_fn: Callable,
                            output_loss_multiplier: float) -> (
            Tuple)[List[tf.Tensor], tf.Tensor, tf.Tensor, tf.Tensor]:
        """
        This function run part of the training step, calculating the losses and the gradients for the batch.

        Args:
            imgs_to_optimize (tf.Tensor): The images to optimize for the batch.
            batch_index (int): The index of the batch.
            activation_extractor (KerasActivationExtractor): Extractor for layer activations.
            all_imgs_opt_handler (KerasImagesOptimizationHandler): Handles the images optimization process.
            bn_layer_weights (Dict): weights to multiply the loss for each layer.
            bn_alignment_loss_fn (Callable): Function to compute BatchNorm alignment loss.
            output_loss_fn (Callable): Function to compute output loss.
            output_loss_multiplier (float): Multiplier for the output loss.

        Returns:
    Returns:
        Tuple[List[tf.Tensor], tf.Tensor, tf.Tensor, tf.Tensor]: A tuple containing:
        - The gradients calculated for the images
        - Total loss
        - BN loss
        - Output loss
        """
        # Create a gradient tape to compute gradients
        with tf.GradientTape(watch_accessed_variables=False) as tape:
            # Watch the images to be optimized to compute gradients.
            tape.watch(imgs_to_optimize)

            # Perform image input manipulation
            input_imgs = all_imgs_opt_handler.image_pipeline.image_input_manipulation(images=imgs_to_optimize)

            # Forward pass to extract activations
            output = activation_extractor.run_model(inputs=input_imgs)

            # Compute BatchNorm alignment loss
            bn_loss = all_imgs_opt_handler.compute_bn_loss(input_imgs=input_imgs,
                                                           batch_index=batch_index,
                                                           activation_extractor=activation_extractor,
                                                           bn_alignment_loss_fn=bn_alignment_loss_fn,
                                                           bn_layer_weights=bn_layer_weights)

            # Compute output loss
            # If output_loss_multiplier is zero return 0
            output_loss = output_loss_multiplier * output_loss_fn(
                output_imgs=output,
                activation_extractor=activation_extractor,
                tape=tape) if output_loss_multiplier > 0 else tf.zeros(1)

            # Compute total loss
            total_loss = bn_loss + output_loss

            # Get the trainable variables
            variables = [imgs_to_optimize]

        # Compute gradients of the total loss with respect to the images
        gradients = tape.gradient(total_loss, variables)

        # Return the computed gradients and individual loss components
        return gradients, total_loss, bn_loss, output_loss


else:
    def get_tensorflow_data_generation_config(*args, **kwargs):
        Logger.critical('Installing tensorflow is mandatory when using get_tensorflow_data_generation_config. '
                        'Could not find Tensorflow package.')  # pragma: no cover


    def tensorflow_data_generation_experimental(*args, **kwargs):
        Logger.critical('Installing tensorflow is mandatory when using pytorch_data_generation_experimental. '
                        'Could not find Tensorflow package.')  # pragma: no cover
