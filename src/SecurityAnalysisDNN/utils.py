import importlib.util
import os
import sys
from pathlib import Path


def getResourcePath(relativePath: str, packageName: str) -> Path:
    """Resolves a relative path to a package resource.
    This function attempts to be robust to the following cases:

    - Case 1: The package is installed into the current environment as either a full or editable install.
    - Case 2: The package is being run from source. This case assumes a src-layout package structure,
        i.e., `/<project-root>/src/<packageName>/<relativePath>`.
    - Case 3: The package is bundled as part of an EXE created by PyInstaller,
        and will unpack to locations stored in the `_MEIPASS`/`_MEIPASS2` environment variables.

    Args:
        relativePath (str): Path to resource, relative to the specified package (including filename and extension).
        packageName (str): Package name.

    Raises:
        `ModuleNotFoundError`: Raised when the specified package cannot be found.
        `FileNotFoundError`: Raised if the specified resource file cannot be found.

    Returns:
        Path: Absolute path to package resource.
    """
    try:
        packageSpec = importlib.util.find_spec(packageName)  # Get path to parent package
        if packageSpec is None:  # Package is not installed, likely running from source
            packageSpec = importlib.util.find_spec("src." + packageName)
        if packageSpec is None:  # Package doesn't exist, or project doesn't use src-layout
            raise ModuleNotFoundError(packageName)
        resourcePath = Path(packageSpec.submodule_search_locations[0]) / relativePath
        if not resourcePath.is_file():
            raise FileNotFoundError(str(resourcePath))
        return resourcePath

    except ModuleNotFoundError:
        try:  # Attempt to load the file from the PyInstaller temp directory
            basePath = sys._MEIPASS
        except AttributeError:
            basePath = os.environ.get("_MEIPASS2", None)
        if basePath is None:
            raise
        resourcePath = Path(os.path.join(basePath, relativePath))
        if not resourcePath.is_file():
            raise FileNotFoundError(str(resourcePath))
        return resourcePath