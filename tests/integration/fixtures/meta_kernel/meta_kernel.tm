KPL/MK

   SPICE meta-kernel fixture for the meta-kernel-capabilities test suite.

   References only small kernels already committed to this repository
   (see tests/cpp/test_meta_kernel_cspice_probe.cpp and
   tests/integration/test_meta_kernel_integration.py), so it is
   self-contained and requires no host-downloaded ephemeris.

\begindata

    PATH_VALUES     = ( '/repo/Universe/ephemeris_files',
                         '/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/ephemeris_files' )

    PATH_SYMBOLS    = ( 'LSKPCK',
                         'BENNU' )

    KERNELS_TO_LOAD = ( '$LSKPCK/naif0012.tls',
                         '$LSKPCK/pck00010.tpc',
                         '$BENNU/bennu_refdrmc_v1.bsp' )

\begintext
