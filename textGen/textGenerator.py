
import torch
import re

from .transformers.clipTextGenerator import ClipTextGenerator



class SentenceGenerator:
	def __init__ (self, model_path, tokenizer, device='cpu'):
		self.device = device

		self.tokenizer = tokenizer
		self.model = ClipTextGenerator.from_pretrained(model_path)
		self.model.to(device)


	def ids2Text (self, ids):
		words = [self.tokenizer._convert_id_to_token(id) for id in ids.tolist()]
		sentence = ''.join(words)
		sentence = re.sub(r'<\|\w+\|>', '', sentence)
		sentence = re.sub(r'<\/w>,', ',', sentence)
		sentence = re.sub(r'<\/w>\.', '.', sentence)
		sentence = re.sub(r'<\/w>', ' ', sentence)
		sentence = re.sub(r'(?P<n>\d+) k,', '\g<n>k,', sentence)
		sentence = re.sub(r'(?P<n>\d+) k$', '\g<n>k', sentence)
		sentence = re.sub(r'\s+$', '', sentence)

		return sentence


	def generate (self, leading_text='', temperature=1, length_limit=1000):
		ids = self.tokenizer(leading_text, return_tensors='pt')['input_ids'][0, :-1].cpu()

		while True:
			if ids[-1].item() == self.tokenizer.eos_token_id or ids.shape[0] >= length_limit:
				break

			with torch.no_grad():
				output = self.model(ids[None, -self.tokenizer.model_max_length:].to(self.device))[0]
				weights = torch.exp((output[-1] / temperature).clip(max=80.))
				next_id = torch.multinomial(weights, 1).cpu()

				ids = torch.cat((ids, next_id))

		return self.ids2Text(ids)
