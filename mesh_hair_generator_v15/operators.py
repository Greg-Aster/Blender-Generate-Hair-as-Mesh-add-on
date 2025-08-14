import bpy
import bmesh
import mathutils
from mathutils import Vector, Matrix, noise
from mathutils.kdtree import KDTree
import random
import math

# Try to import numpy for vectorized operations
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: numpy not available. Hair generation will use slower fallback methods.")
    print("For best performance, install numpy: pip install numpy")

# Constant for vertex color layer name to ensure consistency
VCOL_LAYER_NAME = "HairMeshVCol"

class MESH_HAIR_OT_Generate(bpy.types.Operator):
    bl_idname = "mesh_hair.generate"
    bl_label = "Generate Hair"
    bl_description = "Generate hair as mesh geometry"
    bl_options = {'REGISTER', 'UNDO'}
    
    # Progress tracking
    _progress = 0.0
    _total_operations = 0
    _current_operation = 0
    _cancelled = False

    def execute(self, context):
        props = context.scene.mesh_hair
        
        # Reset progress tracking
        self._progress = 0.0
        self._current_operation = 0
        self._cancelled = False
        
        # Validation
        if not props.emitter_object:
            self.report({'ERROR'}, "No emitter object selected")
            return {'CANCELLED'}
        
        if props.emitter_object.type != 'MESH':
            self.report({'ERROR'}, "Emitter must be a mesh object")
            return {'CANCELLED'}
        
        # Calculate total operations for progress tracking
        hair_count = props.hair_count
        if props.use_preview:
            hair_count = int(hair_count * props.preview_percentage / 100)
        
        child_count = 0
        if props.use_children:
            child_count = hair_count * props.children_count
        
        self._total_operations = hair_count + child_count + 5  # +5 for setup/cleanup operations
        
        # Cleanup previous hair
        self.cleanup_previous_hair()
        self.update_progress(context, "Cleaning up previous hair...")
        
        # Generate hair mesh
        try:
            hair_obj = self.generate_hair_mesh(context, props)
            self.update_progress(context, "Hair generation complete!", 1.0)
            
            if hair_obj:
                vertex_count = len(hair_obj.data.vertices)
                face_count = len(hair_obj.data.polygons)
                self.report({'INFO'}, f"Generated hair: {vertex_count:,} vertices, {face_count:,} faces")
            
            return {'FINISHED'}
        except Exception as e:
            # Ensure progress bar is ended even on error
            try:
                context.window_manager.progress_end()
            except:
                pass
            self.report({'ERROR'}, f"Hair generation failed: {str(e)}")
            return {'CANCELLED'}
    
    def update_progress(self, context, message="", progress=None):
        """Update progress bar and message"""
        if progress is not None:
            self._progress = progress
        else:
            self._current_operation += 1
            self._progress = self._current_operation / max(self._total_operations, 1)
        
        # Update progress in UI (with error handling)
        try:
            context.window_manager.progress_update(self._progress)
        except:
            pass  # Continue even if progress update fails
        
        # Print progress to console
        percentage = int(self._progress * 100)
        if message:
            print(f"[{percentage:3d}%] {message}")
        
        # Force UI update (with error handling)
        try:
            if context.area:
                context.area.tag_redraw()
        except:
            pass
        
        # Process events to keep UI responsive (with error handling)
        try:
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
        except:
            pass
    
    def cleanup_previous_hair(self):
        """Remove any existing preview hair object"""
        hair_obj = bpy.data.objects.get("HairMesh_Preview")
        if hair_obj:
            bpy.data.objects.remove(hair_obj, do_unlink=True)
    
    def generate_hair_mesh(self, context, props):
        """Main hair generation function using duplicate and prune approach"""
        emitter = props.emitter_object
        
        # Initialize progress bar
        context.window_manager.progress_begin(0, 100)
        self.update_progress(context, "Starting hair generation...")
        
        # Step 1: Duplicate the Emitter properly
        self.update_progress(context, "Duplicating emitter object...")
        bpy.ops.object.select_all(action='DESELECT')
        emitter.select_set(True)
        context.view_layer.objects.active = emitter
        
        # Duplicate using linked data to ensure proper copy
        bpy.ops.object.duplicate(linked=False)
        
        # Get the duplicated object (this becomes our hair object)
        hair_obj = context.active_object
        if not hair_obj or hair_obj == emitter:
            self.report({'ERROR'}, "Failed to duplicate emitter object")
            return None
            
        hair_obj.name = "HairMesh_Preview"
        hair_obj.data = hair_obj.data.copy()  # Ensure unique mesh data
        hair_obj.data.name = "HairMesh_Preview"
        
        print(f"Duplicated {emitter.name} -> {hair_obj.name}")
        print(f"Original location: {emitter.location}")
        print(f"Duplicate location: {hair_obj.location}")
        
        # Get evaluated mesh data for accurate hair generation
        depsgraph = context.evaluated_depsgraph_get()
        eval_obj = emitter.evaluated_get(depsgraph)
        original_mesh = eval_obj.to_mesh()
        
        # Calculate hair count (with preview mode)
        hair_count = props.hair_count
        if props.use_preview:
            hair_count = int(hair_count * props.preview_percentage / 100)
        
        # Step 2: Generate Hair Geometry and add to existing mesh
        # Create bmesh from duplicated object
        bm = bmesh.new()
        bm.from_mesh(hair_obj.data)
        
        # Store original face count for pruning later
        original_face_count = len(bm.faces)
        
        # Distribute points on surface using original mesh (identity matrix since we're working with duplicated object)
        self.update_progress(context, "Distributing hair points on surface...")
        points_data = self.distribute_points_on_surface(original_mesh, Matrix.Identity(4), hair_count, props)
        
        # Generate hair geometry data (new architecture)
        total_expected = hair_count
        if props.use_children:
            total_expected += hair_count * props.children_count
        self.update_progress(context, f"Calculating geometry for {total_expected:,} hair strands...")
        hair_data = self.calculate_all_hair_geometry(points_data, props, emitter, context)
        
        # Create mesh from calculated data (bulk operation)
        self.update_progress(context, f"Building mesh: {len(hair_data['vertices']):,} vertices, {len(hair_data['faces']):,} faces...")
        self.create_mesh_from_data(bm, hair_data)
        
        # Step 3: Apply changes back to mesh
        self.update_progress(context, "Applying geometry changes...")
        bm.to_mesh(hair_obj.data)
        
        # Step 4: Prune original geometry if requested
        if not props.keep_emitter_geometry:
            self.update_progress(context, "Pruning original geometry...")
            self.prune_original_geometry(hair_obj, original_face_count)
        
        bm.free()
        
        # Cleanup evaluated mesh
        eval_obj.to_mesh_clear()
        
        # Create appropriate material for hair cards
        if props.render_type == 'HAIR_CARDS':
            self.update_progress(context, "Creating hair card material...")
            self.create_hair_card_material(hair_obj, props)
        
        # Apply shade smooth if enabled
        if props.shade_smooth:
            self.update_progress(context, "Applying smooth shading...")
            bpy.ops.object.select_all(action='DESELECT')
            hair_obj.select_set(True)
            context.view_layer.objects.active = hair_obj
            bpy.ops.object.shade_smooth()
        
        # End progress bar
        context.window_manager.progress_end()
        
        self.report({'INFO'}, f"Generated hair with perfect material inheritance")
        return hair_obj
    
    def calculate_all_hair_geometry(self, points_data, props, emitter, context):
        """
        Calculate all hair geometry data without modifying bmesh.
        This is the new high-performance approach that separates calculation from creation.
        Preserves material inheritance and UV coordinates from the emitter object.
        """
        all_vertices = []
        all_faces = []
        all_material_indices = []
        all_uv_coords = []  # Store UV coordinates for each vertex
        
        # Validation for specific render types
        if props.render_type == 'OBJECT' and (not props.instance_object or props.instance_object.type != 'MESH'):
            self.update_progress(context, "OBJECT render type requires a valid mesh instance object")
            return {
                "vertices": all_vertices,
                "faces": all_faces, 
                "material_indices": all_material_indices,
                "uv_coords": all_uv_coords
            }
        
        # Add children to points_data if enabled
        # This is much more efficient than a separate function for children
        if props.use_children and props.children_count > 0:
            parent_points = list(points_data)  # Make a copy
            for point_data in parent_points:
                parent_pos = point_data['position']
                parent_normal = point_data['normal']
                
                for _ in range(props.children_count):
                    # Create 3D spherical offset around parent using surface-aware distribution
                    # Generate random point on a circle in the tangent plane to the surface
                    angle = random.uniform(0, 2 * math.pi)
                    radius = random.uniform(0.2, 1.0) * props.children_radius  # Vary distance from parent
                    
                    # Create tangent vectors perpendicular to surface normal
                    if abs(parent_normal.z) < 0.9:
                        tangent1 = parent_normal.cross(Vector((0, 0, 1))).normalized()
                    else:
                        tangent1 = parent_normal.cross(Vector((1, 0, 0))).normalized()
                    tangent2 = parent_normal.cross(tangent1).normalized()
                    
                    # Calculate offset in tangent plane
                    tangent_offset = (tangent1 * math.cos(angle) + tangent2 * math.sin(angle)) * radius
                    
                    # Add small variation along normal (slight height variation)
                    normal_variation = parent_normal * random.uniform(-props.children_radius * 0.1, props.children_radius * 0.2)
                    
                    child_position = parent_pos + tangent_offset + normal_variation
                    
                    # Create child data
                    child_data = point_data.copy()
                    child_data['position'] = child_position
                    child_data['is_child'] = True  # Mark as child for length calculation
                    # Add some variation to child normal for more natural look
                    variation = Vector((
                        random.uniform(-0.1, 0.1),
                        random.uniform(-0.1, 0.1),
                        random.uniform(-0.05, 0.05)
                    ))
                    child_data['normal'] = (parent_normal + variation).normalized()
                    points_data.append(child_data)
        
        # === CLUMPING SYSTEM SETUP ===
        clump_centers = []
        clump_kdtree = None
        clump_assignments = {}  # Store clump assignment for each point index
        
        if props.clump > 0 and len(points_data) > 1:
            # 1. Create clump centers (inversely proportional to clump value)
            # Higher clump value = fewer, stronger clumps
            num_centers = max(1, int(len(points_data) * (1.0 - props.clump)))
            
            # Randomly select clump centers from existing points
            center_indices = random.sample(range(len(points_data)), min(num_centers, len(points_data)))
            
            for idx in center_indices:
                center_data = points_data[idx].copy()
                # Pre-calculate a "parent" length for this clump center
                parent_length = props.hair_length * (1.0 + random.uniform(-props.length_random, props.length_random))
                center_data['parent_length'] = parent_length
                clump_centers.append(center_data)
            
            # 2. Build KDTree for efficient nearest neighbor search
            clump_kdtree = KDTree(len(clump_centers))
            for i, center in enumerate(clump_centers):
                clump_kdtree.insert(center['position'], i)
            clump_kdtree.balance()
            
            # 3. Pre-assign each point to its nearest clump center
            for point_idx, point_data in enumerate(points_data):
                if clump_kdtree:
                    nearest_pos, nearest_idx, nearest_dist = clump_kdtree.find(point_data['position'])
                    clump_assignments[point_idx] = {
                        'center_idx': nearest_idx,
                        'center_data': clump_centers[nearest_idx],
                        'distance': nearest_dist
                    }
        
        # Progress tracking
        total_strands = len(points_data)
        processed = 0
        
        # Main Loop - Process all points (parents and children)
        for point_idx, point_data in enumerate(points_data):
            is_child = point_data.get('is_child', False)
            
            # Update progress periodically
            if processed % 1000 == 0:
                progress_msg = f"Processing strand {processed + 1}/{total_strands}"
                if is_child:
                    progress_msg += " (child)"
                self.update_progress(context, progress_msg)
            
            # 1. Calculate Strand Path and Radii (using existing logic)
            start_pos = point_data['position']
            normal = point_data['normal']
            
            # === APPLY CLUMPING MODIFICATIONS ===
            if props.clump > 0 and point_idx in clump_assignments:
                clump_data = clump_assignments[point_idx]
                center_pos = clump_data['center_data']['position']
                
                # Calculate clumping strength with randomness
                clump_strength = props.clump + random.uniform(-props.clump_random, props.clump_random)
                clump_strength = max(0.0, min(1.0, clump_strength))  # Clamp to [0, 1]
                
                # Move the start position towards the clump center
                start_pos = start_pos.lerp(center_pos, clump_strength)
                
                # Update the point_data position for consistency
                point_data['position'] = start_pos
            
            # Calculate length with child modifier
            length = props.hair_length * (props.children_length if is_child else 1.0)
            length *= (1.0 + random.uniform(-props.length_random, props.length_random))
            
            # === APPLY CLUMP-INFLUENCED LENGTH ===
            if props.clump > 0 and props.clump_length_influence > 0 and point_idx in clump_assignments:
                clump_data = clump_assignments[point_idx]
                parent_length = clump_data['center_data']['parent_length']
                
                # Blend towards the clump's parent length
                length = length * (1.0 - props.clump_length_influence) + parent_length * props.clump_length_influence
            
            # Generate path points using existing method
            path_points = self.calculate_hair_path(start_pos, normal, length, props)
            radii = self.calculate_hair_radii(len(path_points), props, is_child)
            
            # 2. Get Material Index (Preserving Inheritance)
            # This is inherited from the original emitter face
            material_index = 0
            if point_data.get('face_index') is not None:
                source_face_idx = point_data['face_index']
                if source_face_idx < len(emitter.data.polygons):
                    material_index = emitter.data.polygons[source_face_idx].material_index
            
            # 3. Get UV Coordinate for texture sampling
            source_uv = point_data.get('uv_coord')
            
            # 4. Generate Vertices and Faces based on render type
            if props.render_type == 'TUBES':
                # TUBES: Generate tube geometry using path points
                if len(path_points) < 2:
                    processed += 1
                    continue
                
                vertex_offset = len(all_vertices)
                rings = []
                
                # Create rings of vertex coordinates
                for i, (point, radius) in enumerate(zip(path_points, radii)):
                    # Calculate orientation vectors
                    if i == 0:
                        if len(path_points) > 1:
                            forward = (path_points[1] - path_points[0]).normalized()
                        else:
                            forward = Vector((0, 0, 1))
                        
                        if abs(forward.z) < 0.9:
                            up = Vector((0, 0, 1))
                        else:
                            up = Vector((1, 0, 0))
                        
                        right = forward.cross(up).normalized()
                        up = right.cross(forward).normalized()
                    else:
                        if i < len(path_points) - 1:
                            forward = (path_points[i + 1] - path_points[i - 1]).normalized()
                        else:
                            forward = (path_points[i] - path_points[i - 1]).normalized()
                        
                        up = right.cross(forward).normalized()
                        right = forward.cross(up).normalized()
                    
                    # Create ring vertices
                    ring_coords = []
                    ring_uvs = []
                    for j in range(props.sides):
                        angle = j * 2 * math.pi / props.sides
                        offset = (right * math.cos(angle) + up * math.sin(angle)) * radius
                        vert_pos = point + offset
                        ring_coords.append(vert_pos)
                        
                        # Calculate UV for this vertex
                        if source_uv:
                            uv_variation = 0.01
                            offset_u = random.uniform(-uv_variation, uv_variation)
                            offset_v = random.uniform(-uv_variation, uv_variation)
                            
                            varied_uv = Vector((
                                max(0, min(1, source_uv.x + offset_u)),
                                max(0, min(1, source_uv.y + offset_v))
                            ))
                            ring_uvs.append(varied_uv)
                        else:
                            ring_uvs.append(Vector((0, 0)))
                    
                    rings.append(ring_coords)
                    all_uv_coords.extend(ring_uvs)
                
                # Add all vertices for this strand
                all_vertices.extend([coord for ring in rings for coord in ring])
                
                # Create faces between rings using indices
                num_segments = len(path_points) - 1
                for i in range(num_segments):
                    for j in range(props.sides):
                        j_next = (j + 1) % props.sides
                        
                        # Get indices for the quad face
                        v1 = vertex_offset + (i * props.sides) + j
                        v2 = vertex_offset + (i * props.sides) + j_next
                        v3 = vertex_offset + ((i + 1) * props.sides) + j_next
                        v4 = vertex_offset + ((i + 1) * props.sides) + j
                        
                        # Create two triangular faces for the quad
                        all_faces.append((v1, v2, v3))
                        all_faces.append((v1, v3, v4))
                        all_material_indices.append(material_index)
                        all_material_indices.append(material_index)
            
            elif props.render_type == 'OBJECT':
                # OBJECT: Calculate transformation matrix for instancing
                # Calculate scale
                scale = props.object_scale
                if is_child:
                    scale *= props.children_length
                
                # Add random scale variation
                if props.object_scale_random > 0:
                    scale_variation = random.uniform(-props.object_scale_random, props.object_scale_random)
                    scale *= (1.0 + scale_variation)
                
                # Calculate rotation matrix
                if props.align_to_normal:
                    # Align object to surface normal
                    up = normal
                    if abs(up.z) < 0.9:
                        forward = Vector((0, 0, 1))
                    else:
                        forward = Vector((1, 0, 0))
                    
                    right = up.cross(forward).normalized()
                    forward = right.cross(up).normalized()
                    
                    rotation_matrix = Matrix((right, forward, up)).to_4x4().transposed()
                else:
                    rotation_matrix = Matrix.Identity(4)
                
                # Add random rotation
                if props.object_rotation_random > 0:
                    random_angle = random.uniform(0, props.object_rotation_random * math.pi * 2)
                    random_rotation = Matrix.Rotation(random_angle, 4, normal)
                    rotation_matrix = random_rotation @ rotation_matrix
                
                # Create transformation matrix
                scale_matrix = Matrix.Scale(scale, 4)
                translation_matrix = Matrix.Translation(start_pos)
                transform_matrix = translation_matrix @ rotation_matrix @ scale_matrix
                
                # Generate instance geometry data
                self.calculate_instance_geometry_data(
                    all_vertices, all_faces, all_material_indices, all_uv_coords,
                    props.instance_object, transform_matrix, material_index, source_uv
                )
            
            elif props.render_type == 'HAIR_CARDS':
                # HAIR_CARDS: Generate card geometry
                # Calculate card dimensions
                card_width = props.card_width
                if props.card_variation:
                    width_factor = 1.0 + (random.uniform(-0.3, 0.3))
                    card_width *= max(0.3, width_factor)
                
                # Create hair direction with effects
                hair_direction = normal.copy()
                
                # Add gravity effect
                if props.gravity != 0:
                    gravity_vec = Vector((0, 0, -props.gravity))
                    hair_direction += gravity_vec * 0.5
                
                # Add noise for natural variation
                if props.noise_factor > 0:
                    noise_offset = Vector((
                        noise.noise(start_pos * props.noise_scale),
                        noise.noise(start_pos * props.noise_scale + Vector((100, 0, 0))),
                        noise.noise(start_pos * props.noise_scale + Vector((0, 100, 0)))
                    )) * props.noise_factor
                    hair_direction += noise_offset
                
                hair_direction.normalize()
                
                # Generate card geometry data
                self.calculate_hair_card_geometry_data(
                    all_vertices, all_faces, all_material_indices, all_uv_coords,
                    start_pos, hair_direction, normal, length, card_width,
                    props, material_index, source_uv
                )
            
            processed += 1
        
        return {
            "vertices": all_vertices,
            "faces": all_faces,
            "material_indices": all_material_indices,
            "uv_coords": all_uv_coords
        }
    
    def calculate_instance_geometry_data(self, all_vertices, all_faces, all_material_indices, 
                                       all_uv_coords, instance_obj, transform_matrix, 
                                       material_index, source_uv):
        """Calculate transformed instance object geometry data"""
        instance_mesh = instance_obj.data
        vertex_offset = len(all_vertices)
        
        # Transform and add vertices
        for vert in instance_mesh.vertices:
            transformed_pos = transform_matrix @ vert.co
            all_vertices.append(transformed_pos)
            
            # Add UV coordinate for this vertex
            if source_uv:
                uv_variation = 0.01
                offset_u = random.uniform(-uv_variation, uv_variation)
                offset_v = random.uniform(-uv_variation, uv_variation)
                
                varied_uv = Vector((
                    max(0, min(1, source_uv.x + offset_u)),
                    max(0, min(1, source_uv.y + offset_v))
                ))
                all_uv_coords.append(varied_uv)
            else:
                all_uv_coords.append(Vector((0, 0)))
        
        # Add faces with proper vertex indices
        for poly in instance_mesh.polygons:
            if len(poly.vertices) == 3:
                # Triangle face
                face = tuple(vertex_offset + v for v in poly.vertices)
                all_faces.append(face)
                all_material_indices.append(material_index)
            elif len(poly.vertices) == 4:
                # Quad face - split into two triangles
                v = poly.vertices
                face1 = (vertex_offset + v[0], vertex_offset + v[1], vertex_offset + v[2])
                face2 = (vertex_offset + v[0], vertex_offset + v[2], vertex_offset + v[3])
                all_faces.extend([face1, face2])
                all_material_indices.extend([material_index, material_index])
    
    def calculate_hair_card_geometry_data(self, all_vertices, all_faces, all_material_indices,
                                        all_uv_coords, start_pos, hair_dir, surface_normal,
                                        length, width, props, material_index, source_uv):
        """Calculate hair card geometry data (subdivided plane oriented along hair direction)"""
        vertex_offset = len(all_vertices)
        
        # Calculate card orientation
        forward = hair_dir.normalized()
        
        # Create perpendicular vectors for the card
        temp_up = Vector((0, 0, 1))
        if abs(forward.dot(temp_up)) > 0.9:
            temp_up = Vector((1, 0, 0))
        
        right = forward.cross(temp_up).normalized()
        up = right.cross(forward).normalized()
        
        # Add random rotation variation for natural look
        if props.card_variation:
            random_angle = random.uniform(-math.pi * 0.2, math.pi * 0.2)
            rotation_matrix = Matrix.Rotation(random_angle, 3, forward)
            right = rotation_matrix @ right
            up = rotation_matrix @ up
        
        # Create vertices for subdivided card
        subdivisions = props.card_subdivision
        vertices = []
        
        # Generate grid of vertices
        for i in range(subdivisions + 1):
            t = i / subdivisions  # Parameter along length (0 to 1)
            
            # Apply taper along length (cards get narrower toward tip)
            width_at_t = width * (1.0 - t * 0.3)  # 30% narrower at tip
            
            # Calculate position along hair path
            pos_along_hair = start_pos + forward * (length * t)
            
            # Add slight curve/bend for more natural look
            if t > 0:
                bend_amount = t * t * props.gravity * 0.1  # Quadratic bend
                pos_along_hair += Vector((0, 0, -bend_amount))
            
            # Create vertices across width
            left_pos = pos_along_hair - right * (width_at_t * 0.5)
            right_pos = pos_along_hair + right * (width_at_t * 0.5)
            
            vertices.extend([left_pos, right_pos])
        
        # Add vertices to main list
        all_vertices.extend(vertices)
        
        # Add UV coordinates for vertices
        for i in range(subdivisions + 1):
            t = i / subdivisions
            # Left and right UV coordinates
            if source_uv:
                uv_variation = 0.01
                for side in range(2):  # Left and right
                    offset_u = random.uniform(-uv_variation, uv_variation)
                    offset_v = random.uniform(-uv_variation, uv_variation)
                    
                    base_u = side  # 0 for left, 1 for right
                    varied_uv = Vector((
                        max(0, min(1, source_uv.x + offset_u + base_u * 0.1)),
                        max(0, min(1, source_uv.y + offset_v + t * 0.1))
                    ))
                    all_uv_coords.append(varied_uv)
            else:
                all_uv_coords.extend([Vector((0, t)), Vector((1, t))])
        
        # Create faces (quads between subdivision levels)
        for i in range(subdivisions):
            # Indices for current row and next row
            curr_left = vertex_offset + i * 2
            curr_right = vertex_offset + i * 2 + 1
            next_left = vertex_offset + (i + 1) * 2
            next_right = vertex_offset + (i + 1) * 2 + 1
            
            # Create two triangular faces for the quad
            face1 = (curr_left, curr_right, next_right)
            face2 = (curr_left, next_right, next_left)
            
            all_faces.extend([face1, face2])
            all_material_indices.extend([material_index, material_index])
    
    def create_mesh_from_data(self, bm, hair_data):
        """
        Efficiently populates the bmesh using pre-calculated geometry data.
        This is the bulk creation step that applies all the calculated hair geometry at once.
        Preserves material inheritance and UV coordinate assignments.
        """
        vertices = hair_data["vertices"]
        faces = hair_data["faces"]
        material_indices = hair_data["material_indices"]
        uv_coords = hair_data["uv_coords"]
        
        if not vertices or not faces:
            print("No geometry data to create.")
            return
        
        print(f"Creating mesh from {len(vertices):,} vertices and {len(faces):,} faces")
        
        # Step 1: Bulk-create all vertices
        bm_verts = [bm.verts.new(coord) for coord in vertices]
        
        # Step 2: Ensure lookup table is updated after adding all vertices
        bm.verts.ensure_lookup_table()
        
        # Step 3: Set up UV layer if we have UV coordinates
        uv_layer = None
        if uv_coords and len(uv_coords) > 0:
            # Ensure UV layer exists
            if not bm.loops.layers.uv:
                uv_layer = bm.loops.layers.uv.new("UVMap")
            else:
                uv_layer = bm.loops.layers.uv.active
        
        # Step 4: Bulk-create all faces with material assignment
        created_faces = 0
        skipped_faces = 0
        
        for i, face_indices in enumerate(faces):
            try:
                # Get the bmesh vertices using the indices
                face_verts = [bm_verts[index] for index in face_indices]
                
                # Create the face
                new_face = bm.faces.new(face_verts)
                
                # CRITICAL STEP FOR MATERIAL INHERITANCE
                # Assign the material index we stored earlier
                if i < len(material_indices):
                    new_face.material_index = material_indices[i]
                
                # Assign UV coordinates if available
                if uv_layer and uv_coords:
                    for loop_idx, loop in enumerate(new_face.loops):
                        # Calculate the UV coordinate index for this loop
                        # This maps back to the vertex UV we calculated earlier
                        vertex_idx = face_indices[loop_idx]
                        if vertex_idx < len(uv_coords):
                            loop[uv_layer].uv = uv_coords[vertex_idx]
                
                created_faces += 1
                
            except IndexError as e:
                print(f"Skipping face {i} with invalid vertex index: {e}")
                skipped_faces += 1
                continue
            except ValueError as e:
                # bmesh will raise ValueError for invalid faces (e.g., non-manifold)
                # We can safely ignore these
                skipped_faces += 1
                continue
        
        # Step 5: Update bmesh indices and normals
        bm.faces.ensure_lookup_table()
        bm.normal_update()
        
        print(f"Successfully created {created_faces:,} faces, skipped {skipped_faces} invalid faces")
        
        if created_faces == 0:
            print("WARNING: No faces were created! Check vertex indices and face definitions.")
    
    def distribute_points_on_surface(self, mesh, matrix_world, count, props):
        """Distribute points across the mesh surface using triangulated mesh for reliable sampling"""
        points_data = []
        
        # Check for UV layer
        if not mesh.uv_layers.active:
            if props.use_surface_color:
                self.report({'WARNING'}, "Emitter has no active UV map. Surface color sampling disabled.")
        
        uv_layer = mesh.uv_layers.active.data if mesh.uv_layers.active else None
        
        # Get vertex group for density distribution
        vertex_group = None
        if props.distribution_mode == 'DENSITY' and props.density_vertex_group:
            vertex_group_idx = props.emitter_object.vertex_groups.find(props.density_vertex_group)
            if vertex_group_idx != -1:
                vertex_group = props.emitter_object.vertex_groups[vertex_group_idx]
            else:
                self.report({'WARNING'}, f"Vertex group '{props.density_vertex_group}' not found. Using default distribution.")
        
        # Triangulate the mesh for reliable sampling
        mesh.calc_loop_triangles()
        
        # Build triangle area list for weighted selection
        tri_areas = [tri.area for tri in mesh.loop_triangles]
        total_area = sum(tri_areas)
        
        if total_area == 0:
            self.report({'ERROR'}, "Emitter mesh has zero surface area.")
            return []
        
        tri_probs = [area / total_area for area in tri_areas]
        
        # For rejection sampling methods, we may need more attempts
        max_attempts = count * 10  # Allow up to 10x attempts for rejection sampling
        attempts = 0
        
        while len(points_data) < count and attempts < max_attempts:
            attempts += 1
            
            # Select a triangle based on area
            tri_idx = self.weighted_random_choice(tri_probs)
            tri = mesh.loop_triangles[tri_idx]
            
            # Apply slope masking first (cheapest check)
            if props.use_slope_mask:
                world_normal = (matrix_world.to_3x3() @ tri.normal).normalized()
                up_vector = Vector((0, 0, 1))
                slope_angle = world_normal.angle(up_vector)
                if slope_angle > props.slope_max_angle:
                    continue  # Reject this triangle and try another
            
            # Get random barycentric coordinates for the triangle
            r1, r2 = random.random(), random.random()
            if r1 + r2 > 1.0:
                r1, r2 = 1.0 - r1, 1.0 - r2
            r3 = 1.0 - r1 - r2
            
            # Get vertex and loop indices from the triangle
            v1_idx, v2_idx, v3_idx = tri.vertices
            l1_idx, l2_idx, l3_idx = tri.loops
            
            # Get vertex positions
            v1 = mesh.vertices[v1_idx].co
            v2 = mesh.vertices[v2_idx].co
            v3 = mesh.vertices[v3_idx].co
            
            # Calculate position and normal (in local space when matrix_world is identity)
            local_pos = v1 * r1 + v2 * r2 + v3 * r3
            world_pos = matrix_world @ local_pos
            world_normal = (matrix_world.to_3x3() @ tri.normal).normalized()
            
            # Apply distribution mode filtering
            accept_point = True
            
            if props.distribution_mode == 'DENSITY' and vertex_group:
                # Interpolate vertex weights using barycentric coordinates
                try:
                    w1 = vertex_group.weight(v1_idx)
                except RuntimeError:
                    w1 = 0.0
                try:
                    w2 = vertex_group.weight(v2_idx)
                except RuntimeError:
                    w2 = 0.0
                try:
                    w3 = vertex_group.weight(v3_idx)
                except RuntimeError:
                    w3 = 0.0
                
                interpolated_weight = w1 * r1 + w2 * r2 + w3 * r3
                
                # Use weight as probability (0.0 = never accept, 1.0 = always accept)
                if random.random() > interpolated_weight:
                    accept_point = False
            
            elif props.distribution_mode == 'NOISE':
                # Calculate noise value at world position
                noise_value = noise.noise(world_pos * props.noise_distribution_scale)
                # Normalize noise from [-1, 1] to [0, 1]
                noise_value = (noise_value + 1.0) * 0.5
                
                # Apply threshold (areas below threshold are rejected)
                if noise_value < props.noise_distribution_threshold:
                    accept_point = False
            
            if not accept_point:
                continue  # Reject this point and try another
            
            # Calculate UV coordinate
            uv_coord = None
            if uv_layer:
                uv1 = Vector(uv_layer[l1_idx].uv)
                uv2 = Vector(uv_layer[l2_idx].uv)
                uv3 = Vector(uv_layer[l3_idx].uv)
                uv_coord = uv1 * r1 + uv2 * r2 + uv3 * r3
            
            points_data.append({
                'position': world_pos,
                'normal': world_normal,
                'uv_coord': uv_coord,
                'face_index': tri.polygon_index,  # Store original face index for material inheritance
            })
        
        # Report if we couldn't generate enough points
        if len(points_data) < count:
            generated = len(points_data)
            self.report({'INFO'}, f"Generated {generated}/{count} points due to distribution constraints")
        
        return points_data
    
    def weighted_random_choice(self, weights):
        """Select index based on weights"""
        total = sum(weights)
        r = random.uniform(0, total)
        cumsum = 0
        for i, weight in enumerate(weights):
            cumsum += weight
            if r <= cumsum:
                return i
        return len(weights) - 1
    
    def calculate_hair_path(self, start_pos, normal, length, props):
        """Calculate the path points for a hair strand"""
        points = []
        segments = props.segments
        
        for i in range(segments + 1):
            t = i / segments
            
            # Base direction along normal
            direction = normal * props.normal_factor
            
            # Add gravity effect
            if props.gravity != 0:
                gravity_vec = Vector((0, 0, -props.gravity))
                direction += gravity_vec * t  # Increase effect along length
            
            # Add noise for natural variation
            if props.noise_factor > 0:
                noise_offset = Vector((
                    noise.noise(start_pos * props.noise_scale + Vector((0, 0, t * 10))),
                    noise.noise(start_pos * props.noise_scale + Vector((0, t * 10, 0))),
                    noise.noise(start_pos * props.noise_scale + Vector((t * 10, 0, 0)))
                )) * props.noise_factor * t
                direction += noise_offset
            
            # Add wave deformation
            if props.wave_frequency > 0 and props.wave_amplitude > 0:
                wave_offset = math.sin(t * props.wave_frequency * math.pi * 2) * props.wave_amplitude
                tangent = Vector((1, 0, 0))  # Simple tangent for wave
                direction += tangent * wave_offset
            
            # Add kink deformation
            if props.kink_frequency > 0 and props.kink_amplitude > 0:
                kink_offset = math.sin(t * props.kink_frequency * math.pi * 2) * props.kink_amplitude
                bitangent = Vector((0, 1, 0))  # Simple bitangent for kink
                direction += bitangent * kink_offset
            
            direction.normalize()
            
            # Calculate position
            pos = start_pos + direction * length * t
            points.append(pos)
        
        return points
    
    def calculate_hair_radii(self, point_count, props, is_child):
        """Calculate radius at each point along the strand"""
        radii = []
        root_radius = props.root_radius
        tip_radius = props.tip_radius
        
        # Reduce radius for children
        if is_child:
            root_radius *= 0.7
            tip_radius *= 0.7
        
        # Add random variation
        radius_mult = 1.0 + random.uniform(-props.radius_random, props.radius_random)
        root_radius *= radius_mult
        tip_radius *= radius_mult
        
        for i in range(point_count):
            t = i / (point_count - 1)
            # Linear interpolation from root to tip
            radius = root_radius * (1 - t) + tip_radius * t
            radii.append(radius)
        
        return radii
    
