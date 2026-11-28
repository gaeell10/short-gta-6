"""Shared helpers for the 3D cartoon scenes (Blender bpy module)."""
import math
import bpy
from mathutils import Vector

C = bpy.context


def reset(res=(720, 1280), samples=16, engine="CYCLES"):
    global OUTLINE
    OUTLINE = None
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = engine
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False
    if engine == "CYCLES":
        sc.cycles.device = "CPU"
        sc.cycles.samples = samples
        sc.cycles.use_denoising = True
        sc.cycles.max_bounces = 4
        sc.cycles.diffuse_bounces = 2
        sc.cycles.glossy_bounces = 2
        sc.cycles.transmission_bounces = 2
        sc.cycles.use_adaptive_sampling = True
    sc.view_settings.view_transform = "Standard"
    sc.view_settings.look = "None"
    w = bpy.data.worlds.new("W")
    sc.world = w
    w.use_nodes = True
    return sc


def world_color(col, strength=1.0):
    bg = bpy.context.scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value = (*col, 1)
    bg.inputs[1].default_value = strength


def world_gradient(top, bottom, strength=1.0, stars=False):
    """Camera-ray gradient sky (vertical), optional procedural stars."""
    nt = bpy.context.scene.world.node_tree
    n = nt.nodes
    bg = n["Background"]
    tc = n.new("ShaderNodeTexCoord")
    sep = n.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Window"], sep.inputs[0])
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*bottom, 1)
    ramp.color_ramp.elements[1].color = (*top, 1)
    nt.links.new(sep.outputs[1], ramp.inputs[0])
    col_out = ramp.outputs[0]
    if stars:
        vor = n.new("ShaderNodeTexVoronoi")
        vor.feature = "DISTANCE_TO_EDGE" if False else "F1"
        vor.inputs["Scale"].default_value = 260
        nt.links.new(tc.outputs["Window"], vor.inputs["Vector"])
        mr = n.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = 0.0
        mr.inputs["From Max"].default_value = 0.06
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        nt.links.new(vor.outputs["Distance"], mr.inputs["Value"])
        noise = n.new("ShaderNodeTexWhiteNoise")
        noise.noise_dimensions = "3D"
        nt.links.new(vor.outputs["Color"], noise.inputs["Vector"])
        gt = n.new("ShaderNodeMath")
        gt.operation = "GREATER_THAN"
        gt.inputs[1].default_value = 0.72
        nt.links.new(noise.outputs["Value"], gt.inputs[0])
        mul = n.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(mr.outputs[0], mul.inputs[0])
        nt.links.new(gt.outputs[0], mul.inputs[1])
        mul2 = n.new("ShaderNodeMath")
        mul2.operation = "MULTIPLY"
        mul2.inputs[1].default_value = 3.0
        nt.links.new(mul.outputs[0], mul2.inputs[0])
        add = n.new("ShaderNodeMix")
        add.data_type = "RGBA"
        add.blend_type = "ADD"
        nt.links.new(mul2.outputs[0], add.inputs[0])
        nt.links.new(col_out, add.inputs[6])
        add.inputs[7].default_value = (1, 1, 1, 1)
        col_out = add.outputs[2]
    nt.links.new(col_out, bg.inputs[0])
    bg.inputs[1].default_value = strength


