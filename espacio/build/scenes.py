"""The nine 3D cartoon scenes. Each build_<id>() creates the scene and returns
(update(t), shots) where shots is a list of functions tt -> (cam_loc, target, lens)."""
import math
import random

import bpy
from mathutils import Vector

import toon as T

R = math.radians


def lerp(a, b, x):
    return a + (b - a) * x


def ease(x):
    x = min(max(x, 0), 1)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- shared props
def stars(n=260, radius=60, center=(0, 0, 0), seed=1, col=(1, 0.95, 0.85), size=(0.08, 0.22), upper=False):
    rnd = random.Random(seed)
    base = T.sphere((0, 0, -500), 1, T.emit_mat("star", col, 8), seg=8, name="star0")
    objs = []
    for i in range(n):
        while True:
            v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
            if 0.2 < v.length <= 1 and (not upper or v.z > 0.02):
                break
        v.normalize()
        o = base.copy()
        bpy.context.scene.collection.objects.link(o)
        o.location = Vector(center) + v * radius * rnd.uniform(0.85, 1.0)
        s = rnd.uniform(*size) * radius / 60
        o.scale = (s, s, s)
        objs.append((o, s, rnd.uniform(0, 6.28), rnd.uniform(2, 5)))
    return objs


def twinkle(objs, t):
    for o, s, ph, sp in objs:
        k = s * (0.75 + 0.35 * math.sin(t * sp + ph))
        o.scale = (k, k, k)


