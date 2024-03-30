
#import torch.nn as nn
from transformers import CLIPTextModel
from transformers.modeling_utils import PreTrainedModel
from transformers.configuration_utils import PretrainedConfig

from .invWordEmbed import InvWordEmbed



class ClipTextGeneratorConfig (PretrainedConfig):
	model_type = 'clip_text_generator'
	is_composition = True


	def __init__(
		self,
		vocab_size=49408,
		hidden_size=768,
		intermediate_size=3072,
		num_hidden_layers=12,
		num_attention_heads=12,
		max_position_embeddings=77,
		hidden_act="quick_gelu",
		layer_norm_eps=0.00001,
		dropout=0.0,
		attention_dropout=0.0,
		initializer_range=0.02,
		initializer_factor=1.0,
		pad_token_id=1,
		bos_token_id=0,
		eos_token_id=2,
		**kwargs
	):
		super().__init__(pad_token_id=pad_token_id, bos_token_id=bos_token_id, eos_token_id=eos_token_id, **kwargs)

		self.vocab_size = vocab_size
		self.hidden_size = hidden_size
		self.intermediate_size = intermediate_size
		self.dropout = dropout
		self.num_hidden_layers = num_hidden_layers
		self.num_attention_heads = num_attention_heads
		self.max_position_embeddings = max_position_embeddings
		self.layer_norm_eps = layer_norm_eps
		self.hidden_act = hidden_act
		self.initializer_range = initializer_range
		self.initializer_factor = initializer_factor
		self.attention_dropout = attention_dropout


class ClipTextGenerator (PreTrainedModel):
	config_class = ClipTextGeneratorConfig
	load_tf_weights = False


	def __init__ (self, config, **kwargs):
		super().__init__(config, **kwargs)

		self.text_encoder = CLIPTextModel._from_config(config)
		self.unembed = InvWordEmbed._from_config(config)


	def forward (self, ids):
		x = self.text_encoder(ids).last_hidden_state
		x = self.unembed(x)

		return x
