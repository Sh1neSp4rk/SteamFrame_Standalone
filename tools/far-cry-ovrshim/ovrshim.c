/* ovrshim: a proxy openvr_api.dll (32-bit) for Far Cry VR on the Steam Frame.
 *
 * Proton's 32-bit vrclient asserts and aborts the game in IVROverlay::SetOverlayTexture when it gets a Vulkan texture
 * ("vroverlay_manual.c:465 !status"); CryVR draws its HUD/menus through overlays with Vulkan textures from its DXVK
 * fork. All exports forward to the mod's own openvr_api (renamed openvr_api_real.dll) except VR_GetGenericInterface,
 * which patches slot 60 (SetOverlayTexture) of the IVROverlay_026 vtable it hands out.
 *   FRAMEVR_HUD=skip (default): Vulkan overlay textures are not passed on (no HUD/menu panels, game keeps running)
 *   FRAMEVR_HUD=pass: passed through unchanged (diagnostic: reproduces the crash)
 * Log: ovrshim.log in the current directory. No imports: kernelbase is found through the PEB.
 * Built with clang --target=i686-pc-windows-msvc + lld-link, see build.sh. */

typedef unsigned int u32;
typedef unsigned long long u64;

/* ---- minimal kernelbase access through the PEB ---- */
typedef struct LE { struct LE *f, *b; } LE;
typedef struct { unsigned short len, max; unsigned short *buf; } US;
typedef struct { LE load, mem, init; char *base; void *entry; u32 size; US full, name; } LDR;

static int ieq_w(const unsigned short *w, int n, const char *a)
{
    int i = 0;
    for (; i < n && a[i]; i++) { unsigned c = w[i], d = (unsigned char)a[i]; if (c >= 'A' && c <= 'Z') c += 32; if (d >= 'A' && d <= 'Z') d += 32; if (c != d) return 0; }
    return i == n && !a[i];
}
static char *module(const char *name)
{
    char *peb; __asm__ volatile("movl %%fs:0x30, %0" : "=r"(peb));
    LE *head = (LE *)(*(char **)(peb + 0x0c) + 0x0c);
    for (LE *e = head->f; e != head; e = e->f) { LDR *m = (LDR *)e; if (ieq_w(m->name.buf, m->name.len / 2, name)) return m->base; }
    return 0;
}
static int seq(const char *a, const char *b) { while (*a && *a == *b) { a++; b++; } return *a == *b; }
static void *export_of(char *base, const char *fn)
{
    if (!base) return 0;
    char *nt = base + *(u32 *)(base + 0x3c);
    u32 rva = *(u32 *)(nt + 0x78), size = *(u32 *)(nt + 0x7c);
    char *ed = base + rva; u32 n = *(u32 *)(ed + 0x18);
    u32 *funcs = (u32 *)(base + *(u32 *)(ed + 0x1c)), *names = (u32 *)(base + *(u32 *)(ed + 0x20));
    unsigned short *ords = (unsigned short *)(base + *(u32 *)(ed + 0x24));
    for (u32 i = 0; i < n; i++)
        if (seq(base + names[i], fn)) { u32 f = funcs[ords[i]]; if (f >= rva && f < rva + size) return 0; return base + f; }
    return 0;
}
typedef void *(__stdcall *LoadLibraryA_t)(const char *);
typedef void *(__stdcall *GetProcAddress_t)(void *, const char *);
typedef void *(__stdcall *CreateFileA_t)(const char *, u32, u32, void *, u32, u32, void *);
typedef int (__stdcall *WriteFile_t)(void *, const void *, u32, u32 *, void *);
typedef u32 (__stdcall *GetEnvironmentVariableA_t)(const char *, char *, u32);
typedef u32 (__stdcall *GetTickCount_t)(void);
typedef int (__stdcall *CloseHandle_t)(void *);
static CloseHandle_t pCloseHandle;
typedef int (__stdcall *DeleteFileA_t)(const char *);
static DeleteFileA_t pDeleteFileA;
typedef void *(__stdcall *CreateFileMappingW_t)(void *, void *, u32, u32, u32, const unsigned short *);
typedef void *(__stdcall *MapViewOfFile_t)(void *, u32, u32, u32, u32);
static CreateFileMappingW_t pCreateFileMappingW; static MapViewOfFile_t pMapViewOfFile;
static GetTickCount_t pGetTickCount; static u32 min_ms = 100;
static LoadLibraryA_t pLoadLibraryA; static GetProcAddress_t pGetProcAddress;
static CreateFileA_t pCreateFileA; static WriteFile_t pWriteFile; static GetEnvironmentVariableA_t pGetEnv;
static void *logh;

