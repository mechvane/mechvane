"""Render the logo showcase (tools/build_logo_showcase.py) in Blender with Cycles.

    blender -b --python render_logo_blender.py   (copied into the folder with the OBJ files, logo_looks.json, env.hdr)

Runs inside Blender (5.x). Reads the OBJ files next to it, sets each material straight on the Principled
BSDF from an OpenPBR-style parameter set (the route proposed in ADR 0004), and builds a dark studio: the
background stays near black, while a circuit board with components above the model shows only in the
reflections (invisible to the camera). Writes logo_showcase.png into $BLENDER_OUT.
"""
import json
import math
import os
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent if "__file__" in dir() else Path.cwd()
JOB = Path(os.environ.get("BLENDER_JOB", HERE))
OUT = Path(os.environ.get("BLENDER_OUT", JOB / "out"))
SCALE = 0.01  # 1 Blender unit = 100 mm

# Appearance per surface as OpenPBR parameters, shared with tools/logo_to_gltf.py
_spec = json.loads((JOB / "logo_looks.json").read_text())
LOOKS, BODY_LOOK = _spec["looks"], _spec["bodies"]


def brushed_finish(mat):
    """Brushing direction and fine grinding marks on a Principled material. glTF carries the anisotropy
    strength but Blender's importer (5.2) drops the direction, so the glTF route calls this after import."""
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    # straight brushing: tangents round the X axis run along Y on the flat faces
    tangent = mat.node_tree.nodes.new("ShaderNodeTangent")
    tangent.direction_type = "RADIAL"
    tangent.axis = "X"
    mat.node_tree.links.new(tangent.outputs["Tangent"], bsdf.inputs["Tangent"])
    # fine grinding marks: noise stretched along Y, as a faint bump
    nt = mat.node_tree
    coord = nt.nodes.new("ShaderNodeNewGeometry")   # world position: same marks for OBJ (mm) and glTF
    stretch = nt.nodes.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (90000.0, 600.0, 90000.0)  # 1 Blender unit = 100 mm
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Detail"].default_value = 8.0
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    nt.links.new(coord.outputs["Position"], stretch.inputs["Vector"])
    nt.links.new(stretch.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def principled(name, p):
    """Material with a Principled BSDF set from an OpenPBR-style parameter dict."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*p["base_color"], 1.0)
    bsdf.inputs["Metallic"].default_value = p.get("base_metalness", 0.0)
    bsdf.inputs["Roughness"].default_value = p.get("specular_roughness", 0.3)
    bsdf.inputs["Anisotropic"].default_value = p.get("specular_anisotropy", 0.0)
    bsdf.inputs["Coat Weight"].default_value = p.get("coat_weight", 0.0)
    bsdf.inputs["Coat Roughness"].default_value = p.get("coat_roughness", 0.03)
    if p.get("specular_anisotropy"):
        brushed_finish(mat)
    return mat


def emissive(name, color, strength):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def reflection_only(obj):
    """Seen in reflections, never by the camera, no shadows on the model."""
    obj.visible_camera = False
    obj.visible_shadow = False
    obj.visible_diffuse = False


def box(name, size, loc, mat, rot=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=(0, 0, rot))
    o = bpy.context.object
    o.name = name
    o.scale = size
    o.data.materials.append(mat)
    reflection_only(o)
    return o


def cylinder(name, r, h, loc, mat):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=loc, vertices=24)
    o = bpy.context.object
    o.name = name
    o.data.materials.append(mat)
    reflection_only(o)
    return o


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
mats = {k: principled(k, v) for k, v in LOOKS.items()}

ROUTE = os.environ.get("ROUTE", "direct")  # direct: OpenPBR values set here; gltf: Blender's glTF importer


def import_gltf():
    """Route B of ADR 0004: logo.gltf (tools/logo_to_gltf.py) through Blender's own importer."""
    bpy.ops.import_scene.gltf(filepath=str(JOB / "logo.gltf"))  # normals come from the file
    for m in bpy.data.materials:
        look = LOOKS.get(m.name.split(".")[0])
        if look and look.get("specular_anisotropy") and m.users and m.name not in LOOKS:
            brushed_finish(m)


def import_direct():
    """Route A: OBJ meshes, materials set straight on the Principled BSDF."""
    for obj_file in sorted(JOB.glob("*.obj")):
        _import_obj(obj_file)


def _import_obj(obj_file):
    bpy.ops.wm.obj_import(filepath=str(obj_file), forward_axis="Y", up_axis="Z")
    for o in bpy.context.selected_objects:
        o.name = obj_file.stem
        o.scale = (SCALE, SCALE, SCALE)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
        o.data.materials.clear()
        if obj_file.stem in ("Plate", "M"):
            # back plate dark, the raised M light: by face height (the plate is 6 mm thick)
            o.data.materials.append(mats["coat_dark"])
            o.data.materials.append(mats["coat_light"])
            o.data.materials.append(mats["weld"])
            for poly in o.data.polygons:
                slanted = 0.15 < abs(poly.normal.z) < 0.97
                if 6.0 < poly.center.z < 8.2 and slanted:
                    poly.material_index = 2   # concave fillet weld at the foot of the M
                else:
                    poly.material_index = 1 if poly.center.z > 6.3 else 0
        else:
            o.data.materials.append(mats[BODY_LOOK.get(obj_file.stem, "steel_brushed")])


(import_gltf if ROUTE == "gltf" else import_direct)()
bpy.ops.object.select_all(action="DESELECT")

# Lights: soft boxes aimed at the model, invisible to the camera by nature
def aimed_light(name, loc, energy, size, target_loc):
    bpy.ops.object.light_add(type="AREA", location=loc)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.size = size
    aim = bpy.data.objects.new(name + "Aim", None)
    aim.location = target_loc
    scene.collection.objects.link(aim)
    c = light.constraints.new("TRACK_TO")
    c.target = aim
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return light


aimed_light("Key", (2.0, -1.2, 1.3), 40, 1.2, (0.5, 0.5, 0.0))
aimed_light("Fill", (-1.6, -0.6, 1.1), 8, 2.0, (0.5, 0.5, 0.0))
aimed_light("Rim", (0.4, 2.6, 0.9), 60, 1.0, (0.5, 0.5, 0.1))

# Camera: "iso" from the front right, "top" straight down (VIEW)
VIEW = os.environ.get("VIEW", "iso")
target = bpy.data.objects.new("Target", None)
target.location = (0.5, 0.52, 0.06)
scene.collection.objects.link(target)
if VIEW == "top":
    bpy.ops.object.camera_add(location=(0.5, 0.5, 4.2), rotation=(0, 0, 0))
    cam = bpy.context.object
    cam.data.lens = 120   # long lens: little perspective, the plate stays square
else:
    bpy.ops.object.camera_add(location=(1.95, -1.55, 1.35))
    cam = bpy.context.object
    cam.data.lens = 55
    track = cam.constraints.new("TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
scene.camera = cam
cam.data.dof.use_dof = True
cam.data.dof.focus_object = target
cam.data.dof.aperture_fstop = 5.6

# Background: the camera sees plain dark grey, everything else (reflections, light) sees the panorama
# env.hdr next to this script (Poly Haven "Vintage Measuring Lab", CC0)
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
env = nt.nodes.new("ShaderNodeTexEnvironment")
env.image = bpy.data.images.load(str(JOB / "env.hdr"))
mapping = nt.nodes.new("ShaderNodeMapping")
mapping.inputs["Rotation"].default_value = (0, 0, math.radians(float(os.environ.get("ENV_ROT", "310"))))
coord = nt.nodes.new("ShaderNodeTexCoord")
nt.links.new(coord.outputs["Generated"], mapping.inputs["Vector"])
nt.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
dark = nt.nodes.new("ShaderNodeBackground")
dark.inputs["Color"].default_value = (0.012, 0.012, 0.014, 1)
env_bg = nt.nodes.new("ShaderNodeBackground")
env_bg.inputs["Strength"].default_value = 0.55
nt.links.new(env.outputs["Color"], env_bg.inputs["Color"])
path = nt.nodes.new("ShaderNodeLightPath")
mix = nt.nodes.new("ShaderNodeMixShader")
nt.links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
nt.links.new(env_bg.outputs["Background"], mix.inputs[1])
nt.links.new(dark.outputs["Background"], mix.inputs[2])
nt.links.new(mix.outputs["Shader"], nt.nodes["World Output"].inputs["Surface"])
nt.nodes.remove(bg)

scene.render.engine = "CYCLES"
prefs = bpy.context.preferences.addons["cycles"].preferences
for backend in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = backend
        prefs.get_devices()
        if any(d.type == backend for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == backend
            scene.cycles.device = "GPU"
            break
    except TypeError:
        continue
scene.cycles.samples = int(os.environ.get("SAMPLES", "256"))
scene.cycles.use_denoising = True
scene.render.resolution_x, scene.render.resolution_y = (int(x) for x in os.environ.get("RES", "1600x1200").split("x"))
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
OUT.mkdir(parents=True, exist_ok=True)
SUFFIX = ROUTE + ("_top" if VIEW == "top" else "")
scene.render.filepath = str(OUT / f"logo_showcase_{SUFFIX}.png")
# what actually reached the Principled BSDF, per material, for comparing the two routes
inputs = ("Base Color", "Metallic", "Roughness", "IOR", "Anisotropic", "Anisotropic Rotation", "Coat Weight",
          "Coat Roughness", "Specular IOR Level")
report = {}
for m in bpy.data.materials:
    if not m.use_nodes:
        continue
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if b is None:
        continue
    vals = {}
    for k in inputs:
        sock = b.inputs.get(k)
        if sock is None:
            continue
        v = sock.default_value
        vals[k] = [round(x, 4) for x in v][:3] if hasattr(v, "__len__") else round(v, 4)
        if sock.is_linked:
            vals[k] = f"linked: {sock.links[0].from_node.type}"
    report[m.name] = vals
(OUT / f"principled_{ROUTE}.json").write_text(json.dumps(report, indent=1))
# the scene itself, with the panorama referenced next to it (copy env.hdr beside the .blend)
env.image.filepath = "//env.hdr"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"logo_showcase_{SUFFIX}.blend"), compress=True)
env.image.filepath = str(JOB / "env.hdr")
bpy.ops.render.render(write_still=True)
print("rendered", scene.render.filepath, "on", scene.cycles.device)
