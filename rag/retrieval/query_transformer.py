import os
from typing import List
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Ensure environment variables are loaded
load_dotenv()

class QueryTransformer:
    """
    A class that transforms user queries to improve retrieval in a RAG pipeline.
    Supports strategies:
    - 'rewrite': Rewrites the query to be optimized for vector and keyword search.
    - 'expand': Generates multiple search query variations to retrieve diverse document angles.
    - 'hyde': Generates a hypothetical document answering the query for semantic search.
    """
    def __init__(self, strategy: str = "rewrite", model_name: str = "llama-3.3-70b-versatile"):
        self.strategy = strategy
        self.llm = ChatGroq(model=model_name, temperature=0.0)

    def transform(self, query: str) -> List[str]:
        """
        Transforms the input query based on the configured strategy.

        Args:
            query: The original user search query.

        Returns:
            A list of transformed queries (or a single query as a list of length 1).
        """
        if self.strategy == "rewrite":
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert tax advisor. Rewrite the following user query to optimize it for a vector database and BM25 search. Focus on tax terms, relevant sections, and keywords. Return ONLY the rewritten query, with no other text, quotes, or conversational phrases."),
                ("user", "{query}")
            ])
            chain = prompt | self.llm | StrOutputParser()
            rewritten = chain.invoke({"query": query}).strip()
            # Clean up any enclosing quotes from the LLM
            if rewritten.startswith('"') and rewritten.endswith('"'):
                rewritten = rewritten[1:-1]
            elif rewritten.startswith("'") and rewritten.endswith("'"):
                rewritten = rewritten[1:-1]
            return [rewritten]

        elif self.strategy == "expand":
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert tax advisor. Generate 3 different search query variations of the following user query to retrieve relevant documents from a database. Focus on different aspects, keywords, and tax terminology. Output the queries separated by newlines, one per line. Do not number them or add any other text."),
                ("user", "{query}")
            ])
            chain = prompt | self.llm | StrOutputParser()
            result = chain.invoke({"query": query})
            queries = [q.strip() for q in result.strip().split("\n") if q.strip()]
            
            # Clean up potential numbering if LLM ignored the instruction
            cleaned_queries = []
            for q in queries:
                q_clean = q.lstrip("0123456789.-) ")
                if q_clean.startswith('"') and q_clean.endswith('"'):
                    q_clean = q_clean[1:-1]
                elif q_clean.startswith("'") and q_clean.endswith("'"):
                    q_clean = q_clean[1:-1]
                if q_clean:
                    cleaned_queries.append(q_clean)
                    
            # Include the original query as well
            if query not in cleaned_queries:
                cleaned_queries.insert(0, query)
            return cleaned_queries[:4]

        elif self.strategy == "hyde":
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert tax advisor. Write a short, hypothetical passage that directly answers the following query. Focus on technical details and relevant tax concepts. Do not explain that this is hypothetical; write it as if it were a direct excerpt from a tax law guide or textbook. Keep it under 3-4 sentences."),
                ("user", "{query}")
            ])
            chain = prompt | self.llm | StrOutputParser()
            hyde_doc = chain.invoke({"query": query}).strip()
            return [hyde_doc]

        return [query]