static void init_k(void)
{
    if (pLoadLibraryA) return;
    char *k = module("kernelbase.dll"); if (!k) k = module("kernel32.dll");
    pLoadLibraryA = (LoadLibraryA_t)export_of(k, "LoadLibraryA"); pGetProcAddress = (GetProcAddress_t)export_of(k, "GetProcAddress");
    pCreateFileA = (CreateFileA_t)export_of(k, "CreateFileA"); pWriteFile = (WriteFile_t)export_of(k, "WriteFile");
    pGetEnv = (GetEnvironmentVariableA_t)export_of(k, "GetEnvironmentVariableA");
    pGetTickCount = (GetTickCount_t)export_of(k, "GetTickCount");
    pCloseHandle = (CloseHandle_t)export_of(k, "CloseHandle");
    pDeleteFileA = (DeleteFileA_t)export_of(k, "DeleteFileA");
    pCreateFileMappingW = (CreateFileMappingW_t)export_of(k, "CreateFileMappingW");
    pMapViewOfFile = (MapViewOfFile_t)export_of(k, "MapViewOfFile");
}
static void log_s(const char *s)
{
    if (!pCreateFileA) return;
    if (!logh) logh = pCreateFileA("ovrshim.log", 0x40000000 /*GENERIC_WRITE*/, 1, 0, 2 /*CREATE_ALWAYS*/, 0x80, 0);
    if (!logh || logh == (void *)-1) return;
    u32 n = 0, w; while (s[n]) n++; pWriteFile(logh, s, n, &w, 0);
}
static void log_hex(const char *label, u32 v)
{
    char b[64]; int i = 0; while (label[i] && i < 40) { b[i] = label[i]; i++; }
    b[i++] = '0'; b[i++] = 'x'; for (int s = 28; s >= 0; s -= 4) b[i++] = "0123456789abcdef"[(v >> s) & 15];
    b[i++] = '\n'; b[i] = 0; log_s(b);
}

/* ---- freestanding helpers the compiler may call ---- */
void *memset(void *d, int c, unsigned n) { unsigned char *p = d; while (n--) *p++ = (unsigned char)c; return d; }
void *memcpy(void *d, const void *s, unsigned n) { unsigned char *p = d; const unsigned char *q = s; while (n--) *p++ = *q++; return d; }

/* ---- the overlay hook ---- */
#define VK_NO_PROTOTYPES
#include <vulkan/vulkan_core.h>
typedef struct { void *handle; int eType; int eColorSpace; } Texture_t;
typedef struct { u64 m_nImage; VkDevice dev; VkPhysicalDevice phys; VkInstance inst; VkQueue queue;
                 u32 family, width, height, format, samples; } VRVulkanTextureData_t;
enum { TextureType_Vulkan = 2, SLOT_SetOverlayTexture = 60, SLOT_SetOverlayRaw = 62, SLOT_SetOverlayFromFile = 63, VT_COPY = 128 };
typedef int (__attribute__((thiscall)) *SetOverlayFromFile_t)(void *self, u64 handle, const char *path);
static SetOverlayFromFile_t orig_set_file;
typedef int (__attribute__((thiscall)) *SetOverlayTexture_t)(void *self, u64 handle, const Texture_t *tex);
typedef int (__attribute__((thiscall)) *SetOverlayRaw_t)(void *self, u64 handle, void *buf, u32 w, u32 h, u32 bpp);
static void *newvt[VT_COPY];
static SetOverlayTexture_t orig_set_texture;
static SetOverlayRaw_t orig_set_raw;
static int mode;          /* 0 raw (default), 1 skip, 2 pass */
static int use_file = 0;  /* FRAMEVR_HUD=file: SetOverlayFromFile (SteamVR caches by path and never frees: leaks) */
static int bridge = 1;    /* default: pixels go to /tmp/farcryvr_bridge_<n>.shm; the native hudbridge sets them as a Vulkan texture.
                           * FRAMEVR_HUD=raw: SetOverlayRaw (dies after ~460 updates under Proton) */
enum { SLOT_CreateOverlay = 1, BR_HDR = 4096, BR_MAXDIM = 1024, BR_SIZE = BR_HDR + BR_MAXDIM * BR_MAXDIM * 4 };
static struct { u64 h; char key[128]; } keys[8];
static int stress;        /* FRAMEVR_HUD_STRESS=1: publish even unchanged frames (test SteamVR's limits) */
static int opaque;        /* FRAMEVR_HUD_OPAQUE=1: force alpha 255 (diagnostic) */
static int input_log;     /* FRAMEVR_INPUT_LOG=1: log IVRInput_010 traffic */
static u32 every = 2, maxdim = 1024, skipped;

/* Vulkan readback: blit (downscale + RGBA) -> copy to a host buffer -> SetOverlayRaw. Proton's 32-bit vrclient can't
 * take Vulkan overlay textures (its wow64 conversion asserts on 64-bit native handles), but raw pixels pass fine. */
static struct {
    int loaded;
    PFN_vkGetDeviceProcAddr gdpa;
    PFN_vkCreateCommandPool CreateCommandPool; PFN_vkAllocateCommandBuffers AllocateCommandBuffers;
    PFN_vkCreateFence CreateFence; PFN_vkResetFences ResetFences; PFN_vkWaitForFences WaitForFences;
    PFN_vkCreateImage CreateImage; PFN_vkGetImageMemoryRequirements GetImageMemoryRequirements;
    PFN_vkAllocateMemory AllocateMemory; PFN_vkBindImageMemory BindImageMemory; PFN_vkCreateBuffer CreateBuffer;
    PFN_vkGetBufferMemoryRequirements GetBufferMemoryRequirements; PFN_vkBindBufferMemory BindBufferMemory;
    PFN_vkMapMemory MapMemory; PFN_vkBeginCommandBuffer BeginCommandBuffer; PFN_vkEndCommandBuffer EndCommandBuffer;
    PFN_vkResetCommandBuffer ResetCommandBuffer; PFN_vkCmdPipelineBarrier CmdPipelineBarrier;
    PFN_vkCmdBlitImage CmdBlitImage; PFN_vkCmdCopyImageToBuffer CmdCopyImageToBuffer; PFN_vkQueueSubmit QueueSubmit;
    PFN_vkGetFenceStatus GetFenceStatus;
    VkPhysicalDeviceMemoryProperties mem;
} vk;

