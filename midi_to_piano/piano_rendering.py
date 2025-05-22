import bpy  # type: ignore
import bmesh # type: ignore


# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

SCALE_FACTOR = 100
WHITE_KEY_W = 0.030 * SCALE_FACTOR
WHITE_KEY_H = 0.030 * SCALE_FACTOR
WHITE_KEY_L = 0.230 * SCALE_FACTOR  # Tiefe

BLACK_KEY_W = 0.016 * SCALE_FACTOR
BLACK_KEY_H = 0.038 * SCALE_FACTOR
BLACK_KEY_L = 0.120 * SCALE_FACTOR
KEY_GAP = 0.3

def set_origin_at_back(obj, length):
    """Move cursor to the rear edge of *obj* and set that as the origin."""
    x, y, _ = obj.location
    bpy.context.scene.cursor.location = (x, y + length / 2, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")


def slope_top_front(obj,
                    depth_ratio=0.1,   # front 10 %
                    drop_ratio =0.30,   # 30 % of key height
                    front_axis ="Y"):   # pianist faces +Y  (positive world-Y)
    """
    Add a bevel to the *front* strip of the key – only in the Y direction.
    Works even when the mesh is the original 8-vertex cube.
    """
    ax = 0 if front_axis.upper()=="X" else 1          # axis index: 0→X, 1→Y

    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    # ----- basic measurements in the object’s LOCAL space -----
    z_top      = max(v.co.z for v in bm.verts)
    front      = min(v.co[ax] for v in bm.verts)
    back       = max(v.co[ax] for v in bm.verts)
    full_len   = back - front
    ramp_len   = full_len * depth_ratio
    ramp_limit = front + ramp_len
    z_target   = z_top * (1 - drop_ratio)

    # ----- 1. ONE loop-cut exactly at ramp_limit, on the TOP surface only -----
    # pick only top-surface edges whose endpoints straddle the limit *along Y*
    to_cut = [
        e for e in bm.edges
        if abs(e.verts[0].co.z - z_top) < 1e-6        # both verts on the top
        and abs(e.verts[1].co.z - z_top) < 1e-6
        and (e.verts[0].co[ax] - ramp_limit) *
            (e.verts[1].co[ax] - ramp_limit) < 0      # endpoints on opposite sides
    ]

    if to_cut:
        # ---------- NEW: tell Blender exactly where on each edge to cut ----------
        edge_perc = {}
        for e in to_cut:
            v1, v2 = e.verts
            p = (ramp_limit - v1.co[ax]) / (v2.co[ax] - v1.co[ax])   # 0–1 along that edge
            edge_perc[e] = p

        bmesh.ops.subdivide_edges(
            bm,
            edges         = to_cut,
            cuts          = 1,
            edge_percents = edge_perc,      # ← precise cut location
            use_grid_fill = False
        )

    # ----- 2. lower only the vertices in the front strip -----
    for v in bm.verts:
        if abs(v.co.z - z_top) < 1e-6 and v.co[ax] <= ramp_limit + 1e-6:
            t = (ramp_limit - v.co[ax]) / ramp_len     # 0 at ramp_limit → 1 at very front
            v.co.z = z_top - t * (z_top - z_target)

    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    
  
def build_key(
    name: str,
    width: float,
    height: float,
    length: float,
    left: float,
    top: float,
    is_black: bool,
):
    """Create a key whose **left edge** sits at *left* and **top edge** sits at *top* and return the object.
    note: length = "tiefe"
    """
    cube_x = left + width / 2
    cube_y = top - length / 2
    bpy.ops.mesh.primitive_cube_add(size=1, location=(cube_x, cube_y, height))

    key = bpy.context.object
    key.name = name
    key.scale = (width, length, height)
    key.rotation_mode = "XYZ"

    # UNIQUE material per key -------------------------------------
    mat = bpy.data.materials.new(f"{name}_Mat")
    base_colour       = (0.01, 0.01, 0.01, 1) if is_black else (0.9, 0.9, 0.9, 1)
    mat.diffuse_color = base_colour
    key.data.materials.append(mat)

    set_origin_at_back(key, length)
    return key


def create_piano():
    """Build an 88-key keyboard in a collection named 'Piano'."""

    # If the collection already exists, reuse it
    piano_col = bpy.data.collections.get("Piano")
    if piano_col is None:
        piano_col = bpy.data.collections.new("Piano")
        bpy.context.scene.collection.children.link(piano_col)

    # White note names A0–C8 (52 keys)
    white_notes = [
        "A0",
        "B0",
        *[f"{n}{o}" for o in range(1, 8) for n in ("C", "D", "E", "F", "G", "A", "B")],
        "C8",
    ]

    left = 10.0  # current left edge position along X
    pending_black = []  # tuples (center_x, note_name)

    for idx, note in enumerate(white_notes):
        build_key(
            name=f"White_{note}",
            width=WHITE_KEY_W,
            height=WHITE_KEY_H,
            length=WHITE_KEY_L,
            left=left,
            top=WHITE_KEY_L,
            is_black=False,
        )

        # No black keys after last white key
        if idx == len(white_notes) - 1:
            break

        # Decide if a black key follows this white key (no sharps after E or B)
        if note[0] not in {"E", "B"}:
            black_center = left + WHITE_KEY_W  # halfway between this and next white
            pending_black.append((black_center, note))

        left += WHITE_KEY_W + KEY_GAP  # advance left edge for next white

    # Build black keys after all whites for clarity
    for center_x, base_note in pending_black:
        bkey = build_key(
            name=f"Black_{base_note}#",
            width=BLACK_KEY_W,
            height=BLACK_KEY_H,
            length=BLACK_KEY_L,
            left=center_x - BLACK_KEY_W / 2,
            top=WHITE_KEY_L,
            is_black=True,
        )
        # Lift black keys higher than whites
        bkey.location.z += (WHITE_KEY_H - BLACK_KEY_H) / 2
         # ---------------- add the front slope here ----------------
        slope_top_front(bkey, depth_ratio=0.16, drop_ratio=0.35, front_axis="Y")

    print(
        f"Piano generated with {len(white_notes)} white and {len(pending_black)} black keys"
    )