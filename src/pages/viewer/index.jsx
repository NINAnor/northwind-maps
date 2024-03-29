import { ErrorComponent, Route } from "@tanstack/react-router";
import rootRoute from "../root";
import Layers from "./components/Layers";
import Map from "./components/Map";
import MapContextProvider from "./components/MapContextProvider";
import Metadata from "./components/Metadata";
import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import mapApi from "../../api";
import { NotFoundError } from "../../lib/utils";
import Lazy from "./components/Lazy";

const fetchMap = async () => {
  const map = await mapApi
    .get(window.METADATA_URL)

  if (!map) {
    throw new NotFoundError(`Map not found!`)
  }

  return map
}


const mapQueryOptions = queryOptions({
    queryKey: ['maps'],
    queryFn: fetchMap,
  })


export const viewerRoute = new Route({
  component: Viewer,
  path: '/',
  getParentRoute: () => rootRoute,
  errorComponent: MapErrorComponent,
  loader: ({ context: { queryClient }}) =>
    queryClient.ensureQueryData(mapQueryOptions),
})


function MapErrorComponent({ error }) {
  if (error instanceof NotFoundError) {
    return <div>{error.message}</div>
  }

  return <ErrorComponent error={error} />
}


export function Viewer() {
  const mapQuery = useSuspenseQuery(mapQueryOptions);
  const map = mapQuery.data;

  console.log(map);

  return (
    <MapContextProvider>
      <div id="app-wrap" style={{ display: 'flex' }}>
        <div id="sidebar">
          <Metadata {...map.data} />
          <Layers layers={map.data.layers} />
          <Lazy lazy={map.data.lazy} />
        </div>
        <Map {...map.data} />
      </div>
    </MapContextProvider>
  );
}