/* two copy slots per overlay: a copy is submitted on one while the other's finished result is published, so the
 * game never waits on the GPU; unchanged pictures are not re-sent to SteamVR */
typedef struct {
    u64 handle; int ok, failed; u32 calls, next, published, unchanged;
    VkDevice dev; u32 sw, sh, sfmt, dw, dh; VkFormat dfmt;
    VkImage img; VkDeviceMemory imem; VkCommandPool pool;
    VkBuffer buf[2]; VkDeviceMemory bmem[2]; void *map[2]; VkCommandBuffer cb[2]; VkFence fence[2]; int pending[2];
    u32 seq[2], sig, last_ms, rejected;
    volatile u32 *shm;
} Ov;
static Ov ovs[8];

static int vk_load(const VRVulkanTextureData_t *d)
{
    if (vk.loaded) return vk.loaded > 0;
    vk.loaded = -1;
    char *v1 = module("vulkan-1.dll"); if (!v1) v1 = pLoadLibraryA("vulkan-1.dll");
    PFN_vkGetInstanceProcAddr gipa = v1 ? (PFN_vkGetInstanceProcAddr)pGetProcAddress(v1, "vkGetInstanceProcAddr") : 0;
    if (!gipa) { log_s("readback: no vulkan-1.dll vkGetInstanceProcAddr\n"); return 0; }
    vk.gdpa = (PFN_vkGetDeviceProcAddr)gipa(d->inst, "vkGetDeviceProcAddr");
    PFN_vkGetPhysicalDeviceMemoryProperties gpmp = (PFN_vkGetPhysicalDeviceMemoryProperties)gipa(d->inst, "vkGetPhysicalDeviceMemoryProperties");
    if (!vk.gdpa || !gpmp) { log_s("readback: instance functions missing\n"); return 0; }
    gpmp(d->phys, &vk.mem);
#define L(n) if (!(vk.n = (PFN_vk##n)vk.gdpa(d->dev, "vk" #n))) { log_s("readback: missing vk" #n "\n"); return 0; }
    L(CreateCommandPool) L(AllocateCommandBuffers) L(CreateFence) L(ResetFences) L(WaitForFences) L(CreateImage)
    L(GetImageMemoryRequirements) L(AllocateMemory) L(BindImageMemory) L(CreateBuffer) L(GetBufferMemoryRequirements)
    L(BindBufferMemory) L(MapMemory) L(BeginCommandBuffer) L(EndCommandBuffer) L(ResetCommandBuffer)
    L(CmdPipelineBarrier) L(CmdBlitImage) L(CmdCopyImageToBuffer) L(QueueSubmit) L(GetFenceStatus)
    vk.loaded = 1; log_s("readback: Vulkan functions loaded\n");
    return 1;
}
static int mem_type(u32 bits, VkMemoryPropertyFlags want, VkMemoryPropertyFlags prefer)
{
    int best = -1;
    for (u32 i = 0; i < vk.mem.memoryTypeCount; i++) {
        if (!(bits & (1u << i)) || (vk.mem.memoryTypes[i].propertyFlags & want) != want) continue;
        if ((vk.mem.memoryTypes[i].propertyFlags & prefer) == prefer) return (int)i;
        if (best < 0) best = (int)i;
    }
    return best;
}
static int setup(Ov *o, const VRVulkanTextureData_t *d)
{
    o->ok = 0; o->dev = d->dev; o->sw = d->width; o->sh = d->height; o->sfmt = d->format;
    if (bridge && maxdim > BR_MAXDIM) maxdim = BR_MAXDIM;
    u32 m = o->sw > o->sh ? o->sw : o->sh;
    o->dw = m > maxdim ? o->sw * maxdim / m : o->sw; o->dh = m > maxdim ? o->sh * maxdim / m : o->sh;
    o->dfmt = (d->format == VK_FORMAT_B8G8R8A8_SRGB || d->format == VK_FORMAT_R8G8B8A8_SRGB) ? VK_FORMAT_R8G8B8A8_SRGB : VK_FORMAT_R8G8B8A8_UNORM;
    if (use_file) o->dfmt = o->dfmt == VK_FORMAT_R8G8B8A8_SRGB ? VK_FORMAT_B8G8R8A8_SRGB : VK_FORMAT_B8G8R8A8_UNORM;   /* BMP is BGRA */
    VkResult r; VkMemoryRequirements req; int t;
    VkImageCreateInfo ii = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO };
    ii.imageType = VK_IMAGE_TYPE_2D; ii.format = o->dfmt; ii.extent.width = o->dw; ii.extent.height = o->dh; ii.extent.depth = 1;
    ii.mipLevels = 1; ii.arrayLayers = 1; ii.samples = VK_SAMPLE_COUNT_1_BIT; ii.tiling = VK_IMAGE_TILING_OPTIMAL;
    ii.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT; ii.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    if ((r = vk.CreateImage(o->dev, &ii, 0, &o->img))) { log_hex("readback: vkCreateImage ", r); return 0; }
    vk.GetImageMemoryRequirements(o->dev, o->img, &req);
    if ((t = mem_type(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT, 0)) < 0) { log_s("readback: no image memory type\n"); return 0; }
    VkMemoryAllocateInfo ai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO }; ai.allocationSize = req.size; ai.memoryTypeIndex = (u32)t;
    if ((r = vk.AllocateMemory(o->dev, &ai, 0, &o->imem)) || (r = vk.BindImageMemory(o->dev, o->img, o->imem, 0))) { log_hex("readback: image memory ", r); return 0; }
    VkCommandPoolCreateInfo pi = { VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO };
    pi.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT; pi.queueFamilyIndex = d->family;
    if ((r = vk.CreateCommandPool(o->dev, &pi, 0, &o->pool))) { log_hex("readback: vkCreateCommandPool ", r); return 0; }
    VkCommandBufferAllocateInfo ci = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO };
    ci.commandPool = o->pool; ci.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; ci.commandBufferCount = 2;
    if ((r = vk.AllocateCommandBuffers(o->dev, &ci, o->cb))) { log_hex("readback: vkAllocateCommandBuffers ", r); return 0; }
    for (int k = 0; k < 2; k++) {
        VkBufferCreateInfo bi = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO }; bi.size = (VkDeviceSize)o->dw * o->dh * 4;
        bi.usage = VK_BUFFER_USAGE_TRANSFER_DST_BIT; bi.sharingMode = VK_SHARING_MODE_EXCLUSIVE;
        if ((r = vk.CreateBuffer(o->dev, &bi, 0, &o->buf[k]))) { log_hex("readback: vkCreateBuffer ", r); return 0; }
        vk.GetBufferMemoryRequirements(o->dev, o->buf[k], &req);
        t = mem_type(req.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT, VK_MEMORY_PROPERTY_HOST_CACHED_BIT);
        if (t < 0) { log_s("readback: no host memory type\n"); return 0; }
        ai.allocationSize = req.size; ai.memoryTypeIndex = (u32)t;
        if ((r = vk.AllocateMemory(o->dev, &ai, 0, &o->bmem[k])) || (r = vk.BindBufferMemory(o->dev, o->buf[k], o->bmem[k], 0)) ||
            (r = vk.MapMemory(o->dev, o->bmem[k], 0, VK_WHOLE_SIZE, 0, &o->map[k]))) { log_hex("readback: buffer memory ", r); return 0; }
        VkFenceCreateInfo fi = { VK_STRUCTURE_TYPE_FENCE_CREATE_INFO };
        if ((r = vk.CreateFence(o->dev, &fi, 0, &o->fence[k]))) { log_hex("readback: vkCreateFence ", r); return 0; }
        o->pending[k] = 0;
    }
    o->next = 0; o->sig = 0;
    log_hex("readback: overlay set up, source width ", o->sw); log_hex("  source height ", o->sh);
    log_hex("  source format ", o->sfmt); log_hex("  raw width ", o->dw); log_hex("  raw height ", o->dh);
    o->ok = 1; return 1;
}
static int readback(Ov *o, const VRVulkanTextureData_t *d, int k)
{
    VkCommandBuffer cb = o->cb[k]; VkResult r;
    vk.ResetCommandBuffer(cb, 0);
    VkCommandBufferBeginInfo bb = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO }; bb.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vk.BeginCommandBuffer(cb, &bb);
    VkImageMemoryBarrier b[2] = { { VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER }, { VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER } };
    VkImageSubresourceRange rng = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
    /* the app hands OpenVR its overlay image in TRANSFER_SRC_OPTIMAL; make its writes visible to our read */
    b[0].srcAccessMask = VK_ACCESS_MEMORY_WRITE_BIT; b[0].dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    b[0].oldLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL; b[0].newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    b[0].srcQueueFamilyIndex = b[0].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b[0].image = (VkImage)d->m_nImage; b[0].subresourceRange = rng;
    b[1].srcAccessMask = 0; b[1].dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT;
    b[1].oldLayout = VK_IMAGE_LAYOUT_UNDEFINED; b[1].newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    b[1].srcQueueFamilyIndex = b[1].dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b[1].image = o->img; b[1].subresourceRange = rng;
    vk.CmdPipelineBarrier(cb, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, 0, 0, 0, 2, b);
    VkImageBlit bl; memset(&bl, 0, sizeof bl);
    bl.srcSubresource.aspectMask = bl.dstSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
    bl.srcSubresource.layerCount = bl.dstSubresource.layerCount = 1;
    bl.srcOffsets[1].x = (int)o->sw; bl.srcOffsets[1].y = (int)o->sh; bl.srcOffsets[1].z = 1;
    bl.dstOffsets[1].x = (int)o->dw; bl.dstOffsets[1].y = (int)o->dh; bl.dstOffsets[1].z = 1;
    vk.CmdBlitImage(cb, (VkImage)d->m_nImage, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, o->img, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &bl, VK_FILTER_LINEAR);
    b[1].srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; b[1].dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT;
    b[1].oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL; b[1].newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;
    vk.CmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, 0, 0, 0, 1, &b[1]);
    VkBufferImageCopy cp; memset(&cp, 0, sizeof cp);
    cp.imageSubresource.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT; cp.imageSubresource.layerCount = 1;
    cp.imageExtent.width = o->dw; cp.imageExtent.height = o->dh; cp.imageExtent.depth = 1;
    vk.CmdCopyImageToBuffer(cb, o->img, VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL, o->buf[k], 1, &cp);
    VkBufferMemoryBarrier hb = { VK_STRUCTURE_TYPE_BUFFER_MEMORY_BARRIER };
    hb.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; hb.dstAccessMask = VK_ACCESS_HOST_READ_BIT;
    hb.srcQueueFamilyIndex = hb.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; hb.buffer = o->buf[k]; hb.size = VK_WHOLE_SIZE;
    vk.CmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_HOST_BIT, 0, 0, 0, 1, &hb, 0, 0);
    vk.EndCommandBuffer(cb);
    VkSubmitInfo si = { VK_STRUCTURE_TYPE_SUBMIT_INFO }; si.commandBufferCount = 1; si.pCommandBuffers = &cb;
    vk.ResetFences(o->dev, 1, &o->fence[k]);
    if ((r = vk.QueueSubmit(d->queue, 1, &si, o->fence[k]))) { log_hex("readback: vkQueueSubmit ", r); return 0; }
    o->pending[k] = 1;
    return 1;
}
/* cheap change detection: a sparse sample of the picture (every 61st pixel) */
static u32 signature(const u32 *p, u32 n) { u32 h = 2166136261u; for (u32 i = 0; i < n; i += 61) h = (h ^ p[i]) * 16777619u; return h; }

