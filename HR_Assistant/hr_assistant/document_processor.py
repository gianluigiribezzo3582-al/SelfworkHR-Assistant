# document_processor.py
import os
import uuid
import hashlib
import mimetypes
import tempfile
from zipfile import ZipFile
from config import Config
from semantic_chunking import SemanticChunking
from markitdown import MarkItDown

_md_converter = MarkItDown()


class DocumentProcessor:
    # Estensioni accettate per la sincronizzazione/upload, con relativa categoria
    SUPPORTED_EXTENSIONS = {
        ".txt": "text",
        ".pdf": "document",
        ".doc": "document",
        ".docx": "document",
        ".ppt": "presentation",
        ".pptx": "presentation",
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".html": "web",
        ".htm": "web",
        ".csv": "data",
        ".json": "data",
        ".xml": "data",
        # File di Archivio
        ".zip": "archive",
    }

    @staticmethod
    def read_first_lines(file_path, n_lines=100):
        """Restituisce le prime n righe non vuote del contenuto del file, convertito in
        markdown: funziona sia per file di testo semplice sia per formati binari
        (pdf, docx, xlsx...), da cui altrimenti non si potrebbe estrarre nulla."""
        content = DocumentProcessor._extract_content(file_path)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines[:n_lines]

    @staticmethod
    def get_file_hash(file_path):
        """Calcola l'hash MD5 del contenuto del file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def get_document_metadata(file_path):
        extension = os.path.splitext(file_path)[1].lower()
        return {
            "hash": DocumentProcessor.get_file_hash(file_path),
            "last_modified": os.path.getmtime(file_path),
            "source": os.path.basename(file_path),
            "file_type": DocumentProcessor.SUPPORTED_EXTENSIONS.get(extension, "unknown"),
            "mime_type": mimetypes.guess_type(file_path)[0] or "",
            "extension": extension,
        }

    @staticmethod
    def _convert_to_markdown(file_path):
        """Converte un file in markdown tramite MarkItDown, per uniformare l'estrazione
        del testo tra i diversi formati supportati (pdf, docx, pptx, xlsx, html, csv...)."""
        try:
            result = _md_converter.convert(file_path)
            return result.text_content
        except Exception as e:
            print(f"Errore nella conversione di {file_path}: {str(e)}")
            return ""

    @staticmethod
    def _process_zip_file(file_path):
        """Estrae un archivio zip e converte in markdown ogni file supportato al suo interno."""
        results = []
        with tempfile.TemporaryDirectory() as temp_dir:
            with ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        inner_path = os.path.join(root, file)
                        if os.path.splitext(file)[1].lower() in DocumentProcessor.SUPPORTED_EXTENSIONS:
                            content = DocumentProcessor._convert_to_markdown(inner_path)
                            if content:
                                results.append((file, content))
        return results

    @staticmethod
    def _extract_content(file_path):
        """Estrae il contenuto testuale (markdown) di un file supportato, gestendo anche
        gli archivi zip. Ritorna stringa vuota per estensioni non supportate."""
        extension = os.path.splitext(file_path)[1].lower()
        file_type = DocumentProcessor.SUPPORTED_EXTENSIONS.get(extension)

        if not file_type:
            return ""

        if file_type == "archive":
            content = ""
            for filename, zip_content in DocumentProcessor._process_zip_file(file_path):
                content += f"\n\nFile: {filename}\n{zip_content}"
            return content

        return DocumentProcessor._convert_to_markdown(file_path)

    @staticmethod
    def process_single_document(file_path):
        """Suddivide un singolo file in chunk semantici pronti per l'indicizzazione."""
        documents = []
        metadatas = []
        ids = []

        content = DocumentProcessor._extract_content(file_path)

        if content and not content.isspace():
            sc = SemanticChunking()
            chunks = sc.chunk_text(content)
            file_metadata = DocumentProcessor.get_document_metadata(file_path)

            for chunk in chunks:
                if not chunk.isspace() and not chunk == "":
                    documents.append(chunk)
                    metadatas.append(file_metadata)
                    ids.append(str(uuid.uuid4()))

        return documents, metadatas, ids

    @staticmethod
    def process_documents(db):
        """Sincronizza i CV in resumes/ con il database: aggiunge, aggiorna e rimuove
        solo cio' che e' effettivamente cambiato, usando l'hash MD5 come impronta."""
        current_files = {
            f: DocumentProcessor.get_document_metadata(
                os.path.join(Config.DOCUMENTS_DIR, f)
            )
            for f in os.listdir(Config.DOCUMENTS_DIR)
            if os.path.splitext(f)[1].lower() in DocumentProcessor.SUPPORTED_EXTENSIONS
            # Esclude file temporanei/di lock (es. "~$file.docx" creato da Word mentre il
            # documento e' aperto) e file nascosti, che non sono veri CV.
            and not f.startswith(("~$", "."))
        }

        existing_files = db.get_tracked_files()

        files_to_add = set(current_files.keys()) - set(existing_files.keys())
        files_to_remove = set(existing_files.keys()) - set(current_files.keys())
        files_to_update = {
            f
            for f in set(current_files.keys()) & set(existing_files.keys())
            if current_files[f]["hash"] != existing_files[f]["hash"]
        }

        for action, files in [("add", files_to_add), ("update", files_to_update)]:
            for filename in files:
                file_path = os.path.join(Config.DOCUMENTS_DIR, filename)
                documents, metadatas, ids = DocumentProcessor.process_single_document(
                    file_path
                )

                if action == "update":
                    db.remove_document_by_source(filename)

                if documents:
                    db.add_documents(documents, metadatas, ids)

        for filename in files_to_remove:
            db.remove_document_by_source(filename)

        return len(files_to_add), len(files_to_update), len(files_to_remove)
