import bpy
import csv
import mathutils as mt
# globals

frames = []
rotation_frames = {}
hipy = []
hipx = []
class CSVPropertiesPanel(bpy.types.Panel):
    bl_label = "CSV Properties"
    bl_idname = "OBJECT_PT_csv_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        layout.prop(scene, "csv_file_path")
        layout.prop(scene, "armature_name")
#        print(bpy.data.scenes[0].csv_file_path)

        
        col = layout.column()
        col.operator("object.read_csv", text="Read CSV")
        
        row = layout.row()
        col = layout.column()
        col.label(text = "Modelling Properties")
        col.prop(scene, "avg_frames_per_sample")
        col.prop(scene, "min_frames_between_sample")
        col.prop(scene, "min_confidence")
         
        row = layout.row()      
        row = layout.row()
        row.operator("object.get_armature", text="Get Armature")
        row.operator("object.start_modeling", text="Model Armature")

class Rotation:
    def __init__(self, euler, bone, axis=None, axis_val=None, visibility = None):
        self.euler = euler
        self.bone = bone
        self.axis = axis
        self.axis_val = axis_val
        self.visibility = visibility

    def __str__(self):
        return f'{self.euler}, {self.visibility}, {self.bone}'

def assign_pt(b_name, ld_vec, ref_vec, swizzle):
    ld_vec = swizzle(ld_vec)
    diff = ref_vec.rotation_difference(ld_vec).to_euler()
    bpy.context.object.pose.bones[b_name].rotation_euler = diff
    
def assign_pt_by_bone(bone, ld_vec, ref_vec, swizzle):
    ld_vec = swizzle(ld_vec)
    diff = ref_vec.rotation_difference(ld_vec).to_euler()
    bone.rotation_euler = diff

def swizzle_l_shoulder(vec):
    return -vec.z, vec.x,-vec.y

def swizzle_r_shoulder(vec):
    return vec.z,-vec.x,-vec.y

def swizzle_l_thigh(vec):
    return -vec.x, vec.y, -vec.z
    # return vec

def swizzle_default(vec):
    return vec


# clean these up

def insert_frame(bone, time, ld_vec, ref_vec, swizzle, visibility = 1.0, rotations = None):
#    assign_pt_by_bone(bone, ld_vec, ref_vec, swizzle)
    # @nisan here
   
    ld_vec = swizzle(ld_vec)
    diff = ref_vec.rotation_difference(ld_vec).to_euler()
#        euler, bone, axis=None, axis_val=None, visibility = None
    if rotations != None:
        rotations[bone.name].append(Rotation(diff, bone.name, visibility = visibility))
    #if visibility >= 0.5:
    #    bone.keyframe_insert(data_path="rotation_euler",frame=time)

class GetArmatureOperator(bpy.types.Operator):
    bl_idname = "object.get_armature"
    bl_label = "Get Armature"
    
    def execute(self, context):
        CO = bpy.context.object
        if CO.type == 'ARMATURE':
            bpy.data.scenes[0].armature_name = CO.name_full
            self.report({'INFO'}, "Armature Selected in Add-on" ) 
        elif CO.parent.type == "ARMATURE":
            self.report({'INFO'}, "Armature Selected from parent of Mesh in Add-on" ) 
            bpy.data.scenes[0].armature_name = CO.parent.name_full    
        else:
            print("Couldn't find linked armature")
            self.report({'ERROR'}, f"Couldn't Find linked Armature" )
         
        return {'FINISHED'}

class ReadCSVOperator(bpy.types.Operator):
    bl_idname = "object.read_csv"
    bl_label = "Read CSV"
    #filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        global frames
        frames = []
        scene = context.scene
