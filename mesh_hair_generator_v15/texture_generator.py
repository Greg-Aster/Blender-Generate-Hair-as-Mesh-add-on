import bpy
import bmesh
import mathutils
from mathutils import Vector
import random
import math

# Try to import numpy (not required for texture generation)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def create_hair_card_texture(name="HairCardTexture", width=256, height=512, strand_count=5):
    """Create a procedural hair card texture with alpha channel"""
    
    # Create new image
    image = bpy.data.images.new(name, width=width, height=height, alpha=True)
    pixels = [0.0] * (width * height * 4)  # RGBA
    
    # Generate hair strands
    for strand in range(strand_count):
        # Random strand parameters
        x_center = random.uniform(0.2, 0.8) * width
        strand_width = random.uniform(8, 20)
        strand_darkness = random.uniform(0.3, 0.7)
        
        # Create strand path with slight curve
        curve_strength = random.uniform(-0.3, 0.3)
        
        for y in range(height):
            t = y / height
            
            # Calculate strand center with curve
            x_offset = curve_strength * math.sin(t * math.pi) * width * 0.3
            strand_x = x_center + x_offset
            
            # Calculate strand width (tapers at ends)
            width_factor = 1.0
            if t < 0.1:  # Taper at root
                width_factor = t * 10
            elif t > 0.9:  # Taper at tip
                width_factor = (1.0 - t) * 10
            
            current_width = strand_width * width_factor
            
            # Fill pixels around strand center
            for x in range(max(0, int(strand_x - current_width)), 
                          min(width, int(strand_x + current_width))):
                
                # Distance from strand center
                distance = abs(x - strand_x)
                alpha = max(0, 1.0 - (distance / current_width))
                
                # Add some noise for realism
                noise = random.uniform(0.8, 1.2)
                alpha *= noise
                alpha = min(1.0, max(0.0, alpha))
                
                # Calculate pixel index
                pixel_index = (y * width + x) * 4
                
                if pixel_index < len(pixels):
                    # Hair color (dark brown/black)
                    color_r = strand_darkness * random.uniform(0.8, 1.2)
                    color_g = strand_darkness * 0.7 * random.uniform(0.8, 1.2)
                    color_b = strand_darkness * 0.4 * random.uniform(0.8, 1.2)
                    
                    # Blend with existing pixel
                    existing_alpha = pixels[pixel_index + 3]
                    blend_alpha = min(1.0, existing_alpha + alpha)
                    
                    if blend_alpha > existing_alpha:
                        pixels[pixel_index] = max(pixels[pixel_index], color_r)     # R
                        pixels[pixel_index + 1] = max(pixels[pixel_index + 1], color_g) # G
                        pixels[pixel_index + 2] = max(pixels[pixel_index + 2], color_b) # B
                        pixels[pixel_index + 3] = blend_alpha  # A
    
    # Assign pixels to image
    image.pixels[:] = pixels
    image.pack()
    
    return image

