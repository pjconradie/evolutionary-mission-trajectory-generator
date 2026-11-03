KPL/MK

   SPICE meta-kernel for OSIRIS_universe-based promoted tutorial baselines
   (see docs/3_NLP_Solvers/IPOPT/meta_kernel_baselining_commands.md). Lists
   every kernel the flat loader would otherwise scan for this universe:
   the committed tutorial ephemeris files plus the shared de430.bsp staged
   from testatron/universe/ephemeris_files (not committed; see
   testatron/universe/ephemeris_files/go_get_these_files.txt).

   Referenced by:
     Config_Files/LowSIRIS-REx
     Config_Files/LowSIRIS-REx_high_thrust
     Config_Files/LowSIRIS-REx_high_thrust_low_c3
     Force_Models/LowSIRIS-REx
     Force_Models/LowSIRIS-REx_forcemodel_nlp
     LowSIRIS-REx/LowSIRIS-REx
     OSIRIS-REx/OSIRIS-REx

\begindata

    PATH_VALUES     = ( '/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/OSIRIS_universe/ephemeris_files',
                         '/repo/testatron/universe/ephemeris_files' )

    PATH_SYMBOLS    = ( 'OSIRIS',
                         'SHARED' )

    KERNELS_TO_LOAD = ( '$OSIRIS/naif0012.tls',
                         '$OSIRIS/pck00010.tpc',
                         '$OSIRIS/bennu_refdrmc_v1.bsp',
                         '$SHARED/de430.bsp' )

\begintext
