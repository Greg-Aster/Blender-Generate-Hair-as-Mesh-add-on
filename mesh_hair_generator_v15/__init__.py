bl_info = {
    "name": "Mesh Hair Generator",
    "author": "Generated for MEGAMEAL Project", 
    "version": (15, 0, 0),
    "blender": (4, 4, 0),
    "location": "3D View > Sidebar > Mesh Hair",
    "description": "Generate realistic grass and hair with noise distribution, clumping, and terrain-aware placement",
    "category": "Mesh",
}

import bpy
from . import properties
from . import ui
from . import operators
from . import guides
from . import texture_generator

modules = [
    properties,
    ui,
    operators,
    guides,
    texture_generator,
]

def register():
    # Import and reload modules to avoid registration conflicts
    import importlib
    for module in modules:
        importlib.reload(module)
        module.register()

def unregister():
    for module in reversed(modules):
        try:
            module.unregister()
        except Exception as e:
            print(f"Error unregistering {module.__name__}: {e}")

if __name__ == "__main__":
    register()