/* FRAMEVR_HUD=file: SteamVR's raw path stops accepting updates after a few hundred (leak); hand it a BMP in /tmp
 * instead, alternating two file names so it reloads. Top-down 32-bit BGRA (the blit writes BGRA in this mode). */
static int publish_file(void *self, Ov *o, u64 handle, const void *pixels)
{
    /* SteamVR caches overlay images by path, so every update gets a new name; the file from 4 updates ago is deleted */
    static u32 counter;
    u32 c = ++counter;
    char path[64] = "Z:\\tmp\\farcryvr_hud_0_00000000.bmp", old[64];
    path[20] = (char)('0' + ((u32)handle & 7));
    for (int i = 0; i < 8; i++) path[29 - i] = "0123456789abcdef"[(c >> (4 * i)) & 15];
    memcpy(old, path, sizeof path);
    if (c > 4) { u32 oc = c - 4; for (int i = 0; i < 8; i++) old[29 - i] = "0123456789abcdef"[(oc >> (4 * i)) & 15]; if (pDeleteFileA) pDeleteFileA(old); }
    u32 w = o->dw, h = o->dh, img = w * h * 4;
    unsigned char hd[54]; memset(hd, 0, sizeof hd);
    u32 fsz = 54 + img;
    hd[0] = 'B'; hd[1] = 'M'; memcpy(hd + 2, &fsz, 4); hd[10] = 54;
    u32 v = 40; memcpy(hd + 14, &v, 4); memcpy(hd + 18, &w, 4); int nh = -(int)h; memcpy(hd + 22, &nh, 4);
    hd[26] = 1; hd[28] = 32; memcpy(hd + 34, &img, 4);
    void *f = pCreateFileA(path, 0x40000000, 0, 0, 2, 0x80, 0);
    if (!f || f == (void *)-1) { log_s("file: cannot write /tmp bmp\n"); return 99; }
    u32 wr; pWriteFile(f, hd, 54, &wr, 0); pWriteFile(f, pixels, img, &wr, 0); pCloseHandle(f);
    return orig_set_file(self, handle, path);
}

