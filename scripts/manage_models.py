import os
import shutil
import json
from datetime import datetime

class ModelVersionManager:
    def __init__(self, base_path='models'):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def create_version(self, version_name, artifacts, metadata):
        """
        Creates a new version directory and copies artifacts.
        artifacts: list of paths to files
        metadata: dict of metrics/params
        """
        version_dir = os.path.join(self.base_path, version_name)
        if os.path.exists(version_dir):
            print(f"Version {version_name} already exists. Overwriting...")
            shutil.rmtree(version_dir)
        
        os.makedirs(version_dir)
        
        # Copy artifacts
        for artifact in artifacts:
            if os.path.exists(artifact):
                shutil.copy(artifact, version_dir)
            else:
                print(f"Warning: Artifact {artifact} not found.")
        
        # Save metadata
        metadata['version'] = version_name
        metadata['timestamp'] = datetime.now().isoformat()
        with open(os.path.join(version_dir, 'metadata.json'), 'w') as f:
            json.dump(metadata, f, indent=4)
            
        print(f"Version {version_name} created successfully at {version_dir}")

    def promote_to_latest(self, version_name):
        """Updates the 'latest' symlink or directory to point to the specified version."""
        latest_dir = os.path.join(self.base_path, 'latest')
        version_dir = os.path.join(self.base_path, version_name)
        
        if not os.path.exists(version_dir):
            raise ValueError(f"Version {version_name} does not exist.")
            
        if os.path.exists(latest_dir):
            if os.path.islink(latest_dir):
                os.unlink(latest_dir)
            else:
                shutil.rmtree(latest_dir)
                
        # On Windows, symlinks require admin or specific settings, so we copy instead for robustness
        # in this environment, or use directory junctions. For now, let's copy to be safe.
        shutil.copytree(version_dir, latest_dir)
        print(f"Promoted version {version_name} to 'latest'.")

    def list_versions(self):
        """Lists all available model versions."""
        versions = [d for d in os.listdir(self.base_path) if os.path.isdir(os.path.join(self.base_path, d))]
        return sorted(versions)

if __name__ == "__main__":
    manager = ModelVersionManager()
    print("Available versions:", manager.list_versions())
