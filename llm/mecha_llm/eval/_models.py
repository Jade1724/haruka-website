"""Azure OpenAI judge models for the evaluators (RAGAS + DeepEval).

Imports are lazy (inside the functions) so this module — and the modules that
import it — stay importable without the optional ``eval`` dependencies installed
(e.g. for pytest collection).
"""

from ..config import settings


def ragas_llm():
    from langchain_openai import AzureChatOpenAI
    from ragas.llms import LangchainLLMWrapper

    return LangchainLLMWrapper(
        AzureChatOpenAI(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_chat_deployment,
            temperature=0,
        )
    )


def ragas_embeddings():
    from langchain_openai import AzureOpenAIEmbeddings
    from ragas.embeddings import LangchainEmbeddingsWrapper

    return LangchainEmbeddingsWrapper(
        AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_deployment=settings.azure_openai_embedding_deployment,
        )
    )


def deepeval_model():
    from deepeval.models import AzureOpenAIModel

    return AzureOpenAIModel(
        model=settings.azure_openai_chat_deployment,
        deployment_name=settings.azure_openai_chat_deployment,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        base_url=settings.azure_openai_endpoint,
        temperature=0,
    )
