#include <boost/archive/text_oarchive.hpp>
#include <boost/filesystem.hpp>
#include <coin/IpIpoptApplication.hpp>
#include <gsl/gsl_sf_bessel.h>
#include <SpiceUsr.h>

#include <cmath>
#include <sstream>
#include <string>

int main()
{
    const boost::filesystem::path path("/tmp/emtg-dependency-probe");
    boost::filesystem::create_directories(path);
    if (!boost::filesystem::exists(path))
        return 1;

    std::ostringstream stream;
    boost::archive::text_oarchive archive(stream);
    std::string serializedValue = path.string();
    archive << serializedValue;
    boost::filesystem::remove_all(path);

    if (stream.str().empty())
        return 2;
    if (std::abs(gsl_sf_bessel_J0(0.0) - 1.0) > 1.0e-15)
        return 3;

    furnsh_c("/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/ephemeris_files/naif0012.tls");
    SpiceInt kernelCount = 0;
    ktotal_c("ALL", &kernelCount);
    if (failed_c() || kernelCount != 1)
        return 4;

    SpiceDouble epoch = 0.0;
    str2et_c("2000 JAN 1 12:00:00 TDB", &epoch);
    if (failed_c() || std::abs(epoch) > 1.0e-6)
        return 5;
    kclear_c();

    Ipopt::SmartPtr<Ipopt::IpoptApplication> application =
        IpoptApplicationFactory();
    if (application->Initialize() != Ipopt::Solve_Succeeded)
        return 6;

    return 0;
}
