// hudbridge: native (aarch64 Linux) helper for Far Cry VR on the Steam Frame.
//
// Proton's 32-bit OpenVR bridge can't pass Vulkan overlay textures, and SteamVR's raw/file overlay paths leak on
// every update. ovrshim (inside the game) writes each finished HUD/menu frame to /tmp/farcryvr_bridge_<n>.shm; this
// process maps those files, uploads changed frames into its own Vulkan images and hands them to SteamVR with
// SetOverlayTexture on the mod's overlay (found by key), or on a mirror overlay of its own if that is refused.
//
// Usage: hudbridge <pid to follow>   (exits when that process is gone)
#include <openvr.h>
#include <vulkan/vulkan.h>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdarg>
#include <csignal>
#include <cerrno>
#include <ctime>
#include <string>
#include <vector>
#include <fcntl.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/stat.h>

enum { BR_HDR = 4096, BR_MAXDIM = 1024, BR_SIZE = BR_HDR + BR_MAXDIM * BR_MAXDIM * 4, NIMG = 3 };

static void logf(const char *f, ...)
{
    time_t t = time(0); char ts[16]; strftime(ts, sizeof ts, "%H:%M:%S", localtime(&t));
    fprintf(stderr, "%s ", ts); va_list a; va_start(a, f); vfprintf(stderr, f, a); va_end(a); fputc('\n', stderr); fflush(stderr);
}

static VkInstance inst; static VkPhysicalDevice phys; static VkDevice dev; static VkQueue queue; static uint32_t family;
static VkCommandPool pool; static VkCommandBuffer cb; static VkFence fence; static VkPhysicalDeviceMemoryProperties memp;

static int mem_type(uint32_t bits, VkMemoryPropertyFlags want)
{
    for (uint32_t i = 0; i < memp.memoryTypeCount; i++)
        if ((bits & (1u << i)) && (memp.memoryTypes[i].propertyFlags & want) == want) return (int)i;
    return -1;
}
static std::vector<std::string> split(const char *s)
{
    std::vector<std::string> v; std::string cur;
    for (; *s; s++) { if (*s == ' ') { if (!cur.empty()) v.push_back(cur); cur.clear(); } else cur += *s; }
    if (!cur.empty()) v.push_back(cur);
    return v;
}
static bool vk_init()
{
    char buf[4096] = {0};
    vr::VRCompositor()->GetVulkanInstanceExtensionsRequired(buf, sizeof buf);
    std::vector<std::string> ie = split(buf); std::vector<const char *> iep; for (auto &s : ie) iep.push_back(s.c_str());
    VkApplicationInfo ai = { VK_STRUCTURE_TYPE_APPLICATION_INFO }; ai.pApplicationName = "farcryvr_hudbridge"; ai.apiVersion = VK_API_VERSION_1_1;
    VkInstanceCreateInfo ici = { VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO }; ici.pApplicationInfo = &ai;
    ici.enabledExtensionCount = (uint32_t)iep.size(); ici.ppEnabledExtensionNames = iep.data();
    VkResult r = vkCreateInstance(&ici, 0, &inst); if (r) { logf("vkCreateInstance %d (ext: %s)", r, buf); return false; }
    uint64_t pd = 0; vr::VRSystem()->GetOutputDevice(&pd, vr::TextureType_Vulkan, inst);
    phys = (VkPhysicalDevice)pd;
    if (!phys) { uint32_t n = 1; vkEnumeratePhysicalDevices(inst, &n, &phys); }
    vkGetPhysicalDeviceMemoryProperties(phys, &memp);
    memset(buf, 0, sizeof buf);
    vr::VRCompositor()->GetVulkanDeviceExtensionsRequired(phys, buf, sizeof buf);
    std::vector<std::string> de = split(buf); std::vector<const char *> dep; for (auto &s : de) dep.push_back(s.c_str());
    uint32_t nq = 0; vkGetPhysicalDeviceQueueFamilyProperties(phys, &nq, 0);
    std::vector<VkQueueFamilyProperties> qp(nq); vkGetPhysicalDeviceQueueFamilyProperties(phys, &nq, qp.data());
    family = 0; for (uint32_t i = 0; i < nq; i++) if (qp[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) { family = i; break; }
    float prio = 1.0f;
    VkDeviceQueueCreateInfo qi = { VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO }; qi.queueFamilyIndex = family; qi.queueCount = 1; qi.pQueuePriorities = &prio;
    VkDeviceCreateInfo dci = { VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO }; dci.queueCreateInfoCount = 1; dci.pQueueCreateInfos = &qi;
    dci.enabledExtensionCount = (uint32_t)dep.size(); dci.ppEnabledExtensionNames = dep.data();
    if ((r = vkCreateDevice(phys, &dci, 0, &dev))) { logf("vkCreateDevice %d (ext: %s)", r, buf); return false; }
    vkGetDeviceQueue(dev, family, 0, &queue);
    VkCommandPoolCreateInfo pi = { VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO }; pi.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT; pi.queueFamilyIndex = family;
    vkCreateCommandPool(dev, &pi, 0, &pool);
    VkCommandBufferAllocateInfo ca = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO }; ca.commandPool = pool; ca.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY; ca.commandBufferCount = 1;
    vkAllocateCommandBuffers(dev, &ca, &cb);
    VkFenceCreateInfo fi = { VK_STRUCTURE_TYPE_FENCE_CREATE_INFO }; vkCreateFence(dev, &fi, 0, &fence);
    logf("vulkan ready, queue family %u, device extensions: %s", family, buf);
    return true;
}

