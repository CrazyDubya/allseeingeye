#!/usr/bin/env python3
"""
AllSeeingEye Web Application Launcher
"""
import os
import sys
import argparse

def main():
    """
    Main entry point for AllSeeingEye Web Application.
    """
    parser = argparse.ArgumentParser(description='AllSeeingEye Web Application')
    parser.add_argument('--host', default='127.0.0.1', help='Host address to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--upload-dir', help='Directory to store uploads')
    args = parser.parse_args()
    
    # Configure environment for Flask
    if args.debug:
        os.environ['FLASK_ENV'] = 'development'
        os.environ['FLASK_DEBUG'] = '1'
    else:
        os.environ['FLASK_ENV'] = 'production'
        os.environ['FLASK_DEBUG'] = '0'
    
    # Set upload directory if specified
    if args.upload_dir:
        os.environ['ALLSEEINGEYE_UPLOAD_DIR'] = args.upload_dir
    
    # Import app here to ensure environment variables are set first
    from app import app
    
    # Run the Flask application
    app.run(host=args.host, port=args.port, debug=args.debug)

if __name__ == '__main__':
    main()