/* bridge: header {magic, seq, w, h, vkformat, 0, handle lo, handle hi, key[128]} then pixels at BR_HDR.
 * seq is odd while a frame is being written (seqlock); the reader copies and re-checks it. */
static int publish_bridge(Ov *o, u64 handle, const void *pixels)
{
    if (!o->shm) {
        if (!pCreateFileMappingW || !pMapViewOfFile) { log_s("bridge: no file mapping functions\n"); return 99; }
        char path[40] = "Z:\\tmp\\farcryvr_bridge_0.shm"; path[23] = (char)('0' + (int)(o - ovs));
        void *f = pCreateFileA(path, 0xC0000000 /*read|write*/, 3, 0, 4 /*OPEN_ALWAYS*/, 0x80, 0);
        if (!f || f == (void *)-1) { log_s("bridge: cannot open /tmp shm file\n"); return 99; }
        void *m = pCreateFileMappingW(f, 0, 4 /*PAGE_READWRITE*/, 0, BR_SIZE, 0);
        o->shm = m ? (volatile u32 *)pMapViewOfFile(m, 6 /*read|write*/, 0, 0, BR_SIZE) : 0;
        if (!o->shm) { log_s("bridge: mapping failed\n"); return 99; }
        log_s("bridge: mapped "); log_s(path); log_s("\n");
    }
    volatile u32 *h = o->shm;
    u32 s = h[1] | 1; h[1] = s; __sync_synchronize();
    h[0] = 0x52564346; h[2] = o->dw; h[3] = o->dh; h[4] = (u32)o->dfmt; h[6] = (u32)handle; h[7] = (u32)(handle >> 32);
    char *kd = (char *)(h + 8);
    for (int i = 0; i < 8; i++) if (keys[i].h == handle) { for (int j = 0; j < 128; j++) kd[j] = keys[i].key[j]; break; }
    { volatile u32 *d = h + BR_HDR / 4; const u32 *p = pixels; for (u32 i = 0, n = o->dw * o->dh; i < n; i++) d[i] = p[i]; }
    __sync_synchronize(); h[1] = s + 1; __sync_synchronize();
    return 0;
}
typedef int (__attribute__((thiscall)) *CreateOverlay_t)(void *self, const char *key, const char *name, u64 *out);
static CreateOverlay_t orig_create;
static int __attribute__((thiscall)) hook_create(void *self, const char *key, const char *name, u64 *out)
{
    int r = orig_create(self, key, name, out);
    if (!r && out) for (int i = 0; i < 8; i++) if (!keys[i].h) {
        keys[i].h = *out; int j = 0; for (; key && key[j] && j < 127; j++) keys[i].key[j] = key[j]; keys[i].key[j] = 0; break; }
    log_s("CreateOverlay "); log_s(key ? key : "?"); log_hex("  handle lo ", out ? (u32)*out : 0);
    return r;
}

