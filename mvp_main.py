#!/usr/bin/env python3
"""
MVP Entry Point for AI Arts Competition Style Evaluation
Focuses on batch processing with Gemini-only mode and multi-rubric support.
"""

import asyncio
import uvicorn
from src.mvp_api import app

async def start_mvp_server(host: str = "0.0.0.0", port: int = 8001):
    """Start the MVP web server."""
    print("🎨 Starting AI Arts Evaluation MVP...")
    print(f"🌐 Web Interface: http://{host}:{port}/")
    print(f"📊 Batch Processing: Upload multiple files with multiple rubrics")
    print(f"🤖 AI Model: Gemini Pro Vision (multimodal)")
    print(f"📈 UI Style: AI Arts Competition layout")
    print("\n" + "="*60)
    print("MVP Features:")
    print("✅ Multi-rubric evaluation per submission")
    print("✅ Batch processing for multiple submissions")
    print("✅ Gemini-only mode for all media")
    print("✅ AI Arts Competition style UI")
    print("✅ Left image, right scores layout")
    print("="*60 + "\n")
    
    config = uvicorn.Config(
        app, 
        host=host, 
        port=port, 
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        asyncio.run(start_mvp_server())
    else:
        print("🎨 AI Arts Evaluation MVP")
        print("\nUsage:")
        print("  python mvp_main.py serve    # Start the MVP web server")
        print("\nFeatures:")
        print("  • Multi-rubric evaluation")
        print("  • Batch processing")
        print("  • Gemini-only mode")
        print("  • AI Arts Competition UI")

if __name__ == "__main__":
    main()
