import pathlib
import zipfile
import urllib
import json

from osgeo import gdal
import pathlib
from jinja2 import Environment, PackageLoader, select_autoescape
import click


def to_cog(source, force=False):
    '''
    Convert a tif to cog
    Returns the path to the cog
    '''
    source_path = pathlib.Path(source)
    cog_path = source_path.parent / (source_path.stem + '.tif.cog')
    src_ds = gdal.Open(str(source_path))

    # Create GDAL options for the COG transformation
    options = [
        'COMPRESS=DEFLATE',
        'TILING_SCHEME=GoogleMapsCompatible',
        'COMPRESS=LZW',
        'BIGTIFF=IF_SAFER',
    ]


    # Set GDAL_NUM_THREADS to use all available CPUs
    gdal.SetConfigOption('GDAL_NUM_THREADS', 'ALL_CPUS')
    try:
        gdal.SetConfigOption('GDAL_CACHEMAX', '1024')
    except:
        pass

    # Translate and create the COG

    if force or not cog_path.exists():
        pass
        # gdal.Translate(str(cog_path), src_ds, format='COG', creationOptions=options)

    return cog_path


def to_hierarchy(key_map, prefix, parent_key="", downloads={}, zips={}):
    layers = []
    for k in key_map.keys():
        id = '_es_'.join(filter(lambda x:x, [parent_key, k]))
        name = k
        layer = {
            "id": id,
            "name": name.replace('_', ' ').capitalize(),
        }
        if id in downloads:
            layer['download'] = downloads[id]
        if id in zips:
            layer['download'] = str(zips[id])
        if key_map[k]:
            layer['children'] = to_hierarchy(key_map[k], parent_key=id, downloads=downloads, zips=zips, prefix=prefix)

        layers.append(layer)

    return layers

@click.command()
@click.argument("cog_directory")
@click.argument("colormap_file")
@click.option("--output", help="write to output")
@click.option("--tiles_base_url", help="the base url to the tiles, usually points to nginx")
@click.option("--prefix", help="the prefix to the path")
@click.option('--force_cog', default=False, help="Force recreate COG")
def generate_files(cog_directory, colormap_file, output, tiles_base_url, prefix, force_cog=False):
    env = Environment(
        loader=PackageLoader('main'),
        autoescape=select_autoescape()
    )
    env.policies['json.dumps_kwargs']['ensure_ascii'] = False
    BASE = pathlib.Path(cog_directory)
    colormaps = json.load(open(colormap_file))

    SOURCES = {}
    LAZY_SOURCES = {}
    DOWNLOADS = {}

    SOURCES["osm"] = {
        "type": "raster",
        "tiles": [
            "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
        ],
        "attribution": "&copy; <a href=\\\"https://www.openstreetmap.org/copyright\\\">OpenStreetMap</a> contributors &copy; <a href=\\\"https://carto.com/attributions\\\">CARTO</a>",
        "tileSize": 256
    }

    for filepath in BASE.iterdir():
        if not filepath.is_dir() and 'tif' in filepath.suffix:
            cog_path = to_cog(filepath, force=force_cog)
            name, first_dot, rest = cog_path.name.partition('.')

            color = ""
            if name in colormaps:
                color = f"&colormap_name={colormaps.get(name)}"

            LAZY_SOURCES[name] = {
                "type": "raster",
                "tiles": [
                    f"/tiler/tiles/WebMercatorQuad/{{z}}/{{x}}/{{y}}@1x?url={urllib.parse.quote_plus(tiles_base_url)}{urllib.parse.quote_plus(prefix)}{cog_path.name}&bidx=1{color}",
                ]
            }
            DOWNLOADS[name] = f"{prefix}{filepath.name}"
    
    template = env.get_template("style.json.tpl")
    
    with open(f'{output}/style.json', 'w+') as f:
        f.write(template.render({
            "sources": SOURCES,
            "layers": [{"id": k, "type": "raster", "source": k, "layout": {"visibility": "none" if k != "osm" else "visible"},}  for k in SOURCES.keys()]
        }))


    LAYERS = {}
    ZIPS = {}
    ZIP_MAP = {}
    for k in LAZY_SOURCES.keys():
        try:
            title, value = k.split("_es_")
            if not title in LAYERS:
                LAYERS[title] = {}
                ZIP_MAP[title] = BASE / f'{title}.zip'
                ZIPS[title] = zipfile.ZipFile(ZIP_MAP[title], 'w')
            ZIPS[title].write(BASE / f'{k}.tif')

            LAYERS[title][value] = {} 
        except ValueError:
            pass

    with open(f'{output}/metadata.json', 'w+') as f:
        template = env.get_template("metadata.json.tpl")
        f.write(template.render({
            "layers": to_hierarchy(LAYERS, downloads=DOWNLOADS, zips=ZIP_MAP, prefix=prefix),
            "lazy_sources": LAZY_SOURCES,
            "lazy_layers": {k: {"id": k, "type": "raster", "source": LAZY_SOURCES[k]}  for k in LAZY_SOURCES.keys()}
        }))


if __name__ == '__main__':
    generate_files()