static int __attribute__((thiscall)) hook_set_texture(void *self, u64 handle, const Texture_t *tex)
{
    if (!tex || tex->eType != TextureType_Vulkan || mode == 2) return orig_set_texture(self, handle, tex);
    if (mode == 1) { if (skipped++ < 3) log_s("SetOverlayTexture(Vulkan) skipped\n"); return 0; }
    const VRVulkanTextureData_t *d = (const VRVulkanTextureData_t *)tex->handle;
    Ov *o = 0;
    for (int i = 0; i < 8; i++) if (ovs[i].handle == handle) { o = &ovs[i]; break; }
    if (!o) for (int i = 0; i < 8; i++) if (!ovs[i].handle) { o = &ovs[i]; o->handle = handle; log_hex("overlay seen, handle low ", (u32)handle); break; }
    if (!o || o->failed || !d || d->samples > 1) return 0;
    if (o->calls++ % every) return 0;
    /* only trust texture data on the device the first good overlay used, with sane sizes */
    static VkDevice good_dev; static VkQueue good_queue; static u32 bad_logged;
    if (!d->dev || !d->queue || !d->m_nImage || d->width - 1 >= 8192 || d->height - 1 >= 8192 ||
        (good_dev && (d->dev != good_dev || d->queue != good_queue))) {
        if (bad_logged++ < 6) {
            log_hex("skip: bad texture data for overlay ", (u32)handle); log_hex("  dev ", (u32)d->dev); log_hex("  queue ", (u32)d->queue);
            log_hex("  image lo ", (u32)d->m_nImage); log_hex("  width ", d->width); log_hex("  height ", d->height); log_hex("  format ", d->format);
        }
        return 0;
    }
    if (!vk_load(d)) { o->failed = 1; return 0; }
    if (!good_dev) { good_dev = d->dev; good_queue = d->queue; }
    if (!o->ok || o->sw != d->width || o->sh != d->height || o->sfmt != d->format || o->dev != d->dev)
        if (!setup(o, d)) { o->failed = 1; log_s("readback: setup failed, overlay stays blank\n"); return 0; }
    int r = 0;
    /* publish at most ONE finished copy per call (never wait), no more often than min_ms, and only if it changed:
     * SteamVR answers rapid raw updates with VROverlayError_RequestFailed (23) */
    u32 now = pGetTickCount ? pGetTickCount() : 0;
    int ready = -1;
    for (int j = 0; j < 2; j++) {
        if (!o->pending[j] || vk.GetFenceStatus(o->dev, o->fence[j]) != VK_SUCCESS) continue;
        o->pending[j] = 0;
        if (ready < 0 || o->seq[j] > o->seq[ready]) ready = j;   /* newest finished copy */
    }
    if (ready >= 0 && (!o->published || now - o->last_ms >= min_ms)) {
        u32 n = o->dw * o->dh, s = signature((const u32 *)o->map[ready], n);
        if (s == o->sig && o->published && !stress) o->unchanged++;
        else {
            if (opaque) { u32 *p = (u32 *)o->map[ready]; for (u32 i = 0; i < n; i++) p[i] |= 0xff000000u; }
            /* the bridge draws on its own mirror overlay; the game's keeps one transparent pixel so the laser pointer
             * still has a target for the menus (a single raw update, far from the ~460 limit) */
            if (bridge && !o->published) { static u32 clear; log_hex("bridge: transparent pixel on game overlay -> ", (u32)orig_set_raw(self, handle, &clear, 1, 1, 4)); }
            r = bridge ? publish_bridge(o, handle, o->map[ready]) : use_file ? publish_file(self, o, handle, o->map[ready]) : orig_set_raw(self, handle, o->map[ready], o->dw, o->dh, 4);
            if (!r) { o->sig = s; o->last_ms = now; }
            if (r) o->rejected++;
            if (o->published++ < 2 || (r && o->rejected < 5)) log_hex("SetOverlayRaw result ", (u32)r);
            if ((o->published & 511) == 0) { log_hex("published ", o->published); log_hex("  unchanged skipped ", o->unchanged); log_hex("  rejected ", o->rejected); }
        }
    }
    int k = (int)(o->next & 1);
    if (!o->pending[k]) { if (!readback(o, d, k)) { o->failed = 1; log_s("readback: failed, overlay stays blank\n"); return 0; } o->seq[k] = ++o->next; }
    return r;
}