struct Slot {
    int fd = -1; volatile uint32_t *shm = 0; uint32_t last = 0;
    uint32_t w = 0, h = 0, fmt = 0; VkImage img[NIMG] = {}; VkDeviceMemory mem[NIMG] = {}; int cur = 0;
    VkBuffer sb = 0; VkDeviceMemory smem = 0; void *smap = 0;
    vr::VROverlayHandle_t target = vr::k_ulOverlayHandleInvalid, game = vr::k_ulOverlayHandleInvalid; bool mirror = false;
    char key[128] = {0}; unsigned sent = 0, errs = 0;
};
static Slot slots[8];

static void free_images(Slot &s)
{
    vkDeviceWaitIdle(dev);
    for (int i = 0; i < NIMG; i++) { if (s.img[i]) vkDestroyImage(dev, s.img[i], 0); if (s.mem[i]) vkFreeMemory(dev, s.mem[i], 0); s.img[i] = 0; s.mem[i] = 0; }
    if (s.sb) { vkDestroyBuffer(dev, s.sb, 0); vkFreeMemory(dev, s.smem, 0); s.sb = 0; s.smem = 0; s.smap = 0; }
}
static bool make_images(Slot &s, uint32_t w, uint32_t h, uint32_t fmt)
{
    free_images(s);
    VkMemoryRequirements req; VkResult r;
    for (int i = 0; i < NIMG; i++) {
        VkImageCreateInfo ii = { VK_STRUCTURE_TYPE_IMAGE_CREATE_INFO };
        ii.imageType = VK_IMAGE_TYPE_2D; ii.format = (VkFormat)fmt; ii.extent = { w, h, 1 }; ii.mipLevels = 1; ii.arrayLayers = 1;
        ii.samples = VK_SAMPLE_COUNT_1_BIT; ii.tiling = VK_IMAGE_TILING_OPTIMAL;
        ii.usage = VK_IMAGE_USAGE_TRANSFER_DST_BIT | VK_IMAGE_USAGE_TRANSFER_SRC_BIT | VK_IMAGE_USAGE_SAMPLED_BIT;
        ii.initialLayout = VK_IMAGE_LAYOUT_UNDEFINED;
        if ((r = vkCreateImage(dev, &ii, 0, &s.img[i]))) { logf("vkCreateImage %d", r); return false; }
        vkGetImageMemoryRequirements(dev, s.img[i], &req);
        VkMemoryAllocateInfo ai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO }; ai.allocationSize = req.size;
        ai.memoryTypeIndex = (uint32_t)mem_type(req.memoryTypeBits, VK_MEMORY_PROPERTY_DEVICE_LOCAL_BIT);
        if ((r = vkAllocateMemory(dev, &ai, 0, &s.mem[i])) || (r = vkBindImageMemory(dev, s.img[i], s.mem[i], 0))) { logf("image memory %d", r); return false; }
    }
    VkBufferCreateInfo bi = { VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO }; bi.size = (VkDeviceSize)w * h * 4; bi.usage = VK_BUFFER_USAGE_TRANSFER_SRC_BIT;
    if ((r = vkCreateBuffer(dev, &bi, 0, &s.sb))) { logf("vkCreateBuffer %d", r); return false; }
    vkGetBufferMemoryRequirements(dev, s.sb, &req);
    VkMemoryAllocateInfo ai = { VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO }; ai.allocationSize = req.size;
    ai.memoryTypeIndex = (uint32_t)mem_type(req.memoryTypeBits, VK_MEMORY_PROPERTY_HOST_VISIBLE_BIT | VK_MEMORY_PROPERTY_HOST_COHERENT_BIT);
    if ((r = vkAllocateMemory(dev, &ai, 0, &s.smem)) || (r = vkBindBufferMemory(dev, s.sb, s.smem, 0)) ||
        (r = vkMapMemory(dev, s.smem, 0, VK_WHOLE_SIZE, 0, &s.smap))) { logf("staging memory %d", r); return false; }
    s.w = w; s.h = h; s.fmt = fmt; s.cur = 0;
    logf("images %ux%u format %u", w, h, fmt);
    return true;
}
static bool upload(Slot &s, VkImage img)
{
    vkResetCommandBuffer(cb, 0);
    VkCommandBufferBeginInfo bb = { VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO }; bb.flags = VK_COMMAND_BUFFER_USAGE_ONE_TIME_SUBMIT_BIT;
    vkBeginCommandBuffer(cb, &bb);
    VkImageMemoryBarrier b = { VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER };
    b.srcAccessMask = 0; b.dstAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; b.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED; b.newLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL;
    b.srcQueueFamilyIndex = b.dstQueueFamilyIndex = VK_QUEUE_FAMILY_IGNORED; b.image = img; b.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TOP_OF_PIPE_BIT, VK_PIPELINE_STAGE_TRANSFER_BIT, 0, 0, 0, 0, 0, 1, &b);
    VkBufferImageCopy cp = {}; cp.imageSubresource = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 0, 1 }; cp.imageExtent = { s.w, s.h, 1 };
    vkCmdCopyBufferToImage(cb, s.sb, img, VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL, 1, &cp);
    b.srcAccessMask = VK_ACCESS_TRANSFER_WRITE_BIT; b.dstAccessMask = VK_ACCESS_TRANSFER_READ_BIT | VK_ACCESS_SHADER_READ_BIT;
    b.oldLayout = VK_IMAGE_LAYOUT_TRANSFER_DST_OPTIMAL; b.newLayout = VK_IMAGE_LAYOUT_TRANSFER_SRC_OPTIMAL;   // what OpenVR expects
    vkCmdPipelineBarrier(cb, VK_PIPELINE_STAGE_TRANSFER_BIT, VK_PIPELINE_STAGE_ALL_COMMANDS_BIT, 0, 0, 0, 0, 0, 1, &b);
    vkEndCommandBuffer(cb);
    VkSubmitInfo si = { VK_STRUCTURE_TYPE_SUBMIT_INFO }; si.commandBufferCount = 1; si.pCommandBuffers = &cb;
    vkResetFences(dev, 1, &fence);
    VkResult r = vkQueueSubmit(queue, 1, &si, fence); if (r) { logf("vkQueueSubmit %d", r); return false; }
    vkWaitForFences(dev, 1, &fence, VK_TRUE, 1000000000ull);
    return true;
}

