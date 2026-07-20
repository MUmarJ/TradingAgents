import chromadb
from chromadb.config import Settings
from openai import OpenAI

# text-embedding-3-small has 8192 token limit (~32K chars)
# Use conservative limit for the summary
MAX_EMBEDDING_CHARS = 6000

SUMMARIZE_PROMPT = """Summarize this financial analysis into a concise situation description (max 500 words) that captures the key market conditions, sentiment, risks, and fundamentals. Focus on actionable insights that would help identify similar situations in the future:

{text}

Summary:"""


class FinancialSituationMemory:
    def __init__(self, name, config, persistent_dir=None, scope=None):
        """Initialize memory with optional ticker-based scoping.

        Args:
            name: Base collection name (e.g. "bull_memory")
            config: Configuration dictionary
            persistent_dir: Optional path for persistent ChromaDB storage
            scope: Optional scope prefix (e.g. ticker symbol) to isolate
                   collections between different analyses. When provided,
                   collection name becomes "{scope}_{name}".
        """
        if config["backend_url"] == "http://localhost:11434/v1":
            self.embedding = "nomic-embed-text"
            self.llm_model = "llama3"
        else:
            self.embedding = "text-embedding-3-small"
            self.llm_model = "gpt-4o-mini"
        self.client = OpenAI(base_url=config["backend_url"])

        if persistent_dir:
            self.chroma_client = chromadb.PersistentClient(path=persistent_dir)
        else:
            self.chroma_client = chromadb.Client(Settings(allow_reset=True))

        # Scope collection name to prevent cross-contamination between tickers
        collection_name = f"{scope}_{name}" if scope else name
        self.situation_collection = self.chroma_client.get_or_create_collection(name=collection_name)

    def _summarize_for_embedding(self, text: str) -> str:
        """Summarize long text to fit within embedding model's context limit."""
        if len(text) <= MAX_EMBEDDING_CHARS:
            return text

        # Use LLM to create a meaningful summary
        try:
            response = self.client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": SUMMARIZE_PROMPT.format(text=text[:50000])}],
                max_tokens=800,
                temperature=0.3,
            )
            summary = response.choices[0].message.content
            return summary if summary else text[:MAX_EMBEDDING_CHARS]
        except Exception as e:
            # Fallback to truncation if summarization fails
            print(f"MEMORY: Summarization failed ({e}), using truncation")
            return text[:MAX_EMBEDDING_CHARS]

    def get_embedding(self, text):
        """Get OpenAI embedding for a text"""
        # Summarize if text is too long
        processed_text = self._summarize_for_embedding(text)

        response = self.client.embeddings.create(
            model=self.embedding, input=processed_text
        )
        return response.data[0].embedding

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
