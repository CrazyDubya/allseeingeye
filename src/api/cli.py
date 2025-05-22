#!/usr/bin/env python3
"""
Command-line interface for the AllSeeingEye API server
"""

import argparse
import uvicorn
import os
import sys

def main():
    """Main entry point for the API server CLI"""
    parser = argparse.ArgumentParser(description="AllSeeingEye API Server")
    
    parser.add_argument(
        "--host", 
        type=str, 
        default="127.0.0.1", 
        help="Host address to bind to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port", 
        type=int, 
        default=8000, 
        help="Port to bind to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload", 
        action="store_true", 
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--workers", 
        type=int, 
        default=1, 
        help="Number of worker processes (default: 1)"
    )
    
    parser.add_argument(
        "--log-level", 
        type=str, 
        default="info", 
        choices=["debug", "info", "warning", "error", "critical"],
        help="Log level (default: info)"
    )
    
    args = parser.parse_args()
    
    print(f"Starting AllSeeingEye API server on {args.host}:{args.port}...")
    print(f"Documentation will be available at http://{args.host}:{args.port}/docs")
    
    # Run the API server
    uvicorn.run(
        "src.api.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()
