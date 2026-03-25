from fastapi import APIRouter, UploadFile, File, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional
from ..rag.input_pipeline import insert_in_instructions, insertion_pipeline
from ..aws import get_s3_url, upload_s3, delete_file, get_all_s3_files
import os
from dotenv import load_dotenv, find_dotenv
from ..config.database import AsyncSessionLocal, Document, Instruction
from sqlalchemy import delete, select
load_dotenv()



router = APIRouter(prefix="/teacher", tags = ["Teacher APIs"])




@router.post("/upload")
async def uplaod_content(instruction: Optional[str] = None, file: Optional[UploadFile] = File(None)):

    if instruction is None and file is None:
        raise HTTPException(status_code= status.HTTP_204_NO_CONTENT, detail= "NO content provided")
    

    if instruction:
        await insert_in_instructions(instruction)
        return JSONResponse(status_code= status.HTTP_201_CREATED, content= "The intruction has been added")

    if file:

        name = file.filename
        upload_s3(file)
        if name.endswith(".txt"):
            await insertion_pipeline(type_file= "txt", path = get_s3_url(file.filename))
        elif name.endswith(".pdf"):
            await insertion_pipeline(type_file= "pdf", path = get_s3_url(file.filename))


    print("Done")
    return JSONResponse(status_code= status.HTTP_201_CREATED, content= "The file has been added")

        

@router.delete("/delete/file/{filename}")
async def deletefile(filename: str):
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                delete(Document).where(Document.source_file.contains(f"rag_uploads/{filename}"))
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    delete_file(filename=filename)
    
    return JSONResponse(status_code=status.HTTP_200_OK, content="File deleted")


@router.delete("/delete/instruction/{id}")
async def delete_instruction(id: int):
    
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                delete(Instruction).where(Instruction.id == int(id))
            )
            if result.rowcount == 0:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="id not found")
    
    return JSONResponse(status_code=status.HTTP_200_OK, content="File deleted")

@router.get("/instructions")
async def get_all_instructions():
    async with AsyncSessionLocal() as session:
        async with session.begin():
            result = await session.execute(
                select(Instruction.id, Instruction.text)
            )
            rows = result.fetchall()

    return {row[0]: row[1] for row in rows}



@router.get("/files")
async def get_all_files():

    return get_all_s3_files()
