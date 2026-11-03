
The EMTG shall have the ability to use either:
i) a provided `meta_kernel.tm` as reference to Spice Kernels or
ii) be provided with a flat `*/universe/ephemeris_files/...` as reference to Spice Kernels.

iii) The `meta_kernel.tm` shall have priority above a flat universe `*/universe/ephemeris_files/...`. If a `meta_kernel.tm` is used it shall be used.

iv) A compatible meta kernel example is provided below. This is a real `meta_kernel.tm` example used in mission simulations:

```meta-kernel
KPL/MK

   This is a modified spice meta kernel of a similar name, 
   orx_noola_2022_v01.tm. From the original meta kernel, the
   following changes were made:
   - Removed the kernels for
     - IK Files
     - CK Files
     - SCLK Files
     - FK Files
     - DSK Files
   - Modified the PATH_VALUES keyword to point to ...

   The objective of this Kernel file is to analyse the OSIRIS-REx beacon
   navigation capabilities during the year 2022.

   This file was created on July 10, 2025 by Jaco Conradie. The original
   file is located at orx_noola_2022_v01.tm.

   \begindata

      PATH_VALUES     = ('kernels')

      PATH_SYMBOLS    = ('KERNELS')

      KERNELS_TO_LOAD = (
        '$KERNELS/lsk/naif0012.tls'
        
        '$KERNELS/pck/pck00010.tpc'
        
        '$KERNELS/pck/bennu_v17.tpc'
        
        '$KERNELS/spk/plu060.bsp'
        '$KERNELS/spk/ura116.bsp'
        '$KERNELS/spk/nep095.bsp'
        '$KERNELS/spk/sat415.bsp'
        '$KERNELS/spk/jup347.bsp'
        '$KERNELS/spk/de424.bsp'
        
        '$KERNELS/spk/bennu_refdrmc_v1.bsp'

        '$KERNELS/spk/2017/orx_160909_171201_170830_od023_v1.bsp'
        '$KERNELS/spk/2017/orx_170501_180710_171005_od027_v1.bsp'
        '$KERNELS/spk/2017/orx_170923_180710_180321_od031_v1.bsp'

        '$KERNELS/spk/2018/orx_170923_180710_180321_od031_v1.bsp'
        '$KERNELS/spk/2018/orx_180301_181201_180921_od044_v1.bsp'
        '$KERNELS/spk/2018/orx_180801_190302_181218_od077_v1.bsp'
        '$KERNELS/spk/2018/orx_181203_190302_190104_od085_v1.bsp'

        '$KERNELS/spk/2019/orx_181231_190305_190215_od099_v1.bsp'
        '$KERNELS/spk/2019/orx_190201_190327_190315_od110_v1.bsp'
        '$KERNELS/spk/2019/orx_190301_190424_190412_od125_v1.bsp'
        '$KERNELS/spk/2019/orx_190401_190522_190508_od137_v1.bsp'
        '$KERNELS/spk/2019/orx_190426_190605_190522_od143_v1.bsp'
        '$KERNELS/spk/2019/orx_190511_190619_190603_od148_v1.bsp'
        '$KERNELS/spk/2019/orx_190601_190625_190614_od154_v1.bsp'
        '$KERNELS/spk/2019/orx_190612_190917_190730_od170_v1.bsp'
        '$KERNELS/spk/2019/orx_190712_190917_190814_od175_v1.bsp'
        '$KERNELS/spk/2019/orx_190809_191015_191004_od187_v1.bsp'
        '$KERNELS/spk/2019/orx_190915_191029_191014_od191_v1.bsp'
        '$KERNELS/spk/2019/orx_191001_191105_191021_od194_v1.bsp'
        '$KERNELS/spk/2019/orx_191015_191112_191030_od198_v1.bsp'
        '$KERNELS/spk/2019/orx_191027_200101_191104_od200_v1.bsp'
        '$KERNELS/spk/2019/orx_191101_200225_200214_od223_v1.bsp'

        '$KERNELS/spk/2020/orx_191101_200225_200214_od223_v1.bsp'
        '$KERNELS/spk/2020/orx_200127_200324_200311_od232_v1.bsp'
        '$KERNELS/spk/2020/orx_200305_200421_200410_od239_v1.bsp'
        '$KERNELS/spk/2020/orx_200414_200519_200504_od248_v1.bsp'
        '$KERNELS/spk/2020/orx_200401_200418_200418_od242_v2.bsp'
        '$KERNELS/spk/2020/orx_200430_200714_200701_od263_v1.bsp'
        '$KERNELS/spk/2020/orx_200616_200811_200727_od269_v1.bsp'
        '$KERNELS/spk/2020/orx_200709_200814_200814_od276_v1.bsp'
        '$KERNELS/spk/2020/orx_200811_200908_200828_od280_v1.bsp'
        '$KERNELS/spk/2020/orx_200827_201020_201020_od294_v1.bsp'
        '$KERNELS/spk/2020/orx_201020_210524_210103_od297_v1.bsp'
        '$KERNELS/spk/2020/orx_201020_201109_201020_od294_v1.bsp' 

        '$KERNELS/spk/orx_210101_210330_210310_od302_v1.bsp'
        '$KERNELS/spk/orx_210115_230917_230915_merged_v1.bsp'
        '$KERNELS/spk/orx_230809_231001_230930_od383a_v1.bsp'
        )

   \begintext

End of MK file.
```

