// composable per chiamare il backend proxy
import axios from "axios";

export const useApi = () => {
  const config = useRuntimeConfig();
  const base = config.public.apiBase;

  const getStations = async () => {
    return axios.get(`${base}/stations`).then((r) => r.data);
  };

  const getStation = async (id: string) => {
    return axios.get(`${base}/stations/${id}`).then((r) => r.data);
  };

  return { getStations, getStation };
};
