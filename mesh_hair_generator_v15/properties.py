import bpy
import math
from bpy.props import (
    PointerProperty,
    CollectionProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    BoolProperty,
    EnumProperty,
)

class MeshHairGuide(bpy.types.PropertyGroup):
    """Individual guide curve reference"""
    curve_object: PointerProperty(
        name="Guide Curve",
        type=bpy.types.Object,
        description="Curve object to guide hair direction"
    )
    influence: FloatProperty(
        name="Influence",
        default=1.0,
        min=0.0,
        max=1.0,
        description="How much this guide affects nearby hair"
    )

def update_preset(self, context):
    """Update all properties when preset is changed"""
    if self.preset == 'CUSTOM':
        return  # Don't change anything for custom
    
    # Apply preset configurations
    if self.preset == 'SHORT_GRASS':
        # Short lawn grass
        self.hair_length = 0.08
        self.length_random = 0.2
        self.hair_count = 15000
        self.distribution_mode = 'NOISE'
        self.noise_distribution_scale = 8.0
        self.noise_distribution_threshold = 0.3
        self.clump = 0.3
        self.clump_random = 0.4
        self.clump_length_influence = 0.6
        self.use_children = True
        self.children_count = 4
        self.children_radius = 0.01
        self.children_length = 0.9
        self.normal_factor = 0.8
        self.gravity = 0.1
        self.noise_factor = 0.05
        self.use_slope_mask = True
        self.slope_max_angle = math.radians(45)
        self.hair_color = (0.2, 0.6, 0.1, 1.0)  # Deep green
        
    elif self.preset == 'LUSH_MEADOW':
        # Wild, dense meadow grass
        self.hair_length = 0.25
        self.length_random = 0.4
        self.hair_count = 8000
        self.distribution_mode = 'NOISE' 
        self.noise_distribution_scale = 12.0
        self.noise_distribution_threshold = 0.4
        self.clump = 0.7
        self.clump_random = 0.6
        self.clump_length_influence = 0.8
        self.use_children = True
        self.children_count = 5
        self.children_radius = 0.03
        self.children_length = 0.8
        self.normal_factor = 1.2
        self.gravity = 0.3
        self.noise_factor = 0.15
        self.wave_frequency = 1.0
        self.wave_amplitude = 0.1
        self.use_slope_mask = True
        self.slope_max_angle = math.radians(35)
        self.hair_color = (0.3, 0.7, 0.2, 1.0)  # Meadow green
        
    elif self.preset == 'SPARSE_FIELD':
        # Patchy, sparse grassland
        self.hair_length = 0.15
        self.length_random = 0.6
        self.hair_count = 5000
        self.distribution_mode = 'NOISE'
        self.noise_distribution_scale = 6.0
        self.noise_distribution_threshold = 0.6
        self.clump = 0.5
        self.clump_random = 0.8
        self.clump_length_influence = 0.4
        self.use_children = True
        self.children_count = 3
        self.children_radius = 0.02
        self.children_length = 0.7
        self.normal_factor = 1.0
        self.gravity = 0.2
        self.noise_factor = 0.2
        self.use_slope_mask = True
        self.slope_max_angle = math.radians(50)
        self.hair_color = (0.4, 0.6, 0.3, 1.0)  # Dry grass
        
    elif self.preset == 'FOREST_FLOOR':
        # Long, wild forest undergrowth
        self.hair_length = 0.35
        self.length_random = 0.5
        self.hair_count = 6000
        self.distribution_mode = 'NOISE'
        self.noise_distribution_scale = 15.0
        self.noise_distribution_threshold = 0.5
        self.clump = 0.8
        self.clump_random = 0.4
        self.clump_length_influence = 0.9
        self.use_children = True
        self.children_count = 6
        self.children_radius = 0.04
        self.children_length = 0.6
        self.normal_factor = 1.5
        self.gravity = 0.4
        self.noise_factor = 0.3
        self.wave_frequency = 2.0
        self.wave_amplitude = 0.2
        self.kink_frequency = 1.0
        self.kink_amplitude = 0.1
        self.use_slope_mask = True
        self.slope_max_angle = math.radians(60)
        self.hair_color = (0.2, 0.5, 0.1, 1.0)  # Dark forest green

