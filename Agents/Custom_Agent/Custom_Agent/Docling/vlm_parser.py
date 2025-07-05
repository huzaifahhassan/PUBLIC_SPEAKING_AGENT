import os

from docling.datamodel import vlm_model_specs
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    VlmPipelineOptions,
)
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.pipeline.vlm_pipeline import VlmPipeline

pipeline_options = VlmPipelineOptions(
    vlm_options=vlm_model_specs.SMOLDOCLING_TRANSFORMERS,
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            pipeline_cls=VlmPipeline,
            pipeline_options=pipeline_options,
        ),
    }
)

# change current working directory to the location of the sample PDF
os.chdir("Agents/Custom_Agent/Custom_Agent/Docling")

# Document parser function
def doc_parser(source: str):
    source = source + ".pdf" if not source.endswith(".pdf") else source
    markdown_doc = converter.convert(source=source).document.export_to_markdown()
    print("Parsed Document Markdown: " , markdown_doc)
    # Saving Script to File
    text_file = open("Markdown.txt", "w")
    text_file.write(markdown_doc)
    text_file.close()
    return markdown_doc





