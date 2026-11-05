KPL/MK

   SPICE meta-kernel for OSIRIS_universe-based promoted tutorial baselines
   (see docs/3_NLP_Solvers/IPOPT/meta_kernel_baselining_commands.md). Lists
   every kernel the flat loader would otherwise scan for this universe. All
   kernel files below are resolved relative to the execution-root universe
   folder's staged ephemeris_files directory (/artifacts/universe/ephemeris_files
   inside the dev-container and archive-runtime containers alike), exactly
   where prepare_tutorial_universe() already copies the tutorial's committed
   ephemeris files and supplements the shared de430.bsp (not committed; see
   testatron/universe/ephemeris_files/go_get_these_files.txt). This keeps the
   fixture portable across both the toolchain dev container (which also
   mounts the full repository at /repo) and a packaged archive-runtime
   container (which mounts only this single case directory, with no /repo).

   Referenced by:
     Config_Files/LowSIRIS-REx
     Config_Files/LowSIRIS-REx_high_thrust
     Config_Files/LowSIRIS-REx_high_thrust_low_c3
     Force_Models/LowSIRIS-REx
     Force_Models/LowSIRIS-REx_forcemodel_nlp
     LowSIRIS-REx/LowSIRIS-REx
     OSIRIS-REx/OSIRIS-REx

\begindata

    PATH_VALUES     = ( '/artifacts/universe/ephemeris_files' )

    PATH_SYMBOLS    = ( 'KERNELS' )

    KERNELS_TO_LOAD = ( '$KERNELS/naif0012.tls',
                         '$KERNELS/pck00010.tpc',
                         '$KERNELS/bennu_refdrmc_v1.bsp',
                         '$KERNELS/de430.bsp' )

\begintext