def create_hair_atlas_texture(name="HairAtlasTexture", width=512, height=512, regions=4):
    """Create a hair atlas texture with multiple hair patterns"""
    
    image = bpy.data.images.new(name, width=width, height=height, alpha=True)
    pixels = [0.0] * (width * height * 4)  # RGBA
    
    regions_per_side = int(math.sqrt(regions))
    region_width = width // regions_per_side
    region_height = height // regions_per_side
    
    for region_y in range(regions_per_side):
        for region_x in range(regions_per_side):
            # Create different hair patterns for each region
            strand_count = random.randint(3, 7)
            
            for strand in range(strand_count):
                # Random strand parameters for this region
                base_x = region_x * region_width
                base_y = region_y * region_height
                
                x_center = base_x + random.uniform(0.2, 0.8) * region_width
                strand_width = random.uniform(6, 15)
                strand_darkness = random.uniform(0.4, 0.8)
                
                # Create strand with different characteristics per region
                curve_type = (region_x + region_y) % 3
                
                for y in range(region_height):
                    t = y / region_height
                    actual_y = base_y + y
                    
                    # Different curve types for variety
                    if curve_type == 0:  # Straight
                        x_offset = 0
                    elif curve_type == 1:  # S-curve
                        x_offset = math.sin(t * math.pi * 2) * region_width * 0.2
                    else:  # Wave
                        x_offset = math.sin(t * math.pi) * region_width * 0.3
                    
                    strand_x = x_center + x_offset
                    
                    # Width tapering
                    width_factor = 1.0
                    if t < 0.15:
                        width_factor = t / 0.15
                    elif t > 0.85:
                        width_factor = (1.0 - t) / 0.15
                    
                    current_width = strand_width * width_factor
                    
                    for x in range(max(base_x, int(strand_x - current_width)), 
                                  min(base_x + region_width, int(strand_x + current_width))):
                        
                        distance = abs(x - strand_x)
                        alpha = max(0, 1.0 - (distance / current_width))
                        alpha *= random.uniform(0.7, 1.0)  # Add noise
                        alpha = min(1.0, max(0.0, alpha))
                        
                        pixel_index = (actual_y * width + x) * 4
                        
                        if pixel_index < len(pixels):
                            # Vary hair color by region
                            region_hue = (region_x + region_y) * 0.1
                            color_r = (strand_darkness + region_hue) * random.uniform(0.8, 1.2)
                            color_g = strand_darkness * 0.7 * random.uniform(0.8, 1.2)
                            color_b = strand_darkness * 0.4 * random.uniform(0.8, 1.2)
                            
                            existing_alpha = pixels[pixel_index + 3]
                            blend_alpha = min(1.0, existing_alpha + alpha)
                            
                            if blend_alpha > existing_alpha:
                                pixels[pixel_index] = max(pixels[pixel_index], color_r)
                                pixels[pixel_index + 1] = max(pixels[pixel_index + 1], color_g)
                                pixels[pixel_index + 2] = max(pixels[pixel_index + 2], color_b)
                                pixels[pixel_index + 3] = blend_alpha
    
    image.pixels[:] = pixels
    image.pack()
    
    return image

def create_default_hair_textures():
    """Create a set of default hair card textures"""
    textures = []
    
    # Basic hair card texture
    basic_texture = create_hair_card_texture("HairCard_Basic", 256, 512, 5)
    textures.append(basic_texture)
    
    # Dense hair texture
    dense_texture = create_hair_card_texture("HairCard_Dense", 256, 512, 8)
    textures.append(dense_texture)
    
    # Sparse hair texture
    sparse_texture = create_hair_card_texture("HairCard_Sparse", 256, 512, 3)
    textures.append(sparse_texture)
    
    # Hair atlas for variation
    atlas_texture = create_hair_atlas_texture("HairCard_Atlas", 512, 512, 4)
    textures.append(atlas_texture)
    
    print(f"Created {len(textures)} default hair card textures")
    return textures

class MESH_HAIR_OT_CreateTextures(bpy.types.Operator):
    bl_idname = "mesh_hair.create_textures"
    bl_label = "Create Hair Card Textures"
    bl_description = "Generate default hair card textures with alpha channels"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            textures = create_default_hair_textures()
            self.report({'INFO'}, f"Created {len(textures)} hair card textures")
            
            # Auto-select the basic texture if none is selected
            props = context.scene.mesh_hair
            if not props.hair_card_texture and textures:
                props.hair_card_texture = textures[0]
                self.report({'INFO'}, f"Auto-selected '{textures[0].name}' as hair card texture")
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Failed to create textures: {str(e)}")
            return {'CANCELLED'}

def register():
    bpy.utils.register_class(MESH_HAIR_OT_CreateTextures)

def unregister():
    bpy.utils.unregister_class(MESH_HAIR_OT_CreateTextures)