def planet_mat(name, cols, scale=3.0, bands=False, distort=4.0, emit=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = 0.55
    p.inputs["Specular IOR Level"].default_value = 0.25
    tc = nt.nodes.new("ShaderNodeTexCoord")
    if bands:
        tex = nt.nodes.new("ShaderNodeTexWave")
        tex.wave_type = "BANDS"
        tex.bands_direction = "Z"
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Distortion"].default_value = distort
        tex.inputs["Detail"].default_value = 2
        out = tex.outputs["Fac"]
    else:
        tex = nt.nodes.new("ShaderNodeTexNoise")
        tex.inputs["Scale"].default_value = scale
        tex.inputs["Detail"].default_value = 3
        out = tex.outputs["Fac"]
    nt.links.new(tc.outputs["Object"], tex.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = cols[0][0], (*cols[0][1], 1)
    el[1].position, el[1].color = cols[-1][0], (*cols[-1][1], 1)
    for pos, c in cols[1:-1]:
        e = el.new(pos)
        e.color = (*c, 1)
    if not bands:
        ramp.color_ramp.interpolation = "CONSTANT"
    nt.links.new(out, ramp.inputs[0])
    nt.links.new(ramp.outputs[0], p.inputs["Base Color"])
    if emit:
        nt.links.new(ramp.outputs[0], p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = emit
    return m


def sun_mat():
    m = planet_mat("sunm", [(0, (1, 0.35, 0.02)), (0.45, (1, 0.55, 0.05)), (0.6, (1, 0.75, 0.2)), (1, (1, 0.85, 0.35))],
                   5, emit=1.6)
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0, 0, 0, 1)
    return m


def earth(loc, r, ol=0.04):
    m = planet_mat("earth", [(0.0, (0.05, 0.3, 0.95)), (0.52, (0.05, 0.3, 0.95)), (0.53, (0.2, 0.75, 0.25)),
                             (0.68, (0.95, 0.95, 0.95))], scale=2.2)
    return T.sphere(loc, r, m, name="earth", ol=ol)


def glow(loc, size, col, strength=2.0, name="glow"):
    """Camera-facing soft radial glow billboard."""
    bpy.ops.mesh.primitive_plane_add(size=size, location=loc)
    o = bpy.context.active_object
    o.name = name
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.remove(nt.nodes["Principled BSDF"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = "SPHERICAL"
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Location"].default_value = (0, 0, 0)
    mp.inputs["Scale"].default_value = (2 / size, 2 / size, 2 / size)
    nt.links.new(tc.outputs["Object"], mp.inputs[0])
    nt.links.new(mp.outputs[0], grad.inputs[0])
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    pw.inputs[1].default_value = 2.2
    nt.links.new(grad.outputs["Fac"], pw.inputs[0])
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*col, 1)
    e.inputs[1].default_value = strength
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(pw.outputs[0], mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(e.outputs[0], add.inputs[0])
    nt.links.new(tr.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], nt.nodes["Material Output"].inputs[0])
    o.data.materials.append(m)
    o.visible_shadow = False
    o.visible_diffuse = False
    o.visible_glossy = False
    return o


def face_cam(o, cam):
    T.look(o, cam.location)
    o.rotation_euler.rotate_axis("X", R(180))


def ground(size, col, strength=0.35, scale=1.0, sub=6, name="ground", rough=0.9, loc=(0, 0, 0), seed=0):
    bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=120, size=size, location=loc)
    g = bpy.context.active_object
    g.name = name
    tex = bpy.data.textures.new(name + "tx", "CLOUDS")
    tex.noise_scale = scale
    tex.noise_basis = "BLENDER_ORIGINAL"
    d = g.modifiers.new("disp", "DISPLACE")
    d.texture = tex
    d.strength = strength
    d.mid_level = 0.5
    for p in g.data.polygons:
        p.use_smooth = True
    g.data.materials.append(T.mat(name + "m", col, rough=rough, spec=0.1))
    return g


def sunglasses(M):
    blk = T.mat("glass", (0.02, 0.02, 0.05), rough=0.05, spec=1.0, coat=1.0)
    b = M["body"]
    x, y, z = M["base"]
    sc0 = M["root"].scale.copy()
    M["root"].scale = (1, 1, 1)
    bpy.context.view_layer.update()
    parts = []
    for s in (-1, 1):
        g = T.cyl((x + 0.37 * s, y - 1.02, z + 1.36), 0.3, 0.06, blk, rot=(R(90), 0, 0), name="lens", ol=0.015)
        g.scale = (1, 0.85, 1)
        T.parent(g, b)
        parts.append(g)
    br = T.box((x, y - 1.05, z + 1.45), (0.2, 0.05, 0.05), blk, bevel=0.01)
    T.parent(br, b)
    M["root"].scale = sc0
    return parts


def shot(loc0, loc1, tgt0, tgt1, lens=35, dur=4.0):
    def f(tt):
        x = ease(tt / dur)
        return Vector(loc0).lerp(Vector(loc1), x), Vector(tgt0).lerp(Vector(tgt1), x), lens
    return f


def space_bg(top=(0.03, 0.01, 0.1), bottom=(0.12, 0.04, 0.28)):
    T.world_gradient(top, bottom, 1.0, stars=False)


# ---------------------------------------------------------------- scenes
def build_hook():
    space_bg()
    st = stars(300, 60, seed=3)
    e = earth((-3.2, 6, -1.5), 2.8)
    sat = T.sphere((4, 14, 6), 1.6, planet_mat("sat", [(0, (0.95, 0.8, 0.5)), (0.5, (0.85, 0.6, 0.35)),
                                                       (1, (1, 0.9, 0.65))], 6, bands=True), name="sat", ol=0.05)
    ring = T.torus((4, 14, 6), 2.6, 0.55, T.mat("ring", (0.95, 0.85, 0.6), rough=0.5), rot=(R(70), R(15), 0),
                   ol=0.04)
    ring.scale = (1, 1, 0.08)
    M = T.mascot((0, 0, 0))
    trail = []
    for i in range(14):
        trail.append(T.sphere((0, 0, -50), 0.09, T.emit_mat(f"tr{i}", (1, 0.85, 0.3), 6), seg=12))
    T.three_point(target=(0, 0, 1))
    T.light("POINT", (-3, -2, 1), 150, (0.4, 0.6, 1), 1)

    def upd(t, k, tt):
        twinkle(st, t)
        e.rotation_euler = (0, R(15), t * 0.4)
        sat.rotation_euler = (0, 0, t * 0.6)
        hop = 0
        T.animate_mascot(M, t, mood="talk" if k < 2 else "wow", wave=1.0 if k == 0 else 0.0)
        M["root"].location = M["base"] + Vector((0, 0, 0.25 * math.sin(t * 2.2)))
        if k == 2:  # take off!
            up = max(0, tt - 0.6) ** 2 * 3.5
            M["root"].location = M["base"] + Vector((0, 0, up))
            for i, s in enumerate(trail):
                d = i * 0.06
                s.location = M["root"].location + Vector((math.sin(t * 20 + i) * 0.15, 0, -0.1 - i * 0.35 - (up * 0.2)))
                s.scale = (max(0.05, 1 - i / 14) * (1 if up > 0.05 else 0.001),) * 3
        else:
            for s in trail:
                s.location = (0, 0, -50)
    shots = [shot((0, -9, 1.6), (0, -7.2, 1.8), (0, 0, 1.6), (0, 0, 1.4), 30, 8),
             shot((0.8, -3.6, 1.6), (0.5, -3.2, 1.5), (0, 0, 1.4), (0, 0, 1.4), 40, 4),
             shot((0, -8, 0.5), (0, -9, 1.5), (0, 0, 1.5), (0, 0, 4.0), 30, 3)]

    def track(k, tt, t):
        loc, tgt, lens = shots[k](tt)
        if k == 2:
            tgt = Vector(tgt)
            tgt.z = max(tgt.z, M["root"].location.z + 1.2)
            loc = Vector(loc)
            loc.z = max(loc.z, M["root"].location.z * 0.7)
        return loc, tgt, lens
    return upd, track, len(shots)


def build_s1():  # Venus: a day longer than a year
    space_bg((0.05, 0.01, 0.06), (0.25, 0.08, 0.15))
    st = stars(220, 60, seed=4)
    vm = planet_mat("venus", [(0, (1.0, 0.75, 0.3)), (0.45, (0.95, 0.55, 0.2)), (1, (1.0, 0.88, 0.55))], 3,
                    bands=True, distort=8)
    piv = T.empty((0, 0, 0), "orbit")
    venus = T.sphere((0, 0, 0), 2.0, vm, name="venus", ol=0.05)
    T.parent(venus, piv)
    sun = T.sphere((9, 22, 3), 4.0, sun_mat(), name="sun")
    g = glow((9, 21, 3), 26, (1, 0.5, 0.1), 2.5)
    M = T.mascot((0, 0, 1.92), scale=0.45)
    T.parent(M["root"], venus)
    pillow = T.sphere((0, 0, 1.95), 0.3, T.mat("pil", (0.95, 0.4, 0.6)), name="zz")
    pillow.location = (100, 0, 0)
    T.light("SUN", (5, 10, 5), 3.5, (1, 0.85, 0.65), 0.05, target=(0, 0, 0))
    T.light("AREA", (-4, -6, 4), 350, (0.7, 0.75, 1), 6, (0, 0, 0))
    zs = [T.sphere((0, 0, -60), 0.08, T.emit_mat("z", (1, 1, 1), 3), seg=10) for _ in range(3)]

    def upd(t, k, tt):
        twinkle(st, t)
        venus.rotation_euler = (R(-12), 0, t * 0.12)
        T.animate_mascot(M, t * 0.6, mood="talk" if k != 1 else "idle")
        M["body"].rotation_euler.y = R(10) * math.sin(t * 0.9)
        face_cam(g, bpy.context.scene.camera)
        # Zz bubbles from the bored mascot
        for i, z in enumerate(zs):
            ph = (t * 0.5 + i / 3) % 1.0
            head = M["root"].matrix_world @ Vector((0.4, 0, 2.6))
            z.location = head + Vector((0.6 * ph, 0, 1.2 * ph))
            s = 0.6 + 1.6 * ph
            z.scale = (s, s, s)
    shots = [shot((0, -9.5, 2.5), (1.2, -8.2, 2.2), (0.5, 0, 1.2), (0.3, 0, 1.0), 32, 6),
             shot((-1.5, -4.2, 3.2), (-1.0, -3.6, 3.0), (0, 0, 2.4), (0, 0, 2.4), 45, 5),
             shot((5, -12, 6), (3, -14, 4), (3, 6, 2), (2, 6, 2), 30, 5)]

    def track(k, tt, t):
        return shots[k % 3](tt)
    return upd, track, 3


def build_s2():  # Saturn floats in a bathtub
    space_bg((0.02, 0.05, 0.12), (0.2, 0.15, 0.4))
    st = stars(220, 60, seed=5)
    tubm = T.mat("tub", (0.97, 0.97, 1.0), rough=0.15, spec=0.6, coat=0.5)
    outer = T.box((0, 0, 0), (9, 5, 3.2), tubm, bevel=0.0, name="tub")
    inner = T.box((0, 0, 0.5), (8.3, 4.3, 3.2), None, bevel=0.0, name="inner")
    bo = outer.modifiers.new("bool", "BOOLEAN")
    bo.object = inner
    bo.operation = "DIFFERENCE"
    inner.hide_render = True
    inner.hide_viewport = True
    bev = outer.modifiers.new("bev", "BEVEL")
    bev.width = 0.35
    bev.segments = 6
    bev.limit_method = "ANGLE"
    T.outline(outer, 0.05)
    gold = T.mat("gold", (1, 0.75, 0.25), rough=0.25, spec=0.8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            T.sphere((3.9 * sx, 2.0 * sy, -1.75), 0.38, gold, ol=0.02)
    water = T.box((0, 0, 0.75), (8.3, 4.3, 0.05), T.mat("water", (0.25, 0.7, 1.0), rough=0.08, spec=0.8), bevel=0)
    smat = planet_mat("sat2", [(0, (0.98, 0.82, 0.5)), (0.5, (0.88, 0.6, 0.35)), (1, (1, 0.92, 0.7))], 6, bands=True)
    sat = T.sphere((0.3, 0, 1.2), 1.15, smat, name="sat", ol=0.04)
    ring = T.torus((0.3, 0, 1.2), 1.9, 0.38, T.mat("ring2", (0.95, 0.85, 0.65), rough=0.5), rot=(R(18), 0, 0),
                   ol=0.03)
    ring.scale = (1, 1, 0.09)
    ringp = T.empty((0.3, 0, 1.2), "ringp")
    T.parent(sat, ringp)
    T.parent(ring, ringp)
    # rubber duck
    duck = T.empty((-2.6, -0.4, 0.8), "duck")
    ym = T.mat("duck", (1, 0.85, 0.1), rough=0.3, coat=0.4)
    om = T.mat("beak", (1, 0.45, 0.05), rough=0.4)
    db = T.sphere((-2.6, -0.4, 1.05), 0.55, ym, ol=0.025)
    db.scale = (1.2, 0.9, 0.7)
    dh = T.sphere((-2.9, -0.55, 1.65), 0.36, ym, ol=0.02)
    bk = T.sphere((-3.25, -0.72, 1.6), 0.16, om, ol=0.012)
    bk.scale = (1.4, 1, 0.5)
    for s in (-1, 1):
        T.sphere((-3.0 + 0.12 * s, -0.86, 1.75), 0.06, T.mat("de", (0, 0, 0), rough=0.1))
    for o in (db, dh, bk):
        T.parent(o, duck)
    # bubbles
    bub = []
    bm = T.mat("bub", (0.9, 0.95, 1.0), rough=0.05, spec=1.0, coat=1.0)
    rnd = random.Random(2)
    for i in range(18):
        b = T.sphere((rnd.uniform(-3.8, 3.8), rnd.uniform(-1.9, 1.9), 0.8), rnd.uniform(0.12, 0.35), bm, seg=16)
        bub.append((b, b.location.copy(), rnd.uniform(0, 6)))
    M = T.mascot((2.6, -2.3, 1.62), scale=0.55)
    T.three_point(key=900, target=(0, 0, 0.5))

    def upd(t, k, tt):
        twinkle(st, t)
        ringp.location = Vector((0.3, 0, 1.2 + 0.15 * math.sin(t * 2.0)))
        ringp.rotation_euler = (R(6) * math.sin(t * 1.5), R(8) * math.sin(t * 1.1), t * 0.3)
        duck.location = Vector((-2.6 + 0.3 * math.sin(t * 0.7), -0.4, 0.8 + 0.08 * math.sin(t * 2.6)))
        duck.rotation_euler = (R(5) * math.sin(t * 2.6), R(6) * math.sin(t * 1.9), R(15) * math.sin(t * 0.5))
        for b, p0, ph in bub:
            b.location = p0 + Vector((0, 0, 0.05 * math.sin(t * 3 + ph)))
        T.animate_mascot(M, t, mood="talk" if k == 0 else "wow", wave=0)
        M["root"].rotation_euler = (0, 0, R(15))
    shots = [shot((0, -13, 6), (0, -11.5, 5), (0, 0, 0.8), (0, 0, 0.9), 32, 5),
             shot((4.2, -8.5, 3.6), (3.6, -7.6, 3.3), (1.6, -1.2, 1.9), (1.4, -1.0, 1.9), 34, 5)]

    def track(k, tt, t):
        return shots[k % 2](tt)
    return upd, track, 2


def build_s3():  # The Sun: a million Earths
    space_bg((0.06, 0.01, 0.02), (0.25, 0.05, 0.08))
    st = stars(200, 70, seed=6)
    sun = T.sphere((0, 14, 2), 8.0, sun_mat(), name="sun")
    g = glow((0, 13, 2), 40, (1, 0.45, 0.05), 2.5)
    n = 40
    em = planet_mat("earthm", [(0.0, (0.05, 0.3, 0.95)), (0.5, (0.05, 0.3, 0.95)), (0.51, (0.2, 0.75, 0.25)),
                               (1, (0.2, 0.75, 0.25))], scale=2.5)
    earths = []
    rnd = random.Random(7)
    for i in range(n):
        e = T.sphere((0, 0, -80), 0.25, em, seg=20)
        earths.append((e, rnd.uniform(-1, 1), rnd.uniform(-1, 1), i / n))
    M = T.mascot((2.6, -3.5, -1.6), scale=0.75)
    sunglasses(M)
    beam = T.sphere((0, 0, -80), 0.25, T.emit_mat("beam", (1, 0.95, 0.6), 12), seg=16)
    beam.scale = (1, 1, 1)
    target_earth = earth((-6, -16, -2), 1.0)
    T.light("POINT", (0, 5, 2), 4000, (1, 0.7, 0.3), 3)
    T.light("AREA", (4, -9, 3), 300, (0.8, 0.85, 1), 5, (2, -3, 0))
    T.light("POINT", (-3, -13, 0), 400, (1, 0.85, 0.6), 1)

    def upd(t, k, tt):
        twinkle(st, t)
        sun.rotation_euler = (0, 0, t * 0.15)
        face_cam(g, bpy.context.scene.camera)
        for e, ox, oz, ph in earths:
            f = (t * 0.22 + ph) % 1.0
            p0 = Vector((ox * 7, -6, oz * 4 - 1))
            p1 = Vector((ox * 2, 9, 2 + oz * 2))
            e.location = p0.lerp(p1, f)
            s = 1.0 - 0.7 * f
            e.scale = (s, s, s)
            e.rotation_euler = (0, 0, t * 2 + ph * 10)
        T.animate_mascot(M, t, mood="talk" if k != 1 else "wow")
        M["root"].rotation_euler = (0, 0, R(25))
        if k == 2:
            f = min(1, tt / 2.8)
            beam.location = Vector((0, 6, 2)).lerp(Vector((-6, -15, -1.7)), ease(f))
            beam.scale = (1, 1, 1)
            T.look(beam, (-6, -16, -2))
            beam.scale = (0.6, 0.6, 4.0)
        else:
            beam.location = (0, 0, -80)
    shots = [shot((0, -16, 1), (0, -13, 1.5), (0, 6, 2), (0, 6, 2.5), 28, 6),
             shot((5.5, -9.5, 0.4), (4.8, -8.8, 0.3), (2.4, -3.5, -0.3), (2.6, -3.5, -0.3), 42, 4),
             shot((-9, -22, 1), (-8.5, -21, 0.6), (-4, -6, 0), (-5, -12, -1), 28, 4)]

    def track(k, tt, t):
        return shots[min(k, 2)](tt)
    return upd, track, 3


def build_s4():  # Moon footprints
    T.world_color((0.005, 0.005, 0.02), 1.0)
    st = stars(320, 70, seed=8, upper=True)
    gr = ground(60, (0.55, 0.55, 0.58), 0.6, 1.4, name="moon")
    # craters: dark rings
    cm = T.mat("crater", (0.38, 0.38, 0.42), rough=0.95)
    rnd = random.Random(3)
    for i in range(10):
        x, y = rnd.uniform(-14, 14), rnd.uniform(2, 22)
        r = rnd.uniform(0.8, 2.2)
        c = T.torus((x, y, 0.15), r, r * 0.22, cm)
        c.scale = (1, 1, 0.35)
    # footprints trail
    fm = T.mat("print", (0.25, 0.25, 0.28), rough=1)
    prints = []
    for i in range(12):
        s = 1 if i % 2 else -1
        p = T.sphere((s * 0.35 + math.sin(i * 0.4) * 0.6, 7 - i * 1.0, 0.32), 0.3, fm, seg=16)
        p.scale = (0.7, 1.2, 0.08)
        prints.append(p)
    flag_m = T.mat("flagm", (0.95, 0.2, 0.3), rough=0.6)
    pole = T.cyl((-2.2, 9, 1.8), 0.05, 3.6, T.mat("pole", (0.85, 0.85, 0.9), 0.3, spec=0.8))
    flag = T.box((-1.45, 9, 3.15), (1.4, 0.04, 0.9), flag_m, bevel=0.02, ol=0.02)
    e = earth((8, 40, 14), 4.5, ol=0.06)
    M = T.mascot((0.4, -6.2, 0.25), scale=0.8)
    T.light("SUN", (-6, -4, 6), 4.5, (1, 0.97, 0.92), 0.02, (0, 0, 0))
    T.light("AREA", (5, -8, 4), 200, (0.6, 0.7, 1), 8, (0, 0, 0))

    def upd(t, k, tt):
        twinkle(st, t)
        e.rotation_euler = (0, R(20), t * 0.3)
        T.animate_mascot(M, t, mood="talk", hop=0.45)
        M["root"].location.y = -6.2 + 0.35 * t
        flag.rotation_euler = (0, 0, R(3) * math.sin(t * 2))
    shots = [shot((-4, -14, 5), (-3, -12, 4), (0, 2, 0.5), (0, 3, 0.5), 30, 5),
             shot((0.5, -3.5, 0.9), (0.4, -2.8, 0.6), (0.2, 3, 0.2), (0.2, 4, 0.2), 30, 4),
             shot((4, -12, 2), (3, -10, 2.2), (0, -3, 1.5), (0, -2, 2.0), 35, 4)]

    def track(k, tt, t):
        loc, tgt, lens = shots[k % 3](tt)
        if k % 3 == 2:
            tgt = M["root"].location + Vector((0, 0, 1.0))
        return loc, tgt, lens
    return upd, track, 3


def build_s5():  # Blue sunsets on Mars
    T.world_gradient((0.1, 0.05, 0.06), (0.35, 0.6, 0.95), 1.0)
    gr = ground(80, (0.75, 0.3, 0.12), 0.9, 2.5, name="mars")
    rnd = random.Random(9)
    rm = T.mat("rock", (0.55, 0.22, 0.1), rough=0.9)
    for i in range(18):
        r = T.sphere((rnd.uniform(-10, 10), rnd.uniform(-2, 25), 0.1), rnd.uniform(0.2, 0.8), rm, seg=10, ol=0.02)
        r.scale = (1, rnd.uniform(0.7, 1.3), rnd.uniform(0.5, 0.8))
        r.rotation_euler = (rnd.random(), rnd.random(), rnd.random())
    # distant hills
    hm = T.mat("hill", (0.55, 0.25, 0.15), rough=1)
    for i in range(6):
        h = T.sphere((-30 + i * 12, 55, -6), rnd.uniform(9, 14), hm, seg=24)
        h.scale = (1.5, 0.6, 0.7)
    sun = T.sphere((4, 70, 6), 2.4, T.emit_mat("bsun", (0.85, 0.95, 1.0), 6), name="sun")
    g = glow((4, 69, 6), 60, (0.3, 0.6, 1.0), 2.5)
    M = T.mascot((0, 0, 0.45), scale=0.8)
    T.light("SUN", (2, 30, 3), 2.5, (0.6, 0.75, 1), 0.05, (0, 0, 0))
    T.light("AREA", (-3, -7, 4), 350, (1, 0.7, 0.55), 6, (0, 0, 1))

    def upd(t, k, tt):
        sun.location.z = 6 - 0.15 * t
        g.location = Vector((4, 69, sun.location.z))
        face_cam(g, bpy.context.scene.camera)
        T.animate_mascot(M, t, mood="talk" if k < 2 else "wow", wave=1.0 if k == 3 else 0.0)
        turn = ease((tt - 0.2) / 0.5) if k in (1, 3) else 0
        M["root"].rotation_euler = (0, 0, R(180) * (1 - turn))
    shots = [shot((-1.5, -5, 1.5), (-1.0, -4.0, 1.3), (1, 30, 3), (2, 40, 3), 30, 4),
             shot((2.5, -6, 1.6), (2.0, -5.4, 1.5), (0, 0, 1.2), (0, 0, 1.2), 38, 5),
             shot((0, 20, 2.5), (0, 18, 2.0), (0, 0, 1.0), (0, 0, 0.8), 28, 4),
             shot((0.5, -4.2, 1.6), (0.3, -3.6, 1.5), (0, 0, 1.3), (0, 0, 1.3), 40, 3)]

    def track(k, tt, t):
        return shots[k % 4](tt)
    return upd, track, 4


def build_s6():  # Neutron star teaspoon
    space_bg((0.01, 0.02, 0.08), (0.08, 0.1, 0.3))
    st = stars(260, 60, seed=10)
    ns = T.sphere((3, 18, 8), 0.8, T.emit_mat("ns", (0.6, 0.9, 1.0), 6), name="ns")
    g = glow((3, 17.9, 8), 9, (0.3, 0.6, 1.0), 2.5)
    beams = T.empty((3, 18, 8), "beams")
    bm = T.emit_mat("beamm", (0.4, 0.75, 1.0), 2.5)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.9, radius2=0.03, depth=5,
                                        location=(3, 18, 8 + 2.5 * s), rotation=(0 if s < 0 else R(180), 0, 0))
        c = bpy.context.active_object
        c.data.materials.append(bm)
        T.parent(c, beams)
    # seesaw: spoon vs mountain
    plank_m = T.mat("plank", (0.85, 0.55, 0.3), rough=0.6)
    piv = T.empty((0, -2, 0.9), "seesaw")
    plank = T.box((0, -2, 1.0), (7.5, 1.0, 0.18), plank_m, bevel=0.05, ol=0.03)
    T.parent(plank, piv)
    bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=0.8, depth=1.0, location=(0, -2, 0.4))
    tri = bpy.context.active_object
    tri.data.materials.append(T.mat("tri", (0.4, 0.3, 0.8)))
    T.outline(tri, 0.03)
    # spoon
    steel = T.mat("steel", (0.85, 0.87, 0.9), rough=0.15, spec=1.0)
    bowl = T.sphere((-2.6, -2, 1.35), 0.6, steel, ol=0.02)
    bowl.scale = (1, 0.75, 0.3)
    handle = T.cyl((-1.3, -2, 1.3), 0.08, 2.2, steel, rot=(0, R(84), 0), ol=0.015)
    tiny = T.sphere((-2.6, -2, 1.55), 0.22, T.emit_mat("tiny", (0.6, 0.9, 1.0), 10))
    for o in (bowl, handle, tiny):
        T.parent(o, piv)
    # mountain
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=1.6, depth=2.6, location=(2.6, -2, 2.4))
    mt = bpy.context.active_object
    mt.data.materials.append(T.mat("mtn", (0.45, 0.45, 0.55), rough=0.9))
    T.outline(mt, 0.03)
    bpy.ops.mesh.primitive_cone_add(vertices=7, radius1=0.62, depth=1.0, location=(2.6, -2, 3.2))
    snow = bpy.context.active_object
    snow.data.materials.append(T.mat("snow", (1, 1, 1), rough=0.5))
    for o in (mt, snow):
        T.parent(o, piv)
    M = T.mascot((-4.6, -3.2, -0.4), scale=0.55)
    floor = T.cyl((0, -2, -0.25), 6.5, 0.3, T.mat("plat", (0.3, 0.25, 0.6), rough=0.6), ol=0.04)
    T.three_point(target=(0, -2, 1))
    T.light("POINT", (2, 12, 6), 500, (0.5, 0.8, 1), 1)

    def upd(t, k, tt):
        twinkle(st, t)
        beams.rotation_euler = (R(25), 0, t * 2.5)
        ns.scale = (1 + 0.05 * math.sin(t * 20),) * 3
        face_cam(g, bpy.context.scene.camera)
        tilt = R(-14) * ease(t / 1.2) if k == 0 else R(-14) + R(14) * ease(tt / 0.9) if k == 1 else R(-1.5) * math.sin(t * 3)
        piv.rotation_euler = (0, tilt, 0)
        T.animate_mascot(M, t, mood="wow" if k == 2 else "talk")
        M["root"].rotation_euler = (0, 0, R(-30))
    shots = [shot((0, -16, 4.5), (0, -14, 4.0), (0.5, 0, 3.2), (0.5, 0, 3.0), 22, 6),
             shot((-1, -13, 2.6), (-0.5, -12, 2.4), (0, -2, 1.6), (0, -2, 1.6), 24, 4),
             shot((-4.6, -6.0, 0.9), (-4.4, -5.3, 0.9), (-4.6, -3.2, 0.5), (-4.6, -3.2, 0.5), 42, 4)]

    def track(k, tt, t):
        return shots[k % 3](tt)
    return upd, track, 3


