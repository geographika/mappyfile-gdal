conda activate gdal-master
# gdal dataset identify -r C:\docs\gdal\autotest

pip install -e D:\GitHub\mappyfile-gdal


cd "D:\GitHub\mappyfile-gdal\scripts"

gdal dataset identify -r -q "C:\docs\gdal\autotest\ogr" > datasets.txt

cd "C:\docs\gdal\autotest\gdrivers\data"
gdal dataset identify -r -o "D:\GitHub\mappyfile-gdal\scripts\datasets.csv" --overwrite "."
gdal dataset identify -r -o "D:\GitHub\mappyfile-gdal\scripts\datasets-detailed.csv" --overwrite "." --detailed

# TOCHECK why do we need --force-recursive here?
cd "C:\docs\gdal\autotest\ogr\data"
gdal dataset identify --force-recursive -o "D:\GitHub\mappyfile-gdal\scripts\datasets-vector.csv" --overwrite "."

# following fails with encoding issues
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$json = gdal vector info "D:\Data\natural_earth_vector.gpkg\packages\natural_earth_vector.gpkg" --of json  2>$nul
[System.IO.File]::WriteAllText("D:\GitHub\mappyfile-gdal\scripts\sample_vector_json\natural_earth_vector.gpkg.json", ($json -join "`n"))


$json = gdal vector info "D:\Data\France\ADMIN-EXPRESS_3-2__SHP_LAMB93_FXX_2025-02-17\ADMIN-EXPRESS\1_DONNEES_LIVRAISON_2025-02-00187\ADE_3-2_SHP_LAMB93_FXX-ED2025-02-17\ARRONDISSEMENT_MUNICIPAL.shp" --of json  2>$nul
[System.IO.File]::WriteAllText("D:\GitHub\mappyfile-gdal\scripts\sample_vector_json\ARRONDISSEMENT_MUNICIPAL.shp.json", ($json -join "`n"))

$json = gdal vector info "D:\Data\France\ADMIN-EXPRESS_3-2__SHP_LAMB93_FXX_2025-02-17\ADMIN-EXPRESS\1_DONNEES_LIVRAISON_2025-02-00187\ADE_3-2_SHP_LAMB93_FXX-ED2025-02-17\CANTON.shp" --of json  2>$nul
[System.IO.File]::WriteAllText("D:\GitHub\mappyfile-gdal\scripts\sample_vector_json\CANTON.shp.json", ($json -join "`n"))

gdal info .\aaigrid\byte.tif.grd --of json

# gdal info C:\docs\gdal\autotest\gdrivers\data\mbtiles\field_type_from_values.mbtiles
# ERROR 1: 'C:\docs\gdal\autotest\gdrivers\data\mbtiles\field_type_from_values.mbtiles' has both raster and vector content. Please use 'gdal raster info' or 'gdal vector info'


gdal dataset check NE1_50M_SR_W.tif

gdal raster info "C:\docs\gdal\autotest\gdrivers\data\zarr\v3\vlen_utf8.zarr" --of json
# ERROR 6: Only arrays with numeric data types can be exposed as classic GDALDataset
# following seems to run without any errors
gdal dataset check "C:\docs\gdal\autotest\gdrivers\data\zarr\v3\vlen_utf8.zarr"

# VRT errors due to <SourceFilename relativeToVRT="1">../netcdf/byte_no_cf.nc</SourceFilename>
# relativeToVRT="1": the path is relative to the VRT file itself, so the current folder doesn't matter?

cd D:\GitHub\mappyfile-gdal
# $env:GDAL_VRT_ENABLE_PYTHON = "YES"
python ./scripts/generate_json.py --csv ./scripts/datasets_sample.csv --root C:\docs\gdal\autotest\gdrivers\data --out-dir ./scripts/sample_json

python ./scripts/generate_json.py --csv ./scripts/datasets-vector.csv --root C:\docs\gdal\autotest\ogr\data --out-dir ./scripts/sample_vector_json


# Mapfile generation
cd D:\GitHub\mappyfile-gdal
python ./tests/test_mapfile_generation.py

# image outputs

# the following has no effect in a Mapfile
#     CONFIG  "GDAL_VRT_PYTHON_TRUSTED_MODULES" "YES"
# need to set as an environment variable
$env:GDAL_VRT_ENABLE_PYTHON = "YES"
map2img -m scripts/mapfiles/raster/vrt__n43_hillshade.vrt.raster.stats.map -o ../../output/raster/vrt__n43_hillshade.vrt.raster.stats.png -all_debug 5

map2img -m scripts/mapfiles/vector/data__mvt__point_polygon__1__1__1.pbf.vector.map -o ../../output/vector/data__mvt__point_polygon__1__1__1.pbf.vector.png -all_debug 5
map2img -m scripts/mapfiles/vector/natural_earth_vector.gpkg.map -o ../../output/vector/natural_earth_vector.gpkg.png -all_debug 5