#        csv_path = "D:\Download\input - Sheet1.csv"
        csv_path = bpy.data.scenes[0].csv_file_path
        try:
            with open(csv_path) as csv_file:
                csv_reader = csv.reader(csv_file)
                frame = []
                for row in csv_reader:
                    if row == ['index','x','y','z','vis']:
                        pass
                    elif row[0] == '-1':
                        frames.append(frame)
                        frame = []
                    else:
                        index,x,y,z,vis = row
                        scale = 0.3
                        frame.append([int(index), float(x), float(y), float(z) * scale, float(vis)])
                    #bpy.ops.mesh.primitive_uv_sphere_add(radius = 1,location=(x, y, 0))
        # print(data)
        
        
            print("CSV Reading: Complete")
            self.report({'INFO'}, "CSV Reading: Complete" )

        except Exception as e:
            print(f"CSV Reading Failed.\nReason: {e}")
            self.report({'ERROR'}, f"CSV Reading Failed.\nReason: {e}" )
        
        return {'FINISHED'}

# landmark_vectors = {}
swizzle_functions = {
    'l_shoulder' : swizzle_l_shoulder, 
    'l_forearm' : swizzle_l_shoulder,
    'r_shoulder' : swizzle_r_shoulder,
    'r_forearm' : swizzle_r_shoulder,
    'l_thigh': swizzle_l_thigh, # calculate what this should be, reusing for now
    'r_thigh': swizzle_l_thigh,
    'l_shin' : swizzle_l_thigh,
    'r_shin' : swizzle_l_thigh,
}

reference_vectors = {
    'l_shoulder' : mt.Vector([0, 1, 0]),                    
    'l_forearm' : mt.Vector([0, 1, 0]),
    'r_shoulder' : mt.Vector([0, 1, 0]),
    'r_forearm' : mt.Vector([0, 1, 0]),
    #'l_thigh': mt.Vector([-0.12187,0.99255,0]) 
    'l_thigh' : mt.Vector([-0.12187,0.99255,0]),
    'r_thigh' : mt.Vector([0.12187,0.99255,0]),
}


"""
                    ld_vec = landmarks[25] - landmarks[23]
#bpy.context.object.pose.bones['l_thigh'].rotation_euler = Euler([0,0,radians(-7)],"XYZ")
                    ref_vec = 
                    ld_vec.x,ld_vec.y,ld_vec.z = 

                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    bpy.context.object.pose.bones['l_thigh'].rotation_euler = diff  

"""

class StartModelingOperator(bpy.types.Operator):
    bl_idname = "object.start_modeling"
    bl_label = "Model"
    
    
    def execute(self, context):  
        global frames
        global rotaion_frames
        
        armature_name = bpy.data.scenes[0].armature_name
        armature = bpy.data.objects[armature_name]
        AFPS = bpy.data.scenes[0].avg_frames_per_sample
        MFBS = bpy.data.scenes[0].min_frames_between_sample
        min_conf = bpy.data.scenes[0].min_confidence
        
