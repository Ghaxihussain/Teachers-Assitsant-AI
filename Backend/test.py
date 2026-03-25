

import asyncio
from .rag.input_pipeline import rag_query

result = asyncio.run(rag_query("what is the prof name?"))
print(result)