def mat(name, col, rough=0.45, emit=0.0, spec=0.3, coat=0.0, sss=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*col, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Specular IOR Level"].default_value = spec
    if coat:
        p.inputs["Coat Weight"].default_value = coat
    if emit:
        p.inputs["Emission Color"].default_value = (*col, 1)
        p.inputs["Emission Strength"].default_value = emit
    if sss:
        p.inputs["Subsurface Weight"].default_value = sss
        p.inputs["Subsurface Radius"].default_value = (0.3, 0.15, 0.1)
    return m


def emit_mat(name, col, strength=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*col, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return m


OUTLINE = None


def outline_mat():
    global OUTLINE
    if OUTLINE is None:
        m = bpy.data.materials.new("Outline")
        m.use_nodes = True
        nt = m.node_tree
        nt.nodes.remove(nt.nodes["Principled BSDF"])
        e = nt.nodes.new("ShaderNodeEmission")
        e.inputs[0].default_value = (0.02, 0.01, 0.04, 1)
        e.inputs[1].default_value = 1.0
        nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
        m.use_backface_culling = True
        OUTLINE = m
    return OUTLINE


def outline(obj, thick=0.03):
    """Inverted-hull cartoon outline."""
    obj.data.materials.append(outline_mat())
    mod = obj.modifiers.new("ol", "SOLIDIFY")
    mod.thickness = thick
    mod.offset = 1
    mod.use_flip_normals = True
    mod.material_offset = len(obj.data.materials) - 1
    # backface culling only works in eevee; in cycles use a lightpath trick
    m = OUTLINE
    nt = m.node_tree
    if "lp" not in nt.nodes:
        lp = nt.nodes.new("ShaderNodeNewGeometry")
        lp.name = "lp"
        cam = nt.nodes.new("ShaderNodeLightPath")
        inv = nt.nodes.new("ShaderNodeMath")
        inv.operation = "SUBTRACT"
        inv.inputs[0].default_value = 1.0
        nt.links.new(lp.outputs["Backfacing"], inv.inputs[1])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(inv.outputs[0], mul.inputs[0])
        nt.links.new(cam.outputs["Is Camera Ray"], mul.inputs[1])
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        e = [x for x in nt.nodes if x.type == "EMISSION"][0]
        nt.links.new(mul.outputs[0], mix.inputs[0])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(e.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs[0])
    return obj


def smooth(obj, sub=2):
    for p in obj.data.polygons:
        p.use_smooth = True
    if sub:
        m = obj.modifiers.new("sub", "SUBSURF")
        m.levels = sub
        m.render_levels = sub
    return obj


def sphere(loc=(0, 0, 0), r=1.0, m=None, seg=48, name="S", ol=0.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=seg // 2, radius=r, location=loc)
    o = bpy.context.active_object
    o.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    if m:
        o.data.materials.append(m)
    if ol:
        outline(o, ol)
    return o


def cyl(loc, r, depth, m=None, rot=(0, 0, 0), name="C", ol=0.0, verts=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if m:
        o.data.materials.append(m)
    bev = o.modifiers.new("bev", "BEVEL")
    bev.width = min(r, depth) * 0.25
    bev.segments = 4
    for p in o.data.polygons:
        p.use_smooth = True
    if ol:
        outline(o, ol)
    return o


def box(loc, size, m=None, name="B", bevel=0.1, ol=0.0, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 5
    for p in o.data.polygons:
        p.use_smooth = True
    if m:
        o.data.materials.append(m)
    if ol:
        outline(o, ol)
    return o


def torus(loc, R, r, m=None, rot=(0, 0, 0), name="T", ol=0.0):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc, rotation=rot,
                                     major_segments=96, minor_segments=24)
    o = bpy.context.active_object
    o.name = name
    for p in o.data.polygons:
        p.use_smooth = True
    if m:
        o.data.materials.append(m)
    if ol:
        outline(o, ol)
    return o


def empty(loc=(0, 0, 0), name="E"):
    o = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    return o


def parent(child, par):
    child.parent = par
    child.matrix_parent_inverse = par.matrix_world.inverted()


def camera(loc, target, lens=35):
    cd = bpy.data.cameras.new("Cam")
    cd.lens = lens
    cam = bpy.data.objects.new("Cam", cd)
    bpy.context.scene.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = loc
    look(cam, target)
    return cam


def look(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def light(kind, loc, energy, col=(1, 1, 1), size=1.0, target=(0, 0, 0)):
    ld = bpy.data.lights.new(kind, kind)
    ld.energy = energy
    ld.color = col
    if kind == "AREA":
        ld.size = size
    elif kind in ("POINT", "SPOT"):
        ld.shadow_soft_size = size
    elif kind == "SUN":
        ld.angle = size
    o = bpy.data.objects.new(kind, ld)
    bpy.context.scene.collection.objects.link(o)
    o.location = loc
    look(o, target)
    return o


def three_point(key=600, fill=250, rim=500, warm=(1, .95, .85), cool=(.7, .8, 1), target=(0, 0, 1)):
    light("AREA", (4, -5, 6), key, warm, 4, target)
    light("AREA", (-5, -3, 3), fill, cool, 5, target)
    light("AREA", (0, 5, 5), rim, (1, 1, 1), 3, target)


# ---------------------------------------------------------------- mascot
def mascot(loc=(0, 0, 0), body_col=(0.25, 0.85, 0.35), scale=1.0):
    """Cute round alien 'Bipo'. Returns dict of parts for animation."""
    root = empty(loc, "Bipo")
    body = empty(loc, "BipoBody")
    parent(body, root)
    skin = mat("skin", body_col, rough=0.35, spec=0.4, coat=0.3, sss=0.05)
    belly = mat("belly", (0.75, 1.0, 0.6), rough=0.4)
    white = mat("eyew", (1, 1, 1), rough=0.15, spec=0.6)
    black = mat("pupil", (0.02, 0.02, 0.04), rough=0.1, spec=0.8)
    pink = mat("cheek", (1.0, 0.35, 0.55), rough=0.5)
    mouthm = mat("mouth", (0.35, 0.02, 0.08), rough=0.4)
    ant = mat("ant", (1.0, 0.78, 0.1), rough=0.3, emit=0.6)
    x, y, z = loc
    b = sphere((x, y, z + 1.0), 1.0, skin, name="torso", ol=0.035)
    b.scale = (1.0, 0.92, 1.05)
    parent(b, body)
    bl = sphere((x, y - 0.62, z + 0.78), 0.62, belly, name="belly")
    bl.scale = (1, 0.55, 1)
    parent(bl, body)
    eyes, pupils = [], []
    for s in (-1, 1):
        e = sphere((x + 0.36 * s, y - 0.72, z + 1.35), 0.33, white, name="eye", ol=0.02)
        e.scale = (1, 0.7, 1.15)
        parent(e, body)
        p = sphere((x + 0.36 * s, y - 0.97, z + 1.33), 0.17, black, name="pupil")
        p.scale = (1, 0.5, 1.2)
        parent(p, e)
        h = sphere((x + 0.36 * s + 0.06, y - 1.04, z + 1.43), 0.055, emit_mat("hl", (1, 1, 1), 4), name="hl")
        parent(h, p)
        eyes.append(e)
        pupils.append(p)
        c = sphere((x + 0.62 * s, y - 0.7, z + 1.0), 0.12, pink, name="cheek")
        c.scale = (1, 0.4, 0.7)
        parent(c, body)
    # smile: half torus (bottom half kept via bisect)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.2, minor_radius=0.045, location=(x, y - 0.93, z + 1.0),
                                     rotation=(math.radians(90), 0, 0), major_segments=48, minor_segments=12)
    m = bpy.context.active_object
    m.name = "mouth"
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.bisect(plane_co=(x, y, z + 1.0), plane_no=(0, 0, 1), clear_outer=True)
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in m.data.polygons:
        p.use_smooth = True
    m.data.materials.append(mouthm)
    parent(m, body)
    # antennas
    ants = []
    for s in (-1, 1):
        a = empty((x + 0.3 * s, y, z + 1.95), "antroot")
        parent(a, body)
        st = cyl((x + 0.3 * s, y, z + 2.25), 0.04, 0.6, skin, name="antstick")
        parent(st, a)
        tip = sphere((x + 0.3 * s, y, z + 2.6), 0.13, ant, name="anttip", ol=0.015)
        parent(tip, a)
        a.rotation_euler = (0, math.radians(18 * s), 0)
        ants.append(a)
    # arms
    arms = []
    for s in (-1, 1):
        sh = empty((x + 0.88 * s, y, z + 0.95), "shoulder")
        parent(sh, body)
        arm = sphere((x + 1.18 * s, y, z + 0.95), 0.36, skin, name="arm", ol=0.025)
        arm.scale = (1.0, 0.55, 0.5)
        parent(arm, sh)
        hand = sphere((x + 1.5 * s, y, z + 0.95), 0.2, skin, name="hand", ol=0.02)
        parent(hand, sh)
        arms.append(sh)
    legs = []
    for s in (-1, 1):
        lg = sphere((x + 0.42 * s, y - 0.1, z + 0.12), 0.3, skin, name="foot", ol=0.025)
        lg.scale = (1, 1.3, 0.55)
        parent(lg, root)
        legs.append(lg)
    root.scale = (scale,) * 3
    return {"root": root, "body": body, "eyes": eyes, "pupils": pupils, "arms": arms, "ants": ants,
            "legs": legs, "mouth": m, "base": Vector(loc)}


def animate_mascot(M, t, mood="talk", wave=0.0, hop=0.0, look_x=0.0):
    """Procedural idle/talk animation at time t (seconds)."""
    b = M["body"]
    # breathing squash/stretch
    s = 1 + 0.03 * math.sin(t * 5.0)
    b.scale = (1 / math.sqrt(s), 1 / math.sqrt(s), s)
    b.rotation_euler = (0, math.radians(4 * math.sin(t * 2.1)), math.radians(6 * math.sin(t * 1.3)) + look_x)
    if hop:
        h = abs(math.sin(t * hop * math.pi))
        M["root"].location = M["base"] + Vector((0, 0, 0.6 * h * M["root"].scale[2]))
    # blink every ~3s
    ph = (t % 3.1)
    bl = 0.12 if ph < 0.12 else 1.0
    for e in M["eyes"]:
        e.scale = (1, 0.7, 1.15 * bl)
    # mouth talk
    if mood == "talk":
        o = 1 + 0.6 * max(0, math.sin(t * 17) * math.sin(t * 5.3))
    elif mood == "wow":
        o = 2.2
    else:
        o = 1.0
    M["mouth"].scale = (1, 1, o)
    for i, a in enumerate(M["ants"]):
        sgn = -1 if i == 0 else 1
        a.rotation_euler = (math.radians(10 * math.sin(t * 6 + i)), math.radians(18 * sgn + 8 * math.sin(t * 4 + i)), 0)
    # arms: right arm waves
    for i, a in enumerate(M["arms"]):
        sgn = -1 if i == 0 else 1
        base = math.radians(28) * sgn
        sw = math.radians(10) * math.sin(t * 3 + i)
        if wave and i == 1:
            a.rotation_euler = (0, math.radians(-70) + math.radians(25) * math.sin(t * 12) * wave, 0)
        else:
            a.rotation_euler = (0, base + sw, 0)


def render_to(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
