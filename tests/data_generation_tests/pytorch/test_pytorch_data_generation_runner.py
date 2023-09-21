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
import unittest

from torch.optim.lr_scheduler import StepLR, ReduceLROnPlateau

from model_compression_toolkit.data_generation.common.enums import SchedulerType, BatchNormAlignemntLossType, \
    DataInitType, BNLayerWeightingType, ImageGranularity, ImagePipelineType, ImageNormalizationType, OutputLossType
from tests.data_generation_tests.pytorch.base_pytorch_data_generation_test import BasePytorchDataGenerationTest


class PytorchDataGenerationTestRunner(unittest.TestCase):
    def test_pytorch_scheduler_types(self):
        BasePytorchDataGenerationTest(self, scheduler=StepLR, scheduler_type=SchedulerType.STEP).run_test()
        BasePytorchDataGenerationTest(self, scheduler=ReduceLROnPlateau, scheduler_type=SchedulerType.REDUCE_ON_PLATEAU).run_test()

    def test_pytorch_layer_weighting_types(self):
        BasePytorchDataGenerationTest(self, layer_weighting_type=BNLayerWeightingType.AVERAGE).run_test()

    def test_pytorch_bn_alignment_types(self):
        BasePytorchDataGenerationTest(self, bn_alignment_loss_type=BatchNormAlignemntLossType.L2_SQUARE).run_test()

    def test_pytorch_data_init_types(self):
        BasePytorchDataGenerationTest(self, data_init_type=DataInitType.Gaussian).run_test()
        BasePytorchDataGenerationTest(self, data_init_type=DataInitType.Diverse).run_test()

    def test_pytorch_image_granularity_types(self):
        BasePytorchDataGenerationTest(self, image_granularity=ImageGranularity.ImageWise).run_test()
        BasePytorchDataGenerationTest(self, image_granularity=ImageGranularity.BatchWise).run_test()
        BasePytorchDataGenerationTest(self, image_granularity=ImageGranularity.AllImages).run_test()

    def test_pytorch_image_pipeline_types(self):
        BasePytorchDataGenerationTest(self, image_pipeline_type=ImagePipelineType.IDENTITY).run_test()
        BasePytorchDataGenerationTest(self, image_pipeline_type=ImagePipelineType.RANDOM_CROP, extra_pixels=32).run_test()
        BasePytorchDataGenerationTest(self, image_pipeline_type=ImagePipelineType.RANDOM_CROP_FLIP, extra_pixels=0).run_test()
        BasePytorchDataGenerationTest(self, image_pipeline_type=ImagePipelineType.RANDOM_CROP_FLIP, extra_pixels=1).run_test()

    def test_pytorch_image_normalization_types(self):
        BasePytorchDataGenerationTest(self, image_normalization_type=ImageNormalizationType.TORCHVISION).run_test()
        BasePytorchDataGenerationTest(self, image_normalization_type=ImageNormalizationType.NO_NORMALIZATION).run_test()

    def test_pytorch_output_loss_types(self):
        BasePytorchDataGenerationTest(self, output_loss_type=OutputLossType.NONE).run_test()
        BasePytorchDataGenerationTest(self, output_loss_type=OutputLossType.MIN_MAX_DIFF).run_test()

if __name__ == '__main__':
    unittest.main()