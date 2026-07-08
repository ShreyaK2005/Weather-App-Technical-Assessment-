import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------- WEATHER ----------------

export const getCurrentWeather = (
    location,
    startDate,
    endDate
) =>
    api.get("/weather/current", {
        params: {
            location,
            start_date: startDate || undefined,
            end_date: endDate || undefined,
        },
    });

// ---------------- CRUD ----------------

export const getRecords = (location = "") =>
    api.get("/records", {
        params: {
            location: location || undefined,
        },
    });

export const getRecordsByLocation = (location) =>
    api.get("/records", {
        params: { location }
    });
export const exportRecordUrl = (id, format) =>
    `${import.meta.env.VITE_API_BASE_URL}/records/${id}/export?format=${format}`;


export const getRecord = (id) =>
    api.get(`/records/${id}`);

export const createRecord = (record) =>
    api.post("/records", record);

export const updateRecord = (id, record) =>
    api.put(`/records/${id}`, record);

export const deleteRecord = (id) =>
    api.delete(`/records/${id}`);

// ---------------- EXPORT ----------------

export const exportRecord = (id, format) =>
    api.get(`/records/${id}/export`, {
      params: { format },
      responseType: "blob",
    });

export default api;


