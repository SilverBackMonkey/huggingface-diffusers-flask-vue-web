
import random
import math
import numpy as np
import re
from transformers import BertTokenizer, pipeline



class SentenceGenerator:
	def __init__(self, templates_path, reserved_path, device=-1):
		self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
		self.unmasker = pipeline('fill-mask', model='bert-base-uncased', device=device)

		with open(reserved_path, 'r') as file:
			text = file.read()
			self.reserved_words = text.split('\n')

		with open(templates_path, 'r', encoding='utf-8') as file:
			text = file.read()
			sentences = text.split('\n')

			self.templates = [self.tokenize(sentence) for sentence in sentences]


	def tokenize (self, sentence):
		return self.tokenizer.basic_tokenizer.tokenize(sentence, never_split=self.tokenizer.all_special_tokens)


	def joinSentence (self, words):
		sentence = ' '.join(words)
		sentence = sentence.replace(' ,', ',')
		sentence = sentence.replace(' .', '.')
		sentence = sentence.replace(" ' s", "'s")
		sentence = re.sub(r'"\s([^"]*)\s"', r'"\1"', sentence)
		sentence = re.sub(r"'\s([^']*)\s'", r'"\1"', sentence)

		return sentence


	def transform_sentence (self, sentence, temperature=1):
		idx = [i for i, word in enumerate(sentence) if not word in self.reserved_words]

		if len(idx) <= 0:
			return sentence

		mid = idx[random.randrange(len(idx))]

		masked_sentence = ' '.join([word if i != mid else '[MASK]' for i, word in enumerate(sentence)])
		candidates = self.unmasker(masked_sentence)
		candidates = [c for c in candidates if c['token_str'] != 'the' and not c['token_str'] in sentence and re.match(r'^\w+', c['token_str']) is not None]
		if len(candidates) == 0:
			return sentence

		scores = [item['score'] for item in candidates]
		logits = [math.log(s) for s in scores]
		scores = [math.exp(logit / temperature) for logit in logits]
		score_sum = sum(scores)
		scores = [s / score_sum for s in scores]

		index = np.random.choice(len(scores), p=scores)

		nw = candidates[index]['token_str']
		new_sentence = [word if i != mid else nw for i, word in enumerate(sentence)]

		return new_sentence


	def generate (self, temperature=1, change_rate=0.5):
		template = self.templates[random.randrange(len(self.templates))]
		n_vary_word = len([word for word in template if not (word in self.reserved_words)])

		n_changes = max(1, round(math.exp(np.random.randn() * 0.4) * n_vary_word * change_rate))
		#print('n_changes:', n_changes)

		words = template
		for i in range(n_changes):
			words = self.transform_sentence(words, temperature)

		return self.joinSentence(words)
