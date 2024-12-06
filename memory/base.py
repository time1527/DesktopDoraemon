import os
from abc import ABC
import shutil
from typing import Union,Optional, Dict
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings


from log import logger
from settings import WORK_DIR
from utils.utils import get_file_type,read_text_from_file
    

class BaseMemory(ABC):
    """
    load -> chunk -> embedding -> store 
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg = cfg or {}

        # files:Path or [Path] -> [str]
        self.files = self.cfg.get('files',[])
        if not isinstance(self.files,list):
            self.files = [self.files]
        self.files = list(map(lambda x:os.path.abspath(str(x)),self.files))

        # embedding
        self.embedding_cfg = self.cfg.get('embedding_cfg')
        self.embedding_cfg["model_name"] = os.path.abspath(self.embedding_cfg["model_name"])

        # vector_store
        self.vector_store_path = self.cfg.get('vector_store_path')
        self._load_vector_store()
    
    def _files_to_docs(self) -> Union[list[Document],Document]:
        """
        load and chunk
        """
        docs = []
        for file in self.files:
            file_type = get_file_type(file)

            if file_type == 'txt':
                from langchain_community.document_loaders import TextLoader
                loader = TextLoader(file)
                doc = loader.load()
            elif file_type == "pdf":
                from langchain_community.document_loaders import PyPDFLoader
                loader = PyPDFLoader(file).load()
                doc = loader.load()
            elif file_type == "md":
                doc = read_text_from_file(file)
            # TODO: other loader 
            else:
                logger.warning(f"Unsupported file type: {file_type}")
            
            doc = self._chunk(doc,file_type)
            docs.extend(doc)
        return docs

    def _chunk(self,docs,type):
        if type == "md":
            from langchain.text_splitter import MarkdownHeaderTextSplitter
            headers_to_split_on = [("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3"), ("####", "Header 4")]
            text_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
            docs = text_splitter.split_text(docs)

            def add_metadata(x:Document):
                x.page_content = " ".join(list(x.metadata.values()) + [x.page_content])
                return x

            docs = list(map(lambda x:add_metadata(x),docs))
        else:
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=200,
                chunk_overlap=50
            )
            docs = text_splitter.split_documents(docs)
        return docs
    
    def _load_vector_store(self) -> None:
        assert (self.vector_store_path and 
                os.path.exists(self.vector_store_path) and 
                os.path.isdir(self.vector_store_path)) or self.files

        # 有向量库路径 且 存在 -> 从向量库加载
        if self.vector_store_path and \
          os.path.exists(self.vector_store_path) and \
          os.path.isdir(self.vector_store_path):
            self.vector_store = FAISS.load_local(
                self.vector_store_path,
                HuggingFaceEmbeddings(**self.embedding_cfg),
                allow_dangerous_deserialization=True
            )
            return
        elif self.files:
            docs = self._files_to_docs()
            self.vector_store = FAISS.from_documents(
                docs,
                HuggingFaceEmbeddings(**self.embedding_cfg)
            )
            path = self.vector_store_path if self.vector_store_path else WORK_DIR / 'vector_store'
            shutil.rmtree(path,ignore_errors=True)
            self.vector_store.save_local(path)
            self.vector_store_path = path