class MeshHairProperties(bpy.types.PropertyGroup):
    """Properties for the Mesh Hair Generator"""

    # --- Presets ---
    preset: EnumProperty(
        name="Preset",
        items=[
            ('CUSTOM', 'Custom', 'Custom settings'),
            ('SHORT_GRASS', 'Short Grass', 'Short lawn grass'),
            ('LUSH_MEADOW', 'Lush Meadow', 'Dense, wild meadow grass'),
            ('SPARSE_FIELD', 'Sparse Field', 'Patchy grassland with bare spots'),
            ('FOREST_FLOOR', 'Forest Floor', 'Long forest undergrowth'),
        ],
        default='CUSTOM',
        description="Choose a preset configuration for different grass types",
        update=update_preset
    )

    # --- Source ---
    emitter_object: PointerProperty(
        name="Emitter",
        type=bpy.types.Object,
        description="The object to grow hair from"
    )
    
    guide_curves: CollectionProperty(
        name="Guide Curves",
        type=MeshHairGuide,
        description="Curves used to guide the hair direction"
    )
    
    use_vertex_groups: BoolProperty(
        name="Use Vertex Groups",
        default=False,
        description="Use vertex groups to control hair density"
    )
    
    density_vertex_group: bpy.props.StringProperty(
        name="Density Group",
        description="Vertex group name controlling hair density"
    )

    # --- Generation ---
    hair_count: IntProperty(
        name="Count", 
        default=10000, 
        min=1, 
        max=100000,
        description="Number of hair strands to generate"
    )
    
    hair_length: FloatProperty(
        name="Length", 
        default=0.15, 
        min=0.01,
        description="Base length of hair strands"
    )
    
    length_random: FloatProperty(
        name="Length Random", 
        default=0.3,
        min=0, 
        max=1,
        description="Random variation in hair length"
    )
    
    distribution_mode: EnumProperty(
        name="Distribution",
        items=[
            ('RANDOM', 'Random', 'Random distribution across surface'),
            ('EVEN', 'Even', 'Even distribution based on face area'),
            ('DENSITY', 'Density Map', 'Use vertex group for density control'),
            ('NOISE', 'Noise', 'Use procedural noise for density'),
        ],
        default='EVEN',
        description="How to distribute hair across the surface"
    )
    
    # --- Noise Distribution ---
    noise_distribution_scale: FloatProperty(
        name="Noise Scale",
        default=5.0,
        min=0.1,
        max=50.0,
        description="The size of the noise pattern for distribution (larger value = larger patches)"
    )
    
    noise_distribution_threshold: FloatProperty(
        name="Noise Threshold",
        default=0.5,
        min=0.0,
        max=1.0,
        description="Cuts off hair generation in areas where noise is below this value"
    )
    
    # --- Slope-Based Masking ---
    use_slope_mask: BoolProperty(
        name="Use Slope Mask",
        default=False,
        description="Prevent hair from growing on steep slopes"
    )
    
    slope_max_angle: FloatProperty(
        name="Max Slope Angle",
        subtype='ANGLE',
        default=math.radians(60),  # 60 degrees in radians
        min=0,
        max=math.pi/2,  # 90 degrees in radians
        description="The maximum angle (from vertical) that hair is allowed to grow on"
    )

    # --- Render Type ---
    render_type: EnumProperty(
        name="Render As",
        items=[
            ('TUBES', 'Tubes', 'Generate hair as procedural tube geometry'),
            ('OBJECT', 'Object', 'Use a custom object as hair geometry'),
            ('HAIR_CARDS', 'Hair Cards', 'Generate optimized flat cards with alpha textures (industry standard)'),
        ],
        default='TUBES',
        description="How to render the hair strands"
    )
    
    instance_object: PointerProperty(
        name="Instance Object",
        type=bpy.types.Object,
        description="Object to use as hair geometry (when Render As = Object)"
    )
    
    hair_card_texture: PointerProperty(
        name="Hair Card Texture",
        type=bpy.types.Image,
        description="Texture image with alpha channel for hair cards (when Render As = Hair Cards)"
    )

    # --- Geometry ---
    segments: IntProperty(
        name="Segments", 
        default=6, 
        min=1, 
        max=20,
        description="Number of segments along each hair strand (Tubes only)"
    )
    
    sides: IntProperty(
        name="Sides", 
        default=4, 
        min=2, 
        max=8,
        description="Number of sides for hair tube cross-section (Tubes only)"
    )
    
    root_radius: FloatProperty(
        name="Root Radius", 
        default=0.005, 
        min=0.001,
        description="Radius at the root of hair strands"
    )
    
    tip_radius: FloatProperty(
        name="Tip Radius", 
        default=0.001, 
        min=0.0,
        description="Radius at the tip of hair strands"
    )
    
    radius_random: FloatProperty(
        name="Radius Random",
        default=0.2,
        min=0.0,
        max=1.0,
        description="Random variation in hair thickness (Tubes only)"
    )
    
    # --- Object Instance Settings ---
    object_scale: FloatProperty(
        name="Scale",
        default=1.0,
        min=0.01,
        max=10.0,
        description="Scale factor for instance objects"
    )
    
    object_scale_random: FloatProperty(
        name="Scale Random",
        default=0.3,
        min=0.0,
        max=1.0,
        description="Random variation in object scale"
    )
    
    object_rotation_random: FloatProperty(
        name="Rotation Random",
        default=1.0,
        min=0.0,
        max=1.0,
        description="Random rotation variation (0=no rotation, 1=full random)"
    )
    
    align_to_normal: BoolProperty(
        name="Align to Surface",
        default=True,
        description="Align instance objects to surface normal"
    )
    
    # --- Hair Card Settings ---
    card_width: FloatProperty(
        name="Card Width",
        default=0.02,
        min=0.001,
        max=0.1,
        description="Width of hair card planes"
    )
    
    card_subdivision: IntProperty(
        name="Card Subdivisions",
        default=3,
        min=1,
        max=8,
        description="Number of subdivisions along card length for better deformation"
    )
    
    card_variation: BoolProperty(
        name="Random Card Variation",
        default=True,
        description="Randomly vary card dimensions and orientation for natural look"
    )
    
    card_atlas_mode: BoolProperty(
        name="Use Texture Atlas",
        default=False,
        description="Randomly sample different regions from a texture atlas"
    )
    
    atlas_regions: IntProperty(
        name="Atlas Regions",
        default=4,
        min=1,
        max=16,
        description="Number of different hair patterns in the texture atlas"
    )

    # --- Styling ---
    clump: FloatProperty(
        name="Clump", 
        default=0.0, 
        min=0, 
        max=1,
        description="How much hair clumps together"
    )
    
    clump_random: FloatProperty(
        name="Clump Random",
        default=0.5,
        min=0.0,
        max=1.0,
        description="Random variation in clumping"
    )
    
    clump_length_influence: FloatProperty(
        name="Length Influence",
        default=0.5,
        min=0.0,
        max=1.0,
        description="How much a clump's 'parent' hair dictates the length of the other hairs in the clump"
    )
    
    # Direction and Growth
    normal_factor: FloatProperty(
        name="Normal Factor",
        default=1.0,
        min=0.0,
        max=2.0,
        description="How much hair follows surface normal"
    )
    
    gravity: FloatProperty(
        name="Gravity",
        default=0.0,
        min=-2.0,
        max=2.0,
        description="Gravity effect on hair direction"
    )
    
    # Noise and Variation
    noise_factor: FloatProperty(
        name="Noise Factor",
        default=0.1,
        min=0.0,
        max=2.0,
        description="Overall noise intensity"
    )
    
    noise_scale: FloatProperty(
        name="Noise Scale",
        default=1.0,
        min=0.1,
        max=10.0,
        description="Scale of noise pattern"
    )
    
    # Kink/Wave
    kink_frequency: FloatProperty(
        name="Kink Frequency", 
        default=0,
        min=0,
        max=10,
        description="Frequency of kinks along hair strands"
    )
    
    kink_amplitude: FloatProperty(
        name="Kink Amplitude", 
        default=0,
        min=0,
        max=1,
        description="Strength of kink displacement"
    )
    
    wave_frequency: FloatProperty(
        name="Wave Frequency",
        default=0.0,
        min=0.0,
        max=5.0,
        description="Frequency of waves along hair"
    )
    
    wave_amplitude: FloatProperty(
        name="Wave Amplitude",
        default=0.0,
        min=0.0,
        max=0.5,
        description="Amplitude of wave displacement"
    )

    # --- Material ---
    hair_color: FloatVectorProperty(
        name="Base Color",
        subtype='COLOR',
        default=(0.3, 0.7, 0.2, 1.0),  # Studio Ghibli grass green
        size=4,
        min=0,
        max=1,
        description="Base color of hair strands"
    )
    
    color_random: FloatProperty(
        name="Color Random",
        default=0.1,
        min=0.0,
        max=1.0,
        description="Random variation in hair color"
    )
    
    use_surface_color: BoolProperty(
        name="Use Surface Color",
        default=True,
        description="Sample color from emitter surface"
    )
    
    surface_color_blend: FloatProperty(
        name="Surface Color Blend",
        default=0.7,
        min=0.0,
        max=1.0,
        description="How much to blend with surface color"
    )

    # --- Advanced ---
    use_children: BoolProperty(
        name="Use Children",
        default=True,
        description="Generate child hairs for thickness"
    )
    
    children_count: IntProperty(
        name="Children Count",
        default=3,
        min=0,
        max=10,
        description="Number of child hairs per parent"
    )
    
    children_radius: FloatProperty(
        name="Children Radius",
        default=0.02,
        min=0.001,
        max=0.1,
        description="Radius around parent for child placement"
    )
    
    children_length: FloatProperty(
        name="Children Length",
        default=0.8,
        min=0.1,
        max=2.0,
        description="Length multiplier for child hairs"
    )

    # --- Performance ---
    preview_percentage: FloatProperty(
        name="Preview %",
        default=50.0,
        min=1.0,
        max=100.0,
        description="Percentage of hair to show in preview"
    )
    
    use_preview: BoolProperty(
        name="Preview Mode",
        default=True,
        description="Generate reduced hair count for preview"
    )
    
    batch_size: IntProperty(
        name="Batch Size",
        default=5000,
        min=100,
        max=50000,
        description="Number of hair strands to process per batch (reduces memory usage)"
    )
    
    use_batching: BoolProperty(
        name="Use Batching",
        default=True,
        description="Process hair in batches to prevent memory issues with large counts"
    )
    
    # --- Output Control ---
    keep_emitter_geometry: BoolProperty(
        name="Keep Emitter Geometry",
        default=True,
        description="Keep the original emitter mesh combined with hair"
    )
    
    shade_smooth: BoolProperty(
        name="Shade Smooth",
        default=True,
        description="Apply smooth shading to generated hair mesh"
    )

def register():
    bpy.utils.register_class(MeshHairGuide)
    bpy.utils.register_class(MeshHairProperties)
    bpy.types.Scene.mesh_hair = PointerProperty(type=MeshHairProperties)

def unregister():
    bpy.utils.unregister_class(MeshHairProperties)
    bpy.utils.unregister_class(MeshHairGuide)
    if hasattr(bpy.types.Scene, 'mesh_hair'):
        del bpy.types.Scene.mesh_hair