// mirror overlay: copy placement of the game's overlay every frame we publish
static void mirror_follow(Slot &s)
{
    auto *ov = vr::VROverlay(); if (s.game == vr::k_ulOverlayHandleInvalid) return;
    float w = 1; if (ov->GetOverlayWidthInMeters(s.game, &w) == vr::VROverlayError_None) ov->SetOverlayWidthInMeters(s.target, w);
    vr::VROverlayTransformType tt; ov->GetOverlayTransformType(s.game, &tt);
    vr::HmdMatrix34_t m;
    if (tt == vr::VROverlayTransform_Absolute) { vr::ETrackingUniverseOrigin o; if (!ov->GetOverlayTransformAbsolute(s.game, &o, &m)) ov->SetOverlayTransformAbsolute(s.target, o, &m); }
    else if (tt == vr::VROverlayTransform_TrackedDeviceRelative) { vr::TrackedDeviceIndex_t d; if (!ov->GetOverlayTransformTrackedDeviceRelative(s.game, &d, &m)) ov->SetOverlayTransformTrackedDeviceRelative(s.target, d, &m); }
    if (ov->IsOverlayVisible(s.game)) ov->ShowOverlay(s.target); else ov->HideOverlay(s.target);
    uint32_t so = 0; if (!ov->GetOverlaySortOrder(s.game, &so)) ov->SetOverlaySortOrder(s.target, so + 1);
    vr::VRTextureBounds_t tb; if (!ov->GetOverlayTextureBounds(s.game, &tb)) ov->SetOverlayTextureBounds(s.target, &tb);
    float a = 1; if (!ov->GetOverlayAlpha(s.game, &a)) ov->SetOverlayAlpha(s.target, a);
    float c = 0; if (!ov->GetOverlayCurvature(s.game, &c)) ov->SetOverlayCurvature(s.target, c);
}

