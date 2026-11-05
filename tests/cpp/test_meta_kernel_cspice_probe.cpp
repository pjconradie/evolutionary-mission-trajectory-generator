#include <SpiceUsr.h>

#include <cstring>
#include <string>

namespace
{
    bool endsWith(const std::string &value, const std::string &suffix)
    {
        return value.size() >= suffix.size()
            && value.compare(value.size() - suffix.size(), suffix.size(), suffix) == 0;
    }
}

int main()
{
    const char *metaKernel =
        "/repo/tests/integration/fixtures/meta_kernel/meta_kernel.tm";
    const char *malformedMetaKernel =
        "/repo/tests/integration/fixtures/meta_kernel/malformed_meta_kernel.tm";

    // Loading a valid meta-kernel should resolve its PATH_SYMBOLS/PATH_VALUES
    // and load the three kernels it lists.
    furnsh_c(metaKernel);
    if (failed_c())
        return 1;

    SpiceInt kernelCount = 0;
    ktotal_c("ALL", &kernelCount);
    // ktotal_c also counts the meta-kernel file itself (as a loaded text/META
    // kernel), so expect the 3 data kernels plus the meta-kernel entry.
    if (kernelCount != 4)
        return 2;

    const std::string expectedSuffixes[3] = {
        "naif0012.tls", "pck00010.tpc", "bennu_refdrmc_v1.bsp"};
    bool found[3] = {false, false, false};
    for (SpiceInt i = 0; i < kernelCount; ++i)
    {
        SpiceChar file[256];
        SpiceChar filtyp[32];
        SpiceChar source[256];
        SpiceInt handle = 0;
        SpiceBoolean entryFound = SPICEFALSE;
        kdata_c(i, "ALL", sizeof(file), sizeof(filtyp), sizeof(source),
                file, filtyp, source, &handle, &entryFound);
        if (!entryFound || failed_c())
            return 3;
        for (int j = 0; j < 3; ++j)
        {
            if (endsWith(std::string(file), expectedSuffixes[j]))
                found[j] = true;
        }
    }
    if (!found[0] || !found[1] || !found[2])
        return 4;

    // Unloading the meta-kernel should unload every kernel it loaded.
    unload_c(metaKernel);
    if (failed_c())
        return 5;

    SpiceInt kernelCountAfterUnload = 0;
    ktotal_c("ALL", &kernelCountAfterUnload);
    if (kernelCountAfterUnload != 0)
        return 6;

    // A meta-kernel that references a nonexistent kernel file should fail to
    // load, leave a retrievable CSPICE diagnostic, and load no data kernel
    // (CSPICE may still register the malformed .tm file itself as a loaded
    // text/META kernel entry before it hits the missing KERNELS_TO_LOAD
    // entry, so this checks "no .bsp got loaded" rather than an empty pool).
    erract_c((SpiceChar *)"SET", 100, (SpiceChar *)"RETURN");
    furnsh_c(malformedMetaKernel);
    if (!failed_c())
        return 7;

    SpiceChar message[1841];
    getmsg_c("LONG", sizeof(message), message);
    reset_c();
    if (std::strlen(message) == 0)
        return 8;

    SpiceInt kernelCountAfterFailedLoad = 0;
    ktotal_c("ALL", &kernelCountAfterFailedLoad);
    for (SpiceInt i = 0; i < kernelCountAfterFailedLoad; ++i)
    {
        SpiceChar file[256];
        SpiceChar filtyp[32];
        SpiceChar source[256];
        SpiceInt handle = 0;
        SpiceBoolean entryFound = SPICEFALSE;
        kdata_c(i, "ALL", sizeof(file), sizeof(filtyp), sizeof(source),
                file, filtyp, source, &handle, &entryFound);
        if (entryFound && endsWith(std::string(file), ".bsp"))
            return 9;
    }

    return 0;
}
