"""Chain that just formats a prompt and calls an LLM."""
from typing import Any, Dict, List, Union

from pydantic import BaseModel, Extra

import langchain
from langchain.chains.base import Chain
from langchain.llms.base import LLM
from langchain.prompts.base import BasePromptTemplate


class LLMChain(Chain, BaseModel):
    """Chain to run queries against LLMs.

    Example:
        .. code-block:: python

            from langchain import LLMChain, OpenAI, PromptTemplate
            prompt_template = "Tell me a {adjective} joke"
            prompt = PromptTemplate(
                input_variables=["adjective"], template=prompt_template
            )
            llm = LLMChain(llm=OpenAI(), prompt=prompt)
    """

    prompt: BasePromptTemplate
    """Prompt object to use."""
    llm: LLM
    """LLM wrapper to use."""
    output_key: str = "text"  #: :meta private:

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Will be whatever keys the prompt expects.

        :meta private:
        """
        return self.prompt.input_variables

    @property
    def output_keys(self) -> List[str]:
        """Will always return text key.

        :meta private:
        """
        return [self.output_key]

    def _call(self, inputs: Dict[str, Any]) -> Dict[str, str]:
        selected_inputs = {k: inputs[k] for k in self.prompt.input_variables}
        prompt = self.prompt.format(**selected_inputs)
        if self.verbose:
            langchain.logger.log_llm_inputs(selected_inputs, prompt)
        kwargs = {}
        if "stop" in inputs:
            kwargs["stop"] = inputs["stop"]
        response = self.llm(prompt, **kwargs)
        if self.verbose:
            langchain.logger.log_llm_response(response)
        return {self.output_key: response}

    def predict(self, **kwargs: Any) -> str:
        """Format prompt with kwargs and pass to LLM.

        Args:
            **kwargs: Keys to pass to prompt template.

        Returns:
            Completion from LLM.

        Example:
            .. code-block:: python

                completion = llm.predict(adjective="funny")
        """
        return self(kwargs)[self.output_key]

    def predict_and_parse(self, **kwargs: Any) -> Union[str, List[str], Dict[str, str]]:
        """Call predict and then parse the results."""
        result = self.predict(**kwargs)
        if self.prompt.output_parser is not None:
            return self.prompt.output_parser.parse(result)
        else:
            return result
