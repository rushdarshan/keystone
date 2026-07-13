from .linear_baseline import register_linear
from .activation import register_activation
from .depth import register_depth
from .width import register_width
from .convolution import register_convolution
from .residual import register_residual
from .batchnorm import register_batchnorm
from .dropout import register_dropout
from .layernorm import register_layernorm
from .attention import register_attention
from .patch_embed import register_patch_embed
from .pos_embed import register_pos_embed
from .head_only import register_head_only


def register_all():
    register_linear()
    register_head_only()
    register_activation()
    register_depth()
    register_width()
    register_convolution()
    register_residual()
    register_batchnorm()
    register_dropout()
    register_layernorm()
    register_attention()
    register_patch_embed()
    register_pos_embed()