class MESH_HAIR_OT_Finalize(bpy.types.Operator):
    bl_idname = "mesh_hair.finalize"
    bl_label = "Finalize Hair"
    bl_description = "Convert preview hair to final mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hair_obj = bpy.data.objects.get("HairMesh_Preview")
        if not hair_obj:
            self.report({'ERROR'}, "No preview hair found")
            return {'CANCELLED'}
        
        props = context.scene.mesh_hair
        emitter_name = props.emitter_object.name if props.emitter_object else "Hair"
        
        # Rename to final name
        final_name = f"{emitter_name}_HairMesh"
        hair_obj.name = final_name
        hair_obj.data.name = final_name
        
        self.report({'INFO'}, f"Hair finalized as '{final_name}'")
        return {'FINISHED'}

class MESH_HAIR_OT_DeletePreview(bpy.types.Operator):
    bl_idname = "mesh_hair.delete_preview"
    bl_label = "Delete Preview"
    bl_description = "Delete the preview hair mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        hair_obj = bpy.data.objects.get("HairMesh_Preview")
        if hair_obj:
            bpy.data.objects.remove(hair_obj, do_unlink=True)
            self.report({'INFO'}, "Preview hair deleted")
        else:
            self.report({'WARNING'}, "No preview hair found")
        return {'FINISHED'}

