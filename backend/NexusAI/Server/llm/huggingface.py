from __future__ import annotations
from langchain.chat_models.base import BaseChatModel
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from huggingface_hub import InferenceClient
import logging
from typing import *

from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import (
    BaseChatModel,
)
from langchain_core.messages import (
    BaseMessage,
    ChatMessage,
    SystemMessage,
    ToolMessage
)
from langchain_core.outputs import ChatGeneration,  ChatResult
from langchain_core.pydantic_v1 import BaseModel, Field, root_validator
from langchain_core.runnables import Runnable
from langchain_core.utils import (
    get_from_dict_or_env,
    get_pydantic_field_names,
    pre_init,
)


logger = logging.getLogger(__name__)

def convert_dict_to_message(_dict: Mapping[str, Any]) -> BaseMessage:
    """Convert a dictionary to a LangChain message.

    Args:
        _dict: The dictionary.

    Returns:
        The LangChain message.
    """
    role = _dict.get("role")
    if role == "user":
        return HumanMessage(content=_dict.get("content", ""))
    elif role == "assistant":
        # Fix for azure
        # Also OpenAI returns None for tool invocations
        content = _dict.get("content", "") or ""
        additional_kwargs: Dict = {}
        if function_call := _dict.get("function_call"):
            additional_kwargs["function_call"] = dict(function_call)
        if tool_calls := _dict.get("tool_calls"):
            additional_kwargs["tool_calls"] = tool_calls
        return AIMessage(content=content, additional_kwargs=additional_kwargs)
    elif role == "system":
        return SystemMessage(content=_dict.get("content", ""))
    elif role == "function":
        return FunctionMessage(content=_dict.get("content", ""), name=_dict.get("name"))  # type: ignore[arg-type]
    elif role == "tool":
        additional_kwargs = {}
        if "name" in _dict:
            additional_kwargs["name"] = _dict["name"]
        return ToolMessage(
            content=_dict.get("content", ""),
            tool_call_id=_dict.get("tool_call_id"),  # type: ignore[arg-type]
            additional_kwargs=additional_kwargs,
        )
    else:
        return ChatMessage(content=_dict.get("content", ""), role=role)  # type: ignore[arg-type]

