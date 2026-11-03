KPL/MK

   SPICE meta-kernel for the EVM_universe-based promoted tutorial baseline
   (see docs/3_NLP_Solvers/IPOPT/meta_kernel_baselining_commands.md). Lists
   every kernel the flat loader would otherwise scan for this universe:
   the committed tutorial ephemeris files plus the shared de430.bsp staged
   from testatron/universe/ephemeris_files (not committed; see
   testatron/universe/ephemeris_files/go_get_these_files.txt).

   Referenced by:
     Flybys/EVM

\begindata

    PATH_VALUES     = ( '/repo/docs/0_Users/tutorial/Tutorial_EMTG_Files/EVM_universe/ephemeris_files',
                         '/repo/testatron/universe/ephemeris_files' )

    PATH_SYMBOLS    = ( 'EVM',
                         'SHARED' )

    KERNELS_TO_LOAD = ( '$EVM/naif0012.tls',
                         '$EVM/pck00010.tpc',
                         '$SHARED/de430.bsp' )

\begintext
