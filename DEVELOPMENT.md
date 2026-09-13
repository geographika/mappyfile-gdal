# Development and Design Notes

```console
conda activate gdal-mapserver
conda install mapserver --yes


cd D:\GitHub\mappyfile-gdal

pip install -r requirements-dev.txt
pip install -e .

cd D:\GitHub\mappyfile-gdal

gdal info ./tests/data/ne_110m_land.fgb --of JSON

# Linux
gdal vector info ./tests/data/ne_110m_land.fgb --of JSON | mappyfile-gdal | map2img -m /dev/stdin -o out.png
# Windows
gdal vector info ./tests/data/ne_110m_land.fgb --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png
# Windows PowerShell 7
gdal vector info ./tests/data/ne_110m_land.fgb --of JSON | mappyfile-gdal - out.map && map2img -m out.map -o out.png

#sample map2img command
map2img -m ./scripts/mapfiles/aaigrid__pixel_per_line.asc.raster.map -o ../output/aaigrid__pixel_per_line.asc.raster.png -all_debug 5

gdal info K:\Data\NATIONAL_LAND_COVER_MAP.gdb.zip --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png

gdal info "/vsicurl/https://raw.githubusercontent.com/ofrohn/d3-celestial/master/data/constellations.lines.json" --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png

```


- Cannot stream to map2img on Windows, so you need to write to a temporary file first.
- Can stream on Linux, using `/dev/stdin` as the input Mapfile, but this would require absolute paths for `DATA` and `SHAPEPATH`.
- No WCS client functionality in MapServer - but WCS files can be read through GDAL
- [MS RFC 25: Align MapServer pixel and extent models with OGC models](https://mapserver.org/development/rfc/ms-rfc-25.html) - problems!

- Initially had a `split` parameter. However, easier to do this with GDAL, and select just the layers required:

```
gdal info D:\Data\natural_earth_vector.gpkg\packages\natural_earth_vector.gpkg --summary
gdal info D:\Data\natural_earth_vector.gpkg\packages\natural_earth_vector.gpkg --of JSON --layer ne_10m_lakes --layer ne_10m_admin_0_countries | mappyfile-gdal - out.map --shapepath "D:\Data\natural_earth_vector.gpkg\packages"; map2img -m out.map -o out.png


gdal info natural_earth_vector.gpkg --of JSON --layer ne_10m_lakes --layer ne_10m_admin_0_countries | mappyfile-gdal - out.map; map2img -m out.map -o out.png

```

See lakes-countries.png

## Raster

### NoData

```
# from map2img the following is returned
LoadGDALImage(pixel_per_line): NODATA value -99999 in GDAL
file or PROCESSING directive largely ignored.  Not yet fully supported for
unclassified scaled data.  The NODATA value is excluded from auto-scaling
min/max computation, but will not be transparent.
```

```
PROCESSING "SCALE=0.005,0.178"
PROCESSING "NODATA=NaN"
```

### Scale

When using `SCALE=AUTO`, MapServer computes the min/max from the pixels intersecting the requested area, not from the whole raster.
See https://lists.osgeo.org/pipermail/mapserver-users/2015-August/078144.html

This can lead to inconsistent rendering across different requests, as each tile or zoom level may have its own range. 
Precomputing SCALE from the GDAL info stats provides consistent rendering.

See also https://mapserver.org/input/raster.html#special-processing-directives

SCALE only affects how cells are drawn when the layer is unclassified.
If you classify the raster, the classification values are used instead.

MapServer maps each value to a gray level between 0 and 255; values outside the range are clamped to black or white.

### Example Commands

```

gdal vector info K:\Data\Unified_Geologic_Map_of_the_Moon_GIS_v2\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Global_Geology_of_the_Moon_5M_03-02-2020.gdb  --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png
gdal vector info K:\Data\Unified_Geologic_Map_of_the_Moon_GIS_v2\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Shapefiles --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png

mappyfile validate out.map

```

Driver issue:

```
Warning 1: Linear_Features layer has a K:\Data\Unified_Geologic_Map_of_the_Moon_GIS_v2\Unified_Geologic_Map_of_the_Moon_GIS\Lunar_GIS\Global_Geology_of_the_Moon_5M_03-02-2020.gdb\a0000000d.gdbtable.cdf file using Compressed Data Format (CDF)
that is unhandled by the OpenFileGDB driver, but could be handled by the FileGDB driver.

Add  --input-format FileGDB to gdal vector info
```

jp2 file:

```
conda install -c conda-forge libgdal-jp2openjpeg --yes

$data = "D:\Data\France\BDORTHO_2-0_RVB-0M20_JP2-E080_LAMB93_D095_2024-01-01\ORTHOHR\1_DONNEES_LIVRAISON_2025-06-00022\OHR_RVB_0M20_JP2-E080_LAMB93_D95-2024\95-2024-0595-6890-LA93-0M20-E080.jp2"
$json = gdal raster info $data  --of JSON
$out = [IO.Path]::GetFullPath((Join-Path $PWD "tests/json/raster/95-2024-0595-6890-LA93-0M20-E080.jp2.json"))
[System.IO.File]::WriteAllText($out, ($json -join "`n"))

gdal raster info $data --of JSON | mappyfile-gdal - out.map; map2img -m out.map -o out.png
mappyfile validate out.map

```

## Performance

Measure time spent in each function for a large JSON file.

```
mappyfile-gdal ./tests/json/vector/natural_earth_vector.gpkg.json out.map
python -m cProfile -s cumtime -m mappyfile_gdal.cli ./tests/json/vector/natural_earth_vector.gpkg.json out.map | Select-Object -First 40
```

`mappyfile.loads()` and `mappyfile.create()` were causing the above to take ~150 seconds. Approach updated to make dicts from scratch, which reduced the time to ~1 second.