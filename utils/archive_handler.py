#!/usr/bin/env python3
"""
Archive extraction utility for AllSeeingEye web application.
Handles various archive formats securely.
"""
import os
import shutil
import zipfile
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory


class ArchiveHandler:
    """
    Handles extraction of various archive formats for analysis.
    Supports security measures to prevent path traversal attacks.
    """
    
    @staticmethod
    def extract_archive(archive_path, target_dir):
        """
        Extract an archive to the target directory.
        
        Args:
            archive_path (str): Path to the archive file
            target_dir (str): Directory to extract to
            
        Returns:
            bool: True if extraction was successful, False otherwise
            
        Raises:
            ValueError: If the archive format is not supported
            OSError: If there are issues with file operations
        """
        archive_path = Path(archive_path)
        
        # Determine archive type by extension
        if archive_path.suffix.lower() == '.zip':
            return ArchiveHandler._extract_zip(archive_path, target_dir)
        elif archive_path.suffix.lower() in ('.tar', '.tgz', '.gz', '.bz2'):
            return ArchiveHandler._extract_tar(archive_path, target_dir)
        else:
            raise ValueError(f"Unsupported archive format: {archive_path.suffix}")
    
    @staticmethod
    def _extract_zip(zip_path, target_dir):
        """Extract a ZIP archive safely."""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Check for path traversal attacks
                for file_info in zip_ref.infolist():
                    file_path = Path(file_info.filename)
                    if file_path.is_absolute() or '..' in file_path.parts:
                        raise ValueError("Archive contains unsafe file paths")
                
                # Extract all files
                zip_ref.extractall(path=target_dir)
            return True
        except (zipfile.BadZipFile, OSError) as e:
            print(f"Error extracting ZIP file: {e}")
            return False
    
    @staticmethod
    def _extract_tar(tar_path, target_dir):
        """Extract a TAR archive safely."""
        try:
            # Determine the appropriate mode based on file extension
            mode = 'r'
            if tar_path.suffix.lower() == '.gz' or tar_path.name.endswith('.tar.gz') or tar_path.suffix.lower() == '.tgz':
                mode = 'r:gz'
            elif tar_path.suffix.lower() == '.bz2' or tar_path.name.endswith('.tar.bz2'):
                mode = 'r:bz2'
            
            with tarfile.open(tar_path, mode) as tar_ref:
                # Check for unsafe paths
                for member in tar_ref.getmembers():
                    if member.name.startswith('/') or '..' in member.name.split('/'):
                        raise ValueError("Archive contains unsafe file paths")
                
                # Filter out unsafe paths
                safe_members = [m for m in tar_ref.getmembers() 
                                if not m.name.startswith('/') and '..' not in m.name.split('/')]
                
                # Extract safe members
                for member in safe_members:
                    tar_ref.extract(member, path=target_dir)
            return True
        except (tarfile.ReadError, OSError) as e:
            print(f"Error extracting TAR file: {e}")
            return False

    @staticmethod
    def process_uploaded_archive(upload_path):
        """
        Process an uploaded archive by extracting it to a temporary directory.
        
        Args:
            upload_path (str): Path to the uploaded archive
            
        Returns:
            str: Path to the directory containing extracted files
            
        Raises:
            ValueError: If extraction fails
        """
        temp_dir = TemporaryDirectory(prefix="allseeingeye_")
        extract_dir = temp_dir.name
        
        try:
            success = ArchiveHandler.extract_archive(upload_path, extract_dir)
            if not success:
                raise ValueError("Failed to extract archive")
            
            # Find the "root" directory of the project
            # Often, archives contain a single top-level directory
            contents = os.listdir(extract_dir)
            if len(contents) == 1 and os.path.isdir(os.path.join(extract_dir, contents[0])):
                # If there's just one directory, use that as the root
                project_dir = os.path.join(extract_dir, contents[0])
            else:
                # Otherwise, use the extract directory as is
                project_dir = extract_dir
            
            return project_dir, temp_dir
        except Exception as e:
            # Clean up on error
            temp_dir.cleanup()
            raise ValueError(f"Error processing archive: {str(e)}")


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: archive_handler.py <archive_path>")
        sys.exit(1)
    
    archive_path = sys.argv[1]
    with TemporaryDirectory() as extract_dir:
        print(f"Extracting {archive_path} to {extract_dir}...")
        success = ArchiveHandler.extract_archive(archive_path, extract_dir)
        print(f"Extraction {'successful' if success else 'failed'}")
        if success:
            print("Extracted contents:")
            for root, dirs, files in os.walk(extract_dir):
                level = root.replace(extract_dir, '').count(os.sep)
                indent = ' ' * 4 * level
                print(f"{indent}{os.path.basename(root)}/")
                sub_indent = ' ' * 4 * (level + 1)
                for f in files:
                    print(f"{sub_indent}{f}")