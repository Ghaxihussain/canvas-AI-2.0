from sqlalchemy import Column, String, Text, TIMESTAMP, ForeignKey, insert, select, delete, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from uuid import uuid4
import re
from .database import Base
import openai
import os
from dotenv import load_dotenv
load_dotenv()
EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_DIM = 1536

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class RagStore(Base):
    __tablename__ = "rag_store"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    class_id = Column(UUID(as_uuid=True), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String, nullable=True)
    source_type = Column(String, nullable=False)          
    source_id = Column(UUID(as_uuid=True), nullable=True) 
    source_name = Column(String, nullable=True)           
    source_file_key = Column(String, nullable=True)
    content = Column(Text, nullable=False)               
    embedding = Column(Vector(VECTOR_DIM), nullable=False)
    extra_metadata = Column(JSONB, nullable=True)               
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            "rag_store_embedding_idx",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"embedding": "vector_cosine_ops"}
        ),
    )


    @classmethod
    def get_embedding(cls, text):
        try:
            response = openai_client.embeddings.create(
                input=text,
                model=EMBEDDING_MODEL
            )
            return {"input": response.usage.prompt_tokens,"output": 0,  "embedding": response.data[0].embedding}
        except Exception as e:
            print(e)
            return None

    @classmethod
    def create(cls, class_id, uploaded_by, source_type, content, embedding, db,
            source_id=None, source_name=None, source_file_key=None, extra_metadata=None):

        try:
            title = re.search(r'<title>(.*?)</title>', content).group(1).strip()
            content_in = re.search(r'<content>(.*?)</content>', content, re.DOTALL).group(1).strip()
            
            if embedding is None:
                return None
            
            db.execute(insert(cls).values(
                class_id=class_id,
                uploaded_by=uploaded_by,
                source_type=source_type,
                source_id=source_id,
                source_name=source_name,
                title = title,
                source_file_key=source_file_key,
                content=content_in,
                embedding=embedding,
                extra_metadata=extra_metadata
            ))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None
        

    @classmethod
    def create_all(cls, class_id, uploaded_by, source_type, chunks, embeddings, db,
            source_id=None, source_name=None, source_file_key=None, extra_metadata=None):
        if len(chunks) == len(embeddings):
            for i in range(len(chunks)):
                try:
                    title = re.search(r'<title>(.*?)</title>', chunks[i]).group(1).strip()
                    content_in = re.search(r'<content>(.*?)</content>', chunks[i], re.DOTALL).group(1).strip()
                    
                    if embeddings[i] is None:
                        print(f"Chunk {i} is None")
                        continue
                    
                    db.execute(insert(cls).values(
                        class_id=class_id,
                        uploaded_by=uploaded_by,
                        source_type=source_type,
                        source_id=source_id,
                        source_name=source_name,
                        title = title,
                        source_file_key=source_file_key,
                        content=content_in,
                        embedding=embeddings[i],
                        extra_metadata={"chunk_index": i}
                    ))
                    db.commit()
                   
                except Exception as e:
                    db.rollback()
                    print(e)
                
                print(f"Chunk {i} success")
            return True
        else:
            return "chunk, embeddings size mismatched"
        


    @classmethod
    def get_by_id(cls, rag_id, db):
        try:
            return db.execute(
                select(cls).where(cls.id == rag_id)
            ).scalar_one_or_none()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def get_by_class_id(cls, class_id, db):
        try:
            return db.execute(
                select(cls).where(cls.class_id == class_id)
            ).scalars().all()
        except Exception as e:
            print(e)
            return None

    @classmethod
    def delete_by_id(cls, rag_id, db):
        try:
            chunk = cls.get_by_id(rag_id, db)
            if chunk is None:
                return False

            db.execute(delete(cls).where(cls.id == rag_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None

    @classmethod
    def delete_by_source_id(cls, source_id, db):
        """Delete all chunks belonging to a specific document/assignment/etc."""
        try:
            db.execute(delete(cls).where(cls.source_id == source_id))
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            print(e)
            return None


    @classmethod
    def search(cls, query, class_id, db, top_k=5):
        try:
            embedding_response = cls.get_embedding(query)
            if embedding_response is None:
                return None

            query_embedding = embedding_response["embedding"]
            input_tokens = embedding_response["input"]

            results = db.execute(
                select(cls)
                .where(cls.class_id == class_id)
                .order_by(cls.embedding.cosine_distance(query_embedding))
                .limit(top_k)
            ).scalars().all()

            return {"results": results, "input": input_tokens, "output": 0}
        except Exception as e:
            print(e)
            return None