/* ---- IVRInput_010 logging (slots confirmed from CryGame.dll call sites) ---- */
enum { SLOT_GetActionHandle = 2, SLOT_UpdateActionState = 4, SLOT_GetDigital = 5, SLOT_GetAnalog = 6 };
typedef int (__attribute__((thiscall)) *GetActionHandle_t)(void *self, const char *name, u64 *out);
typedef int (__attribute__((thiscall)) *UpdateActionState_t)(void *self, void *sets, u32 size, u32 count);
typedef int (__attribute__((thiscall)) *GetActionData_t)(void *self, u64 action, void *data, u32 size, u64 restrict_dev);
static void *invt[VT_COPY];
static GetActionHandle_t orig_gah; static UpdateActionState_t orig_uas; static GetActionData_t orig_gdig, orig_gana;
static struct { u64 h; char name[48]; u32 calls, errs; u32 last; } acts[48]; static int nacts;
static u32 uas_calls;
static void log_str2(const char *a, const char *b) { log_s(a); log_s(b); log_s("\n"); }
static int act_index(u64 h) { for (int i = 0; i < nacts; i++) if (acts[i].h == h) return i; return -1; }
static int __attribute__((thiscall)) hook_gah(void *self, const char *name, u64 *out)
{
    int r = orig_gah(self, name, out);
    if (out && nacts < 48) { acts[nacts].h = *out; int i = 0; const char *p = name; for (int k = 0; p[k]; k++) if (p[k] == '/') i = k + 1;
        int j = 0; for (; p[i + j] && j < 47; j++) acts[nacts].name[j] = p[i + j]; acts[nacts].name[j] = 0; nacts++; }
    log_str2("action ", name); log_hex("  -> result ", (u32)r); log_hex("  handle lo ", out ? (u32)*out : 0);
    return r;
}
static int __attribute__((thiscall)) hook_uas(void *self, void *sets, u32 size, u32 count)
{
    int r = orig_uas(self, sets, size, count);
    if (uas_calls++ % 500 == 0 || r) {
        log_hex("UpdateActionState result ", (u32)r); log_hex("  set struct size ", size); log_hex("  set count ", count);
        for (u32 i = 0; i < count && i < 6; i++) { u32 *s = (u32 *)((char *)sets + i * size);
            log_hex("  set handle lo ", s[0]); log_hex("    restrict lo ", s[2]); log_hex("    priority ", s[7]); }
    }
    return r;
}
static int __attribute__((thiscall)) hook_gdig(void *self, u64 action, void *data, u32 size, u64 rd)
{
    int r = orig_gdig(self, action, data, size, rd);
    int i = act_index(action); if (i < 0) return r;
    unsigned char *d = data; u32 state = d ? ((u32)d[0] | (u32)d[16] << 8) : 0xffff;   /* bActive, bState */
    if (r) acts[i].errs++;
    if ((acts[i].calls++ % 600 == 0) || state != acts[i].last || (r && acts[i].errs < 4)) {
        log_str2("digital ", acts[i].name); log_hex("  result ", (u32)r); log_hex("  size ", size);
        log_hex("  active|state<<8 ", state); log_hex("  restrict lo ", (u32)rd); acts[i].last = state;
    }
    return r;
}
static int __attribute__((thiscall)) hook_gana(void *self, u64 action, void *data, u32 size, u64 rd)
{
    int r = orig_gana(self, action, data, size, rd);
    int i = act_index(action); if (i < 0) return r;
    unsigned char *d = data; u32 act = d ? d[0] : 0xff; u32 x = d ? *(u32 *)(d + 16) : 0, y = d ? *(u32 *)(d + 20) : 0;
    u32 moving = (x & 0x7fffffff) > 0x3e000000 || (y & 0x7fffffff) > 0x3e000000;   /* |x| or |y| > 0.125 */
    if (r) acts[i].errs++;
    if ((acts[i].calls++ % 600 == 0) || (moving && acts[i].last != 1) || (!moving && acts[i].last == 1) || (r && acts[i].errs < 4)) {
        log_str2("analog ", acts[i].name); log_hex("  result ", (u32)r); log_hex("  size ", size); log_hex("  active ", act);
        log_hex("  x bits ", x); log_hex("  y bits ", y); log_hex("  restrict lo ", (u32)rd); acts[i].last = moving;
    }
    return r;
}

typedef void *(__cdecl *GGI_t)(const char *, int *);
static GGI_t real_ggi;

