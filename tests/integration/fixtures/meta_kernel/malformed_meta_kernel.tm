KPL/MK

   Deliberately malformed meta-kernel fixture: references a kernel file
   that does not exist, to exercise EMTG's and CSPICE's error-handling
   path for a bad SPICE_meta_kernel (see
   tests/cpp/test_meta_kernel_cspice_probe.cpp and
   tests/integration/test_meta_kernel_integration.py).

\begindata

    PATH_VALUES     = ( '/repo/tests/integration/fixtures/meta_kernel' )

    PATH_SYMBOLS    = ( 'KERNELS' )

    KERNELS_TO_LOAD = ( '$KERNELS/does_not_exist.bsp' )

\begintext
