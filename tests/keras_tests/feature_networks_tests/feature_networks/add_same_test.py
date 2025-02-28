# Copyright 2021 Sony Semiconductor Israel, Inc. All rights reserved.
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


from tests.common_tests.base_feature_test import BaseFeatureNetworkTest
import model_compression_toolkit as mct
import tensorflow as tf
from tests.keras_tests.feature_networks_tests.base_keras_feature_test import BaseKerasFeatureNetworkTest
import numpy as np
from tests.common_tests.helpers.tensors_compare import cosine_similarity
from model_compression_toolkit.core.common.quantization.quantization_config import DEFAULTCONFIG
from tests.keras_tests.utils import get_layers_from_model_by_type

keras = tf.keras
layers = keras.layers


class AddSameTest(BaseKerasFeatureNetworkTest):
    def __init__(self, unit_test):
        super().__init__(unit_test, experimental_exporter=True)

    def create_networks(self):
        inputs = layers.Input(shape=self.get_input_shapes()[0][1:])
        x = layers.Conv2D(6, 7)(inputs)
        x = layers.BatchNormalization()(x)
        outputs = layers.Add()([x, x])
        return keras.Model(inputs=inputs, outputs=outputs)

    def compare(self, quantized_model, float_model, input_x=None, quantization_info=None):
        add_layer = get_layers_from_model_by_type(quantized_model, layers.Add)[0]
        self.unit_test.assertTrue(len(add_layer.input) == 2)
        self.unit_test.assertTrue(add_layer.input[0].ref()==add_layer.input[1].ref())