#        print(AFPS)
        
        # clear all animations
        #for bone in  bpy.data.armatures[armature_name].bones:
        #    bone.select = True
        #    bpy.ops.anim.keyframe_clear_v3d()
        #    bone.select = False    
        armature.animation_data_clear()
        

        
        # set mode to pose mode if its already not set
        if bpy.context.mode != 'POSE':
            bpy.ops.object.posemode_toggle()
        
        # turn off inherit rotaion for all bones and reset them to default T pose
        for i in armature.data.bones:
            i.use_inherit_rotation = i.name in [ 'head_end', 'r_hand_end', 'l_hand_end', 'l_hand', 'r_hand', 'r_foot', 'r_foot_end', 'l_foot', 'l_foot_end']

        for i in armature.pose.bones:
            i.rotation_mode = 'XYZ'
            i.rotation_euler = mt.Euler((0,0,0),"XYZ")
            i.location = mt.Vector()

        frame_counter = 0
        visibility = {}
        
        hipy = []
        hipx = []
        
        for bone in armature.pose.bones:
            rotation_frames[bone.name] = []
        for frame_points in frames:
            
            # @nisan here
            # rotation_frames = []
            
            
            visibilities = [pt[4] for pt in frame_points]
            landmarks = [mt.Vector(pt[1:4]) for pt in frame_points]
            # print(landmarks)
            landmark_vectors = {}          
            # grab all desired landmark vectors
            try:
                landmark_vectors['l_shoulder'] = (landmarks[13] - landmarks[11]).normalized() 
                landmark_vectors['l_forearm'] = (landmarks[15] - landmarks[13]).normalized()
                landmark_vectors['r_shoulder'] = (landmarks[14] - landmarks[12]).normalized()
                landmark_vectors['r_forearm'] = (landmarks[16] - landmarks[14]).normalized()
                landmark_vectors['l_thigh'] = (landmarks[25] - landmarks[23]).normalized()
                landmark_vectors['r_thigh'] = (landmarks[26] - landmarks[24]).normalized()
                landmark_vectors['l_shin'] = (landmarks[27] - landmarks[25]).normalized()
                landmark_vectors['r_shin'] = (landmarks[28] - landmarks[26]).normalized()

                visibility['l_shoulder'] = min(visibilities[13], visibilities[11])
                visibility['l_forearm'] = min(visibilities[15], visibilities[13])
                visibility['r_shoulder'] = min(visibilities[14], visibilities[12])
                visibility['r_forearm'] = min(visibilities[16], visibilities[14])
                visibility['l_thigh'] = min(visibilities[25], visibilities[23])
                visibility['r_thigh'] = min(visibilities[26], visibilities[24])
                visibility['l_shin'] = min(visibilities[27], visibilities[25])
                visibility['r_shin'] = min(visibilities[28], visibilities[26])
                visibility['head'] = min( [visibilities[x] for x in range(0,7)] + [visibilities[x] for x in range(9,11)])
                visibility['body'] = min( [visibilities[x] for x in [11,12,23,24]  ])
                visibility['waist'] = min( [visibilities[x] for x in [11,12,23,24]  ])

            except Exception as e:
                self.report({'ERROR'}, f"landmark and visibility assignement error: {e}" )

                pass
            
            hipx.append( (landmarks[23].x +  landmarks[23].x)/2 )
            hipy.append( (landmarks[23].y +  landmarks[23].y)/2 )

            for bone in armature.pose.bones:
                # insert_frame(armature.pose.bones['l_shoulder'], (0, 20), (landmarks[13] - landmarks[11]).normalized(), mt.Vector([0, 1, 0]), swizzle_l_shoulder)
                if bone.name == 'head_end':
                    continue
                # elif bone.name == 'r_ankle':

                elif bone.name == 'head':
                    t= {}
                    for i in range(3):
                        t[i+1] = (landmarks[i+1]+landmarks[i+4])/2  
                    t[4] = (landmarks[9]+landmarks[10])/2
                    sum_eye = (t[1]+t[2]+t[3])/3
                    sum_mouth_and_nose = (t[4]+sum_eye+landmarks[0])/3
                    v1 = landmarks[5]
                    v2 = landmarks[2]
                    v3 = sum_eye
                    v4 = sum_mouth_and_nose

                    ld_vec = v2-v1
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    ref_vec = mt.Vector([1,0,0])
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    yrot = diff.y
                    #bpy.context.object.pose.bones['body'].rotation_euler = diff

                    m1  = v3
                    m2  = v4
                    rm = (m1-m2)
                    ld_vec = rm
                    ref_vec = mt.Vector([0,1,0])
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    ##diff.y = yrotto_

                    # @nisan here
                    #bone.rotation_euler = diff
                    #bone.rotation_euler.rotate_axis("Y",yrot)

                    #bone.keyframe_insert(data_path="rotation_euler",frame=frame_counter)
                    #  euler, bone, axis=None, axis_val=None, visibility = None
                    rotation_frames[bone.name].append(Rotation(diff, bone.name, "Y", yrot, visibility.get(bone.name, 0)))
                    # print(len(rotation_frames[bone.name]))
                elif bone.name == 'body':
                    v1 = landmarks[12]
                    v2 = landmarks[11]
                    v3 = landmarks[24]
                    v4 = landmarks[23]

                    ld_vec  = v2-v1
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    ref_vec = mt.Vector([1,0,0])
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    yrot = diff.y
                    #bpy.context.object.pose.bones['body'].rotation_euler = diff

                    m1  = (v2+v1)/2
                    m2  = (v4+v3)/2
                    rm = (m1-m2)/2
                    ld_vec = rm
                    ref_vec = mt.Vector([0,1,0])
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    ##diff.y = yrotto_
                    # @nisan here
                    #bone.rotation_euler = diff
                    #bone.rotation_euler.rotate_axis("Y",yrot)

                    #bone.keyframe_insert(data_path="rotation_euler",frame=frame_counter)
                    rotation_frames[bone.name].append(Rotation(diff, bone.name, "Y", yrot, visibility.get(bone.name, 0)))
                elif bone.name == 'waist':
                    v1 = landmarks[12]
                    v2 = landmarks[11]
                    v3 = landmarks[24]
                    v4 = landmarks[23]

                    ld_vec = v4-v3
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    ref_vec = mt.Vector([1,0,0])
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    yrot = diff.y
                    #bpy.context.object.pose.bones['body'].rotation_euler = diff

                    m1  = (v2+v1)/2
                    m2  = (v4+v3)/2
                    rm = (m1-m2)/2
                    ld_vec = rm
                    ref_vec = mt.Vector([0,1,0])
                    ld_vec.x,ld_vec.y,ld_vec.z = ld_vec.x ,  -ld_vec.y,  -ld_vec.z
                    diff = ref_vec.rotation_difference(ld_vec).to_euler()
                    ##diff.y = yrotto_
                    
                    # @nisan here
                    #bone.rotation_euler = diff
                    #bone.rotation_euler.rotate_axis("Y",yrot)

                    #bone.keyframe_insert(data_path="rotation_euler",frame=frame_counter)
                    rotation_frames[bone.name].append(Rotation(diff, bone.name, "Y", yrot, visibility.get(bone.name, 0)))
                else:
                    insert_frame(bone, frame_counter, \
                    landmark_vectors.get(bone.name, mt.Vector()), \
                    reference_vectors.get(bone.name, mt.Vector()), \
                    swizzle_functions.get(bone.name, swizzle_default), visibility.get(bone.name, 0), rotation_frames)
                

                # if not first:
                #     lis = [landmarks,lm,lm1,lm2]
                #     for i in range(len(lis)):
                #         hip_center.append((lis[i][24]/2 + lis[i][23]/2))
                #     diff = []
                #     for i in range(len(hip_center)-1):
                #         diff.append(current_hip - prev_hip)
                #     for i in range(len(diff)):
                #     #    bone.keyframe_insert(data_path="rotation_euler",frame=time)
                #         bpy.context.object.pose.bones['waist'].location.x += diff[i].x
                #         bpy.context.object.pose.bones['waist'].location.z += diff[i].y
                #         bpy.context.object.pose.bones['waist'].keyframe_insert(data_path="location",index = 0,frame=i)
                #         bpy.context.object.pose.bones['waist'].keyframe_insert(data_path="location",index = 1,frame=i)
                # prev_hip = current_hip

            frame_counter += 1
            # rotation_frames.append(rotation_frames)
        # hip_center = []
        # for i in range(len(frames)):
        #     hip_center.append((mt.Vector(frames[i][24])/2 + mt.Vector(frames[i][23])/2))

        # diff = []
        # for i in range(1, len(hip_center)):
        #     diff.append(hip_center[i -1] - hip_center[i])
        # for i in range(len(diff)):
        #     armature.pose.bones['waist'].location.x += diff[i].x
        #     armature.pose.bones['waist'].location.y += diff[i].y * 2
        #     armature.pose.bones['waist'].keyframe_insert(data_path="location",frame=i)
        # print(rotation_frames)
        
        if AFPS > len(rotation_frames["body"]):
            AFPS = len(rotation_frames["body"])
        if AFPS<MFBS:
            AFPS = MFBS+1
        print(AFPS , MFBS , min_conf/100)
        
        
        for bone in rotation_frames.keys():
            l_index =0
            for i in range(0,len(rotation_frames[bone]),AFPS):
                index = 0
