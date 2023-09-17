import os
import openai
from pathlib import Path
from learn_python.delphi.tutor import Tutor, ConfigurationError, LLMBackends
from uuid import uuid1
import json
from pprint import pformat

API_KEY_FILE = Path(__file__).parent / 'openai_api.key'


class OpenAITutor(Tutor):
    """
    https://platform.openai.com/docs/guides/gpt

    .. note::
    
        The OpenAI API is stateless, so each request needs to include the entire context
        the llm should respond to.
    """

    api_key = None
    model_priority = ['gpt-4', 'gpt-3.5-turbo']

    # this is a gpt parameter, None will use the default
    # Lower values for temperature result in more consistent
    # outputs, while higher values generate more diverse and 
    # creative results. Select a temperature value based on the 
    # desired trade-off between coherence and creativity for your 
    # specific application
    TEMPERATURE = None

    messages = []

    BACKEND = LLMBackends.OPEN_AI

    def __init__(self, api_key=api_key):
        if api_key is None and API_KEY_FILE.is_file():
            self.api_key = API_KEY_FILE.read_text().strip()
        
        if not self.api_key:
            with open(API_KEY_FILE, 'a'):
                os.utime(API_KEY_FILE, None)
            raise ConfigurationError(
                'The tutor requires an api key to be installed. '
                f'Please paste your OpenAI API key into the file: {API_KEY_FILE.relative_to(os.getcwd())}. '
                'See https://platform.openai.com/account/api-keys for details, or inquire with the instructor.'
            )
        
        openai.api_key = self.api_key
        super().__init__()

    def get_model(self, messages):
        # todo - return 32k model for large messages
        model = self.model_priority[0]
        self.logger.info('get_model() = %s', model)
        return model

    async def send(self):
        messages=[
            {'role': 'system', 'content': self.directive},
            *self.messages
        ]
        self.logger.info('send(), with directive')
        return await openai.ChatCompletion.acreate(
            model=self.get_model(messages),
            messages=messages,
            functions=self.functions
        )

    def handle_response(self, response):
        # todo run any functions that were called out
        self.logger.info('handle_response(%s)', response)
        resp = response['choices'][0]['message']
        self.call_function(
            resp.get('function_call', {}).get('name', None),
            **json.loads(resp.get('function_call', {}).get('arguments', '{}'))
        )
        return resp['content']