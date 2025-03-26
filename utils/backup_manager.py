import os
import shutil
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class BackupManager:
    """Manages backup operations for the quiz bot."""
    
    def __init__(self, backup_dir=None):
        """Initialize the backup manager.
        
        Args:
            backup_dir: Directory to store backups. Defaults to '.history'.
        """
        self.backup_dir = backup_dir or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.history')
        os.makedirs(self.backup_dir, exist_ok=True)
        logger.info(f"BackupManager initialized with backup directory: {self.backup_dir}")
    
    def backup_file(self, file_path):
        """Create a backup of the specified file.
        
        Args:
            file_path: Path to the file to backup.
            
        Returns:
            Path to the backup file or None if backup failed.
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Cannot backup non-existent file: {file_path}")
                return None
                
            # Create backup filename with timestamp
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f"{name}_{timestamp}{ext}"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copy the file
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup of {file_path} at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to backup {file_path}: {str(e)}", exc_info=True)
            return None
    
    def get_latest_backup(self, original_filename):
        """Get the path to the latest backup of a file.
        
        Args:
            original_filename: The original filename to find backups for.
            
        Returns:
            Path to the latest backup or None if no backups exist.
        """
        try:
            name, ext = os.path.splitext(os.path.basename(original_filename))
            backup_pattern = f"{name}_*{ext}"
            
            # Find all matching backups
            backups = []
            for filename in os.listdir(self.backup_dir):
                if filename.startswith(name + '_') and filename.endswith(ext):
                    backups.append(os.path.join(self.backup_dir, filename))
            
            if not backups:
                return None
                
            # Return the most recent backup (based on modification time)
            return max(backups, key=os.path.getmtime)
        except Exception as e:
            logger.error(f"Failed to get latest backup for {original_filename}: {str(e)}", exc_info=True)
            return None