#                if i<l_index:
#                    print("break")
#                    continue
#                var = i - l_index
                
                i = l_index + MFBS
                sample_visib = [x.visibility for x in rotation_frames[bone][i:i + AFPS ]]
                if len(sample_visib) == 0:
                    continue
                max_visib = max(sample_visib)
#                print(min_conf)
                
                if max_visib > min_conf/100.0:
                    index = sample_visib.index(max_visib) + i
                    if bone == "body":
                        print(f"index {index} , i: {i}, l_index: {l_index}")
                    l_index = index
#                    print("hehre")     
                    armature.pose.bones[bone].rotation_euler = rotation_frames[bone][index].euler
                    if rotation_frames[bone][index].axis != None:
                        armature.pose.bones[bone].rotation_euler.rotate_axis(rotation_frames[bone][index].axis, rotation_frames[bone][index].axis_val)
                    armature.pose.bones[bone].keyframe_insert(data_path="rotation_euler",frame=index)
#                    i +=     
                else:
                    sample_visib = [x.visibility for x in rotation_frames[bone][i:i + AFPS * 2]]
                    max_visib = max(sample_visib)
                    index = sample_visib.index(max_visib) + i
                    l_index = index
#                    print("hehre")     
                    armature.pose.bones[bone].rotation_euler = rotation_frames[bone][index].euler
                    if rotation_frames[bone][index].axis != None:
                        armature.pose.bones[bone].rotation_euler.rotate_axis(rotation_frames[bone][index].axis, rotation_frames[bone][index].axis_val)
                    armature.pose.bones[bone].keyframe_insert(data_path="rotation_euler",frame=index)
        
        testy = hipy[0]
    
        armature.pose.bones['waist'].location.y = 0
        armature.pose.bones['waist'].keyframe_insert(data_path="location",index=1,frame=0)
                
        delta = 0
        for i in range(1,len(hipy)):
            delta += (testy - hipy[i])
            if abs(delta)>.1:
                testy = hipy[i]
                armature.pose.bones['waist'].location.y = hipy[i] - hipy[0]
                armature.pose.bones['waist'].keyframe_insert(data_path="location",index=1,frame=i)
                delta =0


        testx = hipx[0]
    
        armature.pose.bones['waist'].location.x = 0
        armature.pose.bones['waist'].keyframe_insert(data_path="location",index=0,frame=0)
                
        delta = 0
        for i in range(1,len(hipx)):
            delta += (testx - hipx[i])
            if abs(delta)>.1:
                testx = hipx[i]
                armature.pose.bones['waist'].location.x = hipx[i] - hipx[0]
                armature.pose.bones['waist'].keyframe_insert(data_path="location",index=0,frame=i)
                delta =0
    

    # def __init__(self, euler, bone, axis=None, axis_val=None, visibility = None):
    #     self.euler = euler
    #     self.bone = bone
    #     self.axis = axis
    #     self.axis_val = axis_val
    #     self.visibility = visibility
    #     print(rotation_frames)
        bpy.data.scenes["Scene"].frame_end = len(frames)
        return {'FINISHED'}

