# Copyright 2022 Sony Semiconductor Israel, Inc. All rights reserved.
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
import torch.nn
from torch.nn import Conv2d, Linear, ConvTranspose2d
from model_compression_toolkit.core.common.graph.graph_matchers import NodeOperationMatcher
from model_compression_toolkit.core.common.substitutions.weights_activation_split import BaseWeightsActivationSplit

"""
Matches: (DepthwiseConv2D, Conv2D, Dense, Conv2DTranspose)
"""
OP2D_NODE = NodeOperationMatcher(Conv2d) | \
            NodeOperationMatcher(Linear) | \
            NodeOperationMatcher(ConvTranspose2d)


class WeightsActivationSplit(BaseWeightsActivationSplit):
    """
    Substitution extends BaseWeightsActivationSplit for Keras framework.
    """

    def __init__(self):
        """
        Initializes a WeightsActivationSplit substitution for Keras framework.
        """

        super().__init__(activation_layer_type=torch.nn.Identity,
                         fw_attr={},
                         matcher_instance=OP2D_NODE)
