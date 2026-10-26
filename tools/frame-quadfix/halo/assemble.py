"""Builds framexr.c for Halo MCC VR: tools/frame-quadfix/quadfix.c plus the Frame pad bridge (pad_part.c) and the
head-locked quad handling (space_part.c). Usage: python3 assemble.py <this folder>"""
import pathlib, sys

here = pathlib.Path(sys.argv[1])
src = (here.resolve().parent / "quadfix.c").read_text()   # the base layer in tools/frame-quadfix
pad = (here / "pad_part.c").read_text()

def sub(old, new):
    global src
    if old not in src:
        sys.exit("anchor not found: " + old[:60])
    src = src.replace(old, new, 1)

sub("static PFN_xrPathToString next_path_to_string;\n",
    "static PFN_xrPathToString next_path_to_string;\n" + pad + "\n")
sub("XrResult r = keep ? next_suggest(instance, s) : XR_SUCCESS;",
    "XrResult r = keep ? (pad_enabled ? pad_suggest_touch(instance, s) : next_suggest(instance, s)) : XR_SUCCESS;")
sub('    if (!next_gipa) return XR_ERROR_HANDLE_INVALID;\n',
    '    if (streq(name, "xrAttachSessionActionSets") && next_attach && pad_enabled) { *function = (PFN_xrVoidFunction)pad_attach; return XR_SUCCESS; }\n'
    '    if (streq(name, "xrSyncActions") && next_sync && pad_enabled) { *function = (PFN_xrVoidFunction)pad_sync; return XR_SUCCESS; }\n'
    '    if (!next_gipa) return XR_ERROR_HANDLE_INVALID;\n')
sub('        next_gipa(*instance, "xrPathToString", (PFN_xrVoidFunction *)&next_path_to_string);\n',
    '        next_gipa(*instance, "xrPathToString", (PFN_xrVoidFunction *)&next_path_to_string);\n'
    '        next_gipa(*instance, "xrCreateActionSet", (PFN_xrVoidFunction *)&next_create_set);\n'
    '        next_gipa(*instance, "xrCreateAction", (PFN_xrVoidFunction *)&next_create_action);\n'
    '        next_gipa(*instance, "xrStringToPath", (PFN_xrVoidFunction *)&next_string_to_path);\n'
    '        next_gipa(*instance, "xrAttachSessionActionSets", (PFN_xrVoidFunction *)&next_attach);\n'
    '        next_gipa(*instance, "xrSyncActions", (PFN_xrVoidFunction *)&next_sync);\n'
    '        next_gipa(*instance, "xrGetActionStateBoolean", (PFN_xrVoidFunction *)&next_get_bool);\n'
    '        const char *pe = getenv("FRAMEXR_PAD");\n'
    '        pad_enabled = !(pe && streq(pe, "0"));\n'
    '        if (logf) { fprintf(logf, "pad bridge %s\\n", pad_enabled ? "enabled" : "disabled (FRAMEXR_PAD=0)"); fflush(logf); }\n')
sub("/* frame_quadfix: an OpenXR API layer", "/* frame_quadfix (+ Frame pad bridge for Halo MCC VR, see below): an OpenXR API layer")
# FRAMEXR_QUAD=norm: keep every quad (eye visibility untouched) but normalise its orientation; Halo's F1 panel in
# stereo gameplay was rejected with XR_ERROR_POSE_INVALID in pass mode.
sub('mode = (m && streq(m, "drop")) ? 1 : (m && streq(m, "pass")) ? 2 : 0;',
    'mode = (m && streq(m, "drop")) ? 1 : (m && streq(m, "pass")) ? 2 : (m && streq(m, "norm")) ? 3 : 0;')
sub('mode == 0 ? "both" : mode == 1 ? "drop" : "pass"',
    'mode == 0 ? "both" : mode == 1 ? "drop" : mode == 2 ? "pass" : "norm"')
sub('            if (mode == 2) { layers[n++] = h; continue; }\n',
    '            if (mode == 2) { layers[n++] = h; continue; }\n'
    '            if (mode == 3) {\n'
    '                memcpy(&quads[n], q, sizeof *q);\n'
    '                normalise(&quads[n].pose.orientation);\n'
    '                move_view_quad(&quads[n], base_space, info->displayTime);\n'
    '                layers[n] = (const XrCompositionLayerBaseHeader *)&quads[n];\n'
    '                n++; continue;\n'
    '            }\n')
