import os
import requests
import asyncio
from typing import Dict, List, Any
import PyPDF2
import docx
from bs4 import BeautifulSoup
import io

async def extract_content_from_file(file_path: str, mime_type: str) -> Dict[str, Any]:
    """Extract content from uploaded file"""
    
    if mime_type == "application/pdf":
        return await extract_from_pdf(file_path)
    elif mime_type == "text/plain":
        return await extract_from_text(file_path)
    elif mime_type == "text/markdown":
        return await extract_from_markdown(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return await extract_from_docx(file_path)
    else:
        # Fallback to text extraction
        return await extract_from_text(file_path)

async def extract_from_pdf(file_path: str) -> Dict[str, Any]:
    """Extract content from PDF file"""
    blocks = []
    
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    # Split into paragraphs
                    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
                    
                    for i, paragraph in enumerate(paragraphs):
                        blocks.append({
                            "type": "paragraph",
                            "content": paragraph,
                            "page": page_num + 1,
                            "paragraph_index": i,
                            "confidence_score": 0.9
                        })
    
    except Exception as e:
        raise Exception(f"Failed to extract from PDF: {str(e)}")
    
    return {
        "source_type": "pdf",
        "blocks": blocks,
        "total_blocks": len(blocks)
    }

async def extract_from_text(file_path: str) -> Dict[str, Any]:
    """Extract content from text file"""
    blocks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # Split by double newlines (paragraphs)
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            for i, paragraph in enumerate(paragraphs):
                # Detect if it's a heading (all caps, short, or starts with #)
                if (len(paragraph) < 100 and 
                    (paragraph.isupper() or paragraph.startswith('#'))):
                    block_type = "heading"
                else:
                    block_type = "paragraph"
                
                blocks.append({
                    "type": block_type,
                    "content": paragraph,
                    "index": i,
                    "confidence_score": 0.95
                })
    
    except Exception as e:
        raise Exception(f"Failed to extract from text file: {str(e)}")
    
    return {
        "source_type": "text",
        "blocks": blocks,
        "total_blocks": len(blocks)
    }

async def extract_from_markdown(file_path: str) -> Dict[str, Any]:
    """Extract content from markdown file"""
    blocks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            
            current_block = ""
            current_type = "paragraph"
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('#'):
                    # Save previous block
                    if current_block.strip():
                        blocks.append({
                            "type": current_type,
                            "content": current_block.strip(),
                            "confidence_score": 0.95
                        })
                    
                    # Start new heading block
                    current_block = line
                    current_type = "heading"
                    
                elif line.startswith('-') or line.startswith('*'):
                    # Save previous block
                    if current_block.strip() and current_type != "list":
                        blocks.append({
                            "type": current_type,
                            "content": current_block.strip(),
                            "confidence_score": 0.95
                        })
                        current_block = ""
                    
                    current_type = "list"
                    current_block += line + "\n"
                    
                elif line == "":
                    # End current block
                    if current_block.strip():
                        blocks.append({
                            "type": current_type,
                            "content": current_block.strip(),
                            "confidence_score": 0.95
                        })
                        current_block = ""
                        current_type = "paragraph"
                        
                else:
                    current_block += line + "\n"
            
            # Save final block
            if current_block.strip():
                blocks.append({
                    "type": current_type,
                    "content": current_block.strip(),
                    "confidence_score": 0.95
                })
    
    except Exception as e:
        raise Exception(f"Failed to extract from markdown: {str(e)}")
    
    return {
        "source_type": "markdown",
        "blocks": blocks,
        "total_blocks": len(blocks)
    }

async def extract_from_docx(file_path: str) -> Dict[str, Any]:
    """Extract content from Word document"""
    blocks = []
    
    try:
        doc = docx.Document(file_path)
        
        for i, paragraph in enumerate(doc.paragraphs):
            if paragraph.text.strip():
                # Detect heading style
                if paragraph.style.name.startswith('Heading'):
                    block_type = "heading"
                else:
                    block_type = "paragraph"
                
                blocks.append({
                    "type": block_type,
                    "content": paragraph.text.strip(),
                    "style": paragraph.style.name,
                    "index": i,
                    "confidence_score": 0.9
                })
    
    except Exception as e:
        raise Exception(f"Failed to extract from DOCX: {str(e)}")
    
    return {
        "source_type": "docx",
        "blocks": blocks,
        "total_blocks": len(blocks)
    }

async def extract_content_from_url(url: str) -> Dict[str, Any]:
    """Extract content from URL"""
    
    try:
        # Use requests instead of aiohttp for compatibility
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch URL: HTTP {response.status_code}")
        
        content = response.text
        content_type = response.headers.get('content-type', '').lower()
        
        if 'html' in content_type:
            return await extract_from_html(content, url)
        else:
            # Treat as plain text
            return await extract_from_text_content(content, url)
    
    except Exception as e:
        raise Exception(f"Failed to extract from URL {url}: {str(e)}")

async def extract_from_html(html_content: str, url: str) -> Dict[str, Any]:
    """Extract content from HTML"""
    blocks = []
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header"]):
            element.decompose()
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if heading.get_text().strip():
                blocks.append({
                    "type": "heading",
                    "content": heading.get_text().strip(),
                    "level": heading.name,
                    "confidence_score": 0.9
                })
        
        # Extract paragraphs
        for paragraph in soup.find_all('p'):
            text = paragraph.get_text().strip()
            if text and len(text) > 20:  # Filter out very short paragraphs
                blocks.append({
                    "type": "paragraph",
                    "content": text,
                    "confidence_score": 0.85
                })
        
        # Extract lists
        for list_element in soup.find_all(['ul', 'ol']):
            list_items = [li.get_text().strip() for li in list_element.find_all('li')]
            if list_items:
                blocks.append({
                    "type": "list",
                    "content": "\n".join(f"- {item}" for item in list_items),
                    "confidence_score": 0.9
                })
    
    except Exception as e:
        raise Exception(f"Failed to parse HTML: {str(e)}")
    
    return {
        "source_type": "html",
        "source_url": url,
        "blocks": blocks,
        "total_blocks": len(blocks)
    }

async def extract_from_text_content(text_content: str, url: str) -> Dict[str, Any]:
    """Extract content from plain text"""
    blocks = []
    
    # Split by double newlines (paragraphs)
    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
    
    for i, paragraph in enumerate(paragraphs):
        blocks.append({
            "type": "paragraph",
            "content": paragraph,
            "index": i,
            "confidence_score": 0.8
        })
    
    return {
        "source_type": "text",
        "source_url": url,
        "blocks": blocks,
        "total_blocks": len(blocks)
    }