def build_s7():  # More stars than sand grains
    T.world_gradient((0.01, 0.01, 0.06), (0.1, 0.12, 0.35), 1.0)
    st = stars(700, 80, seed=11, size=(0.05, 0.2), upper=True)
    sea = T.box((0, 40, -0.6), (200, 60, 0.1), T.mat("sea", (0.03, 0.08, 0.25), rough=0.12, spec=0.9), bevel=0)
    sand = ground(40, (0.95, 0.8, 0.55), 0.35, 2.0, name="sand", loc=(0, -6, 0))
    rnd = random.Random(12)
    gm = [T.mat(f"g{i}", c, rough=0.8) for i, c in enumerate([(0.95, 0.8, 0.5), (0.9, 0.7, 0.45), (1, 0.9, 0.7)])]
    grains = []
    for i in range(160):
        a = rnd.uniform(0, 6.28)
        r = rnd.uniform(0, 0.9) ** 0.7
        gx, gy = 1.6 + math.cos(a) * r, -5.2 + math.sin(a) * r
        gz = 0.2 + (1 - r) * 0.5 + rnd.uniform(0, 0.08)
        o = T.sphere((gx, gy, gz), rnd.uniform(0.04, 0.08), gm[i % 3], seg=8)
        grains.append(o)
    M = T.mascot((-0.6, -4.8, 0.2), scale=0.8)
    shell = T.sphere((2.6, -6.2, 0.2), 0.25, T.mat("shell", (1, 0.6, 0.7), 0.4), ol=0.015)
    shell.scale = (1, 0.8, 0.5)
    T.light("AREA", (-3, -9, 5), 380, (0.65, 0.75, 1.0), 8, (0, -5, 0))
    T.light("AREA", (3, -2, 3), 150, (1, 0.8, 0.6), 3, (0, -5, 0.5))

    def upd(t, k, tt):
        twinkle(st, t)
        T.animate_mascot(M, t, mood="wow" if k == 3 else "talk", wave=0)
        look_up = ease((tt - 0.1) / 0.6) if k == 2 else 0
        M["body"].rotation_euler.x = R(-20) * look_up
    shots = [shot((0, -14, 2.2), (0, -12, 2.6), (0, 10, 3), (0, 10, 5), 26, 5),
             shot((2.4, -7.6, 1.3), (2.2, -7.0, 1.1), (1.6, -5.2, 0.4), (1.6, -5.2, 0.4), 40, 4),
             shot((-0.6, -8.5, 0.4), (-0.6, -8.8, 0.6), (-0.6, 0, 6), (-0.6, 0, 9), 24, 4),
             shot((-1.2, -8.2, 1.6), (-0.9, -7.6, 1.5), (-0.6, -4.8, 1.3), (-0.6, -4.8, 1.3), 40, 3)]

    def track(k, tt, t):
        return shots[k % 4](tt)
    return upd, track, 4