__declspec(dllexport) void *__cdecl VR_GetGenericInterface(const char *version, int *err)
{
    init_k();
    if (!real_ggi) {
        void *real = pLoadLibraryA("openvr_api_real.dll");
        real_ggi = real ? (GGI_t)pGetProcAddress(real, "VR_GetGenericInterface") : 0;
        char v[16] = {0};
        if (pGetEnv && pGetEnv("FRAMEVR_HUD", v, sizeof v)) {
            mode = seq(v, "pass") ? 2 : seq(v, "skip") ? 1 : 0;
            if (seq(v, "file")) { use_file = 1; bridge = 0; } else if (seq(v, "raw")) bridge = 0;
        }
        if (bridge) { if (maxdim > BR_MAXDIM) maxdim = BR_MAXDIM; min_ms = 33; log_s("  publishing through the native hudbridge (/tmp/farcryvr_bridge_*.shm)\n"); }
        if (use_file) log_s("  publishing through SetOverlayFromFile (/tmp/farcryvr_hud_*.bmp)\n");
        if (pGetEnv && pGetEnv("FRAMEVR_HUD_STRESS", v, sizeof v) && v[0] == '1') { stress = 1; log_s("  stress: publishing unchanged frames too\n"); }
        if (pGetEnv && pGetEnv("FRAMEVR_HUD_EVERY", v, sizeof v) && v[0] >= '1' && v[0] <= '9') every = (u32)(v[0] - '0');
        if (pGetEnv && pGetEnv("FRAMEVR_HUD_MAX", v, sizeof v)) { u32 n = 0; for (int i = 0; v[i] >= '0' && v[i] <= '9'; i++) n = n * 10 + (u32)(v[i] - '0'); if (n >= 256) maxdim = n; }
        log_s(mode == 2 ? "ovrshim loaded, FRAMEVR_HUD=pass\n" : mode == 1 ? "ovrshim loaded, FRAMEVR_HUD=skip\n" : "ovrshim loaded, FRAMEVR_HUD=raw\n");
        if (pGetEnv && pGetEnv("FRAMEVR_HUD_OPAQUE", v, sizeof v) && v[0] == '1') opaque = 1;
        if (pGetEnv && pGetEnv("FRAMEVR_HUD_MS", v, sizeof v)) { u32 n = 0; for (int i = 0; v[i] >= '0' && v[i] <= '9'; i++) n = n * 10 + (u32)(v[i] - '0'); min_ms = n; }
        log_hex("  min ms ", min_ms);
        if (pGetEnv && pGetEnv("FRAMEVR_INPUT_LOG", v, sizeof v) && v[0] == '1') input_log = 1;
        log_hex("  every ", every); log_hex("  max ", maxdim); log_hex("  opaque ", (u32)opaque); log_hex("  input log ", (u32)input_log);
        if (!real_ggi) { log_s("openvr_api_real.dll / VR_GetGenericInterface missing\n"); if (err) *err = 101; return 0; }
    }
    void *obj = real_ggi(version, err);
    int is_input = 1; const char *q = "IVRInput_010"; for (int i = 0; q[i]; i++) if (version[i] != q[i]) { is_input = 0; break; }
    if (obj && is_input && input_log) {
        void **vt = *(void ***)obj;
        if (vt != invt) {
            for (int i = 0; i < VT_COPY; i++) invt[i] = vt[i];
            orig_gah = (GetActionHandle_t)vt[SLOT_GetActionHandle]; invt[SLOT_GetActionHandle] = (void *)hook_gah;
            orig_uas = (UpdateActionState_t)vt[SLOT_UpdateActionState]; invt[SLOT_UpdateActionState] = (void *)hook_uas;
            orig_gdig = (GetActionData_t)vt[SLOT_GetDigital]; invt[SLOT_GetDigital] = (void *)hook_gdig;
            orig_gana = (GetActionData_t)vt[SLOT_GetAnalog]; invt[SLOT_GetAnalog] = (void *)hook_gana;
            *(void ***)obj = invt;
            log_hex("IVRInput_010 patched for logging, object ", (u32)obj);
        }
    }
    int is_overlay = 1; const char *p = "IVROverlay_026"; for (int i = 0; p[i]; i++) if (version[i] != p[i]) { is_overlay = 0; break; }
    if (obj && is_overlay) {
        void **vt = *(void ***)obj;
        if (vt != newvt) {
            for (int i = 0; i < VT_COPY; i++) newvt[i] = vt[i];
            orig_set_texture = (SetOverlayTexture_t)vt[SLOT_SetOverlayTexture];
            orig_set_raw = (SetOverlayRaw_t)vt[SLOT_SetOverlayRaw];
            orig_set_file = (SetOverlayFromFile_t)vt[SLOT_SetOverlayFromFile];
            orig_create = (CreateOverlay_t)vt[SLOT_CreateOverlay];
            newvt[SLOT_SetOverlayTexture] = (void *)hook_set_texture;
            newvt[SLOT_CreateOverlay] = (void *)hook_create;
            *(void ***)obj = newvt;
            log_hex("IVROverlay_026 patched, object ", (u32)obj);
        }
    }
    return obj;
}

/* ---- the other 17 exports: jump stubs to openvr_api_real (lld-link mangles x86 .def forwarders) ---- */
#define FWD_LIST(X) X(LiquidVR) X(VRControlPanel) X(VRHeadsetView) X(VRPaths) X(VRVirtualDisplay) X(VR_GetInitToken) \
    X(VR_GetRuntimePath) X(VR_GetStringForHmdError) X(VR_GetVRInitErrorAsEnglishDescription) X(VR_GetVRInitErrorAsSymbol) \
    X(VR_InitInternal) X(VR_InitInternal2) X(VR_IsHmdPresent) X(VR_IsInterfaceVersionValid) X(VR_IsRuntimeInstalled) \
    X(VR_RuntimePath) X(VR_ShutdownInternal)
#define DECL_P(n) void *p_##n;
FWD_LIST(DECL_P)
void resolve_all(void)
{
    static int done; if (done) return;
    init_k(); void *real = pLoadLibraryA("openvr_api_real.dll");
#define RES(n) p_##n = real ? pGetProcAddress(real, #n) : 0;
    FWD_LIST(RES)
    done = 1;
}
/* cdecl exports: arguments stay on the stack; eax/ecx/edx are scratch, so resolve then tail-jump */
#define STUB(n) __attribute__((naked)) void n(void) { __asm__ volatile("call _resolve_all\n\tjmp *_p_" #n); }
FWD_LIST(STUB)

int __stdcall DllMain(void *inst, u32 reason, void *reserved) { (void)inst; (void)reason; (void)reserved; return 1; }
