
import torch.nn as nn
from transformers.modeling_utils import PreTrainedModel
from transformers.configuration_utils import PretrainedConfig



class InvWordEmbedConfig (PretrainedConfig):
	model_type = 'inv_word_embed'

	def __init__ (self, vocab_size=1, hidden_size=1, **kwargs):
		super().__init__(**kwargs)

		self.vocab_size = vocab_size
		self.hidden_size = hidden_size


class InvWordEmbed (PreTrainedModel):
	config_class = InvWordEmbedConfig
	load_tf_weights = False


	def __init__ (self, config, **kwargs):
		super().__init__(config, **kwargs)

		self.fc = nn.Linear(config.hidden_size, config.vocab_size)

	def forward (self, x):
		return self.fc(x)
