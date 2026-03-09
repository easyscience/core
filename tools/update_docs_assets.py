"""
Update documentation assets from the assets-branding repository.

This script fetches branding assets (logos, icons, images) from the
easyscience/assets-branding GitHub repository and copies them to the
appropriate locations in the documentation directory.
"""

import shutil
from pathlib import Path

import pooch

# Configuration: Define what to fetch and where to copy
GITHUB_REPO = 'easyscience/assets-branding'
GITHUB_BRANCH = 'master'
BASE_URL = f'https://raw.githubusercontent.com/{GITHUB_REPO}/refs/heads/{GITHUB_BRANCH}'
PROJECT_NAME = 'easyscience'

# Mapping of source files to destination paths
# Format: "source_path_in_repo": "destination_path_in_project"
ASSETS_MAP = {
    # Logos
    f'{PROJECT_NAME}/logos/dark.svg': 'docs/docs/assets/images/logo_dark.svg',
    f'{PROJECT_NAME}/logos/light.svg': 'docs/docs/assets/images/logo_light.svg',
    # Favicon
    f'{PROJECT_NAME}/icons/color.png': 'docs/docs/assets/images/favicon.png',
    # Icon overrides
    f'{PROJECT_NAME}/icons/bw.svg': f'docs/overrides/.icons/{PROJECT_NAME}.svg',
    'easyscience-org/icons/eso-icon_bw.svg': 'docs/overrides/.icons/easyscience.svg',
}


def fetch_and_copy_asset(
    source_path: str,
    dest_path: str,
    cache_dir: Path,
) -> None:
    """
    Fetch an asset from GitHub and copy it to the destination.

    Args:
        source_path: Path to the file in the GitHub repository
        dest_path: Destination path in the project
        cache_dir: Directory to cache downloaded files
    """
    url = f'{BASE_URL}/{source_path}'

    # Create a unique cache filename based on source path
    cache_filename = source_path.replace('/', '_')

    # Download file using pooch
    file_path = pooch.retrieve(
        url=url,
        known_hash=None,  # Skip hash verification
        path=cache_dir,
        fname=cache_filename,
    )

    # Create destination directory if it doesn't exist
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy the file to destination
    shutil.copy2(file_path, dest)
    print(f'Copied {file_path} -> {dest_path}')


def main():
    """Main function to update all documentation assets."""
    print('📥 Updating documentation assets...')
    print(f'   Repository: {GITHUB_REPO}')
    print(f'   Branch: {GITHUB_BRANCH}\n')

    # Use a temporary cache directory
    cache_dir = Path.home() / '.cache' / GITHUB_REPO
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Fetch and copy each asset
    for source_path, dest_path in ASSETS_MAP.items():
        try:
            fetch_and_copy_asset(source_path, dest_path, cache_dir)
            print()
        except Exception as e:
            print(f'❌ Failed to fetch {source_path}: {e}')

    print('\n✅ Documentation assets updated successfully!')


if __name__ == '__main__':
    main()