# head-locked (VIEW space) quads -> projection space; see space_part.c
space = (here / "space_part.c").read_text()
sub("static XrResult XRAPI_CALL quadfix_end_frame(", space + "\nstatic XrResult XRAPI_CALL quadfix_end_frame(")
sub('    unsigned n = 0, nquads = 0;\n',
    '    unsigned n = 0, nquads = 0;\n'
    '    XrSpace base_space = XR_NULL_HANDLE;   /* the projection layer space, for head-locked quads */\n'
    '    int has_view_quad = 0;   /* the F1 panel is up: SteamVR rejected it together with the crosshair quad */\n'
    '    for (unsigned i = 0; i < info->layerCount; i++) {\n'
    '        if (!base_space && info->layers[i]->type == XR_TYPE_COMPOSITION_LAYER_PROJECTION) base_space = info->layers[i]->space;\n'
    '        if (info->layers[i]->type == XR_TYPE_COMPOSITION_LAYER_QUAD && is_view_space(info->layers[i]->space)) has_view_quad = 1;\n'
    '    }\n')
sub('            if (mode == 3) {\n'
    '                memcpy(&quads[n], q, sizeof *q);\n',
    '            if (mode == 3) {\n'
    '                if (has_view_quad && !is_view_space(q->space)) continue;   /* menu up: show only the menu panel */\n'
    '                memcpy(&quads[n], q, sizeof *q);\n')
sub('    if (streq(name, "xrEndFrame") && next_end_frame)',
    '    if (streq(name, "xrCreateReferenceSpace") && next_create_ref_space) { *function = (PFN_xrVoidFunction)frame_create_ref_space; return XR_SUCCESS; }\n'
    '    if (streq(name, "xrEndFrame") && next_end_frame)')
sub('        next_gipa(*instance, "xrCreateActionSet", (PFN_xrVoidFunction *)&next_create_set);\n',
    '        next_gipa(*instance, "xrCreateActionSet", (PFN_xrVoidFunction *)&next_create_set);\n'
    '        next_gipa(*instance, "xrCreateReferenceSpace", (PFN_xrVoidFunction *)&next_create_ref_space);\n'
    '        next_gipa(*instance, "xrLocateSpace", (PFN_xrVoidFunction *)&next_locate_space);\n')
sub('"frames %llu: with quads ok %llu fail %llu | without quads ok %llu fail %llu\\n",\n'
    '                    frames, quad_ok, quad_fail, plain_ok, plain_fail);',
    '"frames %llu: with quads ok %llu fail %llu | without quads ok %llu fail %llu | head-locked quads moved %llu failed %llu\\n",\n'
    '                    frames, quad_ok, quad_fail, plain_ok, plain_fail, view_quads_moved, view_quads_failed);')
# log the quads of the first few rejected frames whatever the mode
sub('    frames++;\n',
    '    frames++;\n'
    '    static int fail_detail_left = 6;\n'
    '    if (XR_FAILED(r) && fail_detail_left > 0 && logf) {\n'
    '        fail_detail_left--;\n'
    '        fprintf(logf, "REJECTED frame %llu (%d), %u layers:\\n", frames, (int)r, info->layerCount);\n'
    '        for (unsigned i = 0; i < info->layerCount; i++) {\n'
    '            const XrCompositionLayerBaseHeader *h = info->layers[i];\n'
    '            if (h->type == XR_TYPE_COMPOSITION_LAYER_QUAD) log_quad((const XrCompositionLayerQuad *)h, i);\n'
    '            else fprintf(logf, "  layer[%u] type=%d flags=0x%llx space=%p\\n", i, (int)h->type, (unsigned long long)h->layerFlags, (void *)h->space);\n'
    '        }\n'
    '        fflush(logf);\n'
    '    }\n')
# Halo-only scope (matters on Windows, where an implicit layer loads into every OpenXR app)
sub('static XrResult XRAPI_CALL quadfix_gipa(XrInstance instance, const char *name, PFN_xrVoidFunction *function)\n{\n',
    'static XrResult XRAPI_CALL quadfix_gipa(XrInstance instance, const char *name, PFN_xrVoidFunction *function)\n{\n'
    '    if (layer_off) { if (!next_gipa) return XR_ERROR_HANDLE_INVALID; return next_gipa(instance, name, function); }\n')
sub('    open_log();\n    next_gipa = layer_info->nextInfo->nextGetInstanceProcAddr;\n',
    '    decide_layer_scope();\n    if (!layer_off) { open_log(); if (logf) { fprintf(logf, "layer active (Halo MCC process)\\n"); fflush(logf); } }\n'
    '    next_gipa = layer_info->nextInfo->nextGetInstanceProcAddr;\n')
(here / "framexr.c").write_text(src)
print("wrote", here / "framexr.c")