class HuggingFaceChatModel(BaseChatModel):
    """`OpenAI` Chat large language models API.

    To use, you should have the ``openai`` python package installed, and the
    environment variable ``OPENAI_API_KEY`` set with your API key.

    Any parameters that are valid to be passed to the openai.create call can be passed
    in, even if not explicitly saved on this class.

    Example:
        .. code-block:: python

            from langchain_community.chat_models import ChatOpenAI
            openai = ChatOpenAI(model="gpt-3.5-turbo")
    """

    @property
    def lc_secrets(self) -> Dict[str, str]:
        return {"openai_api_key": "OPENAI_API_KEY"}

    @classmethod
    def get_lc_namespace(cls) -> List[str]:
        """Get the namespace of the langchain object."""
        return ["langchain", "chat_models", "openai"]

    @property
    def lc_attributes(self) -> Dict[str, Any]:
        attributes: Dict[str, Any] = {}

        return attributes

    @classmethod
    def is_lc_serializable(cls) -> bool:
        """Return whether this model can be serialized by Langchain."""
        return True


    model_name: str = Field(default=None, alias="model")
    """Model name to use."""
    temperature: float = 0.7
    """What sampling temperature to use."""
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    """Holds any model parameters valid for `create` call not explicitly specified."""
    # When updating this to use a SecretStr
    # Check for classes that derive from this class (as some of them
    # may assume openai_api_key is a str)
    token: Optional[str] = Field(default=None, alias="api_key")
    """Automatically inferred from env var `OPENAI_API_KEY` if not provided."""

    streaming: bool = True
    """Whether to stream the results or not."""
    n: int = 1
    """Number of chat completions to generate for each prompt."""
    max_tokens: Optional[int] = None
    """Maximum number of tokens to generate."""


    class Config:
        """Configuration for this pydantic object."""

        allow_population_by_field_name = True

    @root_validator(pre=True)
    def build_extra(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Build extra kwargs from additional params that were passed in."""
        all_required_field_names = get_pydantic_field_names(cls)
        extra = values.get("model_kwargs", {})
        for field_name in list(values):
            if field_name in extra:
                raise ValueError(f"Found {field_name} supplied twice.")
            if field_name not in all_required_field_names:
                logger.warning(
                    f"""WARNING! {field_name} is not default parameter.
                        {field_name} was transferred to model_kwargs.
                        Please confirm that {field_name} is what you intended."""
                )
                extra[field_name] = values.pop(field_name)

        invalid_model_kwargs = all_required_field_names.intersection(extra.keys())
        if invalid_model_kwargs:
            raise ValueError(
                f"Parameters {invalid_model_kwargs} should be specified explicitly. "
                f"Instead they were passed in as part of `model_kwargs` parameter."
            )

        values["model_kwargs"] = extra
        return values

    @property
    def _llm_type(self) -> str:
        return "huggingface"

    @pre_init
    def validate_environment(cls, values: Dict) -> Dict:
        """Validate that api key and python package exists in environment."""
        if values["n"] < 1:
            raise ValueError("n must be at least 1.")
        if values["n"] > 1 and values["streaming"]:
            raise ValueError("n must be 1 when streaming.")

        values["token"] = get_from_dict_or_env(
            values, "llama_token", "LLAMA_TOKEN"
        )



        client_params = {
                "token": values["token"],
            }

        if not values.get("client"):
                values["client"] = InferenceClient(**client_params).chat_completion
        if not values.get("async_client"):
                values["async_client"] = InferenceClient(
                    **client_params
                )
        elif not values.get("client"):
            values["client"] = InferenceClient.chat_completion
        else:
            pass
        return values

    def _generate(self, messages: List[BaseMessage], stop: list = None, max_tokens: int = 500,**kwargs):
        generations=[]
        hf_messages = [{"role": message.type, "content": message.content} for message in messages]
        response_content = ""
        _client = InferenceClient(model=self.model_name, token=self.token)
        for message in _client.chat_completion(
                messages=hf_messages,
                max_tokens=self.max_tokens,
                stream=self.streaming,
        ):
            if "choices" in message and "delta" in message.choices[0]:
                response_content += message.choices[0].delta.content

        response=ChatMessage(content=response_content,role="assistant")
        gen=ChatGeneration(message=response)
        generations.append(gen)
        if not generations:
            raise ValueError("No generations were generated.")
        return ChatResult(generations=generations)



    def bind_functions(
        self,
        functions: Sequence[Union[Dict[str, Any], Type[BaseModel], Callable]],
        function_call: Optional[str] = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        """Bind functions (and other objects) to this chat model.

        Args:
            functions: A list of function definitions to bind to this chat model.
                Can be  a dictionary, pydantic model, or callable. Pydantic
                models and callables will be automatically converted to
                their schema dictionary representation.
            function_call: Which function to require the model to call.
                Must be the name of the single provided function or
                "auto" to automatically determine which function to call
                (if any).
            kwargs: Any additional parameters to pass to the
                :class:`~langchain.runnable.Runnable` constructor.
        """
        from langchain.chains.openai_functions.base import convert_to_openai_function

        formatted_functions = [convert_to_openai_function(fn) for fn in functions]
        if function_call is not None:
            if len(formatted_functions) != 1:
                raise ValueError(
                    "When specifying `function_call`, you must provide exactly one "
                    "function."
                )
            if formatted_functions[0]["name"] != function_call:
                raise ValueError(
                    f"Function call {function_call} was specified, but the only "
                    f"provided function was {formatted_functions[0]['name']}."
                )
            function_call_ = {"name": function_call}
            kwargs = {**kwargs, "function_call": function_call_}
        return super().bind(
            functions=formatted_functions,
            **kwargs,
        )