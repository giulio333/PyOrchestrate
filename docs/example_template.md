# Example Section Template

This template provides a consistent structure and format for example sections in the docstrings of the `Config` classes for different types of agents.

## Template

```python
Examples:
    Creating a custom configuration for a [AgentType]:

    >>> class [AgentType]Config([BaseConfigClass]):
    ...     [attribute_1] = [default_value_1]  # [description_1]
    ...     [attribute_2] = [default_value_2]  # [description_2]
    ...     [attribute_3] = [default_value_3]  # [description_3]

    >>> # Default configuration
    >>> default_[agent_type]_config = [AgentType]Config()

    >>> # Custom configuration
    >>> custom_[agent_type]_config = [AgentType]Config(
    ...     [attribute_1]=[custom_value_1],
    ...     [attribute_2]=[custom_value_2],
    ...     [attribute_3]=[custom_value_3]
    ... )
```

## Example

Here is an example of how to use this template for a `ChatAgent`:

```python
Examples:
    Creating a custom configuration for a ChatAgent:

    >>> class ChatAgentConfig(BaseAgent.Config):
    ...     model_name = "gpt-3.5-turbo"  # Default model name
    ...     max_tokens = 1000             # Default maximum tokens per request
    ...     temperature = 0.7             # Default temperature for sampling

    >>> # Default configuration
    >>> default_chat_config = ChatAgentConfig()

    >>> # Custom configuration
    >>> custom_chat_config = ChatAgentConfig(
    ...     model_name="gpt-4",
    ...     max_tokens=2000,
    ...     temperature=0.9
    ... )
```