def build_cta():
    space_bg((0.05, 0.01, 0.12), (0.3, 0.08, 0.35))
    st = stars(260, 60, seed=13)
    e = earth((-3.5, 7, 4.5), 1.8)
    sat = T.sphere((3.8, 8, -0.5), 1.2, planet_mat("satc", [(0, (0.98, 0.82, 0.5)), (1, (0.85, 0.6, 0.35))], 6,
                                                   bands=True), ol=0.04)
    ring = T.torus((3.8, 8, -0.5), 2.0, 0.4, T.mat("ringc", (0.95, 0.85, 0.65)), rot=(R(70), R(-20), 0), ol=0.03)
    ring.scale = (1, 1, 0.09)
    M = T.mascot((0, 0, 0))
    rnd = random.Random(14)
    cols = [(1, 0.3, 0.5), (0.3, 0.8, 1), (1, 0.85, 0.2), (0.5, 1, 0.4), (0.8, 0.4, 1)]
    cms = [T.mat(f"cf{i}", c, rough=0.4, emit=0.4) for i, c in enumerate(cols)]
    conf = []
    for i in range(70):
        c = T.box((0, 0, -80), (0.18, 0.1, 0.02), cms[i % 5], bevel=0)
        conf.append((c, rnd.uniform(-3.5, 3.5), rnd.uniform(-2, 2), rnd.uniform(0, 1), rnd.uniform(2, 6)))
    T.three_point(target=(0, 0, 1))

    def upd(t, k, tt):
        twinkle(st, t)
        e.rotation_euler = (0, R(15), t * 0.5)
        T.animate_mascot(M, t, mood="talk", wave=1.0, hop=1.2)
        for c, x, y, ph, sp in conf:
            f = (t * 0.25 + ph) % 1.0
            c.location = (x + 0.3 * math.sin(t * sp), y, 5 - 7 * f)
            c.rotation_euler = (t * sp, t * sp * 0.7, ph * 6)
    shots = [shot((0, -8.5, 1.8), (0, -7.0, 1.6), (0, 0, 1.6), (0, 0, 1.5), 30, 7)]

    def track(k, tt, t):
        return shots[0](tt)
    return upd, track, 1


BUILD = {"hook": build_hook, "s1": build_s1, "s2": build_s2, "s3": build_s3, "s4": build_s4, "s5": build_s5,
         "s6": build_s6, "s7": build_s7, "cta": build_cta}
