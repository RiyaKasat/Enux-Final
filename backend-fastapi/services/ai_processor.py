import google.generativeai as genai
import os
import json
import asyncio
from typing import List, Dict, Any

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    model = None

PLAYBOOK_ASSET_TYPES = [
    "goal",
    "strategy", 
    "timeline",
    "faq",
    "task",
    "process",
    "template",
    "checklist",
    "resource",
    "metric"
]

async def process_content_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process content blocks with AI to categorize and suggest asset mappings"""
    
    if not model:
        # Fallback processing without AI
        return await fallback_process_blocks(blocks)
    
    processed_blocks = []
    
    # Process blocks in batches to avoid API limits
    batch_size = 5
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i + batch_size]
        
        try:
            batch_results = await process_batch_with_ai(batch)
            processed_blocks.extend(batch_results)
        except Exception as e:
            print(f"AI processing failed for batch {i}: {e}")
            # Fallback to basic processing for this batch
            fallback_results = await fallback_process_blocks(batch)
            processed_blocks.extend(fallback_results)
        
        # Add small delay to respect API limits
        await asyncio.sleep(0.5)
    
    return processed_blocks

async def process_batch_with_ai(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a batch of blocks with Gemini AI"""
    
    # Prepare the prompt
    blocks_text = []
    for i, block in enumerate(blocks):
        blocks_text.append(f"Block {i+1} ({block['type']}):\n{block['content']}\n")
    
    prompt = f"""
    You are an AI assistant that categorizes business content into playbook assets.
    
    Available asset types: {', '.join(PLAYBOOK_ASSET_TYPES)}
    
    For each content block below, suggest the most appropriate asset type and provide a confidence score (0.0-1.0).
    
    Content blocks:
    {chr(10).join(blocks_text)}
    
    Respond in JSON format with an array of objects, each containing:
    - "block_index": the block number (1-based)
    - "suggested_asset_type": one of the available asset types
    - "confidence_score": float between 0.0 and 1.0
    - "reasoning": brief explanation of the classification
    
    Example:
    [
        {{
            "block_index": 1,
            "suggested_asset_type": "goal",
            "confidence_score": 0.9,
            "reasoning": "This block describes a specific business objective"
        }}
    ]
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Extract JSON from response
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        ai_results = json.loads(response_text)
        
        # Merge AI results with original blocks
        processed_blocks = []
        for i, block in enumerate(blocks):
            # Find corresponding AI result
            ai_result = next(
                (r for r in ai_results if r.get("block_index") == i + 1),
                None
            )
            
            processed_block = {
                **block,
                "suggested_asset_type": ai_result.get("suggested_asset_type") if ai_result else "resource",
                "confidence_score": ai_result.get("confidence_score", 0.7) if ai_result else 0.7,
                "ai_reasoning": ai_result.get("reasoning") if ai_result else None
            }
            
            processed_blocks.append(processed_block)
        
        return processed_blocks
    
    except Exception as e:
        print(f"AI processing error: {e}")
        # Fallback to basic processing
        return await fallback_process_blocks(blocks)

async def fallback_process_blocks(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Fallback processing without AI using keyword-based classification"""
    
    # Define keyword mappings for asset types
    asset_keywords = {
        "goal": ["goal", "objective", "target", "aim", "vision", "mission"],
        "strategy": ["strategy", "approach", "plan", "method", "framework"],
        "timeline": ["timeline", "schedule", "deadline", "milestone", "phase"],
        "faq": ["faq", "question", "answer", "q&a", "frequently asked"],
        "task": ["task", "action", "step", "todo", "activity", "deliverable"],
        "process": ["process", "procedure", "workflow", "flow", "steps"],
        "template": ["template", "format", "example", "sample", "boilerplate"],
        "checklist": ["checklist", "check", "verify", "ensure", "confirm"],
        "resource": ["resource", "tool", "link", "reference", "documentation"],
        "metric": ["metric", "kpi", "measure", "track", "analytics", "data"]
    }
    
    processed_blocks = []
    
    for block in blocks:
        content_lower = block["content"].lower()
        
        # Score each asset type based on keyword matches
        scores = {}
        for asset_type, keywords in asset_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                scores[asset_type] = score / len(keywords)
        
        # Determine best match
        if scores:
            best_asset_type = max(scores.items(), key=lambda x: x[1])
            suggested_asset_type = best_asset_type[0]
            confidence_score = min(0.8, best_asset_type[1] * 2)  # Cap at 0.8 for fallback
        else:
            # Default classification based on block type
            if block["type"] == "heading":
                suggested_asset_type = "goal"
                confidence_score = 0.6
            elif "list" in block["type"]:
                suggested_asset_type = "checklist"
                confidence_score = 0.7
            else:
                suggested_asset_type = "resource"
                confidence_score = 0.5
        
        processed_block = {
            **block,
            "suggested_asset_type": suggested_asset_type,
            "confidence_score": confidence_score,
            "processing_method": "fallback"
        }
        
        processed_blocks.append(processed_block)
    
    return processed_blocks

async def generate_embeddings(text: str) -> List[float]:
    """Generate embeddings for text content"""
    # This would integrate with embedding service (OpenAI, etc.)
    # For now, return dummy embeddings
    return [0.0] * 1536  # Standard embedding dimension

async def enhance_block_with_ai(block: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance a single block with additional AI insights"""
    
    if not model:
        return block
    
    prompt = f"""
    Analyze this business content block and provide insights:
    
    Type: {block['type']}
    Content: {block['content']}
    
    Provide:
    1. A concise summary (max 100 chars)
    2. Key topics or tags (max 5)
    3. Suggested improvements or completions
    
    Respond in JSON format:
    {{
        "summary": "brief summary",
        "tags": ["tag1", "tag2"],
        "suggestions": ["suggestion1", "suggestion2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        if response_text.startswith('```json'):
            response_text = response_text[7:-3]
        elif response_text.startswith('```'):
            response_text = response_text[3:-3]
        
        ai_insights = json.loads(response_text)
        
        return {
            **block,
            "ai_summary": ai_insights.get("summary"),
            "ai_tags": ai_insights.get("tags", []),
            "ai_suggestions": ai_insights.get("suggestions", [])
        }
    
    except Exception as e:
        print(f"AI enhancement error: {e}")
        return block
