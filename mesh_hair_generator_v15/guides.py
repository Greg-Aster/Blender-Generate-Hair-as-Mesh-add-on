import bpy
import bmesh
from mathutils import Vector, Matrix
import math

class GuideManager:
    """Handles guide curve operations and hair direction interpolation"""
    
    def __init__(self, guide_curves):
        self.guide_curves = guide_curves
        self.guide_data = []
        self.prepare_guides()
    
    def prepare_guides(self):
        """Prepare guide curve data for interpolation"""
        self.guide_data.clear()
        
        for guide in self.guide_curves:
            if guide.curve_object and guide.curve_object.type == 'CURVE':
                curve_data = self.extract_curve_data(guide.curve_object, guide.influence)
                if curve_data:
                    self.guide_data.append(curve_data)
    
    def extract_curve_data(self, curve_obj, influence):
        """Extract spline data from curve object"""
        if not curve_obj.data.splines:
            return None
        
        # Use the first spline
        spline = curve_obj.data.splines[0]
        
        points = []
        if spline.type == 'BEZIER':
            for point in spline.bezier_points:
                world_pos = curve_obj.matrix_world @ point.co
                points.append(world_pos)
        elif spline.type in ['NURBS', 'POLY']:
            for point in spline.points:
                world_pos = curve_obj.matrix_world @ Vector(point.co[:3])
                points.append(world_pos)
        
        if len(points) < 2:
            return None
        
        return {
            'points': points,
            'influence': influence,
            'length': self.calculate_curve_length(points)
        }
    
    def calculate_curve_length(self, points):
        """Calculate total length of curve"""
        length = 0
        for i in range(1, len(points)):
            length += (points[i] - points[i-1]).length
        return length
    
    def get_direction_at_point(self, position, surface_normal):
        """Get interpolated direction from guides at given position"""
        if not self.guide_data:
            return surface_normal
        
        # Find closest guide and interpolate
        closest_guide = None
        min_distance = float('inf')
        
        for guide in self.guide_data:
            distance = self.distance_to_curve(position, guide['points'])
            if distance < min_distance:
                min_distance = distance
                closest_guide = guide
        
        if not closest_guide:
            return surface_normal
        
        # Get direction from closest point on curve
        curve_direction = self.get_curve_direction_at_position(position, closest_guide['points'])
        
        # Blend with surface normal based on influence and distance
        influence = closest_guide['influence']
        
        # Reduce influence based on distance (falloff)
        distance_falloff = min(1.0, min_distance / 1.0)  # 1.0 unit falloff
        effective_influence = influence * (1.0 - distance_falloff)
        
        # Interpolate between surface normal and curve direction
        result_direction = surface_normal.lerp(curve_direction, effective_influence)
        result_direction.normalize()
        
        return result_direction
    
    def distance_to_curve(self, point, curve_points):
        """Calculate minimum distance from point to curve"""
        min_distance = float('inf')
        
        for i in range(len(curve_points) - 1):
            p1 = curve_points[i]
            p2 = curve_points[i + 1]
            
            # Distance from point to line segment
            distance = self.distance_point_to_segment(point, p1, p2)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def distance_point_to_segment(self, point, seg_start, seg_end):
        """Calculate distance from point to line segment"""
        segment = seg_end - seg_start
        segment_length_sq = segment.length_squared
        
        if segment_length_sq == 0:
            return (point - seg_start).length
        
        # Project point onto line segment
        t = max(0, min(1, (point - seg_start).dot(segment) / segment_length_sq))
        projection = seg_start + t * segment
        
        return (point - projection).length
    
    def get_curve_direction_at_position(self, position, curve_points):
        """Get curve direction at closest point"""
        closest_segment_idx = 0
        min_distance = float('inf')
        
        # Find closest segment
        for i in range(len(curve_points) - 1):
            p1 = curve_points[i]
            p2 = curve_points[i + 1]
            distance = self.distance_point_to_segment(position, p1, p2)
            
            if distance < min_distance:
                min_distance = distance
                closest_segment_idx = i
        
        # Get direction from closest segment
        if closest_segment_idx < len(curve_points) - 1:
            direction = curve_points[closest_segment_idx + 1] - curve_points[closest_segment_idx]
            direction.normalize()
            return direction
        
        return Vector((0, 0, 1))  # Default upward direction

class MESH_HAIR_OT_CreateGuideFromSelection(bpy.types.Operator):
    bl_idname = "mesh_hair.create_guide_from_selection"
    bl_label = "Create Guide from Selection"
    bl_description = "Create a guide curve from selected edges or vertices"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        # Check if we're in edit mode with a mesh selected
        if context.mode != 'EDIT_MESH':
            self.report({'ERROR'}, "Must be in Edit Mode with a mesh selected")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Active object must be a mesh")
            return {'CANCELLED'}
        
        # Get selected elements
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # Get selected vertices
        selected_verts = [v for v in obj.data.vertices if v.select]
        
        if len(selected_verts) < 2:
            self.report({'ERROR'}, "Select at least 2 vertices to create a guide")
            bpy.ops.object.mode_set(mode='EDIT')
            return {'CANCELLED'}
        
        # Create curve from selected vertices
        curve_data = bpy.data.curves.new(name="HairGuide", type='CURVE')
        curve_data.dimensions = '3D'
        
        spline = curve_data.splines.new(type='NURBS')
        spline.points.add(len(selected_verts) - 1)
        
        # Set point positions
        for i, vert in enumerate(selected_verts):
            world_pos = obj.matrix_world @ vert.co
            spline.points[i].co = (*world_pos, 1.0)
        
        # Create curve object
        curve_obj = bpy.data.objects.new("HairGuide", curve_data)
        context.collection.objects.link(curve_obj)
        
        # Add to guides list
        props = context.scene.mesh_hair
        guide = props.guide_curves.add()
        guide.curve_object = curve_obj
        guide.influence = 1.0
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        self.report({'INFO'}, f"Created guide curve with {len(selected_verts)} points")
        return {'FINISHED'}

class MESH_HAIR_OT_ClearGuides(bpy.types.Operator):
    bl_idname = "mesh_hair.clear_guides"
    bl_label = "Clear All Guides"
    bl_description = "Remove all guide curves"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.mesh_hair
        props.guide_curves.clear()
        self.report({'INFO'}, "Cleared all guide curves")
        return {'FINISHED'}

class MESH_HAIR_OT_SelectGuideObjects(bpy.types.Operator):
    bl_idname = "mesh_hair.select_guide_objects"
    bl_label = "Select Guide Objects"
    bl_description = "Select all guide curve objects in the scene"

    def execute(self, context):
        props = context.scene.mesh_hair
        
        bpy.ops.object.select_all(action='DESELECT')
        
        selected_count = 0
        for guide in props.guide_curves:
            if guide.curve_object:
                guide.curve_object.select_set(True)
                selected_count += 1
        
        if selected_count > 0:
            self.report({'INFO'}, f"Selected {selected_count} guide objects")
        else:
            self.report({'WARNING'}, "No guide objects found")
        
        return {'FINISHED'}

def register():
    bpy.utils.register_class(MESH_HAIR_OT_CreateGuideFromSelection)
    bpy.utils.register_class(MESH_HAIR_OT_ClearGuides)
    bpy.utils.register_class(MESH_HAIR_OT_SelectGuideObjects)

def unregister():
    bpy.utils.unregister_class(MESH_HAIR_OT_SelectGuideObjects)
    bpy.utils.unregister_class(MESH_HAIR_OT_ClearGuides)
    bpy.utils.unregister_class(MESH_HAIR_OT_CreateGuideFromSelection)