class MESH_HAIR_OT_AddGuide(bpy.types.Operator):
    bl_idname = "mesh_hair.add_guide"
    bl_label = "Add Guide"
    bl_description = "Add a guide curve slot"

    def execute(self, context):
        props = context.scene.mesh_hair
        guide = props.guide_curves.add()
        return {'FINISHED'}

class MESH_HAIR_OT_RemoveGuide(bpy.types.Operator):
    bl_idname = "mesh_hair.remove_guide"
    bl_label = "Remove Guide"
    bl_description = "Remove guide curve"
    
    index: bpy.props.IntProperty()

    def execute(self, context):
        props = context.scene.mesh_hair
        props.guide_curves.remove(self.index)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MESH_HAIR_OT_Generate)
    bpy.utils.register_class(MESH_HAIR_OT_Finalize)
    bpy.utils.register_class(MESH_HAIR_OT_DeletePreview)
    bpy.utils.register_class(MESH_HAIR_OT_AddGuide)
    bpy.utils.register_class(MESH_HAIR_OT_RemoveGuide)

def unregister():
    bpy.utils.unregister_class(MESH_HAIR_OT_RemoveGuide)
    bpy.utils.unregister_class(MESH_HAIR_OT_AddGuide)
    bpy.utils.unregister_class(MESH_HAIR_OT_DeletePreview)
    bpy.utils.unregister_class(MESH_HAIR_OT_Finalize)
    bpy.utils.unregister_class(MESH_HAIR_OT_Generate)
