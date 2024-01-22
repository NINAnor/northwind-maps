# Generate data script

Upload the data in `data` folder. For example `layers` will contain all the `.tif` files.

```bash
docker compose build
docker compose run cli /app/data/layers --output /app/data/layers
```

This will convert all the rasters to cog, applying a colorscale based on `Reds`. 