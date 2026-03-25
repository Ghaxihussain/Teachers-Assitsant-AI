


# unstructured ---> structured the pdf --> chunk ---> embed -->store
from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import Image, Table
from unstructured_pytesseract import pytesseract
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text as unstructured_partition_text
from unstructured.partition.pdf import partition_pdf as unstructured_partition_pdf
from ..config.database import AsyncSessionLocal, Document, Instruction
import base64
from openai import OpenAI
from unstructured.documents.elements import Image, Table
from sqlalchemy import insert
from sqlalchemy import text, select
from unstructured.chunking.title import chunk_by_title
from dotenv import load_dotenv  
from pgvector.sqlalchemy import Vector
import asyncio
import requests
load_dotenv()
client = OpenAI()



def partition_txt_file(text_path: str) -> list:
    
    if text_path.startswith("http"):
        content = requests.get(text_path).text
    else:
        with open(text_path, "r") as f:
            content = f.read()
    
    elements = unstructured_partition_text(text=content)
    return elements


def partition_pdf_file(path: str) -> list:
    if path.startswith("http"):
        elements = unstructured_partition_pdf(
            url=path, 
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True   
        )
    else:
        elements = unstructured_partition_pdf(
            filename=path,  
            strategy="hi_res",
            infer_table_structure=True,
            extract_image_block_types=["Image"],
            extract_image_block_to_payload=True   
        )
    return elements




def chunk_data(type_file, path):
    els = None
    if type_file == "txt":
        els = partition_txt_file(path)
    elif type_file == "pdf":
        els= partition_pdf_file(path)
    
    chunks = chunk_by_title(
        els,
        max_characters=3000,
        new_after_n_chars=2400,
        combine_text_under_n_chars=500,
        include_orig_elements=True
    )
    return chunks
    

def extract_from_chunk(chunk) -> dict:
    result = {
        "text": chunk.text.strip(),
        "images": [],
        "tables": []
    }

    elements_to_check = chunk.metadata.orig_elements or []

    for el in elements_to_check:
        if isinstance(el, Image):
            b64 = getattr(el.metadata, "image_base64", None)
            if b64:
                result["images"].append(b64)

        elif isinstance(el, Table):
            html = getattr(el.metadata, "text_as_html", None)
            result["tables"].append(html if html else el.text)

    return result


def summarize_chunk(chunk_data: dict) -> str:

    content = []

    if chunk_data["text"]:
        content.append({
            "type": "text",
            "text": f"Here is the text content:\n{chunk_data['text']}"
        })
    for b64 in chunk_data["images"]:
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{b64}"
            }
        })

    for table_html in chunk_data["tables"]:
        content.append({
            "type": "text",
            "text": f"Here is a table from the document:\n{table_html}"
        })

    content.append({
        "type": "text",
        "text": "Summarize all the above content concisely. If there are images, describe what they show. If there are tables, summarize the data."
    })

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": content}],
        max_tokens=500
    )
    return response.choices[0].message.content


def get_chunk_output(chunk_data: dict) -> str:
    has_visuals = bool(chunk_data["images"] or chunk_data["tables"])

    if has_visuals:
        return summarize_chunk(chunk_data)
    else:
        return chunk_data["text"]


def embed_chunk(text: str) -> list[float]:
    response = client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def file_to_embedds(type_of_file: str, path: str) -> list[dict]:
    chunks = chunk_data(type_of_file, path)
    results = []

    for i, chunk in enumerate(chunks):
        extracted = extract_from_chunk(chunk)
        content_to_embed = get_chunk_output(extracted)

        results.append({
            "text": extracted["text"],
            "summary": content_to_embed,
            "images": len(extracted["images"]),
            "tables": extracted["tables"],
            "embedding": embed_chunk(content_to_embed),
            "source_file": path,                       
            "file_type": type_of_file,                          
            "chunk_index": i,                         
            "page_number": getattr(chunk.metadata, "page_number", None),  
        })

    return results
 
async def insert_to_vector_db(files_to_embed_returned_value):
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                insert(Document),
                files_to_embed_returned_value  # pass the whole list of dicts
            )


async def insertion_pipeline(type_file: str, path: str):
    print("Insertion started ..... ")
    await insert_to_vector_db((file_to_embedds(type_file, path)))
    print("Inserted")
    return True


async def insert_in_instructions(text: str):
    emd = embed_chunk(text)
    async with AsyncSessionLocal() as session:
        async with session.begin():
            await session.execute(
                insert(Instruction).values(text = text, embedding = emd)
            )

    return "Inserted the instruction"





async def rag_query(query: str) -> str:
    query_embedding = embed_chunk(query)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document.text)
            .order_by(Document.embedding.l2_distance(query_embedding))
            .limit(3)
        )
        chunks = result.fetchall()
    
    context = "\n\n".join([row[0] for row in chunks])
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Answer the question using only the provided context."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    
    return response.choices[0].message.content


async def rag_query(query: str) -> str:
    query_embedding = embed_chunk(query)
    
    async with AsyncSessionLocal() as session:

        doc_result = await session.execute(
            select(Document.text)
            .order_by(Document.embedding.l2_distance(query_embedding))
            .limit(3)
        )
        chunks = doc_result.fetchall()

        instr_result = await session.execute(
            select(Instruction.text)
            .order_by(Instruction.embedding.l2_distance(query_embedding))
            .limit(2)
        )
        instructions = instr_result.fetchall()

    context = "\n\n".join([row[0] for row in chunks])
    relevant_instructions = "\n".join([row[0] for row in instructions])

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"You are a teacher assistant.\n\nRelevant instructions:\n{relevant_instructions}"},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
        ]
    )
    return response.choices[0].message.content



# files_to_embed ---> insert_to_vector_db 



# direct insert use insertion_pipeline


# for output, use rag_query



# print(asyncio.run(rag_query("what is FPGA?")))