def register():
    bpy.utils.register_class(CSVPropertiesPanel)
    bpy.utils.register_class(ReadCSVOperator)
    
    bpy.utils.register_class(GetArmatureOperator)
    bpy.utils.register_class(StartModelingOperator)
    bpy.types.Scene.armature_name = bpy.props.StringProperty(name = "Armature Name")
    bpy.types.Scene.csv_file_path = bpy.props.StringProperty(subtype="FILE_PATH" , name="CSV File Path")
    bpy.types.Scene.avg_frames_per_sample = bpy.props.IntProperty(name = "Avg. Frames per Sample", min =1,max=90)
    bpy.types.Scene.min_frames_between_sample = bpy.props.IntProperty(name = "Min. Frames Between Samples", min =1,max=90)
    bpy.types.Scene.min_confidence = bpy.props.IntProperty(subtype="PERCENTAGE" , name="Minimum Confidence",min = 0, max = 100)



def unregister():
    del bpy.types.Scene.csv_file_path
    bpy.utils.unregister_class(CSVPropertiesPanel)
    bpy.utils.unregister_class(ReadCSVOperator)
    bpy.utils.unregister_class(StartModelingOperator)
    bpy.utils.unregister_class(GetArmatureOperator)
        
    
if __name__ == "__main__":    
    register()