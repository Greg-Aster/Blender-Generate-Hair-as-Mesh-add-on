import bpy

class MESH_HAIR_PT_Panel(bpy.types.Panel):
    bl_label = "Mesh Hair Generator"
    bl_idname = "MESH_HAIR_PT_Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mesh Hair'

    def draw(self, context):
        layout = self.layout
        props = context.scene.mesh_hair

        # Presets
        preset_box = layout.box()
        preset_box.label(text="Grass Presets", icon='PRESET')
        preset_box.prop(props, "preset", text="")
        
        if props.preset != 'CUSTOM':
            preset_box.label(text="Adjust any setting to switch to Custom", icon='INFO')

        # Source Objects
        box = layout.box()
        box.label(text="Source", icon='MESH_DATA')
        box.prop(props, "emitter_object")
        
        if props.emitter_object and props.emitter_object.type != 'MESH':
            box.label(text="Emitter must be a mesh!", icon='ERROR')

        # Guide Curves Section
        guides_box = box.box()
        guides_box.label(text="Guide Curves")
        
        if len(props.guide_curves) > 0:
            for i, guide in enumerate(props.guide_curves):
                row = guides_box.row()
                row.prop(guide, "curve_object", text=f"Guide {i+1}")
                row.prop(guide, "influence", text="")
                op = row.operator("mesh_hair.remove_guide", text="", icon='X')
                op.index = i
        
        guides_box.operator("mesh_hair.add_guide", text="Add Guide Curve")

        # Generation Settings
        gen_box = layout.box()
        gen_box.label(text="Generation", icon='SETTINGS')
        
        row = gen_box.row()
        row.prop(props, "hair_count")
        if props.use_preview:
            row.prop(props, "preview_percentage", text="%")
        
        row = gen_box.row()
        row.prop(props, "hair_length")
        row.prop(props, "length_random", text="Random")
        
        gen_box.prop(props, "distribution_mode")
        
        if props.distribution_mode == 'DENSITY':
            gen_box.prop(props, "density_vertex_group")
        elif props.distribution_mode == 'NOISE':
            row = gen_box.row()
            row.prop(props, "noise_distribution_scale")
            row.prop(props, "noise_distribution_threshold")
        
        # Slope masking (works with any distribution mode)
        gen_box.prop(props, "use_slope_mask")
        if props.use_slope_mask:
            gen_box.prop(props, "slope_max_angle")

        # Render Type
        render_box = layout.box()
        render_box.label(text="Render Type", icon='SHADING_RENDERED')
        render_box.prop(props, "render_type", expand=True)
        
        if props.render_type == 'OBJECT':
            render_box.prop(props, "instance_object")
            if not props.instance_object:
                render_box.label(text="Select an object to instance", icon='INFO')
            elif props.instance_object.type != 'MESH':
                render_box.label(text="Instance object should be a mesh", icon='ERROR')
        
        # Geometry Settings (conditional based on render type)
        if props.render_type == 'TUBES':
            geo_box = layout.box()
            geo_box.label(text="Tube Geometry", icon='MESH_CYLINDER')
            
            row = geo_box.row()
            row.prop(props, "segments")
            row.prop(props, "sides")
            
            row = geo_box.row()
            row.prop(props, "root_radius")
            row.prop(props, "tip_radius")
            
            geo_box.prop(props, "radius_random")
        
        elif props.render_type == 'OBJECT':
            obj_box = layout.box()
            obj_box.label(text="Object Settings", icon='OBJECT_DATA')
            
            row = obj_box.row()
            row.prop(props, "object_scale")
            row.prop(props, "object_scale_random")
            
            obj_box.prop(props, "object_rotation_random")
            obj_box.prop(props, "align_to_normal")
            obj_box.prop(props, "use_instance_materials")
        
        elif props.render_type == 'HAIR_CARDS':
            card_box = layout.box()
            card_box.label(text="Hair Card Settings", icon='TEXTURE')
            
            card_box.prop(props, "hair_card_texture")
            if not props.hair_card_texture:
                card_box.label(text="Select a texture with alpha channel", icon='INFO')
                # Add button to create default textures
                card_box.operator("mesh_hair.create_textures", text="Create Default Hair Textures", icon='ADD')
            
            row = card_box.row()
            row.prop(props, "card_width")
            row.prop(props, "card_subdivision")
            
            card_box.prop(props, "card_variation")
            
            # Atlas settings
            atlas_box = card_box.box()
            atlas_box.label(text="Texture Atlas")
            atlas_box.prop(props, "card_atlas_mode")
            if props.card_atlas_mode:
                atlas_box.prop(props, "atlas_regions")

        # Direction & Growth
        dir_box = layout.box()
        dir_box.label(text="Direction & Growth", icon='FORCE_WIND')
        
        row = dir_box.row()
        row.prop(props, "normal_factor")
        row.prop(props, "gravity")
        
        row = dir_box.row()
        row.prop(props, "noise_factor")
        row.prop(props, "noise_scale")

        # Styling
        style_box = layout.box()
        style_box.label(text="Styling", icon='BRUSH_DATA')
        
        row = style_box.row()
        row.prop(props, "clump")
        row.prop(props, "clump_random")
        
        # Show clump length influence when clumping is enabled
        if props.clump > 0:
            style_box.prop(props, "clump_length_influence")
        
        # Waves and Kinks
        wave_box = style_box.box()
        wave_box.label(text="Waves & Kinks")
        
        row = wave_box.row()
        row.prop(props, "wave_frequency")
        row.prop(props, "wave_amplitude")
        
        row = wave_box.row()
        row.prop(props, "kink_frequency")
        row.prop(props, "kink_amplitude")

        # Children
        children_box = layout.box()
        children_box.label(text="Children", icon='PARTICLE_DATA')
        children_box.prop(props, "use_children")
        
        if props.use_children:
            row = children_box.row()
            row.prop(props, "children_count")
            row.prop(props, "children_length")
            children_box.prop(props, "children_radius")

        # Material
        mat_box = layout.box()
        mat_box.label(text="Material", icon='MATERIAL')
        mat_box.prop(props, "hair_color")
        mat_box.prop(props, "color_random")
        
        mat_box.prop(props, "use_surface_color")
        if props.use_surface_color:
            mat_box.prop(props, "surface_color_blend")

        # Performance
        perf_box = layout.box()
        perf_box.label(text="Performance", icon='PREFERENCES')
        perf_box.prop(props, "use_preview")
        
        perf_box.prop(props, "use_batching")
        if props.use_batching:
            perf_box.prop(props, "batch_size")
        
        # Output Control
        output_box = layout.box()
        output_box.label(text="Output", icon='EXPORT')
        output_box.prop(props, "keep_emitter_geometry")
        output_box.prop(props, "shade_smooth")

        # Actions
        layout.separator()
        
        col = layout.column(align=True)
        
        # Check if we can generate
        can_generate = props.emitter_object and props.emitter_object.type == 'MESH'
        
        # Additional validation for object mode
        if props.render_type == 'OBJECT' and can_generate:
            if not props.instance_object or props.instance_object.type != 'MESH':
                can_generate = False
        
        # Additional validation for hair cards mode
        if props.render_type == 'HAIR_CARDS' and can_generate:
            if not props.hair_card_texture:
                can_generate = False
        
        row = col.row(align=True)
        row.scale_y = 1.5
        
        if can_generate:
            if props.use_preview:
                row.operator("mesh_hair.generate", text="Generate Preview", icon='PLAY')
            else:
                row.operator("mesh_hair.generate", text="Generate Hair", icon='PLAY')
        else:
            row.enabled = False
            if not props.emitter_object:
                row.operator("mesh_hair.generate", text="Select Mesh Emitter", icon='ERROR')
            elif props.render_type == 'OBJECT' and not props.instance_object:
                row.operator("mesh_hair.generate", text="Select Instance Object", icon='ERROR')
            elif props.render_type == 'HAIR_CARDS' and not props.hair_card_texture:
                row.operator("mesh_hair.generate", text="Select Hair Card Texture", icon='ERROR')
            else:
                row.operator("mesh_hair.generate", text="Invalid Settings", icon='ERROR')
        
        # Finalize button
        hair_obj = bpy.data.objects.get("HairMesh_Preview")
        if hair_obj:
            row = col.row(align=True)
            row.scale_y = 1.2
            row.operator("mesh_hair.finalize", text="Finalize Hair Mesh", icon='CHECKMARK')
            
            # Delete preview button
            row = col.row(align=True)
            row.operator("mesh_hair.delete_preview", text="Delete Preview", icon='TRASH')

        # Info
        if can_generate:
            expected_count = props.hair_count
            if props.use_children:
                expected_count += props.hair_count * props.children_count
            if props.use_preview:
                expected_count = int(expected_count * props.preview_percentage / 100)
            
            info_box = layout.box()
            info_box.label(text=f"Expected strands: {expected_count:,}")
            info_box.label(text=f"Estimated vertices: {expected_count * (props.segments + 1) * props.sides:,}")

class MESH_HAIR_PT_Advanced(bpy.types.Panel):
    bl_label = "Advanced Settings"
    bl_idname = "MESH_HAIR_PT_Advanced"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Mesh Hair'
    bl_parent_id = "MESH_HAIR_PT_Panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        props = context.scene.mesh_hair

        # Vertex Groups
        vg_box = layout.box()
        vg_box.label(text="Vertex Groups")
        vg_box.prop(props, "use_vertex_groups")

def register():
    bpy.utils.register_class(MESH_HAIR_PT_Panel)
    bpy.utils.register_class(MESH_HAIR_PT_Advanced)

def unregister():
    bpy.utils.unregister_class(MESH_HAIR_PT_Advanced)
    bpy.utils.unregister_class(MESH_HAIR_PT_Panel)