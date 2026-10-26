
/* ---- Head-locked quads (Halo MCC VR) -----------------------------------------------------------------------------
 * SteamVR on the Frame rejects a frame (XR_ERROR_POSE_INVALID) when a quad layer is placed in a VIEW reference space:
 * Halo's F1 panel during stereo gameplay is a head-locked quad 1.2 m ahead, and every such frame was dropped, so the
 * menu never appeared. Quads in a VIEW space are re-expressed in the projection layer's space at the frame's display
 * time (same apparent placement). Reference spaces are recorded as the app creates them. */
static PFN_xrCreateReferenceSpace next_create_ref_space;
static PFN_xrLocateSpace next_locate_space;
static XrSpace view_spaces[8];
static unsigned view_space_count;
static unsigned long long view_quads_moved, view_quads_failed;

static XrResult XRAPI_CALL frame_create_ref_space(XrSession session, const XrReferenceSpaceCreateInfo *info, XrSpace *space)
{
    XrResult r = next_create_ref_space(session, info, space);
    if (XR_SUCCEEDED(r) && info->referenceSpaceType == XR_REFERENCE_SPACE_TYPE_VIEW && view_space_count < 8) {
        view_spaces[view_space_count++] = *space;
        if (logf) { fprintf(logf, "view reference space %p recorded\n", (void *)*space); fflush(logf); }
    }
    return r;
}

static int is_view_space(XrSpace s)
{
    for (unsigned i = 0; i < view_space_count; i++) if (view_spaces[i] == s) return 1;
    return 0;
}

static void quat_mul(const XrQuaternionf *a, const XrQuaternionf *b, XrQuaternionf *o)
{
    XrQuaternionf r;
    r.w = a->w * b->w - a->x * b->x - a->y * b->y - a->z * b->z;
    r.x = a->w * b->x + a->x * b->w + a->y * b->z - a->z * b->y;
    r.y = a->w * b->y - a->x * b->z + a->y * b->w + a->z * b->x;
    r.z = a->w * b->z + a->x * b->y - a->y * b->x + a->z * b->w;
    *o = r;
}

static void quat_rotate(const XrQuaternionf *q, const XrVector3f *v, XrVector3f *o)
{
    XrQuaternionf p = {v->x, v->y, v->z, 0}, c = {-q->x, -q->y, -q->z, q->w}, t, r;
    quat_mul(q, &p, &t); quat_mul(&t, &c, &r);
    o->x = r.x; o->y = r.y; o->z = r.z;
}

/* Re-express a VIEW-space quad in base_space at time t; returns 1 when moved. */
static int move_view_quad(XrCompositionLayerQuad *q, XrSpace base_space, XrTime t)
{
    if (!next_locate_space || !base_space || !is_view_space(q->space)) return 0;
    XrSpaceLocation loc; memset(&loc, 0, sizeof loc); loc.type = XR_TYPE_SPACE_LOCATION;
    if (XR_FAILED(next_locate_space(q->space, base_space, t, &loc)) ||
        !(loc.locationFlags & XR_SPACE_LOCATION_POSITION_VALID_BIT) ||
        !(loc.locationFlags & XR_SPACE_LOCATION_ORIENTATION_VALID_BIT)) { view_quads_failed++; return 0; }
    XrVector3f rotated; quat_rotate(&loc.pose.orientation, &q->pose.position, &rotated);
    q->pose.position.x = loc.pose.position.x + rotated.x;
    q->pose.position.y = loc.pose.position.y + rotated.y;
    q->pose.position.z = loc.pose.position.z + rotated.z;
    quat_mul(&loc.pose.orientation, &q->pose.orientation, &q->pose.orientation);
    q->space = base_space;
    view_quads_moved++;
    return 1;
}