static void service(int i)
{
    Slot &s = slots[i];
    if (!s.shm) {
        char path[64]; snprintf(path, sizeof path, "/tmp/farcryvr_bridge_%d.shm", i);
        int fd = open(path, O_RDONLY); if (fd < 0) return;
        struct stat st; if (fstat(fd, &st) || st.st_size < BR_SIZE) { close(fd); return; }
        void *p = mmap(0, BR_SIZE, PROT_READ, MAP_SHARED, fd, 0); if (p == MAP_FAILED) { close(fd); return; }
        s.fd = fd; s.shm = (volatile uint32_t *)p; logf("slot %d: mapped %s", i, path);
    }
    volatile uint32_t *h = s.shm;
    uint32_t s1 = __atomic_load_n(&h[1], __ATOMIC_ACQUIRE);
    if ((s1 & 1) || s1 == s.last || h[0] != 0x52564346) return;
    uint32_t w = h[2], hh = h[3], fmt = h[4];
    if (!w || !hh || w > BR_MAXDIM || hh > BR_MAXDIM) return;
    if (w != s.w || hh != s.h || fmt != s.fmt) if (!make_images(s, w, hh, fmt)) { s.last = s1; return; }
    memcpy(s.smap, (const void *)((const char *)h + BR_HDR), (size_t)w * hh * 4);
    char key[128]; memcpy(key, (const void *)(h + 8), sizeof key); key[127] = 0;
    __atomic_thread_fence(__ATOMIC_ACQUIRE);
    if (__atomic_load_n(&h[1], __ATOMIC_ACQUIRE) != s1) return;   // torn: the next tick retries
    s.last = s1;
    auto *ov = vr::VROverlay();
    if (s.target == vr::k_ulOverlayHandleInvalid || strcmp(key, s.key)) {
        strcpy(s.key, key);
        vr::EVROverlayError e = ov->FindOverlay(key, &s.game);
        logf("slot %d: FindOverlay(%s) -> %d, handle %llx", i, key, e, (unsigned long long)s.game);
        if (e) { s.game = vr::k_ulOverlayHandleInvalid; return; }
        s.target = s.game; s.mirror = false;
    }
    VkImage img = s.img[s.cur]; s.cur = (s.cur + 1) % NIMG;
    if (!upload(s, img)) return;
    vr::VRVulkanTextureData_t vd = { (uint64_t)img, dev, phys, inst, queue, family, s.w, s.h, s.fmt, 1 };
    vr::Texture_t tex = { &vd, vr::TextureType_Vulkan, vr::ColorSpace_Auto };
    if (s.mirror) mirror_follow(s);
    vr::EVROverlayError e = ov->SetOverlayTexture(s.target, &tex);
    if (e && !s.mirror) {
        // not allowed to set another process's overlay: draw on a mirror overlay of our own, just above the game's
        logf("slot %d: SetOverlayTexture on the game's overlay -> %d, switching to a mirror overlay", i, e);
        char mk[160]; snprintf(mk, sizeof mk, "farcryvr.bridge.%d", i);
        vr::EVROverlayError ce = ov->CreateOverlay(mk, "Far Cry VR HUD", &s.target);
        logf("slot %d: CreateOverlay(%s) -> %d", i, mk, ce);
        if (ce) { s.target = vr::k_ulOverlayHandleInvalid; return; }
        s.mirror = true; mirror_follow(s);
        e = ov->SetOverlayTexture(s.target, &tex);
    }
    s.sent++;
    if (e) { if (s.errs++ < 10) logf("slot %d: SetOverlayTexture -> %d", i, e); }
    else if (s.sent <= 2 || (s.sent % 1000) == 0) logf("slot %d: %u frames sent (%s)", i, s.sent, s.mirror ? "mirror" : "direct");
}

int main(int argc, char **argv)
{
    pid_t follow = argc > 1 ? (pid_t)atoi(argv[1]) : 0;
    signal(SIGPIPE, SIG_IGN);
    vr::EVRInitError ie = vr::VRInitError_Unknown;
    for (int tries = 0; tries < 120; tries++) {
        vr::VR_Init(&ie, vr::VRApplication_Overlay);
        if (ie == vr::VRInitError_None) break;
        if (follow && kill(follow, 0) && errno == ESRCH) return 0;
        sleep(1);
    }
    if (ie) { logf("VR_Init failed: %d", ie); return 1; }
    logf("hudbridge up, following pid %d", (int)follow);
    if (!vk_init()) { vr::VR_Shutdown(); return 1; }
    for (unsigned tick = 0;; tick++) {
        if (follow && (tick % 50) == 0 && kill(follow, 0) && errno == ESRCH) break;
        for (int i = 0; i < 8; i++) service(i);
        if ((tick % 3) == 0) for (int i = 0; i < 8; i++) if (slots[i].mirror) mirror_follow(slots[i]);   // ~80 Hz
        vr::VREvent_t ev; while (vr::VRSystem()->PollNextEvent(&ev, sizeof ev)) if (ev.eventType == vr::VREvent_Quit) goto out;
        usleep(4000);
    }
out:
    logf("game gone, exiting");
    if (dev) vkDeviceWaitIdle(dev);
    vr::VR_Shutdown();
    for (int i = 0; i < 8; i++) { char p[64]; snprintf(p, sizeof p, "/tmp/farcryvr_bridge_%d.shm", i); unlink(p); }
    return 0;
}
