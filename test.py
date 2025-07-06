import openai

openai.api_key = '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'

# List all available models
models = openai.Model.list()

for model in models['data']:
    print(model['id'])
